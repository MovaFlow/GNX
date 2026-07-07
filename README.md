<img width="416" height="416" alt="gnx_logo" src="https://github.com/user-attachments/assets/ee2b9912-30fb-404c-b447-fe62f0832e9e" />

# GNX — Goblin Nest Extender

> **Game version:** 1.33

GNX is a mod layer patched into `data.win` that lets you add custom captive classes and dungeon cells via JSON files. No GameMaker, no recompilation — drop a folder into `GNX_mods/` and run.

---

## Installing GNX

1. Install [G3M](https://github.com/y114git/G3M).
2. Add Goblin Nest as a custom game in G3M.
3. Download **Goblin Nest eXtender _GNX_1.2.5.zip** and add it as a mod for Goblin Nest in G3M.
4. Activate it and launch from G3M.

On first boot, `gnx_debug.txt` is written to `%LOCALAPPDATA%\goblin_nest\gnx_debug.txt`. It should end with `[GNX-TEST] N/N passed`.

---

## Making Mods

A mod is a folder inside `<game>/GNX_mods/` containing a `manifest.json`. GNX auto-discovers and loads all such folders on startup, in alphabetical order.

```
GNX_mods/
  my_mod/
    manifest.json
    classes.json     ← optional
    cells.json       ← optional
    strips/          ← packed sprite strips
```

**Docs:**
- [`docs/TUTORIAL.md`](docs/TUTORIAL.md) — step-by-step walkthrough, from skeleton mod to custom class and cell.
- [`docs/GNX_MODDING.md`](docs/GNX_MODDING.md) — full field-by-field reference for every JSON block.
- [`docs/example_mod/`](docs/example_mod/) — a working reference mod (custom class + custom cell + vanilla patch).

**Tools** (in `tools/`, require Python 3.9+ and `pip install Pillow`):

| Script | Purpose |
|--------|---------|
| `scaffold_class.py` | Generate a `classes.json` stub from detected sprite folders |
| `scaffold_cell.py` | Generate a `cells.json` stub for a new cell |
| `generate_class.py` | Interactive `classes.json` generator |
| `generate_cell.py` | Interactive `cells.json` generator (also handles vanilla patches) |
| `export_class_sprites.py` | Copy + rename a vanilla class's sprites as a starting point |
| `build_mod.py` | Pack sprites, verify, and deploy a mod to the game folder |

---

## Compatibility

GNX targets game version **1.33**. Mods declare which versions they support in `manifest.json` — a version mismatch causes the mod to be silently skipped (check `gnx_debug.txt`).

---

## Development

If you want to look at the code, just unpack the mod, the gml files are in there.
The diffs are on the github under GNX\diffs for all modified files.

---

## Credit
All credit goes to @BadColor for making this game. You are truly wonderful. We look forward to your success.

Go support the developper, they deserve it:

Steam Page: https://store.steampowered.com/app/3782910/Goblin_Nest/

Itch.io : https://badcolor.itch.io/goblin-nest

Discord (mod support is here): https://discord.gg/7HEAnEmyW2

Credit to @nevereverever for their excellent work on the Frieren Mod ([link](https://github.com/nevereverever53/GN_Mod_Frieren)), the advanced escape and conditional boss capture mecanics have been generalized to be used in GNX.

Credit to @kazull for improving the export_class_sprites script to include idons and work with special classes.

