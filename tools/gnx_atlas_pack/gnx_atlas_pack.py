#!/usr/bin/env python3
"""
gnx-atlas-pack: Pack a GNX mod's sprite strips into per-mod texture atlases.

Reads mod's strips/ folder (horizontal frame strips), splits each strip into
frames, shelf-packs frames into 4096x4096 atlas PNGs, writes:
    <mod>/atlas/atlas_N.png
    <mod>/atlas/uv.json

Frame counts and origins come from the mod's JSON (classes.json, cells.json and the
manifest's monster_art), matched to the strip's file name without regard to capitals.
A strip the JSON does not name gets a guessed count (near-square frames, biased toward
common GNX sizes such as 90x90, 175x90, 175x115) and a [WARN] line: check those.

Identical frames (same size and pixels, e.g. the empty frames of a layer) are stored
once; every frame that repeats one points at the same place in uv.json.

Usage: python gnx_atlas_pack.py <mod_dir> [--atlas-size 4096] [--padding 2] [--dry-run]
Needs Pillow. The released dist/gnx_atlas_pack.exe is this script built with PyInstaller.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.stderr.write("ERROR: Pillow is required. pip install Pillow\n")
    sys.exit(1)

DEFAULT_ATLAS_SIZE = 4096
DEFAULT_PADDING = 2


def infer_frame_count(strip_w: int, strip_h: int) -> int:
    """
    Guess frame count for a horizontal strip.
    GNX convention: frame_width divides strip_width evenly, all frames same size.
    Common ratios observed in real mods (frieren, gnx_test_mod):
      strip_w/strip_h ratios: 1, 2, 3, 5, 7, 15, 30, 45, 60, ~70
    We pick the smallest integer N such that strip_w/N produces a frame_width
    that is a "reasonable" sprite size (>= strip_h/2, <= strip_h*4).
    Falls back to 1 if strip is square-ish.
    """
    if strip_w == strip_h:
        return 1

    # Prefer frame_width close to strip_h (near-square frames)
    # Try N = strip_w / candidate_w where candidate_w near strip_h
    best_n = 1
    best_score = float('inf')
    # candidates: N from 1..(strip_w // 20) but bounded
    for n in range(1, min(strip_w, 200) + 1):
        if strip_w % n != 0:
            continue
        fw = strip_w // n
        # We want fw to be reasonable relative to strip_h
        # Ideal fw is roughly [strip_h*0.5, strip_h*3]
        if fw < 8 or fw > strip_h * 5:
            continue
        # score: distance from "nice" ratio fw ~= strip_h * K where K in [1, 2]
        ratio = fw / strip_h
        # Prefer ratios 1.0, 1.4, 1.9 (from observed 90/90, 175/115~1.5, etc.)
        # Simple heuristic: minimize deviation from 1.0 while N is small
        # Weight: N * abs(fw - strip_h)
        score = abs(fw - strip_h) + n * 0.1
        if score < best_score:
            best_score = score
            best_n = n
    return max(1, best_n)


def read_manifest_sprite_meta(mod_dir: Path) -> tuple:
    """
    Read classes.json / cells.json, and the manifest's monster_art ("sprites" and "world"), to extract explicit
    frame counts and origins.
    Returns (frame_map, origin_map) where:
      frame_map[filename] = int frame count
      origin_map[filename] = (xorig, yorig)
    """
    frame_map = {}
    origin_map = {}

    def walk(node):
        if isinstance(node, dict):
            path = node.get("strip") or node.get("path")
            frames = node.get("frames") if "frames" in node else None
            if path and isinstance(path, str):
                # file names ignore case on Windows: "spr_h_Damona_x.png" in the JSON is spr_h_damona_x.png on disk
                fname = os.path.basename(path).lower()
                if frames and isinstance(frames, int):
                    frame_map[fname] = frames
                xo = node.get("xorig", 0)
                yo = node.get("yorig", 0)
                if xo != 0 or yo != 0:
                    origin_map[fname] = (xo, yo)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    def read(p):
        raw = p.read_text(encoding="utf-8-sig")
        return json.loads(re.sub(r',\s*([}\]])', r'\1', raw))

    for jf in ("classes.json", "cells.json"):
        p = mod_dir / jf
        if not p.exists():
            continue
        try:
            walk(read(p))
        except Exception:
            continue

    # the global monster_art file (a name or the object itself): its "sprites" list and its "world" entries. A world entry may name
    # a file in strips/ (the packer packs all of strips/); one outside it is simply never looked up. A manifest or art file that cannot
    # be read is said, not skipped: the frame counts it holds would be guessed
    manifest = mod_dir / "manifest.json"
    if manifest.exists():
        try:
            art = read(manifest).get("monster_art")
            if isinstance(art, str):
                art = read(mod_dir / art)
            if isinstance(art, dict):
                walk(art)
        except (OSError, ValueError, AttributeError) as e:
            print(f"  WARN: cannot read monster_art frame counts ({e}); frame counts of its strips are guessed")
    return frame_map, origin_map


class Rect:
    __slots__ = ("key", "frame_idx", "w", "h", "img", "x", "y", "atlas")

    def __init__(self, key, frame_idx, w, h, img):
        self.key = key
        self.frame_idx = frame_idx
        self.w = w
        self.h = h
        self.img = img
        self.x = 0
        self.y = 0
        self.atlas = 0


def shelf_pack(rects, atlas_size, padding):
    """Shelf pack. Returns list of atlas surfaces (as [rects_in_atlas_0, ...])."""
    # Sort by height desc, then width desc
    rects_sorted = sorted(rects, key=lambda r: (-r.h, -r.w))
    atlases = [[]]  # list of atlases, each is list of rects
    atlas_shelves = [[]]  # per atlas, list of (y, height, x_used)

    for r in rects_sorted:
        placed = False
        for ai, shelves in enumerate(atlas_shelves):
            # Try existing shelves
            for shelf in shelves:
                shelf_y, shelf_h, shelf_x = shelf
                if r.h + padding <= shelf_h and shelf_x + r.w + padding <= atlas_size:
                    r.x = shelf_x
                    r.y = shelf_y
                    r.atlas = ai
                    shelf[2] = shelf_x + r.w + padding
                    atlases[ai].append(r)
                    placed = True
                    break
            if placed:
                break
            # Try new shelf on this atlas
            next_y = max((s[0] + s[1] for s in shelves), default=0)
            if next_y + r.h + padding <= atlas_size and r.w + padding <= atlas_size:
                new_shelf = [next_y, r.h + padding, r.w + padding]
                shelves.append(new_shelf)
                r.x = 0
                r.y = next_y
                r.atlas = ai
                atlases[ai].append(r)
                placed = True
                break
        if not placed:
            # Open a new atlas
            atlases.append([])
            atlas_shelves.append([])
            ai = len(atlases) - 1
            if r.w + padding > atlas_size or r.h + padding > atlas_size:
                raise ValueError(f"Frame too big for atlas: {r.key}[{r.frame_idx}] {r.w}x{r.h}")
            new_shelf = [0, r.h + padding, r.w + padding]
            atlas_shelves[ai].append(new_shelf)
            r.x = 0
            r.y = 0
            r.atlas = ai
            atlases[ai].append(r)
    return atlases


def pack_mod(mod_dir: Path, atlas_size: int, padding: int, dry_run: bool = False):
    strips_dir = mod_dir / "strips"
    if not strips_dir.exists():
        print(f"[SKIP] {mod_dir.name}: no strips/ folder")
        return None

    frame_map, origin_map = read_manifest_sprite_meta(mod_dir)

    # rects = the frames stored in the atlas; frames = every frame as (key, index, rect). Identical frames (same size
    # and pixels, e.g. the empty frames of a layer that is not drawn in every frame) are stored once and shared: GNX
    # reads each frame's position from uv.json, so two frames may point at the same place (no GNX change needed)
    rects = []
    frames = []
    seen = {}
    stats = {"strips": 0, "frames": 0, "total_px": 0, "unknown_stride": [], "shared": 0, "shared_px": 0}

    for png in sorted(strips_dir.glob("*.png")):
        img = Image.open(png).convert("RGBA")
        w, h = img.size
        stats["strips"] += 1

        # Determine frame count
        if png.name.lower() in frame_map:
            n = frame_map[png.name.lower()]
        else:
            n = infer_frame_count(w, h)
            if n > 1:
                print(f"[WARN] {png.name}: no \"frames\" for it in classes.json or cells.json, guessed {n}. Check it.")
            if n == 1 and w > h * 1.5:
                stats["unknown_stride"].append(png.name)

        if w % n != 0:
            print(f"[WARN] {png.name}: width {w} not divisible by inferred frames {n}. Using n=1.")
            n = 1

        fw = w // n
        key = png.stem  # sprite key = filename without extension

        for i in range(n):
            frame_img = img.crop((i * fw, 0, (i + 1) * fw, h))
            sig = (fw, h, hashlib.blake2b(frame_img.tobytes(), digest_size=16).digest())
            r = seen.get(sig)
            if r is None:
                r = seen[sig] = Rect(key, i, fw, h, frame_img)
                rects.append(r)
            else:
                stats["shared"] += 1
                stats["shared_px"] += fw * h
            frames.append((key, i, r))
            stats["frames"] += 1
            stats["total_px"] += fw * h

    print(f"[{mod_dir.name}] strips={stats['strips']} frames={stats['frames']} "
          f"total_px={stats['total_px']:,}")
    if stats["shared"]:
        print(f"[{mod_dir.name}] {stats['shared']} frames repeat an earlier one and share its place "
              f"({stats['shared_px'] / (atlas_size * atlas_size):.1f} atlas pages saved)")
    if stats["unknown_stride"]:
        print(f"[{mod_dir.name}] {len(stats['unknown_stride'])} strips could not infer stride "
              f"(kept as 1 frame). Sample: {stats['unknown_stride'][:3]}")

    atlases = shelf_pack(rects, atlas_size, padding)

    print(f"[{mod_dir.name}] packed into {len(atlases)} atlas(es) of {atlas_size}x{atlas_size}")
    for ai, arects in enumerate(atlases):
        used = sum(r.w * r.h for r in arects)
        print(f"  atlas_{ai}: {len(arects)} frames, occupancy {used/(atlas_size*atlas_size)*100:.1f}%")

    if dry_run:
        return {"atlases": len(atlases), "stats": stats}

    # Write atlases
    out_dir = mod_dir / "atlas"
    out_dir.mkdir(exist_ok=True)

    uv = {
        "atlas_version": 1,
        "atlas_size": atlas_size,
        "padding": padding,
        "atlas_files": [],
        "entries": {}
    }

    for ai, arects in enumerate(atlases):
        surf = Image.new("RGBA", (atlas_size, atlas_size), (0, 0, 0, 0))
        for r in arects:
            surf.paste(r.img, (r.x, r.y))
        out_path = out_dir / f"atlas_{ai}.png"
        surf.save(out_path, "PNG", optimize=True)
        uv["atlas_files"].append(f"atlas_{ai}.png")

    # Build entries dict grouped by key: every frame, at the place of the rect that holds its pixels
    entries = {}
    for key, idx, r in frames:
        if key not in entries:
            entries[key] = {"frames": []}
        # Placeholder; we'll sort after
        entries[key]["frames"].append({
            "frame_idx": idx,
            "atlas": r.atlas,
            "x": r.x,
            "y": r.y,
            "w": r.w,
            "h": r.h,
        })
    # Sort frames by frame_idx, then drop the frame_idx field; add origins
    for k, v in entries.items():
        v["frames"].sort(key=lambda f: f["frame_idx"])
        for f in v["frames"]:
            del f["frame_idx"]
        strip_fname = (k + ".png").lower()
        if strip_fname in origin_map:
            v["xo"], v["yo"] = origin_map[strip_fname]

    uv["entries"] = entries

    uv_path = out_dir / "uv.json"
    uv_path.write_text(json.dumps(uv, indent=2), encoding="utf-8")

    print(f"[{mod_dir.name}] wrote {len(atlases)} atlas PNG(s) + uv.json to {out_dir}")
    return {"atlases": len(atlases), "stats": stats, "out_dir": str(out_dir)}


def main():
    ap = argparse.ArgumentParser(description="Pack GNX mod sprites into per-mod atlases.")
    ap.add_argument("mod_dir", help="Path to mod folder (must contain strips/ subfolder).")
    ap.add_argument("--atlas-size", type=int, default=DEFAULT_ATLAS_SIZE)
    ap.add_argument("--padding", type=int, default=DEFAULT_PADDING)
    ap.add_argument("--dry-run", action="store_true", help="Compute stats without writing atlases.")
    args = ap.parse_args()

    mod_dir = Path(args.mod_dir)
    if not mod_dir.is_dir():
        print(f"ERROR: {mod_dir} is not a directory", file=sys.stderr)
        sys.exit(2)

    result = pack_mod(mod_dir, args.atlas_size, args.padding, args.dry_run)
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
