---
category: context
subject: shelved-features
---

Two feature sets are built but inert as of v1.3.14, all marked `[SHELVED 1.3.11]` in code. (1) GMLC runtime GML compiler: 35 files moved to GNX/gml_shelved/ so install_foundation.csx skips them; global.gnx_gmlc_env=-1; scr_gnx_gmlc_expose_functions removed; tool action types "gml" and "travel_map" removed from the allowlist; tests T46-T53 removed. (2) Multi-map travel: all code in place but guarded by global.gnx_multimap_enabled=false (s_initials ~3548). scr_gnx_travel returns false immediately; the deferred load trigger (gnx_trigger_load in obj_control_Step_0) is inert; save-side gnx_active_map/gnx_maps writing skipped; T54-T57 SKIP. Restore GMLC: move files back + uncomment [SHELVED] blocks. Restore multi-map: set the flag true.
