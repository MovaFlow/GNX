---
type: subsystem
summary: Custom raid encounter pools with weighted/conditional spawning, AP overrides, per-encounter limits, post-raid cage escape, and birth-class (human class to goblin troop class) mapping.
entry_points:
  - GNX/gml/gml_GlobalScript_s_raid_encounter.gml
  - GNX/gml/gml_GlobalScript_s_initials.gml
covers:
  - GNX/gml/gml_GlobalScript_s_raid_encounter.gml
  - GNX/gml/gml_GlobalScript_s_raid_function.gml
  - GNX/gml/gml_GlobalScript_s_raid_cal_stat.gml
  - GNX/gml/gml_GlobalScript_s_mon_remove.gml
  - GNX/gml/gml_GlobalScript_s_initials.gml
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"key_functions":"gnx_pool_add (~6293), gnx_pool_pick (~6332, uses argument[] + argument_count — named params crash when omitted), scr_gnx_init_encounter_pools (~6426), scr_gnx_check_post_raid_escape (~5586)","two_class_systems":"human class_id 0-13+ (sprites/breeding) vs goblin class 0-3 per species (raid stats/skills). scr_mon_birth maps human->goblin.","stages":"pools cover stages 0-4; stage 4 integrated 2026-07-22","escape_formula":"irandom(1,100) <= base_chance + irandom(1,100) - scale + scale*(over_diff-1)"}
edges:
  - to: save-load type: depends_on reason: pre-rolled encounters + formation rows in stage_info need orphan sanitize
---

- GML runtime quirk (general): named function params arg0-arg7 CANNOT be omitted by callers in this runtime — reading an unpassed named param crashes ('argN not set before reading it'). For optional/variadic params use the argument[] array accessor + argument_count guard. gnx_pool_add/gnx_pool_pick and scr_gnx_exec_tool_action's variadic paths all use this pattern. <!-- id:bd0c -->
