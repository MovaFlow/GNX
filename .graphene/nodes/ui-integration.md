---
type: subsystem
summary: Hooks into vanilla menus and windows: settings-menu DEBUG/SOUND injection, build-menu unlock wiring for all 8 categories, button/window dispatch, tooltip/blueprint text.
entry_points:
  - GNX/gml/gml_GlobalScript_s_button_activate.gml
  - GNX/gml/gml_GlobalScript_s_button_text.gml
covers:
  - GNX/gml/gml_GlobalScript_s_button_activate.gml
  - GNX/gml/gml_GlobalScript_s_button_text.gml
  - GNX/gml/gml_GlobalScript_s_window_alpha.gml
  - GNX/gml/gml_GlobalScript_s_slot_windows.gml
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"settings_injection":"3 identical sites in s_button_activate.gml (settings open, guide BACK, tool BACK) — draw override + button shift + entry button","build_menu":"scr_gnx_apply_unlocks / scr_gnx_migrate_unlocks push h_types to unlock.breed/utility/pleasure + b_*/t_* order arrays; b_other uses b_pleasure_order","custom_sprite":"spr_gnx_option_window imported by install_foundation.csx","interact_types":"9001-9010 tool menu, 9020 sound page, 9030/hijacked-45 travel"}
edges:
  - to: gnx-registries type: depends_on reason: build-menu unlock wiring reads cell_registry category fields
---
