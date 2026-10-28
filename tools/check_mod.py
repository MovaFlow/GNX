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
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"

# manifest key -> schema name
DATA_KEYS = ["classes", "cells", "quests", "tools", "sounds", "props", "items"]


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
