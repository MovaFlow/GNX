#!/usr/bin/env python3
"""
gnx_pack_strips.py — GNX Mod Strip Packer
Converts per-frame PNG arrays in mod JSON files into horizontal sprite strips.
GMS2 loads a strip with one sprite_add call instead of one per frame.

Usage:
    python gnx_pack_strips.py <mod_dir>
    python gnx_pack_strips.py <mod_dir> --dry-run

Modifies classes.json and cells.json in-place.
Original files are backed up as *.json.bak before modification.
Strips are written to <mod_dir>/strips/.
"""

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path


def natural_sort_key(p: Path) -> list:
    """Sort path by embedded integers so frame_9 < frame_10."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.stem)]

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")


def find_json_files(mod_dir: Path, manifest: dict) -> dict[str, Path]:
    """Return {role: path} for cells and classes JSON files listed in manifest."""
    found = {}
    for role in ("cells", "classes"):
        if role in manifest:
            p = mod_dir / manifest[role]
            if p.exists():
                found[role] = p
    return found


def pack_sprite_strip(frames: list[str], mod_dir: Path, strips_dir: Path,
                      key: str, dry_run: bool,
                      canvas_w: int | None = None,
                      canvas_h: int | None = None) -> tuple[str, int] | None:
    """
    Pack a list of frame PNG paths into a horizontal strip.
    Returns (strip_relative_path, frame_count) or None on error.
    Frame paths are relative to mod_dir.
    """
    abs_frames = [mod_dir / f for f in frames]

    # Verify all frames exist
    missing = [str(p) for p in abs_frames if not p.exists()]
    if missing:
        print(f"  WARN [{key}]: missing frames, skipping: {missing[:3]}{'...' if len(missing) > 3 else ''}")
        return None

    if dry_run:
        # Just report what would be done
        img0 = Image.open(abs_frames[0])
        w, h = img0.size
        img0.close()
        strip_path = strips_dir / f"{key}.png"
        rel = strip_path.relative_to(mod_dir).as_posix()
        print(f"  [dry] {key}: {len(frames)} frames {w}x{h} → strips/{key}.png ({w * len(frames)}x{h})")
        return rel, len(frames)

    # Load all frames
    imgs = [Image.open(p).convert("RGBA") for p in abs_frames]
    w, h = imgs[0].size

    # Validate all frames are the same size
    for i, img in enumerate(imgs[1:], 1):
        if img.size != (w, h):
            print(f"  WARN [{key}]: frame {i} size {img.size} != frame 0 size {(w, h)}, skipping")
            for im in imgs:
                im.close()
            return None

    # Pad to canvas_w x canvas_h if specified (top-left anchor)
    if canvas_w is not None or canvas_h is not None:
        cw = canvas_w if canvas_w is not None else w
        ch = canvas_h if canvas_h is not None else h
        if (w, h) != (cw, ch):
            if w > cw or h > ch:
                print(f"  WARN [{key}]: frame {w}x{h} exceeds canvas {cw}x{ch}, skipping pad")
            else:
                padded = []
                for img in imgs:
                    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
                    canvas.paste(img, (0, 0))
                    img.close()
                    padded.append(canvas)
                imgs = padded
                print(f"  padded: {key} {w}x{h} → {cw}x{ch}")
                w, h = cw, ch

    # Build horizontal strip
    strip = Image.new("RGBA", (w * len(imgs), h), (0, 0, 0, 0))
    for i, img in enumerate(imgs):
        strip.paste(img, (i * w, 0))
        img.close()

    strip_path = strips_dir / f"{key}.png"
    strip.save(strip_path, "PNG", optimize=False, compress_level=1)
    strip.close()

    rel = strip_path.relative_to(mod_dir).as_posix()
    return rel, len(frames)


def process_sprites_dict(sprites: dict, mod_dir: Path, strips_dir: Path,
                         dry_run: bool, sprite_prefix: str = "",
                         sprite_suffix: str = "",
                         force: bool = False) -> tuple[dict, int, int]:
    """
    Process a sprites dict, converting frame arrays to strips.
    sprite_prefix: default prefix prepended to key (e.g. "spr_h_goblin").
    sprite_suffix: default suffix appended to key (e.g. "_alpha_test").
    Per-entry "prefix"/"suffix" fields override the cell-level defaults.
    force: re-pack even if a strip entry already exists (re-discovers from sprites/ folder).
    Returns (updated_sprites, packed_count, skipped_count).
    """
    updated = {}
    packed = skipped = 0

    for key, val in sprites.items():
        if not isinstance(val, dict):
            updated[key] = val
            continue

        frames = val.get("frames")

        # --force: treat already-packed entries as needing re-discovery
        if force and ("strip" in val or not isinstance(frames, list)):
            frames = None

        # Auto-discover frames if no explicit list or strip
        strip_name = key  # default; overridden below when folder_name is derived
        if frames is None and (force or "strip" not in val):
            # Per-entry prefix/suffix override cell-level defaults
            pfx = val.get("prefix", sprite_prefix)
            sfx = val.get("suffix", sprite_suffix)
            folder_name = val.get("folder") or (f"{pfx}_{key}{sfx}" if pfx else f"{key}{sfx}")
            strip_name = folder_name  # unique per class when prefix differs
            sprite_dir = mod_dir / "sprites" / folder_name
            if sprite_dir.is_dir():
                discovered = sorted(sprite_dir.glob("*.png"), key=natural_sort_key)
                if discovered:
                    frames = [str(p.relative_to(mod_dir).as_posix()) for p in discovered]
                    print(f"  auto: {key} → {len(frames)} frames from sprites/{folder_name}/")
                else:
                    print(f"  WARN [{key}]: sprites/{folder_name}/ exists but no PNGs found — skipping")
                    updated[key] = val
                    skipped += 1
                    continue
            else:
                print(f"  WARN [{key}]: no folder found (tried sprites/{folder_name}/) — skipping")
                updated[key] = val
                skipped += 1
                continue

        if not isinstance(frames, list) or len(frames) == 0:
            updated[key] = val
            continue

        result = pack_sprite_strip(frames, mod_dir, strips_dir, strip_name, dry_run,
                                   canvas_w=val.get("canvas_w"),
                                   canvas_h=val.get("canvas_h"))
        if result is None:
            updated[key] = val
            skipped += 1
        else:
            strip_path, frame_count = result
            new_val = {"strip": strip_path, "frames": frame_count}
            for field in ("xorig", "yorig", "canvas_w", "canvas_h", "folder"):
                if field in val:
                    new_val[field] = val[field]
            updated[key] = new_val
            packed += 1
            if not dry_run:
                print(f"  packed: {key} ({frame_count} frames → {strip_path})")

    return updated, packed, skipped


def process_json_file(json_path: Path, mod_dir: Path, strips_dir: Path,
                      dry_run: bool, force: bool = False,
                      global_suffix: str = "") -> tuple[int, int]:
    """
    Load a JSON file (array or object), find all sprites dicts, pack strips.
    Backs up original and writes updated file.
    Returns (total_packed, total_skipped).
    """
    print(f"\nProcessing: {json_path.name}")

    with open(json_path, encoding="utf-8") as f:
        raw = f.read()
    # GMS2 json_parse allows trailing commas; strip them before Python parsing
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    data = json.loads(raw)

    total_packed = total_skipped = 0

    def walk(obj):
        nonlocal total_packed, total_skipped
        if isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, dict) and "sprites" in item and isinstance(item["sprites"], dict):
                    label = item.get("name", item.get("id", f"[{i}]"))
                    prefix = item.get("sprite_prefix", "")
                    print(f"  Entry: {label}" + (f" (prefix: {prefix})" if prefix else ""))
                    suffix = item.get("sprite_suffix", global_suffix)
                    updated, p, s = process_sprites_dict(
                        item["sprites"], mod_dir, strips_dir, dry_run, prefix, suffix, force)
                    item["sprites"] = updated
                    total_packed += p
                    total_skipped += s
                elif isinstance(item, dict):
                    walk(item)
        elif isinstance(obj, dict):
            if "sprites" in obj and isinstance(obj["sprites"], dict):
                prefix = obj.get("sprite_prefix", "")
                suffix = obj.get("sprite_suffix", global_suffix)
                updated, p, s = process_sprites_dict(
                    obj["sprites"], mod_dir, strips_dir, dry_run, prefix, suffix, force)
                obj["sprites"] = updated
                total_packed += p
                total_skipped += s
            else:
                for v in obj.values():
                    walk(v)

    walk(data)

    if not dry_run:
        # Fix 3: timestamped backup so re-runs don't overwrite the original
        bak = json_path.with_suffix(f".{int(time.time())}.json.bak")
        shutil.copy2(json_path, bak)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent="\t", ensure_ascii=False)
        print(f"  Saved. Backup: {bak.name}")

    return total_packed, total_skipped


def strip_frames_from_file(json_path: Path):
    """Remove frames arrays from all sprite defs, leaving only origins/canvas fields."""
    with open(json_path, encoding="utf-8") as f:
        raw = f.read()
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    data = json.loads(raw)

    keep = {"xorig", "yorig", "canvas_w", "canvas_h", "folder"}  # fix 1: preserve folder
    count = 0

    def walk(obj):
        nonlocal count
        if isinstance(obj, list):
            for item in obj:
                walk(item)
        elif isinstance(obj, dict):
            if "sprites" in obj and isinstance(obj["sprites"], dict):
                for key, val in obj["sprites"].items():
                    if isinstance(val, dict) and "frames" in val and isinstance(val["frames"], list):
                        obj["sprites"][key] = {k: v for k, v in val.items() if k in keep}
                        count += 1
            for v in obj.values():
                walk(v)

    walk(data)
    import time
    bak = json_path.with_suffix(f".{int(time.time())}.json.bak")
    shutil.copy2(json_path, bak)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent="\t", ensure_ascii=False)
    print(f"Stripped {count} sprite frame lists from {json_path.name} (backup: {bak.name})")


def main():
    parser = argparse.ArgumentParser(description="Pack mod sprite frames into GMS2 strips.")
    parser.add_argument("mod_dir", help="Path to mod folder (contains manifest.json)")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing files")
    parser.add_argument("--force", action="store_true",
                        help="Re-pack all sprites, including already-packed entries (re-discovers from sprites/ folder)")
    parser.add_argument("--suffix", default="",
                        help="Global sprite_suffix appended to auto-discovered folder names (e.g. '_test'). "
                             "Overridden by sprite_suffix in JSON or suffix per entry.")
    parser.add_argument("--strip-frames", metavar="JSON_FILE",
                        help="Remove frames arrays from a source JSON file and exit")
    args = parser.parse_args()

    if args.strip_frames:
        strip_frames_from_file(Path(args.strip_frames).resolve())
        return

    mod_dir = Path(args.mod_dir).resolve()
    if not mod_dir.is_dir():
        sys.exit(f"Not a directory: {mod_dir}")

    manifest_path = mod_dir / "manifest.json"
    if not manifest_path.exists():
        sys.exit(f"manifest.json not found in {mod_dir}")

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Mod: {manifest.get('name', mod_dir.name)} v{manifest.get('version', '?')}")
    print(f"Dir: {mod_dir}")
    if args.dry_run:
        print("Mode: DRY RUN (no files written)\n")

    json_files = find_json_files(mod_dir, manifest)
    if not json_files:
        # Fallback: scan for cells.json / classes.json directly
        for name in ("cells.json", "classes.json"):
            p = mod_dir / name
            if p.exists():
                role = name.replace(".json", "")
                json_files[role] = p

    if not json_files:
        sys.exit("No cells.json or classes.json found (check manifest keys 'cells'/'classes').")

    strips_dir = mod_dir / "strips"
    if not args.dry_run:
        strips_dir.mkdir(exist_ok=True)

    total_packed = total_skipped = 0
    for role, path in json_files.items():
        p, s = process_json_file(path, mod_dir, strips_dir, args.dry_run, args.force, args.suffix)
        total_packed += p
        total_skipped += s

    print(f"\nDone. Packed: {total_packed} sprites | Skipped: {total_skipped}")
    if total_packed:
        print("Next: update GML loader to use strip format (gnx_resolve_sprite).")


if __name__ == "__main__":
    main()
