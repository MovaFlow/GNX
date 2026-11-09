"""Lists every monster sprite named in GNX/gml, by file and function (monster art rework, Phase 0).
Run: python tools/mon_art_inventory.py    -> harness_game/mon_art/inventory.json + a summary"""
import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SPRITE = re.compile(r"\bspr_(?:h_(?:goblin|hobgoblin|ogre)|goblin|hobgoblin|ogre|mon)[a-z0-9_]*\b")
FUNC = re.compile(r"^function\s+([A-Za-z0-9_]+)")
SKIP = ("s_gnx_harness", "s_gnx_tests")


def scan(text, filename):
    out = []
    func = "(top)"
    for n, line in enumerate(text.splitlines(), 1):
        m = FUNC.match(line)
        if m:
            func = m.group(1)
        code = line.split("//", 1)[0]
        for name in SPRITE.findall(code):
            out.append({"sprite": name, "file": filename, "func": func, "line": n})
    return out


def main():
    entries = []
    for f in sorted((REPO / "GNX" / "gml").glob("*.gml")):
        if not any(s in f.name for s in SKIP):
            entries += scan(f.read_text(encoding="utf-8", errors="replace"), f.name)
    sprites = {}
    for e in entries:
        sprites.setdefault(e["sprite"], []).append({"file": e["file"], "func": e["func"], "line": e["line"]})
    funcs = Counter(e["func"] for e in entries)
    out = REPO / "harness_game" / "mon_art"
    out.mkdir(parents=True, exist_ok=True)
    (out / "inventory.json").write_text(json.dumps({"sprites": sprites, "funcs": funcs}, indent=1), encoding="utf-8")
    print(f"{len(sprites)} sprites at {len(entries)} sites in {len(funcs)} functions")
    for name, count in funcs.most_common():
        print(f"  {count:5d}  {name}")


if __name__ == "__main__":
    main()
