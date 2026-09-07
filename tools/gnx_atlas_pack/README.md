# gnx-atlas-pack — GNX Mod Sprite Atlas Packer

Packs a GNX mod's sprite strips into one or more texture atlases + a UV JSON
table, reducing VRAM texture pages and improving boot performance when multiple
mods are loaded.

## Measured results

On real mods:

| Mod             | Strips | Frames | Texture pages before | After |
|-----------------|--------|--------|----------------------|-------|
| frieren_mod     | 57     | 1 261  | 57                   | **1** |
| gnx_test_mod    | 316    | 14 775 | 316                  | **8** |

## Installation (modder)

Requirements: **Python 3.10+** and **Pillow**.

```
pip install Pillow
```

Optional, to build a standalone .exe:

```
pip install pyinstaller
pyinstaller --onefile gnx_atlas_pack.py
```

The .exe appears under `dist\gnx_atlas_pack.exe`.

## Usage

Expected mod structure:

```
my_mod/
  manifest.json
  classes.json
  strips/
    spr_h_char_idle_head.png
    spr_h_char_idle_breast.png
    ...
```

Run:

```
python gnx_atlas_pack.py path\to\my_mod
```

Or with the .exe:

```
gnx_atlas_pack.exe path\to\my_mod
```

Output:

```
my_mod/
  atlas/
    atlas_0.png         (packed atlas, 4096x4096)
    atlas_1.png         (if needed)
    ...
    uv.json             (per-sprite UV table)
```

## Options

```
--atlas-size N    Max atlas size (default: 4096)
--padding N       Padding between frames (default: 2, prevents bleeding)
--dry-run         Simulate without writing, show stats + atlas count
```

## Frame count detection

The tool infers the number of frames per strip from:
1. An explicit `"frames": N` field in `classes.json` / `cells.json` if one
   exists for that PNG file.
2. Otherwise: heuristic (frame_width = divisor of strip_width that produces
   the most square-like frames).

A strip with ambiguous detection (e.g. 1 frame instead of 15) is logged:

```
[my_mod] 2 strips could not infer stride (kept as 1 frame). Sample: ['spr_h_..._hand.png']
```

These are typically single-frame sprites (hand, icon). Nothing to do.

If a real animated strip is misdetected, add an explicit `"frames": N` in
your `classes.json` for that file.

## How GNX consumes the atlas

Once `atlas/uv.json` is present, the GNX loader (at boot) detects it, loads
each `atlas_N.png` as a single sprite, and populates a UV table that the
`gnx_draw_sprite_ext` draw wrappers use instead of the per-strip path. The
legacy format (strips only, no `atlas/`) remains supported indefinitely.

## Distribution

You can ship your mod:

- **With atlas only** (recommended): distribute `manifest.json`, `classes.json`,
  and the `atlas/` folder. Optionally remove `strips/` before packaging.
- **With strips + atlas** (allows re-pack by contributors): keep `strips/`
  as source, `atlas/` as output.
- **Without atlas** (backwards-compatible): distribute as before, GNX takes
  the legacy path.

## Known limitations

- Sprite origin defaults to `(0, 0)` (top-left corner). If your `classes.json`
  declares `xorig`/`yorig` on an entry, the packer reads and propagates them
  into the atlas UV data (`xo`/`yo` fields in uv.json).
- Explicit frame list format (multi-file) is not yet supported: only the
  `{"strip": "file.png", "frames": N}` format is recognized.
- Rotation: the GML wrapper uses `draw_sprite_general` (when rot != 0) —
  functional but very slightly more expensive than `draw_sprite_ext`.
