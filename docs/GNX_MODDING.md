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

---

## 1. Mod Folder Structure

```
<game folder>/
  GNX_mods/
    my_mod/
      manifest.json
      classes.json     ← optional
      cells.json       ← optional
      strips/          ← packed sprite strips
        spr_h_myclass_idle_head.png
        ...
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

| Field | Required | Notes |
|-------|----------|-------|
| `mod_id` | yes | Must match folder name |
| `name` | yes | Display name |
| `version` | yes | Semver string |
| `compatible_game_versions` | yes | Array of game version strings. Must include the running game version or the mod is silently skipped |
| `classes` | no | Path relative to mod folder; omit if no classes |
| `cells` | no | Path relative to mod folder; omit if no cells |

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

Vanilla ID map:
```
0=Peasant  1=Cleric   2=Knight   3=Ranger   4=Nun     5=Samurai
6=Mage     7=Warrior  8=Lilith   9=Cow     10=Nyx    11=Giant
12=Morrigan 13=Cat    14+ = mod range
```

### override

`true` = replace an existing vanilla class's sprites. The class_id must match
a vanilla class (0–13). Stats fields (`preg_c_override` etc.) still apply.
Use this to reskin Peasant, Cleric, etc.

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
| `preg_mon_type_override` | int | 0 | Monster type for offspring: 0=goblin, 1=hobgoblin, 2=ogre |
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
| `category` | `"breed"`, `"utility"`, or `"pleasure"` |
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

> **Note:** `hand_frames` only supports `frame_1`/`frame_2`/`frame_3` at
> runtime. A 4th frame variant (`hand_frame_4`, used by vanilla T.WALL1/2) is
> not currently readable from `cells.json`.

---

## 8. Cell Sprite Blocks

### human_spr

Defines how the human character is drawn in this cell.

```json
"human_spr": {
  "mode": "base+class",
  "base_body": "standard"
}
```

| `mode` | Description |
|--------|-------------|
| `"base+class"` | Standard: draws base body with class-specific clothing on top |
| `"class_only"` | Draws only the class clothing, no base body underneath |

`base_body`: `"standard"` for normal cells, `"big"` for large cells.

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

| Field | Notes |
|-------|-------|
| `stage` | Raid stage index (0 = earliest) |
| `level` | Encounter level within the stage |
| `weight` | Relative spawn weight. Higher = appears more often. Vanilla classes use 100–200 |
| `min_lvl` | Minimum unit level for this entry |
| `max_lvl` | Maximum unit level for this entry |

Multiple entries can be provided to cover different stages/levels.

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

### birth_classes

```json
"birth_classes": [0, 0, 0, 0]
```

| Field | Type | Notes |
|-------|------|-------|
| `birth_classes` | int[4] | Maps this class to a vanilla `mon_class` (0-3, by `mon_type`) when it gives birth. Index = `mon_type` (0=goblin, 1=hobgoblin, 2=ogre, 3=?). Recommended for class_id ≥ 14 if the class can become pregnant |

Used by `s_slot_data.gml` (`scr_set_unit_*` birth logic): when a modded unit
(`class_id >= 14`) gives birth, `_mon_class = birth_classes[_mon_type]` picks
which vanilla breeder-window slot the offspring is grouped under, and the
unit's `class_id` is registered into `global.gnx_br_unlock[_mon_type][_mon_class]`
so its portrait cycles into that window (`s_mon_head_draw.gml`).

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
