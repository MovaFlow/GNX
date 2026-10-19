# GNX Modding Guide

Reference for writing mods for Goblin Nest with GNX (Goblin Nest Extender) 1.4.9, game version 1.40. Written by Mav. Quests have their own reference in `QUESTS_SCHEMA.md`; a step-by-step walkthrough is in `TUTORIAL.md`.

## Contents

- [1. How to read this guide](#1-how-to-read-this-guide)
- [2. Glossary](#2-glossary)
- [3. Mod folder and loading](#3-mod-folder-and-loading)
- [4. manifest.json](#4-manifestjson)
- [5. Sprites](#5-sprites)
- [6. Classes (classes.json)](#6-classes-classesjson)
- [7. Clothing maps: how a class looks in each cell](#7-clothing-maps-how-a-class-looks-in-each-cell)
- [8. Cells (cells.json)](#8-cells-cellsjson)
- [9. The physical block: how a cell behaves](#9-the-physical-block-how-a-cell-behaves)
- [10. Cell sprites: human_spr and mon_spr](#10-cell-sprites-human_spr-and-mon_spr)
- [11. Multi-monster cells](#11-multi-monster-cells)
- [12. Patching vanilla cells and classes](#12-patching-vanilla-cells-and-classes)
- [13. Raid spawns and the trade shop](#13-raid-spawns-and-the-trade-shop)
- [14. Pregnancy and birth](#14-pregnancy-and-birth)
- [15. Bosses: cage escape and tower](#15-bosses-cage-escape-and-tower)
- [16. Special classes and monster sprite overrides](#16-special-classes-and-monster-sprite-overrides)
- [17. Tools (tools.json)](#17-tools-toolsjson)
- [18. Sounds (sounds.json)](#18-sounds-soundsjson)
- [19. Props (props.json)](#19-props-propsjson)
- [20. Atlas packing](#20-atlas-packing)
- [21. Multi-map travel](#21-multi-map-travel)
- [Appendix A. Vanilla IDs and cell list](#appendix-a-vanilla-ids-and-cell-list)
- [Appendix B. Troubleshooting](#appendix-b-troubleshooting)

## 1. How to read this guide

**In short:** how to build a Goblin Nest mod with GNX (Goblin Nest Extender), the layer that loads JSON files into the game. Written for beginners: every key and term is explained where it first appears, and every feature has a small example to copy.

### 1.1 Who this guide is for

- You want to add captive classes, cells, quests, tool buttons, sounds or props to Goblin Nest.
- You can edit text files and draw PNG images. No programming or GameMaker knowledge is needed.
- For a first mod, read sections 1–5, then follow [TUTORIAL.md](TUTORIAL.md), then the section for the feature you need.

### 1.2 Versions covered

- **GNX 1.4.9** on **Goblin Nest 1.40**. Mods marked for game versions 1.38 and 1.39 are accepted too ([4.2](#42-the-version-check)).
- Features new in 1.4.9 say so where they are described. A mod that uses them needs GNX 1.4.9; `CHANGELOG.md` lists every change.
- The statements in this guide were checked against the GNX source code.

### 1.3 JSON in two minutes

All GNX data files are JSON, a plain-text format for structured data (images are PNG, sounds OGG). A small piece of a class entry:

```json
{
  "name": "Witch",
  "is_special": false,
  "fap_mul": 1.5,
  "icon_hair": -1,
  "raid_spawns": [
    { "stage": 0, "level": 1, "weight": 10 }
  ]
}
```

- `{ ... }` is an **object**: a group of named values. Each entry is a **key** (text in double quotes), a colon `:` and a **value**. Entries are separated by commas.
- `[ ... ]` is a **list** (JSON calls it an *array*): values in a fixed order, separated by commas. `raid_spawns` is a list holding one object.
- A value is **text** (JSON: *string*) in double quotes, like `"Witch"`; a **number**, like `10`, `1.5` or `-1`; **true/false**; or another object or list. Only text takes quotes, and only double quotes.
- **Text and numbers are different.** `"required_class": 11` means class number 11; `"required_class": "11"` looks for a class *named* "11" and fails with a warning. Write ID numbers without quotes.
- **Keys must be spelled exactly**, including upper and lower case. A misspelled key such as `"Is_special"` is treated as missing.
- **No comments, no trailing commas**: no `//`, no `/* */`, no comma after the last item. An invalid file is rejected with an `invalid` error ([Appendix B](#appendix-b-troubleshooting)).
- **Use `/` in file paths**, for example `"strips/spr_h_witch_idle_head.png"`; a single `\` breaks the text.

> **Tip:** an online JSON validator finds missing commas and quotes in seconds.

### 1.4 What `-1` means

In GNX files `-1` almost always means **"none" or "not used"**: `"icon_hair": -1` means no hair layer on the icon, a sprite value of `-1` draws nothing, and `"slot_dirt_init": -1` means the cell never gets dirty. A few keys give `-1` a special meaning; their sections say so. Write it as a number, without quotes.

`0` is not "none": in a sprite field it is game sprite number 0 ([5.4](#54-gnx-references-and-vanilla-sprite-names)).

### 1.5 How this guide is laid out

- A main section starts with **In short**, then a minimal example and its explanation, field tables, more examples, and **When** boxes: a situation (mostly a common mistake) and what GNX does in it.
- **Field tables** have four columns: `Key | What it means | Type | Default`.
  - Type words: `number`, `text`, `true/false`, `list`, `object`, `sprite`, `sprite or -1`. A `sprite` is a `gnx:` reference to your own sprite or the name of a game sprite ([5.4](#54-gnx-references-and-vanilla-sprite-names)).
  - Default: `required` = GNX needs the key; a value = used when the key is left out; `—` = the feature is off without the key.
- **Examples** are valid JSON and belong to one example mod: folder `my_mod`, normal class `Witch` (files `strips/spr_h_witch_...png`), special class `Queen`, standard cell `ALTAR`, big cell `BIG ALTAR`, state key `witch_state`.
- **Log lines** from `gnx_debug.txt` are exact; parts in `<angle brackets>` vary.

### 1.6 Where to look

| I want to… | Read |
|---|---|
| Build my first mod step by step | [TUTORIAL.md](TUTORIAL.md) |
| Look up a word | [2. Glossary](#2-glossary) |
| Set up the folder, understand load order, find the log | [3. Mod folder and loading](#3-mod-folder-and-loading) |
| Write `manifest.json` or save my own variables | [4. manifest.json](#4-manifestjson) |
| Add images | [5. Sprites](#5-sprites) |
| Add a new captive class | [6. Classes](#6-classes-classesjson), [7. Clothing maps](#7-clothing-maps-how-a-class-looks-in-each-cell) |
| Add a new cell | [8. Cells](#8-cells-cellsjson), [9. The physical block](#9-the-physical-block-how-a-cell-behaves), [10. Cell sprites](#10-cell-sprites-human_spr-and-mon_spr), [11. Multi-monster cells](#11-multi-monster-cells) |
| Change a vanilla cell or class | [12. Patching](#12-patching-vanilla-cells-and-classes) |
| Make my class appear in raids or the shop | [13. Raid spawns and the trade shop](#13-raid-spawns-and-the-trade-shop) |
| Control pregnancy and offspring | [14. Pregnancy and birth](#14-pregnancy-and-birth) |
| Make a boss | [15. Bosses](#15-bosses-cage-escape-and-tower), [16. Special classes](#16-special-classes-and-monster-sprite-overrides) |
| Add buttons, keybinds, sounds or props | [17. Tools](#17-tools-toolsjson), [18. Sounds](#18-sounds-soundsjson), [19. Props](#19-props-propsjson) |
| Make many sprites load faster | [20. Atlas packing](#20-atlas-packing) |
| Write quests and events | [QUESTS_SCHEMA.md](QUESTS_SCHEMA.md) |
| Look up a vanilla ID number | [Appendix A](#appendix-a-vanilla-ids-and-cell-list) |
| Fix an error | [Appendix B](#appendix-b-troubleshooting) |

---

## 2. Glossary

**In short:** plain definitions of the words used in this guide. Each row links to the section with the details.

| Term | Meaning |
|---|---|
| alpha / line | A monster sprite pair: `alpha` is the filled body (tinted or see-through per the game's monster display settings), `line` the outline on top. [§10](#10-cell-sprites-human_spr-and-mon_spr) |
| atlas | One large PNG with many sprites plus `uv.json` with their positions; optional, loads faster. [§20](#20-atlas-packing) |
| base_body | `human_spr` key naming the set of vanilla body poses used for the captive: `standard`, `big` or `tent`. [§10](#10-cell-sprites-human_spr-and-mon_spr) |
| by_class | In a fixed-mode `human_spr`: sprites per class, so classes can look different in the same cell. [§10](#10-cell-sprites-human_spr-and-mon_spr) |
| captive | See *unit*. |
| category | cells.json key: the cell's build-menu tab and, with it, the cell size. [§8](#8-cells-cellsjson) |
| cell | A nest room where a captive is placed and monsters visit her. Its type ID is `h_type`. [§8](#8-cells-cellsjson) |
| class | A type of captive, such as Peasant, Cleric or your Witch. [§6](#6-classes-classesjson) |
| class_id | A class's ID number: vanilla classes are 0–13, mod classes get a hash ID. [§6](#6-classes-classesjson), [Appendix A](#appendix-a-vanilla-ids-and-cell-list) |
| clothed variant (`_c`) | An overlay (usually clothes) over a body part, with the same frame layout: keys ending in `_c`, `spr_c_array` lists. [§7](#7-clothing-maps-how-a-class-looks-in-each-cell) |
| condition | A test such as "state key `witch_state` equals 2", checked by quests, conditional raid spawns, cage escape, tower bosses and tool guards. [QUESTS_SCHEMA.md](QUESTS_SCHEMA.md), [§13](#13-raid-spawns-and-the-trade-shop) |
| encounter pool | The weighted list of classes a raid encounter picks from, one per stage and encounter level. [§13](#13-raid-spawns-and-the-trade-shop) |
| fixed mode | `"mode": "fixed"` in `human_spr`: the cell draws its own human sprites instead of the captive's clothing. [§10](#10-cell-sprites-human_spr-and-mon_spr) |
| frame | One picture of an animation. [§5](#5-sprites) |
| gnx: reference | Text such as `"gnx:idle_head"`: the entry `idle_head` from the `sprites` dict of the same class or cell. [5.4](#54-gnx-references-and-vanilla-sprite-names) |
| h_type | A cell type's ID: vanilla 1–42 (0, 16, 26, 35 are not cells), mod cells a hash ID 100–9999. [§8](#8-cells-cellsjson), [Appendix A](#appendix-a-vanilla-ids-and-cell-list) |
| hash ID | An ID GNX calculates from `"<folder>.<name>"`: same text, same number; a rename changes it. [3.4](#34-duplicate-ids) |
| human_spr | Cell key that decides which captive sprites the cell draws. [§10](#10-cell-sprites-human_spr-and-mon_spr) |
| is_special | Class flag for boss-type classes: one skin tone, a different clothing format and some extra rules. [§16](#16-special-classes-and-monster-sprite-overrides) |
| layer | One entry of `physical.layers`: a sprite and a layer type, drawn in list order. [§9](#9-the-physical-block-how-a-cell-behaves) |
| leg variant | The captive's leg pose: `leg_1` or `leg_2` (random for most classes) or `leg_0` (the kneeling body of Shaman and Warrior). `leg_any` in a clothing map is the fallback for a missing leg key. [§7](#7-clothing-maps-how-a-class-looks-in-each-cell) |
| manifest | `manifest.json`, the file that turns a folder into a mod. [§4](#4-manifestjson) |
| mod folder | A folder directly inside `GNX_mods/`. Its name is the mod's identity. [§3](#3-mod-folder-and-loading) |
| mon_spr | Cell key holding the monster sprites for that cell. [§10](#10-cell-sprites-human_spr-and-mon_spr) |
| mon_type | Monster species number: 0 goblin, 1 hobgoblin, 2 tentacle, 3 ogre. [Appendix A](#appendix-a-vanilla-ids-and-cell-list) |
| origin (xorig / yorig) | A sprite's pivot point in pixels from its top-left corner, placed on the drawing position. [5.3](#53-the-origin) |
| override | `"override": true` on a class entry: merges your fields into an existing class, or registers a class at a fixed `class_id`. [§6](#6-classes-classesjson), [§12](#12-patching-vanilla-cells-and-classes) |
| patch (vanilla patch) | A cells.json entry with an existing `h_type`: it changes that cell instead of creating one. [§12](#12-patching-vanilla-cells-and-classes) |
| phase | A cell animation stage: 0 start, 1 idle, 2 loop, 3 ejaculation, 4 birth (tentacle cells). Class sprites reuse the loop sprites for phase 3. [§10](#10-cell-sprites-human_spr-and-mon_spr) |
| placement | A numbered monster position in a cell that holds more than one monster. [§11](#11-multi-monster-cells) |
| required_class | Cell key listing the classes allowed into the cell. [§9](#9-the-physical-block-how-a-cell-behaves) |
| save state | Your mod's saved variables (`save_state.fields` in the manifest); each name, such as `witch_state`, is a **state key**. [4.3](#43-save_state) |
| skin | Skin tone 0–2 of a normal-class captive; body strips hold 3 skin versions of each pose. Special classes have one. [5.5](#55-how-frames-are-arranged-in-a-strip) |
| slot | (1) The game's internal word for a cell. (2) A numbered position in the `spr_array` / `spr_c_array` lists. [§7](#7-clothing-maps-how-a-class-looks-in-each-cell), [§8](#8-cells-cellsjson) |
| slot type | Cell size: small, big, tentacle or XL. It comes from `category`; the `slot_type` number in cells.json only affects the default `base_body` ([10.1](#101-human_spr-the-three-modes)). [§8](#8-cells-cellsjson) |
| sprite | An image or animation, made of one or more frames. [§5](#5-sprites) |
| sprite key | The name of an entry in a `sprites` dict, for example `idle_head`, used as `"gnx:idle_head"`. [5.1](#51-the-sprites-dict) |
| stage | A raid area: 0 Village, 1 Mountain, 2 Forest, 3 Castle, 4 Tower. [Appendix A](#appendix-a-vanilla-ids-and-cell-list), [§13](#13-raid-spawns-and-the-trade-shop) |
| state key | See *save state*. |
| strip | One PNG holding all frames of a sprite side by side, left to right. [§5](#5-sprites) |
| string reference | Text `"<folder>.<name>"` pointing at a class or cell, for example `"my_mod.Witch"`. It is case-sensitive. [§6](#6-classes-classesjson), [3.3](#33-load-order) |
| unit / captive | A captured human. The game code calls captives "units". [§6](#6-classes-classesjson) |
| vanilla | The original game without mods. |

---

## 3. Mod folder and loading

**In short:** a mod is one folder inside `GNX_mods/` that contains a `manifest.json`. GNX finds these folders when the game starts, loads them in alphabetical order, and writes everything it does into the log file `gnx_debug.txt`.

### 3.1 Folder layout

```
<game folder>/                  the folder that holds the game's .exe
  GNX_mods/
    my_mod/                     your mod folder; its name is the mod's identity
      manifest.json             required: makes this folder a mod (section 4)
      classes.json              optional: new captive classes (section 6)
      cells.json                optional: new cells (section 8)
      quests.json               optional: events and quests (QUESTS_SCHEMA.md)
      tools.json                optional: tool buttons and keybinds (section 17)
      sounds.json               optional: voices and sound effects (section 18)
      props.json                optional: decoration props (section 19)
      strips/                   your sprite strips (name is a convention)
        spr_h_witch_idle_head.png
      sprites/                  per-frame PNG folders for "folder" sprites (name is a convention)
        witch_icon/
      sounds/                   .ogg files for sounds.json (fixed name)
      portraits/                quest portraits (fixed name)
      atlas/                    optional packed atlas with uv.json (section 20)
```

- `GNX_mods/` sits next to the game's executable; the log line `[GNX] mods_root=<path>` shows the exact path.
- Data files load **only when `manifest.json` names them** ([4.4](#44-data-file-keys)), so their names are free. So are `strips/` and `sprites/`: sprite paths are relative to the mod folder ([5.2](#52-where-gnx-takes-the-image-from)).
- `sounds/` and `portraits/` are **fixed names**.
- `atlas/` is used only when it contains a `uv.json` file ([§20](#20-atlas-packing)).

### 3.2 How GNX finds mods

- At game start GNX checks every folder **directly** inside `GNX_mods/`. A folder with a `manifest.json` is a mod; there is no index file to edit.
- A folder without a `manifest.json` is skipped with `[GNX-WARN] folder '<name>' has no manifest.json, skipped`
- If `GNX_mods/` itself is missing, GNX writes `[GNX] mods/ folder not found, no mods loaded`.
- To switch a mod off, use the MODS menu ([4.5](#45-requires-and-the-mods-menu)) or move its folder out of `GNX_mods/`.

> **When** the manifest sits one folder too deep (`GNX_mods/my_mod/my_mod/manifest.json`), the mod is not found; only `GNX_mods/my_mod/manifest.json` counts. This often happens after unzipping a download into a folder of the same name.

### 3.3 Load order

GNX loads mods **in alphabetical order of their folder names**, comparing character codes: digits before capital letters, capital letters before small ones. Example order: `01_base`, `Zeta`, `alpha`, `my_mod`.

Loading runs in **three phases**, alphabetical inside each:

1. save state from the manifest ([4.3](#43-save_state)), the atlas and the `classes` file of **every** mod;
2. the `cells` file of every mod;
3. the `quests`, `tools`, `sounds` and `props` files of every mod.

Mods switched off in the MODS menu, or whose `requires` are missing, are not loaded at all ([4.5](#45-requires-and-the-mods-menu)). Mods with their own map load their content only on that map ([§21](#21-multi-map-travel)).

**String references** (`"<folder>.<name>"`) work across mods whatever the folder names:

- `required_class` and fixed-mode `by_class`: looked up after all classes have loaded;
- `class_map` `classes` and text entries in `birth_classes`: after all mods have loaded;
- cell names in class conditions (such as `cell_built` in `raid_spawns`): after phase 2.

Only changing another mod's class (`override`) or cell (a patch) needs your mod to load **after** that mod.

Example: `my_mod/cells.json` has `"required_class": ["my_mod.Witch", "zz_extra.Nun"]`. Both refs are found, although `zz_extra` sorts after `my_mod`. If a ref is misspelled, or its mod is missing or switched off, GNX writes:

```
[GNX-WARN] cell h=8040 required_class ref 'zz_extra.Nun' not found. Check: folder name + class name must match exactly (case-sensitive).
```

(8040 is the hash ID of `my_mod.ALTAR`.) Use `requires` ([4.5](#45-requires-and-the-mods-menu)) so your mod does not load without the mod it needs.

### 3.4 Duplicate IDs

**Classes.** A new class gets a hash ID (14–9999) from `"<folder>.<name>"`. If that number is taken, GNX uses the next free one, so two mods never overwrite each other's classes by accident.

- An existing class is changed **only** by an entry with `"override": true` and an existing `class_id`. Your fields are then merged into it, and the log says `[GNX] class_id <N> override (merge)`.
- A `class_id` without `"override": true` is ignored ([§6](#6-classes-classesjson), [§12](#12-patching-vanilla-cells-and-classes)).

**Cells.** A new cell without `h_type` gets a hash ID (100–9999), also moving to the next free number if needed.

- An explicit `h_type` that **already exists** does not create a new cell. The entry becomes a **patch** that changes some fields of that cell ([§12](#12-patching-vanilla-cells-and-classes)). The log says `[GNX] patched h=<N> by mod=<folder>`, plus a warning for vanilla IDs 1–42.

**Keeping IDs stable.** A hash ID stays the same at every game start unless the folder or `name` is renamed or an earlier-loading mod takes the number first.

> **When** the mod folder, a class `name` or a cell `name` is renamed after release, the IDs change and saved games lose that content. On loading, a captive of an unknown class becomes a new peasant, and a cell of an unknown type is rebuilt as an empty WALL 1, G.BANG 1 or T.WALL 1, depending on its size; the log shows `[GNX-SANITIZE]` lines. The mod's saved state is stored under the folder name too ([4.3](#43-save_state)).

### 3.5 The log file: gnx_debug.txt

GNX writes every loading step, warning and error into `gnx_debug.txt`.

- **Where:** in the game's save folder, not the game folder. On Windows usually `%LOCALAPPDATA%\goblin_nest\gnx_debug.txt`; otherwise search your computer for the file name.
- **When:** the file is rewritten every time GNX loads mods: at game start and when you quit to the main menu. Copy it before restarting if you want to keep it.
- **Errors also pop up.** If any mod has an `ERROR` line, a message box appears at the end of loading. It starts with `Mod loading problem(s):` and ends with `Details in gnx_debug.txt.`

A healthy start for the example mod (shortened with `...`):

```
[GNX] loader start
[GNX] mods_root=<game folder>\GNX_mods/
[GNX] loading: My Mod v1.0.0
[GNX] mod_state init: my_mod v1 keys=2
...
[GNX] class 4305 registered: Witch
...
[GNX] cell OK: h=8040 name=ALTAR cat=breed
[GNX] registered 1 cell(s)
...
[GNX] loader done
...
[GNX-TEST] N/N passed
```

What to look for, in this order:

1. `[GNX] loading: <name> v<version>`: manifest found, version check passed. If missing, look for `[GNX-WARN] folder ...` or `[GNX] ERROR: Mod '<folder>': ...`.
2. `[GNX] mod_state init: <folder> v<N> keys=<N>`: your save state was set up. `keys` counts your fields plus the built-in `_version`.
3. `[GNX] class <N> registered: <name>` and `[GNX] cell OK: h=<N> name=<name> cat=<category>`: the ID each entry got, needed for numeric IDs elsewhere.
4. Any line with `ERROR`, `WARN` or `FAIL`; [Appendix B](#appendix-b-troubleshooting) explains them.

---

## 4. manifest.json

**In short:** `manifest.json` makes a folder a mod. It names the mod, lists the game versions it supports and the data files to load, and declares the mod's own saved variables. Every mod needs one.

```json
{
  "name": "My Mod",
  "version": "1.0.0",
  "compatible_game_versions": ["1.40"],
  "classes": "classes.json",
  "cells": "cells.json",
  "save_state": {
    "version": 1,
    "fields": { "witch_state": 0 }
  }
}
```

What this example does:

- `name` and `version` appear in the MODS menu ([4.5](#45-requires-and-the-mods-menu)) and in the log line `[GNX] loading: My Mod v1.0.0`.
- `compatible_game_versions`: the game versions the mod is made for (`"1.40"` is current).
- `classes` and `cells` make GNX load those two files; unlisted files are not loaded.
- `save_state` declares a saved variable `witch_state`, starting at `0` in every new game.
- The mod's identity is the **folder name** (`my_mod`): references such as `"my_mod.Witch"`, the saved state and the hash IDs use it, not anything in this file.

### 4.1 Fields

| Key | What it means | Type | Default |
|---|---|---|---|
| `name` | Display name in the MODS menu and the log. | text | required |
| `version` | Your mod version, for example `"1.0.0"`, shown in the MODS menu and the log. | text | required |
| `compatible_game_versions` | Must contain `"1.38"`, `"1.39"` or `"1.40"` ([4.2](#42-the-version-check)). | list | required |
| `classes`, `cells`, `quests`, `tools`, `sounds`, `props` | Paths of the data files, relative to the mod folder ([4.4](#44-data-file-keys)); see [§6](#6-classes-classesjson), [§8](#8-cells-cellsjson), [QUESTS_SCHEMA.md](QUESTS_SCHEMA.md), [§17](#17-tools-toolsjson), [§18](#18-sounds-soundsjson), [§19](#19-props-propsjson). | text | — |
| `save_state` | Saved variables ([4.3](#43-save_state)). | object | — |
| `mod_id` | A second name for other mods' `requires`, usually the folder name. References always use the folder name. | text | — |
| `requires` | Mods this one needs, by folder name or `mod_id` ([4.5](#45-requires-and-the-mods-menu)). | list | — |
| `map`, `map_info`, `map_start` | Which map(s) the mod belongs to, and your own map for multi-map travel ([§21](#21-multi-map-travel)). `map_info` was called `map_button` before 1.4.9; the old name is still read. | — | — |

### 4.2 The version check

GNX does not compare your list with the running game version. It checks that `compatible_game_versions` contains **at least one version GNX accepts: `"1.38"`, `"1.39"` or `"1.40"`**, so a mod marked `["1.39"]` still loads on game 1.40.

With no match, or without the key, the mod is **not loaded at all**. GNX writes this line and also shows it in the error box at the end of loading:

```
[GNX] ERROR: Mod 'my_mod': incompatible with game version 1.40 (compatible: <your list>)
```

> **When** the versions are written as numbers instead of quoted text, they never match: write `["1.40"]`. `"1.33"` from old tutorials is rejected too.

### 4.3 save_state

**In short:** `save_state` lets your mod remember things, such as "has the witch quest started?", in the player's save file.

```json
{
  "save_state": {
    "version": 2,
    "fields": { "witch_state": 0, "altar_uses": 0 }
  }
}
```

- `fields` declares two **state keys** (saved variables) with their **defaults** for a new game.
- `version` is a number you raise when the field list changes, saved as `_version`; it is unrelated to the mod's top-level `version`.

| Key | What it means | Type | Default |
|---|---|---|---|
| `version` | Version of your field list, stored as `_version`. GNX never converts your fields when it changes. | number | 1 (0 without `save_state`) |
| `fields` | State keys and their start values. Use numbers: `state_gte` and `state_lte` compare sizes. | object | — |

How GNX handles the saved state:

- **New game, or a save that has never seen your mod:** every field gets its default.
- **A save that already has your state:** saved values stay, new fields get their defaults, and removed fields stay in the save. Field values are never migrated. `_version` is raised to your `version` when GNX sets up an existing state at mod load, but a state restored from a save keeps its saved number, so do not rely on `_version` to detect a migration.
- The state is stored under the **folder name**; after a rename, old saves get a fresh state.
- The log line `[GNX] mod_state init: my_mod v2 keys=3` confirms the setup; `keys` counts your fields plus `_version`.

State keys are read and written by quests (the `set_state` side effect and the `state_equals` / `state_gte` / `state_lte` conditions, [QUESTS_SCHEMA.md](QUESTS_SCHEMA.md)), tools (the `set_state` action and toggle buttons, [§17](#17-tools-toolsjson)), conditional raid spawns ([§13](#13-raid-spawns-and-the-trade-shop)), and cage escape counters and tower boss conditions ([§15](#15-bosses-cage-escape-and-tower)).

> **When** a field is named `_version`, it clashes with the name GNX reserves for itself. Pick another name.

### 4.4 Data file keys

Each data file key (`classes`, `cells`, `quests`, `tools`, `sounds`, `props`) holds a path relative to your mod folder. The file is loaded only when its key is present.

```json
{
  "name": "My Mod",
  "version": "1.2.0",
  "compatible_game_versions": ["1.40"],
  "classes": "classes.json",
  "cells": "cells.json",
  "quests": "quests.json",
  "tools": "tools.json",
  "sounds": "sounds.json",
  "props": "props.json"
}
```

This loads all six files, in the phases of [3.3](#33-load-order). Paths can point into subfolders, for example `"cells": "data/cells.json"`.

A listed file that is missing or broken is skipped with an error, shown in the message box too:

```
[GNX] ERROR: Mod 'my_mod': cells file 'cells.json' not found
[GNX] ERROR: Mod 'my_mod': cells.json invalid (<message from the JSON reader>)
```

> **When** a data file such as `cells.json` is in the mod folder but not listed in the manifest, GNX **does not load it** and only writes: `[GNX-WARN] mod 'my_mod': cells.json exists but is not declared in manifest.json`

### 4.5 requires and the MODS menu

**In short:** players can switch mods on and off in the game, and your mod can say which other mods it needs.

```json
{
  "name": "Aura Mira",
  "version": "1.0.0",
  "compatible_game_versions": ["1.40"],
  "mod_id": "Aura_Mira",
  "requires": ["Aura"],
  "classes": "classes.json",
  "cells": "cells.json"
}
```

- `requires` lists needed mods by folder name or `mod_id`, here the folder `Aura`.
- If `Aura` is switched off, `Aura Mira` is skipped too; if `Aura` is not installed, it is skipped and reported in the `Mod loading problem(s)` box.
- `requires` does not change the load order ([3.3](#33-load-order)): a mod that patches another mod's cell still needs a folder name that sorts later.

**The MODS menu.** A button in the main menu where the player switches mods on and off.

- The choice is stored in `gnx_mods_off.json` in the save folder and applies to every save. The mod files stay in `GNX_mods/`.
- Every save remembers its mods and what it uses from each (cells, characters, a map). The menu warns before switching off a used mod, and the load page before loading a save whose mods are off or missing.
- Loading such a save turns the missing mod's cells into basic vanilla cells and its characters into peasants. Saving then removes that content from the save for good. Back up the save before loading it with mods missing; if you loaded it anyway, do not save over it, but switch the mods back on and load the original save again.

> **When** a mod seems to have vanished, check the MODS menu first: it may simply be switched off.

---

## 5. Sprites

**In short:** a sprite is an image or animation. Each class or cell entry declares its sprites in a `sprites` dict (where the PNG is, how to cut it into frames); other keys use them through `gnx:` references.

```json
{
  "name": "Witch",
  "sprites": {
    "idle_head": { "strip": "strips/spr_h_witch_idle_head.png", "frames": 90, "xorig": 0, "yorig": 90 },
    "icon_head": { "strip": "strips/spr_h_witch_icon_head.png", "frames": 3, "xorig": 10, "yorig": 13 }
  },
  "icon": "gnx:icon_head"
}
```

This is part of the Witch entry in `classes.json`:

- `idle_head` and `icon_head` are **sprite keys** of your choice.
- `idle_head` cuts the **strip** (one PNG with all frames side by side) into 90 equal frames; `xorig` / `yorig` set its **origin**, the pivot point ([5.3](#53-the-origin)).
- `icon_head` has 3 frames, one per skin tone. `"icon": "gnx:icon_head"` makes it the class icon; `gnx:` means "from this entry's own `sprites` dict".
- The head strip would be used from the clothing map ([§7](#7-clothing-maps-how-a-class-looks-in-each-cell)), for example `"head": "gnx:idle_head"`.

### 5.1 The sprites dict

- Every class entry and every cell entry can have its own `sprites` dict.
- A `gnx:` reference sees only the dict of **the same entry**: a cell cannot reach a class's sprites, and the other way round.
- Key names are your choice (`idle_head`, `loop_breast` are only conventions). Exceptions: GNX picks up `carry_head` and `carry_hair` in a class ([§6](#6-classes-classesjson)) and `wall` in a cell ([§8](#8-cells-cellsjson)) by themselves.
- An entry nothing refers to is never used. One key can be used in many places; GNX loads each file only once.

### 5.2 Where GNX takes the image from

There is **no `mode` key**. GNX uses the first of these keys that the entry has:

| Order | Key you write | What GNX loads |
|---|---|---|
| 1 | `strip` | One PNG, cut into `frames` pieces of equal width, from left to right. |
| 2 | `frames` as a list of paths | Each listed PNG is one frame, in list order. |
| 3 | `path` | One PNG = one frame. |
| 4 | `folder` | All PNGs in a folder, sorted by the number at the end of the file name. |
| 5 | `from_game` | One frame copied from a vanilla game sprite. |
| 6 | plain text instead of an object | One PNG = one frame, origin 0, 0. |

If the mod has an atlas, GNX checks it before all of these ([§20](#20-atlas-packing)).

| Key | What it means | Type | Default |
|---|---|---|---|
| `strip` | Path of a PNG strip, relative to the mod folder. | text | — |
| `frames` | With `strip`: the number of frames. Without `strip`: a list of PNG paths, one per frame. | number or list | 1 |
| `path` | Path of a single-frame PNG. | text | — |
| `folder` | Folder of per-frame PNGs. If it does not exist, GNX tries `strips/<folder>`. | text | — |
| `from_game` | Name of a vanilla sprite; GNX copies **one** frame of it. | text | — |
| `index` | Which frame `from_game` copies (0 = first). | number | 0 |
| `xorig`, `yorig` | Origin: pixels from the left and top edge of a frame. | number | 0 |
| `origin_from` | Vanilla sprite whose origin is copied, instead of `xorig` / `yorig`. | text | — |
| `canvas_w`, `canvas_h` | **Ignored.** A strip's frame width is always the PNG width divided by `frames`. | number | — |

**Strip** (the normal case, as in the example above). The PNG must be exactly `frames` × one frame wide.

**Folder.** Handy while drawing: each frame is its own file and nothing needs packing.

```json
{
  "icon_head": { "folder": "sprites/witch_icon", "xorig": 10, "yorig": 13 }
}
```

- GNX loads every `.png` in `<mod>/sprites/witch_icon/`, or in `<mod>/strips/sprites/witch_icon/` if the first folder does not exist.
- Files are sorted by their end number (`icon_10.png` after `icon_9.png`); if any file has one, files without are skipped.
- All files must be the same size as the first. `frames` is not needed.

**List of files.** Like a folder, but you choose the files and their order:

```json
{
  "icon_head": {
    "frames": ["sprites/witch_icon_0.png", "sprites/witch_icon_1.png", "sprites/witch_icon_2.png"],
    "xorig": 10,
    "yorig": 13
  }
}
```

**Single image.** `path` gives one frame with your origin; plain text gives one frame with origin 0, 0:

```json
{
  "altar_sign": { "path": "strips/spr_altar_sign.png", "xorig": 0, "yorig": 0 },
  "altar_back": "strips/spr_altar_back.png"
}
```

**One frame of a vanilla sprite.** `from_game` keeps the vanilla sprite's origin (`xorig` / `yorig` are ignored):

```json
{
  "peasant_head_still": { "from_game": "spr_h_peasant_idle_head", "index": 0 }
}
```

A **whole** vanilla sprite with all its frames needs no `sprites` entry: write its name where it is used, for example `"head": "spr_h_peasant_idle_head"` ([5.4](#54-gnx-references-and-vanilla-sprite-names)).

> **When** a sprite entry uses `"mode"`, GNX ignores the key. An entry with `"mode": "folder"` and `strip` is loaded as a strip, fails and draws nothing. Write `{ "folder": "..." }` or `{ "from_game": "...", "index": 0 }` instead.

> **When** an entry has both `strip` and `folder`, only `strip` is used.

> **When** two entries use the same PNG with the same `frames` and origin, GNX loads the file once and both share it. With a different `frames`, `xorig`/`yorig` or `origin_from`, each entry gets its own sprite.

### 5.3 The origin

The **origin** is the point GNX places on the drawing position, in pixels from a frame's top-left corner. All captive body parts are drawn at the cell's position, so each needs the origin of the vanilla sprite it replaces, or the parts shift.

- Existing class mods use `"xorig": 0, "yorig": 90` for standard-cell body strips.
- The safest way is `origin_from`, which copies the origin of a vanilla sprite:

```json
{
  "idle_head": { "strip": "strips/spr_h_witch_idle_head.png", "frames": 90, "origin_from": "spr_h_peasant_idle_head" }
}
```

- If the name in `origin_from` is not a game sprite (here a typo), GNX uses `xorig` / `yorig` and writes:
  `[GNX-WARN] idle_head: origin_from 'spr_h_peasant_idle_haed' is not a game sprite - using xorig/yorig`
- The class icon uses origin 10, 13 ([5.7](#57-hand-icon-and-carry-sprites)).

### 5.4 gnx: references and vanilla sprite names

Wherever GNX expects a sprite (clothing maps, icons, cell layers, `human_spr`, `mon_spr` and so on), you can write:

| You write | GNX uses |
|---|---|
| `"gnx:idle_head"` | The entry `idle_head` from the `sprites` dict of the same class or cell. |
| `"spr_h_peasant_idle_head"` | The vanilla game sprite with that name, with all its frames. |
| `-1` | Nothing. |

> **When** a `gnx:` key does not exist or a vanilla name has a typo, the result is `-1`: nothing is drawn and **no warning is written**, so check spelling and case first when a part is invisible. Exception: in a class's clothing and naked maps GNX draws the vanilla sprite instead and writes a warning ([6.2](#62-override-changing-an-existing-class)).

> **When** a sprite field holds a number other than `-1`, GNX uses it as a game sprite number. `0` does not mean "none".

### 5.5 How frames are arranged in a strip

Captive body sprites (head, breast, leg, leg part, cape and their `_c` overlays) are not simple animations. One strip holds the poses of **every cell** that shares the sprite, for **every skin tone**. GNX picks the frame like this:

```
frame number = (row × skins + skin) × frames_per_phase + frame
```

- `row`: the cell pose; each vanilla cell drawing class sprites has one ("Strip row" in [Appendix A](#appendix-a-vanilla-ids-and-cell-list)), and a custom cell picks one with `character_row` ([§9](#9-the-physical-block-how-a-cell-behaves)).
- `skins` / `skin`: 3 and 0–2 for normal classes, 1 and 0 for special classes.
- `frames_per_phase`: 2 for idle (also the start in standard cells) and tentacle birth, 5 for loop (also ejaculation).
- `frame`: the frame inside that short animation, from 0.

So the strip goes **row by row**, inside each row **skin by skin**, and inside each skin **frame by frame**. The idle strip of a normal class:

```
frames:  0-1    2-3    4-5   |  6-7    8-9    10-11  | ... |  84-85  86-87  88-89
         skin0  skin1  skin2 |  skin0  skin1  skin2  | ... |  skin0  skin1  skin2
         row 0 (WALL 1)      |  row 1 (WALL 2)       | ... |  row 14 (FOREPLAY)
```

Example: a Witch with skin 2 in WALL 2 (row 1), idle frame 1: `(1 × 3 + 2) × 2 + 1 = 11`, the 12th picture in the strip.

**Hair** works the same way with the **hair colour** (0, 1 or 2) instead of the skin tone. Hair always has 3 colours, also for special classes.

### 5.6 Frame counts

Standard cells have 15 rows (h_type 1–15), tentacle cells 7 (h_type 27–33). The formula from [5.5](#55-how-frames-are-arranged-in-a-strip) gives:

| Sprite | Normal class (3 skins) | Special class (1 skin) |
|---|---|---|
| Standard idle body parts and `_c` overlays (phase 1 and start) | 90 = 15 × 3 × 2 | 30 = 15 × 1 × 2 |
| Standard loop body parts and `_c` overlays (phases 2 and 3) | 225 = 15 × 3 × 5 | 75 = 15 × 1 × 5 |
| Tentacle idle (phase 1) | 42 = 7 × 3 × 2 | 14 |
| Tentacle loop (phases 2 and 3) | 105 = 7 × 3 × 5 | 35 |
| Tentacle birth (phase 4) | 42 = 7 × 3 × 2 | 14 |
| Hair, standard idle / loop | 90 / 225 | 90 / 225 (3 colours) |
| Big start / idle / loop | 36 / 48 / 105 | 12 / 16 / 35 |
| Hand (`hand_color`, tentacle `hand`) | 6 | 2 |
| Icon / icon hair | 3 / 3 | 1 / 3 |
| Carry head / carry hair (ogre patrol) | 24 / 24 (3 × 8) | 8 / not used |

- A special class can end its standard strips early with `max_row`; rows from `max_row` on fall back to vanilla drawing ([§16](#16-special-classes-and-monster-sprite-overrides)).
- A log line such as `[GNX] idle_head: strip frames=90 idx=<sprite>` shows the frame count GNX used for an entry.

### 5.7 Hand, icon and carry sprites

**Hand.** The class's `hand_color` sprite (and the per-leg `hand` in `clothing_tent`) is drawn once for each hand, at positions the cell sets. Its frame:

```
frame number = skin × (frames ÷ 3) + pose
```

- `pose` is 0 normally and 1 at the body frames listed in the cell's `hand_frames` ([§9](#9-the-physical-block-how-a-cell-behaves)).
- Normal class: **6 frames** (skin 0 pose 0, skin 0 pose 1, skin 1 pose 0, … skin 2 pose 1); with only 2, the skin tones get the wrong hands. Special class: **2 frames** (pose 0, pose 1).

**Icon.** The small head picture in unit lists.

- `icon`: 3 frames, one per skin tone, 21 × 26 pixels with origin 10, 13, like the vanilla icon (the log prints it as `vanilla icon (class 0 frame 0): xo=10 yo=13 w=21 h=26`). Special classes use 1 frame.
- `icon_hair`: 3 frames, one per hair colour. `-1` = no hair on the icon.
- With `"icon": -1` the game shows an unrelated picture from its own icon sheet. Always give a mod class an icon.

**Carry.** When an ogre on patrol carries a captive, GNX draws the class's `carry_head` and `carry_hair` by itself: 8 frames per skin tone or hair colour (24). For a special class `carry_head` is the whole body, 8 frames. Details: [§6](#6-classes-classesjson).

### 5.8 Packing tool and atlas

- GNX loads per-frame PNGs directly with `folder` or a `frames` list, so packing strips is optional.
- The Python script `gnx_pack_strips.py` turns per-frame folders into strips: `python gnx_pack_strips.py path/to/my_mod --force`, with files named `<strip name>/<strip name>_<i>.png`.
- For many sprites, an atlas loads faster than separate strips ([§20](#20-atlas-packing)).

> **When** `frames` does not match the picture (a 90-frame strip declared with `"frames": 30`), every frame is three times too wide and the animation shows the wrong poses.

---

## 6. Classes (classes.json)

**In short:** a *class* is a type of human unit you can capture, such as Peasant, Knight or Lilith. Your classes file (named in `manifest.json`, usually `classes.json`) adds new classes or changes existing ones: the name, the look in each kind of cell, raid strength, where the class spawns and what its offspring become.

The file is a JSON **list** with one object per class. A minimal but complete class:

```json
[
  {
    "name": "Witch",
    "has_hair": false,
    "default_leg": 1,
    "hand_color": "gnx:hand",
    "icon": "gnx:icon_head",
    "fap_mul": 2,
    "bap_mul": 3,
    "birth_class": { "goblin": 2, "hobgoblin": 1, "tentacle": 0, "ogre": 3 },
    "raid_spawns": [
      { "stage": 2, "level": 1, "weight": 20, "min_lvl": 0, "max_lvl": 2 }
    ],
    "sprites": {
      "hand": { "strip": "strips/spr_h_witch_hand.png", "frames": 6, "origin_from": "spr_h_base_hand" },
      "icon_head": { "strip": "strips/spr_unit_icon_witch_head.png", "frames": 3, "origin_from": "spr_unit_icon_head" },
      "idle_head": { "strip": "strips/spr_h_witch_idle_head.png", "frames": 90, "origin_from": "spr_h_base_idle_head" },
      "idle_breast": { "strip": "strips/spr_h_witch_idle_breast.png", "frames": 90, "origin_from": "spr_h_base_idle_breast" },
      "idle_leg_1": { "strip": "strips/spr_h_witch_idle_leg_1.png", "frames": 90, "origin_from": "spr_h_base_idle_leg_1" },
      "idle_legp": { "strip": "strips/spr_h_witch_idle_leg_part.png", "frames": 90, "origin_from": "spr_h_base_idle_leg_part" },
      "loop_head": { "strip": "strips/spr_h_witch_loop_head.png", "frames": 225, "origin_from": "spr_h_base_loop_head" },
      "loop_breast": { "strip": "strips/spr_h_witch_loop_breast.png", "frames": 225, "origin_from": "spr_h_base_loop_breast" },
      "loop_leg_1": { "strip": "strips/spr_h_witch_loop_leg_1.png", "frames": 225, "origin_from": "spr_h_base_loop_leg_1" },
      "loop_legp": { "strip": "strips/spr_h_witch_loop_leg_part.png", "frames": 225, "origin_from": "spr_h_base_loop_leg_part" }
    },
    "clothing_standard": {
      "phase_1": {
        "leg_1": { "head": "gnx:idle_head", "breast": "gnx:idle_breast", "leg": "gnx:idle_leg_1", "leg_part": "gnx:idle_legp" }
      },
      "phase_2": {
        "leg_1": { "head": "gnx:loop_head", "breast": "gnx:loop_breast", "leg": "gnx:loop_leg_1", "leg_part": "gnx:loop_legp" }
      }
    }
  }
]
```

**What this example does:**

- `"name": "Witch"`: other files refer to the class as `"my_mod.Witch"`. Without `class_id`, GNX makes a stable ID from that text ([6.1](#61-class-ids)).
- `"has_hair": false`: no separate hair layer; her hair is painted into the head sprites.
- `"default_leg": 1`: every Witch has leg pose 1, so the clothing map needs only `leg_1`.
- `hand_color` is the hand overlay in standard and big cells; `icon` is the head picture in menus and on the raid screen (3 frames, one per skin tone).
- `fap_mul` / `bap_mul` set her raid strength ([6.4](#64-raid-strength-and-pregnancy)); `birth_class` says which troop type her children join ([§14](#14-pregnancy-and-birth)).
- `raid_spawns` lets her appear in Forest raids (stage 2) at encounter level 1, shown in game as Forest lvl 2 ([§13](#13-raid-spawns-and-the-trade-shop)).
- `sprites` declares the image files ([§5](#5-sprites)); `clothing_standard` says what she wears in standard cells while waiting (`phase_1`) and during the act (`phase_2`) ([§7](#7-clothing-maps-how-a-class-looks-in-each-cell)).

The log line `[GNX] class <id> registered: <name>` shows each class's ID.

> **When** a class has no `clothing_big` or `clothing_tent`, like this Witch, she can still enter big cells (G.BANG, CAGE…) and tentacle cells (BIND, T.WALL…), where the game falls back to vanilla drawing code that does not support a modded class, so parts are missing or wrong. Give every class all three maps, or keep it out with `only_listed_cells`.

### 6.1 Class IDs

Vanilla classes use 0–13 ([Appendix A](#appendix-a-vanilla-ids-and-cell-list)); new classes get 14–9999. Normally GNX makes the ID as a [hash](#2-glossary) of `"<folder>.<name>"`; renaming either changes it ([3.4](#34-duplicate-ids)).

`class_id` is **read only with `"override": true`**:

- If that ID exists, your entry is **merged** into the class ([6.2](#62-override-changing-an-existing-class)).
- If not, a new class is created at exactly that ID. This is the only way to pin a class to a chosen number.

> **When** a pinned ID is already used by another mod, no second class is made: the entry is merged into that mod's class.

### 6.2 override: changing an existing class

`"override": true` with a `class_id` changes an existing class, usually a vanilla one. GNX **merges the top-level keys**: each key you write replaces the old value, every other key stays. You do not need to repeat sprites or clothing to change one number.

```json
[
  { "override": true, "class_id": 0, "preg_c_override": 3 }
]
```

Every new Peasant (class 0) gets 3 pregnancies; everything else stays vanilla. The log shows `[GNX] class_id 0 override (merge)`.

On vanilla classes (0–13) these keys have **no effect**; the game's built-in rules apply:

- `birth_class`, `birth_classes`, `birth_spr` ([§14](#14-pregnancy-and-birth))
- `mon_spr_overrides` ([§16](#16-special-classes-and-monster-sprite-overrides))
- `carry_head` / `carry_hair` sprites ([6.5](#65-ogre-carry-sprites))
- `only_listed_cells`

**Clothing maps are filled in.** In `clothing_standard`, `clothing_big`, `clothing_tent` and the three `naked_*` maps, every part you leave out comes from the old class, so `"clothing_standard": { "phase_1": {...} }` keeps the old `phase_2`. A missing or unloadable sprite in your map is replaced by the old one, with `[GNX-WARN] Mod 'my_mod' class 0: 2 sprite(s) missing or not loadable, using the vanilla class's instead`. A part with `leg_any` gets no old `leg_0`–`leg_2`. In a **new** non-special class, missing or unloadable sprites in these maps are replaced by the Peasant's, with the same warning.

> **When** an override contains another object, that object is not merged but replaced as a whole: `clothing_giant`, `mon_spr_overrides`, `birth_spr` and `post_raid` completely; `"birth_class": { "goblin": 2 }` sets the other three species to 0; `"voice": { "pitch": 1.0 }` without `bank` loses the voice bank. Write the complete object.

> **When** Hathor (9), Nyx (10), Selene (11), Morrigan (12) or Bastet (13) is overridden without `fap_mul` and `bap_mul`, the defaults 1 and 0 replace their built-in raid strength. Write both keys.

> **When** **another mod's** class (ID ≥ 14) is overridden with new `carry_head`/`carry_hair` sprites, they replace the old ones.

### 6.3 Core fields

| Key | What it means | Type | Default |
|---|---|---|---|
| `name` | Class name: used in refs (`"my_mod.Witch"`, case-sensitive), for the hash ID and as the class name in game. | text | `"UNKNOWN"` (always set it) |
| `override` | `true` = change an existing class or create one at a fixed `class_id` ([6.2](#62-override-changing-an-existing-class)). | true/false | `false` |
| `class_id` | ID number, read only with `"override": true`. | number | hash (14–9999) |
| `is_special` | A "special" class with one skin tone and its own clothing format, like Lilith or Nyx ([§16](#16-special-classes-and-monster-sprite-overrides)). | true/false | `false` |
| `has_hair` | `true` = each unit gets one of 3 hair variants from the `hair` sprites; `false` = no hair layer. | true/false | `true` |
| `hand_color` | Hand overlay (gloves or skin colour) for normal classes in standard and big cells; tentacle cells use the per-leg `hand` of `clothing_tent`. 6 frames: 3 skins × open/closed. | sprite or -1 | `-1` |
| `icon` | Head icon in menus and on the raid screen, 3 frames (one per skin). Without it the game shows an unrelated picture from its icon sheet, so always set it. | sprite or -1 | `-1` |
| `icon_hair` | Hair on the icon, 3 frames (one per hair variant); drawn only with `icon` and hair. | sprite or -1 | `-1` |
| `default_leg` | Fixed leg pose for the class: `1` or `2` (normal poses) or `0` (kneeling body of vanilla Shaman, Warrior and Bastet). | number | random 1 or 2 |
| `scr_unit` | Passive effect in a cell: `0` = milk refills over time like Hathor, `1` = remaining pregnancies slowly refill to the starting number like Selene, `-1` = none. | number | `-1` |
| `only_listed_cells` | `true` = enters only cells whose `required_class` lists it ([§8](#8-cells-cellsjson)); vanilla cells must be patched to allow it ([§12](#12-patching-vanilla-cells-and-classes)). IDs ≥ 14 only. | true/false | `false` |
| `voice` | Fixed moan voice, e.g. `{ "bank": "soft", "pitch": 1.0 }`, with a bank from your own `sounds.json` ([§18](#18-sounds-soundsjson)). | object | random voice |

### 6.4 Raid strength and pregnancy

| Key | What it means | Type | Default |
|---|---|---|---|
| `fap_mul` | Enemy **HP** the class adds to a raid encounter: `fap_mul × unit level`. | number | `1` |
| `bap_mul` | Enemy **AP** (attack power) added: `bap_mul × unit level`. | number | `0` |
| `preg_c_override` | How many times a unit can get pregnant; each birth uses one. `-1` = unlimited ([§14](#14-pregnancy-and-birth)). | number | 4–9, by unit level |
| `preg_mon_type_override` | Forces the children's species, whoever bred her: `0` goblin, `1` hobgoblin, `2` tentacle, `3` ogre. | number | breeding monster's species |

Vanilla `fap_mul`/`bap_mul`: Peasant 1/0, Cleric 1/4, Knight 3/1, Ranger 2/5, Nun 0/2, Samurai 6/2, Shaman 1/2, Warrior 5/0.

### 6.5 Ogre carry sprites

In DISPLAY_B an ogre can carry a unit around (the "patrol"). For classes with ID ≥ 14, GNX draws the carried unit from `sprites` entries with these exact names; no other key points to them.

```json
{
  "name": "Witch",
  "carry_base_spr": { "leg_1": "gnx:carry_base", "leg_2": "gnx:carry_base", "leg_0": "gnx:carry_base_kneel" },
  "sprites": {
    "carry_head": { "strip": "strips/spr_h_witch_carry_head.png", "frames": 24, "origin_from": "spr_ogre_carry_head_peasant" },
    "carry_base": { "strip": "strips/spr_h_witch_carry_base.png", "frames": 24, "origin_from": "spr_ogre_carry_base" },
    "carry_base_kneel": { "strip": "strips/spr_h_witch_carry_base_v3.png", "frames": 24, "origin_from": "spr_ogre_carry_base_v3" }
  }
}
```

- `carry_head`: the head, 8 walk frames × 3 skin tones = 24.
- `carry_hair` (not used, the Witch has no hair): 8 frames × 3 hair variants = 24.
- `carry_base_spr`: the body, either one sprite or one per leg pose (`leg_0`, `leg_1`, `leg_2`); missing poses stay vanilla. Also 8 × 3 frames. Unlike the other two, it also works on vanilla classes.
- Canvas 115 × 115 with origin (55, 114), like the vanilla carry sprites, or `origin_from`.

For **special** classes `carry_head` is the **whole** carried body (8 frames, one skin), and `carry_hair` and `carry_base_spr` are ignored. Without `carry_head`, **nothing** is drawn on the ogre's back.

The ogre's own walking sprite is the `patrol` key of `mon_spr_overrides` ([§16](#16-special-classes-and-monster-sprite-overrides)).

### 6.6 Other class keys

| Key | Purpose | Section |
|---|---|---|
| `sprites` | The class's image files | [§5](#5-sprites) |
| `clothing_standard`, `clothing_big`, `clothing_tent`, `clothing_giant` | Look in each cell type | [§7](#7-clothing-maps-how-a-class-looks-in-each-cell) |
| `naked_standard`, `naked_big`, `naked_tent` | Bare body under the clothes | [§7](#7-clothing-maps-how-a-class-looks-in-each-cell) |
| `raid_spawns`, `trade_stage` | Raid enemies and the trader's shop | [§13](#13-raid-spawns-and-the-trade-shop) |
| `birth_class`, `birth_classes`, `birth_spr` | Offspring and birth animations | [§14](#14-pregnancy-and-birth) |
| `post_raid`, `tower_boss_condition` | Cage escape and tower boss | [§15](#15-bosses-cage-escape-and-tower) |
| `gb1_breast_d2`, `mon_spr_overrides` | Special sprites in some vanilla cells | [§16](#16-special-classes-and-monster-sprite-overrides) |
| `carry_base_spr` | Ogre carry body | [6.5](#65-ogre-carry-sprites) |

> **When** the classes file is not a JSON list `[ ... ]` (even for one class), loading stops with `Mod '<folder>': <file> is not a JSON array`.

> **When** a modded class has neither `clothing_standard` nor `clothing_giant`, the self-test reports `[GNX-TEST] FAIL  T16 mod class entries invalid: <ids>`. T16 does not check the phases, so treat `clothing_standard` with `phase_1` and `phase_2` as required for normal classes.

---

## 7. Clothing maps: how a class looks in each cell

**In short:** a *clothing map* tells GNX which sprites to draw for your class in a group of cells. For a normal class the game draws a shared bare body (the "base body") and your map adds clothes, head and hair on top. There is one map per cell type (standard, big, tentacle, giant), with sprites per [phase](#2-glossary) (animation stage) and per leg pose.

```json
{
  "name": "Witch",
  "clothing_standard": {
    "phase_1": {
      "leg_1": { "head": "gnx:idle_head", "breast": "gnx:idle_breast", "leg": "gnx:idle_leg_1", "leg_part": "gnx:idle_legp" },
      "leg_any": { "head": "gnx:idle_head", "breast": "gnx:idle_breast", "leg": "gnx:idle_leg_2", "leg_part": "gnx:idle_legp" },
      "cape": "gnx:idle_cape"
    },
    "phase_2": {
      "leg_1": { "head": "gnx:loop_head", "breast": "gnx:loop_breast", "leg": "gnx:loop_leg_1", "leg_part": "gnx:loop_legp" },
      "leg_any": { "head": "gnx:loop_head", "breast": "gnx:loop_breast", "leg": "gnx:loop_leg_2", "leg_part": "gnx:loop_legp" }
    }
  }
}
```

**What this example does:**

- `clothing_standard` is used in standard cells such as WALL 1 or RIDE.
- `phase_1` is the idle animation (waiting), `phase_2` the loop (the act); ejaculation (phase 3) reuses `phase_2`.
- `leg_1` is for units with leg pose 1; `leg_any` is the fallback for every other pose, here pose 2.
- `head`, `breast`, `leg` and `leg_part` (a separate piece such as a skirt hem) are the clothing sprites. `hair` is left out because the Witch has no hair.
- `cape` is a phase-level extra sprite, drawn on the cell's cape layer (type 11). Among vanilla standard cells only M.PRESS 1 and DISPLAY have that layer.
- The `gnx:` sprites must be declared in the class's `sprites` ([§5](#5-sprites)); they are left out to keep the example short.

### 7.1 Which map is used in which cell

The `mode` and `base_body` of a cell's `human_spr` ([§10](#10-cell-sprites-human_spr-and-mon_spr)) decide which map GNX reads:

| Cell setting | Vanilla cells | Normal class uses | Special class uses |
|---|---|---|---|
| `base+class`, `base_body: "standard"` | WALL 1, WALL 2, T.FRAME 1, MILK 1, BIRTH 1, BJ 1, WALL 3, WALL 4, M.PRESS 1, DISPLAY, DRINK, BIRTH 2, PRONE 1, RIDE, FOREPLAY | `clothing_standard` (+ `naked_standard`) | `clothing_standard` tables |
| `base+class`, `base_body: "big"` | CAGE, G.BANG 2, G.BANG 1, OGRE FRONT, OGRE BEHIND, OGRE BEHIND 2, G.BANG 3, DISPLAY_B | `clothing_big` (+ `naked_big`) | `clothing_big` tables |
| `base+class`, `base_body: "tent"` | BIND 1, BIND 2, T.WALL 1, T.WALL 2, T.WALL 3, MILK 2, RECOVER | `clothing_tent` (+ `naked_tent`) | `clothing_tent` tables |
| GIANT (`h_type` 37) | GIANT | `clothing_giant`, otherwise `clothing_standard` | `clothing_giant`, otherwise `clothing_standard` |
| `mode: "fixed"` | DAIRY, CHAINS, LILITH SHRINE | nothing: the cell has its own sprites | nothing |
| no `human_spr` | CLONE_B, CLEAN, S.SHRINE, F.SHRINE, R.SHRINE | nothing: no class sprites here | nothing |

Custom cells follow their own `human_spr`. In `fixed` and `class_map` mode the cell supplies the sprites and clothing maps are ignored. In custom standard cells the start phase also uses `phase_1`.

Which cells a class may enter is a separate question, decided by the cell's `required_class` ([§8](#8-cells-cellsjson)). Vanilla GIANT, for example, allows only Selene (11) and must be patched ([§12](#12-patching-vanilla-cells-and-classes)) for any other class, even one with `clothing_giant`.

### 7.2 Leg keys

Every unit has leg pose 1 or 2 (random) or 0 (kneeling body, set with `default_leg: 0`). Maps choose sprites per pose with these keys:

| Key | Used for | Read in |
|---|---|---|
| `leg_1` | leg pose 1 | all normal maps, `naked_*`, `carry_base_spr` |
| `leg_2` | leg pose 2 | all normal maps, `naked_*`, `carry_base_spr` |
| `leg_0` | leg pose 0 (kneeling) | `clothing_standard`, `clothing_tent`, `naked_*`, `carry_base_spr`, **not** `clothing_big` |
| `leg_any` | fallback when the unit's pose key is missing | all normal maps and `naked_*` |

Without the pose key and `leg_any`, GNX finds no clothes and falls back to the game's own code, which has no sprites for a modded class.

### 7.3 clothing_standard

| Key | What it means | Type | Default |
|---|---|---|---|
| `phase_1` | Idle sprites | object | required |
| `phase_2` | Loop sprites (also ejaculation) | object | required |
| `phase_N.leg_1` / `leg_2` / `leg_0` / `leg_any` | One entry per leg pose ([7.2](#72-leg-keys)) | object | — |
| `phase_N.cape` | Sprite for the cape layer (type 11) | sprite or -1 | `-1` |
| `max_row` | Special classes only ([§16](#16-special-classes-and-monster-sprite-overrides)) | number | — |

A leg entry has `hair` (3 hair variants per cell row), `head` (with face), `breast` (upper body clothing), `leg` and `leg_part` (a separate piece such as a skirt hem), each sprite or -1, default `-1`.

There is **no `hand` key** here: GNX ignores it and draws the class's `hand_color`. Standard strips hold every standard cell pose: 90 frames for idle, 225 for loop ([5.5](#55-how-frames-are-arranged-in-a-strip)).

### 7.4 clothing_big

Used in big cells. Its three phases have **different names**, and the leg keys hold sprites directly instead of objects:

```json
{
  "name": "Witch",
  "clothing_big": {
    "start": { "head": "gnx:big_start_head", "breast": "gnx:big_start_breast", "leg_1": "gnx:big_start_leg_1", "leg_2": "gnx:big_start_leg_2" },
    "idle": { "head": "gnx:big_idle_head", "breast": "gnx:big_idle_breast", "leg_1": "gnx:big_idle_leg_1", "leg_2": "gnx:big_idle_leg_2" },
    "loop": { "head": "gnx:big_loop_head", "breast": "gnx:big_loop_breast", "leg_any": "gnx:big_loop_leg" }
  }
}
```

| Key | What it means | Type | Default |
|---|---|---|---|
| `start`, `idle`, `loop` | Phases 0, 1 and 2 (loop also for ejaculation) | object | — |
| `<phase>.head`, `.breast`, `.hair` | Head, upper body clothing, optional hair | sprite or -1 | `-1` |
| `<phase>.leg_1`, `leg_2`, `leg_any` | Leg clothing for pose 1, pose 2 or any pose | sprite or -1 | — |

- `leg_0` is **not read** here; kneeling units use `leg_any`.
- There is no `leg_part`, `cape` or `hand` key; the hand uses `hand_color`.
- Without `clothing_big`, or without the needed phase, GNX falls back to the game's own code.

### 7.5 clothing_tent

Used in tentacle cells. Same shape as `clothing_standard`, with `phase_1` (idle), `phase_2` (loop and ejaculation) and `phase_4` (birth); example in [7.9](#79-complete-example-normal-class). Leg entries have `hair`, `head`, `breast`, `hand`, `leg` and `leg_part` (sprite or -1, default -1). The per-leg **`hand`** replaces the class's `hand_color`, which tentacle cells ignore. Tentacle cells use class sprites only when the class has a `clothing_tent`.

### 7.6 clothing_giant

Used only in the vanilla GIANT cell (`h_type` 37). It always uses the special-class table format, for normal and special classes alike, and no `start`/`idle`/`loop`:

```json
{
  "name": "Witch",
  "clothing_giant": {
    "phase_1": {
      "spr_array": [-1, "gnx:giant_idle_head", "gnx:giant_idle_breast", "gnx:giant_idle_hand", "gnx:giant_idle_leg_a", "gnx:giant_idle_leg_b", -1],
      "spr_c_array": [-1, -1, "gnx:giant_idle_breast_c", "gnx:giant_idle_hand_c", "gnx:giant_idle_leg_a_c", "gnx:giant_idle_leg_b_c"]
    },
    "phase_2": {
      "spr_array": [-1, "gnx:giant_loop_head", "gnx:giant_loop_breast", "gnx:giant_loop_hand", "gnx:giant_loop_leg_a", "gnx:giant_loop_leg_b", -1],
      "spr_c_array": [-1, -1, "gnx:giant_loop_breast_c", "gnx:giant_loop_hand_c", "gnx:giant_loop_leg_a_c", "gnx:giant_loop_leg_b_c"]
    }
  }
}
```

- Phase keys are `phase_0`, `phase_1`, `phase_2` and `phase_4`; GIANT uses 1 (idle), 2 (loop, also ejaculation) and 4 (birth), never 0.
- `spr_array` is the full body and `spr_c_array` the clothes, slot by slot ([7.7](#77-special-class-tables-spr_array-and-spr_c_array)). There is no base body, so draw the complete body.
- GIANT draws one frame per animation frame (idle 2, loop 5, birth 2), with no cell rows and no skin tones. Slots `[4]` and `[5]` are the two legs, which the cell mirrors; `[6]` goes on the cape layer. Hair and head overlay (`spr_c_array` `[0]`, `[1]`) are not drawn. Vanilla Selene's tables follow this layout.
- Without `clothing_giant`, GNX uses `clothing_standard` and the standard base body, but GIANT draws only the first frames of those strips, so the class looks wrong.
- A **special** class with `clothing_giant` but without the phase the cell asks for gets no new sprites for it; there is no fallback to `clothing_standard`.
- `clothing_giant` does not let the class into GIANT: patch the cell's `required_class` ([§12](#12-patching-vanilla-cells-and-classes)).

### 7.7 Special-class tables: spr_array and spr_c_array

Special classes (`"is_special": true`, [§16](#16-special-classes-and-monster-sprite-overrides)) have no base body. Each phase of `clothing_standard`, `clothing_big` and `clothing_tent` is a table of the full body (`spr_array`) and the clothes (`spr_c_array`), with these phase keys:

| Map | Phase keys for special classes |
|---|---|
| `clothing_standard` | `phase_1`, `phase_2` |
| `clothing_big` | `phase_0` (start), `phase_1` (idle), `phase_2` (loop), not `start`/`idle`/`loop` |
| `clothing_tent` | `phase_1`, `phase_2`, `phase_4` |
| `clothing_giant` | `phase_0`, `phase_1`, `phase_2`, `phase_4` (all classes) |

Each list position ("slot") is one body part:

| Slot | `spr_array` (body) | `spr_c_array` (clothes) | Cell layer type |
|---|---|---|---|
| `[0]` | not used | hair | drawn with the head (10) |
| `[1]` | head | head overlay | 10 |
| `[2]` | breast | breast clothes | 6 |
| `[3]` | hand | hand clothes | 7 |
| `[4]` | leg | leg clothes | 8 |
| `[5]` | leg part | leg part clothes | 9 |
| `[6]` | cape / extra | — (not read) | 11 |

Write all 7 entries in `spr_array` and at least 6 in `spr_c_array` (a 7th is ignored), with `-1` for unused slots. In cells with a cape layer (M.PRESS 1, DISPLAY, GIANT) GNX reads slot `[6]` without checking the list length, so a shorter list can cause an error.

There is no leg choice in these tables: a special class has one fixed body per phase. Use `default_leg` to fix its pose elsewhere, for example on the ogre carry.

### 7.8 naked_standard, naked_big, naked_tent

A normal class is drawn as the shared vanilla bare body plus its clothes. The `naked_*` maps replace that bare body for your class only, for example for another skin colour, a tail or a different body shape. They apply only to normal classes, and only when the matching clothing map is used for that phase.

```json
{
  "name": "Witch",
  "naked_standard": {
    "hand": "gnx:naked_hand",
    "phase_1": {
      "leg_1": { "head": "gnx:naked_idle_head", "breast": "gnx:naked_idle_breast", "leg": "gnx:naked_idle_leg_1", "leg_part": "gnx:naked_idle_legp" }
    },
    "phase_2": {
      "leg_1": { "head": "gnx:naked_loop_head", "breast": "gnx:naked_loop_breast", "leg": "gnx:naked_loop_leg_1", "leg_part": "gnx:naked_loop_legp" }
    }
  },
  "naked_big": {
    "hand": "gnx:naked_hand",
    "idle": {
      "head": "gnx:naked_big_idle_head",
      "breast": "gnx:naked_big_idle_breast",
      "leg_1": "gnx:naked_big_idle_leg_1",
      "leg_0": { "head": "gnx:naked_big_idle_head_kneel", "breast": "gnx:naked_big_idle_breast_kneel", "leg": "gnx:naked_big_idle_leg_kneel" }
    }
  }
}
```

| Map | Structure |
|---|---|
| `naked_standard` | `hand` + `phase_1`, `phase_2`; leg entries `leg_1`/`leg_2`/`leg_0`/`leg_any` with `head`, `breast`, `leg`, `leg_part`. |
| `naked_tent` | Like `naked_standard`, with `phase_1`, `phase_2`, `phase_4`. |
| `naked_big` | `hand` + `start`, `idle`, `loop`, each with `head`, `breast` and leg sprites `leg_1`/`leg_2`/`leg_any`, plus an optional `leg_0` **object** (`head`, `breast`, `leg`) for kneeling units. |

- Each sprite replaces the matching vanilla base body sprite and needs its frame layout. Anything left out, or failing to load, stays vanilla.
- `hand` replaces the bare hand in all phases; like the base hand it needs 6 frames (3 skins × open/closed).

### 7.9 Complete example: normal class

The Witch with all three maps for normal cells. With `default_leg: 1` only `leg_1` or `leg_any` is needed. Sprites are declared as in [§6](#6-classes-classesjson) and left out here.

```json
{
  "name": "Witch",
  "has_hair": false,
  "default_leg": 1,
  "hand_color": "gnx:hand",
  "clothing_standard": {
    "phase_1": {
      "leg_any": { "head": "gnx:idle_head", "breast": "gnx:idle_breast", "leg": "gnx:idle_leg_1", "leg_part": "gnx:idle_legp" }
    },
    "phase_2": {
      "leg_any": { "head": "gnx:loop_head", "breast": "gnx:loop_breast", "leg": "gnx:loop_leg_1", "leg_part": "gnx:loop_legp" }
    }
  },
  "clothing_big": {
    "start": { "head": "gnx:big_start_head", "breast": "gnx:big_start_breast", "leg_any": "gnx:big_start_leg" },
    "idle": { "head": "gnx:big_idle_head", "breast": "gnx:big_idle_breast", "leg_any": "gnx:big_idle_leg" },
    "loop": { "head": "gnx:big_loop_head", "breast": "gnx:big_loop_breast", "leg_any": "gnx:big_loop_leg" }
  },
  "clothing_tent": {
    "phase_1": {
      "leg_any": { "head": "gnx:tent_idle_head", "breast": "gnx:tent_idle_breast", "hand": "gnx:tent_hand", "leg": "gnx:tent_idle_leg", "leg_part": "gnx:tent_idle_legp" }
    },
    "phase_2": {
      "leg_any": { "head": "gnx:tent_loop_head", "breast": "gnx:tent_loop_breast", "hand": "gnx:tent_hand", "leg": "gnx:tent_loop_leg", "leg_part": "gnx:tent_loop_legp" }
    },
    "phase_4": {
      "leg_any": { "head": "gnx:tent_birth_head", "breast": "gnx:tent_birth_breast", "hand": "gnx:tent_hand", "leg": "gnx:tent_birth_leg", "leg_part": "gnx:tent_birth_legp" }
    }
  }
}
```

Standard cells get idle and loop clothes for any leg pose, with the hand from `hand_color`. Big cells get start, idle and loop clothes, with plain sprites as leg keys. Tentacle cells get idle, loop and birth clothes, each with its own `hand`.

### 7.10 Complete example: special class

The special example class "Queen". Every phase is a full-body table; `clothing_tent` follows the same pattern with `phase_1`, `phase_2` and `phase_4`.

```json
{
  "name": "Queen",
  "is_special": true,
  "has_hair": false,
  "clothing_standard": {
    "phase_1": {
      "spr_array": [-1, "gnx:q_idle_head", "gnx:q_idle_breast", "gnx:q_hand", "gnx:q_idle_leg", "gnx:q_idle_legp", -1],
      "spr_c_array": [-1, -1, "gnx:q_idle_breast_c", "gnx:q_hand_c", "gnx:q_idle_leg_c", "gnx:q_idle_legp_c"]
    },
    "phase_2": {
      "spr_array": [-1, "gnx:q_loop_head", "gnx:q_loop_breast", "gnx:q_hand", "gnx:q_loop_leg", "gnx:q_loop_legp", -1],
      "spr_c_array": [-1, -1, "gnx:q_loop_breast_c", "gnx:q_hand_c", "gnx:q_loop_leg_c", "gnx:q_loop_legp_c"]
    }
  },
  "clothing_big": {
    "phase_0": {
      "spr_array": [-1, "gnx:q_big_start_head", "gnx:q_big_start_breast", "gnx:q_hand", "gnx:q_big_start_leg", -1, -1],
      "spr_c_array": [-1, -1, "gnx:q_big_start_breast_c", "gnx:q_hand_c", "gnx:q_big_start_leg_c", -1]
    },
    "phase_1": {
      "spr_array": [-1, "gnx:q_big_idle_head", "gnx:q_big_idle_breast", "gnx:q_hand", "gnx:q_big_idle_leg", -1, -1],
      "spr_c_array": [-1, -1, "gnx:q_big_idle_breast_c", "gnx:q_hand_c", "gnx:q_big_idle_leg_c", -1]
    },
    "phase_2": {
      "spr_array": [-1, "gnx:q_big_loop_head", "gnx:q_big_loop_breast", "gnx:q_hand", "gnx:q_big_loop_leg", -1, -1],
      "spr_c_array": [-1, -1, "gnx:q_big_loop_breast_c", "gnx:q_hand_c", "gnx:q_big_loop_leg_c", -1]
    }
  }
}
```

- `"is_special": true` switches all maps to the table format. With one skin tone her strips are a third as long as a normal class's (standard idle 30 frames, loop 75; [§16](#16-special-classes-and-monster-sprite-overrides)).
- `clothing_big` uses `phase_0/1/2` instead of `start/idle/loop`.
- The hand (`q_hand`, slot `[3]`) needs only 2 frames (open/closed).

> **When** `clothing_standard` lacks `phase_1` or `phase_2`, the game hits an error as soon as the class enters a standard cell: GNX reads both without checking.

> **When** `clothing_standard` or `clothing_big` has a `hand` key, it is ignored. Use `hand_color` there, and the per-leg `hand` only in `clothing_tent`.

> **When** a normal class uses `spr_array` tables, or a special class uses `start`/`idle`/`loop`, it gets no sprites: the two kinds of class use different formats under the same map names.

---

## 8. Cells (cells.json)

**In short:** a cell is one room slot in your dungeon. The player builds it from the build menu, puts a captive in it, and monsters come to it for a scene. `cells.json` (named by the `cells` key in [manifest.json](#4-manifestjson)) is a list of cell objects. Each object adds a new cell or, if its ID already exists, patches that cell ([§12](#12-patching-vanilla-cells-and-classes)).

A cell entry has four big parts:

- top-level keys: name, build menu tab, price, payout (this section);
- `physical`: how the cell behaves: scripts, layers, effects ([§9](#9-the-physical-block-how-a-cell-behaves));
- `human_spr` and `mon_spr`: how the captive and the monsters are drawn ([§10](#10-cell-sprites-human_spr-and-mon_spr));
- `sprites`: the cell's own sprite list ([§5](#5-sprites)).

### 8.1 Minimal example: the ALTAR cell

A standard-size breeding cell that reuses the vanilla WALL 1 body pose, with its own back wall and goblin sprites. Every key the loader requires is present.

```json
[
  {
    "name": "ALTAR",
    "category": "breed",
    "mon_types": [0],
    "price": 200,
    "spawn_info": { "coin": 2, "mood": 1, "coin_mul": false, "mood_mul": false },
    "physical": {
      "allow_preg": true,
      "max_mon_num": 1,
      "anal": -1,
      "slot_dirt_init": 0,
      "character_row": 0,
      "layers": [
        [12, "spr_dirt_wall", false, -1, false],
        [0, "gnx:altar_back", false, -1],
        [2, "spr_slot_wall_1_handc", true, -1],
        [5, "spr_slot_wall_1_extra", false, -1],
        [7, -1, false, -1, false],
        [8, -1, false, -1, false]
      ],
      "scr_idle": "scr_slot_h_state_idle",
      "scr_h": ["scr_slot_h_base_start", "scr_slot_h_base_wait", "scr_slot_h_base_sloop", "scr_slot_h_base_floop", "scr_slot_h_base_wait", "scr_slot_h_base_ej", "scr_slot_h_base_wait"],
      "scr_draw": "scr_draw_slot_gnx",
      "hand_x": [17, 6],
      "hand_y": [-42, -40],
      "hand_xscale": [1, 1],
      "hand_angle": [90, 0],
      "hand_frames": {
        "frame_1": [1],
        "frame_2": [2, 3],
        "frame_3": [2, 3]
      },
      "sp_spr": "spr_sp_v_start",
      "sq_x": 22,
      "sq_y": [-31, -30],
      "sp_x": 22,
      "sp_y": [-28, -33],
      "sp_anim_x": 0,
      "sp_anim_y": -1
    },
    "human_spr": { "mode": "base+class", "base_body": "standard" },
    "mon_spr": {
      "start": {
        "body": {
          "leg_any": { "alpha": "gnx:gob_altar_start", "line": "gnx:gob_altar_start_line" }
        },
        "hand": "gnx:gob_altar_start_hand",
        "hand_xscale": "random"
      },
      "loop": {
        "body": {
          "leg_any": { "alpha": "gnx:gob_altar_loop", "line": "gnx:gob_altar_loop_line" }
        },
        "hand": { "leg_any": "gnx:gob_altar_loop_hand" }
      }
    },
    "sprites": {
      "altar_back": { "strip": "strips/spr_slot_altar_back.png", "frames": 1, "origin_from": "spr_slot_wall_1_back" },
      "gob_altar_start": { "strip": "strips/spr_h_goblin_altar_start_alpha.png", "frames": 2, "origin_from": "spr_h_goblin_body_start_v1_alpha" },
      "gob_altar_start_line": { "strip": "strips/spr_h_goblin_altar_start_line.png", "frames": 2, "origin_from": "spr_h_goblin_body_start_v1_line" },
      "gob_altar_start_hand": { "strip": "strips/spr_h_goblin_altar_start_hand.png", "frames": 2, "origin_from": "spr_h_goblin_hand_start_alpha" },
      "gob_altar_loop": { "strip": "strips/spr_h_goblin_altar_loop_alpha.png", "frames": 5, "origin_from": "spr_h_goblin_body_loop_v1_alpha" },
      "gob_altar_loop_line": { "strip": "strips/spr_h_goblin_altar_loop_line.png", "frames": 5, "origin_from": "spr_h_goblin_body_loop_v1_line" },
      "gob_altar_loop_hand": { "strip": "strips/spr_h_goblin_altar_loop_hand.png", "frames": 5, "origin_from": "spr_h_goblin_hand_loop_v1_alpha" }
    }
  }
]
```

**What this example does**

- There is no `h_type` (ID number); GNX makes one from `"my_mod.ALTAR"` ([8.3](#83-h_type-the-cells-id)). Other files refer to the cell by that text (folder + `.` + `name`, case-sensitive).
- `"category": "breed"` puts it in the standard breeding tab, as a standard-size (45 px) cell ([8.4](#84-category-build-menu-tab-and-cell-size)).
- `"mon_types": [0]`: only goblins come ([8.5](#85-mon_types-which-monsters-come)). `"price": 200` is the cell price; built through NEW → CUSTOM it costs 300 with the standard slot ([8.4](#84-category-build-menu-tab-and-cell-size)). `spawn_info` is the gold and mood paid when a scene ends ([8.6](#86-spawn_info-gold-and-mood)).
- `physical` is copied from vanilla WALL 1, except the back wall layer `"gnx:altar_back"` ([§9](#9-the-physical-block-how-a-cell-behaves)). Like WALL 1, its body layers draw only the captive's legs (type 8) and hands (type 7); a pose that also shows the head or breast needs layers 10 and 6 ([9.4](#94-layers-what-gets-drawn)).
- `human_spr` with `base+class` draws the captive like a vanilla cell: the vanilla base body plus the class's clothing, in the WALL 1 pose because `character_row` is 0 ([§10](#10-cell-sprites-human_spr-and-mon_spr)).
- `mon_spr` replaces the goblin's sprites: `start` is the first animation, `loop` the main one, and `leg_any` means "for every captive leg variant". A plain sprite name such as `"gnx:gob_altar_start_hand"` is a fill sprite with no outline ([10.8](#108-mon_spr-monster-sprites)).
- `sprites` declares every `gnx:` sprite of the cell (`origin_from`: [5.3](#53-the-origin)). The start strips have 2 frames (the idle animation length) and the loop strips 5.

### 8.2 Top-level fields

| Key | What it means | Type | Default |
|-----|---------------|------|---------|
| `h_type` | The cell's ID number. Leave it out ([8.3](#83-h_type-the-cells-id)). | number | hash of `"<folder>.<name>"` (100–9999) |
| `name` | Name in the build menu and second half of the ref `"my_mod.ALTAR"`. Vanilla names are uppercase. | text | required |
| `category` | Build menu tab, and with it the cell size ([8.4](#84-category-build-menu-tab-and-cell-size)). | text | required |
| `locked` | `true` = registered but not in the build menu until the quest side effect `unlock_cell` (QUESTS_SCHEMA.md). | true/false | `false` |
| `mon_types` | Monster types the cell calls in ([8.5](#85-mon_types-which-monsters-come)). | list | goblins and hobgoblins |
| `slot_type` | Does not set the cell size. Only when `base_body` is left out, `2` makes it `"big"` and `3` `"tent"` ([10.1](#101-human_spr-the-three-modes)). Vanilla: 0 standard, 1 big, 3 tentacle. | number | `0` |
| `price` | Build cost in gold. | number | `100` |
| `code_text` | Short code on the cell's blueprint item (vanilla WALL 1: `"A"`). | text | `-1` (none) |
| `spawn_info` | Gold and mood paid when a scene ends ([8.6](#86-spawn_info-gold-and-mood)). | object | `-1`, but required for any cell with a scene |
| `physical` | How the cell behaves ([§9](#9-the-physical-block-how-a-cell-behaves)). | object | required |
| `human_spr` | How the captive is drawn ([§10](#10-cell-sprites-human_spr-and-mon_spr)). | object | `base+class` with `base_body` from `category` |
| `mon_spr` | Goblin sprites in this cell ([10.8](#108-mon_spr-monster-sprites)). | object | none (vanilla sprites) |
| `mon_spr_hob`, `mon_spr_ogr` | Hobgoblin and ogre sprites. | object | none (falls back to `mon_spr`) |
| `mon_spr_p0` … `mon_spr_ogr_p2` | Sprites for one [placement](#2-glossary) only ([§11](#11-multi-monster-cells)). | object | none |
| `sfx_type` | Sound set ([§18](#18-sounds-soundsjson)). | text | none |
| `sprites` | The cell's sprite list ([§5](#5-sprites)). `wall` is drawn automatically ([8.7](#87-sprites-and-the-wall-key)). | object | none |

### 8.3 h_type: the cell's ID

Vanilla cells use 1–42 (0, 16, 26 and 35 are not cells; [Appendix A](#appendix-a-vanilla-ids-and-cell-list)).

**Leave `h_type` out.** GNX then makes a hash ID (100–9999) from `"<folder>.<name>"` ([3.4](#34-duplicate-ids)); renaming either changes it. The log shows the result: `[GNX] cell OK: h=<id> name=ALTAR cat=breed`.

If you do write `h_type`:

- Write a plain number: `"h_type": 500`, never `"h_type": "500"`.
- Use 100 or higher. 43–99 registers, but custom monster sprites for vanilla captives (class ID below 14) and the `mon_positions` strip rows ([§11](#11-multi-monster-cells)) need 100+.
- An ID that already exists makes the entry a patch, not a new cell ([§12](#12-patching-vanilla-cells-and-classes)).

### 8.4 category: build menu tab and cell size

`category` decides the build menu tab and, with it, the size of the cell that gets built; `slot_type` has no effect on this. Modded cells do not appear in these tabs, though: they are all listed under **NEW → CUSTOM**, where `category` decides only the size.

| `category` | Build menu tab | Cell size | Vanilla cells in this tab |
|------------|----------------|-----------|---------------------------|
| `breed` | standard breeding | standard, 45 px | WALL 1–4, M.PRESS 1, PRONE, RIDE 1 |
| `utility` | standard utility | standard, 45 px | BIRTH 1–2, MILK 1, DISPLAY, DRINK |
| `pleasure` | standard pleasure | standard, 45 px | TITFUCK, ORAL, FOREPLAY |
| `b_breed` | big breeding | big, 77 px | G.BANG 1–3, M.PRESS 2, BEHIND, RIDE 2 |
| `b_utility` | big utility | big, 77 px | TRANSFER, PATROL, CLONE |
| `b_other` | big other | big, 77 px | DAIRY, GIANT, CHAINS, L/F/S/R.SHRINE |
| `t_breed` | tentacle breeding | tentacle, 45 px | T.WALL 1–3, BIND 1–2 |
| `t_utility` | tentacle utility | tentacle, 45 px | CLEAN, MILK 2, RECOVER |
| `xl_breed` | XL breeding | XL, 150 px | none |

**The CUSTOM list.** A pillar's NEW menu gets a sixth entry, **CUSTOM**, once at least one modded cell (`h_type` above 42) is unlocked.

- It lists every unlocked modded cell: standard, big, tentacle, then XL. XL cells are left out when the floor has no room for a 150 px slot.
- One click builds a slot of the right size next to the pillar with the cell in it, for the slot price (CELL 100, BIG CELL 300, TENTACLE 150, XL CELL 500) plus the cell's `price`. The `cell_built` quest hooks fire as for a normal build.
- The normal lists show vanilla cells only; newly unlocked modded cells mark CUSTOM as new.

- The menu of an existing empty slot (BREED / UTILITY / …) also ends with CUSTOM when a modded cell fits that slot's size, and puts the cell into that slot for its `price` only (new in 1.4.9).

> **When** `category` has an unknown value (it is case-sensitive, so `"Breed"` is unknown), the cell is registered but never appears in a build menu, and a quest `unlock_cell` on it logs `[GNX-WARN] unlock: cell h=<id> is not in any build category - skipped`.

### 8.5 mon_types: which monsters come

`mon_types` lists the monster types the cell calls in: `0` goblin, `1` hobgoblin, `2` tentacle, `3` ogre. Each call picks one type from the list at random; without the key, goblins and hobgoblins come.

- `mon_types` also filters your custom monster sprites: a type not in the list never gets this cell's `mon_spr` sprites.
- With `mon_placements` ([§11](#11-multi-monster-cells)) the placements decide which types come. `mon_types` is then only the sprite filter, so it must still list every type used in the placements.
- In the vanilla cells 4, 17–24 and 36–39 the game itself decides which monsters come; a patched `mon_types` only filters the sprites there.

### 8.6 spawn_info: gold and mood

`spawn_info` is the payout the player gets each time a scene ends normally (after the ejaculation step, when the monsters leave). It is also shown in the build menu and the cell's window. All four keys must be present.

```json
{
  "spawn_info": { "coin": 2, "mood": 1, "coin_mul": true, "mood_mul": false }
}
```

| Key | What it means | Type | Default |
|-----|---------------|------|---------|
| `coin` | Base gold value, not the gold amount itself (see the formula). Vanilla uses 0–3 (0.5 also occurs). | number | required |
| `mood` | Base mood value. Vanilla uses 0.5–3. | number | required |
| `coin_mul` | `true` = gold grows with the captive's level. | true/false | required |
| `mood_mul` | `true` = mood grows with the captive's level. | true/false | required |

How the payout is computed (`L` = the captive's level, counted up to 5; `true` = 1, `false` = 0):

- **Gold** = (B + 2 × `coin`) × (1 + L × `coin_mul`) × mood bonus, rounded down. B is 1 when `coin` is above 0, otherwise 0. The mood bonus is ×1.2 at a mood bar of 75–94, ×1.4 at 95 or more, otherwise ×1.
- **Mood bar change** = `mood` × 0.125 × (1 + L × `mood_mul`), on a bar from 0 to 100.

**Worked example.** The example above, a level 3 captive, mood bar at 80:

- Gold = (1 + 2 × 2) × (1 + 3 × 1) × 1.2 = 5 × 4 × 1.2 = **24 gold**.
- Mood = 1 × 0.125 × (1 + 3 × 0) = **+0.125**.
- With `"coin": 0` the cell pays **no gold**.

Tentacle cells pay too, with the same formula, at the end of each tentacle scene.

> **When** a cell with a scene has no `spawn_info`, it loads fine, but the game hits an error the first time a scene in it ends, because the payout code reads `spawn_info` without checking it. Cells without monsters do not need it.

### 8.7 sprites and the wall key

`sprites` is the cell's own sprite list, in the format of [§5](#5-sprites); references work as in [5.4](#54-gnx-references-and-vanilla-sprite-names).

One key is special: `wall`. `scr_draw_slot_gnx` draws it first, under all layers, as the cell's back wall, using the frame of the cell's random background variant (picked when the cell is built). It can replace a type 0 background layer.

> **When** a layer shows nothing, check the log line `[GNX] cell sprites h=<id>: [0]=… [1]=…`: it lists the resolved sprite of every layer, and `-1` there means a broken name.

---

## 9. The physical block: how a cell behaves

**In short:** `physical` controls what the cell does: which scripts run the scene, which picture layers it draws and in which order, where the captive's hands and fluid effects go, who may enter, and how many monsters come. Most keys are required, so the easiest start is to copy a vanilla cell's values (the ALTAR in [§8](#8-cells-cellsjson) copies WALL 1).

```json
{
  "physical": {
    "allow_preg": true,
    "max_mon_num": 1,
    "anal": -1,
    "slot_dirt_init": 0,
    "character_row": 0,
    "layers": [
      [12, "spr_dirt_wall", false, -1, false],
      [0, "gnx:altar_back", false, -1],
      [2, "spr_slot_wall_1_handc", true, -1],
      [5, "spr_slot_wall_1_extra", false, -1],
      [7, -1, false, -1, false],
      [8, -1, false, -1, false]
    ],
    "scr_idle": "scr_slot_h_state_idle",
    "scr_h": ["scr_slot_h_base_start", "scr_slot_h_base_wait", "scr_slot_h_base_sloop", "scr_slot_h_base_floop", "scr_slot_h_base_wait", "scr_slot_h_base_ej", "scr_slot_h_base_wait"],
    "scr_draw": "scr_draw_slot_gnx",
    "hand_x": [17, 6],
    "hand_y": [-42, -40],
    "hand_xscale": [1, 1],
    "hand_angle": [90, 0],
    "hand_frames": {
      "frame_1": [1],
      "frame_2": [2, 3],
      "frame_3": [2, 3]
    },
    "sp_spr": "spr_sp_v_start",
    "sq_x": 22,
    "sq_y": [-31, -30],
    "sp_x": 22,
    "sp_y": [-28, -33],
    "sp_anim_x": 0,
    "sp_anim_y": -1,
    "required_class": ["my_mod.Witch", 0],
    "sign_y_base": -84
  }
}
```

This is the `physical` block of vanilla WALL 1 with the ALTAR's back wall (`gnx:altar_back`), explained key by key in 9.1–9.8. Two optional keys are added: `required_class` lets only the Witch and the peasant (class 0) in ([9.9](#99-optional-keys)), and `sign_y_base` sets the height of a sign layer; this cell has none, so it only shows an optional key.

### 9.1 Required keys

Every new cell needs these keys. If one is missing (or `physical` or `category`), GNX skips the cell and reports it in the `Mod loading problem(s)` box, for example `[GNX] ERROR: Mod 'my_mod': cell 'ALTAR' physical is missing: sq_x sq_y - cell skipped`. `layers` is not checked this way: a missing `layers` is an error while loading. A patch ([§12](#12-patching-vanilla-cells-and-classes)) needs none of them.

| Key | What it means | Type | Default |
|-----|---------------|------|---------|
| `allow_preg` | Captives can get pregnant in this cell. | true/false | required |
| `max_mon_num` | Monsters in the cell at once; `0` for cells without monsters, more than 1: [§11](#11-multi-monster-cells). | number | required |
| `anal` | `-1` = never; `false`/`true` = rolled ([9.2](#92-anal)). | `-1` or true/false | required |
| `slot_dirt_init` | Dirt level when built: `0` = clean, `-1` = never gets dirty. | number | required |
| `layers` | Picture layers, drawn in list order ([9.4](#94-layers-what-gets-drawn)). | list | required |
| `scr_idle` | Script that runs while no scene is playing. | text | required |
| `scr_h` | Scripts for the scene steps ([9.5](#95-scr_idle-and-scr_h-the-scene-scripts)). | list | required |
| `scr_draw` | Draw script; use `"scr_draw_slot_gnx"`. | text | required |
| `hand_x`, `hand_y`, `hand_xscale`, `hand_angle` | Hand position, mirroring and angle per hand pose; `[]` if the cell never draws hands ([9.7](#97-hands-hand_x-hand_y-hand_xscale-hand_angle-hand_frames)). | list | required |
| `sq_x`, `sp_x` | X position of the squirt and splash effects; `-1` turns the effect off. | number | required |
| `sq_y`, `sp_y` | Y positions as `[normal, anal]`; a 1-entry list is used for both. | list | required |
| `sp_anim_x`, `sp_anim_y` | How far the splash moves per animation frame. | number | required |

Optional keys with defaults: `character_row` (0), `sp_spr` (-1), `hand_frames` (none), and everything in [9.9](#99-optional-keys) and [9.10](#910-advanced-vanilla-pattern-fields).

### 9.2 anal

`anal` decides whether a scene can be an anal scene.

- `-1`: never. Most vanilla cells use this.
- `false` or `true` on **standard and XL cells** (both behave the same): GNX rolls every time a monster enters, by the captive's pregnancy counter `preg_c` (pregnancies left, [§14](#14-pregnancy-and-birth)): about 66 % when `preg_c` is below 1 (a 60 % roll, then 15 %), otherwise 15 %. `-1` (unlimited) also counts as below 1. Being pregnant right now does not matter.
- On **big and tentacle cells** there is no roll: `true` = always anal, `false` = never.

An anal scene:

- causes no pregnancy; the pregnancy chance for later scenes rises instead;
- uses the second entry of `sq_y` and `sp_y`;
- in a cell with custom goblin sprites, gives a vanilla captive (class ID below 14) the **vanilla** goblin sprites instead of your `mon_spr`. Hobgoblin sprites are not affected.

Vanilla uses `false` only on WALL 1–4.

### 9.3 character_row

`character_row` picks the strip row (cell pose) this cell uses. Frame = (row × skins + skin) × frames per row + current frame, with `skins` 3 in base+class and class_map mode, 1 in fixed mode ([5.5](#55-how-frames-are-arranged-in-a-strip)).

- **base+class:** the shared vanilla base body strips and the class clothing strips are used, and their rows are the vanilla cells. For standard cells the row is the vanilla cell ID minus 1: WALL 1 = 0, WALL 2 = 1, TITFUCK = 2, ORAL = 5, WALL 3 = 6, WALL 4 = 7, M.PRESS 1 = 8, PRONE = 12, RIDE 1 = 13, FOREPLAY = 14. So `character_row` chooses which vanilla pose your cell reuses; copy that cell's `layers` too, so the right body parts are drawn.
- **fixed and class_map:** the strips are yours. Use row 0 unless they have more rows.

Monster strips use the same row (monster frame = row × frames per row + current frame), so your `mon_spr` strips need frames in that row. With `mon_positions` ([§11](#11-multi-monster-cells)) the monster row is the placement number instead.

> **When** `character_row` is above 0, a one-row monster strip may still show the right frames, because frame numbers past the end of a strip wrap around. The safe choice is `character_row: 0` for cells with their own art.

### 9.4 layers: what gets drawn

`layers` is a list; each entry is one picture layer:

```json
{
  "layers": [
    [0, "gnx:altar_back", false, -1],
    [7, -1, false, -1, false]
  ]
}
```

| Position | What it means | Type |
|----------|---------------|------|
| `[0]` | Layer type (table below). | number |
| `[1]` | Sprite: `"gnx:<key>"`, a vanilla name, or `-1`. Body layers (types 6–11) take `-1`; the game fills them from the captive's sprite tables. | sprite or -1 |
| `[2]` | MOD-window flag. `true` = the layer gets a row in the cell's MOD window (opened by clicking a built cell), where the player can change it; `-2` = always drawn, never listed; `false` = neither. | true/false or -2 |
| `[3]` | Always `-1`; the game uses it for the clothing overlay at runtime. Any other number is drawn as a sprite. | -1 |
| `[4]` | Optional "replace" flag: `true` = when a clothing overlay is shown, draw only the overlay, not the body under it. | true/false |

The loader keeps only the first five positions.

**Layer types**

| Type | Draws | Notes |
|------|-------|-------|
| 0 | Background or extra picture | A multi-frame sprite animates with the scene; a one-frame sprite is drawn as is. Use `false` at `[2]`. |
| 1 | Sign | Drawn at height `sign_y_base`. With `[2] = true` the player can put it left or right, or hide it. |
| 2 | Hand pose overlay (player choice) | Starts as "none". With `[2] = true` the player picks one of its frames in the MOD window; the frame number picks the `hand_x`/`hand_y`/… entry and turns on the hands (type 7). |
| 3 | Leg pose overlay (player choice) | Like type 2; a choice turns on the leg part (type 9). |
| 5 | Extra picture | Frame 0 while the cell is empty, frame 1 with a captive (a one-frame sprite always shows its frame). |
| 6 | Breast | Body layer, `spr_array[2]`. |
| 7 | Hands | Body layer, `spr_array[3]`, drawn twice (mirrored) at `hand_x`/`hand_y`, only when an earlier type 2 layer has a pose chosen or this layer has `-2` at `[2]`. |
| 8 | Legs | Body layer, `spr_array[4]`. The monster's `touch` and `enter` overlays are drawn here. |
| 9 | Leg part | Body layer, `spr_array[5]`, only when an earlier type 3 layer has a pose chosen, or with `-2` at `[2]`. |
| 10 | Head and hair | Body layer, `spr_array[1]`; hair from `spr_c_array[0]`. |
| 11 | Cape or extra body part | Body layer, `spr_array[6]`. |
| 12 | Dirt | Drawn only while the cell is dirty. Frame = dirt level − 1, so it needs 3 frames. |

`spr_array` is the captive's sprite table for the current phase ([§10](#10-cell-sprites-human_spr-and-mon_spr)). Types 6, 7 and 8 get a clothing on/off switch in the MOD window when a captive enters. Vanilla types 4, 13 and 14 (special MOD-window controls) are not drawn by `scr_draw_slot_gnx`.

**Draw order.** The first entry is at the back, the last in front. Before the layers, the game draws the plain cell background and then the `wall` sprite, if any ([8.7](#87-sprites-and-the-wall-key)).

**Auto-added layers.** For `fixed` and `class_map` cells ([§10](#10-cell-sprites-human_spr-and-mon_spr)), GNX appends any missing layer of type 10, 6, 7, 8 or 9 at the **end** of the list, in front of everything. base+class cells get nothing added: without your body layers the captive is not drawn. To control the order, list all body layers yourself.

> **When** layers are set up, these rules apply:
> - Type 2 must come before type 7, and type 3 before type 9, because the hands and the leg part check the earlier choice.
> - Layers of type 6–10 need all five positions (`[type, -1, false, -1, false]`); a four-entry body layer can cause an error when clothing is drawn.
> - A type 2 or 3 layer with `false` at `[2]` never gets a choice, so the hands (or leg part) never show. Use `true`.
> - Auto-added type 7 and 9 layers have `false` at `[2]`, so in a fixed cell without a type 2 layer the `spr_array[3]` hands never show. Add `[7, -1, -2, -1, false]` to always draw them (with `hand_x[0]` etc.).

### 9.5 scr_idle and scr_h: the scene scripts

`scr_idle` runs while the cell waits, and calls monsters to it. `scr_h` lists the scene scripts, one per step: the scene starts at the first entry, and each script moves to the next when done. The ejaculation script ends the scene: the monsters leave, the payout happens, and the cell returns to `scr_idle`.

Most vanilla breeding cells use the 7-entry list from the example: start (the monster gets in position), pause, slow loop, fast loop, pause, ejaculation (the scene ends), and a pause that is normally not reached. Other lengths work. Vanilla FOREPLAY skips the start: `["scr_slot_h_base_sloop", "scr_slot_h_base_floop", "scr_slot_h_base_wait", "scr_slot_h_base_ej", "scr_slot_h_base_wait"]`.

| Script | Used for | Vanilla cells using it |
|--------|----------|------------------------|
| `scr_slot_h_state_idle` | idle (`scr_idle`) | most breeding cells |
| `scr_slot_h_base_start` | start; the captive keeps her idle animation, sped up | WALL 1–4, M.PRESS 1, PRONE, RIDE 1, TITFUCK, ORAL |
| `scr_slot_h_big_start` | start; the captive switches to her start ([phase](#2-glossary) 0) sprites | M.PRESS 2, BEHIND, RIDE 2 |
| `scr_slot_h_base_wait`, `_sloop`, `_floop`, `_ej` | pause, slow loop, fast loop, ejaculation | most breeding cells |
| `scr_slot_h_base_ej_2` | shorter ejaculation | TITFUCK |

Other vanilla scripts (tentacle, G.BANG, CHAINS, DAIRY, GIANT, birth and milk cells) are written for their own cells; check how the vanilla cell uses one before reusing it.

> **When** a script name is wrong (names are case-sensitive), GNX logs `[GNX] WARNING: script not found: <name>`. There is **no fallback**: the game hits an error when the cell reaches that step (for `scr_idle`, as soon as a captive is in the cell).
>
> **When** a fixed-mode cell uses `scr_slot_h_big_start`, it needs a `phase_0` entry in `human_spr` ([§10](#10-cell-sprites-human_spr-and-mon_spr)). `scr_slot_h_base_start` never switches to phase 0.

### 9.6 scr_draw

Use `"scr_draw_slot_gnx"`: it draws the `wall` sprite, the layers and the splash effect. Vanilla draw scripts handle cell-specific extras and do not draw `wall`. A wrong name logs `[GNX] WARNING: script not found: <name>` and causes an error when the cell is drawn.

### 9.7 Hands: hand_x, hand_y, hand_xscale, hand_angle, hand_frames

These keys place the **captive's** hands (layer type 7); the monster's hand is part of `mon_spr` ([10.8](#108-mon_spr-monster-sprites)).

Each list has **one entry per frame of the type 2 hand pose overlay**: pose N chosen by the player uses entry N; with `-2` at `[2]` of the type 7 layer, entry 0. Vanilla WALL 1 has 2 entries, WALL 2 has 3, RIDE 1 none.

| Key | What it means | Type | Default |
|-----|---------------|------|---------|
| `hand_x` | Pixels from the cell's left edge. | list | required |
| `hand_y` | Pixels from the cell's floor line; negative = up. | list | required |
| `hand_xscale` | `1` = normal, `-1` = flipped. | list | required |
| `hand_angle` | Rotation in degrees. | list | required |
| `hand_frames` | Body frames that switch the hand to its second frame, per phase. | object | none |

Each hand is drawn twice: at `hand_x`, and mirrored at the same distance from the cell's right edge.

**hand_frames** keys are phases: `frame_1` idle (also the start of standard cells), `frame_2` loop, `frame_3` ejaculation, `frame_4` tentacle birth. Each lists body animation frames during which the hand shows its next frame (for example a closed hand); otherwise it shows its first frame. Vanilla T.WALL 1/2 use `"frame_4": [1]`.

### 9.8 Fluid effects: sp_spr, sq_*, sp_*

Positions are pixels from the cell's bottom-left corner: x to the right, negative y up.

| Key | What it means | Type | Default |
|-----|---------------|------|---------|
| `sq_x` | X of the squirt particles during the loops; `-1` = no squirt. | number | required |
| `sq_y` | Y as `[normal, anal]`. | list | required |
| `sp_spr` | Splash sprite that stays after the scene (vanilla: `"spr_sp_v_start"`). | sprite or -1 | `-1` |
| `sp_x` | X of the splash and its drips; `-1` = no splash. | number | required |
| `sp_y` | Y as `[normal, anal]`. | list | required |
| `sp_anim_x`, `sp_anim_y` | Pixels the splash moves per body animation frame, to follow the body. | number | required |

`sq_y` and `sp_y` must be lists even with one value (`[-30]`), which is then used for both cases. With a splash (`sp_x` not -1), set `sp_spr` too.

### 9.9 Optional keys

| Key | What it means | Type | Default |
|-----|---------------|------|---------|
| `character_row` | Strip row of the cell's pose ([9.3](#93-character_row)). | number | `0` |
| `required_class` | Which classes may be put in the cell (below). | number, text or list | anyone |
| `slot_range` | Effect radius in cells; on a breeding cell only a range indicator in the MOD window (vanilla CLEAN, TRANSFER, PATROL and shrines use it with own scripts). | number | `-1` (none) |
| `range_draw_func` | Script drawing that indicator, only with `slot_range`: `"scr_draw_mod_range"` (default look) or `"scr_draw_l_shrine_range"`. | text | default indicator |
| `scr_unoccupy` | Script run when the captive leaves. `"scr_gnx_unoccupy_log"` only logs `[GNX] scr_gnx_unoccupy_log slot h=<id>`. | text | none |
| `sign_y_base` | Height of the type 1 sign, in pixels from the floor line (vanilla −84 to −92); without it the sign sits at the floor line. | number | none |
| `sign_y_jitter` | Random extra height (−jitter to +jitter) picked when built; only with `sign_y_base`. | number | `2` |
| `mon_placements`, `mon_positions` | Multi-monster settings ([§11](#11-multi-monster-cells)). | list | none |

**required_class** limits who can be placed in the cell: a class ID (`"required_class": 0`), a class ref `"<folder>.<class name>"` (`"required_class": "my_mod.Witch"`), or a list of both (`["my_mod.Witch", 0]`).

Refs are case-sensitive and work for any mod ([3.3](#33-load-order)). A ref that is not found logs `[GNX-WARN] cell h=<id> required_class ref '<ref>' not found. Check: folder name + class name must match exactly (case-sensitive).`, and the self-test reports `[GNX-TEST] FAIL  T84 bad required_class: …`. That entry matches nobody: a single unresolved ref lets **nobody** in, while in a list only that entry fails.

On big cells, `required_class` replaces the vanilla class locks of DAIRY (cow), GIANT (giant), CHAINS (Morrigan) and L.SHRINE (Lilith). A class with `only_listed_cells: true` ([§6](#6-classes-classesjson)) enters only cells whose `required_class` lists it.

> **When** a cell is a tentacle cell (`t_breed`, `t_utility`), `required_class` is **not checked**: every class can be placed there, except `only_listed_cells` classes the cell does not list.

**TRANSFER and modded classes.** After birth or milking, or in a TRANSFER cell, vanilla sends Lilith, Morrigan and Cow to their own cells (SHRINE 39, CHAINS 38, DAIRY 36). A modded class (ID ≥ 14) treats every cell whose `required_class` lists it as its own: GNX tries a free one in range first, otherwise a regular cell (still subject to `required_class` and `only_listed_cells`).

### 9.10 Advanced vanilla-pattern fields

Starting values some vanilla cells need. Only the matching vanilla scripts read them; with the GNX draw script and standard scene scripts most do nothing.

| Key | What it does | Type | Vanilla cells using it |
|-----|--------------|------|------------------------|
| `bar_glow_rep` | Glow repeat count for the captive's progress bar. | number | RECOVER (`0`) |
| `milk_step` | Starting milking step counter. | number | MILK 1 (`0`) |
| `milk_num` | Starting milk counter. | number | MILK 2 (`0`) |
| `drink_num` | Starting drink counter. | number | DRINK (`0`) |
| `mon_index` | Only its length is used: a zero-filled list of that length. | list | DRINK (`[0, 0]`) |
| `blink_spr` | Captive blink sprite; only the DAIRY draw script uses it. | sprite | DAIRY (`spr_cow_blink`) |
| `anim_struct_overrides` | Extra animation values set when built; `char_state` is also applied when a captive enters. | object | DAIRY, TRANSFER, PATROL |
| `visual` | Turns on the "visual" display mode used by vanilla scripts. | true/false | TRANSFER, PATROL (`true`) |
| `slot_front` | Sprite in front of the cell, drawn only by the vanilla tentacle draw script, not `scr_draw_slot_gnx`. | sprite or -1 | T.WALL 1–3, MILK 2, RECOVER |
| `sp_place_init` | `true` = start an empty list of splash places. | true/false | G.BANG 1, CHAINS |
| `set_timer` | Starting value of a timer used by vanilla scripts. | number | G.BANG 1–3, CHAINS (`0`) |
| `slot_h` | `false` = no captive can be put in the cell. | true/false | S/F/R.SHRINE, CLEAN, CLONE (`false`) |
| `scr_slot_step` | Script run every step while the cell is **empty**; a captive entering replaces it, and it is cleared when she leaves. Use only with `slot_h: false`. | text | R.SHRINE, CLEAN, CLONE |
| `scr_slot_base` | Extra script run every step next to `scr_idle`/`scr_h`, not replacing them. | text | L.SHRINE (`scr_slot_h_lilith_idle`) |
| `candle_index` | Starting candle frame, used only by L.SHRINE scripts. | number | L.SHRINE (`0`) |
| `clone_wait` | Starting clone timer. | number | CLONE (`0`) |
| `extra_spawn_part` | `true` = one extra particle switch. | true/false | T.WALL 1–3, BIND 1–2 |
| `dirt_fix_inc` | `true` = while the cell exists, dirt no longer lowers mood. | true/false | L.SHRINE |
| `death_fix_inc` | `true` = turns on the death-protection counter once when built. | true/false | S.SHRINE |
| `del_item_type` | When built, removes the first inventory item of this type. | number | DAIRY (`2`) |

> **When** `scr_slot_step` or `scr_slot_base` has a typo, nothing warns; the script simply never runs.

---

## 10. Cell sprites: human_spr and mon_spr

**In short:** `human_spr` decides where the captive's sprites come from; `mon_spr` (with `mon_spr_hob` and `mon_spr_ogr`) replaces the monsters' sprites in this cell. The `layers` say *where and in which order* body parts are drawn, `human_spr` says *which sprites* fill them.

### 10.1 human_spr: the three modes

| `mode` | Where the captive's sprites come from | Use it when |
|--------|----------------------------------------|-------------|
| `"base+class"` | Vanilla base body strips plus each class's clothing ([§7](#7-clothing-maps-how-a-class-looks-in-each-cell)), at row `character_row`. | You reuse a vanilla pose. |
| `"fixed"` | One sprite table per phase, written in the cell; the same for every class, with optional per-class exceptions. | Your own pose, same look for everyone. |
| `"class_map"` | A sprite table per class, plus a `default` for all others. | Your own pose, different art per class. |

`human_spr` is optional; without it, or without `mode`, the cell uses `base+class`. Without `base_body`, GNX takes it from `category`: `b_…` (or `slot_type` 2) gives `"big"`, `t_…` (or `slot_type` 3) gives `"tent"`, all others `"standard"` ([10.7](#107-categories-and-base_body)). With `fixed` or `class_map`, write both keys anyway.

A [phase](#2-glossary) is an animation stage: 0 start, 1 idle, 2 loop, 3 ejaculation (uses the phase 2 table), 4 tentacle birth.

### 10.2 base+class

```json
{
  "human_spr": { "mode": "base+class", "base_body": "standard" }
}
```

- The captive is drawn as in a vanilla cell: base body plus the class's `clothing_standard` (or `clothing_big`/`clothing_tent`, by `base_body`).
- `physical.character_row` picks the vanilla pose ([9.3](#93-character_row)). You must list the body layers (types 6–10) yourself.
- `is_special` classes use their own sprite tables instead ([§16](#16-special-classes-and-monster-sprite-overrides)).

### 10.3 fixed

```json
{
  "human_spr": {
    "mode": "fixed",
    "base_body": "standard",
    "phase_1": {
      "spr_array": [-1, "gnx:altar_idle_head", "gnx:altar_idle_breast", -1, "gnx:altar_idle_leg", -1, -1],
      "spr_c_array": ["gnx:altar_idle_hair", -1, "gnx:altar_idle_breast_c", -1, -1, -1, -1]
    },
    "phase_2": {
      "spr_array": [-1, "gnx:altar_loop_head", "gnx:altar_loop_breast", -1, "gnx:altar_loop_leg", -1, -1],
      "spr_c_array": ["gnx:altar_loop_hair", -1, "gnx:altar_loop_breast_c", -1, -1, -1, -1]
    }
  }
}
```

Every class looks the same in this cell. `phase_1` is used while idle (and for the start of a standard cell), `phase_2` for the loops and ejaculation. `spr_array` holds the body sprites (here head, breast, legs), `spr_c_array` the clothing overlays and the hair (here a breast overlay and hair).

| Phase key | Used for | Needed |
|-----|----------|--------|
| `phase_0` | start, only with `base_body: "big"` and `scr_slot_h_big_start` | big cells with `scr_slot_h_big_start` |
| `phase_1` | idle; also the start on non-big cells | always |
| `phase_2` | loops and ejaculation | always |
| `phase_4` | tentacle birth | tentacle cells with a birth step |

The positions are the slots of [7.7](#77-special-class-tables-spr_array-and-spr_c_array): `[0]` hair (only in `spr_c_array`, drawn with the captive's hair colour), `[1]` head, `[2]` breast, `[3]` hand, `[4]` leg, `[5]` leg part, `[6]` cape (only in `spr_array`). Write 7 positions in `spr_array` and at least 6 in `spr_c_array`, with `-1` for "nothing".

**Strip layout.** Fixed mode has no skin colours: one block per row, frame = row × frames per row + frame. The hair strip still has 3 blocks per row, one per hair colour ([§5](#5-sprites)).

> **When** phases or lists are missing:
> - Without `phase_1` or `phase_2` the self-test reports `[GNX-TEST] FAIL  DROUTE h=<id> FIXED_MISSING_PHASE`; in game, the missing phase uses the vanilla sprites for that cell size.
> - A big fixed cell with `scr_slot_h_big_start` but no `phase_0` shows the vanilla big-cell base body during the start.
> - Lists shorter than the layers need cause an error when the captive enters (positions 0–5 are always read, 6 when the cell has a type 11 layer).

### 10.4 by_class and by_mon_type (fixed mode only)

Inside a fixed-mode phase, `by_class` gives some classes their own sprites, and inside a `by_class` entry `by_mon_type` can change them again for one monster type.

```json
{
  "phase_2": {
    "spr_array": [-1, "gnx:altar_loop_head", "gnx:altar_loop_breast", -1, "gnx:altar_loop_leg", -1, -1],
    "spr_c_array": ["gnx:altar_loop_hair", -1, -1, -1, -1, -1, -1],
    "by_class": {
      "my_mod.Witch": {
        "spr_array": [-1, "gnx:witch_altar_loop_head", "gnx:witch_altar_loop_breast", -1, "gnx:witch_altar_loop_leg", -1, -1],
        "spr_c_array": [-1, -1, -1, -1, -1, -1, -1],
        "by_mon_type": {
          "1": {
            "spr_array": [-1, "gnx:witch_altar_hob_head", "gnx:witch_altar_hob_breast", -1, "gnx:witch_altar_hob_leg", -1, -1],
            "spr_c_array": [-1, -1, -1, -1, -1, -1, -1]
          }
        }
      }
    }
  }
}
```

Every class uses the phase's own lists except the Witch, who uses her `by_class` entry, or its `by_mon_type` entry when the monster is a hobgoblin (`"1"`). Checks go `by_mon_type` → `by_class` → the phase's lists.

- `by_class` keys: a class ref `"<folder>.<class name>"` or a class ID as text (`"9"` = vanilla cow), resolved when the cell loads, so classes of any mod work ([3.3](#33-load-order)). A miss logs `[GNX-WARN] by_class '<ref>' not found. Check: folder name + class name must match exactly (case-sensitive).`
- `by_mon_type` keys: `"0"` goblin, `"1"` hobgoblin, `"2"` tentacle, `"3"` ogre.
- Each entry needs a 7-position `spr_array` and a `spr_c_array` with at least 6 positions, as in [10.3](#103-fixed).

> **When** a cell holds several monsters ([§11](#11-multi-monster-cells)), `by_mon_type` looks only at the **first** one.

### 10.5 class_map

```json
{
  "human_spr": {
    "mode": "class_map",
    "base_body": "standard",
    "default": {
      "phase_1": {
        "spr_array": [-1, "gnx:altar_idle_head", "gnx:altar_idle_breast", -1, "gnx:altar_idle_leg", -1, -1],
        "spr_c_array": ["gnx:altar_idle_hair", -1, -1, -1, -1, -1, -1]
      },
      "phase_2": {
        "spr_array": [-1, "gnx:altar_loop_head", "gnx:altar_loop_breast", -1, "gnx:altar_loop_leg", -1, -1],
        "spr_c_array": ["gnx:altar_loop_hair", -1, -1, -1, -1, -1, -1]
      }
    },
    "classes": {
      "my_mod.Witch": {
        "phase_1": {
          "spr_array": [-1, "gnx:witch_altar_idle_head", "gnx:witch_altar_idle_breast", -1, "gnx:witch_altar_idle_leg", -1, -1],
          "spr_c_array": ["gnx:witch_altar_idle_hair", -1, "gnx:witch_altar_idle_breast_c", -1, "gnx:witch_altar_idle_leg_c", -1, -1]
        },
        "phase_2": {
          "spr_array": [-1, "gnx:witch_altar_loop_head", "gnx:witch_altar_loop_breast", -1, "gnx:witch_altar_loop_leg", -1, -1],
          "spr_c_array": ["gnx:witch_altar_loop_hair", -1, "gnx:witch_altar_loop_breast_c", -1, "gnx:witch_altar_loop_leg_c", -1, -1]
        }
      }
    }
  }
}
```

The Witch uses her own entry under `classes`, with clothing overlays; every other class uses `default`. Phases and positions are as in fixed mode ([10.3](#103-fixed)).

- `classes` keys: class refs or class IDs as text; refs to **any** mod work, as they are resolved again after all mods load. A miss logs `[GNX-WARN] class_map h=<id> unresolved ref: <ref>`.
- class_map strips keep **3 skin blocks per row**, unlike fixed mode; `is_special` classes use one.
- Only `spr_array` and `spr_c_array` are read per phase; `by_mon_type` and `by_class` do nothing here.
- A class with no entry and no `default` fails the self-test (`[GNX-TEST] FAIL  DROUTE h=<id> c=<class> CLASS_MAP_NO_MATCH`) and gets the vanilla fallback sprites. So does a listed class whose entry lacks the needed phase: `default`'s phase is **not** used (verbose log: `[GNX-WARN] class_map h=<id> c=<class> missing phase_<n>`).

### 10.6 Dispatch order

When a phase starts, GNX picks the captive's sprites in this order:

1. GIANT (h_type 37) and the class has `clothing_giant` → that `clothing_giant` phase ([§7](#7-clothing-maps-how-a-class-looks-in-each-cell)).
2. `mode: "fixed"` → `by_mon_type` → `by_class` → the phase's lists. A missing phase goes to step 5.
3. `mode: "class_map"` → the class's entry or `default` → that phase. A missing entry or phase goes to step 5.
4. Otherwise (base+class): `is_special` classes use their own tables by `base_body`, all others the base body plus their clothing.
5. Vanilla fallback: the built-in sprites for that cell size.

### 10.7 Categories and base_body

`category` ([8.4](#84-category-build-menu-tab-and-cell-size)) sets the cell size. Pick the matching `base_body`:

| `category` | Cell size | `base_body` |
|------------|-----------|-------------|
| `breed`, `utility`, `pleasure` | standard, 45 px | `"standard"` |
| `b_breed`, `b_utility`, `b_other` | big, 77 px | `"big"` |
| `t_breed`, `t_utility` | tentacle, 45 px | `"tent"` |
| `xl_breed` | XL, 150 px | no XL value; see below |

In fixed and class_map mode `base_body` only decides whether the start uses `phase_0` (only with `"big"`). There is no XL base body, so an XL cell should use fixed or class_map mode with its own sprites (and `"standard"` or `"big"`).

### 10.8 mon_spr: monster sprites

`mon_spr` replaces the goblin sprites in this cell, `mon_spr_hob` the hobgoblin's and `mon_spr_ogr` the ogre's, all with the same structure. This example gives the ALTAR its own goblin and hobgoblin:

```json
{
  "mon_types": [0, 1],
  "mon_spr": {
    "start": {
      "body": {
        "leg_1": { "alpha": "gnx:gob_altar_start_v1", "line": "gnx:gob_altar_start_v1_line" },
        "leg_2": { "alpha": "gnx:gob_altar_start_v2", "line": "gnx:gob_altar_start_v2_line" },
        "leg_any": { "alpha": "gnx:gob_altar_start_v1", "line": "gnx:gob_altar_start_v1_line" }
      },
      "hand": { "alpha": "gnx:gob_altar_start_hand", "line": "gnx:gob_altar_start_hand_line" },
      "pen": "gnx:gob_altar_start_pen",
      "touch": "gnx:gob_altar_start_touch",
      "hand_xscale": "random"
    },
    "loop": {
      "head": [
        { "alpha": "gnx:gob_altar_head_a", "line": "gnx:gob_altar_head_a_line" },
        { "alpha": "gnx:gob_altar_head_b", "line": "gnx:gob_altar_head_b_line" }
      ],
      "body": {
        "leg_any": { "alpha": "gnx:gob_altar_loop", "line": "gnx:gob_altar_loop_line" },
        "cow": { "alpha": "gnx:gob_altar_loop_cow", "line": "gnx:gob_altar_loop_cow_line" }
      },
      "hand": {
        "leg_any": { "alpha": "gnx:gob_altar_loop_hand", "line": "gnx:gob_altar_loop_hand_line" }
      },
      "pen": "gnx:gob_altar_loop_pen",
      "touch": { "default": "gnx:gob_altar_loop_touch", "cow": "gnx:gob_altar_loop_touch_cow" },
      "enter": "gnx:gob_altar_loop_enter"
    },
    "ej": {
      "body": {
        "leg_any": { "alpha": "gnx:gob_altar_ej", "line": "gnx:gob_altar_ej_line" }
      }
    }
  },
  "mon_spr_hob": {
    "start": {
      "body": {
        "leg_any": { "alpha": "gnx:hob_altar_start", "line": "gnx:hob_altar_start_line" }
      }
    },
    "loop": {
      "body": {
        "leg_any": { "alpha": "gnx:hob_altar_loop", "line": "gnx:hob_altar_loop_line" }
      },
      "pen": "gnx:hob_altar_loop_pen"
    }
  }
}
```

(Every `gnx:` key also needs an entry in the cell's `sprites`, as in [8.1](#81-minimal-example-the-altar-cell).)

**What this example does**

- `"mon_types": [0, 1]`: goblins and hobgoblins come, and both may use this cell's sprites.
- `start`: the body depends on the captive's leg variant (`leg_1`, `leg_2`, otherwise `leg_any`); the hand is one fill + line pair; `pen` and `touch` are single sprites; `"hand_xscale": "random"` mirrors the goblin's hand at random each time.
- `loop` (both loops): one of two heads is picked at random each time the loop sprites are set. The vanilla Cow class gets the `cow` body and touch overlay. `enter` is the penetration overlay.
- `ej` replaces only the body during ejaculation; every other part comes from `loop`.
- `mon_spr_hob` has no head, hand, touch or enter, so those parts are not drawn for the hobgoblin.

### 10.9 mon_spr reference

**Phase blocks**

| Block | Used during | Keys it reads |
|-------|-------------|---------------|
| `start` | the start step | `body`, `hand`, `pen`, `touch`, `hand_xscale` |
| `loop` | slow and fast loop; fallback for `ej` | `head`, `body`, `hand`, `pen`, `touch`, `enter` |
| `ej` | ejaculation | as `loop`; each missing part uses `loop` |

**Part keys**

| Key | What it is | Format |
|-----|------------|--------|
| `body` | The monster's body. Required in practice: no body = vanilla sprites ([10.10](#1010-when-gnx-uses-vanilla-monster-sprites)). | object of variants (below) |
| `hand` in `start` | The monster's hand. | one pair or one sprite, no variants |
| `hand` in `loop`/`ej` | The monster's hand. | variants: `leg_any`, `leg_1`, `leg_2`, `cow` |
| `head` | Head (`loop` and `ej` only). | one pair, or a list of which the first two are used 50/50 |
| `pen` | Drawn first, behind the other monster parts, without transparency. | one sprite |
| `touch` | Hand-on-captive overlay, on the captive's leg layer (type 8). | one sprite or class variants |
| `enter` | Penetration overlay on the leg layer (`loop`/`ej` only). | one sprite or class variants |
| `hand_xscale` | `"random"` = mirror the hand at random; `start` only, other values ignored. Loop and ejaculation always use the normal direction. | text |

A **pair** is `{ "alpha": <fill sprite>, "line": <outline sprite> }`; `line` is optional, and a plain sprite name is a pair without a line. The game's monster transparency setting decides how fill and line are drawn; the line is drawn in all three modes.

**Body and hand variants:** `cow` (vanilla Cow, body and hand), `lilith` (vanilla Lilith, body only), `leg_1`, `leg_2` (captive leg variants), `leg_any` (everyone else, and the fallback). GNX checks the class variant, then the leg variant, then `leg_any`. There is no `leg_0`: kneeling captives use `leg_any` ([§7](#7-clothing-maps-how-a-class-looks-in-each-cell)).

**Touch and enter class variants:** `default`, `cow`, `nyx`, `lilith`, `morrigan`, `cat` (the vanilla classes of those names); every other class, and a plain sprite name, means `default`. Class variants matter only in cells with ID 100 or more, where vanilla classes get custom monster sprites.

**Frame layout of monster strips:** frame = row × frames per row + current frame, with row = `character_row` (or the placement with `mon_positions`). With the standard scene scripts a row has 2 frames for `start` and 5 for `loop` and `ej` (ejaculation shows frames 2–4).

**Frame layout of touch and enter:** they use the **captive's** frame numbers, so they need the layout of the captive's strips (3 skin blocks per row in base+class and class_map, 1 in fixed mode). `touch` is not drawn in the third monster transparency mode.

> **When** monster sprites have the wrong shape, they are ignored:
> - `body` and the loop/ej `hand` must use variants. A pair directly under `body` (`"body": { "alpha": … }`) is ignored, and the monster falls back to vanilla sprites.
> - `start.hand` is the opposite: one pair only; variant keys inside it are ignored.
> - `touch` and `enter` are stored once per cell, not per monster ([§11](#11-multi-monster-cells)).

### 10.10 When GNX uses vanilla monster sprites

GNX draws vanilla monster sprites instead of yours when:

- the cell has no block for that monster type. `mon_spr_hob` and `mon_spr_ogr` fall back to `mon_spr`, so with only `mon_spr`, **hobgoblins and ogres get your goblin art**; limit `mon_types` or add their blocks;
- the monster type is not in `mon_types`;
- the phase block has no body (for example no `start`); without start art, point `start.body` at your loop strips (with row 0 the start shows their first two frames);
- the captive is a vanilla class (ID below 14) and the cell ID is below 100;
- for goblins, in an anal scene with a vanilla captive ([9.2](#92-anal)).

**Ogres.** By default an ogre in a custom cell is **one opaque body sprite**: only the `body` alpha is used and the transparency setting does not apply. If the ogre's body in `mon_spr_ogr` has both `alpha` and `line`, the ogre is drawn like goblins: fill plus outline, following the player's MON TYPE and OPACITY settings.

```json
{
  "mon_spr_ogr": {
    "loop": {
      "body": {
        "leg_any": { "alpha": "gnx:ogre_altar_loop", "line": "gnx:ogre_altar_loop_l" }
      }
    }
  }
}
```

Here the loop body has fill `ogre_altar_loop` and outline `ogre_altar_loop_l` for any leg pose. Without `line` the ogre stays opaque.

---

## 11. Multi-monster cells

**In short:** a cell with `max_mon_num` above 1 holds several monsters at once. `mon_placements` gives each monster a spot ([placement](#2-glossary)) and the monster types allowed there; per-placement sprite keys give each spot its own art. This example is a big cell with a hobgoblin in front of the captive and a goblin or ogre behind her.

```json
[
  {
    "name": "BIG ALTAR",
    "category": "b_breed",
    "mon_types": [0, 1, 3],
    "price": 600,
    "spawn_info": { "coin": 3, "mood": 2, "coin_mul": true, "mood_mul": false },
    "physical": {
      "allow_preg": true,
      "max_mon_num": 2,
      "mon_placements": [
        [1],
        [0, 3]
      ],
      "anal": -1,
      "slot_dirt_init": 0,
      "layers": [
        [12, "spr_dirt_big", false, -1, false],
        [0, "gnx:big_altar_back", false, -1],
        [8, -1, false, -1, false]
      ],
      "scr_idle": "scr_slot_h_state_idle",
      "scr_h": ["scr_slot_h_big_start", "scr_slot_h_base_wait", "scr_slot_h_base_sloop", "scr_slot_h_base_floop", "scr_slot_h_base_wait", "scr_slot_h_base_ej", "scr_slot_h_base_wait"],
      "scr_draw": "scr_draw_slot_gnx",
      "hand_x": [],
      "hand_y": [],
      "hand_xscale": [],
      "hand_angle": [],
      "sp_spr": "spr_sp_v_start",
      "sq_x": 38,
      "sq_y": [-30],
      "sp_x": 38,
      "sp_y": [-30],
      "sp_anim_x": 0,
      "sp_anim_y": 1
    },
    "human_spr": {
      "mode": "fixed",
      "base_body": "big",
      "phase_0": {
        "spr_array": [-1, -1, -1, -1, "gnx:big_altar_start", -1, -1],
        "spr_c_array": [-1, -1, -1, -1, -1, -1, -1]
      },
      "phase_1": {
        "spr_array": [-1, -1, -1, -1, "gnx:big_altar_idle", -1, -1],
        "spr_c_array": [-1, -1, -1, -1, -1, -1, -1]
      },
      "phase_2": {
        "spr_array": [-1, -1, -1, -1, "gnx:big_altar_loop", -1, -1],
        "spr_c_array": [-1, -1, -1, -1, -1, -1, -1]
      }
    },
    "mon_spr_hob_p0": {
      "start": {
        "body": { "leg_any": "gnx:hob_front_start" }
      },
      "loop": {
        "body": { "leg_any": "gnx:hob_front_loop" }
      }
    },
    "mon_spr_p1": {
      "start": {
        "body": { "leg_any": "gnx:gob_back_start" }
      },
      "loop": {
        "body": { "leg_any": "gnx:gob_back_loop" },
        "enter": "gnx:gob_back_enter"
      }
    },
    "mon_spr_ogr_p1": {
      "start": {
        "body": { "leg_any": "gnx:ogre_back_start" }
      },
      "loop": {
        "body": { "leg_any": "gnx:ogre_back_loop" }
      }
    },
    "sprites": {
      "big_altar_back": { "strip": "strips/spr_slot_big_altar_back.png", "frames": 1, "origin_from": "spr_big_slot_back" },
      "big_altar_start": { "strip": "strips/spr_h_big_altar_start.png", "frames": 2, "origin_from": "spr_h_base_big_start_head" },
      "big_altar_idle": { "strip": "strips/spr_h_big_altar_idle.png", "frames": 2, "origin_from": "spr_h_base_big_idle_head" },
      "big_altar_loop": { "strip": "strips/spr_h_big_altar_loop.png", "frames": 5, "origin_from": "spr_h_base_big_loop_head" },
      "hob_front_start": { "strip": "strips/spr_h_hobgoblin_big_altar_front_start.png", "frames": 2, "origin_from": "spr_h_hobgoblin_body_start_v1_alpha" },
      "hob_front_loop": { "strip": "strips/spr_h_hobgoblin_big_altar_front_loop.png", "frames": 5, "origin_from": "spr_h_hobgoblin_body_loop_v1_alpha" },
      "gob_back_start": { "strip": "strips/spr_h_goblin_big_altar_back_start.png", "frames": 2, "origin_from": "spr_h_goblin_body_start_v1_alpha" },
      "gob_back_loop": { "strip": "strips/spr_h_goblin_big_altar_back_loop.png", "frames": 5, "origin_from": "spr_h_goblin_body_loop_v1_alpha" },
      "gob_back_enter": { "strip": "strips/spr_h_goblin_big_altar_back_enter.png", "frames": 5, "origin_from": "spr_h_base_big_loop_head" },
      "ogre_back_start": { "strip": "strips/spr_h_ogre_big_altar_back_start.png", "frames": 2, "origin_from": "spr_h_ogre_body_start" },
      "ogre_back_loop": { "strip": "strips/spr_h_ogre_big_altar_back_loop.png", "frames": 5, "origin_from": "spr_h_ogre_body_loop" }
    }
  }
]
```

**What this example does**

- `b_breed` makes a big (77 px) cell. It starts with `scr_slot_h_big_start`, so the fixed `human_spr` has a `phase_0`. For brevity the whole captive is one sprite per phase on the leg layer (type 8, `spr_array[4]`); the other body layers are auto-added and stay empty.
- `"max_mon_num": 2` with two `mon_placements`: spot 0 (in front) takes only hobgoblins (`[1]`), spot 1 (behind) a goblin or ogre (`[0, 3]`). `mon_types` lists all three types, so they may use this cell's sprites.
- `mon_spr_hob_p0` is the front hobgoblin; `mon_spr_p1` and `mon_spr_ogr_p1` are the goblin and ogre behind her. They use plain sprite names (fill only). The ogre gets only a body, because ogres in custom cells are drawn as one body sprite anyway ([10.10](#1010-when-gnx-uses-vanilla-monster-sprites)).
- Only the back monsters have `enter`, because `touch`/`enter` are shared by the whole cell ([11.4](#114-how-a-scene-runs-with-several-monsters)). The `enter` strips use the captive's frame layout ([10.9](#109-mon_spr-reference)): fixed mode, one row, 5 loop frames.
- There is no `mon_positions`: each placement's art is already drawn in the right spot inside its strip, and all strips use row 0.

### 11.1 mon_placements

`mon_placements` has one entry per placement, as many as `max_mon_num`. Each entry lists the monster types allowed there (`0` goblin, `1` hobgoblin, `2` tentacle, `3` ogre).

- A called monster gets a random free placement, then a random type from that placement's list. A placement only fills if a free monster of that type exists in the nest.
- `mon_types` then no longer decides who comes, but it still filters the custom sprites, so it must contain every type from the placements.
- **Without `mon_placements`, every monster gets placement 0.** They are drawn on top of each other, and `_p1`/`_p2` sprites and later `mon_positions` entries are never used.

### 11.2 Per-placement sprite keys

These top-level keys work like `mon_spr` ([10.8](#108-mon_spr-monster-sprites)), but for one placement only:

| Monster | Placement 0 | Placement 1 | Placement 2 |
|---------|-------------|-------------|-------------|
| goblin | `mon_spr_p0` | `mon_spr_p1` | `mon_spr_p2` |
| hobgoblin | `mon_spr_hob_p0` | `mon_spr_hob_p1` | `mon_spr_hob_p2` |
| ogre | `mon_spr_ogr_p0` | `mon_spr_ogr_p1` | `mon_spr_ogr_p2` |

Only placements 0–2 have keys. A monster at placement N falls back like this: goblin `mon_spr_p<N>` → `mon_spr`; hobgoblin `mon_spr_hob_p<N>` → `mon_spr_hob` → `mon_spr`; ogre `mon_spr_ogr_p<N>` → `mon_spr_ogr` → `mon_spr`. A hobgoblin never uses `mon_spr_p<N>`.

### 11.3 mon_positions

`mon_positions` (inside `physical`) shifts each placement's monster by a few pixels: a list of `{ "x": …, "y": … }`, one per placement. The shift works in every cell, including a patch of a vanilla cell ([§12](#12-patching-vanilla-cells-and-classes)).

```json
{
  "physical": {
    "max_mon_num": 2,
    "mon_placements": [
      [0],
      [0]
    ],
    "mon_positions": [
      { "x": -6, "y": 0 },
      { "x": 8, "y": -2 }
    ]
  }
}
```

Two goblins: the first moved 6 px left, the second 8 px right and 2 px up.

> **When** `mon_positions` is set in a cell with ID 100 or more (hashed IDs always are), the **monster strip row** becomes the placement number instead of `character_row`: placement 0 reads row 0, placement 1 row 1, and so on. A monster strip then needs rows up to the highest placement it is used at: one used only at placement 1 still needs row 1 (row 0 may stay empty). Above, a loop strip has 2 rows × 5 = 10 frames. The captive's strips are not affected, and a patched vanilla cell keeps its own monster rows. If you need no pixel shift, leave `mon_positions` out and draw each placement in place, as in BIG ALTAR.

### 11.4 How a scene runs with several monsters

- **Monsters join during the scene.** The idle, wait, loop and ejaculation scripts keep calling monsters until the cell is full (the start scripts do not). When one arrives, the current step starts over.
- **A newcomer gets its cell sprites** when the next start, slow loop (`scr_slot_h_base_sloop`) or ejaculation step begins. Until then (in the fast loop or a wait) it shows its normal walking sprite.
- **touch and enter are shared.** The cell stores one of each, from the monster whose sprites were set last, and clears them when a monster leaves. Put `touch`/`enter` only in the placement that should show them.
- **Ejaculation ends the scene for everyone.** With `max_mon_num` above 1 the standard ejaculation script removes **all** monsters. The payout ([8.6](#86-spawn_info-gold-and-mood)) and the pregnancy roll happen once per scene. The offspring type, and `by_mon_type` ([10.4](#104-by_class-and-by_mon_type-fixed-mode-only)), use the first monster in the cell's list (the one called first).

---

## 12. Patching vanilla cells and classes

**In short:** a cell entry whose `h_type` already exists changes that cell instead of creating a new one. Use it to let your class into a vanilla cell, give it its own sprites there, or swap a vanilla cell's layers. Only some fields can be patched; the rest are ignored without a message.

This example lets the Witch use L.SHRINE (LILITH SHRINE, h_type 39) with her own sprites:

```json
[
  {
    "h_type": 39,
    "physical": {
      "required_class": ["my_mod.Witch"]
    },
    "human_spr": {
      "phase_1": {
        "by_class": {
          "my_mod.Witch": {
            "spr_array": [-1, "gnx:witch_shrine_idle_head", "gnx:witch_shrine_idle_breast", -1, "gnx:witch_shrine_idle_leg", -1, -1],
            "spr_c_array": [-1, -1, "gnx:witch_shrine_idle_breast_c", -1, "gnx:witch_shrine_idle_leg_c", -1, -1]
          }
        }
      },
      "phase_2": {
        "by_class": {
          "my_mod.Witch": {
            "spr_array": [-1, "gnx:witch_shrine_loop_head", "gnx:witch_shrine_loop_breast", -1, "gnx:witch_shrine_loop_leg", -1, -1],
            "spr_c_array": [-1, -1, "gnx:witch_shrine_loop_breast_c", -1, "gnx:witch_shrine_loop_leg_c", -1, -1]
          }
        }
      }
    },
    "sprites": {
      "witch_shrine_idle_head": { "strip": "strips/spr_h_witch_shrine_idle_head.png", "frames": 6, "origin_from": "spr_h_lilith_shrine_idle_head" },
      "witch_shrine_idle_breast": { "strip": "strips/spr_h_witch_shrine_idle_breast.png", "frames": 6, "origin_from": "spr_h_lilith_shrine_idle_breast" },
      "witch_shrine_idle_breast_c": { "strip": "strips/spr_h_witch_shrine_idle_breast_c.png", "frames": 6, "origin_from": "spr_h_lilith_shrine_idle_breast_c" },
      "witch_shrine_idle_leg": { "strip": "strips/spr_h_witch_shrine_idle_leg.png", "frames": 6, "origin_from": "spr_h_lilith_shrine_idle_leg" },
      "witch_shrine_idle_leg_c": { "strip": "strips/spr_h_witch_shrine_idle_leg_c.png", "frames": 6, "origin_from": "spr_h_lilith_shrine_idle_leg_c" },
      "witch_shrine_loop_head": { "strip": "strips/spr_h_witch_shrine_loop_head.png", "frames": 15, "origin_from": "spr_h_lilith_shrine_loop_head" },
      "witch_shrine_loop_breast": { "strip": "strips/spr_h_witch_shrine_loop_breast.png", "frames": 15, "origin_from": "spr_h_lilith_shrine_loop_head" },
      "witch_shrine_loop_breast_c": { "strip": "strips/spr_h_witch_shrine_loop_breast_c.png", "frames": 15, "origin_from": "spr_h_lilith_shrine_loop_head" },
      "witch_shrine_loop_leg": { "strip": "strips/spr_h_witch_shrine_loop_leg.png", "frames": 15, "origin_from": "spr_h_lilith_shrine_loop_leg" },
      "witch_shrine_loop_leg_c": { "strip": "strips/spr_h_witch_shrine_loop_leg_c.png", "frames": 15, "origin_from": "spr_h_lilith_shrine_loop_leg_c" }
    }
  }
]
```

**What this example does**

- `required_class` is **merged**: vanilla L.SHRINE allows Lilith (class 8), and after the patch Lilith and the Witch. You do not need to repeat `8`.
- L.SHRINE is a vanilla fixed-mode cell, so each phase gets a `by_class` entry for the Witch. The phases have no lists of their own, so Lilith keeps her vanilla sprites, and `mode`, `base_body` and every other field not given stay as they were.
- The hand position `[3]` is `-1`, so the Witch is drawn without the shrine's hand sprite.
- The frame counts (6 = 3 skins × 2 idle frames, 15 = 3 × 5 loop frames) assume that L.SHRINE's vanilla draw script reads normal classes with 3 skin blocks per row. Check in game.

Every vanilla patch writes two lines to `gnx_debug.txt`. The warning also appears for intentional patches; ignore it then.

```
[GNX-WARN] mod 'my_mod' patches vanilla cell h=39 (h_type 1-42 are vanilla). Remove 'h_type' from cells.json to auto-assign a unique ID.
[GNX] patched h=39 by mod=my_mod
```

### 12.1 When an entry is a patch

An entry is a patch when it has an explicit `h_type` that is already registered: a vanilla cell (1–15, 17–25, 27–34, 36–42) or a cell of a mod that loaded earlier (see that mod's `[GNX] cell OK: h=<id> …` line). IDs 0, 16, 26 and 35 are not cells, so such an entry registers as a new cell. An entry without `h_type` is never a patch; its hash ID moves to the next free number on a clash.

### 12.2 What a patch changes

| Part | Fields a patch applies | Notes |
|------|------------------------|-------|
| top level | `name`, `price`, `code_text`, `spawn_info`, `slot_type`, `mon_types`, `sfx_type` | `name`, `price`, `spawn_info`, `code_text`: **no visible effect** on vanilla cells (built-in text). |
| monster sprites | `mon_spr`, `mon_spr_hob`, `mon_spr_ogr` | Replaced as a whole. On vanilla cells they affect only captives of class 14 or higher. |
| sprites | `sprites.wall` | Also used to resolve `gnx:` keys inside the patch. |
| `human_spr` | `mode`, `base_body`, `phase_0`, `phase_1`, `phase_2`, `phase_4` | Phases are merged ([12.3](#123-merge-rules-across-mods)). |
| `physical` | every required key of [9.1](#91-required-keys), plus `character_row`, `hand_frames`, `sp_spr`, `mon_placements`, `required_class`, `range_draw_func`, `scr_unoccupy` | Each given field replaces the old value, except `required_class` (merged). |

**Ignored in a patch** (no message): `category`, `locked`, `human_spr.default` and `human_spr.classes` (class_map content), `mon_spr_p0` … `mon_spr_ogr_p2`, every field from [9.10](#910-advanced-vanilla-pattern-fields), `slot_range`, `sign_y_base` and `sign_y_jitter`.

> **When** a patch contains these keys, they do less than expected:
> - `physical.mon_positions` shifts the monsters but keeps the cell's own monster strip rows ([11.3](#113-mon_positions)).
> - `by_class` works only in **fixed-mode** cells: vanilla DAIRY (36), CHAINS (38) and L.SHRINE (39). On a base+class cell (WALL 1, G.BANG …) phases are not read at all.

### 12.3 Merge rules across mods

Several mods can patch the same cell; patches are applied in load order (alphabetical by folder).

- **`required_class`:** merged. New refs are added to the existing list (vanilla plus earlier mods), duplicates are dropped, and a ref that is not found is left out with the `required_class ref … not found` warning.
- **`by_class`:** merged per class key, so mod A's Witch entry and mod B's Queen entry both stay. For the same class key, the later mod's entry replaces the whole earlier one, `by_mon_type` included.
- **`spr_array` / `spr_c_array` in a phase:** kept when the patch phase leaves them out, replaced when it gives them.
- **Everything else:** the later mod wins; a later `layers` list, for example, replaces the earlier one completely.

### 12.4 Example: let the Witch into GIANT

```json
[
  {
    "h_type": 37,
    "physical": {
      "required_class": ["my_mod.Witch"]
    }
  }
]
```

GIANT (h_type 37) accepts only the giant class (11) through its `required_class`; the patch makes the list `[11, Witch]`. That is all access needs, while a `clothing_giant` block alone does not open GIANT. Give the Witch a `clothing_giant` too ([§7](#7-clothing-maps-how-a-class-looks-in-each-cell)): without it GIANT draws her `clothing_standard`, which has no GIANT pose, so she shows the wrong frames.

### 12.5 Patching classes

Classes are patched in `classes.json`: an entry with `"override": true` and the `class_id` of an existing class (vanilla 0–13 or another mod's) is merged into it. The fields you give replace the old ones, the rest stays, and the log shows `[GNX] class_id <id> override (merge)`. Without `override`, `class_id` is ignored and the entry becomes a new class ([§6](#6-classes-classesjson)).

> **When** one mod refers to another, load order matters only for an override of its class or a patch of its cell: that mod must load earlier (alphabetically). Class refs in `required_class`, fixed-mode `by_class` and `class_map` work with any mod ([3.3](#33-load-order)).

---

## 13. Raid spawns and the trade shop

**In short:** `raid_spawns` makes your class appear as a raid enemy, so the player can capture units of it; `trade_stage` puts it in the raid trader's shop. Both are class keys in `classes.json`.

```json
{
  "name": "Witch",
  "raid_spawns": [
    { "stage": 0, "level": 1, "weight": 10, "min_lvl": 0, "max_lvl": 1 },
    { "stage": 2, "level": 2, "weight": 25, "min_lvl": 2, "max_lvl": 3 }
  ],
  "trade_stage": 1
}
```

**What this example does:**

- The first entry adds the Witch to the Village (stage 0), encounter level 1, as unit level 0 or 1 (`min_lvl`–`max_lvl`). Her chance is small: weight 10 against the vanilla total of 100.
- The second adds her to the Forest (stage 2), encounter level 2, at unit level 2–3, with a higher weight.
- `"trade_stage": 1` lets the trader offer her once the player has the Mountain stage.

### 13.1 Stages and encounter levels

Stages: `0` Village, `1` Mountain, `2` Forest, `3` Castle, `4` Tower. Each stage has the encounter levels `0`, `1` and `2`, the difficulty the player selects, which the game shows as lvl 1–3: `"stage": 2, "level": 1` is Forest lvl 2. They are **not** unit levels: `min_lvl`/`max_lvl` set the spawned unit's own level (capped at 7). Quest conditions such as `stage_cleared` use the same stage numbers.

Encounter level `0` is special:

- For stages 0–3, GNX **skips** level-0 entries and logs `[GNX] raid_spawn skipped level=0 class=<id> stage=<stage>`. Mods cannot add enemies to the first level of these stages.
- In the Tower (stage 4), level 0 is the normal tower and level 1 the endless tower; both are allowed.

### 13.2 raid_spawns fields

`raid_spawns` is a list; each entry adds the class to one pool (one stage + encounter level).

| Key | What it means | Type | Default |
|---|---|---|---|
| `stage` | Raid location, 0–4 | number | required |
| `level` | Encounter level: 1–2 for stages 0–3, 0–1 for stage 4 | number | required |
| `weight` | How often the class is picked compared to the rest of the pool | number | `10` |
| `min_lvl` | Lowest unit level of a spawned unit | number | `0` |
| `max_lvl` | Highest unit level. Keep both between 0 and 7, with `min_lvl` ≤ `max_lvl`. | number | `1` |
| `condition` | Spawn only while this is true. Quest condition format ([QUESTS_SCHEMA.md](QUESTS_SCHEMA.md)), checked in your mod's state when an encounter is built. | object | always |
| `max_per_encounter` | Most units of this class in one encounter | number | unlimited |
| `ap_override` | `[HP, AP]` the unit adds to the encounter instead of `fap_mul × level` and `bap_mul × level`. Exactly 2 numbers, otherwise ignored. **Ignored in the Tower**, where enemy HP and AP are fixed. | list | class values |

### 13.3 How weight works

For every enemy slot GNX picks one class from the pool. Its chance is its weight divided by the total weight of all classes that may appear right now (condition true, `max_per_encounter` not reached).

The vanilla pools add up to about 100, with single weights between 12 and 65:

| Stage | Level 1 | Level 2 |
|---|---|---|
| 0 Village | Peasant 50, Nun 50 | Peasant 30, Nun 50, Knight 20 |
| 1 Mountain | Knight 50, Shaman 50 | Shaman 30, Knight 30, Warrior 40 |
| 2 Forest | Ranger 65, Cleric 35 | Samurai 30, Ranger 30, Cleric 40 |
| 3 Castle | Nun 50, Samurai 50 | Peasant, Cleric, Knight, Ranger 17 each; Nun, Samurai 16 each |
| 4 Tower (levels 0 and 1) | Peasant to Warrior, 12 each | — |

Example: the Witch in Village level 1 with weight 10 makes the pool total 110, so each enemy slot is a Witch with chance 10 / 110, about 9%. With weight 100 it would be 100 / 200 = 50%, and she would make up half of the enemies.

> **When** `stage` or `level` has numbers outside [13.1](#131-stages-and-encounter-levels), the entry goes into a pool the game never uses. GNX writes no warning.

> **When** no entry of a pool can be picked (all blocked by `condition` or `max_per_encounter`), the enemy becomes a level-0 Peasant.

> **When** a condition reads a state key not declared in `save_state.fields`, it compares against "no value" and is false. Declare every key used in conditions.

### 13.4 Boss spawn example

A rare, strong Witch, one per encounter, who appears only until she has been captured. `witch_state` is declared in `manifest.json` under `save_state.fields` with the value `0` ([4.3](#43-save_state)).

```json
{
  "name": "Witch",
  "raid_spawns": [
    {
      "stage": 2,
      "level": 2,
      "weight": 15,
      "min_lvl": 5,
      "max_lvl": 5,
      "condition": { "type": "state_equals", "key": "witch_state", "value": 0 },
      "max_per_encounter": 1,
      "ap_override": [150, 150]
    }
  ]
}
```

- She is added to Forest encounter level 2, at unit level 5.
- `condition` keeps her in the pool only while `witch_state` is `0`. Once your mod changes it ([§15](#15-bosses-cage-escape-and-tower)), she stops spawning here.
- `max_per_encounter: 1` prevents two Witches in one fight.
- `ap_override` makes her add 150 enemy HP and 150 AP, instead of `fap_mul × 5` and `bap_mul × 5`.

### 13.5 trade_stage

During raids a trader sells captured units. `trade_stage` (a raid stage, 0–4) adds your class to the offer from that stage on; other values are silently ignored. Without it the class is not sold.

- The trader has one slot per unlocked stage, at most 3.
- Each unlocked stage adds its vanilla trade classes to the pool **once** each, and every modded class with that `trade_stage` **3 times**, so it is three times as likely as a single vanilla class.
- Each slot picks a random pool entry: slot 1 sells a level-0 unit for 100, slot 2 a level-1 unit for 200, slot 3 a level-2 unit for 300. Your class is not guaranteed on every visit.

---

## 14. Pregnancy and birth

**In short:** these class keys set how often a unit can get pregnant, her children's species, the troop type they join and the birth animation. `birth_class`, `birth_classes` and `birth_spr` work only for classes with ID 14 or higher.

```json
{
  "name": "Witch",
  "preg_c_override": 6,
  "birth_class": { "goblin": 2, "hobgoblin": 1, "tentacle": 0, "ogre": 3 },
  "birth_spr": {
    "birth_1": { "goblin": "gnx:witch_birth_1_goblin", "hobgoblin": "gnx:witch_birth_1_hobgoblin" },
    "bind_1": "gnx:witch_bind_1"
  }
}
```

**What this example does:**

- `"preg_c_override": 6`: each Witch can give birth 6 times.
- `birth_class`: goblin children join goblin troop type 2, hobgoblin children type 1, tentacle children type 0, ogre children type 3.
- `birth_spr`: in BIRTH 1 she has her own animation for goblin and hobgoblin children (vanilla for the others), and in BIND 1 always `witch_bind_1`. Other birth cells stay vanilla.

### 14.1 Pregnancy: preg_c_override and preg_mon_type_override

Each unit has a pregnancy counter: the pregnancies she has left. Each birth lowers it by 1, and at 0 she cannot get pregnant any more; `-1` means unlimited and is never lowered. She can get pregnant whenever the counter is not 0, in a cell that allows pregnancy.

| Key | What it means | Type | Default |
|---|---|---|---|
| `preg_c_override` | Starting value of the counter. `-1` = unlimited births. | number | random by unit level: 4–5 at level 0 up to 8–9 at level 4; 4–5 again at levels 5–7 |
| `preg_mon_type_override` | Species of every child, whoever bred her: `0` goblin, `1` hobgoblin, `2` tentacle, `3` ogre | number | species of the first monster in the cell |

Both keys also work on vanilla classes through `override` ([6.2](#62-override-changing-an-existing-class)). With `scr_unit: 1` ([6.3](#63-core-fields)) the counter slowly refills to its starting value.

### 14.2 birth_class: which troop the child joins

Every monster species has four troop types, 0–3: separate groups on the raid screen, each with its own count, level and raid skill. `birth_class` picks the type per species (see the example above).

| Key | What it means | Type | Default |
|---|---|---|---|
| `birth_class.goblin`, `.hobgoblin`, `.tentacle`, `.ogre` | Troop type of children of that species. Rounded down and limited to 0–3; a species left out gets type 0. | number 0–3 | `0` |

What the types do, from the game's skill descriptions:

| Type | Goblin | Hobgoblin | Tentacle | Ogre |
|---|---|---|---|---|
| 0 | more food from raids | more gold from raids | mood rises after winning a raid | more front-formation skill stacks |
| 1 | chance for monsters not to die | higher capture chance | chance of milk after capturing | more back-formation skill stacks |
| 2 | front-formation AP increase | caravan speed increase | captured units may get one more star | more rare-star units spawn |
| 3 | higher item chance | back-formation AP increase | more gold and food from raids | front- and back-formation AP increase |

For comparison, vanilla goblin children of a Peasant are type 0, those of a Knight type 2.

> **When** a class with ID ≥ 14 has **neither** `birth_class` nor `birth_classes`, it produces **no offspring**: the birth animation plays, but no monster is added. Always give a modded class a `birth_class`.

### 14.3 birth_classes (old format)

The older form is a list of four numbers in species order (goblin, hobgoblin, tentacle, ogre):

```json
{ "name": "Witch", "birth_classes": [2, 1, 0, 3] }
```

If both are present, `birth_class` wins. Prefer it: GNX does **not** check or limit `birth_classes`, so the list must hold exactly four numbers from 0 to 3.

### 14.4 birth_spr: birth animations

At a birth the game draws a birth sprite over the cell (the newborn appearing). `birth_spr` replaces it for your class in these vanilla cells (example in [§14](#14-pregnancy-and-birth)); missing keys use the vanilla sprite.

| Key | Cell | Value | Frames per skin (× 3 for a normal class) |
|---|---|---|---|
| `birth_1` | BIRTH 1 (5) | object with `goblin`/`hobgoblin`/`tentacle`/`ogre` sprites | 6 |
| `birth_2` | BIRTH 2 (12) | object like `birth_1` | 6 |
| `bind_1`, `bind_2` | BIND 1 (27), BIND 2 (28) | one sprite for all species | 5 |
| `t_wall_1`, `t_wall_2`, `t_wall_3` | T.WALL 1 (31), T.WALL 2 (32), T.WALL 3 (29) | one sprite | 6 |
| `giant` | GIANT (37) | one sprite | 6 in total, no skin blocks |

How the frames are used:

- One block per skin tone (a special class: one block); its first frames play during labour, the rest at the birth.
- **BIRTH 1** stops on frame 5 of the block until the player clicks the newborn, so its block has 6 frames.
- **BIRTH 2** adds the child the moment frame 5 is reached and never shows that frame, but the block is still 6 frames long, because the game moves to the next skin by 6 frames.
- **BIND 1/2** (5-frame blocks) and **T.WALL 1/2/3** (6-frame blocks) add the child at the end of the block. **GIANT** uses 6 frames without skin blocks.

Values are `gnx:` sprites or vanilla sprite names. `birth_1` and `birth_2` must be objects, the other keys single sprites.

> **When** the cell is not one of these eight vanilla cells, or the class ID is below 14, `birth_spr` has no effect.

---

## 15. Bosses: cage escape and tower

**In short:** two class keys make a class behave like a boss. `post_raid.cage_escape` gives captured units a chance to escape from your cage after each won raid, and `tower_boss_condition` lets the class appear as a Tower boss. Both are usually driven by a state key, so the story can move on.

A full boss setup for the Witch. The state keys in `manifest.json` (relevant part only):

```json
{
  "save_state": {
    "version": 1,
    "fields": { "witch_state": 0, "witch_escapes": 0 }
  }
}
```

The same Witch class entry in `classes.json`: add these keys to the object that already holds the `raid_spawns` of [13.4](#134-boss-spawn-example). A second entry named Witch without `override` would become a separate class.

```json
{
  "name": "Witch",
  "post_raid": {
    "cage_escape": {
      "condition": { "type": "state_equals", "key": "witch_state", "value": 0 },
      "base_chance": 0,
      "over_diff_scale": 300,
      "counter_key": "witch_escapes",
      "popup": "witch_escaped",
      "on_escape_event": "witch_hint",
      "escape_event_threshold": 2,
      "on_survive_state": { "key": "witch_state", "value": 1 },
      "on_survive_event": "witch_captured"
    }
  },
  "tower_boss_condition": { "type": "state_equals", "key": "witch_state", "value": 1 }
}
```

**What this example does:**

- While `witch_state` is `0`, the Witch spawns as a level-5 boss in the Forest ([13.4](#134-boss-spawn-example)), and after every won raid GNX checks each Witch in the cage for an escape.
- If she escapes: she leaves the cage, popup `witch_escaped` shows, `witch_escapes` rises by 1, and from the 2nd escape on the event `witch_hint` fires.
- If she stays, `witch_state` becomes `1` and the event `witch_captured` fires. That stops the raid spawn and the escape check and makes the tower condition true, so from then on she can appear as a Tower boss.
- The popup and events are defined in your `quests.json` (`popups`, `events`, [QUESTS_SCHEMA.md](QUESTS_SCHEMA.md)) and written **without** the folder name; GNX adds `my_mod.` itself.

### 15.1 cage_escape fields

All keys are inside `"post_raid": { "cage_escape": { ... } }`.

| Key | What it means | Type | Default |
|---|---|---|---|
| `condition` | The check runs only while this is true. Quest condition format ([QUESTS_SCHEMA.md](QUESTS_SCHEMA.md)), checked in your mod's state. | object | always |
| `base_chance` | Raises (negative: lowers) the escape chance ([15.2](#152-escape-chance)). | number | `0` |
| `over_diff_scale` | How strongly the player's raid power changes the chance ([15.2](#152-escape-chance)). | number | `300` |
| `counter_key` | State key raised by 1 on every escape | text | none |
| `popup` | Popup from your `quests.json` `popups`, shown on escape. A name that is not found is shown as text (with `my_mod.` in front). | text | none |
| `on_escape_event` | Event fired on every escape once the counter has reached the threshold. **Needs `counter_key` and `escape_event_threshold`.** | text | none |
| `escape_event_threshold` | Counter value from which `on_escape_event` fires | number | none |
| `on_escape_state` | `{ "key": ..., "value": ... }` set when she escapes | object | none |
| `on_survive_state` | `{ "key": ..., "value": ... }` set when she does not escape | object | none |
| `on_survive_event` | Event fired when she does not escape | text | none |

Every check logs a `[GNX-ESCAPE]` or `[GNX-SURVIVE]` line with the power ratio, the roll and the threshold.

### 15.2 Escape chance

GNX compares the player's raid strength with the enemy strength of the stage level just played:

`power ratio = (player raid HP + AP) ÷ (enemy HP + AP)`

Then it rolls two numbers from 1 to 100, **R1** and **R2**. She escapes if:

`R1 ≤ base_chance + R2 − over_diff_scale + over_diff_scale × (power ratio − 1)`

With the defaults (`base_chance` 0, `over_diff_scale` 300) the chance is 50% when the player is exactly twice as strong as the enemies, and it changes quickly around that point:

| Power ratio | 1.0 | 1.5 | 1.7 | 1.8 | 1.9 | 2.0 | 2.1 | 2.2 | 2.3 or more |
|---|---|---|---|---|---|---|---|---|---|
| Defaults (0 / 300) | 0% | 0% | 0.6% | 8% | 25% | 50% | 76% | 92% | ~100% |
| `over_diff_scale: 100` | 0% | 13% | 25% | 32% | 40% | 50% | 60% | 68% | 75% |
| `base_chance: 20` | 0% | 0% | 5% | 18% | 41% | 68% | 88% | 98% | 100% |

- A lower `over_diff_scale` flattens the curve; at `0` the power ratio does not matter at all.
- `base_chance` shifts it: with `over_diff_scale: 0`, `0` gives about 50%, `50` about 88%, `100` always (handy for testing).

### 15.3 tower_boss_condition

```json
{ "name": "Witch", "tower_boss_condition": { "type": "state_equals", "key": "witch_state", "value": 1 } }
```

While this condition (quest format, checked in your mod's state) is true, the class is in the Tower's boss pool. Without it the class is never a Tower boss.

- Each of the 5 enemies of a Tower fight has a 5% chance (plus a skill bonus) to be a level-6 boss, picked at random from the pool; the same boss can appear twice.
- The vanilla pool holds Hathor (9), Lilith (8), Bastet (13), Morrigan (12), Nyx (10) and Selene (11), each once unlocked. Your class joins with the same chance as each.
- This works in both Tower pools (encounter level 0 and 1). Before Lilith has been beaten, Tower level 0 is a fixed fight against Lilith alone, with no other bosses.

> **When** the escape check runs, it covers **every** unit of the class in the cage after **every** won raid, while `condition` is true, not just the last one captured. An escaped unit is gone for good, and `on_survive_state`/`on_survive_event` repeat until the condition becomes false (as in the example). The condition is checked separately for each unit, so a state change by one unit applies to the next: once the first Witch survives and sets `witch_state` to 1, the others in the cage no longer pass the check.

> **When** an event or popup name is written with the folder prefix (`"my_mod.witch_hint"`), GNX adds it again and looks for `my_mod.my_mod.witch_hint`, so nothing happens. Only the mod's own popups and events can be used here.

> **When** the defaults are kept, escape is impossible while the player is less than about 1.7 times as strong as the enemies. Raise `base_chance` or lower `over_diff_scale` for escapes in close fights.

---

## 16. Special classes and monster sprite overrides

**In short:** three advanced class features. `is_special` turns a class into a "special" class like Lilith or Nyx (one skin tone, full-body sprite tables). `gb1_breast_d2` is an extra breast sprite for one G.BANG cell. `mon_spr_overrides` replaces the **monster** sprites that some vanilla cells draw for your class.

```json
{
  "name": "Queen",
  "is_special": true,
  "has_hair": false,
  "gb1_breast_d2": "gnx:q_gb_breast_d2",
  "clothing_standard": {
    "max_row": 4,
    "phase_1": {
      "spr_array": [-1, "gnx:q_idle_head", "gnx:q_idle_breast", "gnx:q_hand", "gnx:q_idle_leg", "gnx:q_idle_legp", -1],
      "spr_c_array": [-1, -1, "gnx:q_idle_breast_c", "gnx:q_hand_c", "gnx:q_idle_leg_c", "gnx:q_idle_legp_c", -1]
    },
    "phase_2": {
      "spr_array": [-1, "gnx:q_loop_head", "gnx:q_loop_breast", "gnx:q_hand", "gnx:q_loop_leg", "gnx:q_loop_legp", -1],
      "spr_c_array": [-1, -1, "gnx:q_loop_breast_c", "gnx:q_hand_c", "gnx:q_loop_leg_c", "gnx:q_loop_legp_c", -1]
    }
  },
  "mon_spr_overrides": { "patrol": "gnx:q_ogre_patrol", "goblin_giant_body_alpha": "gnx:q_gob_giant_alpha", "goblin_giant_body_line": "gnx:q_gob_giant_line" }
}
```

**What this example does:**

- `"is_special": true`: one skin tone and full-body tables ([7.7](#77-special-class-tables-spr_array-and-spr_c_array)).
- `"max_row": 4`: her standard tables are used only in the first four standard cells (WALL 1, WALL 2, T.FRAME 1, MILK 1) ([16.2](#162-clothing_standardmax_row)).
- `gb1_breast_d2`: her breast sprite in G.BANG 2 when a second monster joins ([16.3](#163-gb1_breast_d2)).
- `mon_spr_overrides`: another ogre walking sprite when it carries her (`patrol`), and her own goblin body and outline in the GIANT loop.

### 16.1 What is_special changes

| Area | Normal class | Special class |
|---|---|---|
| Skin tones | 3 (random per unit) | 1 |
| Body | shared base body + your clothes | your full body (`spr_array`) + clothes (`spr_c_array`) |
| Clothing format | leg-based maps (`start/idle/loop` in big cells) | tables per phase; big cells use `phase_0/1/2` |
| `naked_*`, `hand_color` | used | not used (the hand is slot `[3]`) |
| Frame counts | standard idle 90, loop 225; tent idle 42, loop 105, birth 42; hand 6 | a third: standard 30 / 75; tent 14 / 35 / 14; hand 2 |
| `clothing_standard.max_row` | ignored | available ([16.2](#162-clothing_standardmax_row)) |
| Ogre carry | head + base + hair sprites | `carry_head` is the whole body (8 frames); without it nothing is drawn |
| LILITH SHRINE | vanilla monster touch/enter overlays drawn | goblin/hobgoblin touch and enter and the ogre enter are **not** drawn without overrides |
| Spawn buttons in tools ([§17](#17-tools-toolsjson)) | unit level up to 4 (or 6) | unit level 5 (or 6/7 if asked for) |
| GIANT without the needed `clothing_giant` phase | uses `clothing_standard` | no new sprites for that phase |

Big-cell frame counts follow the vanilla big-cell sprites ([5.6](#56-frame-counts)). `is_special` does **not** change drop pools, spawn limits or raid strength.

### 16.2 clothing_standard.max_row

A standard strip holds one block ("row") per standard cell, in `h_type` order. `max_row` lets a special class supply only the first rows: from row `max_row` on (that row included), GNX skips the class's tables. In vanilla cells the row is `h_type − 1`:

| Row | Cell | Row | Cell | Row | Cell |
|---|---|---|---|---|---|
| 0 | WALL 1 | 5 | BJ 1 | 10 | DRINK |
| 1 | WALL 2 | 6 | WALL 3 | 11 | BIRTH 2 |
| 2 | T.FRAME 1 | 7 | WALL 4 | 12 | PRONE 1 |
| 3 | MILK 1 | 8 | M.PRESS 1 | 13 | RIDE |
| 4 | BIRTH 1 | 9 | DISPLAY | 14 | FOREPLAY |

So `"max_row": 4` covers rows 0–3; BIRTH 1 and every later cell are skipped.

Skipped cells use the game's own code: for an override of a vanilla special class (8–13) they keep the vanilla sprites, but a **modded** class has none there, so keep it out (for example with `only_listed_cells`).

> **When** the cell is a custom cell, the row is its `character_row` ([§9](#9-the-physical-block-how-a-cell-behaves)), default 0, so it is skipped only when `character_row` is `max_row` or higher.

### 16.3 gb1_breast_d2

| Key | What it means | Type | Default |
|---|---|---|---|
| `gb1_breast_d2` | Breast sprite in the cell the game calls **G.BANG 2** (`h_type` 18) while its second monster position is occupied, drawn with the normal breast layer's frame number. | sprite | the class's normal breast sprite |

The "gb1" comes from the game's internal `gb_1` sprites of G.BANG 2. In vanilla, Hathor, Bastet, Morrigan, Nyx and Lilith have their own version. The key works for any class, and also replaces Lilith's (class 8) through an override.

### 16.4 mon_spr_overrides: how it works

Some vanilla cells pick monster sprites by captive class, for example a different goblin pose for Hathor. `mon_spr_overrides` lets your class do the same: an object of `"key": sprite` pairs, with `gnx:` sprites or vanilla sprite names.

- **Only classes with ID ≥ 14**; vanilla classes ignore it, even through `override`.
- **Only the vanilla cells listed below.** In your own cells use the cell's `mon_spr` ([§10](#10-cell-sprites-human_spr-and-mon_spr)).
- **`-1` is dropped.** Keys with `-1` (or a sprite that cannot be found) are removed when the class loads, so the vanilla sprite is drawn. To hide a sprite, use a fully transparent one.
- **Give `_alpha` and `_line` keys as a pair.** Monsters are a fill (`alpha`, drawn with the player's monster-transparency setting) plus an outline (`line`). With only the alpha, GNX looks for the outline by name (`..._alpha` → `..._line`), which never works for mod sprites, so the monster has no outline. For the giant head and the G.BANG 2 extra goblin, a missing line keeps the **vanilla** outline over your fill. The dairy `_line` keys are read only with their `_alpha` key.
- **Match the vanilla frame layout**: each override uses the frame numbers of the vanilla sprite it replaces.

In key names, `pen` is the penis layer, `touch` the monster's hands on the captive, `enter` the penetration overlay; `hand` and `head` are separately drawn monster parts.

### 16.5 Override keys that work

In the tables, "body" means body fill (`_alpha`) and outline (`_line`); "loop" includes the ejaculation.

**LILITH SHRINE (`h_type` 39)**, a fixed-mode Lilith cell; patch its `required_class` to use it with your class ([§12](#12-patching-vanilla-cells-and-classes)).

| Key | Monster | Replaces |
|---|---|---|
| `goblin_shrine_start_body_alpha` / `goblin_shrine_start_body_line` | goblin | body, start |
| `goblin_shrine_start_hand_alpha` / `goblin_shrine_start_hand_line` | goblin | hand, start |
| `goblin_shrine_start_pen` | goblin | pen, start |
| `goblin_shrine_body_alpha` / `goblin_shrine_body_line` | goblin | body, loop |
| `goblin_shrine_touch`, `goblin_shrine_enter` | goblin | touch, enter, loop |
| `hobgoblin_shrine_start_body_alpha` / `hobgoblin_shrine_start_body_line` | hobgoblin | body, start |
| `hobgoblin_shrine_start_hand_alpha` / `hobgoblin_shrine_start_hand_line` | hobgoblin | hand, start |
| `hobgoblin_shrine_start_pen` | hobgoblin | pen, start |
| `hobgoblin_shrine_body_alpha` / `hobgoblin_shrine_body_line` | hobgoblin | body, loop |
| `hobgoblin_shrine_touch`, `hobgoblin_shrine_enter` | hobgoblin | touch, enter, loop |
| `ogre_shrine_start_alpha` / `ogre_shrine_start_line` | ogre | body, start |
| `ogre_shrine_start_pen` | ogre | pen, start |
| `ogre_shrine_loop_alpha` / `ogre_shrine_loop_line` | ogre | body, loop |
| `ogre_shrine_loop_enter` | ogre | enter, loop |
| `shrine_bg`, `shrine_dirt`, `shrine_sign` | cell | background (layer type 0), dirt (12), sign above the cell (1) |

Two more keys exist only for this cell:

- `shrine_loop_hand`: the class's loop hands, drawn in the breast layer (type 6) **under** the breast sprite while a monster is in the cell and the loop runs. Vanilla does this only for Lilith; without the key a modded class's arms vanish during the loop.
- `shrine_loop_hand_c` (optional): used instead while that layer shows its clothed variant; otherwise `shrine_loop_hand` is used.

```json
{
  "name": "Witch",
  "mon_spr_overrides": { "shrine_loop_hand": "gnx:shrine_loop_hand", "shrine_loop_hand_c": "gnx:shrine_loop_hand_c" }
}
```

Declare both in the class's `sprites` as full-canvas strips with the canvas size, frame count and origin of the breast strip the class uses in the shrine loop.

**GIANT (`h_type` 37)**

| Key | Monster | Replaces |
|---|---|---|
| `goblin_giant_start_body_alpha` / `goblin_giant_start_body_line` | goblin | body, start |
| `goblin_giant_start_pen` | goblin | pen, start |
| `goblin_giant_body_alpha` / `goblin_giant_body_line` | goblin | body, loop |
| `goblin_giant_pen`, `goblin_giant_touch`, `goblin_giant_enter` | goblin | pen, touch, enter, loop |
| `goblin_giant_head_alpha` / `goblin_giant_head_line` | goblin | head that the GIANT cell draws itself, later in the act |
| `hobgoblin_giant_start_body_alpha` / `hobgoblin_giant_start_body_line` | hobgoblin | body, start |
| `hobgoblin_giant_start_pen` | hobgoblin | pen, start |
| `hobgoblin_giant_body_alpha` / `hobgoblin_giant_body_line` | hobgoblin | body, loop |
| `hobgoblin_giant_pen`, `hobgoblin_giant_touch`, `hobgoblin_giant_enter` | hobgoblin | pen, touch, enter, loop |
| `hobgoblin_giant_head_alpha` / `hobgoblin_giant_head_line` | hobgoblin | head drawn by the cell |
| `ogre_giant_start_alpha` / `ogre_giant_start_line` | ogre | body, start |
| `ogre_giant_start_pen` | ogre | pen, start |
| `ogre_giant_loop_alpha` / `ogre_giant_loop_line` | ogre | body, loop |
| `ogre_giant_loop_pen`, `ogre_giant_loop_touch` | ogre | pen, touch, loop |
| `giant_cloth` | cell | cloth overlay drawn over the captive (vanilla only for Selene) |

**DAIRY (`h_type` 36)**, a fixed-mode Hathor cell; patch it to use it with your class.

| Key | Monster | Replaces |
|---|---|---|
| `goblin_dairy_body_alpha` / `goblin_dairy_body_line` | goblin | body |
| `goblin_dairy_touch` | goblin | touch |
| `hobgoblin_dairy_body_alpha` / `hobgoblin_dairy_body_line` | hobgoblin | body |
| `hobgoblin_dairy_touch` | hobgoblin | touch |
| `dairy_blink` | cell | eye-blink sprite (1 frame); vanilla has one only for Hathor, so other classes do not blink without it |

**DRINK (`h_type` 11)**

| Key | Monster | Replaces |
|---|---|---|
| `goblin_drink_touch` | goblin | touch |
| `goblin_drink_draw` | goblin | the drinking goblin the cell draws on the breast layer |

**G.BANG 2 (`h_type` 18; the keys say "gb1")**

| Key | Monster | Replaces |
|---|---|---|
| `ogre_touch` | goblin | touch overlay; despite the name, used while goblins are in the cell |
| `goblin_gb1_draw_body_b` / `goblin_gb1_draw_body_l` | goblin | body fill / outline of the extra goblin drawn while the second position is occupied |

**CHAINS (`h_type` 38)**, a fixed-mode Morrigan cell; patch it to use it with your class.

| Key | Monster | Replaces |
|---|---|---|
| `ogre_chain_body` | ogre | body, once per occupied position (one frame row per position) |
| `ogre_chain_extra` | ogre | extra layer while the second position is occupied |

**Ogre carry (DISPLAY_B, `h_type` 24):** `patrol` replaces the ogre's walking sprite while it carries a unit of this class ([6.5](#65-ogre-carry-sprites)).

### 16.6 Override keys that GNX reads but does not apply

GNX gives every vanilla cell a built-in monster sprite table for modded classes, with the game's default sprites. The keys below are checked only when that table has not picked a monster body, which in vanilla cells never happens, so **they have no visible effect**:

| Cell | Keys |
|---|---|
| G.BANG 2 (18) | `goblin_gb1_body`, `hobgoblin_gb1_body` |
| G.BANG 1 (19) | `goblin_gb2_body`, `goblin_gb2_enter` |
| G.BANG 3 (23) | `goblin_gb3_hand`, `goblin_gb3_enter`, `hobgoblin_gb3_hand`, `hobgoblin_gb3_enter` |
| Standard cells, goblin | `goblin_wall_touch_start`, `goblin_wall_touch_loop`, `goblin_wall_enter_loop`, `goblin_wall_touch_ej`, `goblin_wall_enter_ej` |
| WALL 1–4 in anal mode, goblin | `goblin_wall_touch_anal_start`, `goblin_wall_touch_anal_loop`, `goblin_wall_enter_anal_loop`, `goblin_wall_touch_anal_ej`, `goblin_wall_enter_anal_ej` |
| Standard cells, hobgoblin | `hobgoblin_wall_body_start`, `hobgoblin_wall_hand_start`, `hobgoblin_wall_touch_loop`, `hobgoblin_wall_enter_loop`, `hobgoblin_wall_touch_ej`, `hobgoblin_wall_enter_ej`, `hobgoblin_wall_touch_anal_loop`, `hobgoblin_wall_enter_anal_loop` |
| Cells without their own ogre sprites | `ogre_wall_body_start`, `ogre_wall_body_loop` |

To change monster sprites there, patch the cell's `mon_spr`, `mon_spr_hob` or `mon_spr_ogr` ([§12](#12-patching-vanilla-cells-and-classes), format in [§10](#10-cell-sprites-human_spr-and-mon_spr)). That affects **every** modded class in the cell.

> **When** G.BANG keys are chosen, mind the numbers: `gb1` keys belong to `h_type` 18, shown as **G.BANG 2**; `gb2` keys to `h_type` 19, shown as **G.BANG 1**.

> **When** a key is misspelled, or its `gnx:` sprite is missing from `sprites`, the override is silently ignored and the vanilla sprite is drawn. Check the sprite load lines in `gnx_debug.txt`.

> **When** DAIRY, CHAINS or LILITH SHRINE get overrides, they matter only if the class can enter: in vanilla these cells accept only Hathor, Morrigan and Lilith, so patch `required_class` first ([§12](#12-patching-vanilla-cells-and-classes)).

---

## 17. Tools (tools.json)

**In short:** `tools.json` adds buttons to the in-game **TOOLS** menu and keyboard shortcuts (keybinds). Each button or key runs a list of *actions*, such as "add 1000 gold" or "unlock a cell": cheat menus, debug helpers and test shortcuts without any GML code. The file is loaded only when `manifest.json` has `"tools": "tools.json"` ([4.4](#44-data-file-keys)).

```json
{
  "categories": [
    {
      "label": "WITCH TOOLS",
      "buttons": [
        {
          "label": "+1000 GOLD",
          "actions": [
            { "type": "add_gold", "amount": 1000 }
          ],
          "popup": "Added 1000 gold"
        }
      ]
    }
  ]
}
```

`categories` are the entries of the TOOLS menu, here one, `WITCH TOOLS`. `label` is the text the player sees, `buttons` the clickable buttons inside the category, and `actions` what a button does, in order: here `add_gold` with `amount` 1000. `popup` is a short message box shown after all actions.

### 17.1 Opening the tool menu

In the options window, click the button next to **DEBUG** to open the **TOOLS** menu. GNX always adds it, even when no mod has a `tools.json`. It lists:

1. the top-level categories of every mod's `tools.json`, in mod load order ([§3](#3-mod-folder-and-loading));
2. **SPAWN** and 3. **GNX DEBUG**, which GNX builds itself ([§17.3](#173-built-in-menus-spawn-and-gnx-debug)).

Every list shows at most 10 entries per page in two columns, with arrow buttons and a page number (such as `1/2`) when there are more. **BACK** goes one level up.

> **When** two mods use the same category label, two identical entries appear: GNX merges all categories into one list without mod names. Use labels that show the mod (`WITCH TOOLS`, not `CHEATS`).

### 17.2 Structure of tools.json

The file is one object with two optional lists: `categories` (top-level TOOLS entries) and `keybinds` ([§17.8](#178-keybinds)). Each category is an object:

| Key | What it means | Type | Default |
|---|---|---|---|
| `label` | Text of the entry. | text | required |
| `buttons` | Buttons shown when the category is opened. | list | none |
| `categories` | Sub-menus with the same keys, nested as deep as you like. | list | none |

```json
{
  "categories": [
    {
      "label": "WITCH SPAWNS",
      "categories": [
        {
          "label": "GOBLINS",
          "buttons": [
            {
              "label": "WARRIOR",
              "actions": [
                { "type": "spawn_mon", "species": 0, "class": 0, "amount": 1 }
              ]
            },
            {
              "label": "RANGER",
              "actions": [
                { "type": "spawn_mon", "species": 0, "class": 1, "amount": 1 }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

The TOOLS menu shows `WITCH SPAWNS`; it opens a sub-menu `GOBLINS` with two buttons that add one goblin (`species` 0) Warrior (`class` 0) or Ranger (`class` 1). BACK returns one level at a time.

> **When** a category has both `categories` and `buttons`, only the sub-categories show. A category with neither shows only BACK.

> **When** a category or button has no `label`, the game hits a GameMaker error ("... not set before reading it").

### 17.3 Built-in menus: SPAWN and GNX DEBUG

GNX builds both after all mods have loaded.

**SPAWN** has three sub-menus:

- **MONSTERS**: one entry per species (Goblin, Hobgoblin, Tentacle, Ogre), each with `Warrior x1`, `Ranger x1`, `Mage x1` and `Shaman x1`.
- **UNITS**: a `VANILLA` group with classes 0–13, then one group per mod (folder name in capitals) with its classes. Each button creates one captive in the prison.
- **CELLS**: a `VANILLA` group with the vanilla cells of the build menus, then one group per mod with **every** cell it registered. Each button unlocks that cell in the build menu, with a popup such as `ALTAR unlocked!`.

A button list whose buttons include one starting with `create_unit` (also in your own categories) gets a **RANK** selector on the left: `1`–`5` (stars), `MAX`, `CLONE`, `SPECIAL` (internally 0–7). `create_unit` uses it when it has no `level` ([§17.6](#176-action-reference)).

**GNX DEBUG** holds eight test switches; their ON/OFF state is never saved.

| Button | What it turns on (its ON popup) |
|---|---|
| PERF LOG | `Perf logging ON (gnx_debug.txt)`: a performance line every 120 frames (about 2 seconds). |
| VERBOSE | `Verbose debug logging ON`: many extra trace lines; use it when a cell or class draws wrong. |
| CAPT100 | `Raid capture rate forced to 100%` |
| TRACE | `Entity lifecycle tracing ON (gnx_debug.txt)` |
| OVERLAY | `GameMaker debug overlay ON (FPS, memory, textures)` |
| PERF HUD | `GNX perf HUD ON (FPS, sprites, VRAM)` |
| RUN ALL | `Off-screen cells now RUN (step culling OFF)` |
| ECON | `Economy probe ON - report every game day in gnx_debug.txt` |

All except OVERLAY also log `[GNX-TOOL] set_var <key> = <value>` when clicked, a quick check that the tool menu reacts at all.

### 17.4 Buttons

```json
{
  "label": "REFILL MOOD",
  "actions": [
    { "type": "set_val", "key": "mood", "value": 100 }
  ],
  "popup": "Mood refilled"
}
```

This button sets the game value `mood` to 100 and shows `Mood refilled`.

| Key | What it means | Type | Default |
|---|---|---|---|
| `label` | Text on the button. | text | required |
| `actions` | Actions run on click, in order ([§17.6](#176-action-reference)). | list | empty list |
| `popup` | Message shown after the actions. | text | none |
| `toggle` | Makes it an ON/OFF button; names the save-state key that stores ON or OFF ([§17.5](#175-toggle-buttons)). | text | none |
| `undo_actions` | Actions run when a toggle is switched OFF. | list | empty list |
| `undo_popup` | Message shown when a toggle is switched OFF. | text | none |
| `guard` | One condition that must be true before anything runs ([§17.7](#177-guards)). | object | none |
| `guard_fail_popup` | Message shown when the guard is false. | text | none |

Every popup text (`popup`, `undo_popup`, `guard_fail_popup`, keybind popups and the `popup` action) can also be a popup key from your `quests.json`, written in full with your folder name (`"my_mod.witch_hint"`). Any other text is shown as written.

### 17.5 Toggle buttons

A button with `toggle` switches between ON and OFF, and GNX adds ` [ON]` or ` [OFF]` to its label.

```json
{
  "label": "LOCK MOOD",
  "toggle": "mood_locked",
  "actions": [
    { "type": "set_continuous", "key": "mood_lock", "value": true }
  ],
  "undo_actions": [
    { "type": "set_continuous", "key": "mood_lock", "value": false }
  ],
  "popup": "Mood locked at 100",
  "undo_popup": "Mood unlocked"
}
```

- The save-state key `mood_locked` stores 1 (ON) or 0 (OFF).
- While it is 0 (or not set), a click runs `actions`, sets it to 1 and shows `popup`; here that starts the "mood lock" effect ([§17.9](#179-continuous-effects)).
- With any other value, a click runs `undo_actions`, sets it to 0 and shows `undo_popup`.
- The label shows `[ON]` only when the key is exactly 1.

Declare the key in the manifest's `save_state.fields` ([§4](#4-manifestjson)), for example `"fields": { "mood_locked": 0 }`.

> **When** a toggle key is not declared, it still works, but the boot test reports `[GNX-TEST] FAIL  T39 missing toggle keys: ...`.

> **When** a save is loaded after a restart, a toggle can show ON while its effect is not running: the toggle state is saved, continuous effects are not ([§17.9](#179-continuous-effects)). Click it twice (OFF, then ON) to restart the effect.

### 17.6 Action reference

An action is an object with a `type` and the fields it needs. GNX knows **39** action types.

- Fields marked *required* have no default; a missing one can cause a GameMaker error ("... not set before reading it") or make the action fail. Numbers must be JSON numbers (`1000`, not `"1000"`).
- A **class or cell reference** (`class_id` of `create_unit` and `create_unit_cage`, `h_type` of `give_blueprint` and `unlock_cell`) can be a number or text: `"my_mod.Witch"`, `"my_mod.ALTAR"`, or a bare name such as `"Witch"` for your own mod. An unknown reference shows `Unknown class (...). Contact modder.` (or `Unknown cell`) and logs `[GNX-WARN] tool class ref '...' not found (mod=my_mod)` (or `tool cell ref`).
- An unknown `type` does nothing and logs `[GNX-TOOL] unknown action type: <type>`. `"type": "gml"` also does nothing and fails the boot test (`[GNX-TEST] FAIL  T37 invalid tool actions: ...`).

**Resources (7)**

| Type | Fields | What it does |
|---|---|---|
| `add_gold` | `amount` (required) | Adds gold; negative values subtract. Never below 0. |
| `add_food` | `amount` (required) | Adds food. Never below 0. |
| `add_milk` | `rarity` (default -1), `amount` (default 1) | Adds milk of rarity 0–4; `-1` adds `amount` of every rarity. |
| `add_orbs` | `amount` (required) | Adds orbs (the vanilla orb counter). Never below 0. |
| `give_item` | `item_type`, `data`, `level` (all required) | Creates one inventory item from the game's internal item data. Advanced; the actions below are easier. |
| `give_blueprint` | `h_type` (cell reference, required), `fragment` (default false), `lvl` (default 1) | Gives a complete blueprint, or with `"fragment": true` a fragment of level `lvl` (a complete blueprint is level 3). |
| `give_prop` | `prop_id` (required) | Unlocks a prop in the edit-mode menu with the vanilla popup. `prop_id` is the prop's **number** ([§19.5](#195-prop-ids)). Same as `unlock_prop`. |

**Monsters (5)**

`species`: 0 goblin, 1 hobgoblin, 2 tentacle, 3 ogre. `class`: 0 Warrior, 1 Ranger, 2 Mage, 3 Shaman.

| Type | Fields | What it does |
|---|---|---|
| `spawn_mon` | `species`, `amount` (required), `class` (optional) | Adds `amount` monsters to that class, or without `class` to **each** of the four. A `species` outside 0–3 does nothing. |
| `set_troop_level` | `species`, `class`, `value` (all required) | Sets the level of that monster class. |
| `add_troop_exp` | `species`, `class`, `amount` (all required) | Adds experience through the normal level-up logic. |
| `set_skill_level` | `species`, `class`, `value` (all required) | Sets the skill level of that monster class. |
| `set_troop_size` | `value` (required, 0–7) | Sets the maximum troop size: 0 = 10, 1 = 25, 2 = 50, 3 = 90, 4 = 150, 5 = 220, 6 = 320, 7 = unlimited. Clamped to 0–7. |

**Captives (2)**

| Type | Fields | What it does |
|---|---|---|
| `create_unit` | `class_id` (class reference, required), `level` (optional) | Puts a new captive in the first free prison slot and shows `<Name> added!`, or `Prison is full!`. Without `level` (or with 0 or less) it uses the RANK selector ([§17.3](#173-built-in-menus-spawn-and-gnx-debug)). A normal class keeps 0–4 or 6 (CLONE), 5 and 7 become 4; a special class keeps 6 or 7, anything else becomes 5 (MAX). |
| `create_unit_cage` | `class_id` (class reference, required), `level` (default 1) | Adds a **new** cage slot holding a new captive (it does not fill an empty slot), so the cage grows each time. No popup, no capacity check. |

**Unlocks (7)**

| Type | Fields | What it does |
|---|---|---|
| `unlock_boss` | `index` (required, 0–4) | Starts the vanilla intro event of a still-locked boss: 0 cow, 1 Nyx, 2 goddess, 3 Morrigan, 4 Lilith. |
| `unlock_stage_next` | `stage` (required, 0–3) | Discovers raid stage 0 Village, 1 Mountain, 2 Forest or 3 Castle (with the vanilla event for 1–3), or, if already discovered, raises its highest level by one. |
| `unlock_breeds` | none | Unlocks all breeding tips. |
| `unlock_cell` | `h_type` (cell reference, required) | Adds the cell to its build menu tab and shows `<NAME> unlocked!`; a cell without a build category shows `Cell has no build category. Contact modder.` |
| `unlock_prop` | `prop_id` (required) | Same as `give_prop`. |
| `unlock_raid` | none | Enables the raid button. |
| `unlock_all_cells` | none | Unlocks every cell in the small, big, tentacle and XL build lists. |

> **When** `unlock_cell`, `give_prop` or `unlock_prop` runs again, it adds a second entry: nothing checks whether it is already unlocked. Protect one-time buttons with a guard and a state key ([§17.10](#1710-full-example)).

**World and time (3):** `add_floor` (no fields) adds a cave floor; `set_day` (`value`, required) sets the day counter, at least 1; `add_day_time` (`amount`, required) adds to the day timer.

**Speed and display (3)**

| Type | Fields | What it does |
|---|---|---|
| `set_speed` | `target` (text), `value` (number), both required | `"world"`: game speed 0–10 (0 pauses); `"cart"`: raid cart speed 0–10; `"range"`: extra cell range 0–20. Clamped; any other `target` does nothing. |
| `swap_mouse` | none | Swaps the mouse buttons for moving the camera and selecting. |
| `show_debug_overlay` | `enable` (default true) | Shows or hides GameMaker's debug overlay. |

**Value setters (2):** `set_val` and `set_var`, each with `key` (text) and `value`, both required, set one game value or global setting. Only the keys below work; any other does nothing and logs `[GNX-TOOL] unknown set_val key: <key>` (or `set_var`).

| `set_val` key | Meaning | Allowed range |
|---|---|---|
| `mood` | Mood | 0–100 |
| `food`, `money`, `orb_num`, `day_timer` | Food, gold, orbs, time of the current day | 0 or more |
| `day` | Day counter | 1 or more |
| `cart_spd` | Raid cart speed | 0–10 |
| `add_range` | Extra cell range | 0–20 |
| `sfx_vol`, `bgm_vol` | Sound effect and music volume | 0–1 |
| `alpha_type`, `crate_alpha_type` | Monster (MON TYPE) and prop (PROP TYPE) transparency mode | 0–2 |
| `mon_alpha`, `crate_alpha` | Monster and prop opacity | 0–1 |
| `show_head`, `ui_place` | Vanilla head-display and UI placement options | not clamped |

| `set_var` key | Meaning |
|---|---|
| `w_spd` | Game speed, clamped to 0–10 |
| `gnx_perf_enabled`, `gnx_debug_verbose`, `gnx_force_capture_100`, `gnx_trace_entities`, `gnx_perf_hud`, `gnx_cull_step_off`, `gnx_econ_on` | The GNX DEBUG switches ([§17.3](#173-built-in-menus-spawn-and-gnx-debug)): `0` = off, any other number = on. |

**Raid screen (3):** `reroll_shop`, `reroll_trade` and `reroll_encounters` (no fields) re-roll the raid shop stock, the trade stock, or the encounters of the open stage. They work only while the raid screen is open, whichever page (map, shop or trade) shows.

**State and messages (6)**

| Type | Fields | What it does |
|---|---|---|
| `set_state` | `key` (text), `value`, both required | Sets a key in your mod's save state ([§4](#4-manifestjson)). |
| `set_continuous` | `key` (text), `value` (true/false), both required | Starts or stops a continuous effect ([§17.9](#179-continuous-effects)). The field is `value`, not `enable`. |
| `fire_event` | `event_id` (text or number, required) | Text: fires a quest event, written with your folder name (`"my_mod.witch_intro"`; GNX adds no prefix here); an unknown ID does nothing. Number: fires that vanilla game event. |
| `fire_trigger` | `hook` (text, required) | Runs the quest triggers of that hook now, from **all** mods. Hooks: [QUESTS_SCHEMA.md](QUESTS_SCHEMA.md). |
| `popup` | `text` (required) | Shows a popup; can be a popup key (`"my_mod.<key>"`). |
| `play_sfx` | `sfx_type` (number, required; not `type`) | Plays a vanilla sound: 0 click, 1 failed click, 2 random click, 3 mail, 4 building, 5 coins, 6 get coin, 7 upgrade, 14 demolish, 16 raid, 21 save, 23 shop, 24 trade. |

**Travel (1):** `travel_map` (`target`, required; `label`, default `target`) opens the travel selector for the map `target` ([§21](#21-multi-map-travel)). It is refused, with a message, while a raid is out, a window is open or the player holds something.

### 17.7 Guards

A guard is one condition object checked before a button does anything. If it is false, GNX shows `guard_fail_popup` (if set) and stops.

```json
{
  "label": "UNLOCK COW BOSS",
  "actions": [
    { "type": "unlock_boss", "index": 0 }
  ],
  "guard": { "type": "boss_locked", "index": 0 },
  "guard_fail_popup": "Already unlocked"
}
```

The button runs `unlock_boss` only while boss 0 is locked; afterwards a click shows `Already unlocked`.

| Guard `type` | Fields | True when |
|---|---|---|
| `boss_locked`, `boss_unlocked` | `index` | That boss is still locked / is unlocked (numbers as in `unlock_boss`). |
| `stage_undiscovered` | `stage` | That raid stage is not discovered yet. |
| `has_unit_slot` | none | The prison has a free slot. |
| `on_screen` | (`screen` is ignored) | The raid screen is open, whatever `screen` says. |
| any quest condition | see [QUESTS_SCHEMA.md](QUESTS_SCHEMA.md) | For example `state_equals`, `state_gte`, `gold_gte`, `floor_gte`; state keys come from your own mod. |

> **When** a guard has an unknown type (for example `has_cage_space`, which does not exist), it is false and **always fails**.

> **When** a toggle is switched OFF, its guard is checked too: a false guard keeps the toggle ON.

> **When** a guard uses a text reference (`"my_mod.ALTAR"`), it never matches, because guards do not translate references. `cell_built`, `boss_captured` and similar need numeric IDs here.

### 17.8 Keybinds

A keybind runs actions when the player presses a key; GNX checks them every frame.

```json
{
  "keybinds": [
    {
      "key": "F9",
      "modifier": "ctrl",
      "actions": [
        { "type": "add_food", "amount": 100 }
      ],
      "popup": "+100 food"
    },
    {
      "key": "0-9",
      "modifier": "alt",
      "action_per_key": { "type": "set_speed", "target": "world", "value": 0 },
      "popup_template": "World speed = {key}"
    }
  ]
}
```

- **Ctrl+F9** adds 100 food and shows `+100 food`.
- The second keybind covers the ten number keys with **Alt** held. `action_per_key` is one action (an object, not a list). On Alt+7, GNX copies it and replaces `value` with 7, so the game speed becomes 7; the `0` in the file is only a placeholder. `popup_template` then shows `World speed = 7`.

| Key | What it means | Type | Default |
|---|---|---|---|
| `key` | `"F1"`–`"F12"`, `"A"`–`"Z"` (capitals only), `"0"`–`"9"` (number row, not numpad), `"space"`, `"tab"`, `"escape"`, or the range `"0-9"` (the only range form). | text | required |
| `modifier` | `"none"`: only with Shift, Ctrl and Alt all released. `"shift"`, `"ctrl"`, `"alt"`: that key must be held (others are not checked). Any other value: no check. | text | `"none"` |
| `actions` | Actions for a single key. | list | empty list |
| `action_per_key` | One action for `"0-9"`; its `value` field is replaced with the pressed digit. | object | none |
| `popup` | Message after a single key, or for a range without `popup_template`. | text | none |
| `popup_template` | Message for `"0-9"`; the first `{key}` becomes the digit. Ignored for single keys. | text | none |

Keybinds are blocked while the game locks input (for example during screen transitions), but **not** while a dialog textbox is open.

> **When** `{key}` is written in an action field other than `value`, it stays literal text: only `value` receives the digit.

> **When** a key name is unknown (for example lowercase `"f9"` or `"a"`), the keybind never fires, and the boot test shows `[GNX-TEST] FAIL  T38 invalid keybinds: my_mod(no_vk_code)`.

### 17.9 Continuous effects

A continuous effect runs every frame while active; `set_continuous` starts and stops it. GNX has exactly one: `mood_lock`, which sets mood to 100 every frame. Each mod has its own list of active effects. They are **not saved**: the list is empty at every game start. An unknown effect key is accepted but does nothing.

### 17.10 Full example

With `witch_state` and `mood_locked` declared in the manifest's `save_state.fields` (both `0`), `tools.json`:

```json
{
  "categories": [
    {
      "label": "WITCH TOOLS",
      "buttons": [
        {
          "label": "ADD WITCH",
          "actions": [
            { "type": "create_unit", "class_id": "my_mod.Witch" }
          ],
          "guard": { "type": "has_unit_slot" },
          "guard_fail_popup": "No free prison slot"
        },
        {
          "label": "UNLOCK ALTAR",
          "actions": [
            { "type": "unlock_cell", "h_type": "my_mod.ALTAR" },
            { "type": "set_state", "key": "witch_state", "value": 1 }
          ],
          "guard": { "type": "state_equals", "key": "witch_state", "value": 0 },
          "guard_fail_popup": "ALTAR is already unlocked"
        },
        {
          "label": "LOCK MOOD",
          "toggle": "mood_locked",
          "actions": [
            { "type": "set_continuous", "key": "mood_lock", "value": true }
          ],
          "undo_actions": [
            { "type": "set_continuous", "key": "mood_lock", "value": false }
          ],
          "popup": "Mood locked at 100",
          "undo_popup": "Mood unlocked"
        }
      ]
    }
  ],
  "keybinds": [
    {
      "key": "0-9",
      "modifier": "alt",
      "action_per_key": { "type": "set_speed", "target": "world", "value": 0 },
      "popup_template": "World speed = {key}"
    }
  ]
}
```

- `ADD WITCH` creates a Witch captive unless the prison is full (guard `has_unit_slot`). Because of this `create_unit` button, the category gets the RANK selector, which sets her rank.
- `UNLOCK ALTAR` unlocks the ALTAR and sets `witch_state` to 1; its guard lets it run only while `witch_state` is 0, so the cell is unlocked once.
- `LOCK MOOD` toggles the `mood_lock` effect, and Alt+0 … Alt+9 set the game speed (Alt+0 pauses).

---

## 18. Sounds (sounds.json)

**In short:** `sounds.json` adds moan voices for captives, extra sex-scene sound effects and optional ambience voices for goblins, hobgoblins and ogres. The audio files (OGG Vorbis only) go into the `sounds/` folder, and GNX adds a sound settings page to the options window.

```
my_mod/
  manifest.json      "sounds": "sounds.json"
  sounds.json
  sounds/
    soft_1.ogg
    soft_2.ogg
    orgasm_1.ogg
```

Minimal `sounds.json`:

```json
{
  "voice_banks": {
    "soft": {
      "clips": ["soft_1.ogg", "soft_2.ogg"]
    }
  },
  "sfx": {
    "orgasm": ["orgasm_1.ogg"]
  }
}
```

`voice_banks` defines one bank of moan clips, `soft`; each captive gets one bank as her voice ([§18.3](#183-which-voice-a-captive-gets)). `clips` are file names **inside** `sounds/` (`"soft_1.ogg"`, not `"sounds/soft_1.ogg"`). `sfx` adds a clip to the shared `orgasm` pool ([§18.4](#184-sfx-pools-and-when-sounds-play)).

| Key | What it means | Type | Default |
|---|---|---|---|
| `voice_banks` | Named moan banks: `{ "<bank name>": { "clips": [ ... ] } }`. | object | none |
| `sfx` | File lists for the five effect pools `orgasm`, `bj_slurp`, `bj_gag`, `bj_moan`, `bj_breathe`. | object | none |
| `voice_map` | Fixed voice per class ID ([§18.3](#183-which-voice-a-captive-gets)). | object | none |
| `settings_defaults` | Starting values of the sound sliders ([§18.6](#186-the-sound-settings-page-and-settings_defaults)). | object | built-in values |
| `ambience` | Monster ambience voices ([§18.7](#187-ambience-monster-voices)). | object | none |

### 18.1 Audio files

GNX loads each clip as an audio stream when the mod loads, which works only with **OGG Vorbis** (`.ogg`). Other formats such as `.wav` fail: the log shows `[GNX-SOUND] loaded <file> idx=-1` and the clip is skipped. Convert first, for example with `ffmpeg -i in.wav -c:a libvorbis -q:a 5 out.ogg`. A missing file logs `[GNX-SOUND] file not found: <path>`.

> **When** no clip of a voice bank loads, the bank is not created at all, as `[GNX-SOUND] bank 'my_mod.soft' clips=0` shows.

### 18.2 voice_banks

A voice bank is a named list of moan clips. GNX adds your folder name to the bank name, so `soft` in `my_mod` becomes `my_mod.soft`, and two mods can both have a `soft` bank. When a captive with that voice moans, a random clip of her bank plays.

A bank can also have its own climax clips:

```json
{
  "voice_banks": {
    "soft": { "clips": ["soft_1.ogg"], "orgasm": ["soft_climax_1.ogg"] }
  }
}
```

When a captive with this bank climaxes in a normal cell, one of its `orgasm` clips plays; a bank without `orgasm` uses the shared `sfx.orgasm` pool ([18.4](#184-sfx-pools-and-when-sounds-play)). `clips` is still required.

### 18.3 Which voice a captive gets

GNX picks a voice (a bank plus a pitch) once per captive and stores it on her; it picks again only if she has none. The order:

1. `voice_map` in a `sounds.json`, by class ID;
2. the class's `voice` in `classes.json`;
3. otherwise a random bank from all loaded mods.

Captives of level 6 or 7 (CLONE and SPECIAL in the RANK selector) always get a random bank. The pitch (1.0 = unchanged) comes from the same place as the bank, otherwise it is random between 0.9 and 1.15.

**`voice_map`** gives a class a fixed voice without changing the class, useful for vanilla characters:

```json
{
  "voice_map": {
    "8": { "bank": "soft", "pitch": 0.91 },
    "13": { "bank": "loud", "pitch": 1.1 }
  }
}
```

Class 8 always gets `my_mod.soft` at pitch 0.91, class 13 `my_mod.loud` at 1.1.

Each key is a class ID as text (read as a number, so a mod class's numeric ID works too); `bank` (required) is a bank of **this** `sounds.json` without the folder prefix, and `pitch` is optional.

**`voice` in classes.json** does the same from the class side: `"voice": { "bank": "soft", "pitch": 1.0 }` gives every Witch `my_mod.soft` at pitch 1.0, unless `voice_map` has an entry for her class ID.

> **When** `voice_map` or a class `voice` names a bank, GNX always adds **its own** mod's folder name, so only banks from the same mod's `sounds.json` can be used.

> **When** two mods put the same class ID in `voice_map`, the later-loading mod wins.

> **When** `voice_map` changes later, captives that already have a voice keep it.

**Voice by monster type.** A captive can sound different depending on the monster in her cell, with `by_mon_type` in a class's `voice` or a `voice_map` entry:

```json
{
  "voice": {
    "bank": "soft",
    "pitch": 1.0,
    "by_mon_type": {
      "hobgoblin": "rough",
      "ogre": { "bank": "deep", "pitch": 0.9 }
    }
  }
}
```

With a hobgoblin she uses `my_mod.rough` at her own pitch, with an ogre `my_mod.deep` at 0.9, with goblins or tentacles her normal `soft` voice.

- Keys: `goblin`, `hobgoblin`, `tentacle`, `ogre`; a value is a bank name or `{ "bank": …, "pitch": … }`, with your folder prefix added.
- It is checked on every moan. The first monster in the cell decides, and tentacle cells count as `tentacle`. An unlisted type or an unloaded bank uses her normal voice.
- A `voice_map` entry may have only `by_mon_type`: the class keeps its normal voice except for the listed types.
- Climaxes use the chosen bank's `orgasm` clips if it has some. Nothing is stored in saves.

### 18.4 sfx pools and when sounds play

The `sfx` pools are shared: every sound mod adds its clips to the same five pools.

```json
{
  "sfx": {
    "orgasm": ["orgasm_1.ogg", "orgasm_2.ogg"],
    "bj_slurp": ["slurp_1.ogg"],
    "bj_gag": ["gag_1.ogg"],
    "bj_moan": ["bj_moan_1.ogg"],
    "bj_breathe": ["breathe_1.ogg"]
  }
}
```

When each sound plays (a "thrust" is the moment the vanilla slap sound plays):

| Moment | Normal cell | Oral cell ([§18.5](#185-oral-cells-sfx_type)) |
|---|---|---|
| Each thrust | With a chance of MOAN FRQ %, a random clip of the captive's voice bank, at MOAN VOL. | With a chance of MOAN FRQ % (at most 10 %), a `bj_moan` clip at MOAN VOL; otherwise a random `bj_slurp` or `bj_gag` clip at BJ VOL. |
| Ejaculation | With a chance of ORGASM FRQ %, an `orgasm` clip at MOAN VOL, pitch = voice pitch + 0.05. | With a chance of ORGASM FRQ %, a `bj_breathe` clip at MOAN VOL, pitch kept within 0.95–1.05. |

While any mod has voice or sfx clips loaded, the vanilla slap sounds use PLAP VOL and the vanilla ejaculation sound EJ VOL instead of the normal SFX volume.

> **When** no voice bank is loaded anywhere, captives have no voice and no thrust sounds play (moans and all `bj_*` thrust sounds), even if `sfx` clips are loaded.

### 18.5 Oral cells (sfx_type)

GNX uses the `bj_*` pools on oral cells: vanilla cell 6, vanilla cell 18 while its third monster slot is in use, and any cell whose `cells.json` entry (new cell or patch) has `"sfx_type": "bj"`. Adding that key to the ALTAR entry of [8.1](#81-minimal-example-the-altar-cell) makes it use the oral rules of [§18.4](#184-sfx-pools-and-when-sounds-play).

### 18.6 The sound settings page and settings_defaults

When any mod loads voice banks, `sfx` clips or ambience clips, the options window gets a button for a sound page:

| Control | Shown when | Range |
|---|---|---|
| MOAN VOL, PLAP VOL, EJ VOL, BJ VOL | voice or sfx clips are loaded | 0–500 % (steps of 10 %) |
| MOAN FRQ, ORGASM FRQ | voice or sfx clips are loaded | 0–100 % (steps of 1; wraps around) |
| GOB VOL | ambience clips are loaded | 0–200 % |
| AMB GOB | ambience clips are loaded | OFF and the allowed ambience modes ([§18.7](#187-ambience-monster-voices)) |

The values are stored in the save file. `settings_defaults` sets the starting slider values:

```json
{
  "settings_defaults": { "moan_vol": 0.5, "moan_frq": 15, "orgasm_frq": 5, "plap_vol": 0.5, "ej_vol": 0.5, "bj_vol": 0.5 }
}
```

| Key | What it means | Type | Default |
|---|---|---|---|
| `moan_vol`, `plap_vol`, `ej_vol`, `bj_vol` | MOAN VOL, PLAP VOL, EJ VOL, BJ VOL; 1.0 is shown as 100 %. | number (0–5) | 0.5 |
| `moan_frq` | MOAN FRQ in percent. | number (0–100) | 15 |
| `orgasm_frq` | ORGASM FRQ in percent. | number (0–100) | 5 |

Only the first mod in load order that brings voice or sfx clips sets these values; without `settings_defaults` there, and in a save without stored values, the table defaults apply.

> **When** `settings_defaults` is written, give all six keys: GNX sets only the keys listed.

> **When** a mod has only `ambience` clips, its `settings_defaults` is never applied.

### 18.7 Ambience: monster voices

The `ambience` block adds short voice lines that goblins, hobgoblins and ogres say while on screen, plus one line at the end of a raid. Tentacles have no ambience.

```json
{
  "ambience": {
    "variants": ["balanced", "individual"],
    "species": {
      "goblin": {
        "ambient": ["gob_idle_1.ogg", "gob_idle_2.ogg"],
        "breeding": ["gob_breed_1.ogg"],
        "victory": ["gob_win_1.ogg"],
        "defeat": ["gob_lose_1.ogg"]
      },
      "ogre": {
        "ambient": ["ogre_idle_1.ogg"]
      }
    }
  }
}
```

The player may choose `balanced` or `individual`; goblins get all four clip lists, ogres only `ambient`, hobgoblins stay silent.

| Key | What it means | Type | Default |
|---|---|---|---|
| `variants` | Allowed modes: any of `"balanced"`, `"three_lane"`, `"individual"`; other names are ignored. The modes of all mods are combined. | list | all three |
| `species` | Object with the keys `goblin`, `hobgoblin`, `ogre`. | object | none |
| `ambient` | Normal lines of that species. | list | none |
| `breeding` | Second pool: each time a monster speaks, it is picked with a 45 % chance (if it has clips), otherwise `ambient`. Whether the monster is actually breeding is not checked. | list | none |
| `victory`, `defeat` | Line played once when a raid is won / lost. | list | none |

The clip pools are shared by all mods, like the `sfx` pools. The player picks the mode with **AMB GOB** on the sound page; it starts **OFF**, so nothing plays until it is turned on.

| Mode (label) | Behaviour |
|---|---|
| `balanced` (BAL) | One random on-screen monster per species speaks: goblins every 3–7 s, hobgoblins every 4.5–9 s, ogres every 6.5–12 s. |
| `three_lane` (3-LN) | Three independent voices, each every 3–7 s, each picking a random on-screen monster. |
| `individual` (IND) | Every on-screen monster speaks on its own every 3–6 s. |

- Only monsters on screen (with an 80-pixel margin) whose species has `ambient` or `breeding` clips speak. Nothing plays while the game is paused (speed 0) or the camera is locked (for example during a dialog box).
- Volume is the SFX volume × GOB VOL, also changed by the camera zoom. Pitch varies a little per species (goblin 0.98–1.05, hobgoblin 0.98–1.03, ogre 0.97–1.02).
- At the end of a raid one `victory` or `defeat` clip plays (only with AMB GOB not OFF). The species is picked at random, weighted by the goblins, hobgoblins and ogres in the raid party; only species with clips in that pool count.

### 18.8 Full example

```json
{
  "voice_banks": {
    "soft": {
      "clips": ["soft_1.ogg", "soft_2.ogg"]
    },
    "loud": {
      "clips": ["loud_1.ogg"]
    }
  },
  "voice_map": {
    "13": { "bank": "loud", "pitch": 1.1 }
  },
  "sfx": {
    "orgasm": ["orgasm_1.ogg"],
    "bj_slurp": ["slurp_1.ogg"],
    "bj_moan": ["bj_moan_1.ogg"]
  },
  "settings_defaults": { "moan_vol": 0.6, "moan_frq": 20, "orgasm_frq": 5, "plap_vol": 0.5, "ej_vol": 0.5, "bj_vol": 0.5 },
  "ambience": {
    "variants": ["balanced"],
    "species": {
      "goblin": {
        "ambient": ["gob_idle_1.ogg"]
      }
    }
  }
}
```

Class 13 always gets `my_mod.loud` at pitch 1.1, others their class `voice` or a random bank. `bj_gag` and `bj_breathe` stay empty unless another mod fills them. As the first sound mod in load order, it starts moans a bit louder and more often, and goblins on screen say `gob_idle_1.ogg` once AMB GOB is set to BAL.

---

## 19. Props (props.json)

**In short:** `props.json` adds decorations (props) such as candles, banners or barrels to the edit-mode prop menu. Each prop has a sprite, a menu group (top, middle or bottom) and a few placement options. The file is loaded when `manifest.json` has `"props": "props.json"`.

```json
{
  "props": [
    { "id": "iron_candle", "display_name_key": "Iron Candle", "position": "top", "sprite": "gnx:iron_candle", "x_random_range": 4, "xscale_random": true }
  ],
  "sprites": {
    "iron_candle": { "strip": "strips/prop_iron_candle.png", "frames": 1, "xorig": 8, "yorig": 16 }
  }
}
```

**What this example does:**

- `props` is the list of props, here one. Its `id` becomes `my_mod.iron_candle`, which GNX turns into a number ([§19.5](#195-prop-ids)).
- `display_name_key` is the button text in edit mode; `position` puts the prop in the **top** menu group with the top default height.
- `sprite` points to the entry `iron_candle` of the `sprites` block, which loads the PNG as a one-frame sprite with its [origin](#2-glossary) at 8, 16 (example values for a 16×16 image).
- Each placed candle is shifted sideways by a random −4 to +4 pixels (`x_random_range`) and mirrored at random (`xscale_random`).

### 19.1 File layout

`props.json` is an object `{ "props": [...], "sprites": {...} }` or just the list of props, which then has no custom sprites. Other top-level keys (such as `schema_version`) are ignored. Errors go to `gnx_debug.txt`, for example `[GNX] ERROR: Mod 'my_mod': props file 'props.json' not found` or `[GNX] ERROR: Mod 'my_mod': props must be an array or { props: [...] }`.

### 19.2 Prop fields

| Key | What it means | Type | Default |
|---|---|---|---|
| `id` | Prop name in your mod; the prop number is made from `<folder>.<id>`. | text | required |
| `display_name_key` | Button text in edit mode, shown as written in every language. | text | the `id` |
| `code_text` | Stored, but nothing draws it for props. | text | `"?"` |
| `position` | Menu group and default height: `"top"`, `"mid"` or `"bot"`. Other text works like `"bot"`, but the boot test reports `bad_pos`. | text | `"bot"` |
| `sprite` | `"gnx:<key>"` or `"<key>"` from the `sprites` block. Without a usable sprite, frame 0 of vanilla `spr_between_prop` is drawn. | text | none |
| `price` | Price stored on the prop's unlock item (an orange print, for example from a quest `prop` reward), **not** a cost for placing it. | number | -1 |
| `y_offset` | Vertical shift in pixels from the prop spot; negative moves up. | number | top -30, mid -10, bot 0 |
| `x_random_range` | Random sideways shift per placed prop, −range to +range pixels. | number | 0 |
| `xscale_random` | `true` = each placed prop is mirrored at random. | true/false | false |
| `locked` | `true` = not in the menu at the start until unlocked ([§19.6](#196-locked-props)). | true/false | false |

### 19.3 Sprites block

Same format as in `classes.json` and `cells.json` ([§5](#5-sprites)), with atlas support ([§20](#20-atlas-packing)). Props do not animate: only frame 0 is drawn.

### 19.4 Menu placement and drawing

| `position` | Edit-mode menu group | Default `y_offset` | Drawn |
|---|---|---|---|
| `"top"` | top group | -30 | behind bottom props |
| `"mid"` | middle group | -10 | behind bottom props |
| `"bot"` | bottom group | 0 | in front of top and middle props |

With the mouse over a cell, its props get the same yellow highlight as vanilla props.

### 19.5 Prop IDs

The game saves props as numbers. GNX makes the number as a [hash](#2-glossary) of `<folder>.<id>`, from 100 to 9999; if two props collide, the later one moves to the next free number, so in that rare case it depends on load order.

`give_prop`, `unlock_prop` ([§17.6](#176-action-reference)) and the quest `prop` reward ([QUESTS_SCHEMA.md](QUESTS_SCHEMA.md)) need this number, not the text ID. It is in `gnx_debug.txt`:

```
[GNX] prop 'my_mod.iron_candle' -> id=2734 pos=top
```

> **When** the mod folder or a prop's `id` is renamed, or the mod is removed, the number changes or disappears, and placed props with the old number are deleted when the save loads (GNX deletes props with unknown numbers of 100 or higher).

### 19.6 Locked props

A prop with `"locked": true` is not in the edit-mode menu at the start; a tool action or quest reward with its number unlocks it.

```json
{
  "props": [
    { "id": "witch_banner", "display_name_key": "Witch Banner", "position": "mid", "sprite": "gnx:witch_banner", "locked": true }
  ],
  "sprites": {
    "witch_banner": { "strip": "strips/prop_witch_banner.png", "frames": 1, "xorig": 8, "yorig": 0 }
  }
}
```

A matching tool button, if the log line for the banner reads `id=3012`:

```json
{
  "label": "UNLOCK BANNER",
  "actions": [
    { "type": "unlock_prop", "prop_id": 3012 }
  ]
}
```

Clicking it adds the banner to the middle menu group with the vanilla unlock popup; the unlock is stored in the save.

> **When** `give_prop` or `unlock_prop` runs on an already unlocked prop, it adds it again. Use them only once per locked prop (with a guard and a state key).

### 19.7 Testing

The boot test checks every prop: `[GNX-TEST] PASS  T59 prop_registry valid`, or `[GNX-TEST] FAIL  T59 prop_registry invalid: ...` with the prop number and the problem (`bad_spr`, `no_name`, `bad_pos`, `not_in_order`).

---

## 20. Atlas packing

**In short:** an atlas is a few large PNG images (*pages*) that hold all sprite frames of a mod, plus `atlas/uv.json`, which says where each frame sits. GNX then loads one texture per page instead of one per [strip](#2-glossary), so booting is faster and uses fewer textures. It is optional: a mod works the same without `atlas/`.

Minimal `atlas/uv.json`:

```json
{
  "atlas_files": ["atlas_0.png"],
  "entries": {
    "spr_unit_icon_witch_head": {
      "frames": [
        { "atlas": 0, "x": 0, "y": 0, "w": 21, "h": 26 },
        { "atlas": 0, "x": 23, "y": 0, "w": 21, "h": 26 },
        { "atlas": 0, "x": 46, "y": 0, "w": 21, "h": 26 }
      ],
      "xo": 10,
      "yo": 13
    }
  }
}
```

and the matching sprite entry in `classes.json`:

```json
{
  "icon_head": { "strip": "strips/spr_unit_icon_witch_head.png", "frames": 3, "xorig": 10, "yorig": 13 }
}
```

- `atlas_files` lists the page images inside `atlas/`, here one.
- `entries` has one entry per strip, named after the strip's file name without folder and `.png`.
- `frames` gives each frame's place: `atlas` is the page number (0 = first file), `x`/`y` the top-left corner, `w`/`h` the size. `xo`/`yo` are the [origin](#2-glossary).
- The `classes.json` entry finds `spr_unit_icon_witch_head` by name and draws its three frames from `atlas_0.png`; the strip PNG itself is not loaded.

### 20.1 Folder structure

```
my_mod/
  manifest.json
  classes.json
  strips/          original strips (keep them; the packer reads them)
  atlas/           written by the packer
    atlas_0.png
    atlas_1.png
    uv.json
```

### 20.2 Running the packer

The packer is a separate Python tool: `python gnx_atlas_pack.py <mod_folder_path>`, with Python 3 and Pillow (a standalone `.exe` is in `tools/gnx_atlas_pack/`). It reads `strips/`, `classes.json` and `cells.json` for frame counts and origins, packs the frames into pages of up to 4096×4096 and writes `<mod>/atlas/`. Extra keys in its `uv.json` (`atlas_version`, `atlas_size`, `padding`) are not read by GNX.

Measured on one two-mod setup (results depend on the mods and the computer):

| Metric | Without atlas | With atlas |
|---|---|---|
| Texture pages | 373 | 7 |
| Estimated VRAM | ~576 MB | ~320 MB |
| Boot time | 94 s | 1.8 s |

### 20.3 uv.json format

| Key | What it means | Type | Default |
|---|---|---|---|
| `atlas_files` | Page file names inside `atlas/`, in order. | list | required |
| `entries` | One object per strip, named after the strip's file name without folder and extension. | object | required |
| `frames` | Per frame: `atlas` (page number), `x`, `y`, `w`, `h` (pixel rectangle). A frame with `w` or `h` 0 is empty and skipped. | list | required |
| `xo`, `yo` | Origin of the sprite. | number | 0 |

### 20.4 How GNX uses the atlas

1. At the start of your mod's loading, before classes, cells and props, GNX loads `atlas/uv.json` and every page, if the file exists.
2. For each sprite in a `sprites` block, GNX takes the file name of its `strip` (or `path`, or the first file of a `frames` list) without folder and extension, and looks for that entry in **your own** `uv.json`, ignoring case (`strips/spr_h_Witch_x.png` finds `spr_h_witch_x`). A `"folder"` sprite is looked up by the folder name.
3. Found: the sprite comes from the atlas and the PNG is not loaded. Not found: the PNG loads normally. Both can be mixed.
4. The frame count comes from `uv.json`, not from `frames`; with fewer frames there, the animation repeats them.
5. The origin is `xo`/`yo` from `uv.json`, unless your entry sets `origin_from` or a non-zero `xorig`/`yorig`: then that wins for this sprite only.

Atlas sprites work everywhere strips do: birth sprites, `carry_base_spr`, naked layers, class icons and the infant in BIRTH cells. `from_game` sprites, quest portraits and the multi-map `map_sprite` never use the atlas.

Useful log lines:

- `[GNX-PERF] mod "my_mod" atlas mode: 1 texture pages, 120 sprite refs`: the atlas was loaded.
- `[GNX-ATLAS] ERROR: malformed uv.json for my_mod`: invalid JSON; the mod loads its strips normally.
- `[GNX-ATLAS] ERROR: my_mod: failed to load atlas_3.png`: one page is missing; its sprites are not drawn, the other pages work.

### 20.5 Known limits

> **When** the packer trims transparent borders, the frames jump around: every frame is drawn at the entry's `xo`/`yo`, with no per-frame offset. Frames must be **untrimmed**.

> **When** a sprite uses a `frames` **list of files**, treat it as not using the atlas: GNX looks up only the first file's name, and a matching entry would replace the whole list.

> **When** two strips in different folders have the same file name, they share one atlas entry, because only the file name is looked up.

> **When** a strip is added or changed, re-run the packer: GNX draws what is in the pages, not in `strips/`. This includes `folder` sprites.

---

## 21. Multi-map travel

**In short:** a mod can add its own map: a second nest with its own floors, cells, prison and raids. The player travels between the village and the mod maps.

```json
{
  "name": "Outpost",
  "version": "1.0.0",
  "compatible_game_versions": ["1.40"],
  "map": "outpost",
  "map_info": {
    "label": "Outpost",
    "map_sprite": "outpost_map.png",
    "return_label": "Village",
    "travel": "advanced",
    "travel_cost": { "gold": 50, "food": 10, "days": 1 },
    "unlock": { "type": "stage_cleared", "stage": 1, "min_level": 2 }
  },
  "map_start": {
    "floors": 1,
    "money": 400,
    "food": 60,
    "goblins": 5,
    "troops": [{ "type": "hobgoblin", "kind": 0, "num": 2 }],
    "cells": [
      { "h_type": 1, "slot_type": 0, "floor": 1 }
    ]
  }
}
```

**What this example does:**

- `"map": "outpost"`: everything else the mod adds (classes, cells, quests, tools, sounds, props, raid encounters) loads only on its own map `outpost`.
- `map_info`: the travel menu entry, available once Mountain (stage 1) is cleared at `min_level` 2. Each trip to or from the Outpost costs 50 gold and 10 food and takes a day.
- `map_start`: the first visit starts with one extra floor, 400 gold, 60 food, 5 goblins, 2 hobgoblins and a WALL 1 cell on floor 1.

> **When** a mod must also work for players still on GNX 1.4.8: `map_info` is new in 1.4.9; before, it was called `map_button`. GNX 1.4.9 still reads `map_button`, so a mod written with `map_button` works in both versions, but `travel_cost`, the new `map_start` keys and cell names in `map_start` work only in 1.4.9. A mod with both `map_info` and `map_button` gets `map_info` and a warning in the `Mod loading problem(s)` box.

### 21.1 map

Not set or `"vanilla"`: the mod belongs to the village map. `"all"`: it loads on every map. Any other text: it belongs to that map and loads only there; the map ID is usually your folder name. A mod can also add content to **another** mod's map by using the same `map` value without `map_info` and `map_start`.

**A list of maps** loads the mod on each map it names, and only there (new in 1.4.9). Example: a class that should appear both in the village and on your Outpost, but not on other mods' maps:

```json
{ "map": ["vanilla", "outpost"] }
```

- The mod keeps one folder name, so its classes and cells get the same hash IDs on every listed map (unless another mod on one of the maps already took that number, [3.4](#34-duplicate-ids)), and a captive carried between them stays the same class.
- `map_info` and `map_start` describe the one mod map in the list (`"outpost"` here). A list naming two or more mod maps can still carry content for all of them, but its `map_info` and `map_start` are ignored and reported in the `Mod loading problem(s)` box.

> **When** `map` is an empty list `[]`, the mod would load nowhere: GNX reports it and treats the mod as a village mod.

### 21.2 map_info

| Key | What it means | Type | Default |
|---|---|---|---|
| `label` | The map's name in the travel menu and on the load page. | text | the `map` ID |
| `map_sprite` | PNG in your mod's `sprites/` folder (133 × 91), drawn as the raid panel's world map while on this map. | text | none |
| `return_label` | The village's name in the travel menu while on this map. | text | `"Return"` |
| `travel` | What may be taken along to or from this map: `"simple"` (gold, food, basic goblins), `"advanced"` (also a TROOPS tab with every monster type, one section per type, amounts set with the game's number pad) or `"complex"` (also a CAPTIVES tab: prisoners are dragged into the destination's free prison places). A trip between two maps uses the higher setting. | text | `"simple"` |
| `travel_cost` | What a trip to or from this map costs: `{ "gold": …, "food": …, "days": … }`, each optional ([21.4](#214-how-travel-works)). A trip between two maps uses the higher value of each. | object | free |
| `unlock` | A condition, or a list that must all hold, in quest condition format ([QUESTS_SCHEMA.md](QUESTS_SCHEMA.md)). Until then the map is hidden from the world map and the travel menu; the first time it holds, the map unlocks for good on every map with `New map: <label> (travel from the world map)`. `state_*` conditions read this mod's own state. | object or list | always available |
| `x`, `y`, `return_x`, `return_y` | Not used. | number | — |

**Travel cost.** The cost is paid from the map the player leaves, on departure. The selector shows it in its title (`Trip: 50 gold, 10 food, 1 day`), and the gold and food it needs cannot be taken along. While the trip cannot be paid, the selector's red warning line says `! Not enough for the trip (…)` and TRAVEL does nothing. `days` pass on arrival.

### 21.3 map_start

`map_start` is applied once, on the first visit; later visits find the map as the player left it.

| Key | What it means | Type | Default |
|---|---|---|---|
| `floors` | Extra floors below the entrance floor (floor 0): `2` gives floors 0, 1 and 2. | number | `0` |
| `money`, `food`, `mood` | Starting values, set only when given. | number | — |
| `goblins` | Basic goblins at the start; `0` for none. | number | `5` |
| `troops` | Other monsters: `[{ "type": "hobgoblin", "kind": 0, "num": 4 }]`. `type` is `goblin`, `hobgoblin`, `tentacle` or `ogre` (or 0–3); `kind` 0–3 picks the variant. | list | none |
| `prisoners` | Captives in the prison: `[{ "class": 3, "level": 2, "num": 2 }]`. `class` is a class ID or reference (`"my_mod.Witch"`); `level` 0–4 for normal classes (special classes get 5). A new map's prison has 5 places; extra prisoners are skipped. | list | none |
| `cells` | Cells built at the start: `{ "h_type": …, "slot_type": …, "floor": … }` each. `h_type` is a number or a cell reference (`"my_mod.MY CELL"`, or `"MY CELL"` for your own cells). `slot_type` and `floor` default to 0; a floor that does not exist is skipped. | list | none |
| `unlock_cells` | Cells unlocked in the build menu from the start: `[2, "my_mod.MY CELL"]`, also cells with `"locked": true`. | list | none |

> **When** `unlock_cells` names a vanilla cell, the village gets it too once the player has been to this map, because unlocks are shared ([21.4](#214-how-travel-works)). A map mod's own cells stay on its map.

`python tools/build_mod.py <mod_dir> <game_dir>` checks `map_info` and `map_start` before deploying (unknown condition types, unknown monster types, cells on floors that do not exist, a missing `map_sprite` file) and deploys the map image from `sprites/`.

### 21.4 How travel works

- **Where:** the round button in the top-left corner of the raid panel's world map opens the travel menu with every other reachable map, village included (the in-game guide has a TRAVEL page). A selector then shows what to take along (see `travel`) and the trip's cost.
- **Travel is refused** while a raid is out (`Can't travel while a raid is out.`), a window is open or the player holds something.
- **The inventory is shared** by all maps: items (milk, blueprints and their torn pieces, bells, orbs) travel with the player on every trip and join the destination's inventory, so blueprint pieces found on different maps complete each other.
- **Unlocks are shared** by all maps and merged on arrival. Boss progress, raid stages and encounters stay with each map.
- **A map the player is not on is frozen:** no births, income or day timer while away. The day counter itself is shared, so time never goes backwards.
- **Saves** store every visited map. If the current map's mod is no longer installed, the player goes back to the village with a short notice; the map stays in the save and returns when the mod is reinstalled.
- **Several map mods:** each map gets its own travel entry. If two mods declare `map_info` or `map_start` for the same map, the first in load order owns it and the other is reported in the `Mod loading problem(s)` box; its content still loads on that map.
- **Tool action** `travel_map` with `"target": "<map ID>"` opens the selector for that map ([§17](#17-tools-toolsjson)).
- **Quests** can follow the player between maps (new in 1.4.9): the trigger hook `map_arrive` runs once after every trip, the conditions `on_map`, `map_visited` and `map_unlocked` tell where the player is and has been, and the side effect `unlock_map` opens a map from a quest. A mod's save state is kept per map, so a storyline that spans maps reads `map_visited` / `map_unlocked` instead of state keys. Details: [QUESTS_SCHEMA.md](QUESTS_SCHEMA.md).
- **Limits:** one map per mod. A map's nest uses the vanilla backgrounds and walls; only the raid panel's world map can be replaced (`map_sprite`).

---

## Appendix A. Vanilla IDs and cell list

**In short:** the ID numbers of the unmodded game's classes, monster types, raid stages and cells, for numeric IDs, vanilla patches and `character_row`.

### A.1 Class IDs

| class_id | In-game name | Registry name | Special (boss) |
|---|---|---|---|
| 0 | PEASANT | peasant | no |
| 1 | CLERIC | cleric | no |
| 2 | KNIGHT | knight | no |
| 3 | RANGER | ranger | no |
| 4 | NUN | nun | no |
| 5 | SAMURAI | samurai | no |
| 6 | SHAMAN | mage | no |
| 7 | WARRIOR | warrior | no |
| 8 | LILITH | lilith | yes |
| 9 | HATHOR | cow | yes |
| 10 | NYX | nyx | yes |
| 11 | SELENE | giant | yes |
| 12 | MORRIGAN | morrigan | yes |
| 13 | BASTET | cat | yes |

- Mod classes get IDs from 14 to 9999 ([3.4](#34-duplicate-ids)).
- The registry name is GNX's internal name, used by some keys (`cow` for Hathor, `cat` for Bastet). Class 11 is `giant` internally but is the boss SELENE; the GIANT *cell* is h_type 37.
- SHAMAN and WARRIOR always use the kneeling `leg_0` body.

### A.2 Monster types (mon_type)

`0` goblin, `1` hobgoblin, `2` tentacle, `3` ogre; JSON keys use the same names (`goblin`, `hobgoblin`, `tentacle`, `ogre`).

### A.3 Raid stages

`0` Village, `1` Mountain, `2` Forest, `3` Castle, `4` Tower (the boss tower: encounter level 0 is the first tower floor, level 1 the endless tower; [§13](#13-raid-spawns-and-the-trade-shop), [§15](#15-bosses-cage-escape-and-tower)).

### A.4 Vanilla cells

- **h_type**: the cell's ID; 0, 16, 26 and 35 are not cells.
- **In-game name** is the English build-button name; **Registry name** is the `name` GNX stores (seen in some log lines). They differ for several cells.
- **Build tab**: the cell's `category`, which decides its size: `breed`/`utility`/`pleasure` small, `b_…` big, `t_…` tentacle. No vanilla cell is `xl_breed` (XL was added by GNX 1.4.6).
- **slot_type**: registry number (0 small, 1 big, 3 tentacle). It does not set the size and does not always match it (see GIANT or the OGRE cells); in a mod cell it only affects the default `base_body` ([10.1](#101-human_spr-the-three-modes)).
- **Body**: the cell's `human_spr`: `standard` / `big` / `tent` = class sprites on that `base_body`, `fixed` = the cell's own human sprites, `—` = the game's own code draws the cell.
- **Strip row**: the row the cell uses in a class's body strips ([5.5](#55-how-frames-are-arranged-in-a-strip)).

| h_type | In-game name | Registry name | Build tab | slot_type | Body | Strip row | Notes |
|---|---|---|---|---|---|---|---|
| 1 | WALL 1 | WALL 1 | breed | 0 | standard | 0 | |
| 2 | WALL 2 | WALL 2 | breed | 0 | standard | 1 | |
| 3 | TITFUCK | T.FRAME 1 | pleasure | 0 | standard | 2 | |
| 4 | MILK 1 | MILK 1 | utility | 0 | standard | 3 | |
| 5 | BIRTH 1 | BIRTH 1 | utility | 0 | standard | 4 | |
| 6 | ORAL | BJ 1 | pleasure | 0 | standard | 5 | |
| 7 | WALL 3 | WALL 3 | breed | 0 | standard | 6 | |
| 8 | WALL 4 | WALL 4 | breed | 0 | standard | 7 | |
| 9 | M.PRESS 1 | M.PRESS 1 | breed | 0 | standard | 8 | |
| 10 | DISPLAY | DISPLAY | utility | 0 | standard | 9 | |
| 11 | DRINK | DRINK | utility | 0 | standard | 10 | |
| 12 | BIRTH 2 | BIRTH 2 | utility | 0 | standard | 11 | |
| 13 | PRONE | PRONE | breed | 0 | standard | 12 | |
| 14 | RIDE 1 | RIDE | breed | 0 | standard | 13 | |
| 15 | FOREPLAY | FOREPLAY | pleasure | 0 | standard | 14 | |
| 17 | TRANSFER | CAGE | b_utility | 1 | big | 0 | |
| 18 | G.BANG 2 | G.BANG 2 | b_breed | 1 | big | 1 | |
| 19 | G.BANG 1 | G.BANG 1 | b_breed | 1 | big | 2 | |
| 20 | M.PRESS 2 | OGRE FRONT | b_breed | 0 | big | 3 | |
| 21 | BEHIND | OGRE BEHIND | b_breed | 0 | big | 4 | |
| 22 | RIDE 2 | OGRE BEHIND 2 | b_breed | 0 | big | 5 | |
| 23 | G.BANG 3 | G.BANG 3 | b_breed | 1 | big | 6 | |
| 24 | PATROL | DISPLAY_B | b_utility | 1 | big | 7 | |
| 25 | CLONE | CLONE_B | b_utility | 1 | — | — | |
| 27 | BIND 1 | BIND 1 | t_breed | 3 | tent | 0 | |
| 28 | BIND 2 | BIND 2 | t_breed | 3 | tent | 1 | |
| 29 | T.WALL 3 | T.WALL 3 | t_breed | 3 | tent | 2 | |
| 30 | MILK 2 | MILK 2 | t_utility | 3 | tent | 3 | |
| 31 | T.WALL 1 | T.WALL 1 | t_breed | 3 | tent | 4 | |
| 32 | T.WALL 2 | T.WALL 2 | t_breed | 3 | tent | 5 | |
| 33 | RECOVER | RECOVER | t_utility | 3 | tent | 6 | |
| 34 | CLEAN | CLEAN | t_utility | 3 | — | — | |
| 36 | DAIRY | DAIRY | b_other | 1 | fixed | — | `required_class` 9 (HATHOR) |
| 37 | GIANT | GIANT | b_other | 0 | standard | — | `required_class` 11 (SELENE); classes with `clothing_giant` use it ([§7](#7-clothing-maps-how-a-class-looks-in-each-cell)) |
| 38 | CHAINS | CHAINS | b_other | 1 | fixed | — | `required_class` 12 (MORRIGAN) |
| 39 | L.SHRINE | LILITH SHRINE | b_other | 0 | fixed | — | `required_class` 8 (LILITH) |
| 40 | S.SHRINE | S.SHRINE | b_other | 1 | — | — | |
| 41 | F.SHRINE | F.SHRINE | b_other | 1 | — | — | |
| 42 | R.SHRINE | R.SHRINE | b_other | 1 | — | — | |

> **When** G.BANG cells are looked up by number: G.BANG 1 is h_type **19** and G.BANG 2 is h_type **18**, the other way round from the names.

---

## Appendix B. Troubleshooting

**In short:** when something does not work, search `gnx_debug.txt` ([3.5](#35-the-log-file-gnx_debugtxt)) for the messages below. They are quoted exactly; `<...>` parts change.

### B.1 How to read the log quickly

1. **Search for `ERROR`.** These lines stop a whole mod or file from loading, so fix them first; they also appear in the message box after loading.
2. **Check for `[GNX] loading: <name> v<version>`** for your mod: the manifest was found and the version check passed.
3. **Search for `WARN`.** The mod loads, but a reference, sprite or script is missing; this explains most "invisible part" and "class not allowed" problems.
4. **Search for `FAIL`.** These are the self-checks after loading (`[GNX-TEST]`); one that names your cell (`h=<N>`) or class ID points to a content problem.
5. **For drawing problems, turn on VERBOSE** (settings window → DEBUG → GNX DEBUG → VERBOSE). Lines such as `[GNX] class_spr h=<N> ...` then show which sprite set each cell picks. The switch is not saved.

### B.2 Log messages

| Message | What it means | What to do |
|---|---|---|
| `[GNX] mods/ folder not found, no mods loaded` | No `GNX_mods` folder where GNX looked. | Create it in the game folder; `[GNX] mods_root=<path>` shows the exact place. |
| `[GNX-WARN] folder '<name>' has no manifest.json, skipped` | No `manifest.json` directly inside a folder in `GNX_mods`. | Move a nested mod up one level, or add a manifest. |
| `[GNX] ERROR: Mod '<folder>': manifest.json invalid (<message>)` | The manifest is not valid JSON. | Validate it: commas, quotes, comments, a comma after the last item. |
| `[GNX] ERROR: Mod '<folder>': incompatible with game version 1.40 (compatible: <list>)` | `compatible_game_versions` is missing or has none of `"1.38"`, `"1.39"`, `"1.40"`; the mod is not loaded. | Use `["1.40"]` ([4.2](#42-the-version-check)). |
| `[GNX] ERROR: Mod '<folder>': cells file '<path>' not found` | A listed file does not exist. Same wording for `classes`, `quests`, `props` and `sounds`; for tools `[GNX] ERROR: Mod '<folder>': <path> not found`. | Fix the path; it is relative to the mod folder, and case may matter. |
| `[GNX] ERROR: Mod '<folder>': <path> invalid (<message>)` | A data file is not valid JSON; the whole file is skipped. | Validate the file. |
| `[GNX] ERROR: Mod '<folder>': <path> is not a JSON array` | classes.json must be a list `[ ... ]`. | Wrap the classes in `[` and `]`. |
| `[GNX-WARN] mod '<folder>': <file> exists but is not declared in manifest.json` | The file is not loaded. | Add its key to the manifest ([4.4](#44-data-file-keys)). |
| `[GNX] WARN <key>: no strip/path/frames/folder, returning fallback` | A sprite entry has no source key (for example a `mode` key or a misspelled name); nothing is drawn. | Use `strip`, `frames`, `path`, `folder` or `from_game` ([5.2](#52-where-gnx-takes-the-image-from)). |
| `[GNX] <key>: strip frames=<N> idx=-1` | The strip PNG could not be loaded, usually a wrong path or file name. | Check the path and name, including case. |
| `[GNX-WARN] <key>: folder '<path>' has no .png frames, returning fallback` | The `folder` sprite's folder is empty or missing. | Check the folder path ([5.2](#52-where-gnx-takes-the-image-from)). |
| `[GNX-WARN] <key>: from_game '<name>' is not a game sprite, returning fallback` | The `from_game` name does not exist. | Fix the sprite name. |
| `[GNX-WARN] <key>: origin_from '<name>' is not a game sprite - using xorig/yorig` | The `origin_from` sprite does not exist; the sprite loads with `xorig` / `yorig`. | Fix the name or remove `origin_from`. |
| `[GNX] WARNING: script not found: <name>` | A cell script name (`scr_h`, `scr_idle` …) does not exist. No fallback: the cell can crash the game when used. | Copy the name exactly ([§9](#9-the-physical-block-how-a-cell-behaves)). |
| `[GNX] class_id <N> override (merge)` | Information: your override was merged into class `<N>`; without `(merge)`, a new class was created at that ID. | Nothing, if intended ([§12](#12-patching-vanilla-cells-and-classes)). |
| `[GNX] class_id <N> hash collision (probe failed)  - skipped` | No free class ID was found; practically never happens. | Report it with your log. |
| `[GNX] patched h=<N> by mod=<folder>` | Information: an existing `h_type` changed that cell instead of creating one. | For a new cell, remove `h_type` ([3.4](#34-duplicate-ids)). |
| `[GNX-WARN] mod '<folder>' patches vanilla cell h=<N> (h_type 1-42 are vanilla). Remove 'h_type' from cells.json to auto-assign a unique ID.` | The same, for a vanilla cell. | Keep it if intended, otherwise remove `h_type` ([§12](#12-patching-vanilla-cells-and-classes)). |
| `[GNX-WARN] cell h=<N> required_class ref '<ref>' not found. Check: folder name + class name must match exactly (case-sensitive).` | A `required_class` text reference matches no loaded class. | Check folder, dot and class `name` letter by letter, that the class's mod is installed and on, and that numeric IDs have no quotes. |
| `[GNX-WARN] by_class '<ref>' not found. Check: folder name + class name must match exactly (case-sensitive).` | A fixed-mode `by_class` key matches no loaded class. | As for `required_class`. |
| `[GNX] ERROR: Mod '<folder>': cell '<name>' has no category ... - cell skipped` (also `has no physical block` and `physical is missing: <keys>`) | A new cell is incomplete and was not registered. | Add the missing keys ([9.1](#91-required-keys)). |
| `[GNX-WARN] Mod '<folder>' class <id>: <n> sprite(s) missing or not loadable, using the vanilla peasant's instead` | Clothing or naked map sprites could not be loaded; the Peasant's (for an override, the old class's) are drawn. | Check the sprite paths and file names. |
| `[GNX-WARN] skipped drawing a sprite that does not exist (<value>), probably a missing mod file` | A sprite that was never loaded was to be drawn; nothing is drawn. | Look for a missing PNG or a misspelled `gnx:` key. |
| `[GNX] ERROR: Mod '<folder>' needs '<mod>' (not installed); not loaded` | A mod in `requires` is missing. | Install it or remove it from `requires`. |
| `[GNX] ERROR: Mod '<folder>' also declares map '<map>' (already owned by '<other>'); its map_info and map_start are ignored` | Two mods declare `map_info` (or its old name `map_button`) or `map_start` for the same map. | Keep them in one mod only ([§21](#21-multi-map-travel)). |
| `[GNX-WARN] class_map h=<N> unresolved ref: <ref>` | A `class_map` class name was not found after all mods loaded. | Check the spelling. |
| `[GNX] raid_spawn skipped level=0 class=<N> stage=<S>` | `"level": 0` is allowed only for stage 4 (Tower). | Use level 1 or 2 for stages 0–3 ([§13](#13-raid-spawns-and-the-trade-shop)). |
| `[GNX] portrait '<folder>.<key>': file not found (<path>)` | A quest portrait is missing. | Portraits are read from `<mod>/portraits/`. |
| `[GNX-SOUND] file not found: <path>` | A sound file is missing. | Sounds are read from `<mod>/sounds/` ([§18](#18-sounds-soundsjson)). |
| `[GNX-WARN] tool class ref '<ref>' not found (mod=<folder>)` | A tool button refers to an unknown class (also `tool cell ref`). | Check the reference ([§17](#17-tools-toolsjson)). |
| `[GNX-WARN] unlock: cell h=<N> is not in any build category - skipped` | The cell is in no build menu, usually because of a misspelled `category`. | Use a category from [§8](#8-cells-cellsjson). |
| `[GNX-SANITIZE] orphaned unit class=<N> -> fresh peasant (slot=<N>)` | A save holds a captive of a class that no longer exists; she became a new peasant. | Usually a renamed folder or class, or a removed mod ([3.4](#34-duplicate-ids)). |
| `[GNX-SANITIZE] orphaned cell h=<N> -> rebuild as h=<N>` | A save holds a cell type that no longer exists; it was rebuilt as a vanilla cell. | Same causes. |
| `[GNX-TEST] FAIL  T16 mod class entries invalid: <ids>` | These mod classes have neither `clothing_standard` nor `clothing_giant`. | Add a clothing map ([§7](#7-clothing-maps-how-a-class-looks-in-each-cell)). |
| `[GNX-TEST] FAIL  T84 bad required_class: h<N>[<i>]` | Entry `<i>` of cell `<N>`'s `required_class` (a single value: `h<N>`) is still unresolved text. | See the `required_class ref ... not found` warning above it. |
| `[GNX-TEST] FAIL  DROUTE h=<N> FIXED_MISSING_PHASE` | A fixed-mode cell lacks `phase_1` or `phase_2`. | Add both ([§10](#10-cell-sprites-human_spr-and-mon_spr)). |
| `[GNX-TEST] FAIL  DROUTE h=<N> c=<class> CLASS_MAP_NO_MATCH` | A `class_map` cell has no `default` and does not list this class. | Add a `default` or list the class ([§10](#10-cell-sprites-human_spr-and-mon_spr)). |

### B.3 Common mistakes

- **ID numbers in quotes:** `"h_type": "24680"` or `"required_class": "11"` is text; write numbers without quotes ([1.3](#13-json-in-two-minutes)).
- **Wrong case or spelling in references:** `"my_mod.witch"` does not find `Witch`, and the folder part must match exactly too.
- **A needed mod is switched off:** check the MODS menu and list needed mods in `requires` ([4.5](#45-requires-and-the-mods-menu)).
- **Manifest one folder too deep:** `GNX_mods/my_mod/my_mod/manifest.json` is not found.
- **Wrong game version:** `compatible_game_versions` needs `"1.38"`, `"1.39"` or `"1.40"` as text.
- **`mode` in a sprite entry:** there is no such key; use the source keys of [5.2](#52-where-gnx-takes-the-image-from).
- **Wrong frame counts:** `frames` must match the strip; normal classes need 3 skin tones in every body strip and 6 hand frames ([5.6](#56-frame-counts)).
- **`class_id` without `"override": true`:** ignored; the class gets a hash ID ([§6](#6-classes-classesjson)).
- **An explicit `h_type` that already exists:** the entry patches that cell. Leave `h_type` out for new cells, or use 100 or higher: below 100, custom monster sprites miss vanilla captives and `mon_positions` does not change the strip rows ([§8](#8-cells-cellsjson)).
- **Misspelled `category`:** the cell appears in no build menu, with no warning at load time ([§8](#8-cells-cellsjson)).
- **Missing phases:** fixed-mode cells need `phase_1` and `phase_2`, plus `phase_0` for a big cell starting with `scr_slot_h_big_start` ([§10](#10-cell-sprites-human_spr-and-mon_spr)).
- **Missing monster sprites:** without `mon_spr` / `mon_spr_hob` / `mon_spr_ogr` for a monster type, vanilla sprites (usually the wall-cell pose) are drawn ([§10](#10-cell-sprites-human_spr-and-mon_spr)).
- **No offspring:** a mod class without `birth_class` and `birth_classes` produces none ([§14](#14-pregnancy-and-birth)).
- **Too short BIRTH 2 strip:** `birth_2` needs 6 frames per skin (18 for a normal class), although the last frame of each block is never shown ([14.4](#144-birth_spr-birth-animations)).
- **Raid weights too high:** vanilla weights are 12–65 per pool, the default 10; 100–200 puts your class in almost every encounter ([§13](#13-raid-spawns-and-the-trade-shop)).
- **Stage numbers mixed up:** 1 is Mountain, 2 is Forest ([A.3](#a3-raid-stages)).
- **`fap_mul` / `bap_mul` as income:** they set enemy strength in raids, not income ([§13](#13-raid-spawns-and-the-trade-shop)).
- **Quest triggers firing again and again:** a trigger fires whenever its hook runs and its conditions pass; guard it with a state key. `increment_state` does not exist ([QUESTS_SCHEMA.md](QUESTS_SCHEMA.md)).
- **Map mod for players still on GNX 1.4.8:** 1.4.8 reads only the old name `map_button`; with `map_info` alone the map gets no travel entry there ([§21](#21-multi-map-travel)).
- **Renaming after release:** a renamed folder, class or cell changes hash IDs and breaks saves ([3.4](#34-duplicate-ids)).
- **`0` instead of `-1`:** in a sprite field `0` is a real game sprite ([1.4](#14-what--1-means)).
