---
type: subsystem
summary: JSON tool/cheat menu (tools.json): ~40 action types, keybind dispatcher, continuous effects, guard conditions, toggle persistence, and the settings-DEBUG tool menu UI.
entry_points:
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - GNX/example_mod/tools.json
covers:
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - GNX/gml/gml_GlobalScript_s_button_activate.gml
  - GNX/example_mod/tools.json
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"key_functions":"scr_gnx_load_tools (~9150), scr_gnx_exec_tool_action (~9265, big dispatcher), scr_gnx_exec_tool_button (~9740), scr_gnx_eval_tool_guard (~9801), scr_gnx_check_keybinds (~9831), scr_gnx_apply_continuous_effects (~9892)","menu_path":"Settings -> DEBUG (interact 9010) -> categories (9001) -> actions (9002); back 9003/9004","framework_tools":"_gnx pseudo-mod always provides PERF LOG + VERBOSE LOG toggles","limitation":"tool actions do NOT resolve string refs — modders must use numeric IDs in tools.json","shelved":"gml and travel_map action types SHELVED v1.3.11"}
edges:
  - to: ui-integration type: depends_on reason: tool menu is injected into the settings window by s_button_activate hooks
---
