---
type: subsystem
summary: Computes human and goblin sprite assignments per cell: base+class / fixed / class_map dispatch modes, naked-layer overrides, mon_spr_overrides, is_special classes.
entry_points:
  - GNX/gml/gml_GlobalScript_s_unit_data.gml
  - GNX/gml/gml_GlobalScript_s_mon_data.gml
covers:
  - GNX/gml/gml_GlobalScript_s_unit_data.gml
  - GNX/gml/gml_GlobalScript_s_mon_data.gml
  - GNX/diffs/gml_GlobalScript_s_unit_data.patch
  - GNX/diffs/gml_GlobalScript_s_mon_data.patch
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"human_dispatch":"scr_set_class_spr_data / scr_set_patrol_spr_data in s_unit_data.gml","goblin_dispatch":"scr_set_mon_spr_data in s_mon_data.gml (~23 mon_spr_overrides sites)","dispatch_priority":"fixed > class_map > is_special > base+class","phase_map":"0=big start, 1=idle, 2=loop, 4=tent; phase 3 remapped to 2; phase 0 auto-remapped to 1 for non-big custom cells"}
edges:
  - to: gnx-registries type: depends_on reason: reads class_registry / cell_registry entries to pick sprites
  - to: atlas-sprites type: depends_on reason: registry sprite fields are SprRefs resolved through the sprite cache / atlas
---

- Cell dispatch modes (cells.json human_spr.mode): base+class (default, class clothing layers), fixed (cell controls spr_array/spr_c_array directly, all classes identical), class_map (per-class {phase_N} entries with 'default' fallback — solves multi-mod row-conflict). class_map keys are string refs or integer-strings; stored as struct not ds_map (GC); deferred resolve pass scr_gnx_deferred_resolve_class_map for cross-mod refs. <!-- id:7337 -->
- class_map/fixed gotchas: spr_array is a composite body+clothes sprite drawn as-is (NOT a naked layer). 'default' is a GML reserved keyword — always variable_struct_get(hspr,"default"). asset_get_index of vanilla compiled sprite names is unreliable in JSON — use gnx: prefix or integer refs. v1.3.14: class_map respects unit_data.skin for row indexing; only fixed forces _draw_skin=-1. <!-- id:3868 -->
- v1.3.14 modder-bug fixes: (bug#2) fixed/class_map cells auto-inject essential body layers 10/6/7/8/9 as empty placeholders when the modder's physical.layers omits them, else only leg renders. (bug#5) anal goblin override gated to _class<14 so modded classes keep GNX-dispatched sprites. <!-- id:0798 -->
- GML runtime quirk (general): sprites are a 'ref' type in this runtime, so is_real / is_numeric return false on a valid sprite. Always validate with sprite_exists(). The whole test suite and every gnx_spr_ok check relies on this. <!-- id:2c08 -->
- GNX registry pre-dispatch in scr_set_mon_spr_data (s_mon_data.gml ~line 177) is gated `if (!_set && (_class >= 14 || _slot_type >= 100))`. Vanilla class (0-13) on vanilla cell (h_type 1-42) skips GNX dispatch entirely so vanilla switches handle it. Without this gate, ej/end phase (arg1==3) falls back to loop sprites for vanilla units (the 2026-08-12 ej regression) because vanilla mon_spr entries lack ej_* keys. <!-- id:dd03 -->
- skin=-1 fix: is_special GNX classes (hash class_id) fall through vanilla's class switch keeping default skin=irandom(0,2); skin=0 then triples the spritesheet row offset. scr_set_class_spr_data forces arg0.skin = -1 right after the _rclass lookup (structs are by-reference so this sticks on the slot). <!-- id:999e -->
