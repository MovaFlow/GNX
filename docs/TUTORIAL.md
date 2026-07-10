# GNX Modding Tutorial — Building Your First Mod

> **Compatibility:** GNX v1.0 · Game version 1.33

This is a hands-on walkthrough for a new modder. It builds up a mod step by
step, from "hello world" to a custom class and a custom cell, using
[`example_mod/`](example_mod/) as the working reference.

For the full field-by-field reference, see [GNX_MODDING.md](GNX_MODDING.md).
This tutorial only explains *what to do, in what order, and how to tell if it
worked*.

---

## Table of Contents

- [0. Prerequisites](#0-prerequisites)
- [1. Mod skeleton (no sprites yet)](#1-mod-skeleton-no-sprites-yet)
- [2. Easiest real change: patch a vanilla cell (no sprites)](#2-easiest-real-change-patch-a-vanilla-cell-no-sprites)
- [3. Sprite pipeline basics](#3-sprite-pipeline-basics)
- [4. Custom class — your own character](#4-custom-class--your-own-character)
- [5. Custom cell — your own room](#5-custom-cell--your-own-room)
- [6. Test, debug, iterate](#6-test-debug-iterate)
- [7. Going further](#7-going-further)
- [8. Tooling reference](#8-tooling-reference)
  - [export_class_sprites.py](#export_class_spritespy--copy--rename-a-vanilla-class)
  - [scaffold_class.py](#scaffold_classpy--generate-a-classesjson-stub-from-detected-sprites)
  - [scaffold_cell.py](#scaffold_cellpy--generate-a-cell-stub)
  - [generate_class.py](#generate_classpy--interactive-classesjson-generator)
  - [generate_cell.py](#generate_cellpy--interactive-cellsjson-generator)
  - [build_mod.py](#build_modpy--pack--verify--deploy)

---

## 0. Prerequisites

**Software:**

- **GNX** — install via [G3M](https://github.com/y114git/G3M) (the mod manager). Add Goblin Nest as a custom game, add the GNX package as a mod, activate it, and launch from G3M. You don't touch any game files yourself.
- **Python 3.9+** — required to run the modding tools. Download from
  [python.org](https://www.python.org/downloads/).
- **Pillow** — Python image library used by all tools:
  ```
  pip install Pillow
  ```
- A text editor and basic JSON literacy. No GameMaker, no recompilation, ever.

**Setting up `<tools>/`:**

All commands in this tutorial reference `<tools>/` — the folder containing the
GNX modding scripts. Depending on how you got them:

- **From G3M:** extract `tools.zip` (shipped alongside the GNX mod) to any
  folder. That folder is `<tools>/`.
- **From this repo:** the `tools/` directory in the repo root is `<tools>/`.

Example — if you extracted to `C:\GNX\tools\`:
```bash
python C:\GNX\tools\scaffold_class.py --name Barbarian ...
```

**Game folder layout after setup:**

```
<game folder>/
  GNX_mods/
    my_mod/
      manifest.json
```

GNX auto-discovers every subfolder that contains a `manifest.json` and loads
them in alphabetical order. No index file needed.

Everything below happens inside `<game folder>/GNX_mods/`.

---

## 1. Mod skeleton (no sprites yet)

Goal: get GNX to recognize your mod and load it cleanly, before you write any
real content.

1. Inside `GNX_mods/`, right-click → New Folder → name it `my_mod`.
   Inside `my_mod/`, create a new text file, rename it `manifest.json`
   (make sure Windows isn't hiding the `.txt` extension — it should not say
   `manifest.json.txt`). Open it and paste:
   ```json
   {
     "mod_id": "my_mod",
     "name": "My Mod",
     "version": "0.1.0",
     "compatible_game_versions": ["1.33"],
     "classes": "classes.json",
     "cells": "cells.json"
   }
   ```
   `mod_id` **must match the folder name**. If you have no classes or cells
   yet, omit those two keys entirely (don't point to files that don't exist).

2. Launch the game. Open `gnx_debug.txt` — written to
   `%LOCALAPPDATA%\goblin_nest\gnx_debug.txt` (GameMaker's default sandbox
   folder on Windows). You should see:
   ```
   [GNX] loader start
   [GNX] mods_root=<game folder>/GNX_mods/
   [GNX] loading: My Mod v0.1.0
   [GNX] loader done
   ```
   followed by `[GNX-TEST] N/N passed`.

If you see `[GNX] mods/ folder not found, no mods loaded`, the `GNX_mods/`
directory is missing. If you see `[GNX] manifest not found: <path>`, your
folder name doesn't match `mod_id`, or the `manifest.json` is missing.

**Stop here and confirm this works before moving on.** This step has zero
gameplay effect, but if the mod isn't loading cleanly now, nothing else will
work either.

---

## 2. Easiest real change: patch a vanilla cell (no sprites)

Goal: change something visible without drawing a single sprite, by reusing
existing vanilla sprites.

Add `my_mod/cells.json`:
```json
[
  {
    "h_type": 1,
    "physical": {
      "layers": [
        [12, "spr_dirt_wall",          false, -1, false],
        [0,  "spr_slot_wall_2_back",   false, -1],
        [2,  "spr_slot_wall_1_handc",  true,  -1],
        [5,  "spr_slot_wall_1_extra",  false, -1],
        [7,  -1,                       false, -1, false],
        [8,  -1,                       false, -1, false]
      ]
    }
  }
]
```
This is the second entry in `example_mod/cells.json`. `h_type: 1` is a
**vanilla** cell ID (0–42), so GNX treats this as a *patch*: only
`physical.layers` is replaced, everything else about the cell (price, income,
h-scene logic) stays vanilla. See [GNX_MODDING.md §10](GNX_MODDING.md#10-vanilla-patches).

Relaunch and check `gnx_debug.txt`:
```
[GNX] patched h=1 by mod=my_mod
```
In-game, the WALL2 cell should now render with WALL1's background sprites.
This confirms: cells.json is being read, and patching an existing `h_type`
works.

**Note on IDs:** vanilla `h_type` is 0–42, vanilla `class_id` is 0–13. For
new cells and classes, **omit the numeric ID** — GNX auto-assigns a stable
hash-based value (`h_type` ≥100, `class_id` ≥14) derived from your mod folder
name and entry name. Same ID every run, no coordination needed between mods.
You can still supply an explicit ID (≥43 / ≥14) if you prefer, but omitting is
the recommended approach.

---

## 3. Sprite pipeline basics

Everything past this point needs sprites. The packer (`gnx_pack_strips.py`,
documented in `gnx_pack_strips_doc.md`) turns a folder of numbered per-frame
PNGs into a single strip image + metadata block.

**Don't have custom art yet?** Use `export_class_sprites.py` (see
[§8 → export_class_sprites.py](#export_class_spritespy--copy--rename-a-vanilla-class))
to copy a vanilla class's full sprite set and rename it to your prefix. This
gives you a working sprite folder you can pack and test immediately, then swap
for real art later. The script requires a one-time UMT sprite export — the full
steps are in §8.

**Basic workflow:**

```
my_mod/
  sprites/
    spr_h_mychar_idle_head/
      0.png
      1.png
      ...
  classes.json   ← declares "idle_head": { "xorig": 0, "yorig": 90 }
```
```bash
python <tools>/gnx_pack_strips.py GNX_mods/my_mod/ --dry-run   # preview
python <tools>/gnx_pack_strips.py GNX_mods/my_mod/             # writes strips/ + rewrites classes.json
```

After packing, the JSON entry becomes:
```json
"idle_head": {
  "strip": "strips/idle_head.png",
  "frames": 90,
  "xorig": 0, "yorig": 90
}
```
At runtime you'll see in `gnx_debug.txt`:
```
[GNX] idle_head: strip frames=90 idx=ref sprite 1530
```
If instead you see:
```
[GNX] WARN idle_head: no strip/path/frames, returning fallback
```
the packer never ran (or the JSON edit happened after packing and the
`strip` key is missing/wrong) — the sprite falls back to a placeholder.

Two fields matter beyond `xorig`/`yorig`:
- `folder`: exact source folder name, when it doesn't match
  `{sprite_prefix}_{key}`.
- `canvas_w` / `canvas_h`: pad frames to a fixed size — required when a
  sprite must match a vanilla slot exactly (e.g. class icons must be 21×26,
  origin 10×13).

---

## 4. Custom class — your own character

Goal: a new selectable class (`class_id >= 14`) that goblins can interact
with in cells.

**Choosing a tool — pick one:**

- **You copied vanilla sprites in §3** → run `scaffold_class.py` now
  (see [§8 → scaffold_class.py](#scaffold_classpy--generate-a-classesjson-stub-from-detected-sprites)).
  It scans your `sprites/` folder and generates a ready-to-fill `classes.json`
  stub with every detected sprite pre-wired and all clothing sections built.
  Merge the output into your `classes.json` array and skip to step 3 below.

- **No sprites yet / using custom art** → run `generate_class.py` instead
  (see [§8 → generate_class.py](#generate_classpy--interactive-classesjson-generator)).
  It walks you through the class fields interactively and writes a stub without
  needing a `sprites/` folder at all. Use `example_mod/classes.json` as a
  reference for field semantics.

**Steps:**

1. **Choose a `sprite_prefix`** (e.g. `spr_h_mychar`). You can omit
   `class_id` entirely — GNX will hash-assign a stable ID. Only supply one if
   you have a specific reason (e.g. cross-mod references by integer).
2. **Decide `override`**:
   - `false` = brand new class, fully separate from vanilla.
   - `true` + a vanilla `class_id` (0–13) = reskin an existing class. Logged
     as `[GNX] class_id <N> override`. Without `override: true`, registering
     an already-used `class_id` is logged as
     `[GNX] class_id <N> collision — skipped` and your class is dropped
     entirely.
3. **Declare every sprite your cells will need** in the `sprites` dict. The
   minimum set depends on which cell types your class will be placed in —
   see [GNX_MODDING.md Quick-Reference](GNX_MODDING.md#quick-reference-sprite-keys-by-cell-type):
   - Standard cells (slot_type 0): `hand`, `idle_*`, `loop_*` (head/breast/leg_1/leg_2/legp).
   - Large cells (slot_type 2): `big_start_*`, `big_idle_*`, `big_loop_*`.
   - Tent cells (slot_type 3): `tent_idle_*`, `tent_loop_*`, `tent_birth_*`.
   - If `has_hair: true`, add the matching `*_hair` sprites.
   - If `icon != -1`, add `icon_head` (3 frames, canvas 21×26, origin 10×13)
     and optionally `icon_hair`.
4. **Map sprites to cell phases** in `clothing_standard` / `clothing_big` /
   `clothing_tent`, using `"gnx:<key>"` references back into your `sprites`
   dict. Every `leg_1`/`leg_2` variant needs its own entry; use `-1` for
   slots you don't have (e.g. `hair: -1` if `has_hair: false`).
5. Optional fields, all documented in GNX_MODDING.md §3 and §11: `fap_mul`,
   `bap_mul`, `preg_c_override`, `preg_mon_type_override`, `raid_spawns`,
   `trade_stage`, `birth_class`.

Pack sprites (step 3), then relaunch. Success looks like:
```
[GNX] class 14 registered: WITCH
```
Each sprite line should show `strip frames=N idx=ref sprite <N>` with frame
counts matching what the cell-type table expects (e.g. 90 = 3 skins × 30
frames for `idle_*`, 225 = 3 skins × 75 frames for `loop_*`). A frame-count
mismatch won't error here, but will desync animations in-game — double-check
against [GNX_MODDING.md §4](GNX_MODDING.md#4-sprite-strips).

You can test a new class immediately by giving it `raid_spawns` (so it
appears in raid encounters) — no custom cell required, since it can occupy
any vanilla cell its `mon_types`/`required_class` allow.

---

## 5. Custom cell — your own room

Goal: a new cell type (`h_type >= 43`) with its own background, hand-cursor
animation, and h-scene sprites.

**Choosing a tool — pick one:**

- **Starting from scratch** → run `scaffold_cell.py`
  (see [§8 → scaffold_cell.py](#scaffold_cellpy--generate-a-cell-stub)).
  Generates a complete stub with every sprite key pre-wired and every sprite
  folder named, ready to drop art into.

- **Prefer interactive prompts** → run `generate_cell.py` instead
  (see [§8 → generate_cell.py](#generate_cellpy--interactive-cellsjson-generator)).
  Asks questions and writes the stub; also handles vanilla patches.

**Using scaffold_cell.py:**

```bash
python <tools>/scaffold_cell.py \
  --name "MY CELL" \
  --category breed \
  --cell-prefix my_cell \
  --mod-dir "<game>/GNX_mods/my_mod"
```

This generates `cell_my_cell_scaffold.json`. The stub omits `h_type` so GNX
hash-assigns a stable ID. Merge it into your `cells.json` array, create the
sprite folders it lists, add your art, then pack (§3).

**Key fields** (full reference: first entry in `example_mod/cells.json`, "RITUAL"):

- `physical.layers`: background/foreground sprite layers — see
  [GNX_MODDING.md §7](GNX_MODDING.md#7-cell-physical-block).
- `physical.scr_idle` / `physical.scr_h`: state-machine script names.
  **These must already exist in the game's code** — GNX cells reuse existing
  scripts (e.g. `scr_slot_h_base_*`), they don't let you inject new GML. If
  you typo one, you'll see `[GNX] WARNING: script not found: <name>` and that
  phase falls back silently.
- `required_class`: restrict the cell to your custom class(es) — e.g. `[14]`
  to make it Witch-only. Accepts integer IDs or `"mod_id.ClassName"` string
  refs.
- `mon_spr`: per-phase goblin sprite assignment (`start`/`loop`, each with
  `body`, `hand`, `pen`, `touch`, optional `head`/`enter`). Every `_alpha`
  (fill) sprite needs a matching `_line` sprite — the linework overlay drawn
  on top in the game's color modes 1 and 2.
- `sprites`: strip declarations for both the cell's own background sprites
  (`wall`, `handc`, `extra`) and every goblin h-scene sprite referenced by
  `mon_spr`.

Pack sprites, relaunch. Success:
```
[GNX] cell sprites h=100: [0]=ref sprite 1400 [1]=ref sprite ...
[GNX] cell OK: h=100 name=MY CELL cat=breed
[GNX] registered N cell(s)
```
If `h_type` collides with one already registered (vanilla *or* another mod),
you'll instead get `[GNX] patched h=<N> by mod=...` and only the fields you
specified are applied on top — usually not what you want for a brand-new cell.
Omit `h_type` entirely and let GNX hash-assign one.

---

## 6. Test, debug, iterate

After every change: relaunch the game, read `gnx_debug.txt` top to bottom.
It's at `%LOCALAPPDATA%\goblin_nest\gnx_debug.txt` — cleared on every launch.

**Loader section** (one block per mod, in alphabetical load order):
```
[GNX] loader start
[GNX] mods_root=...
[GNX] loading: <name> v<version>
... per-sprite/class/cell lines ...
[GNX] registered N cell(s)
[GNX] loader done
```

**Self-test section** — runs automatically after loading:
```
[GNX-TEST] N/N passed                          (count varies with GNX version)
[GNX-TEST] DROUTE: N PASS N FAIL N SKIP        (numbers vary with game content)
```
Any `FAIL` here points at a structural problem (registry size, missing
required field) — it's not specific to your content but worth checking after
big changes.

**Common log messages and what they mean:**

| Message | Meaning | Fix |
|---|---|---|
| `mods/ folder not found, no mods loaded` | `GNX_mods/` directory missing | Create `<game_dir>/GNX_mods/` |
| `manifest not found: <path>` | Folder name ≠ `mod_id`, or no `manifest.json` | Check folder/`mod_id` match |
| `version mismatch: mod=<id> game=<ver>` | `compatible_game_versions` doesn't include the running game version | Add the version string to the array |
| `cells file not found: <path>` | `manifest.json` points to a missing `cells.json` | Fix path or remove the `"cells"` key |
| `WARNING: script not found: <name>` | `scr_idle`/`scr_h`/etc. references a nonexistent script | Use an existing vanilla script name |
| `WARN <key>: no strip/path/frames, returning fallback` | Sprite not packed yet, or `strip` key wrong | Run `gnx_pack_strips.py` |
| `class_id <N> collision — skipped` | `class_id` already used, no `override` | Pick a free `class_id`, or set `override: true` |
| `class_id <N> override` | Reskinning an existing `class_id` | Expected if intentional |
| `patched h=<N> by mod=<id>` | `h_type` already registered (vanilla or earlier mod) — only your fields applied | Expected for vanilla patches; omit `h_type` for new cells |

**In-game checks**, once `gnx_debug.txt` looks clean:
- `[GNX] REG-STANDARD class=N phase=N head/breast/leg/head_c/leg_c=...` fires
  whenever a goblin is placed in a standard cell — confirms your class's
  clothing maps resolve.
- `[GNX] class_spr h=N class=N ...` fires for goblins dispatched to a
  GNX-registered cell.

---

## 7. Going further

Once the basics above work, GNX_MODDING.md covers the rest:

- [§5 Clothing Maps](GNX_MODDING.md#5-clothing-maps) — the full structure of
  `clothing_standard`/`big`/`tent`, including how leg variants, shared sprites,
  and the `leg_any` fallback key work. Read this when your class's sprites
  aren't rendering or are rendering for the wrong leg types.

- [§9 Raid Spawns](GNX_MODDING.md#9-raid-spawns) — how to add your class to
  enemy encounter pools, control spawn rates per stage, and weight the trader
  pool. The fastest way to see your new class in-game without building a custom
  cell first.

- [§11 Trade Shop & Birth Class Mapping](GNX_MODDING.md#11-trade-shop--birth-class-mapping) —
  `trade_stage` controls whether units of your class appear in the raid trader.
  `birth_class` controls how offspring of your class map to goblin troop
  types (0-3) per species. Both are optional but matter once your mod ships
  to users with existing saves.

- [§13 Post-Raid Cage Escape](GNX_MODDING.md#13-post-raid-cage-escape) —
  boss-style characters that escape from the cage after capture, with
  configurable escape chance, popups, and event chains.

- [§14 Special Class Features](GNX_MODDING.md#14-special-class-features) —
  `max_row`, `gb1_breast_d2`, and `mon_spr_overrides` for `is_special`
  classes (Nyx/Lilith-tier) that need custom sprite handling.

- **Quest/dialog system** — see [QUESTS_SCHEMA.md](QUESTS_SCHEMA.md) for
  the full reference on events, triggers, completion conditions, and
  side effects. Declare `"quests": "quests.json"` in your manifest and
  `save_state` for persistent flags.

- **Tool system** — mods can declare tool buttons, keybinds, and cheat
  menus in `tools.json`. Declare `"tools": "tools.json"` in your manifest.
  Supports 38 action types (resources, spawning, unlocks, speed, state),
  toggle buttons with save persistence, guard conditions, and key ranges.
  See [GNX_MODDING.md](GNX_MODDING.md) for the full reference.

- **Multi-mod setups:** mods load in alphabetical folder-name order. A later
  mod can patch/override an earlier one's `h_type` or `class_id` (last-writer-
  wins). A single mod can declare multiple classes and cells in the same
  `classes.json`/`cells.json` arrays — `example_mod` shows one of each plus a
  vanilla patch, all in one `cells.json`.

---

## 8. Tooling reference

All scripts are in `<tools>/` (see [§0](#0-prerequisites) for how to find that
path). Run them with Python 3. All require Pillow (`pip install Pillow`).

---

### `export_class_sprites.py` — copy + rename a vanilla class

Use this when you want to base a new class on an existing vanilla class's
sprites. It does the mechanical rename work so you can immediately pack and
test, then replace frames with real art incrementally.

**One-time prerequisite — export vanilla sprites with UMT:**

1. Download UMT from
   [GitHub](https://github.com/krzys-h/UndertaleModTool/releases)
   and extract it.
2. Open UMT and load your game's `data.win` (File → Open).
3. Run Scripts → Export all sprites and choose an output folder — this becomes
   `<umt-sprites>/`. The export takes a few minutes and only needs to be done
   once.

**Command:**

```bash
python <tools>/export_class_sprites.py \
  --src warrior --src-id 7 \
  --dst barbarian \
  --sprites "<umt-sprites>/" \
  --output "<game>/GNX_mods/my_mod/sprites"
```

`--src` / `--src-id`: the vanilla class to copy from. `--dst`: your new class
name (used in folder naming). `--sprites`: the UMT export folder.
`--output` **must** be the `sprites/` subfolder inside your mod folder.

**Vanilla class IDs (`--src-id`):**

| ID | Class    | ID | Class    | ID | Class    |
|----|----------|----|----------|----|----------|
| 0  | Peasant  | 5  | Samurai  | 10 | Nyx      |
| 1  | Cleric   | 6  | Mage     | 11 | Giant    |
| 2  | Knight   | 7  | Warrior  | 12 | Morrigan |
| 3  | Ranger   | 8  | Lilith   | 13 | Cat      |
| 4  | Nun      | 9  | Cow      |    |          |

**What it does:** copies every sprite folder belonging to the source class and
renames it from `spr_h_warrior_*` to `spr_h_barbarian_*`. Also extracts the
three icon frames (offset = `src_id × 3` in the shared icon sheet) and copies
ogre carry sprites if they exist for the source class.

**Output:** renamed PNG folders in `--output`, plus a full `sprites` JSON
block printed to the console — copy-paste it directly into your `classes.json`
entry's `"sprites"` dict.

**After running:** follow up immediately with `scaffold_class.py` (below) to
generate the `classes.json` stub, then pack with `gnx_pack_strips.py`.

---

### `scaffold_class.py` — generate a classes.json stub from detected sprites

Run this immediately after `export_class_sprites.py`, pointing at the same mod
folder. It scans `sprites/` for all folders matching known sprite key patterns
and writes a complete `classes.json` stub with every detected sprite pre-wired
and all clothing sections built.

```bash
python <tools>/scaffold_class.py \
  --name Barbarian \
  --prefix spr_h_barbarian \
  --mod-dir "<game>/GNX_mods/my_mod"
```

`--prefix` must match the `--dst` you used in `export_class_sprites.py`.

Output: `<mod-dir>/class_barbarian_scaffold.json`. Fill in the stat fields
(`fap_mul`, `bap_mul`, `raid_spawns`, etc.), then merge the object into your
`classes.json` array.

---

### `scaffold_cell.py` — generate a cell stub

Generates a `cells.json` stub for a new cell from scratch — no existing sprites
needed. Defines the sprite folder naming convention and pre-wires all `mon_spr`
and layer refs so you know exactly which folders to create and fill.

```bash
python <tools>/scaffold_cell.py \
  --name "MY CELL" \
  --category breed \
  --cell-prefix my_cell \
  --mod-dir "<game>/GNX_mods/my_mod"
```

`--cell-prefix` is a short lowercase tag used in sprite folder names
(`spr_slot_{prefix}_*`, `spr_h_goblin_{prefix}_*`). After generating, the
script prints the full list of sprite folders to create under `sprites/`.

Output: `cell_my_cell_scaffold.json`. The stub omits `h_type` so GNX
hash-assigns a stable ID. Fill in `hand_x`/`hand_y`/`sp_x`/`sp_y` to match
your art, set `price`/`spawn_info`/`mon_types`, optionally add
`required_class`, then merge into `cells.json` and pack.

Pairs naturally with `scaffold_class.py` when adding a class + dedicated cell
together.

---

### `generate_class.py` — interactive classes.json generator

An alternative to `scaffold_class.py` for when you have no sprites yet or
prefer a guided questionnaire over a scan-based stub.

```bash
python <tools>/generate_class.py
```

Asks for class_id, override, has_hair, cell types used, stats, special sprites,
raid spawns, etc. Writes a standalone `class_<slug>.json` with a
fully-populated `sprites` dict (each entry with an explicit `folder`) and
`clothing_standard`/`big`/`tent` skeletons. Paste the resulting object into
your mod's `classes.json` array.

---

### `generate_cell.py` — interactive cells.json generator

An alternative to `scaffold_cell.py`, also handles vanilla patches.

```bash
python <tools>/generate_cell.py
```

Two modes:

- **Vanilla patch** (h_type 0–42, see §2): asks only for the four layer
  sprites and writes `physical.layers` — nothing else is touched.
- **New cell** (h_type ≥ 43, see §5): full questionnaire — name, category,
  mon_types, slot_type, price, spawn_info, optional `required_class`, h-scene
  toggle. Builds the complete `physical` block (layers, scr_idle/scr_h,
  hand positioning, splash VFX), `human_spr`, `mon_spr`, and a
  fully-populated `sprites` dict with correct frame counts (30/90 start,
  75/225 loop, matching RITUAL).

Writes a standalone `cell_<slug>.json` (or `patch_h<N>.json`). Paste the
resulting object into your mod's `cells.json` array. Advanced physical fields
(DAIRY/DRINK/tent/shrine-style mechanics) are not covered — add those by hand
if needed; see [GNX_MODDING.md §7](GNX_MODDING.md#7-cell-physical-block).

---

### `build_mod.py` — pack + verify + deploy

Replaces the manual sprite-packing and deploy steps with one command. Use this
once your mod is working and you want a clean deployment to the game folder.

```bash
python <tools>/build_mod.py <mod_dir> <game_dir> [--dry-run] [--force] [--skip-pack]
```

`<mod_dir>` is your source folder (outside the game install, contains
`manifest.json`, `sprites/`, etc.). `<game_dir>` is the game's install folder.

Steps it runs:

1. `gnx_pack_strips.py <mod_dir>` — pack sprites (skip with `--skip-pack` if
   `strips/` is already current; add `--force` to repack everything).
2. Verify every `sprites` entry in `classes.json`/`cells.json` has a `strip`
   key — warns on leftovers that would ship as fallback sprites.
3. Clean-rebuild `<game_dir>/GNX_mods/<mod_id>/` from `manifest.json`,
   the declared JSON files, and `strips/`. Source `sprites/` frames are not
   copied — only packed strips go to the game.

Use `--dry-run` to preview what would be written without touching anything.
After deploying, relaunch the game and check `gnx_debug.txt` as in §6.
