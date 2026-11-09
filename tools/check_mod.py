#!/usr/bin/env python3
"""Check a GNX mod's JSON files against the schemas in tools/schemas/.

    python tools/check_mod.py <mod_dir> [<mod_dir> ...]

Reads manifest.json, then every data file it names (classes, cells, quests, tools,
sounds, props, items) and lang/*.json. Prints one line per problem:

    <file>: <path.to.key>: <problem>

Unknown keys are usually typos: GNX skips them without a word, so the setting they
were meant for silently does not apply. A few places decide what a mod IS (the top
level of manifest.json, of a class entry or of a cell entry: override, h_type, map...);
an unknown key there is "blocking" and build_mod.py refuses to deploy unless --force.

Exit code: 0 = clean, 1 = warnings only, 2 = blocking problems (or unreadable files).
Needs the jsonschema package (pip install jsonschema); without it the check is skipped.
"""
import argparse
import json
import sys
from pathlib import Path, PurePosixPath

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"

# manifest key -> schema name
DATA_KEYS = ["classes", "cells", "quests", "tools", "sounds", "props", "items", "raids"]


def load_json(path: Path):
    # the game's json_parse accepts trailing commas ([1, 2,]); so does this check
    raw = path.read_text(encoding="utf-8-sig")
    try:
        return json.loads(raw)
    except ValueError:
        import re
        return json.loads(re.sub(r",(\s*[}\]])", r"\1", raw))


def schema_for(kind: str):
    p = SCHEMA_DIR / f"{kind}.schema.json"
    return load_json(p) if p.exists() else None


def validator_for(schema, jsonschema):
    """A Draft 7 validator for which "common.schema.json#/..." references resolve to tools/schemas/, offline.
    jsonschema 4.18+ takes a registry; older versions a RefResolver with a store."""
    schemas = [load_json(p) for p in SCHEMA_DIR.glob("*.schema.json")]
    try:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT7
    except ImportError:
        resolver = jsonschema.RefResolver(schema["$id"], schema, store={s["$id"]: s for s in schemas})
        return jsonschema.Draft7Validator(schema, resolver=resolver)
    reg = Registry().with_resources((s["$id"], Resource.from_contents(s, default_specification=DRAFT7)) for s in schemas)
    return jsonschema.Draft7Validator(schema, registry=reg)


def fmt_path(err) -> str:
    out = ""
    for part in err.absolute_path:
        out += f"[{part}]" if isinstance(part, int) else (("." if out else "") + str(part))
    return out or "(top)"


def is_blocking(kind: str, err) -> bool:
    """An unknown key where it decides what the mod or an entry is."""
    if err.validator != "additionalProperties":
        return False
    path = list(err.absolute_path)
    if kind == "manifest":
        return len(path) == 0
    if kind in ("classes", "cells"):
        # a list of entries, or { "classes": [...] } / { "cells": [...] }
        return (len(path) == 1 and isinstance(path[0], int)) or (len(path) == 2 and isinstance(path[1], int))
    return False


def check_file(path: Path, kind: str, jsonschema, report):
    schema = schema_for(kind)
    if schema is None:
        return
    try:
        data = load_json(path)
    except (OSError, ValueError) as e:
        report(path, "(file)", f"cannot be read as JSON: {e}", True)
        return
    validator = validator_for(schema, jsonschema)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(map(str, e.absolute_path))):
        report(path, fmt_path(err), message(err), is_blocking(kind, err))


def message(err) -> str:
    """jsonschema's wording, except for unknown keys: name them and the keys that exist there."""
    if err.validator != "additionalProperties" or not isinstance(err.instance, dict):
        return err.message
    import re
    known = list(err.schema.get("properties", {}))
    patterns = list(err.schema.get("patternProperties", {}))
    unknown = [k for k in err.instance if k not in known and not any(re.search(p, k) for p in patterns)]
    hint = f" (known here: {', '.join(known)})" if known and len(known) <= 40 else ""
    return f"unknown key{'s' if len(unknown) > 1 else ''} {', '.join(repr(k) for k in unknown)}: GNX ignores it{hint}"


def art_file_name(v):
    """The file or folder a sprite entry names, looked up in the order GNX does it for an atlas (gnx_atlas_resolve_ref)."""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        for k in ("strip", "path"):
            if isinstance(v.get(k), str):
                return v[k]
        if isinstance(v.get("frames"), list) and v["frames"] and isinstance(v["frames"][0], str):
            return v["frames"][0]
        if isinstance(v.get("folder"), str):
            return v["folder"]
    return None


def world_atlas_clashes(art, mod_dir: Path):
    """[(path, file name, atlas entry)] for every monster_art world file whose base name is an entry of the mod's atlas.
    GNX looks a sprite up in the atlas by base name first, so the atlas art is drawn and the file is never read."""
    try:
        entries = load_json(mod_dir / "atlas" / "uv.json").get("entries")
    except (OSError, ValueError, AttributeError):
        return []
    if not isinstance(entries, dict) or not isinstance(art, dict):
        return []
    atlas = {k.lower(): k for k in entries}  # file names ignore case on Windows, GNX compares both ways
    out = []
    for mon, block in art.items():
        world = block.get("world") if isinstance(block, dict) and mon != "sprites" else None
        for part, v in (world.items() if isinstance(world, dict) else []):
            name = None if part.startswith(("_", "//")) else art_file_name(v)
            entry = atlas.get(PurePosixPath(name.replace("\\", "/")).stem.lower()) if name else None
            if entry:
                out.append((f"monster_art.{mon}.world.{part}", name, entry))
    return out


def check_mod(mod_dir: Path, jsonschema, report):
    manifest = mod_dir / "manifest.json"
    if not manifest.exists():
        report(manifest, "(file)", "missing: a mod folder needs a manifest.json", True)
        return
    check_file(manifest, "manifest", jsonschema, report)
    try:
        m = load_json(manifest)
    except (OSError, ValueError):
        return
    for key in DATA_KEYS:
        rel = m.get(key) if isinstance(m, dict) else None
        if isinstance(rel, str):
            p = mod_dir / rel
            if p.exists():
                check_file(p, key, jsonschema, report)
            else:
                report(manifest, key, f"names '{rel}', which does not exist (GNX logs a mod error and loads the rest)", False)
    art, art_src = (m.get("monster_art") if isinstance(m, dict) else None), manifest
    if isinstance(art, str):
        art_src = mod_dir / art
        if art_src.exists():
            try:
                art = load_json(art_src)
            except (OSError, ValueError) as e:
                report(art_src, "(file)", f"cannot be read as JSON: {e}", True)
                art = None
            if art is not None and not isinstance(art, dict):
                report(art_src, "(top)", "monster_art must be a JSON object of monster -> art (GNX logs a mod error and loads the art of nothing)", True)
                art = None
        else:
            report(manifest, "monster_art", f"names '{art}', which does not exist (GNX logs a mod error and loads the rest)", False)
            art = None
    for where, name, entry in world_atlas_clashes(art, mod_dir):
        report(art_src, where, f"'{name}' has the base name of atlas entry '{entry}': GNX takes the atlas art, and the file is only a fallback when the atlas has another frame count (rename one of them)", False)
    for p in sorted((mod_dir / "lang").glob("*.json")):
        check_file(p, "lang", jsonschema, report)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mods", nargs="+", type=Path)
    ap.add_argument("--quiet", action="store_true", help="print only the summary line")
    args = ap.parse_args(argv)

    try:
        import jsonschema
    except ImportError:
        print("check_mod: jsonschema is not installed (pip install jsonschema); schema check skipped")
        return 0

    problems = []

    def report(path, where, msg, blocking):
        problems.append((path, where, msg, blocking))
        if not args.quiet:
            print(f"{'BLOCKING ' if blocking else ''}{path}: {where}: {msg}")

    for mod in args.mods:
        check_mod(mod, jsonschema, report)

    blocking = sum(1 for p in problems if p[3])
    print(f"check_mod: {len(problems)} problem(s), {blocking} blocking")
    return 2 if blocking else (1 if problems else 0)


if __name__ == "__main__":
    sys.exit(main())
