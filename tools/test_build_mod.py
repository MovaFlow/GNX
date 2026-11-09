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
# "map" as a list: content for each listed map; map_info needs exactly one mod map in it
assert check_map({"map": ["vanilla", "harness_map"]}, here) == []
assert not errs({"map": ["vanilla", "harness_map"], "map_info": {"label": "X"}})
assert errs({"map": ["harness_map", "harness_map_b"], "map_info": {"label": "X"}})
assert errs({"map": ["vanilla", "all"], "map_start": {}})
assert errs({"map": []}) and errs({"map": ["vanilla", 3]})
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


# monster_art and sprite_replace art lives in free folders: the deploy must copy it, for a file name or an inline object, and for every
# value form the loader reads (gnx_resolve_sprite_raw): a file, a folder, strip, path, folder, a frames list of files
from build_mod import art_paths

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp) / "mod"  # outside.png below lands in tmp, not in the system temp folder
    d.mkdir()
    for rel in ("world/walk.png", "world/idle.png", "world/p.png", "world/f1.png", "world/f2.png", "art/x.png", "art/frames/1.png", "art/frames/2.png",
                "art/s.png", "art/y1.png", "fold/0.png", "fold/1.png", "unrelated/other.png"):
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_bytes(b"x")
    (d.parent / "outside.png").write_bytes(b"x")
    (d / "ma.json").write_text(json.dumps({
        "_note": "x",
        "sprites": {"s1": {"strip": "art/s.png", "frames": 2}, "s2": {"frames": ["art/y1.png"]}},
        "goblin": {"world": {"walk": "world/walk.png", "idle": {"strip": "world/idle.png", "frames": 8}, "walk_back": {"path": "world/p.png"},
                             "milk_walk_empty": {"frames": ["world/f1.png", "world/f2.png"]}, "milk_walk_full": {"folder": "fold"}}},
        "ogre": {"world": {"walk": "world/walk.png", "idle": "world/missing.png", "walk_carry": "../outside.png"}}}), encoding="utf-8")
    rel = lambda ps: sorted(str(p.relative_to(d)).replace("\\", "/") for p in ps)
    m = {"monster_art": "ma.json", "sprite_replace": {"spr_a": "art/x.png", "spr_b": "art/frames", "_c": "art/s.png", "spr_d": {"strip": "art/x.png"}}}
    got = rel(art_paths(m, d))
    want = ["art/frames/1.png", "art/frames/2.png", "art/s.png", "art/x.png", "art/y1.png", "fold/0.png", "fold/1.png", "ma.json", "world/f1.png",
            "world/f2.png", "world/idle.png", "world/p.png", "world/walk.png"]
    assert got == want, got
    # inline object: no ma.json; a sprite_replace file name that holds the object
    assert art_paths({"monster_art": {"goblin": {"world": {"walk": "world/walk.png"}}}}, d) == [d / "world" / "walk.png"]
    (d / "sr.json").write_text(json.dumps({"spr_a": "art/x.png", "spr_z": {"folder": "art/frames"}}), encoding="utf-8")
    assert rel(art_paths({"sprite_replace": "sr.json"}, d)) == ["art/frames/1.png", "art/frames/2.png", "art/x.png", "sr.json"]
    # nothing, a missing file, a file that is not JSON, wrong types: no files and no crash
    assert art_paths({}, d) == []
    assert art_paths({"monster_art": "nope.json", "sprite_replace": 5}, d) == []
    (d / "bad.json").write_text("{not json", encoding="utf-8")
    assert rel(art_paths({"monster_art": "bad.json"}, d)) == ["bad.json"]
    assert art_paths({"monster_art": {"goblin": 5, "ogre": {"world": 5}, "sprites": 5}}, d) == []
print("art_paths ok")

# the deploy itself, on real test mods: every art file the manifest names is in GNX_mods/<mod>/ with the same bytes, and a file nothing
# names is not. (harness_replace: sprite_replace from a JSON file, folder and strip forms; the others: monster_art inline, world files)
DEPLOY_ART = {
    "harness_replace": ["sprite_replace.json", "art/red_birth.png", "art/pillar/spr_slot_giant_pillar_1.png", "art/giant_head/spr_giant_idle_head_4.png",
                        "art/small.png", "art/box_same.png", "art/idle_half.png"],
    "harness_art_world": ["world/walk.png", "world/ogre.png", "world/log2.png"],
    "harness_art_world_folder": ["art/walk_same.png", "world/frames/0.png", "world/frames/1.png"],
    "harness_art_world_forms": ["world/walk_same.png", "world/big.png"],
}
for mod, files in DEPLOY_ART.items():
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src" / mod
        shutil.copytree(ROOT / "tools/scenarios/mods" / mod, src)
        (src / "notes_not_art.png").write_bytes(b"x")  # in no manifest entry: stays behind
        game = Path(tmp) / "game"
        game.mkdir()
        r = subprocess.run([sys.executable, str(ROOT / "tools/build_mod.py"), str(src), str(game), "--skip-pack", "--deploy-anyway"], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        dep = game / "GNX_mods" / mod
        for f in files:
            assert (dep / f).is_file(), f"build_mod did not deploy {mod}/{f}"
            assert (dep / f).read_bytes() == (src / f).read_bytes(), f"{mod}/{f} differs"
        assert not (dep / "notes_not_art.png").exists(), f"{mod}: a file no manifest entry names was deployed"
print("art deploy ok")

# an inline object where a role names a file (classes, cells, quests...): the packer and the verify step skip it, no crash
try:
    import gnx_pack_strips  # exits when Pillow is missing (python without it: that one check is skipped, run with py)
    assert gnx_pack_strips.find_json_files(ROOT, {"classes": {"inline": 1}, "cells": ["x"]}) == {}
except SystemExit as e:
    print("skipped the packer check:", e)
with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / "src" / "inline_roles"
    src.mkdir(parents=True)
    (src / "manifest.json").write_text(json.dumps({"mod_id": "inline_roles", "name": "x", "version": "1", "compatible_game_versions": ["1.40"],
                                                   "quests": {"events": {}}, "props": {"props": []}}), encoding="utf-8")
    game = Path(tmp) / "game"
    game.mkdir()
    r = subprocess.run([sys.executable, str(ROOT / "tools/build_mod.py"), str(src), str(game), "--skip-pack", "--deploy-anyway"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (game / "GNX_mods" / "inline_roles" / "manifest.json").is_file()
print("inline roles ok")
