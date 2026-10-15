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


CONDITION_TYPES = {"state_equals", "state_gte", "state_lte", "stage_discovered", "stage_cleared", "boss_captured",
                   "cell_built", "cell_occupied", "unit_count", "raid_won", "gold_gte", "floor_gte", "cell_count"}


def check_map(manifest, mod_dir):
    """Problems in a map mod's manifest (map / map_info / map_start), as (level, message); level ERROR means
    the loader ignores or rejects the part, WARN means it loads but probably not as intended."""
    out = []
    if "map_info" in manifest and "map_button" in manifest:
        out.append(("WARN", "both map_info and map_button (its old name): map_info is used"))
    if "map_info" in manifest or "map_button" in manifest:  # map_button = the old name of map_info, still read
        manifest = dict(manifest, map_button=manifest.get("map_info", manifest.get("map_button")))
    has_btn, has_start = "map_button" in manifest, "map_start" in manifest
    mp = manifest.get("map")
    if not (has_btn or has_start or mp):
        return out
    if (has_btn or has_start) and not mp:
        return [("ERROR", "map_info / map_start need a \"map\" id; without it the mod is not a map mod")]
    if not isinstance(mp, str) or not mp:
        return [("ERROR", f"map must be a non-empty string, got {mp!r}")]
    if mp in ("vanilla", "all") and (has_btn or has_start):
        out.append(("ERROR", f"map '{mp}' is reserved: map_info / map_start are ignored for it"))
    if mp not in ("vanilla", "all") and not has_btn:
        out.append(("WARN", f"map '{mp}' has no map_info: players can only reach it if another mod adds one"))
    mb = manifest.get("map_button", {})
    if has_btn:
        if not isinstance(mb, dict):
            return out + [("ERROR", "map_info must be an object")]
        if "x" in mb or "y" in mb:
            out.append(("WARN", "map_info.x / y are ignored since GNX 1.4.8: maps are reached from the travel "
                                "menu (the map button in the world map's corner)"))
        if "travel" in mb and mb["travel"] not in ("simple", "advanced", "complex"):
            out.append(("ERROR", f"map_info.travel must be simple, advanced or complex, got {mb['travel']!r}"))
        if "map_sprite" in mb and not (mod_dir / "sprites" / mb["map_sprite"]).is_file():
            out.append(("WARN", f"map_info.map_sprite: sprites/{mb['map_sprite']} not found (the default button is used)"))
        if "unlock" in mb:
            conds = mb["unlock"] if isinstance(mb["unlock"], list) else [mb["unlock"]]
            for c in conds:
                if not isinstance(c, dict) or "type" not in c:
                    out.append(("ERROR", f"map_info.unlock: each condition needs a \"type\", got {c!r}"))
                elif c["type"] not in CONDITION_TYPES:
                    out.append(("ERROR", f"map_info.unlock: unknown condition type '{c['type']}' "
                                         f"(known: {', '.join(sorted(CONDITION_TYPES))})"))
    ms = manifest.get("map_start")
    if has_start:
        if not isinstance(ms, dict):
            return out + [("ERROR", "map_start must be an object")]
        for k in ("floors", "money", "food", "mood", "goblins"):
            if k in ms and not isinstance(ms[k], (int, float)):
                out.append(("ERROR", f"map_start.{k} must be a number, got {ms[k]!r}"))
        floors = ms.get("floors", 0) if isinstance(ms.get("floors", 0), (int, float)) else 0
        for i, c in enumerate(ms.get("cells", [])):
            if not isinstance(c, dict) or "h_type" not in c:
                out.append(("ERROR", f"map_start.cells[{i}]: needs an h_type"))
                continue
            if not isinstance(c["h_type"], (int, str)):
                out.append(("ERROR", f"map_start.cells[{i}].h_type must be a number or \"mod.CELL NAME\", "
                                     f"got {c['h_type']!r}"))
            fl = c.get("floor", 0)
            if not isinstance(fl, int) or not 0 <= fl <= floors:
                out.append(("ERROR", f"map_start.cells[{i}].floor {fl!r}: the map has floors 0..{floors} "
                                     f"(map_start.floors adds floors on top of floor 0); the cell is skipped"))
        mon_types = ("goblin", "hobgoblin", "tentacle", "ogre")
        for i, t in enumerate(ms.get("troops", [])):
            if not isinstance(t, dict) or "type" not in t or "num" not in t:
                out.append(("ERROR", f"map_start.troops[{i}]: needs a type and a num"))
                continue
            if t["type"] not in mon_types and t["type"] not in (0, 1, 2, 3):
                out.append(("ERROR", f"map_start.troops[{i}].type {t['type']!r}: use {', '.join(mon_types)} "
                                     f"(or 0-3); the entry is skipped"))
            if not isinstance(t.get("kind", 0), int) or not 0 <= t.get("kind", 0) <= 3:
                out.append(("ERROR", f"map_start.troops[{i}].kind {t.get('kind')!r}: 0-3"))
        for i, p in enumerate(ms.get("prisoners", [])):
            if not isinstance(p, dict) or "class" not in p:
                out.append(("ERROR", f"map_start.prisoners[{i}]: needs a class (a number or \"mod.NAME\")"))
        for i, u in enumerate(ms.get("unlock_cells", [])):
            if not isinstance(u, (int, str)):
                out.append(("ERROR", f"map_start.unlock_cells[{i}] must be an h_type or \"mod.CELL NAME\", got {u!r}"))
    return out


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
    for role in ("classes", "cells", "quests", "tools", "sounds", "props"):
        rel = manifest.get(role)
        if not rel:
            continue
        p = mod_dir / rel
        if not p.exists():
            print(f"WARN: {role}: file '{rel}' not found (referenced by manifest.json)")
            continue
        json_files[role] = (rel, p)
        if role not in ("classes", "cells"):
            continue  # only classes/cells reference packed sprites
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

    # 2b. Map mod checks
    probs = check_map(manifest, mod_dir)
    if probs or manifest.get("map"):
        print("--- Map mod checks ---")
        for level, msg in probs:
            print(f"{level}: {msg}")
        if not probs:
            print(f"OK - map '{manifest['map']}'")
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
        for folder in ("strips", "atlas", "sounds", "portraits"):
            if (mod_dir / folder).is_dir():
                n = sum(1 for f in (mod_dir / folder).rglob("*") if f.is_file())
                print(f"[dry] would copy {folder}/ ({n} files)")
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
        mi = manifest.get("map_info", manifest.get("map_button"))  # map_button = old name of map_info
        ms_name = mi.get("map_sprite") if isinstance(mi, dict) else None
        if ms_name and (mod_dir / "sprites" / ms_name).is_file():  # the world-map image is loaded from sprites/
            (dest / "sprites").mkdir(exist_ok=True)
            shutil.copy2(mod_dir / "sprites" / ms_name, dest / "sprites" / ms_name)
            print(f"  copied: sprites/{ms_name}")
        for folder in ("strips", "atlas", "sounds", "portraits"):  # everything the loader reads from the mod folder
            src_dir = mod_dir / folder
            if src_dir.is_dir():
                shutil.copytree(src_dir, dest / folder)
                n = sum(1 for f in (dest / folder).rglob("*") if f.is_file())
                print(f"  copied: {folder}/ ({n} files)")
    print()

    compat = manifest.get("compatible_game_versions", [])
    print(f"compatible_game_versions: {compat}")
    print("  -> must include the current game version (global.val.version), otherwise")
    print("     scr_gnx_load_mod silently skips the mod (see compatible_game_versions in docs/GNX_MODDING.md).")

    print(f"\nDone.{' (dry run)' if args.dry_run else f' Mod deployed: {dest}'}")


if __name__ == "__main__":
    main()
