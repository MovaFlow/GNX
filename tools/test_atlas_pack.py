#!/usr/bin/env python3
"""Self-check of gnx_atlas_pack: a strip keeps the frame count and origin its JSON declares, also when the JSON writes the
file name with other capitals (file names ignore case on Windows). Usage: python tools/test_atlas_pack.py [packer.exe]"""
import json, os, subprocess, sys, tempfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
exe = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "gnx_atlas_pack", "dist", "gnx_atlas_pack.exe")

with tempfile.TemporaryDirectory() as d:
    mod = os.path.join(d, "pack_test")
    os.makedirs(os.path.join(mod, "strips"))
    # 30 frames of 45 x 90: with no count the packer guesses 15 frames of 90 x 90
    Image.new("RGBA", (45 * 30, 90), (200, 80, 60, 255)).save(os.path.join(mod, "strips", "spr_h_damona_idle_head.png"))
    json.dump({"name": "pack_test", "version": "1", "compatible_game_versions": ["1.40"]}, open(os.path.join(mod, "manifest.json"), "w"))
    json.dump([{"name": "A", "sprites": {"idle_head": {"strip": "strips/spr_h_Damona_idle_head.png", "frames": 30, "xorig": 3, "yorig": 90}}}],
              open(os.path.join(mod, "classes.json"), "w"))
    subprocess.run([exe, mod], check=True, capture_output=True)
    with open(os.path.join(mod, "atlas", "uv.json"), encoding="utf-8") as f:
        e = json.load(f)["entries"]["spr_h_damona_idle_head"]
    n = len(e["frames"])
    assert n == 30, f"FAIL frames: {n}, the JSON says 30"
    assert (e.get("xo"), e.get("yo")) == (3, 90), f"FAIL origin: {e.get('xo')}, {e.get('yo')}"
print("test_atlas_pack: OK")

# the frame counts and origins of the manifest's monster_art "sprites" list and its "world" entries (inline, or in a file, trailing
# commas allowed as the game's json_parse does) are read like those of classes.json and cells.json. This reads the packer's source, so
# it runs without the exe
import contextlib, io
from pathlib import Path

sys.path.insert(0, os.path.join(HERE, "gnx_atlas_pack"))
try:
    import gnx_atlas_pack as packer
except ImportError:
    packer = None
    print("test_atlas_pack: gnx_atlas_pack.py not present, source check skipped")
if packer is not None:
    sprites = {"s1": {"strip": "strips/Spr_Art_One.png", "frames": 12, "xorig": 4, "yorig": 9}, "s2": {"strip": "strips/two.png", "frames": 3}}
    art = {"sprites": sprites, "goblin": {"world": {"walk": {"strip": "strips/walk.png", "frames": 10, "xorig": 1, "yorig": 1},
                                                    "idle": "strips/plain.png"}}}
    want_frames = {"spr_art_one.png": 12, "two.png": 3, "walk.png": 10}
    want_origins = {"spr_art_one.png": (4, 9), "walk.png": (1, 1)}
    for form in ("inline", "file", "trailing commas"):
        with tempfile.TemporaryDirectory() as d:
            man = {"name": "m", "monster_art": art if form == "inline" else "art.json"}
            text = json.dumps(man)
            if form == "trailing commas":
                text = text[:-1] + ",}"  # {"name": ..., "monster_art": "art.json",}
            open(os.path.join(d, "manifest.json"), "w").write(text)
            if form != "inline":
                open(os.path.join(d, "art.json"), "w").write(json.dumps(art)[:-1] + ",}")
            frame_map, origin_map = packer.read_manifest_sprite_meta(Path(d))
            assert frame_map == want_frames, (form, frame_map)
            assert origin_map == want_origins, (form, origin_map)
    # no manifest: nothing, quietly. A manifest or art file that cannot be read: nothing, and it is said
    def read_meta(d):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            r = packer.read_manifest_sprite_meta(Path(d))
        return r, out.getvalue()

    with tempfile.TemporaryDirectory() as d:
        assert read_meta(d) == (({}, {}), "")
        open(os.path.join(d, "manifest.json"), "w").write("{bad")
        r, said = read_meta(d)
        assert r == ({}, {}) and "WARN" in said, (r, said)
        open(os.path.join(d, "manifest.json"), "w").write(json.dumps({"monster_art": "gone.json"}))
        r, said = read_meta(d)
        assert r == ({}, {}) and "WARN" in said, (r, said)
        open(os.path.join(d, "manifest.json"), "w").write(json.dumps({"monster_art": 5}))
        assert read_meta(d) == (({}, {}), "")
    print("test_atlas_pack: monster_art sprites and world OK")

    # every data file the manifest names (props, items, ...) gives its frame counts, not only classes/cells
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "manifest.json"), "w").write(json.dumps({"name": "m", "props": "my_props.json", "items": "items.json"}))
        open(os.path.join(d, "my_props.json"), "w").write(json.dumps(
            {"props": [], "sprites": {"digits": {"strip": "strips/digits.png", "frames": 10, "xorig": 2, "yorig": 3}}}))
        open(os.path.join(d, "items.json"), "w").write(json.dumps({"sprites": {"gem": {"strip": "strips/gem.png", "frames": 4}}}))
        frame_map, origin_map = packer.read_manifest_sprite_meta(Path(d))
        assert frame_map == {"digits.png": 10, "gem.png": 4}, frame_map
        assert origin_map == {"digits.png": (2, 3)}, origin_map
    print("test_atlas_pack: props and items frame counts OK")

    # identical frames, in one strip or across strips, are stored once and share a place; different ones are not
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "strips"))
        a = Image.new("RGBA", (40 * 4, 30), (0, 0, 0, 0))   # frames 0 and 2 empty, 1 and 3 red
        for i in (1, 3):
            a.paste((255, 0, 0, 255), (i * 40, 0, i * 40 + 40, 30))
        a.save(os.path.join(d, "strips", "a.png"))
        b = Image.new("RGBA", (40 * 2, 30), (0, 0, 255, 255))  # frame 0 blue, frame 1 red as in a
        b.paste((255, 0, 0, 255), (40, 0, 80, 30))
        b.save(os.path.join(d, "strips", "b.png"))
        json.dump([{"name": "T", "sprites": {"a": {"strip": "strips/a.png", "frames": 4}, "b": {"strip": "strips/b.png", "frames": 2}}}],
                  open(os.path.join(d, "classes.json"), "w"))
        with contextlib.redirect_stdout(io.StringIO()):
            packer.pack_mod(Path(d), 256, 2)
        uv = json.load(open(os.path.join(d, "atlas", "uv.json"), encoding="utf-8"))
        pos = lambda k, i: tuple(uv["entries"][k]["frames"][i][f] for f in ("atlas", "x", "y"))
        assert pos("a", 0) == pos("a", 2), "FAIL dedup: two empty frames stored twice"
        assert pos("a", 1) == pos("a", 3) == pos("b", 1), "FAIL dedup: red frames stored more than once"
        assert len({pos("a", 0), pos("a", 1), pos("b", 0)}) == 3, "FAIL dedup: different frames share a place"
        page = Image.open(os.path.join(d, "atlas", "atlas_0.png")).convert("RGBA")
        for k, i, want in (("a", 0, (0, 0, 0, 0)), ("a", 3, (255, 0, 0, 255)), ("b", 0, (0, 0, 255, 255))):
            f = uv["entries"][k]["frames"][i]
            assert page.getpixel((f["x"] + 5, f["y"] + 5)) == want, f"FAIL dedup: {k}[{i}] has the wrong pixels"
    print("test_atlas_pack: dedup OK")
