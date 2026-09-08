---
type: subsystem
summary: Save/load integration: GNX field serialization, mod-removal sanitize (orphaned cells/classes/props/encounters), unlock migration, and the shelved multi-map snapshot/restore/travel system.
entry_points:
  - GNX/gml/gml_GlobalScript_s_save_load.gml
  - GNX/gml/gml_GlobalScript_s_patch_updates.gml
covers:
  - GNX/gml/gml_GlobalScript_s_save_load.gml
  - GNX/gml/gml_GlobalScript_s_patch_updates.gml
  - GNX/gml/gml_GlobalScript_s_initials.gml
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"sanitize":"scr_patch_update_pre/post in s_patch_updates.gml — replaces orphaned content with vanilla equivalents","load_clobber_gotcha":"s_save_load.gml ~line 433 'slot_data = _data.slot_data;' blanket-restores the whole struct, reverting registry config (hand_frame, spr layout). Capture-before / re-apply-after any config fix.","unlock_migration":"scr_gnx_migrate_unlocks / scr_gnx_migrate_prop_unlocks strip stale IDs and re-apply","multimap":"scr_gnx_snapshot_map (~7276), scr_gnx_travel (~7492); guarded by global.gnx_multimap_enabled=false (SHELVED v1.3.11)"}
edges:
  - to: gnx-registries type: depends_on reason: sanitize checks class_id / h_type against the registries to detect orphans
---

- Multi-map travel uses a deferred compiled-state-machine approach (Path A, 2026-08-10): scr_gnx_travel only snapshots + sets gnx_travel_data + gnx_trigger_load; next frame obj_control_Step_0 destroys instances, calls scr_create_initials(), sets load_file (0=restore via snapshot bypass, -1=fresh/New-Game path), sets obj_np.load_state=6. Entire feature SHELVED behind global.gnx_multimap_enabled=false. <!-- id:9843 -->
