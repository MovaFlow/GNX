# Changelog

## v1.3.14 — Rebase to vanilla 1.38

**Game version:** 1.38 (rebased from 1.33)

### New Features

- **Custom Decorative Props** (`props.json`): mods can now add custom props to the edit-mode menu with custom sprites, placement offsets, random flip, and per-group positioning (top/mid/bot). Full save/load support with orphan sanitize on mod removal. Test T59 validates prop registry at boot.

- **Custom Birth Sprites** (`birth_spr` in `classes.json`): modded classes can define per-cell-type, per-species infant/birth prop sprites. Supports birth_1, birth_2, bind, tent walls, and giant cells. Test T58 validates birth sprite resolution at boot.

### Bug Fixes

- **SprRef/Atlas draw regression** (Bug #7/#9): restored `gnx_draw_sprite_ext` wrappers on all registry-sourced draw calls across `s_mon_draw.gml`, `s_slot_draw.gml`, `s_unit_head_draw.gml`, `s_raid_draw.gml`. Restored `gnx_sprite_get_number/width/height` query wrappers in `s_slot_data.gml`, `s_slot_function.gml`, `s_button_activate.gml`, `s_slot_windows.gml`. Fixes invisible sprites when 4+ mods loaded in atlas mode.

- **Hand position regression** (Bug #10): fixed by the `sprite_get_number` → `gnx_sprite_get_number` restoration in Bug #17. Custom `hand_x`/`hand_y` values now apply correctly.

- **Birth sprite regression** (Bug #17): 12x `sprite_get_number` → `gnx_sprite_get_number` in `s_slot_draw.gml` (hand sprites on all cells). Added `scr_draw_prop_infant_gnx` for SprRef-aware infant prop rendering.

### Documentation Fixes

- Fixed `cells.json` schema errors: `"data"` → `"physical"`, `"hand_frame"` → `"hand_frames"`, `{ "1": [...] }` → `{ "frame_1": [...] }` in modder guide and schema docs.
- Added `props.json` schema documentation.
- Added `birth_spr` documentation to `classes.json` schema.

### Files Changed

| File | Changes |
|------|---------|
| `s_initials.gml` | prop_registry init, hash, register, load, apply/migrate unlocks, T58+T59 tests, birth_spr loader |
| `s_slot_prop.gml` | New file (vanilla 1.38 + GNX patches): custom prop default case, `scr_draw_gnx_prop`, birth sprite dispatch, `scr_draw_prop_infant_gnx` |
| `s_slot_draw.gml` | 12x `sprite_get_number` → `gnx_sprite_get_number` |
| `s_mon_draw.gml` | 26x `draw_sprite_ext` → `gnx_draw_sprite_ext` on `_mon_spr.*` |
| `s_unit_head_draw.gml` | `gnx_draw_sprite_ext` on icon sprites |
| `s_raid_draw.gml` | `gnx_draw_sprite_ext` on `_gnx_icon` |
| `s_slot_data.gml` | 1x `sprite_get_number` → `gnx_sprite_get_number` |
| `s_slot_function.gml` | 1x `sprite_get_number` → `gnx_sprite_get_number` |
| `s_button_activate.gml` | 3x `sprite_get_number` → `gnx_sprite_get_number` |
| `s_slot_windows.gml` | 2x `sprite_get_width/height` → `gnx_sprite_get_width/height` |
| `s_button_text.gml` | `scr_set_prop_text` GNX hook, `scr_lang_prop_text` guard |
| `s_patch_updates.gml` | Orphaned prop sanitize, prop unlock apply/migrate in post |
