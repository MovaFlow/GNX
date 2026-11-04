"""Writes test strips for the art_probe scenarios to harness_game/test_mods/art_probe (git-ignored).
Run: python tools/make_art_probe_mod.py"""
import json
import struct
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "harness_game" / "test_mods" / "art_probe"


def png(path, w, h, frames, colour_of):
    """A horizontal strip of `frames` frames of w x h, each one flat colour colour_of(frame)."""
    rows = []
    for _ in range(h):
        row = bytearray([0])
        for f in range(frames):
            row += bytes(colour_of(f)) * w
        rows.append(bytes(row))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w * frames, h, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))


def main():
    # frame f has red = 10 * (f + 1), so a read pixel tells which frame was drawn
    png(OUT / "probe" / "big_10f.png", 128, 128, 10, lambda f: (10 * (f + 1), 0, 0, 255))
    png(OUT / "probe" / "row_5f.png", 8, 8, 5, lambda f: (10 * (f + 1), 0, 0, 255))
    (OUT / "manifest.json").write_text(json.dumps({
        "mod_id": "art_probe", "name": "GNX Art Probe", "version": "1.0.0",
        "_about": "Test art for the art_probe scenarios. Not for players.",
        "compatible_game_versions": ["1.40"],
    }, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
