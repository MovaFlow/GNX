---
type: subsystem
summary: cell_registry and class_registry: JSON loaders for classes/cells/props, hash-based ID assignment, class override merge, string-ref resolution.
entry_points:
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - docs/GNX_MODDING.md
covers:
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - GNX/example_mod/classes.json
  - GNX/example_mod/cells.json
  - GNX/example_mod/props.json
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"key_functions":"scr_gnx_load_classes (~7122), gnx_resolve_class (~6710), scr_gnx_load_cells (~4409), scr_gnx_register_cell (~4448), scr_gnx_patch_cell (~4812), scr_gnx_load_props (~4301), gnx_hash_class_id (~6666), gnx_hash_cell_id (~6697), gnx_hash_prop_id (~6684)","hash_ranges":"class_id [14-9999] djb2 of mod.ClassName; cell h_type [100-9999] djb2 of mod.CellName; vanilla h_types are 1-42","runtime_quirk":"ds_map[?key]=value WRITE accessor crashes; use ds_map_add(map,key,value). READ accessor is fine."}
edges:
  - to: atlas-sprites type: depends_on reason: JSON loaders call gnx_resolve_sprite to turn sprite names into SprRefs
  - to: modding-toolkit type: related_to reason: docs + scaffolding scripts + example_mod define the JSON schemas the registries consume
---

- Class override merge (M1 fix): a minimal {"override":true} on a vanilla class_id 0-13 does NOT blank its sprites. scr_gnx_register_class merge pass copies every base-entry field the JSON did not explicitly provide (mapped via a _prov set). Voice-only overrides are safe now, but sounds.json voice_map is still preferred for pure voice config. <!-- id:9ba4 -->
- Hash IDs computable in Python: djb2 with h=5381, h=((h*33)+ord(c)) & 0xFFFFFF; class_id = 14 + (h % 9986); cell h_type = 100 + (h % 9900). Linear probe on collision. <!-- id:7775 -->
