# Changelog

## v1.4.6

**Game version:** 1.39

### New Features

- **XL Cell** (slot type 6): 150px wide cell with dedicated background sprites. Build menu adds a 5th option "XL CELL" (500 gold). Clicking an empty XL cell opens the `xl_breed` category list; occupied XL cells open the cell mod window. Background cycles between default, pillar, rock, and brick styles. Mod cells opt in via `"category": "xl_breed"` in `cells.json`.
- **Shrine monster sprite overrides**: goblin, hobgoblin and ogre sprites (body, hand, pen, outlines, touch, enter) on the shrine cell can be replaced per class via `mon_spr_overrides` in `classes.json`. Shrine background, dirt and sign are also replaceable per class (`shrine_bg`, `shrine_dirt`, `shrine_sign`).
- **Chains ogre body override**: the ogre body on the chains cell can be replaced per class (`ogre_chain_body` in `mon_spr_overrides`).
- **Cell patch merging**: multiple mods can now patch the same vanilla cell. `required_class` and `by_class` entries merge instead of being overwritten; the later-loaded mod wins only for classes it explicitly defines. A phase without `spr_array` keeps existing arrays.

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
