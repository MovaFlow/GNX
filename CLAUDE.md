Bash commands
Prefer these over defaults when available. Fall back silently if missing.
- Search content:`rg` over `grep`
- Find files: `fd` over `find`
- Never use `find -exec` or `xargs` chains when `fd -x` or `rg -l | xargs` would be clearer. Prefer readable pipelines.
- Structural/AST search: `ast-grep` (`sg`) for refactors and pattern-based code search, especially in TS/TSX
- JSON: `jq` for any parsing, filtering, or transformation in pipelines
- YAML/TOML: `yq`

Always remember that your cowork session has no virtualisation.
---

# GN Project — Working Memory

## What This Project Is
Modding a decompiled GameMaker dungeon management game. GML source is decompiled (enums as `UnknownEnum.Value_N`). Full architecture in the **gn-modding skill** — always load it before writing GML.

**Current phase:** Hash-based h_type for cells implemented ✅ (2026-06-17). `h_type` is now optional in `cells.json`; GNX assigns stable IDs [100–9999] via djb2 hash + linear probe. Build menu unlock arrays auto-migrated on save load via `scr_gnx_migrate_unlocks`. String-ref second pass implemented and verified ✅ (2026-06-17). Hash-based class_id auto-assignment implemented ✅ (2026-06-16). GNX dispatch testing complete (2026-06-08). All 35 sprite-dispatch cells verified ✅. Game updated to v1.33 (2026-06-10) — fully ported, 100% 1.33 compatible. Patcher is v1.0 full-file replacement: `patcher/gml/` contains 25 complete patched GML files imported wholesale by `install_foundation.csx`. (Patch-based v2 experiment abandoned 2026-06-16 — Underanalyzer decompiler format incompatibility.)

## Vanilla 1.33 Sync — 2026-06-10
Game updated 1.32 → 1.33. Diffed `v1.32-vanilla` tag against fresh 1.33 decompile
(`E:\SteamLibrary\steamapps\common\Goblin Nest\Code\`). 16 vanilla files changed + 1
new file (`s_set_language.gml`). Of these, 6 overlap with `patcher/gml/` (files the
patcher fully replaces). All 6 ported, in both GMS2 source and `patcher/gml/`.

**Ported (2026-06-10):**
| Patch note | Fix | File / location |
|---|---|---|
| "Fixed alt tab while holding cage units causing crash" | Added `instance_exists(obj_control.hold_id)` guard before `.drag_type` | `s_slot_function.gml`, `scr_check_type_n_preg` (~2811) and `scr_check_type_preg` (~2855). `scr_check_type_milk` (~2895) already had it. |
| "Fixed Hobgoblin haste skill desyncs raid bar if skill level drops after raid" | After haste/spd recalc, also recompute `raid_data.max_time` and reset `raid_data.time_left = max_time * 0.5` | `s_raid_function.gml`, ~line 300, in the `seq_id != -1` haste-recalc block. Also feeds the GNX `seq_id == -1` headless-raid `_arrived` check. |
| `global.val.version` bump | `1.32` → `1.33` | `s_initials.gml` (line 40) + `s_patch_updates.gml` (loop bounds `< 1.32` → `< 1.33`, lines 5 and 121). No new migration `case` needed (845-line block unchanged 1.32→1.33). |
| `scr_draw_highlight` rewrite ("Changed the way highlighting cells work to reduce vram usage, and better improve laptop experiences" / "Fixed cell highlighting not working when hovering on cells past 5 floors") | Surface+`gpu_set_fog` → `shader_set(sh_black)` + `shader_set_uniform_f(hl_set, -0.05)` + `script_execute(arg0, false)` + `shader_reset()`. Old surface was sized to `room_height` (broken past floor 5). | `s_slot_draw.gml` (in `patcher/gml/`), `scr_draw_highlight`. **Dependency check (no patcher change needed):** `hl_set` is an instance var set via `hl_set = shader_get_uniform(sh_black, "hl_col")` in `obj_interact_p_Create_0` and `obj_mon_Create_0` — both are vanilla 1.33 files OUTSIDE `patcher/gml/` scope, so the target 1.33 data.win already has `hl_set`/`sh_black` initialized natively. `obj_slot` (no own Create) and `obj_prop` (`event_inherited()`) inherit from `obj_interact_p`; `obj_mon` sets it directly. All 3 callers (`obj_slot_Draw_0`, `s_mon_draw` on obj_mon, `s_slot_prop` on obj_prop) covered. `script_execute(arg0, false)` retained as-is (matches vanilla 1.33 exactly; pre-existing GMS2-import concern, see table below). |
| `s_button_text.gml` full rebuild | Rebuilt from 1.33 decompile (humanized), incl. WALL1 label per-language switch collapsed to one line. GNX cell_registry name/price block re-inserted at top of `scr_h_slot_text_data`. | `s_button_text.gml` (in `patcher/gml/`), 4001 lines, 12 functions verified. |

**N/A — no action needed:**
| Item | Why |
|---|---|
| `s_set_language.gml` (new file) | New `scr_set_textbox_lang`/`scr_change_lang`, not referenced by any `patcher/gml/` file. Already present natively in 1.33 data.win; nothing for the patcher to replace. |

Other 1.33-changed files outside `patcher/gml/` scope (not audited beyond the
`hl_set` dependency check above): `s_dialog`, `s_guide`, `s_noti_button`,
`s_raid_cat`, `s_text_draw`, `s_textbox_function`, `s_window_alpha`, `obj_menu_Draw_0`.

**Gotcha found during 1.33 retest:** bumping `global.val.version` breaks existing mods
unless their `manifest.json` `compatible_game_versions` array is updated to include
the new version. `scr_gnx_load_mod` (`s_initials.gml` ~3445) does an exact string match
against `global.val.version` and `exit`s the whole mod load (no classes/cells
registered) on mismatch — silently, only logged as `[GNX] version mismatch: mod=X
game=Y`. If a save already has units of a class only defined by that mod, this then
crashes (`scr_set_patrol_spr_data` reads `arg0.leg` on an unregistered class struct →
"not set before reading it" on `obj_np` Step). Fixed for `test_mod` by adding `"1.33"`
to `compatible_game_versions`. **Any future game version bump must update every mod's
manifest the same way.**

## GMS2 Import Fixes (known issues)
| Issue | Fix |
|-------|-----|
| `script_execute(func)` silently fails | Replace with direct call `func()` — affects all object Draw/Step/Destroy events |
| Sizable window sprites render stretched instead of tiled | Enable Nine Slice in GMS2 sprite editor: 4px guides on all sides, mode = Repeat |
| File sandbox blocks external paths | `option_windows_disable_sandbox:true` in `options/windows/options_windows.yy` |

## Bug Fixes (2026-06-05)

| Bug | Root cause | Fix | File |
|-----|-----------|-----|------|
| Goblin teleports to cell after leaving DRINK | `s_main_room_step.gml` snaps x to `slot_id.x` every frame when `mon_data.follow=true`. After drink removal, `follow` stayed true and `slot_id` was changed to target cell by DRINK_REDISPATCH. | Added `mon_data.follow = false` in `scr_remove_mon` preamble (line ~510). | `s_mon_remove.gml` |
| Stool/prop missing on WALL1-2 non-anal scenes | GNX dispatch sets `_set=true` (overrides sprites), skipping vanilla `if(!_anal)` branch. But `slot_data.anal` could be true (shared flag from another goblin), blocking prop assignment even though GNX renders non-anal sprites. | Changed prop guard to `_skip_prop = _anal && !_set`: prop always assigned when GNX dispatches, since GNX has no anal variants. Also syncs prop removal when vanilla anal is active. | `s_mon_data.gml` |

## GNX Mods Path
- `global.gnx_mods_root = program_directory + "GNX_mods/"` — set at top of `scr_gnx_load_mods()` in `s_initials.gml`
- Mods are auto-discovered: any subfolder of `GNX_mods/` containing a `manifest.json` is loaded (alphabetical order, no index file)
- Dev mods live at `E:\Patcher TEST Folder\GNX_mods\test_mod\`
- GMS2 debug `working_directory` = `E:\GMS2-LTS2026\Temp\GMS2TEMP\goblin_nest_6CB553AD_VM\` (new folder each run — unusable for mods)
- Old `E:\mods\` retired 2026-06-11 (moved to `E:\Patcher TEST Folder\mods\`); the now-empty `E:\mods\` folder can be deleted manually.

## 3-Folder Layout (since 2026-06-11)
The project spans three top-level folders:

| Folder | Purpose |
|--------|---------|
| `C:\Users\gbichon\OneDrive\Documents\Claude\Projects\GN Project\` | All docs, scripts, sprite pipeline, GML reference copies, UMT GUI/CLI for sprite work, `patcher\` source (gml + install_foundation.csx + patcher.bat, no binaries) |
| `E:\GMS2-LTS2026\My projects\goblin_nest.yyp\` | GMS2 dev project — live GML source, edited directly here |
| `E:\Patcher TEST Folder\` | Self-contained patcher test rig: `patcher\` (gml + csx + bat), `UTMT_CLI_v0.9.0.0-Windows\` (sibling of `patcher\`, as required by `patcher.bat`'s `..\UTMT_CLI...` reference), `GNX_mods\` (gnx_mods_root, test_mod), `data.win` (1.33 vanilla, drag onto `patcher\patcher.bat` to patch in place), `GoblinNest.exe` + dlls + `options.ini` to run the patched game |

Note: `E:\Patcher TEST Folder\Game Folder\` is a leftover empty directory (could not be removed from the sandbox — "Permission denied" on rmdir); harmless, can be deleted manually in Windows.

## Key Paths
| What | Path |
|------|------|
| GML source files | `GN Project\` (various .gml) |
| Scripts (.py, .csx) | `GN Project\` |
| JSON data files | `GN Project\` (sprite_raw.json, sprite_enum_map.json) |
| MD docs | `GN Project\` (sprite_map.md, enum_map.md, etc.) |
| **Vanilla system docs** | `GN Project\GN_Understanding\` — ARCHITECTURE, CORE, MONSTERS, SLOTS, UNITS, ECONOMY, RAID, UI, RENDERING |
| Code folder (GML only) | `GN Project\Code\` |
| Exported sprites | `GN Project\Sprites\{name}\{name}_{i}.png` |
| Sprite HTML viewer | `GN Project\sprite_map.html` |
| Modded game folder | `GN Project\Goblin Nest - Mod Work\` |
| Mod sprites | `GN Project\Goblin Nest - Mod Work\mods\test_mod\sprites\` |
| Vanilla backup | `GN Project\Goblin Nest - Mod Work\Clean\` |
| UMT v0.9 (GUI, sprite work) | `GN Project\UndertaleModTool_v0.9.0.0-Windows\UndertaleModTool.exe` |
| UMT CLI v0.9 (GUI-folder copy) | `GN Project\UTMT_CLI_v0.9.0.0-Windows\UndertaleModCli.exe` |
| **Patcher test rig** | `E:\Patcher TEST Folder\` — `patcher\`, `UTMT_CLI_v0.9.0.0-Windows\`, `mods\`, `data.win`, `GoblinNest.exe` |

## Sprite Pipeline (COMPLETE)
| Script | Purpose | Status |
|--------|---------|--------|
| `extract_sprites.py` | Greps GML → `sprite_raw.json` (1413 sprites, ~50 categories) | Done |
| `assemble_sprite_map.py` | Concatenates 4 section .md files → `sprite_map.md` | Done |
| `export_sprites_umt.csx` | Run in UMT: exports sprites listed in sprite_raw.json to Sprites/ | Done |
| `generate_sprite_html.py` | Reads sprite_raw.json + Sprites/ → `sprite_map.html` (searchable viewer) | Done |
| `map_sprite_enums.py` | Scans all GML → `sprite_enum_map.json/md` (sprite→enum conditions) | Done |

To regenerate HTML after any change: `python generate_sprite_html.py` from GN Project root.
To regenerate enum condition map: `python map_sprite_enums.py` from GN Project root.

## sprite_raw.json — Key Facts
- 1413 total unique `spr_` identifiers across all GML
- Categories: ~50 buckets (1a_base_standard:92, 2a_goblin_hscene:182, 4_slot:80, 8_other:93, etc.)
- Full details: `memory/projects/gn-sprite-pipeline.md`

## UMT (UndertaleModTool) API — Critical
- **Version:** v0.9.0.0 at `UndertaleModTool_v0.9.0.0-Windows\UndertaleModTool.exe`
- **CLI:** v0.9.0.0 at `UTMT_CLI_v0.9.0.0-Windows\UndertaleModCli.exe` — used by `patcher.bat` for distribution patching; not used for sprite export (too slow)
- **Export sprites:** `TextureWorker.ExportAsPNG(texture, path, null, padded)` — NOT direct blob access
- **Progress:** `IncrementProgressParallel()` inside parallel loop; wrap with `StartProgressBarUpdater()` / `StopProgressBarUpdater()`
- **Pattern:** `using (worker = new()) { await Task.Run(() => Parallel.ForEach(...)); }`
- Scripts run as `.csx` files inside UMT's scripting interface
- **v0.9 breaking change:** `SyncBinding()` and `DisableAllSyncBindings()` removed — delete these calls from any script

## GNX Mod System — Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `gnx_pack_strips.py` | Packs per-frame PNG folders → GMS2 sprite strips. Strip filename = `{sprite_prefix}_{key}.png` (unique per class). `--force` to repack all. | Done |
| `classes.json` | Source defs: Elf (class_id=14) + Peasant override (class_id=0, Knight sprites, `"override":true`). Copy to mod folder then pack. | Done |
| `export_class_sprites.py` | General-purpose: copies + renames any vanilla class sprites to a new class name, extracts icon frames, outputs `sprites` JSON for classes.json. Supersedes `export_elf_sprites.py` / `export_knight_sprites.py`. | Done |
| `sync_gml.py` | Syncs the 25 patched GML files across G3M → GMS2 + Patcher. `python sync_gml.py` (default: G3M → both), `python sync_gml.py patcher` (G3M → Patcher only), `python sync_gml.py check` (diff all three). | Done |

**GML edit target:** `E:\G3M_Package\gml\` (G3M, primary live folder) — edit directly here. GMS2 (`E:\GMS2-LTS2026\My projects\goblin_nest.yyp\scripts\`) is secondary; sync G3M → GMS2 when needed, not the other way. Do NOT edit `Code\` or use the push_to_datawin/ImportGML_GNX workflow.

**Sprite workflow:**
1. Edit `classes.json` / `cells.json`
2. Run export script if needed (`export_elf_sprites.py` / `export_knight_sprites.py`)
3. `python gnx_pack_strips.py "Goblin Nest - Mod Work\mods\test_mod" --force`
4. Run `GoblinNest.exe`

**Doc:** `gnx_pack_strips_doc.md`

## Debug Log
- **GMS2 dev:** `GN Project\Debug\tier3_debug.txt` (absolute path, readable by Claude) — defined as `#macro GNX_LOG` in `s_macro.gml`, change path there if needed
- **Patched game:** `%LOCALAPPDATA%\goblin_nest\gnx_debug.txt` — GM sandboxes relative paths to `%LOCALAPPDATA%\<game_name>\` at runtime; `install_foundation.csx` inlines `GNX_LOG` as `"gnx_debug.txt"` (relative), so `s_macro.gml` path is irrelevant at runtime
- Log is **cleared on each run** (truncated at top of `scr_gnx_load_mods()`)

## Active Debug Logs (intentionally kept)
- `s_unit_data.gml` line ~204: `[GNX] REG-STANDARD class=N phase=N head/breast/leg/head_c/leg_c` — fires on every successful REG-STANDARD dispatch
- `s_unit_data.gml` lines ~32-38: `[GNX] class_spr h=N class=N arg1=N is_special=N base_body=N` — fires for GNX-registered cells
- `s_slot_state.gml`: `[DRINK] place=N drink_num=N→N milk=N` — fires on every drink cell goblin removal
- `s_mon_data.gml`: `[PROP] h=N anal=N gnx=N prop=N phase=N mon=N` — fires on wall 1-2 prop assignment

These 4 are now the ONLY `GNX_LOG` writers in the codebase. All other instances
were orphan debug code, removed 2026-06-10 (see Patcher Sync section).


## Vanilla canvas sizes (use `canvas_w`/`canvas_h` in sprite def to pad):
- Class icon slot (`spr_unit_icon_head`): **21×26**, origin 10×13

## GNX System Status (as of 2026-06-16)
Full modding layer implemented and verified. See `gnx_poc_plan.md` for full details.

| Feature | Status |
|---------|--------|
| Cell registry (39/39 vanilla cells) | ✅ Done |
| Custom cells via cells.json | ✅ Done |
| Custom classes via classes.json | ✅ Done |
| Custom goblin sprites (mon_spr JSON) | ✅ Done |
| Goblin routing to GNX cells | ✅ Done |
| Registry-aware vanilla switches (5) | ✅ Done |
| Physical extension fields (required_class, range_draw_func, scr_unoccupy) | ✅ Done |
| clothing_big / clothing_tent / is_special loaders | ✅ Done |
| Raid encounter pool system | ✅ Done |
| Unit icon system (icon_spr / icon_hair_spr) | ✅ Done |
| Unit stat extensions (class_name, preg_c_override) | ✅ Done |
| fap_mul / bap_mul per class | ✅ Done |
| preg_mon_type_override per class | ✅ Done |
| Hash-based class_id auto-assignment | ✅ Done |
| Hash-based h_type auto-assignment for cells | ✅ Done |
| Build menu unlock migration on save load (scr_gnx_migrate_unlocks) | ✅ Done |
| Mod removal sanitize (scr_patch_update_pre/post) | ✅ Done |

## GNX Test Suite
`scr_gnx_test_suite()` in `s_initials.gml` — called after `scr_gnx_load_mods()` at boot.
Writes `[GNX-TEST] PASS/FAIL T01–T27` to `tier3_debug.txt` + summary line, then a
separate DROUTE dispatch-routing check (`scr_gnx_test_dispatch_routing()`).
27 tests: DS structures, registry sizes, all 39 cells, classes 0–13, WALL1/DAIRY/BIND1
field checks, mod-class integrity, use_legacy_dispatch=false, mod save state (T19-T20),
plus (added 2026-06-12):
- **T21** fixed-mode cells: `phase_1/2` `spr_array`/`spr_c_array` are arrays of real sprites.
- **T22** every class `clothing_*` table resolves to real sprites (arrays + leaf fields), via recursive `scr_gnx_collect_bad_spr`.
- **T23** every mod in `index.txt` actually loaded (catches silent version-mismatch skip) — needs `global.gnx_indexed_mods` / `global.gnx_loaded_mods`, populated in `scr_gnx_load_mods`/`scr_gnx_load_mod`.
- **T24** cell `required_class` + class `birth_classes` resolve in class_registry.
- **T25** every `bl_lookup` value is a real sprite.
- **T26** no duplicate `h_type` in `gnx_registered_cells`.
- **T27** at least one GNX cell has a hash-assigned h_type (>= 100).

Helpers `scr_gnx_spr_ok` / `scr_gnx_collect_bad_spr` live just above the suite.
**Sprite validity uses `sprite_exists`, never `is_real`** — sprites are a `ref` type
in this runtime, so `is_real`/`is_numeric` return false on a valid sprite.
On FAIL, T21/T22 log the exact offending path (e.g. `c15.clothing_big.idle.head`).

**T27 SKIP when no mods loaded** — T27 checks for at least one hash-assigned cell (h_type >= 100). If `gnx_registered_cells` is empty (no mods loaded), T27 logs `SKIP` instead of `FAIL`.

## Runtime Sprite Management (2026-06-12)
**Problem:** ~160 runtime sprites loaded via `sprite_add` at boot. `game_end()` took 10s
cleaning them up; returning to menu re-called `scr_create_initials()` reloading all from
disk (4s).

**Solution:** two-part system in `s_initials.gml`:

1. **Tracking array** (`global.gnx_runtime_sprites`): every `sprite_add` result pushed here.
   `scr_gnx_cleanup_sprites()` iterates + `sprite_delete` all, then empties the array.
   Called before `game_end()` in `s_button_activate.gml` (case 51/button 2).

2. **Sprite cache** (`global.gnx_sprite_cache`, ds_map): persists across `scr_create_initials()`
   calls. Key = `base_dir + key_name`. `gnx_resolve_sprite` checks cache before `sprite_add`;
   on hit returns existing sprite (no disk I/O). On game exit, cache is destroyed after cleanup.

**Result:** game_end ~1-2s (was 10s), menu return instantaneous (was 4s).

**Files modified:** `s_initials.gml` (cache init + lookup/store in `gnx_resolve_sprite`,
cleanup function), `s_button_activate.gml` (cleanup+destroy on exit, no cleanup on menu return).
Synced to both patcher locations.

## Anal Sprites Note
`anal_spr` class-registry feature reverted (anal sprites are goblin-side, not class-side).
Bug fix kept: `&& !_anal` guard on GNX dispatch block in `s_mon_data.gml`.

## Patcher Sync — 2026-06-10
`patcher/gml/` (flat UTMT-codeName files for `install_foundation.csx`) was in
sync with the GMS2 dev source (`goblin_nest.yyp\scripts\`) at this point.

**End-to-end test PASSED (2026-06-10, real Windows run via patcher.bat):**
18/18 GNX-TEST PASS, DROUTE 453 PASS / 0 FAIL / 20 SKIP (expected behavioral-only
cells). `mods_root=E:\Goblin Nest Vanilla\patcher\mods/` confirms
`program_directory + "mods/"` divergence is correct. Test mod (Elf class=14,
Witch class=15, Peasant override class=0, TEST WALL h=43) loaded cleanly,
`carry_head_spr` resolved without error, REG-STANDARD fires correctly during
gameplay. Patcher pipeline considered fully validated.

**Resynced (were stale):**
| File | Change |
|------|--------|
| `gml_GlobalScript_s_mon_draw.gml` | Added `spr_unit.base != -1` guard before `draw_sprite_ext` |
| `gml_GlobalScript_s_unit_data.gml` | GNX class ≥14 carry-sprite struct now reads `carry_head_spr`/`carry_hair_spr` from class_registry |
| `gml_GlobalScript_s_slot_data.gml` | Added GNX `birth_classes` branch (modded unit birth → `gnx_br_unlock`) before vanilla `switch(_mon_type)` |
| `gml_GlobalScript_s_initials.gml` | Added `global.gnx_br_unlock` init, `global.gnx_trade_list` init, `carry_head_spr`/`carry_hair_spr` resolution, `birth_classes`/`trade_stage` registry fields, full `scr_gnx_dump_coverage`. Fixed pre-existing truncation + 88 trailing null bytes. `global.gnx_mods_root = program_directory + "mods/"` correctly preserved (intentional divergence from GMS2 dev's `"E:/mods/"`). |

**New files (were missing entirely):**
- `gml_GlobalScript_s_raid_function.gml` — raid step/state machine (no GNX-specific logic, needed as dependency)
- `gml_GlobalScript_s_trade_function.gml` — trade shop, incl. `scr_choose_trade_item` GNX trade-pool weighting (`global.gnx_trade_list`, 3x weight)
- `gml_GlobalScript_s_mon_head_draw.gml` — `scr_draw_mon_head`, incl. GNX modded-breeder portrait cycling above vanilla breeder window

**Orphan debug cleanup (removed from GMS2 source, not carried to patcher):**
| File | Removed |
|------|---------|
| `s_mon_function.gml` | 4x `GNX_LOG` blocks (CREATED, STATE_ENTER, STATE_WALK, CONTACT) — bugfix logic in `scr_mon_contact` kept |
| `s_mon_state.gml` | `GNX_LOG` PRE_WALK + WALK blocks in `scr_mon_state_walk` — `mon_data.ff` reset logic kept |
| `s_general.gml` | `GNX_LOG` block in `scr_mon_type_construct` default case |
| `s_mouse_action.gml` | `keyboard_check_pressed(ord("L"))` debug-dump keybind (called now-unused `scr_gnx_dump_coverage`/`scr_gnx_dump_cell_coverage`, defs left in `s_initials.gml` as dead code) |

Audit method: `grep -ic "gnx" scripts/*/*.gml` (the `Code/` git repo's vanilla diff
was too noisy — dominated by GMS2-import formatting churn, not useful for this audit).

## UTMT CLI Distribution — decision (2026-06-10)
`UTMT_CLI_v0.9.0.0-Windows` (129MB) ships as-is with the installer, no size reduction.
`install_foundation.csx` only uses `CodeImportGroup` (text-only); `Magick.Native-Q8-x64.dll`
(~25MB) and other assemblies are likely unused for this path, but trimming a self-contained
.NET build can't be validated from this Linux sandbox (no Windows exec). Decided not worth
the risk/effort — keep full distribution.

## Per-Mod Save State (added 2026-06-11)
Mods can declare `save_state` in `manifest.json` with `version` + `fields` (default values).
State stored in `global.val.gnx_mod_data.{mod_name}` (auto-serialized with save).
Runtime alias: `global.gnx_mod_state.{mod_name}` (rebuilt after load in `s_save_load.gml`).

Accessors: `scr_gnx_get_state(mod_name, key)` / `scr_gnx_set_state(mod_name, key, value)`.

Reserved prefixes for future subsystems: `_q_` (quests), `_b_` (bosses), `_d_` (dialogs), `_version` (schema).

**Files modified:** `s_initials.gml` (init + 3 new functions), `s_save_load.gml` (alias rebuild on load).

**Patcher port (2026-06-11):** Save-state system fully ported to `patcher/gml/`.
`gml_GlobalScript_s_initials.gml` got the same global init lines, the 3 functions
(`scr_gnx_init_mod_state`/`scr_gnx_get_state`/`scr_gnx_set_state`), the
`scr_gnx_init_mod_state` call in `scr_gnx_load_mod`, and T19/T20 in
`scr_gnx_test_suite()`. New file `gml_GlobalScript_s_save_load.gml` (734 lines)
created from the 1.33 vanilla decompile (`Code/gml_GlobalScript_s_save_load.gml`,
718 lines) + the 16-line alias-rebuild block in `scr_load_slot()`. Auto-discovered
by `install_foundation.csx` (no manifest entry needed).

## Frieren Mod Analysis (2026-06-11)
Full analysis in `gnx_frieren_analysis.md`. Identified 3 GNX feature tiers:
1. Quest/Dialog modding (quests.json, dialog from JSON, portrait sprites)
2. Boss/Special Character system (boss registry, encounters, escape mechanic)
3. Per-mod save state ← **implemented**

## Hash-Based ID Systems (implemented 2026-06-16/17)

### Class IDs
`class_id` is optional in `classes.json`. GNX assigns stable IDs [14–9999] via djb2 hash of `"mod_folder.ClassName"`, linear probe on collision.

**Known hash IDs (gnx_test_mod):** ELF=1455, Witch=2655. For patcher test_mod: ELF=5951.

### Cell h_types (implemented 2026-06-17)
`h_type` is optional in `cells.json`. GNX assigns stable IDs [100–9999] via djb2 hash of `"mod_folder.CellName"`, linear probe on collision. All vanilla h_types are 1–42, so mod cells never collide with vanilla.

**Known hash IDs (gnx_test_mod):** TEST WALL=8166. For patcher test_mod: TEST WALL=5082.

**Build menu integration:** `scr_gnx_apply_unlocks()` (end of `scr_gnx_load_mods`) pushes each GNX cell's h_type to `unlock.breed/utility/pleasure` based on its `category` field. `scr_gnx_migrate_unlocks()` (called from `scr_load_slot` after save data restores unlock arrays) strips stale h_types not in `cell_registry` and re-runs `scr_gnx_apply_unlocks`. New mod cells appear in the correct build menu automatically, on both fresh games and save loads.

**Computing hash IDs in Python:**
```python
def gnx_hash_class(mod_name, class_name):
    s = mod_name + '.' + class_name
    h = 5381
    for c in s: h = ((h * 33) + ord(c)) & 0xFFFFFF
    return 14 + (h % 9986)

def gnx_hash_cell(mod_name, cell_name):
    s = mod_name + '.' + cell_name
    h = 5381
    for c in s: h = ((h * 33) + ord(c)) & 0xFFFFFF
    return 100 + (h % 9900)
```

**String refs** (`"mod_name.ClassName"` in `required_class`/`birth_classes`) are fully supported ✅ (2026-06-17). GNX resolves them internally at load time using `gnx_class_name_to_id` map. Modders can use string refs or pre-computed integer IDs interchangeably. Load order is classes-first so the map is populated when cells register. The `birth_classes` pass uses `_def.name` (not `_def.class_name`) to match the JSON field.

**Runtime quirks discovered:**
- `ds_map[? key] = value` WRITE accessor crashes ("unable to convert string to int64") — use `ds_map_add(map, key, value)` instead
- `ds_map[? key]` READ accessor works fine

## Mod Removal Sanitize System (implemented 2026-06-17)

When a mod is removed, saves may contain orphaned cells (unknown h_type) and orphaned unit classes (unknown class_id). The sanitize system in `scr_patch_update_pre` / `scr_patch_update_post` (`s_patch_updates.gml`) replaces them cleanly with vanilla equivalents.

**Pre-pass (`scr_patch_update_pre`):**
- **Orphaned cells** (h_type not in `cell_registry`, `anim_struct != -1`): sets `anim_struct = -1` (skips load's `scr_set_slot_h_data`/`scr_occupy_slot`), sets fallback h_type (slot_type 1 → h=19 Gang1, slot_type 2 → h=31 Big Gang1, else → h=1 WALL1), stores `gnx_rebuild` flag and `gnx_had_unit` on slot_data. Goblins assigned to orphaned slots are dropped from `mon_list`. Unit_data set to -1.
- **Orphaned slot units** (class >= 14 not in `class_registry`): replaced with `scr_create_unit_base(0, 1)` (fresh level-1 peasant).
- **Orphaned global unit_list** (same class check): same replacement.
- **Orphaned raid encounter units** (2026-06-22): `stage_info[stage].info[level].unit_list` is a persisted array of pre-rolled enemy unit structs picked from `gnx_encounter_pools`. Any unit with class >= 14 not in `class_registry` is replaced in-place with `scr_create_unit_base(0, 0)` (vanilla goblin level 0). Covers stages 0–4.
- **Orphaned raid formation rows** (2026-06-22): `front_row`, `back_row`, `front_row_save`, `back_row_save` are persisted arrays of `{unit_data, num, lvl}` structs representing the player's selected raid party. Entries with `unit_data.class >= 14` not in `class_registry` are dropped entirely (the player loses those units from their formation, which is correct behavior).

**Post-pass (`scr_patch_update_post`):**
Runs after all `obj_slot` instances are created. `with (obj_slot)` finds slots with `gnx_rebuild` flag, calls `scr_set_slot_h_data(id, gnx_rebuild)` (fully re-initializes slot_data from registry), then `scr_occupy_slot(id, scr_create_unit_base(0, 1), false, 0)` if the slot had a unit.

**Key insight:** `slot_data = _data.slot_data` at load line 417 always runs and would overwrite post-pass changes. Setting `anim_struct = -1` skips the entire load path (lines 288-296 guard), so the post-pass is the only thing that initializes the slot — using the game's own registry data for a correct result.

Logs:
- `[GNX-SANITIZE] orphaned cell h=N -> rebuild as h=N`
- `[GNX-SANITIZE] goblin dropped (slot=N)`
- `[GNX-SANITIZE] orphaned unit class=N -> fresh peasant (slot=N)`
- `[GNX-SANITIZE] raid encounter class=N -> vanilla goblin (stage=S lvl=L)`
- `[GNX-SANITIZE] raid row class=N dropped from <row_name>`

Note: `scr_gnx_mod_removal_migration` (previously in `s_initials.gml`) was removed — fully consolidated into the sanitize passes above.

**Why `gnx_encounter_pools` itself needs no sanitize:** the pools are rebuilt from scratch at boot (`scr_gnx_init_encounter_pools` + loaded mods' `raid_spawns`). Only pre-rolled encounters already stored in `stage_info` (and the player's formation rows) persist across sessions and need sanitizing.

## Next Objective
Quest/Dialog modding (Tier 1 from Frieren analysis). Depends on per-mod save state (done).

## GNX Testing — Completed 2026-06-08
All 35 sprite-dispatch cells verified through GNX with no vanilla fallback.
Remaining 4 ⬜ cells (CLEAN h=34, CLONE_B h=25, S/F/R.SHRINE h=40/41/42) have no goblin h-scene — behavioral-only, outside GNX sprite scope.

Notable bugs fixed during testing:
| Bug | Fix | File |
|-----|-----|------|
| DAIRY crash: GNX pre-switch contaminated head_b/hand_b | Created `_dairy_gob` struct (body_b only, no head/hand/linework) | `s_initials.gml` |
| DAIRY crash: `milk_index not set` | Made `anim_struct_overrides` handler iterate all keys generically | `s_slot_data.gml` |

## Terms
| Term | Meaning |
|------|---------|
| UMT | UndertaleModTool — decompiler/editor for GameMaker .win data files |
| spr_array | GML variable name (NOT a sprite) — in BLACKLIST in extract_sprites.py |
| alpha/line | Goblin sprites come in `_alpha` (fill) + `_line` (linework) pairs |
| Mage/Shaman split | Class Value_6 uses `spr_h_mage_*` (std cells) vs `spr_h_shaman_*` (big cells) |

→ Full details: `memory/projects/gn-sprite-pipeline.md`

## Git Repo (Code/)

Repo root: `Code\` — GML files only.

**Baseline:** `v1.32-vanilla` tag = clean UMT export, no mods. Use `git diff v1.32-vanilla` to see all mod changes.

**Line endings:** `.gitattributes` enforces LF (`eol=lf`). UMT exports LF; do not change this.

**Ignored:** `sprite_map.html` (generated), `tier3_debug.txt` (runtime log), OS/editor junk.

**Workflow to re-baseline a new vanilla export:**
```powershell
Remove-Item -Recurse -Force .git
git init
git add .
git commit -m "vanilla <version>"
git tag v<version>-vanilla
git remote add origin <url>
git push -u origin main --tags
# then overwrite with mod files:
git add .
git commit -m "mod: initial state"
git push
```