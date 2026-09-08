---
type: subsystem
summary: Mod discovery and load orchestration: scans GNX_mods/ for manifest.json, version-checks, and drives per-mod registration of all content types.
entry_points:
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - README.md
covers:
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - GNX/gml/gml_GlobalScript_s_gnx_loader.gml
  - GNX/example_mod/manifest.json
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"key_functions":"scr_gnx_load_mods (s_initials ~3533), scr_gnx_load_mod (~4033), scr_gnx_init_mod_state (~4208), gnx_report_mod_error (~3521)","mods_root":"global.gnx_mods_root = program_directory + \"GNX_mods/\"","load_order":"alphabetical by folder; classes loaded before cells so string refs resolve","debug_log":"%LOCALAPPDATA%/goblin_nest/gnx_debug.txt, cleared each run"}
edges:
  - to: gnx-registries type: depends_on reason: scr_gnx_load_mod calls the class/cell/prop registry loaders per mod
  - to: quest-dialog type: depends_on reason: scr_gnx_load_mod calls scr_gnx_load_quests
  - to: tool-system type: depends_on reason: scr_gnx_load_mod calls scr_gnx_load_tools
  - to: sound-system type: depends_on reason: scr_gnx_load_mod calls scr_gnx_load_sounds
  - to: raid-encounter type: depends_on reason: raid_spawns from classes.json feed scr_gnx_init_encounter_pools
  - to: test-suite type: depends_on reason: scr_gnx_test_suite runs immediately after scr_gnx_load_mods at boot
  - to: install-patcher type: related_to reason: install_foundation.csx patches all the .gml files these subsystems live in into data.win
---

- s_gnx_loader.gml is a 3-line empty placeholder — ALL loader functions were moved into s_initials.gml (v0.2). The file is kept only so UTMT doesn't remove the asset. <!-- id:12b6 -->
- s_initials.gml is a 10,824-line mega-file holding ~112 GNX functions spanning EVERY subsystem (loader, registries, quests, tools, sounds, tests, sprite resolution, multi-map). Use the line ranges in each node's metadata to navigate. Vanilla scr_create_initials also lives here. <!-- id:e464 -->
- Manifest version check: scr_gnx_load_mod does an exact string match of manifest.json compatible_game_versions against global.val.version and silently exit()s the whole mod (no classes/cells registered) on mismatch, logged only as '[GNX] version mismatch'. Any game version bump requires updating every mod's manifest. <!-- id:f24b -->
- Related skills carry deep pre-analyzed knowledge — load before working: 'gn-modding' (vanilla game architecture), 'gnx-system' (framework internals: loader/registries/atlas/dispatch/quests/sanitize/tests), 'gnx-mod-building' (JSON schemas + sprite prep for modders), 'gmlc-integration' (shelved GML runtime compiler). <!-- id:29f6 -->
