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
