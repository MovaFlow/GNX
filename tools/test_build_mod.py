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
assert errs({"map": "m", "map_button": {"travel": "huge"}}) and not errs({"map": "m", "map_button": {"travel": "complex"}})
assert errs({"map_button": {}}) and "need a" in errs({"map_button": {}})[0]
assert errs({"map": "vanilla", "map_start": {}})
assert not errs({"map": "m", "map_button": {"map_sprite": "nope.png"}}) and check_map({"map": "m", "map_button": {"map_sprite": "nope.png"}}, here)
assert errs({"map": "m", "map_button": {"unlock": {"type": "gold_more_than", "value": 1}}})
assert not errs({"map": "m", "map_button": {"unlock": [{"type": "gold_gte", "value": 1}, {"type": "floor_gte", "value": 2}]}})
assert errs({"map": "m", "map_button": {}, "map_start": {"floors": 1, "cells": [{"h_type": 9001, "floor": 2}]}})
assert not errs({"map": "m", "map_button": {}, "map_start": {"cells": [{"h_type": "my_mod.MY CELL"}]}})
assert errs({"map": "m", "map_button": {}, "map_start": {"cells": [{"h_type": [1]}]}})
assert not errs({"map": "m", "map_button": {}, "map_start": {"troops": [{"type": "ogre", "kind": 1, "num": 2}],
                 "prisoners": [{"class": "my_mod.WITCH", "level": 2}], "unlock_cells": [2, "my_mod.MY CELL"]}})
assert errs({"map": "m", "map_button": {}, "map_start": {"troops": [{"type": "dragon", "num": 1}]}})
assert errs({"map": "m", "map_button": {}, "map_start": {"troops": [{"type": "goblin"}]}})
assert errs({"map": "m", "map_button": {}, "map_start": {"prisoners": [{"level": 2}]}})
assert any("ignored" in msg for lvl, msg in check_map({"map": "m", "map_button": {"x": 150}}, here))
# map_info is the current name; map_button (old name) is still read; both = warning, map_info wins
assert errs({"map": "m", "map_info": {"travel": "huge"}}) and not errs({"map": "m", "map_info": {"travel": "complex"}})
assert not [p for p in check_map({"map": "m", "map_info": {}}, here) if "no map_info" in p[1]]
assert any("both" in msg for lvl, msg in check_map({"map": "m", "map_info": {}, "map_button": {}}, here))
assert not errs({"map": "m", "map_info": {"travel": "simple"}, "map_button": {"travel": "huge"}})
print("ok")

# deploy: every file a mod can use reaches GNX_mods/<mod_id>/ (json files from the manifest, the map image,
# and the strips/atlas/sounds/portraits folders). Run on a temp copy of the full test map mod.
import shutil, subprocess, sys, tempfile
with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / "src" / "harness_map_full"
    shutil.copytree(ROOT / "tools/scenarios/mods/harness_map_full", src)
    for rel in ("sounds/snd_fmoan0_1.ogg", "portraits/face.png", "atlas/uv.json", "strips/spr_x.png"):
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(b"test")
    game = Path(tmp) / "game"
    game.mkdir()
    r = subprocess.run([sys.executable, str(ROOT / "tools/build_mod.py"), str(src), str(game), "--skip-pack"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    dep = game / "GNX_mods" / "harness_map_full"
    for rel in ("manifest.json", "quests.json", "tools.json", "sounds.json", "sprites/full_map.png",
                "sounds/snd_fmoan0_1.ogg", "portraits/face.png", "atlas/uv.json", "strips/spr_x.png"):
        assert (dep / rel).is_file(), f"build_mod did not deploy {rel}"
    assert "OK - map 'harness_full'" in r.stdout, r.stdout
print("deploy ok")
assert not errs({"map": "m", "map_info": {"travel_cost": {"gold": 50, "food": 10, "days": 1}}})
assert errs({"map": "m", "map_info": {"travel_cost": {"gold": -5}}}) and errs({"map": "m", "map_info": {"travel_cost": 50}})
