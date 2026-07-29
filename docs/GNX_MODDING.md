# GNX Modding Reference

GNX (Goblin Nest Extender) is a mod layer patched into `data.win` that loads
JSON-defined classes and cells at startup. No recompilation needed — drop files
into `GNX_mods/` and run.

---

## Table of Contents

1. [Mod Folder Structure](#1-mod-folder-structure)
2. [manifest.json](#2-manifestjson)
3. [Custom Classes — classes.json](#3-custom-classes--classesjson)
4. [Sprite Strips](#4-sprite-strips)
5. [Clothing Maps](#5-clothing-maps)
6. [Custom Cells — cells.json](#6-custom-cells--cellsjson)
7. [Cell Physical Block](#7-cell-physical-block)
8. [Cell Sprite Blocks](#8-cell-sprite-blocks)
9. [Raid Spawns](#9-raid-spawns)
10. [Vanilla Patches](#10-vanilla-patches)
11. [Trade Shop & Birth Class Mapping](#11-trade-shop--birth-class-mapping)
12. [Quick-Reference: Sprite Keys by Cell Type](#quick-reference-sprite-keys-by-cell-type)
13. [Post-Raid Cage Escape](#13-post-raid-cage-escape)
14. [Special Class Features](#14-special-class-features)
15. [Tool System — tools.json](#15-tool-system--toolsjson)
16. [Sound System — sounds.json](#16-sound-system--soundsjson)

---

## 1. Mod Folder Structure

```
<game folder>/
  GNX_mods/
    my_mod/
      manifest.json
      classes.json     ← optional
      cells.json       ← optional
      quests.json      ← optional
      tools.json       ← optional
      strips/          ← packed sprite strips
        spr_h_myclass_idle_head.png
        ...
      portraits/       ← quest dialog portraits (133x113)
```

GNX auto-discovers mods: any direct subfolder of `GNX_mods/` that contains a
`manifest.json` is loaded. No index file needed — just drop the folder in.
Load order is alphabetical by folder name. Later mods can override earlier ones
if they share a `class_id` or `h_type` (last writer wins).

---

## 2. manifest.json

```json
{
  "mod_id": "my_mod",
  "name": "My Mod",
  "version": "1.0.0",
  "compatible_game_versions": ["1.33"],
  "classes": "classes.json",
  "cells": "cells.json"
}
```

> **The mod's identity is its folder name**, not any manifest field. The loader
> keys everything — save state, string refs like `"my_mod.ClassName"`, error
> messages — off the folder name. `mod_id` is **not read by the loader**; it's
> optional and informational. If you include it, keep it equal to the folder
> name to avoid confusion.

| Field | Required | Notes |
|-------|----------|-------|
| `name` | yes | Display name (shown in load logs) |
| `version` | yes | Semver string |
| `mod_id` | no | Informational only — not read by the loader. Conventionally set equal to the folder name |
| `compatible_game_versions` | yes | Array of game version strings. Must include the running game version or the mod is silently skipped |
| `compatible_game_versions` | yes | Array of game version strings. Must include the running game version or the mod is silently skipped |
| `classes` | no | Path relative to mod folder; omit if no classes |
| `cells` | no | Path relative to mod folder; omit if no cells |
| `quests` | no | Path relative to mod folder; omit if no quests/events |
| `tools` | no | Path relative to mod folder; omit if no tool buttons/keybinds |
| `sounds` | no | Path relative to mod folder; omit if no custom sounds. See [§16](#16-sound-system--soundsjson) |
| `save_state` | no | Per-mod persistent state definition (see below) |

### save_state

Mods can declare persistent state fields that survive save/load. Declare
defaults in `manifest.json`:

```json
{
  "save_state": {
    "version": 0,
    "fields": {
      "boss_state": -1,
      "escape_count": 0
    }
  }
}
```

Fields are initialized to their default values on first load. Stored in
`global.val.gnx_mod_data.{folder_name}` and auto-serialized with saves.

Access at runtime via quest side effects (`set_state`) or conditions
(`state_equals`, `state_gte`). Reserved prefixes: `_q_`, `_b_`, `_d_`,
`_version`.

---

## 3. Custom Classes — classes.json

Array of class objects. Each defines a capturable human unit type.

```json
[
  {
    "class_id": 14,
    "name": "WITCH",
    "override": false,
    "is_special": false,
    "has_hair": false,
    "hand_color": "gnx:hand",
    "icon": "gnx:icon_head",
    "icon_hair": -1,
    "sprite_prefix": "spr_h_witch",
    "preg_c_override": 2,
    "preg_mon_type_override": 1,
    "fap_mul": 1.0,
    "bap_mul": 1.0,
    "raid_spawns": [ ... ],
    "sprites": { ... },
    "clothing_standard": { ... },
    "clothing_big": { ... },
    "clothing_tent": { ... }
  }
]
```

### class_id

**Optional.** Vanilla classes occupy IDs 0–13. For new classes (≥14), omit
`class_id` and GNX assigns a stable ID automatically using a hash of
`"mod_folder.ClassName"` — same ID every run, no manual coordination needed.

If you supply an explicit `class_id` it must be ≥14. Two mods declaring the
same explicit `class_id` — the last loaded wins (alphabetical order). For
vanilla overrides (0–13) this is intentional (`"override": true`); for new
classes it's a silent collision. Prefer omitting the field to let GNX hash it.

`required_class` and `birth_classes` in cells.json can reference classes by
string (`"my_mod.ClassName"`) or by integer ID — both work.

Vanilla ID map (verified against the game's class registry in `s_initials.gml`):
```
0=Peasant  1=Cleric   2=Knight   3=Ranger   4=Nun      5=Samurai
6=Mage     7=Warrior  8=Lilith   9=Cow     10=Nyx     11=Giant
12=Morrigan 13=Cat    14+ = mod range
```

### override

`true` = modify an existing vanilla class (0–13). The `class_id` must match a
vanilla class. Use this to reskin Peasant/Cleric, or to tweak a single behavior
field on a special (Lilith, etc.).

**Overrides merge, they don't wipe.** GNX only overwrites the fields your JSON
actually specifies; every field you omit is kept from the existing entry. So a
minimal override that sets only `birth_class` or `preg_c_override` leaves the
class's vanilla sprites/clothing fully intact. You do **not** need to re-declare
sprites just to change a stat. (This also makes a voice-only override safe — but
for pure voice config prefer the `sounds.json` `voice_map`, see [§16](#16-sound-system--soundsjson),
which needs no class registration at all.)

### Core fields

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | In-game display name, uppercase |
| `is_special` | bool | If true, unit is a "special" type (Nyx/Lilith-tier); affects drop pools and spawn limits |
| `has_hair` | bool | Whether the class has a separate hair layer (index 0 in spr_array) |
| `hand_color` | string | Sprite key for the hand color overlay. Usually `"gnx:hand"` |
| `icon` | string or -1 | Sprite key for the unit icon head. `-1` = use default goblin icon |
| `icon_hair` | string or -1 | Sprite key for icon hair overlay. `-1` = no hair on icon |
| `sprite_prefix` | string | Prefix used to name all runtime sprites, e.g. `"spr_h_witch"` |
| `default_leg` | int | Optional. Forces all units of this class to a fixed leg variant: `0`=warrior kneeling body (`spr_h_base_*_3`), `1`=leg_1, `2`=leg_2. Omit to use normal random leg selection |
| `voice` | struct | Optional. Fixed moan voice for this class: `{"bank": "soft", "pitch": 1.0}`. `bank` is a voice-bank name from a `sounds.json` (auto-prefixed with the owning mod). `pitch` optional (default random 0.9–1.15). Requires a sound mod to be loaded. See [§16](#16-sound-system--soundsjson) |

### Ogre patrol carry sprites (`gnx:carry_head` / `gnx:carry_hair`)

When an ogre on patrol carries off a captured unit of this class, it draws a
head/hair portrait on the ogre's back. For `class_id >= 14`, declare these in
`sprites` and `gnx_resolve_class` will pick them up automatically — no
reference needed elsewhere (no `gnx:` key in any clothing map).

```json
"sprites": {
  "carry_head": {
    "strip": "strips/spr_h_witch_carry_head.png",
    "frames": 24,
    "xorig": 55, "yorig": 114,
    "canvas_w": 115, "canvas_h": 115
  },
  "carry_hair": {
    "strip": "strips/spr_h_witch_carry_hair.png",
    "frames": 24,
    "xorig": 55, "yorig": 114,
    "canvas_w": 115, "canvas_h": 115
  }
}
```

24 frames, 115×115 canvas, origin (55, 114) — matches vanilla
`spr_ogre_carry_head_*` / `spr_ogre_carry_hair_*`. If `has_hair` is `false`,
omit `carry_hair` (resolves to `-1`, no hair drawn). If omitted entirely,
`carry_head_spr`/`carry_hair_spr` resolve to `-1` and the captive is drawn
without a portrait while carried.

### Stat overrides

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `preg_c_override` | int | class-specific | Pregnancy capacity override |
| `preg_mon_type_override` | int | (none) | Pins offspring species regardless of who bred her: 0=goblin, 1=hobgoblin, 2=tentacle, 3=ogre. Omit to let the breeding monster's species decide |
| `fap_mul` | float | 1.0 | Multiplier on fap income from this class |
| `bap_mul` | float | 0 | Multiplier on birth income from this class. **Default is 0 (birth income disabled).** Set explicitly if births should generate income |

---

## 4. Sprite Strips

All sprites are packed horizontal strips: one PNG per sprite, frames laid
left-to-right. Each frame is `canvas_w × canvas_h` pixels.

### sprites dict

Every sprite used in `clothing_*` or `mon_spr` must be declared here.

```json
"sprites": {
  "idle_head": {
    "strip": "strips/spr_h_witch_idle_head.png",
    "frames": 90,
    "xorig": 0,
    "yorig": 90
  },
  "icon_head": {
    "strip": "strips/spr_unit_icon_witch_head.png",
    "frames": 3,
    "xorig": 10,
    "yorig": 13,
    "canvas_w": 21,
    "canvas_h": 26,
    "folder": "spr_unit_icon_witch_head"
  }
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `strip` | yes | Path to packed strip PNG, relative to mod folder |
| `frames` | yes | Total frame count across the strip |
| `xorig` | yes | X origin (pivot point) |
| `yorig` | yes | Y origin (pivot point). Usually equals frame height |
| `canvas_w` | no | Frame width if non-standard. Default = strip_width / frames |
| `canvas_h` | no | Frame height if non-standard |
| `folder` | no | Source folder name; used by `gnx_pack_strips.py` to find per-frame PNGs |

### gnx: references

Inside `clothing_*` and `mon_spr`, sprite values prefixed with `gnx:` refer
back to keys in this mod's `sprites` dict.

`"head": "gnx:idle_head"` → loads the sprite declared as `"idle_head"` above.

You can also reference vanilla sprites directly by name:
`"head": "spr_h_cleric_idle_head"` → uses the vanilla cleric head sprite.

### Standard frame counts

These match the vanilla game's animation lengths:

| Animation | Phase | Frames (3 skins × N) |
|-----------|-------|----------------------|
| Standard idle/start | 1 | 90 (3×30) |
| Standard loop | 2 | 225 (3×75) |
| Big cell start | — | 36 (3×12) |
| Big cell idle | — | 48 (3×16) or 42 (3×14) |
| Big cell loop | — | 105 (3×35) |
| Tent idle | 1 | 42 (3×14) |
| Tent loop | 2 | 105 (3×35) |
| Tent birth | 4 | 42 (3×14) |
| Hand sprite | — | 2 (open/closed) |
| Icon | — | 3 (one per skin) |

### Packing strips

Use `gnx_pack_strips.py` to convert per-frame PNG folders into strips:

```
python gnx_pack_strips.py path/to/my_mod --force
```

Per-frame folder naming: `{strip_name_without_ext}/{strip_name_without_ext}_{i}.png`

The `folder` field in sprites overrides the auto-derived folder name if needed.

---

## 5. Clothing Maps

Clothing maps wire sprite keys to animation phases and leg variants.
GNX reads these to know which sprite to draw per frame.

### clothing_standard

Standard cells (wall, ride, etc.). Two phases: idle (1) and loop (2).
Each phase has two leg variants (leg_1, leg_2).

```json
"clothing_standard": {
  "phase_1": {
    "leg_1": {
      "hair":     "gnx:idle_hair",   // -1 if class has no hair
      "head":     "gnx:idle_head",
      "breast":   "gnx:idle_breast",
      "hand":     "gnx:hand",
      "leg":      "gnx:idle_leg_1",
      "leg_part": "gnx:idle_legp"    // cloth hem/skirt; -1 if none
    },
    "leg_2": { ... }
  },
  "phase_2": {
    "leg_1": { ... },
    "leg_2": { ... }
  }
}
```

### clothing_big

All large cells (`slot_type 2`) whose `human_spr.base_body` is `"big"` — this
includes both standard large cells (G.BANG, RIDE 2, BEHIND, etc.) and special
large cells (DAIRY, GIANT, CHAINS, all SHRINES). Three sub-phases: start, idle, loop.

```json
"clothing_big": {
  "start": {
    "hair":    "gnx:big_start_hair",  // omit key if no hair
    "head":    "gnx:big_start_head",
    "breast":  "gnx:big_start_breast",
    "leg_any": "gnx:big_start_leg"    // single leg sprite for start
  },
  "idle": {
    "hair":  "gnx:big_idle_hair",
    "head":  "gnx:big_idle_head",
    "breast":"gnx:big_idle_breast",
    "leg_1": "gnx:big_idle_leg_1",   // two leg variants for idle
    "leg_2": "gnx:big_idle_leg_2"
  },
  "loop": {
    "hair":    "gnx:big_loop_hair",
    "head":    "gnx:big_loop_head",
    "breast":  "gnx:big_loop_breast",
    "leg_any": "gnx:big_loop_leg"
  }
}
```

### Leg keys

Inside clothing maps, the key used for the leg slot determines which leg variant it applies to:

| Key | Meaning |
|-----|---------|
| `leg_1` | Standard leg variant 1 (most poses) |
| `leg_2` | Standard leg variant 2 (alternate pose) |
| `leg_any` | Universal fallback — applies to all leg types. Use this when the sprite is the same regardless of leg variant (common for big-cell start/loop phases) |
| `leg_0` | Warrior/kneeling body (`spr_h_base_*_3` sprites). Only needed for classes with `default_leg: 0` |

### clothing_tent

Tent cells. Three phases: idle (1), loop (2), birth (4). Each has two leg variants.

```json
"clothing_tent": {
  "phase_1": {
    "leg_1": {
      "hair":     -1,
      "head":     "gnx:tent_idle_head",
      "breast":   "gnx:tent_idle_breast",
      "hand":     "gnx:hand",
      "leg":      "gnx:tent_idle_leg_1",
      "leg_part": "gnx:tent_idle_legp"
    },
    "leg_2": { ... }
  },
  "phase_2": { ... },
  "phase_4": { ... }
}
```

---

## 6. Custom Cells — cells.json

Array of cell objects. Each defines a dungeon cell.

h_type values 0–42 are reserved for vanilla. For new cells (≥43), omit
`h_type` and GNX assigns a stable ID automatically using a hash of
`"mod_folder.CellName"` — same ID every run, no manual coordination needed.

If you supply an explicit `h_type` it must be ≥43. Two mods declaring the
same explicit `h_type` — the last loaded wins. For vanilla patches (0–42) this
is intentional; for new cells it's a silent collision. Prefer omitting the
field to let GNX hash it.


```json
[
  {
    "name": "MY CELL",
    "category": "breed",
    "mon_types": [0],
    "slot_type": 0,
    "price": 200,
    "spawn_info": { ... },
    "physical": { ... },
    "human_spr": { ... },
    "mon_spr": { ... },
    "sprites": { ... }
  }
]
```

### Top-level cell fields

| Field | Notes |
|-------|-------|
| `h_type` | Optional. Omit for auto hash-assignment (≥100, stable across runs). If explicit, must be ≥43 |
| `name` | Display name in build menu (uppercase) |
| `category` | Build menu tab. Standard: `"breed"`, `"utility"`, `"pleasure"`. Large: `"b_breed"`, `"b_utility"`, `"b_other"`. Tent: `"t_breed"`, `"t_utility"` |
| `mon_types` | Array of monster species that can use this cell: 0=goblin, 1=hobgoblin, 2=ogre |
| `slot_type` | `0`=standard wall, `2`=large cell, `3`=tent |
| `price` | Gold cost to build |
| `spawn_info` | Coin/mood output (see below) |

### spawn_info

```json
"spawn_info": {
  "coin": 2,          // coin income per cycle
  "mood": 1,          // mood income per cycle
  "coin_mul": false,  // if true, coin multiplied by upgrade multiplier
  "mood_mul": false   // if true, mood multiplied by upgrade multiplier
}
```

---

## 7. Cell Physical Block

Controls gameplay behaviour: which scripts run, hand positions, unlock rules.

```json
"physical": {
  "allow_preg": true,
  "max_mon_num": 1,
  "anal": false,
  "slot_dirt_init": 0,
  "character_row": 0,
  "layers": [ ... ],
  "scr_idle": "scr_slot_h_state_idle",
  "scr_h": [ ... ],
  "scr_draw": "scr_draw_slot_gnx",
  "slot_range": 1,
  "required_class": [0, 14],
  "range_draw_func": "scr_draw_l_shrine_range",
  "scr_unoccupy": "scr_gnx_unoccupy_log",
  "hand_x":      [17, 6],
  "hand_y":      [-42, -40],
  "hand_xscale": [1, 1],
  "hand_angle":  [90, 0],
  "hand_frames": { "frame_1": [1], "frame_2": [2, 3], "frame_3": [2, 3] },
  "sp_spr": "spr_sp_v_start",
  "sq_x": 22, "sq_y": [-31, -30],
  "sp_x": 22, "sp_y": [-28, -33],
  "sp_anim_x": 0, "sp_anim_y": -1
}
```

| Field | Notes |
|-------|-------|
| `allow_preg` | Whether this cell can result in pregnancy |
| `max_mon_num` | Max simultaneous goblins (usually 1) |
| `anal` | Whether the cell uses anal variants |
| `slot_dirt_init` | Initial dirt level (0 = clean) |
| `character_row` | Vertical row for the human character: 0=front, 1=back |
| `scr_idle` | Script name for the idle state machine. Use `"scr_slot_h_state_idle"` for standard idle |
| `scr_h` | Array of 7 script names for the 7 h-scene phases (start, wait, slow loop, fast loop, wait, ejaculation, wait) |
| `scr_draw` | Draw script. Use `"scr_draw_slot_gnx"` for all GNX cells |
| `slot_range` | Number of adjacent slots this cell occupies |

### Physical extension fields

These are GNX-only — vanilla cells do not have them.

| Field | Notes |
|-------|-------|
| `required_class` | Array of class IDs that can be placed here. Omit = any class allowed. String refs (`"mod_id.ClassName"`) are supported alongside integer IDs |
| `range_draw_func` | Script to draw the range indicator. Omit = default |
| `scr_unoccupy` | Script called when a unit is removed. Use `"scr_gnx_unoccupy_log"` for logging-only |

### layers array

Each entry defines one rendering layer for the cell background:

```json
"layers": [
  [layer_type, sprite_or_null, animated, shift_index, optional_5th_flag]
]
```

| Index | Meaning |
|-------|---------|
| 0 | Layer type (see table below) |
| 1 | Sprite name (string) or `"gnx:key"` or `-1` for none |
| 2 | Animated (bool) — whether the sprite advances frames during h-scene |
| 3 | Shift index — which `spr_slot` entry controls this layer's mod; `-1` = not moddable |
| 4 | (Optional) extra flag, layer-type specific |

**Layer types:**

| Type | Description |
|------|-------------|
| 0 | Background / back wall |
| 2 | Hand color overlay |
| 5 | Extra foreground layer |
| 7 | Human body part (reserved for internal use) |
| 8 | Human body part (reserved for internal use) |
| 12 | Dirt overlay |

### scr_h phase scripts

Standard wall-type h-scene scripts (copy these for a basic breeding cell):

```json
"scr_h": [
  "scr_slot_h_base_start",
  "scr_slot_h_base_wait",
  "scr_slot_h_base_sloop",
  "scr_slot_h_base_floop",
  "scr_slot_h_base_wait",
  "scr_slot_h_base_ej",
  "scr_slot_h_base_wait"
]
```

### hand_x / hand_y / hand_xscale / hand_angle

Two-element arrays `[leg_variant_1, leg_variant_2]`. Define where the goblin's
hand sprite is drawn relative to the cell origin.

`hand_xscale` = 1 (normal) or -1 (mirrored). `hand_angle` in degrees.

### hand_frames

Which animation frames trigger hand transitions:

```json
"hand_frames": {
  "frame_1": [1],        // frames where hand uses pose 1
  "frame_2": [2, 3],     // frames where hand uses pose 2
  "frame_3": [2, 3]      // frames where hand uses pose 3
}
```

### sp_spr / sq / sp positions

Squirt and splash VFX:
- `sp_spr` — sprite name for the splash effect
- `sq_x/y` — squirt emission position
- `sp_x/y` — splash landing position
- `sp_anim_x/y` — splash drift per frame

---

### Advanced physical fields (vanilla-pattern cells)

All optional. Each is read individually (`variable_struct_exists` guard) by
`scr_gnx_register_cell` / `scr_set_slot_h_data` — omit any you don't need.
These exist to let GNX cells replicate specific vanilla mechanics (DAIRY,
DRINK, shrines, tents, CHAINS/G.BANG, CLONE).

| Field | Type | Effect | Vanilla cells using it |
|-------|------|--------|------------------------|
| `sign_y_base` | int | Base Y offset for the price/sign bubble above the cell | 18 cells (most breeding cells) |
| `sign_y_jitter` | int | Random jitter added to `sign_y_base`: `sign_y = base + irandom_range(-jitter, jitter)`. Default `2` if omitted but `sign_y_base` is set | same 18 cells (most use 2; DAIRY/GIANT/L.SHRINE use 1) |
| `bar_glow_rep` | int | Overrides the progress-bar glow repeat count (default `-1` = none) | RECOVER (`0`) |
| `milk_step` | int | Initial value of `slot_data.milk_step` (milking phase tracker) | MILK1 (`0`) |
| `milk_num` | int | Initial value of `slot_data.milk_num` (milk inventory counter) | MILK2 (`0`) |
| `blink_spr` | sprite name | Blink sprite for the captive (e.g. cow blink) | DAIRY (`spr_cow_blink`) |
| `anim_struct_overrides` | struct | Extra/overridden keys merged into `slot_data.anim_struct` at init | DAIRY (`milk_index`, `milk_timer`, `milk_spd`, `blink_index`, `blink_timer`); TRANSFER/PATROL (`char_state`) |
| `drink_num` | int | Initial value of `slot_data.drink_num` (drink cycle counter) | DRINK (`0`) |
| `mon_index` | array | Length determines size of `slot_data.mon_index`, created zero-filled (values themselves not copied) | DRINK (`[0, 0]` → 2-slot array) |
| `visual` | bool | Sets `slot_data.visual` (enables a visual-only overlay) | TRANSFER, PATROL (`true`) |
| `slot_front` | sprite name or `-1` | Foreground overlay sprite drawn over the cell (tents, etc.) | T.WALL1/2/3, RECOVER, MILK2, BIND1/2, CLEAN |
| `sp_place_init` | bool | If `true`, initializes `slot_data.sp_place = []` | CHAINS, G.BANG1 |
| `set_timer` | int | Initial value of `slot_data.set_timer` | CHAINS, G.BANG1/2/3 (`0`) |
| `slot_h` | bool | Whether the cell has an h-scene at all. Default `true` (omit unless `false`) | S.SHRINE, F.SHRINE, R.SHRINE, CLEAN, CLONE_B (`false`) |
| `scr_slot_step` | script name | Overrides the per-step state script | TRANSFER, R.SHRINE, CLEAN, CLONE_B |
| `scr_slot_base` | script name | Overrides the base idle script | L.SHRINE (`scr_slot_h_lilith_idle`) |
| `candle_index` | int | Initial value of `candle_index` (L.SHRINE candle tracker) | L.SHRINE (`0`) |
| `clone_wait` | int | Initial value of `slot_data.clone_wait` | CLONE_B (`0`) |
| `extra_spawn_part` | bool | If `true`, pushes one extra `false` entry onto `spawn_part` | tent cells (27, 28, 29, 31, 32) |
| `dirt_fix_inc` | bool | If `true`, increments `global.dirt_fix` once at slot init | L.SHRINE |
| `death_fix_inc` | bool | If `true`, increments `global.death_fix` once at slot init | S.SHRINE |
| `del_item_type` | int | On init, removes the first inventory item with this `item_type` from `global.inv_list` | DAIRY |

> **Note:** `hand_frames` supports `frame_1` through `frame_4`. `frame_4` is
> used by vanilla T.WALL 1/2 for the birth pose with hands out.

---

## 8. Cell Sprite Blocks

### human_spr

Defines how the human character is drawn in this cell. Three dispatch modes
are available, set via the `mode` field.

`base_body`: `"standard"` for normal cells, `"big"` for large cells, `"tent"` for tent cells.

#### Mode: `base+class` (default)

Cell provides the base body; class clothing tables provide per-class sprites.
`is_special` classes override with their own sprite tables. This is the standard
mode used by all vanilla cells.

```json
"human_spr": {
  "mode": "base+class",
  "base_body": "standard"
}
```

No additional fields needed. Sprites come from `clothing_standard`/`clothing_big`/
`clothing_tent` in the class's `classes.json` entry.

#### Mode: `fixed`

Cell controls human sprites directly via `spr_array`/`spr_c_array` per phase.
Class clothing is ignored; all classes render the same. Good for shrines,
environmental cells, single-pose scenes.

```json
"human_spr": {
  "mode": "fixed",
  "base_body": "standard",
  "phase_1": {
    "spr_array": ["gnx:idle_hair", "gnx:idle_head", "gnx:idle_breast", -1, "gnx:idle_leg", -1, -1],
    "spr_c_array": [-1, -1, "gnx:idle_breast_c", -1, "gnx:idle_leg_c", -1, -1]
  },
  "phase_2": {
    "spr_array": ["gnx:loop_hair", "gnx:loop_head", "gnx:loop_breast", -1, "gnx:loop_leg", -1, -1],
    "spr_c_array": [-1, -1, "gnx:loop_breast_c", -1, "gnx:loop_leg_c", -1, -1]
  }
}
```

Available phases: `phase_0` (big start), `phase_1` (idle), `phase_2` (loop),
`phase_4` (tent birth). Only define the phases your cell uses.

**`spr_array` slots:** `[0]`=hair, `[1]`=head, `[2]`=breast, `[3]`=breast_d,
`[4]`=leg, `[5]`=arm, `[6]`=extra.

**`spr_c_array` slots:** `[0]`=hair_c (controls hair visibility on head layers),
`[1]`=head_c, `[2]`=breast_c, `[3]`=breast_d_c, `[4]`=leg_c, `[5]`=arm_c,
`[6]`=extra_c. Set `[0]` to a sprite to show hair, `-1` to hide.

#### Mode: `class_map`

Per-class sprite dispatch on custom cells. Each class_id can have its own phase
entries. Classes not listed fall back to `default`. Solves the multi-mod sprite
conflict problem of `base+class` (where two mods adding rows to the same base
strip would collide).

```json
"human_spr": {
  "mode": "class_map",
  "base_body": "standard",
  "default": {
    "phase_1": {
      "spr_array": ["gnx:default_idle_hair", "gnx:default_idle_head", "gnx:default_idle_breast", -1, "gnx:default_idle_leg", -1, -1],
      "spr_c_array": [-1, -1, -1, -1, -1, -1, -1]
    },
    "phase_2": {
      "spr_array": ["gnx:default_loop_hair", "gnx:default_loop_head", "gnx:default_loop_breast", -1, "gnx:default_loop_leg", -1, -1],
      "spr_c_array": [-1, -1, -1, -1, -1, -1, -1]
    }
  },
  "classes": {
    "my_mod.Witch": {
      "phase_1": {
        "spr_array": ["gnx:witch_idle_hair", "gnx:witch_idle_head", "gnx:witch_idle_breast", -1, "gnx:witch_idle_leg", -1, -1],
        "spr_c_array": ["gnx:witch_idle_hair_c", -1, "gnx:witch_idle_breast_c", -1, "gnx:witch_idle_leg_c", -1, -1]
      },
      "phase_2": { "..." : "..." }
    }
  }
}
```

**`classes` keys:** string refs (`"mod.ClassName"`) or integer class_ids as strings
(`"14"`). String refs are resolved to integer IDs at load time. Cross-mod string
refs (referencing classes from another mod) are also supported and resolved in a
deferred pass after all mods load.

**`default`:** fallback for classes without a specific entry. Provide `default`
unless you're certain every possible class has an entry.

**Important:** if `class_map` is set but the dispatched class has no matching entry
AND no `default`, the dispatch does NOT fall through to `is_special` or `base+class`.
The modder must provide a `default` or cover all classes.

Same `spr_array`/`spr_c_array` slot layout and phases as `fixed` mode.

#### Dispatch priority

When resolving human sprites, GNX checks modes in this order:

1. `fixed` -> returns phase sprites directly
2. `class_map` -> looks up `classes[class_id]`, falls back to `default`
3. `is_special` class -> class-side clothing override
4. `base+class` -> base body + class clothing from strips

#### Categories

Build menu categories for the `category` field:

| Category | Menu |
|----------|------|
| `breed` | Standard breed |
| `utility` | Standard utility |
| `pleasure` | Standard pleasure |
| `b_breed` | Large breed |
| `b_utility` | Large utility |
| `b_other` | Large other/pleasure |
| `t_breed` | Tent breed |
| `t_utility` | Tent utility |

### mon_spr

Defines goblin sprites per animation phase. All sprite values use `"gnx:key"`
or a vanilla sprite name.

```json
"mon_spr": {
  "start": {
    "body": {
      "leg_1": { "alpha": "gnx:body_start_v1", "line": "gnx:body_start_v1_l" },
      "leg_2": { "alpha": "gnx:body_start_v2", "line": "gnx:body_start_v2_l" }
    },
    "hand": { "alpha": "gnx:hand_start", "line": "gnx:hand_start_l" },
    "pen": "gnx:pen_start",
    "touch": { "default": "gnx:touch_start" },
    "hand_xscale": "random"
  },
  "loop": {
    "head": [
      { "alpha": "gnx:head_d1", "line": "gnx:head_d1_l" },
      { "alpha": "gnx:head_d2", "line": "gnx:head_d2_l" }
    ],
    "body": {
      "leg_1": { "alpha": "gnx:body_loop_v1", "line": "gnx:body_loop_v1_l" },
      "leg_2": { "alpha": "gnx:body_loop_v2", "line": "gnx:body_loop_v2_l" }
    },
    "hand": {
      "leg_1": { "alpha": "gnx:hand_loop_v1", "line": "gnx:hand_loop_v1_l" },
      "leg_2": { "alpha": "gnx:hand_loop_v2", "line": "gnx:hand_loop_v2_l" }
    },
    "pen": "gnx:pen_loop",
    "touch": { "default": "gnx:touch_loop_v1" },
    "enter": { "default": "gnx:enter_loop" }
  }
}
```

**Goblin sprite pairs:** every fill (`_alpha`) sprite must have a matching
linework (`_line`) sprite. The `_line` variant is used in color modes 1 and 2.

**`head` array:** loop phase supports multiple head variants (random selection
per encounter). Provide one or more `{alpha, line}` objects.

**`hand_xscale`:** `"random"` = mirror randomly per encounter. Or a fixed
integer: `1` (normal) or `-1` (always mirrored).

---

## 9. Raid Spawns

Defines how frequently this class appears in raid encounters.

```json
"raid_spawns": [
  {
    "stage": 0,
    "level": 1,
    "weight": 200,
    "min_lvl": 0,
    "max_lvl": 1
  }
]
```

| Field | Required | Notes |
|-------|----------|-------|
| `stage` | yes | Raid stage index: 0=Village, 1=Forest, 2=Mountain, 3=Castle, 4=Tower |
| `level` | yes | Encounter level within the stage |
| `weight` | yes | Relative spawn weight. Higher = appears more often. Vanilla classes use 100-200 |
| `min_lvl` | yes | Minimum unit level for this entry |
| `max_lvl` | yes | Maximum unit level for this entry |
| `condition` | no | Condition object (same syntax as quest conditions). Evaluated at pick time; entry excluded if false |
| `max_per_encounter` | no | Max units of this class_id per encounter. Default unlimited |
| `ap_override` | no | `[fap, bap]` array. Replaces normal AP calculation for this unit. Use for bosses (e.g. `[300, 300]`) |

Multiple entries can be provided to cover different stages/levels.

### Conditional spawns

Use `condition` to gate a spawn entry on mod state, game progress, etc.:

```json
{
  "stage": 0,
  "level": 2,
  "weight": 30,
  "min_lvl": 5,
  "max_lvl": 5,
  "condition": {"type": "state_equals", "key": "boss_state", "value": 0},
  "max_per_encounter": 1,
  "ap_override": [300, 300]
}
```

This entry only appears in the pool when `boss_state == 0`, spawns at most
one per encounter, and uses 300/300 AP instead of normal level-based stats.
Condition types are the same as quest conditions (see
[QUESTS_SCHEMA.md](QUESTS_SCHEMA.md)).

---

## 10. Vanilla Patches

A cell entry with an existing `h_type` (0–42) only overrides the fields you
specify. All omitted fields keep their vanilla values.

Use this to change a vanilla cell's sprite layers without touching its gameplay:

```json
{
  "h_type": 1,
  "physical": {
    "layers": [
      [12, "spr_dirt_wall",        false, -1, false],
      [0,  "spr_slot_wall_2_back", false, -1],
      [2,  "spr_slot_wall_1_handc", true, -1],
      [5,  "spr_slot_wall_1_extra", false, -1],
      [7,  -1, false, -1, false],
      [8,  -1, false, -1, false]
    ]
  }
}
```

Only `physical.layers` is replaced; all other cell properties remain vanilla.

---

## 11. Trade Shop & Birth Class Mapping

### trade_stage

```json
"trade_stage": 2
```

| Field | Type | Notes |
|-------|------|-------|
| `trade_stage` | int 0-4 | Raid stage at which this class becomes available in the raid trader's shop. Omit = never appears in the shop |

At load, GNX appends the `class_id` to `global.gnx_trade_list[trade_stage]`.
`scr_choose_trade_item()` (s_trade_function.gml) adds each registered class to
the per-stage trade pool **3 times** (3x weight vs. vanilla entries), then
picks `min(3, unlocked_stages)` random units from the combined pool for the
shop's 3 trade slots. A class with `trade_stage` set has roughly a 3x-weighted
chance to appear once its stage is reached, but is not guaranteed every visit.

### birth_class (preferred)

Maps this class to a goblin class (0-3) per species when giving birth.
Determines which troop slot the offspring is grouped under in the raid screen.

```json
"birth_class": {"goblin": 2, "hobgoblin": 1, "tentacle": 0, "ogre": 3}
```

Values are clamped to 0-3. Omitting = goblin class 0 for all species
(weakest, same as peasant). Species keys: `goblin`, `hobgoblin`, `tentacle`,
`ogre`.

### birth_classes (legacy array)

```json
"birth_classes": [2, 1, 0, 3]
```

Same semantics as `birth_class` but indexed by species number (0=goblin,
1=hobgoblin, 2=tentacle, 3=ogre). `birth_class` struct takes priority if
both are present. Prefer `birth_class` for new mods.

**Note:** `birth_classes` on a CELL = array of human class_ids that can birth
from that cell. `birth_classes` on a CLASS = goblin class per species. Same
field name, different semantics.

---

## Quick-Reference: Sprite Keys by Cell Type

### Standard cell (slot_type 0)
Needs in `sprites`: `hand`, `idle_head`, `idle_breast`, `idle_leg_1`,
`idle_leg_2`, `idle_legp`, `loop_head`, `loop_breast`, `loop_leg_1`,
`loop_leg_2`, `loop_legp`. Add `idle_hair` / `loop_hair` if `has_hair=true`.
Add `idle_cape` / `loop_cape` for a cape/cloak overlay.

### Large cell (slot_type 2)
Needs: `hand`, `big_start_head`, `big_start_breast`, `big_start_leg`,
`big_idle_head`, `big_idle_breast`, `big_idle_leg_1`, `big_idle_leg_2`,
`big_loop_head`, `big_loop_breast`, `big_loop_leg`.
Add `big_start_hair`, `big_idle_hair`, `big_loop_hair` if `has_hair=true`.

### Tent cell (slot_type 3)
Needs: `hand`, `tent_idle_head`, `tent_idle_breast`, `tent_idle_leg_1/2`,
`tent_idle_legp`, `tent_loop_head`, `tent_loop_breast`, `tent_loop_leg_1/2`,
`tent_loop_legp`, `tent_birth_head`, `tent_birth_breast`, `tent_birth_leg_1/2`,
`tent_birth_legp`.

### Icon sprites
Required if `icon != -1`: frame count = 3 (one per skin), canvas 21×26,
origin 10×13. Provide `icon_head` (and `icon_hair` if `icon_hair != -1`).

---

## 13. Post-Raid Cage Escape

Classes can define escape behavior for captured units. After a raid win, GNX
checks each cage slot for classes with `post_raid.cage_escape`.

```json
"post_raid": {
  "cage_escape": {
    "condition": {"type": "state_equals", "key": "boss_state", "value": 0},
    "base_chance": 0,
    "over_diff_scale": 300,
    "counter_key": "escape_count",
    "popup": "escape_popup",
    "on_escape_event": "hint_event",
    "escape_event_threshold": 2,
    "on_survive_state": {"key": "boss_state", "value": 1},
    "on_survive_event": "captured_dialog"
  }
}
```

| Field | Notes |
|-------|-------|
| `condition` | Must pass for escape to be attempted. Same syntax as quest conditions |
| `base_chance` | Base escape % (0-100) |
| `over_diff_scale` | Scaling factor based on raid power ratio. Higher = more likely to escape when player dominates |
| `counter_key` | Save state key incremented on each escape |
| `popup` | Key into quests.json `popups` map, shown on escape |
| `on_escape_event` | Event fired after N escapes (see threshold) |
| `escape_event_threshold` | Number of escapes before `on_escape_event` fires |
| `on_survive_state` | State key/value set when the unit does NOT escape (stays captured) |
| `on_survive_event` | Event fired when the unit stays captured |

**Escape formula:** `irandom(1,100) <= (base_chance + irandom(1,100) - scale + scale * (over_diff - 1))`.
At even raid power (over_diff=1) escape is near-impossible. At 2x player
dominance (over_diff=2) escape chance ~50%. Set `base_chance: 100,
over_diff_scale: 0` for guaranteed escape (testing).

---

## 14. Special Class Features

### clothing_standard.max_row

For `is_special` classes: limits which standard cell rows (WALL 1-4 etc.) the
class has sprites for. Cells beyond this row index fall through to vanilla
sprite assignment.

```json
"clothing_standard": {
  "max_row": 4,
  "phase_1": { ... },
  "phase_2": { ... }
}
```

Row index is computed as `h_type - spr_row_pos - 1`. If this exceeds
`max_row`, the GNX is_special path is skipped.

### is_special frame counts

`is_special` classes use `skin = -1` (single skin variant), so their frame
counts differ from standard 3-skin classes:

| Animation | Standard (3 skins) | is_special (1 skin) |
|-----------|-------------------|---------------------|
| Standard idle/start | 90 (3x30) | 30 (1x30) |
| Standard loop | 225 (3x75) | 75 (1x75) |
| Big start | 36 (3x12) | 12 (1x12) |
| Big idle | 48 (3x16) | 16 (1x16) |
| Big loop | 105 (3x35) | 35 (1x35) |
| Tent idle | 42 (3x14) | 14 (1x14) |
| Tent loop | 105 (3x35) | 35 (1x35) |

For big cells, breast/leg sprites are 2x the head frame count (doubled for
the two sub-phases packed into one strip). E.g. big_start head = 12 frames,
big_start breast/leg = 24 frames.

Clothing overlay sprites (`_c` suffix) always match the head frame count
(not the doubled count).

### gb1_breast_d2

Optional per-class breast sprite for the G.BANG 1 cell's second draw phase.
Vanilla has per-class variants for special classes (cow, nyx, morrigan,
lilith). Modded classes without this field fall back to the generic
`spr_slot[2][1]` breast.

```json
"gb1_breast_d2": "gnx:gb1_breast"
```

Declare the sprite in `sprites` and reference it here.

### mon_spr_overrides

Per-class overrides for monster/goblin sprites that are normally hardcoded per
vanilla class in the `switch (_class)` blocks. Covers 25 dispatch sites across
goblin, hobgoblin, and ogre interactions. Without these, modded classes (>= 14)
falling through vanilla switches get default goblin sprites.

```json
"mon_spr_overrides": {
  "patrol": "gnx:ogre_walk",
  "ogre_touch": "gnx:ogre_touch",
  "goblin_wall_touch_start": "gnx:gob_touch_start",
  "goblin_wall_touch_loop": "gnx:gob_touch_loop",
  "goblin_wall_enter_loop": "gnx:gob_enter_loop"
}
```

Declare sprites in `sprites` and reference them with `gnx:` keys.

**Goblin keys:**

| Key | Target | Cell |
|-----|--------|------|
| `goblin_drink_touch` | touch sprite | DRINK |
| `goblin_drink_draw` | draw loop sprite | DRINK (draw) |
| `goblin_gb1_body` | body_b | G.BANG 1 |
| `goblin_gb1_draw_body_b` | draw body alpha | G.BANG 1 (draw) |
| `goblin_gb1_draw_body_l` | draw body line | G.BANG 1 (draw) |
| `goblin_gb2_body` | body_b | G.BANG 2 |
| `goblin_gb2_enter` | enter sprite | G.BANG 2 |
| `goblin_gb3_hand` | hand_b | G.BANG 3 |
| `goblin_gb3_enter` | enter sprite | G.BANG 3 |
| `goblin_wall_touch_start` | touch | WALL start |
| `goblin_wall_touch_loop` | touch | WALL loop |
| `goblin_wall_enter_loop` | enter | WALL loop |
| `goblin_wall_touch_ej` | touch | WALL ej (fallback: `goblin_wall_touch_loop`) |
| `goblin_wall_enter_ej` | enter | WALL ej (fallback: `goblin_wall_enter_loop`) |
| `goblin_wall_touch_anal_start` | touch | WALL anal start |
| `goblin_wall_touch_anal_loop` | touch | WALL anal loop |
| `goblin_wall_enter_anal_loop` | enter | WALL anal loop |
| `goblin_wall_touch_anal_ej` | touch | WALL anal ej (fallback: `goblin_wall_touch_anal_loop`) |
| `goblin_wall_enter_anal_ej` | enter | WALL anal ej (fallback: `goblin_wall_enter_anal_loop`) |

**Hobgoblin keys:**

| Key | Target | Cell |
|-----|--------|------|
| `hobgoblin_gb1_body` | body_b | HOB G.BANG 1 |
| `hobgoblin_gb3_hand` | hand_b | HOB G.BANG 3 |
| `hobgoblin_gb3_enter` | enter | HOB G.BANG 3 |
| `hobgoblin_wall_body_start` | body_b | HOB WALL start |
| `hobgoblin_wall_hand_start` | hand_b | HOB WALL start |
| `hobgoblin_wall_touch_loop` | touch | HOB WALL loop |
| `hobgoblin_wall_enter_loop` | enter | HOB WALL loop |
| `hobgoblin_wall_touch_ej` | touch | HOB WALL ej (fallback: `hobgoblin_wall_touch_loop`) |
| `hobgoblin_wall_enter_ej` | enter | HOB WALL ej (fallback: `hobgoblin_wall_enter_loop`) |
| `hobgoblin_wall_touch_anal_loop` | touch | HOB WALL anal loop |
| `hobgoblin_wall_enter_anal_loop` | enter | HOB WALL anal loop |

**Ogre keys:**

| Key | Target | Cell |
|-----|--------|------|
| `ogre_wall_body_start` | body_b | OGRE WALL start |
| `ogre_wall_body_loop` | body_b | OGRE WALL loop |

**Pre-existing keys:**

| Key | Target | Cell | Notes |
|-----|--------|------|-------|
| `patrol` | patrol walk | DISPLAY_B | 8 frames, 115x115, origin 55x114 |
| `ogre_touch` | ogre touch | G.BANG 2 | 35 frames, origin 0x90 |

**Ej fallback chains:** ej touch/enter keys fall back to their loop counterparts
if not defined. Anal ej falls back to anal loop. This reduces the number of
required sprites for modders who don't need separate ej animations.

---

## 15. Tool System — tools.json

Mods can declare tool buttons, keybinds, and continuous effects in
`tools.json`. GNX renders a generic tool menu (Settings → DEBUG → mod
categories → action buttons) and dispatches actions. No mod-side GML needed.

Declare in `manifest.json`:

```json
{
  "tools": "tools.json"
}
```

GNX always injects a **DEBUG** entry into the settings window (Settings →
DEBUG), even with no mod `tools.json` loaded. It always contains a built-in
**GNX DEBUG** category with two framework toggles:

- **PERF LOG** — sets `gnx_perf_enabled`; logs draw-cull/fps stats every ~2s.
- **VERBOSE LOG** — sets `gnx_debug_verbose`; enables the high-frequency
  dispatch/drink/prop/pool traces in `gnx_debug.txt`. Turn this on to debug why
  a cell or class renders wrong (see the `[GNX] class_spr` trace). Toggling
  either always writes `[GNX-TOOL] set_var <key> = <v>` to `gnx_debug.txt`,
  which confirms the menu is dispatching clicks.

Any loaded mod's `tools.json` adds its own categories alongside GNX DEBUG.

Tools require `save_state` in the manifest for any toggle buttons (the
toggle key must exist in `save_state.fields`). The framework GNX DEBUG toggles
use in-memory state and are never persisted (they reset each session).

---

### tools.json structure

```json
{
  "categories": [
    {
      "label": "GENERAL",
      "buttons": [ ... ]
    }
  ],
  "keybinds": [ ... ]
}
```

Categories appear in the tool menu prefixed with the mod name (e.g.
`"my_mod: GENERAL"`). If only one mod has tools, the prefix is omitted.

---

### Button fields

```json
{
  "label": "Refill Mood",
  "actions": [
    {"type": "set_val", "key": "mood", "value": 100}
  ],
  "popup": "Mood refilled"
}
```

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `label` | string | yes | Button text |
| `actions` | array | yes | Action chain executed on click |
| `popup` | string | no | Toast popup after execution |
| `toggle` | string | no | If set: toggle button. Value = `save_state` key for on/off state |
| `undo_actions` | array | no | Actions when toggling OFF (requires `toggle`) |
| `undo_popup` | string | no | Popup when toggling OFF |
| `guard` | condition | no | Pre-check before executing. Same syntax as quest conditions |
| `guard_fail_popup` | string | no | Popup shown when guard fails |

### Toggle buttons

When `"toggle"` is present, the button alternates between ON and OFF.
State is stored in `save_state` and persists across saves.

```json
{
  "label": "Lock Mood",
  "toggle": "mood_locked",
  "actions": [
    {"type": "set_continuous", "key": "mood_lock", "value": true}
  ],
  "undo_actions": [
    {"type": "set_continuous", "key": "mood_lock", "value": false}
  ],
  "popup": "Mood locked at 100",
  "undo_popup": "Mood unlocked"
}
```

The `toggle` key (`"mood_locked"`) must exist in your manifest's
`save_state.fields`.

### Guard conditions

Same condition evaluator as quests (`state_equals`, `state_gte`,
`gold_gte`, etc.) plus tool-specific types:

| Type | Fields | Checks |
|------|--------|--------|
| `boss_locked` | `index` (0-5) | boss not yet unlocked |
| `boss_unlocked` | `index` (0-5) | boss already unlocked |
| `stage_undiscovered` | `stage` (0-3) | stage not yet discovered |
| `has_unit_slot` | (none) | at least one empty unit_list slot |
| `has_cage_space` | (none) | cage is not full |
| `on_screen` | `screen` ("raid_map"/"shop"/"trade") | player is on that screen |

If the guard fails, `guard_fail_popup` is shown with an error sound and
the button is not executed.

---

### Action types (38 total)

#### Resources (7)

| Type | Fields | Effect |
|------|--------|--------|
| `add_gold` | `amount` | adds gold (negative allowed, clamps to 0) |
| `add_food` | `amount` | adds food |
| `add_milk` | `rarity` (0-4 or -1=all), `amount` | adds milk items |
| `add_orbs` | `amount` | adds shrine orbs |
| `give_item` | `item_type`, `data`, `level` | creates a generic item |
| `give_blueprint` | `h_type` (int or string ref), `fragment` (bool) | complete blueprint (default) or single fragment |
| `give_prop` | `prop_id` | unlocks a decoration prop |

#### Monsters (5)

| Type | Fields | Effect |
|------|--------|--------|
| `spawn_mon` | `species` (0-3), `amount` | spawns troops for all 4 goblin classes |
| `set_troop_level` | `species` (0-3), `class` (0-3), `value` | sets goblin class level directly |
| `add_troop_exp` | `species` (0-3), `class` (0-3), `amount` | adds exp via vanilla levelup logic |
| `set_skill_level` | `species` (0-3), `class` (0-3), `value` | sets skill level directly |
| `set_troop_size` | `value` (0-7) | max troop size index (6=320 cap, 7=unlimited) |

Species: 0=goblin, 1=hobgoblin, 2=tentacle, 3=ogre.

#### Units (2)

| Type | Fields | Effect |
|------|--------|--------|
| `create_unit` | `class_id` (int or string ref), `level` | creates a human captive in unit_list |
| `create_unit_cage` | `class_id` (int or string ref), `level` | creates a human captive in the cage |

#### Unlocks (7)

| Type | Fields | Effect |
|------|--------|--------|
| `unlock_boss` | `index` (0-4) | unlocks a boss (guards against double-unlock) |
| `unlock_stage_next` | `stage` (0-3) | discovers stage or increments max level |
| `unlock_breeds` | (none) | unlocks all breeding tips |
| `unlock_cell` | `h_type` (int or string ref) | unlocks a cell in the build menu |
| `unlock_prop` | `prop_id` | unlocks a decoration prop |
| `unlock_raid` | (none) | enables the raid button |
| `unlock_all_cells` | (none) | unlocks all vanilla + GNX cells |

#### Environment (3)

| Type | Fields | Effect |
|------|--------|--------|
| `add_floor` | (none) | adds a new cave floor |
| `set_day` | `value` | sets the day counter |
| `add_day_time` | `amount` | advances the day timer |

#### Speed / Display (3)

| Type | Fields | Effect |
|------|--------|--------|
| `set_speed` | `target` ("world"/"cart"/"range"), `value` | sets speed or cell range |
| `swap_mouse` | (none) | swaps mouse button bindings |
| `show_debug_overlay` | `enable` (bool) | toggles GameMaker debug tools |

#### Generic setters (2)

| Type | Fields | Effect |
|------|--------|--------|
| `set_val` | `key`, `value` | sets `global.val.{key}`. Allowlisted keys only |
| `set_var` | `key`, `value` | sets `global.{key}`. Allowlisted keys only |

`set_val` allowlist: `mood`, `food`, `money`, `cart_spd`, `add_range`,
`day`, `day_timer`, `orb_num`, `sfx_vol`, `bgm_vol`, `alpha_type`,
`mon_alpha`, `crate_alpha_type`, `crate_alpha`, `show_head`, `ui_place`.

`set_var` allowlist: `w_spd`.

Unknown keys are logged and ignored.

#### Raid / Shop (3)

| Type | Fields | Effect |
|------|--------|--------|
| `reroll_shop` | (none) | re-rolls shop stock (no-op if not on shop screen) |
| `reroll_trade` | (none) | re-rolls trade stock (no-op if not on trade screen) |
| `reroll_encounters` | (none) | re-rolls current stage encounters (no-op if not on raid map) |

#### State / Meta (6)

| Type | Fields | Effect |
|------|--------|--------|
| `set_state` | `key`, `value` | sets a per-mod save state key |
| `set_continuous` | `key`, `enable` (bool) | registers/unregisters a continuous per-frame effect |
| `fire_event` | `event_id` (string or int) | fires a GNX event (string) or vanilla event (int) |
| `fire_trigger` | `hook` | force-evaluates GNX triggers for a hook |
| `popup` | `text` | shows a toast popup |
| `play_sfx` | `type` (1=click, 2=success) | plays a sound effect |

---

### Keybinds

Per-frame keyboard shortcuts checked in `obj_control_Step_0`.

```json
"keybinds": [
  {
    "key": "F10",
    "modifier": "none",
    "actions": [{"type": "popup", "text": "Debug!"}],
    "popup": "F10 pressed"
  },
  {
    "key": "0-9",
    "modifier": "none",
    "action_per_key": {"type": "set_speed", "target": "world", "value": "{key}"},
    "popup_template": "World speed = {key}"
  }
]
```

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `key` | string | yes | Key name (`"F1"`-`"F12"`, `"A"`-`"Z"`, `"0"`-`"9"`, `"space"`, `"tab"`, `"escape"`) or range (`"0-9"`) |
| `modifier` | string | no | `"none"` (default), `"shift"`, `"ctrl"`, `"alt"` |
| `actions` | array | yes* | Action chain for single-key binds |
| `action_per_key` | object | yes* | Template action for ranges. `{key}` is replaced with the pressed digit |
| `popup` | string | no | Toast on activation |
| `popup_template` | string | no | Template with `{key}` placeholder (for ranges) |

*One of `actions` or `action_per_key` required.

Keybinds are suppressed during transitions (`click_lock`, `trans_lock`,
`speed_lock`). Modifier `"none"` rejects the key if shift/ctrl/alt is held,
preventing overlap with modified bindings of the same key.

---

### Continuous effects

Per-frame effects registered via the `set_continuous` action type. Used for
behaviors that need to run every frame (e.g. mood lock).

| Key | Effect |
|-----|--------|
| `mood_lock` | sets `global.val.mood = 100` every frame |

The system is extensible: new keys map to new per-frame behaviors. Continuous
effects are cleared when the player disables the tool system.

---

### Full example

```json
{
  "categories": [
    {
      "label": "CHEATS",
      "buttons": [
        {
          "label": "+1000 Gold",
          "actions": [{"type": "add_gold", "amount": 1000}],
          "popup": "Added 1000 gold"
        },
        {
          "label": "Lock Mood",
          "toggle": "mood_locked",
          "actions": [{"type": "set_continuous", "key": "mood_lock", "value": true}],
          "undo_actions": [{"type": "set_continuous", "key": "mood_lock", "value": false}],
          "popup": "Mood locked",
          "undo_popup": "Mood unlocked"
        },
        {
          "label": "Unlock Hathor",
          "actions": [{"type": "unlock_boss", "index": 0}],
          "popup": "Unlocked Hathor",
          "guard": {"type": "boss_locked", "index": 0},
          "guard_fail_popup": "Already unlocked"
        }
      ]
    }
  ],
  "keybinds": [
    {
      "key": "0-9",
      "modifier": "none",
      "action_per_key": {"type": "set_speed", "target": "world", "value": "{key}"},
      "popup_template": "World speed = {key}"
    }
  ]
}
```

Manifest for this example:

```json
{
  "mod_id": "my_mod",
  "name": "My Mod",
  "version": "1.0.0",
  "compatible_game_versions": ["1.33"],
  "tools": "tools.json",
  "save_state": {
    "version": 1,
    "fields": {
      "mood_locked": 0
    }
  }
}
```

---

## 16. Sound System — sounds.json

Mods can add moan voices and h-scene SFX that load at runtime. Declare the file
in `manifest.json` (`"sounds": "sounds.json"`) and drop the audio in a `sounds/`
subfolder. When any loaded mod provides sounds, GNX adds a **SOUND** page to the
Settings menu (6 sliders: moan/plap/ej/bj volume + moan/orgasm frequency).

> **Audio format must be OGG Vorbis (`.ogg`).** Runtime loading uses
> `audio_create_stream`, which only accepts `.ogg` — `.wav` files fail silently
> (the clip loads as `-1`, the bank ends up empty, and nothing plays). Convert
> first, e.g. `ffmpeg -i in.wav -c:a libvorbis -q:a 5 out.ogg`.

```
my_mod/
  manifest.json          ← "sounds": "sounds.json"
  sounds.json
  sounds/
    soft_1.ogg
    orgasm_1.ogg
    ...
```

### sounds.json schema

```json
{
  "voice_banks": {
    "soft":  {"clips": ["soft_1.ogg", "soft_2.ogg"]},
    "loud":  {"clips": ["loud_1.ogg"]}
  },
  "sfx": {
    "orgasm":     ["orgasm_1.ogg"],
    "bj_slurp":   ["slurp.ogg"],
    "bj_gag":     ["gag.ogg"],
    "bj_moan":    ["bj_moan.ogg"],
    "bj_breathe": ["breathe.ogg"]
  },
  "voice_map": {
    "8":  {"bank": "soft", "pitch": 0.91},
    "13": {"bank": "loud", "pitch": 1.10}
  },
  "settings_defaults": {
    "moan_vol": 0.5, "moan_frq": 15, "orgasm_frq": 5,
    "plap_vol": 0.5, "ej_vol": 0.5, "bj_vol": 0.5
  }
}
```

### voice_banks

Named pools of moan clips. Each captive is assigned one bank; a random clip
plays as her moan. Bank names are auto-prefixed with the mod id internally
(`my_mod.soft`) so two mods can't collide. All values are filenames inside
`sounds/`.

Assignment order for a unit: `voice_map` (fixed per class) → the class's
`classes.json` `voice.bank` → a random bank. Units at **level 6 or 7** (captured
bosses) always get a random voice regardless of the maps.

### sfx pools

Global pools that all sound mods contribute to. Played during the relevant
h-scene beats:

| Pool | When |
|------|------|
| `orgasm` | climax on normal cells |
| `bj_slurp` / `bj_gag` | oral cells, non-moan beats |
| `bj_moan` | oral cells, moan beat |
| `bj_breathe` | oral cells, climax |

BJ pools fire on cells GNX recognizes as oral: vanilla h_types 6 and 18, plus
any custom cell whose `cells.json` sets `"sfx_type": "bj"`.

### voice_map (fixed voice for vanilla classes)

Maps a **vanilla** `class_id` (string key) to a fixed `{bank, pitch}`. Use this
to give named characters (Lilith, Nyx, Morrigan, etc.) a signature voice **without**
a `classes.json` override — overriding a vanilla class just to set a voice is
unnecessary here, and `voice_map` needs no class registration at all. `pitch` is
optional (default random 0.9–1.15).

### settings_defaults

Initial slider values, applied the first time a sound mod loads (first mod
wins). Volumes are 0.0–5.0 (shown as 0–500 %); frequencies are 0–100. Users can
change these in Settings → SOUND; their choices persist with the save.

### classes.json voice field

A mod class can pin its own voice inline instead of via `voice_map`:

```json
"voice": {"bank": "soft", "pitch": 1.0}
```

`bank` refers to a voice bank from any loaded `sounds.json` (prefixed with this
mod's id). See [§3 Core fields](#core-fields).

### cells.json sfx_type

Mark a custom cell as an oral cell so the BJ sfx pools fire on it:

```json
"sfx_type": "bj"
```

Add it alongside the cell's other top-level fields in `cells.json`.
