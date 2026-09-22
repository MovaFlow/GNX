# Changelog

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

- Fixed invisible goblins on pleasure and tittyfuck cells — the last goblin wasn't drawing. Touched `s_mon_data.gml`, `obj_mon_Draw_0.gml`, and several sprite dispatch/draw files.
- Uninitialized `spr_data` on modded cells was causing fallback to wrong sprites.
- Missing `start_frame` defaults for multi-phase cells — animation was starting at frame 0.
- Unit removal on cells with 2+ monsters wasn't cleaning up all slots.

### Documentation

- Modding reference updated: multi-monster cells, tower boss condition (new section 14), locked cells, by_class/by_mon_type overrides, per-placement sprites, required_class arrays.
- Tutorial updated with tower boss, locked cells, and multi-monster cell examples.
- Example mod updated: new DOUBLE PIT multi-monster cell, locked SIREN POOL, tower_boss_condition on SIREN class, by_class/by_mon_type on RITUAL cell.

## v1.4.2

**Game version:** 1.38

### Bug Fixes

- **Atlas packer: wrong frame counts** — the packer looked for `"path"` in classes.json but GNX uses `"strip"`, causing every sprite to fall through to heuristic frame-count inference. Most multi-frame strips got wrong counts, producing misaligned frames, wrong cell types, and skin-tone cycling in atlas mode.
- **Atlas packer: trailing comma tolerance** — classes.json files with trailing commas (valid in JS, not JSON) caused a silent parse failure, compounding the frame-count bug.
- **Atlas packer: missing sprite origins** — the packer did not read `xorig`/`yorig` from classes.json, so all atlas sprites rendered with (0,0) origin instead of their declared offsets (typically bottom-aligned). Origins are now written into uv.json and applied at load time.
- **Atlas runtime: origin fallback** — if an atlas SprRef has no origin but the caller's JSON declares one, the resolver now applies it. Covers atlases packed before the origin fix.

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
