---
type: subsystem
summary: Draw-time code: slot/goblin/unit-head/raid draw functions, off-screen camera culling, GNX portrait draw override, atlas-aware draw wrappers.
entry_points:
  - GNX/gml/gml_GlobalScript_s_slot_draw.gml
  - GNX/gml/gml_GlobalScript_s_mon_draw.gml
covers:
  - GNX/gml/gml_GlobalScript_s_slot_draw.gml
  - GNX/gml/gml_GlobalScript_s_mon_draw.gml
  - GNX/gml/gml_GlobalScript_s_unit_head_draw.gml
  - GNX/gml/gml_GlobalScript_s_raid_draw.gml
  - GNX/gml/gml_GlobalScript_s_text_draw.gml
  - GNX/gml/gml_GlobalScript_s_slot_prop.gml
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"culling":"vertical camera-bounds check at top of scr_draw_slot + 4 goblin draw fns; skip if y outside [camera_y-200, camera_y+view_h+200]","gnx_draw_variant":"fixed/class_map cells MUST use scr_draw = scr_draw_slot_gnx (has _draw_skin=-1 override for standalone sprites)","perf_counters":"gnx_perf_slots_drawn/culled, gnx_perf_mons_drawn/culled, logged every 120 frames when gnx_perf_enabled"}
edges:
  - to: sprite-dispatch type: depends_on reason: draws the sprite slots that sprite-dispatch computed onto slot_data
  - to: atlas-sprites type: depends_on reason: draw calls go through gnx_draw_sprite_ext / gnx_sprite_get_* atlas wrappers
  - to: quest-dialog type: related_to reason: dialog renderer lives in obj_window Draw_0/Draw_64 and s_text_draw portrait override
---

- obj_np.obj_raid (raid window, obj_window interact_type=4) is a PERMANENT compiled-code singleton created once by scr_create_raid — never destroy it during any UI cleanup or every subsequent obj_np.obj_raid access (scr_mouse_control every frame) crashes. Same for the 3 dungeon HUD button groups (Value_32/34/35) — compiled-code singletons, scr_load_slot does not recreate them. <!-- id:2833 -->
- s_slot_prop.gml is a NEW file added in v1.3.14 (vanilla 1.38 base + GNX patches, ~73KB): custom-prop default case, scr_draw_gnx_prop, birth-sprite dispatch, scr_draw_prop_infant_gnx (SprRef-aware infant prop rendering). Props + birth sprites render here. <!-- id:8e01 -->
