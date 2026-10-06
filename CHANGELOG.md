# Changelog

## v1.4.7

**Game version:** 1.39

### New Features

- **`only_listed_cells` class constraint**: classes declaring `"only_listed_cells": true` in `classes.json` can only enter cells whose `required_class` includes them. Enforced across all slot availability checks, carry range checks, and type checks.
- **`clothing_giant` tier**: new clothing sprite set for GIANT cells (h_type 37), alongside the existing `clothing_standard`, `clothing_big`, and `clothing_tent` tiers. Declare `clothing_giant` in `classes.json` with the same phase/sprite structure as the other tiers.
- **Folder sprite loading**: `gnx_resolve_sprite` now supports `"mode": "folder"` to load numbered PNGs from a subdirectory as animation frames, sorted numerically. Also adds `"origin_from"` to copy origin from a vanilla sprite, and `"from_game"` to reference sprites already in data.win.

### Bug Fixes

- Fixed transfer cells not working after loading a save. Carry state (`char_state`, `h_step`) and carry/load flags are now reset on load so the cell re-dispatches transfers from scratch.
- Fixed "only 1 hobgoblin" bug on transfer cells after load. Saved `h_step=1` skipped the load phase that spawns the second hobgoblin.
- Added `instance_exists()` guards on all 5 sites that dereference `carry_start_id` / `carry_end_id` without checking the instance is alive (s_mouse_action, s_slot_function x2, s_mon_remove, s_mon_draw).
- Fixed two vanilla copy-paste bugs in `scr_occupy_slot` case 17: the `carry_end_id` cleanup block wrote to `carry_start_id.slot_data.carry` instead of `carry_end_id`, leaving the end cell's carry flag stuck.
- Added carry/load flag sweep on save load. Clears orphaned flags on cells that no hobgoblin actually references.
- Added `gnx_slot_purge_dead_refs()` to clean dead monster refs from cell placement and unit lists. Runs on cell wake-up from off-screen sleep, unit removal, and monster arrival.
- Fixed `scr_slot_carry_idle` milk class check: any class with `scr_unit == 0` now qualifies, not just hardcoded class 9.
- Relaxed T16 test so classes providing `clothing_giant` instead of `clothing_standard` pass mod class validation.

## v1.4.6

**Game version:** 1.39

### New Features

- **XL Cell** (slot type 6): 150px wide cell with dedicated background sprites. Build menu adds a 5th option "XL CELL" (500 gold). Clicking an empty XL cell opens the `xl_breed` category list; occupied XL cells open the cell mod window. Background cycles between default, pillar, rock, and brick styles. Mod cells opt in via `"category": "xl_breed"` in `cells.json`.
- **Shrine monster sprite overrides**: goblin, hobgoblin and ogre sprites (body, hand, pen, outlines, touch, enter) on the shrine cell can be replaced per class via `mon_spr_overrides` in `classes.json`. Shrine background, dirt and sign are also replaceable per class (`shrine_bg`, `shrine_dirt`, `shrine_sign`).
- **Chains ogre body override**: the ogre body on the chains cell can be replaced per class (`ogre_chain_body` in `mon_spr_overrides`).
- **Cell patch merging**: multiple mods can now patch the same vanilla cell. `required_class` and `by_class` entries merge instead of being overwritten; the later-loaded mod wins only for classes it explicitly defines. A phase without `spr_array` keeps existing arrays.

### Performance

- Camera Y culling on `obj_slot` Draw and Step events — skips all processing for off-screen slots. On a 74-floor save (4883 slots), only ~100 slots per frame run draw/step logic instead of all 4883.
- Camera Y culling on `obj_mon` Draw and Step events — same treatment for ~880 monster instances.
- Camera Y culling on `obj_button` Draw and Step events — 1625 world-space buttons culled, GUI buttons unaffected.
- Camera Y culling on `obj_empty` Draw and Step events — ~250 empty slot instances culled.
- Camera Y culling on five per-frame `with()` loops in `scr_main_end_step` (button follow, mon follow, tent position, prop position, slot cleanup).
- Throttled ambient speaker scan (`scr_gnx_goblin_visible_speakers`) from every frame to every 15 frames.
- Replaced vanilla zoom-based 4-condition bounds check with fast Y check in slot and mon draw.
- Perf counters moved from individual draw functions to Draw_0 event level for accurate culling stats.
- Net result on a 74-floor endless tower save: **12 FPS → 35-38 FPS** (1080 Ti / i7 / 16GB).

### Bug Fixes

- Fixed crash when loading a save with a goblin mid-drink: `spr_data` is now restored for every `mon_step` value (added `default` case to the restore switch).
- Fixed crash when clicking a quest notification whose event lost its dialog (e.g. after editing `quests.json` between saving and loading). Silent notifications are now skipped during restore, and `scr_gnx_dialog_render` exits cleanly when the event has no `dialog` field.
- Fixed watchdog spamming hundreds of log lines every 60 frames for walking/wandering monsters. Walking monsters (state 5/6) legitimately use `draw_self()` and no longer trigger the repair loop.
- Fixed `instance_exists(-1)` bug in watchdog and monster draw code. In GameMaker, `instance_exists(-1)` returns true (means "all instances"), so slot_id must be checked for -1 before calling `instance_exists()`.
- Fixed crash in tent draw function when `mon_data.h_type` is not set on orphaned tent monsters.
- Fixed monsters walking in place after loading a save. Post-sanitize sweep now snaps walk/wander-state monsters within 10px of their slot to the slot position and sets them to hold state.
- Fixed crash when toggling UI debug unit trace on monsters without `slot_width` in their `spr_data`.
- Shrine touch/enter sprites are no longer drawn for `is_special` classes without their own override (they picked the wrong frame because of `skin = -1`).
- Lilith's vanilla breast overlay on shrine is now drawn only for class 8.
- Fixed false `required_class ref 'N' not found` warning on cell patches. Class numbers are stored as numbers, no longer looked up as names.
- Fixed scrollbar not rendering: `instance_exists(obj_window)` always returned true because the raid window singleton is permanently alive. Removed the window check; scrollbar now shows whenever the nest is taller than the viewport.
- Fixed scrollbar color leak: `scr_gnx_draw_scrollbar` set brown `draw_set_color` without resetting to `c_white`, causing gold amounts, unit names, and other text to render in wrong color.
- Fixed carry/transfer cell regression: watchdog was detaching carry hobgoblins (states 7/8/9) and repairing walking goblins (state 0), breaking carry animations and causing invisible/teleporting goblins.
- Fixed crash in `scr_mon_state_carry_idle` when the lead hobgoblin was destroyed mid-carry (`mon_placement[0]` held a dead instance ref).
- Watchdog hardened: simplified skip logic from fragile state skip-list to `mon_state != 1` (only state 1 goblins need repair/detach). Added `continue` after DETACH to prevent cascade into later checks.
- Watchdog moved from per-frame (every 60 frames) to once-after-load in `scr_patch_update_post` — the only time broken draw states exist is right after save restore.
- Fixed dead watchdog Block 4: was checking `slot_data.unit_data` (never exists) instead of instance-level `unit_data` on `obj_slot`.
- Fixed tool action crash when spawning modded classes: `int64` hash IDs from `gnx_class_name_to_id` caused type mismatch. Now cast to `real()`.
- Tool `spawn_unit` action now accepts string class refs (`"mod_name.ClassName"`) in addition to numeric IDs.
- Fixed `class_name` display in tool/debug UI: resolves numeric class_id to registry name.
- Tool actions on unknown class IDs now show an error popup instead of crashing silently.
- Added `mod_name` field to cell and class registry entries for better debug traceability.
- Fixed `mon_step` save guard: drink-state goblins no longer crash on load when `mon_step` has an unrecognized value.
- Fixed crash on malformed atlas `uv.json`: `json_parse` in `gnx_load_atlas_mod` now wrapped in try/catch with logged error, preventing crash on corrupted mod atlases.
- Fixed potential crash in `scr_unit_removal` for multi-monster cell (h_type 36): `mon_placement` swap now guards each slot access with `!= -1` check before accessing `.mon_data`.
- Fixed `scr_unit_removal` missing `break` after `h_unit_list` placement match — loop continued iterating unnecessarily after finding the target.
- Fixed `scr_set_mon_spr_data` crash when `anim_struct` is uninitialized (-1): now falls back to `frame_c = 0`.
- Added `default: return` to `scr_delete_save` switch to guard against out-of-range save slot index.
- Removed dead `var _spr = spr_idle` assignment in save-load hobgoblin state restore.

## v1.4.5

**Game version:** 1.39

### New Features

- **Multi-monster cells**: cells can hold 2+ goblins. Set `max_mon_num` in the `physical` block, use `mon_placements` to control which species goes in each slot, and `mon_positions` to offset draw positions. Per-slot sprite overrides via `mon_spr_p1`/`mon_spr_p2`/etc.
- Modded classes can now appear as **tower bosses**. Add a `tower_boss_condition` to `classes.json` (state_equals, has_unit, quest_complete, etc.) and the class enters both floor 1 and endless tower encounter pools.
- **Locked cells**: set `"locked": true` in `cells.json` to keep a cell out of the build menu until an `unlock_cell` quest side effect grants it.
- Fixed-mode cells now support `by_class` and `by_mon_type` in phase sprite blocks, overriding the `spr_array`/`spr_c_array` when a specific class or monster type occupies the cell. Nest `by_mon_type` inside `by_class` for class + monster combos.
- `required_class` accepts an array of class refs, so one cell can allow multiple specific classes. Also fixes vanilla special cell class restrictions not recognising modded classes.
- `compatible_game_versions` now uses intersection matching against `gnx_accepted_versions`. Mods targeting `"1.39"` keep working on future 1.39.x patches without manifest updates.

### Bug Fixes

- Fixed invisible goblins on pleasure and tittyfuck cells: the last goblin wasn't drawing. Touched `s_mon_data.gml`, `obj_mon_Draw_0.gml`, and several sprite dispatch/draw files.
- Uninitialized `spr_data` on modded cells was causing fallback to wrong sprites.
- Missing `start_frame` defaults for multi-phase cells. Animation started at frame 0.
- Unit removal on cells with 2+ monsters wasn't cleaning up all slots.

### Documentation

- Modding reference updated: multi-monster cells, tower boss condition (new section 14), locked cells, by_class/by_mon_type overrides, per-placement sprites, required_class arrays.
- Tutorial updated with tower boss, locked cells, and multi-monster cell examples.
- Example mod updated: new DOUBLE PIT multi-monster cell, locked SIREN POOL, tower_boss_condition on SIREN class, by_class/by_mon_type on RITUAL cell.

## v1.4.2

**Game version:** 1.38

### Bug Fixes

- **Atlas packer: wrong frame counts**: the packer looked for `"path"` in classes.json but GNX uses `"strip"`, causing every sprite to fall through to heuristic frame-count inference. Most multi-frame strips got wrong counts, producing misaligned frames, wrong cell types, and skin-tone cycling in atlas mode.
- **Atlas packer: trailing comma tolerance**: classes.json files with trailing commas (valid in JS, not JSON) caused a silent parse failure, compounding the frame-count bug.
- **Atlas packer: missing sprite origins**: the packer did not read `xorig`/`yorig` from classes.json, so all atlas sprites rendered with (0,0) origin instead of their declared offsets (typically bottom-aligned). Origins are now written into uv.json and applied at load time.
- **Atlas runtime: origin fallback**: if an atlas SprRef has no origin but the caller's JSON declares one, the resolver now applies it. Covers atlases packed before the origin fix.

### Tools

- Updated `gnx_atlas_pack.py` with all fixes above. Mods using atlas mode should re-pack with the updated tool.

## v1.4.1

**Game version:** 1.38 (rebased from 1.33)

Everything below is new since the last public release (v1.3.11, game 1.33).

### New Features

- **Rebased to game version 1.38**: full rebase of all 49 patched scripts from vanilla 1.33 to 1.38. All new vanilla content (cells, sprites, UI changes) is preserved. Existing mods only need to update `compatible_game_versions` in their manifest.

- **Standalone Installer**: GNX now ships as a single `.exe` that patches the game directly  - no mod manager, no downloads, no command line. Drop it next to `GoblinNest.exe` and run. Supports install, update-in-place (run a newer exe), restore/uninstall, and drag-and-drop mod `.zip` install. Based on fossil-delta binary patching (inspired by Jadwick's GBF).

- **Multi-Map Travel** (`map`, `map_button`, `map_start` in `manifest.json`): mods can declare a second map  - a fully independent dungeon the player travels to and from via a button on the gameplay screen. Each map has its own floor layout, cells, monsters, raid state, quests, and economy. State is frozen on departure and restored on return. Day counter is shared across all maps. First visit applies configurable starting state (floors, gold, food, mood, goblins). Deferred mod loading ensures map-specific content only loads when needed. Save/load fully supported with map label shown on save-select screen.

- **Custom Decorative Props** (`props.json`): mods can now add custom props to the edit-mode menu with custom sprites, placement offsets, random flip, and per-group positioning (top/mid/bot). Full save/load support with orphan sanitize on mod removal.

- **Custom Birth Sprites** (`birth_spr` in `classes.json`): modded classes can define per-cell-type, per-species infant/birth prop sprites. Supports birth_1, birth_2, bind, tent walls, and giant cells.

- **Unsaved Progress Warning**: "Return to Menu" now shows a confirmation dialog ("Unsaved progress will be lost!") before quitting to the menu.

- **Atlas Packing** (optional performance): texture atlas system (`gnx_atlas_pack.py`) packs sprite strips into large atlas PNGs, cutting texture pages from hundreds to single digits, VRAM by ~45%, and boot time from 94s to 1.8s. Fully backwards-compatible.

### Bug Fixes

- **SprRef/Atlas draw regression** (Bug #7/#9): fixed invisible sprites when 4+ mods loaded in atlas mode. Restored `gnx_draw_sprite_ext` wrappers on all registry-sourced draw calls.
- **Hand position regression** (Bug #10): custom `hand_x`/`hand_y` values now apply correctly.
- **Birth sprite regression** (Bug #17): SprRef-aware infant prop rendering via `scr_draw_prop_infant_gnx`.
- **Debug overlay removed**: disabled `show_debug_overlay(true)` that was causing the GameMaker debug menu bar and FPS counter to appear.

### Documentation

- Full modding reference updated for 1.38 (all JSON schemas, new sections for props, birth sprites, multi-map, atlas packing).
- Fixed `cells.json` schema errors in docs.
- Updated tutorial and example mod compatibility from 1.33 to 1.38.
- Updated README with standalone installer as recommended install path.
