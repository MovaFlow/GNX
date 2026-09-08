---
type: subsystem
summary: JSON-driven quests and dialogs: events/triggers/conditions, side effects, rewards, portrait sprites, GNX dialog renderer, save/load persistence.
entry_points:
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - docs/QUESTS_SCHEMA.md
covers:
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - GNX/gml/gml_Object_obj_window_Draw_0.gml
  - GNX/gml/gml_Object_obj_window_Draw_64.gml
  - GNX/gml/gml_GlobalScript_s_textbox_function.gml
  - docs/QUESTS_SCHEMA.md
  - GNX/example_mod/quests.json
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"key_functions":"scr_gnx_load_quests (~5167), scr_gnx_eval_condition (~5433), scr_gnx_check_triggers (~5401), scr_gnx_fire_event (~5698), scr_gnx_apply_side_effects (~5794), scr_gnx_make_reward (~5851), scr_gnx_check_quest_completion (~5879), scr_gnx_save/restore_quest_state (~5925/5949)","completion_hooks":"frame, post_raid, post_raid_win, cell_built","side_effect_timing":"scr_gnx_fire_event applies side_effects SYNCHRONOUSLY before queuing the notification","portraits":"{mod}/portraits/, 133x113, referenced by key; rendered standalone when portrait_index>=100"}
edges:
  - to: save-load type: depends_on reason: quest state serialized separately via scr_gnx_save/restore_quest_state
  - to: rendering type: related_to reason: dialog renderer lives in obj_window Draw_0/Draw_64 and s_text_draw portrait override
---
