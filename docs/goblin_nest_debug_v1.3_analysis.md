# Goblin Nest Debug v1.3 — Mod Analysis

Source: `C:\Users\gbichon\Downloads\Goblin Nest Debug v1.3\` (`mod_config.json` + `data.g3mpatch`).
Author: Radeonix. Declared for `game_version: "1.33"`.

## 1. What kind of mod this is

This is **not a GNX mod**. It's a binary patch built with a third-party tool called
**G3MTool** (per `g3mpatch.json`, `tool.name = "G3MTool"`, `tool.version = "1.0.0"`).

`data.g3mpatch` is a zip archive (`g3mpatch.json` + decompiled `CodeEntries/*.gml` +
`.asm`) that a G3M-compatible mod manager applies by directly overwriting **17 whole
GameMaker code entries (scripts)** in `data.win`, byte for byte. There is no JSON
schema, no manifest-driven registry, no hash IDs — it's a full script replacement,
conceptually the opposite approach from GNX (which hooks small blocks into vanilla
scripts and drives content from JSON).

The 17 replaced scripts (`g3mpatch.json` → `resources.CodeEntries.changed`):

```
s_button_text, s_noti_button, s_shop_function, s_pop_up, s_trade_function,
s_mon_remove, s_slot_windows, s_window_alpha, s_mood, s_button_activate,
s_raid_map_button, s_dialog, s_initials, s_mouse_action, s_quest_function,
s_raid_encounter, s_raid_function
```

## 2. Critical finding: this patch is built from vanilla, with zero GNX awareness

`grep -i "gnx"` across all 17 extracted `.gml` files returns **0 matches**. Confirmed
directly by comparing function counts: GNX's `s_initials.gml` defines 61 functions,
28 of them `scr_gnx_*` (mod loader, registries, quest system, encounter pools, sanitize
hooks — effectively the entire GNX framework). The debug mod's `s_initials.gml`
defines **exactly 1 function** (`scr_create_initials`). Every `scr_gnx_*` function is
gone.

The same pattern shows up via token-diff (identifiers present in the GNX baseline but
absent from the mod's replacement) in the other overlapping files:

| File | GNX-only identifiers missing from the debug mod's version |
|---|---|
| `s_mon_remove` | `follow`, `wander`, `DRINK_REDISPATCH`, `GNX_LOG` (the teleport-on-drink-removal bugfix from CLAUDE.md is gone) |
| `s_raid_encounter` | `gnx_pool_pick`, `_gnx_picked`, `max_per_encounter`, `ap_override` |
| `s_raid_function` | `scr_gnx_check_post_raid_escape`, `scr_gnx_check_triggers`, `scr_gnx_check_quest_completion`, `post_raid_win` |
| `s_slot_windows` | `cell_registry`, `range_draw_func` (physical cell extension) |
| `s_trade_function` | `gnx_trade_list`, `_gnx_pool` (GNX class injection into the trader) |
| `s_button_text` | `cell_registry`, `gnx_price`, `gnx_spawn_info`, `gnx_code_text` (GNX cell tooltip/price lookup) |

**Consequence:** applying this g3mpatch on top of a GNX-modded install replaces these
17 scripts with vanilla-plus-debug-menu versions, deleting the entire GNX framework
and every GNX hook in the other 6 files. Files GNX also touches but that this patch
does *not* replace (`s_unit_data`, `s_mon_data`, `s_slot_data`, `s_save_load`,
`s_patch_updates`, `obj_control_Step_0`, `obj_window_Draw_0/64`, etc.) still call
`scr_gnx_*` functions that would no longer exist — e.g. `obj_control_Step_0` calls
`scr_gnx_check_quest_completion` every frame. That is an undefined-function call in
GameMaker, i.e. a near-certain crash or broken save the moment any of those hooks
fire. **This mod and GNX are not compatible as-is; do not apply this patch over a
GNX install without stripping GNX's own dependency on the 17 replaced scripts first,
or rebuilding the patch against the GNX-modified source.**

## 3. Feature list (vanilla base + this patch)

Entry point: a new oval icon button (`interact_type 5010`) added to the standard
options/settings window (`scr_create_alpha_window`, `s_window_alpha.gml`). Clicking
it opens a new **DEBUG** tab window with 4 categories:

- **GENERAL**
- **SPAWN**
- **UNLOCK**
- **Speeds**
- (+ BACK)

### GENERAL
| Button | Effect |
|---|---|
| Lock Mood | Toggles `global.mood_lock5001`; while on, `scr_mood_value_set` (patched in `s_mood.gml`) forces `global.val.mood = 100` on every call instead of applying normal gain/decay |
| Refill Mood | One-shot: `global.val.mood = 100` |
| :) | Swaps `global.val.camera_click` and `global.val.select_click` (swaps mouse button bindings) and, as a side effect, also sets `global.val.add_range = 10` |
| Debug Logs | Toggles `global.debug5001_overlay`; turning it on calls `show_debug_log(true)`; turning it off calls `show_debug_overlay(false)` — the on/off calls target two different GameMaker debug features (overlay vs. log), so the toggle doesn't cleanly control one thing |
| Nothing | Placeholder — shows "This button currently does nothing" |

The GENERAL category only ever creates 5 button instances (`_num = 5` in
`s_button_activate.gml`, button_num 0–4), but the `case 5001` handler's inner switch
on `button_num` also defines cases 5 through 11. Since no button instance with those
numbers is ever created for this category, they're **unreachable dead code** through
normal play, not a secret menu — but worth flagging since case 5's body is live logic,
not a stub: `scr_create_unit_base(13, 5)` then `ds_list_set(global.unit_list, 1, _unit)`,
i.e. it would spawn a level-5 class-13 (Princess, the special class added in v1.33)
unit and force it into `unit_list` slot 1 if it were ever triggered. Cases 6–11 are
empty. This is very likely leftover code from an earlier layout that had more buttons.

### SPAWN
Adds 100 food, 1000 gold, spawns goblins/hobgoblins/tentacles/orcs, adds a cave floor,
or adds milk — each (except food/gold/floor) opens a second submenu to pick a
quantity: **0.5 / 1 / 5 / 10 / 25 / 50** (0.5 is rejected for units with a
"can't make half a goblin" popup, but is valid for milk).

### UNLOCK
Unlocks each boss (Hathor, Nyx, Selene, Morrigan, Lillith+Tower) by clearing the
relevant `global.unlock.boss[n]` slot, with a guard against double-unlocking.
Also: unlock next Village/Mountain/Forest/Castle level, force-unlock all breeding
tips (`global.val.br_unlock` populated directly), "All Cells" (labelled TODO — not
implemented), and a **CUSTOM** submenu with a single "Frieren" entry that checks
`variable_struct_exists(global.unlock, "frieren")` before unlocking — i.e. it's
aware of *a* Frieren-unlock mod's global struct specifically (not GNX in general),
and shows "Frieren mod is NOT currently loaded" if that struct isn't present.

### Speeds
Small window showing/editing three live values with +/- arrow buttons:
`global.w_spd` (world speed, 0–10), `global.val.cart_spd` (cart/trader speed, 0–10),
`global.val.add_range` (build/cell range extension, 0–20).

### Keyboard shortcuts (`s_mouse_action.gml`)
- **F10**: shows a "Open Debug menu" popup — but does **not** actually create the
  debug window (no window-creation call follows it in the patched code). Looks like
  an unfinished/vestigial hotkey.
- **0–9** (no modifier): sets `global.w_spd` directly to that number
- **Shift+0–9**: sets `global.val.cart_spd`
- **Ctrl+0–9**: sets `global.val.add_range`
- **Easter egg**: setting world speed, cart speed, and cell range all to exactly 6
  fires a one-time hidden event (`scr_add_event(5001, false)`) that queues a Lilith
  dialog line (`scr_dia_lilith_debug5001_Egg` in `s_dialog.gml`) joking about the
  player "flirting" with her via the number 6.

### Floor tools (slot right-click / modify menu, `s_button_activate.gml` case
`UnknownEnum.Value_0`, new button_num 2/3/4; labels "COPY"/"PASTE"/"CLEAR" added in
`s_button_text.gml`)
- **Copy Floor**: stores the clicked cell's floor index in `global.copy_floor_source5001`
- **Paste Floor**: replaces every cell on the target floor with a copy of the source
  floor's layout (cells, pillars, props, `h_type`). Refunds 80% of each destroyed
  cell/pillar's price first. Displaced units are pushed back into the prison list;
  aborts with a popup if there isn't enough free prison space, or if source == destination
- **Clear/Empty Floor**: destroys every cell on the floor (80% refund each) and
  rebuilds it back down to the two starting cells

### Cell management
- **Remove Pillar** (`interact_type 5200`): new button on tent-type cells (`slot_type`
  4/5) next to the existing swap button, in the cell selection window
  (`s_slot_windows.gml`). Deletes a pillar/divider and shifts subsequent cells to
  close the gap; refuses if it's the floor's last remaining pillar.
- Also folded into the same code path: a fix to `scr_check_between_base`'s call site
  in `s_button_activate.gml` — it now checks `ds_list_size(...) > (_pos + 2)` and that
  both neighboring slots have `between_type` before calling `scr_check_between_base`,
  guarding against an out-of-bounds list read when a cell is placed near the end of a
  floor. Leftover debug popups (`"pos + 2 = ..."`, `"array length = ..."`) are still
  printed unconditionally at that spot — looks like debug instrumentation the author
  forgot to remove.

### One-off refresh buttons (new oval buttons, one per screen)
- **Raid map** (`interact_type 5100`, added in `s_raid_map_button.gml`): re-rolls the
  current stage's encounter data (`scr_set_stage_data`)
- **Shop** (`interact_type 5101`, added in `s_shop_function.gml`): re-rolls shop stock
  (`scr_choose_shop_item`) — labelled "Booped the Merchant"
- **Trader** (`interact_type 5102`, added in `s_trade_function.gml`): re-rolls trade
  stock (`scr_choose_trade_item`)

### Logging
`log5001(msg)` (`s_window_alpha.gml`) writes timestamped lines to
`Debug_Logs/<timestamped filename>.txt` under `working_directory` (creates the folder
on first use) and echoes to `show_debug_message`. Called extensively from the floor
copy/paste code and pillar checks.

At game launch, `scr_create_initials()` now dumps **every global variable** (via
`variable_instance_get_names(global)`, plus every field of `global.val` individually)
into that same log file — a full state snapshot on every boot.

## 4. Quirks / apparent bugs noticed in the mod itself

- F10 shows a popup claiming to open the debug menu but doesn't open anything.
- The ":)" GENERAL button's logic is inconsistent with its neighbors: it flips
  `debug5001_overlay` but calls `show_debug_overlay(false)` in the "enabling" branch
  and `show_debug_log(true)` in the other — reads like swapped/leftover logic.
- "All Cells" unlock is explicitly labelled TODO and does nothing.
- Debug popups ("pos + 2 = ...", "array length = ...") fire unconditionally in the
  pillar-check code path, not gated behind any debug toggle — cosmetic noise, not
  a correctness issue.

## 5. Bottom line for this project

Nothing here should be merged into `E:\GNX_Work_folder\GNX\gml\`. If you want the
QoL features (floor copy/paste, speed hotkeys, spawn/unlock cheats) available
alongside GNX, they'd need to be re-implemented as hooks in the GNX-modified
versions of the same 17 scripts — applying this patch as-is on a GNX build will
strip GNX out of those files and very likely crash on first GNX-dependent call.
