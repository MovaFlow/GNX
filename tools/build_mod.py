#!/usr/bin/env python3
"""
build_mod.py — GNX Mod Builder

Packs sprite strips and deploys a mod folder into the game's GNX_mods/ directory.

Usage:
    python build_mod.py <mod_dir> <game_dir> [--dry-run] [--force] [--skip-pack]

<mod_dir>  : mod source folder (manifest.json, classes.json/cells.json, sprites/)
<game_dir> : game install folder (contains the game executable; GNX_mods/ lives
             at <game_dir>/GNX_mods/, i.e. program_directory + "GNX_mods/")

Steps:
  1. Pack sprite strips: gnx_pack_strips.py <mod_dir> [--force] [--dry-run]
  2. Verify every "sprites" entry referenced by classes.json/cells.json has
     a "strip" key (warn on leftovers — these won't be deployed)
  3. Clean-rebuild <game_dir>/GNX_mods/<mod_id>/ from manifest.json,
     classes.json/cells.json (per manifest) and strips/
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PACK_STRIPS = Path(__file__).resolve().parent / "gnx_pack_strips.py"


def load_json_loose(path: Path):
    raw = path.read_text(encoding="utf-8")
    # GMS2 json_parse allows trailing commas; strip them before Python parsing
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    return json.loads(raw)


def find_unpacked(data) -> list[tuple[str, str]]:
    """Return [(entry_label, sprite_key), ...] for sprites with no 'strip' key."""
    leftovers = []

    def walk(obj, label=""):
        if isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, dict):
                    entry_label = item.get("name", item.get("class_id", item.get("h_type", f"[{i}]")))
                    walk(item, str(entry_label))
        elif isinstance(obj, dict):
            if "sprites" in obj and isinstance(obj["sprites"], dict):
                for key, val in obj["sprites"].items():
                    if isinstance(val, dict) and "frames" in val and "strip" not in val:
                        leftovers.append((label, key))
            for k, v in obj.items():
                if k != "sprites":
                    walk(v, label)

    walk(data)
    return leftovers


def run_pack_strips(mod_dir: Path, dry_run: bool, force: bool):
    if not PACK_STRIPS.exists():
        sys.exit(f"gnx_pack_strips.py not found: {PACK_STRIPS}")
    cmd = [sys.executable, str(PACK_STRIPS), str(mod_dir)]
    if dry_run:
        cmd.append("--dry-run")
    if force:
        cmd.append("--force")
    print("--- gnx_pack_strips.py ---")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"gnx_pack_strips.py failed (exit code {result.returncode})")
    print()


def main():
    parser = argparse.ArgumentParser(description="Pack and deploy a GNX mod into the game's GNX_mods/ folder.")
    parser.add_argument("mod_dir", help="Mod source folder (manifest.json, classes/cells.json, sprites/)")
    parser.add_argument("game_dir", help="Game install folder (contains the executable; GNX_mods/ is created there)")
    parser.add_argument("--dry-run", action="store_true", help="Write nothing, just show what would happen")
    parser.add_argument("--force", action="store_true", help="Repack all sprites (passed through to gnx_pack_strips.py)")
    parser.add_argument("--skip-pack", action="store_true", help="Skip gnx_pack_strips.py (strips/ already up to date)")
    args = parser.parse_args()

    mod_dir = Path(args.mod_dir).resolve()
    game_dir = Path(args.game_dir).resolve()

    if not mod_dir.is_dir():
        sys.exit(f"Mod folder not found: {mod_dir}")

    manifest_path = mod_dir / "manifest.json"
    if not manifest_path.exists():
        sys.exit(f"manifest.json not found in {mod_dir}")

    manifest = load_json_loose(manifest_path)
    mod_id = manifest.get("mod_id")
    if not mod_id:
        sys.exit("manifest.json: missing 'mod_id' field")
    if mod_id != mod_dir.name:
        print(f"WARN: mod_id '{mod_id}' != folder name '{mod_dir.name}' (mod_id is used as the folder name in mods/)")

    print(f"Mod: {manifest.get('name', mod_id)} v{manifest.get('version', '?')} (mod_id={mod_id})")
    print(f"Source: {mod_dir}")
    print(f"Game:   {game_dir}")
    if args.dry_run:
        print("Mode: DRY RUN (no files written)")
    print()

    # 1. Pack strips
    if not args.skip_pack:
        run_pack_strips(mod_dir, args.dry_run, args.force)

    # 2. Verify packing completeness
    print("--- Pack verification ---")
    leftovers = []
    json_files = {}
    for role in ("classes", "cells"):
        rel = manifest.get(role)
        if not rel:
            continue
        p = mod_dir / rel
        if not p.exists():
            print(f"WARN: {role}: file '{rel}' not found (referenced by manifest.json)")
            continue
        json_files[role] = (rel, p)
        data = load_json_loose(p)
        for label, key in find_unpacked(data):
            leftovers.append((rel, label, key))

    if leftovers:
        print("Sprites without a 'strip' key (not packed):")
        for rel, label, key in leftovers:
            print(f"  {rel} / {label} / {key}")
        print("-> these sprites will not be included in strips/. Re-run without --skip-pack, or check sprites/.")
    else:
        print("OK - every referenced sprite has a 'strip' key.")

    if not (mod_dir / "strips").is_dir():
        print("WARN: no strips/ folder in the mod - nothing to deploy on the sprite side.")
    print()

    # 3. Deploy
    dest = game_dir / "GNX_mods" / mod_id
    print(f"--- Deploying to {dest} (GNX_mods/) ---")

    files_to_copy = ["manifest.json"]
    for role, (rel, p) in json_files.items():
        files_to_copy.append(rel)

    if args.dry_run:
        if dest.exists():
            print(f"[dry] would remove {dest}")
        print(f"[dry] would create {dest}")
        for f in files_to_copy:
            print(f"[dry] would copy {f}")
        if (mod_dir / "strips").is_dir():
            n = len(list((mod_dir / "strips").glob("*.png")))
            print(f"[dry] would copy strips/ ({n} files)")
    else:
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        for f in files_to_copy:
            src = mod_dir / f
            dst = dest / f
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  copied: {f}")
        strips_src = mod_dir / "strips"
        if strips_src.is_dir():
            shutil.copytree(strips_src, dest / "strips")
            n = len(list((dest / "strips").glob("*.png")))
            print(f"  copied: strips/ ({n} files)")
    print()

    compat = manifest.get("compatible_game_versions", [])
    print(f"compatible_game_versions: {compat}")
    print("  -> must include the current game version (global.val.version), otherwise")
    print("     scr_gnx_load_mod silently skips the mod (see the 1.33 gotcha in CLAUDE.md).")

    print(f"\nDone.{' (dry run)' if args.dry_run else f' Mod deployed: {dest}'}")


if __name__ == "__main__":
    main()
