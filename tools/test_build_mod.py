"""Self-check for build_mod.check_map. Run: python tools/test_build_mod.py"""
import json
from pathlib import Path
from build_mod import check_map

ROOT = Path(__file__).resolve().parent.parent
for mod in ("tools/scenarios/mods/harness_map", "tools/scenarios/mods/harness_map_b",
            "tools/scenarios/mods/harness_map_gated", "GNX/example_mod"):
    d = ROOT / mod
    probs = check_map(json.loads((d / "manifest.json").read_text(encoding="utf-8-sig")), d)
    assert not [p for p in probs if p[0] == "ERROR"], (mod, probs)

here = ROOT / "tools/scenarios/mods/harness_map"
errs = lambda m: [msg for lvl, msg in check_map(m, here) if lvl == "ERROR"]
assert check_map({"name": "plain content mod"}, here) == []
assert errs({"map_button": {}}) and "need a" in errs({"map_button": {}})[0]
assert errs({"map": "vanilla", "map_start": {}})
assert errs({"map": "m", "map_button": {"x": 900}})
assert not errs({"map": "m", "map_button": {"map_sprite": "nope.png"}}) and check_map({"map": "m", "map_button": {"map_sprite": "nope.png"}}, here)
assert errs({"map": "m", "map_button": {"unlock": {"type": "gold_more_than", "value": 1}}})
assert not errs({"map": "m", "map_button": {"unlock": [{"type": "gold_gte", "value": 1}, {"type": "floor_gte", "value": 2}]}})
assert errs({"map": "m", "map_button": {}, "map_start": {"floors": 1, "cells": [{"h_type": 9001, "floor": 2}]}})
assert errs({"map": "m", "map_button": {}, "map_start": {"cells": [{"h_type": "MY CELL"}]}})
assert any(lvl == "WARN" for lvl, _ in check_map({"map": "m", "map_button": {"x": 150}}, here))
print("ok")
