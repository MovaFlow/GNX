#!/usr/bin/env python3
"""
export_class_sprites.py

Original by @kazull. Extended with GNX feature coverage (SPECIAL_ICON_OFFSETS,
extract_icon helper, _c clothing variants, hand_c, non-fatal base body fallback).

Copies all sprites for a source class to a new target class name,
renaming folders and files. Also extracts the icon frames from the
shared spr_unit_icon_head sprite sheet, and copies ogre carry sprites.
Prints the full `sprites` JSON dict for classes.json when done.

Usage:
    python export_class_sprites.py \
        --src ranger --src-id 3 --dst witch \
        --sprites "GN Project/Sprites" \
        --output "mods/my_mod/sprites"

Vanilla class IDs (for icon frame offset = class_id * 3):
    0=Peasant  1=Cleric  2=Knight  3=Ranger  4=Nun     5=Samurai
    6=Mage     7=Warrior 8=Lilith  9=Cow    10=Nyx    11=Giant 12=Morrigan 13=Cat
"""

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image


# folder-suffix -> gnx key, when they differ
# All other suffixes: gnx key == folder suffix
SUFFIX_TO_KEY = {
    "idle_leg_part":       "idle_legp",
    "idle_leg_part_c":     "idle_legp_c",
    "loop_leg_part":       "loop_legp",
    "loop_leg_part_c":     "loop_legp_c",
    "big_start_leg_part":  "big_start_legp",
    "big_idle_leg_part":   "big_idle_legp",
    "big_loop_leg_part":   "big_loop_legp",
    "tent_idle_leg_part":  "tent_idle_legp",
    "tent_idle_leg_part_c": "tent_idle_legp_c",
    "tent_loop_leg_part":  "tent_loop_legp",
    "tent_loop_leg_part_c": "tent_loop_legp_c",
    "tent_birth_leg_part": "tent_birth_legp",
    "tent_birth_leg_part_c": "tent_birth_legp_c",
    "tent_idle_leg_v1":    "tent_idle_leg_1",
    "tent_idle_leg_v2":    "tent_idle_leg_2",
    "tent_loop_leg_v1":    "tent_loop_leg_1",
    "tent_loop_leg_v2":    "tent_loop_leg_2",
    "tent_birth_leg_v1":   "tent_birth_leg_1",
    "tent_birth_leg_v2":   "tent_birth_leg_2",
}

# Special class names and their icon offsets (1 frame each)
SPECIAL_ICON_OFFSETS = {
    "lilith": 24, "cow": 25, "nyx": 26,
    "giant": 27, "morrigan": 28, "cat": 29,
}


def copy_sprite_folder(src_folder: Path, dst_folder: Path, src_prefix: str, dst_prefix: str):
    """Copy all PNGs from src_folder to dst_folder, renaming src_prefix -> dst_prefix."""
    dst_folder.mkdir(parents=True, exist_ok=True)
    copied = 0
    for png in sorted(src_folder.glob("*.png")):
        new_name = png.name.replace(src_prefix, dst_prefix, 1)
        shutil.copy2(png, dst_folder / new_name)
        copied += 1
    return copied


def frame_height(folder: Path, prefix: str) -> int:
    """Read height of the first frame in a sprite folder."""
    pngs = sorted(folder.glob("*.png"))
    if not pngs:
        return 90
    try:
        return Image.open(pngs[0]).size[1]
    except Exception:
        return 90


def frame_count(folder: Path) -> int:
    return len(list(folder.glob("*.png")))


def build_sprite_entry(
    gnx_key: str,
    dst_name: str,
    folder_name: str,
    frames: int,
    xorig: int,
    yorig: int,
    canvas_w: int = None,
    canvas_h: int = None,
) -> dict:
    entry = {
        "strip": f"strips/{dst_name}.png",
        "frames": frames,
        "xorig": xorig,
        "yorig": yorig,
    }
    if canvas_w is not None:
        entry["canvas_w"] = canvas_w
        entry["canvas_h"] = canvas_h
    if folder_name != dst_name:
        entry["folder"] = folder_name
    return entry


def extract_icon(sprites_dir, src_name, dst_name, out_dir, src_id, icon_type="head"):
    """Extract icon frames from shared sprite sheet. Returns (entry, count) or None."""
    icon_src = sprites_dir / f"spr_unit_icon_{icon_type}"
    if not icon_src.is_dir():
        print(f"  WARNING: spr_unit_icon_{icon_type} not found - icon {icon_type} not extracted")
        return None

    src_lower = src_name.lower()
    if src_lower in SPECIAL_ICON_OFFSETS:
        offset = SPECIAL_ICON_OFFSETS[src_lower]
        n_frames = 1
    else:
        offset = src_id * 3
        n_frames = 3

    icon_dst_name = f"spr_unit_icon_{dst_name}_{icon_type}"
    icon_dst = out_dir / icon_dst_name
    icon_dst.mkdir(parents=True, exist_ok=True)

    ok = 0
    for i in range(n_frames):
        src_frame = icon_src / f"spr_unit_icon_{icon_type}_{offset + i}.png"
        dst_frame = icon_dst / f"{icon_dst_name}_{i}.png"
        if src_frame.exists():
            shutil.copy2(src_frame, dst_frame)
            ok += 1
        else:
            print(f"  WARNING: icon {icon_type} frame not found: {src_frame}")

    print(f"  spr_unit_icon_{icon_type}[{offset}-{offset+n_frames-1}] -> {icon_dst_name} ({ok} frames)")

    if ok == 0:
        return None

    w, h = Image.open(icon_dst / f"{icon_dst_name}_0.png").size
    entry = build_sprite_entry(
        f"icon_{icon_type}", icon_dst_name, icon_dst_name,
        frames=ok, xorig=10, yorig=13,
        canvas_w=w, canvas_h=h,
    )
    return entry, ok


def main():
    parser = argparse.ArgumentParser(description="Copy + rename class sprites.")
    parser.add_argument("--src",     required=True, help="Source class name, e.g. ranger")
    parser.add_argument("--src-id",  required=True, type=int, help="Source class_id (for icon offset)")
    parser.add_argument("--dst",     required=True, help="Target class name, e.g. witch")
    parser.add_argument("--sprites", required=True, type=Path, help="Path to UMT Sprites/ folder")
    parser.add_argument("--output",  required=True, type=Path, help="Destination sprites/ folder")
    args = parser.parse_args()

    # If src is mage/shaman and folder is big/standard,tent then swap to shaman/mage
    if args.src in {"mage", "shaman"}:
        print(f"  WARNING: --src {args.src} sprites are split between mage and shaman names, so run twice with both values to get all sprites.")

    src_prefix = f"spr_h_{args.src}"
    dst_prefix = f"spr_h_{args.dst}"
    sprites_dir = args.sprites
    out_dir = args.output

    out_dir.mkdir(parents=True, exist_ok=True)

    sprites_json = {}
    total_copied = 0

    # Body sprites
    src_folders = sorted(sprites_dir.glob(f"{src_prefix}_*"))
    if not src_folders:
        print(f"ERROR: No folders matching {src_prefix}_* in {sprites_dir}")
        return

    for src_folder in src_folders:
        if not src_folder.is_dir():
            continue

        suffix = src_folder.name[len(src_prefix) + 1:]
        dst_name = f"{dst_prefix}_{suffix}"
        dst_folder = out_dir / dst_name

        n = copy_sprite_folder(src_folder, dst_folder, src_prefix, dst_prefix)
        total_copied += n

        gnx_key = SUFFIX_TO_KEY.get(suffix, suffix)
        frames = frame_count(dst_folder)

        if suffix in ("hand", "hand_c"):
            entry = build_sprite_entry(gnx_key, dst_name, dst_name, frames, xorig=3, yorig=1)
        else:
            h = frame_height(dst_folder, dst_prefix)
            entry = build_sprite_entry(gnx_key, dst_name, dst_name, frames, xorig=0, yorig=h)

        if gnx_key != suffix:
            entry["folder"] = dst_name

        sprites_json[gnx_key] = entry
        print(f"  {src_folder.name} -> {dst_folder.name} ({n} frames)")


    # GB1 Breast sprites
    if args.src.lower() in SPECIAL_ICON_OFFSETS:
        gnx_key = "gb1_blb"
        gb1_prefix = f"spr_h_gb_1_big_loop_breast"
        gb1_src_name = f"{gb1_prefix}_{args.src}"
        gb1_src = sprites_dir / gb1_src_name
        if gb1_src.is_dir():
            gb1_dst_name = f"{gb1_prefix}_{args.dst}"
            gb1_dst = out_dir / gb1_dst_name
            n = copy_sprite_folder(gb1_src, gb1_dst, gb1_src_name, gb1_dst_name)
            total_copied += n
            frames = frame_count(gb1_dst)
            h = frame_height(gb1_dst, gb1_dst_name)
            entry = build_sprite_entry(gnx_key, gb1_dst_name, gb1_dst_name, frames, xorig=0, yorig=h)
            entry["folder"] = gb1_dst_name
            sprites_json[gnx_key] = entry
            print(f"  {gb1_src_name} -> {gb1_dst_name} ({n} frames)")
        else:
            print(f"  WARNING: No folders matching {gb1_src_name} - skipped")


    # Special Class Base Body sprites
    if args.src.lower() in SPECIAL_ICON_OFFSETS:
        base_src_prefix = f"spr_h_base"
        src_folders = sorted(sprites_dir.glob(f"{base_src_prefix}_*_{args.src}"))
        if not src_folders:
            print(f"  INFO: No base body folders matching {base_src_prefix}_*_{args.src}")

        for src_folder in src_folders:
            if not src_folder.is_dir():
                continue

            suffix = src_folder.name[len(base_src_prefix) + 1:-(len(args.src)+1)]
            dst_name = f"{dst_prefix}_{suffix}"
            dst_folder = out_dir / dst_name

            n = copy_sprite_folder(src_folder, dst_folder, base_src_prefix, dst_prefix)
            total_copied += n

            gnx_key = SUFFIX_TO_KEY.get(suffix, suffix)
            frames = frame_count(dst_folder)

            if suffix == "hand":
                entry = build_sprite_entry(gnx_key, dst_name, dst_name, frames, xorig=3, yorig=1)
            else:
                h = frame_height(dst_folder, dst_prefix)
                entry = build_sprite_entry(gnx_key, dst_name, dst_name, frames, xorig=0, yorig=h)

            if gnx_key != suffix:
                entry["folder"] = dst_name

            sprites_json[gnx_key] = entry
            print(f"  {src_folder.name} -> {dst_folder.name} ({n} frames)")



    # Icon head
    result = extract_icon(sprites_dir, args.src, args.dst, out_dir, args.src_id, "head")
    if result:
        entry, ok = result
        sprites_json["icon_head"] = entry
        total_copied += ok

    # Icon hair
    result = extract_icon(sprites_dir, args.src, args.dst, out_dir, args.src_id, "hair")
    if result:
        entry, ok = result
        sprites_json["icon_hair"] = entry
        total_copied += ok

    # Ogre carry sprites
    for carry_suffix, gnx_key in [("head", "carry_head"), ("hair", "carry_hair"), ("base", "carry_base")]:
        carry_src_name = f"spr_ogre_carry_{carry_suffix}_{args.src}"
        carry_src = sprites_dir / carry_src_name
        if not carry_src.is_dir():
            print(f"  WARNING: {carry_src_name} not found - carry sprite skipped")
            continue
        carry_dst_name = f"spr_ogre_carry_{carry_suffix}_{args.dst}"
        carry_dst = out_dir / carry_dst_name
        n = copy_sprite_folder(carry_src, carry_dst, carry_src_name, carry_dst_name)
        total_copied += n
        frames = frame_count(carry_dst)
        h = frame_height(carry_dst, carry_dst_name)
        sprites_json[gnx_key] = build_sprite_entry(
            gnx_key, carry_dst_name, carry_dst_name, frames, xorig=0, yorig=h
        )
        print(f"  {carry_src_name} -> {carry_dst_name} ({n} frames)")

    print(f"\nDone. {total_copied} files copied to {out_dir}")
    print(f"      {len(sprites_json)} sprite slots exported.\n")
    print("Next: run scaffold_class.py to generate the full classes.json entry:")
    dst_prefix_hint = f"spr_h_{args.dst}"
    mod_dir_hint = str(args.output.parent)
    print(f"  python scaffold_class.py --name \"{args.dst.title()}\" "
          f"--prefix {dst_prefix_hint} --mod-dir \"{mod_dir_hint}\"")


if __name__ == "__main__":
    main()
