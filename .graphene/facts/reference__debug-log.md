---
category: reference
subject: debug-log
---

Runtime debug log: %LOCALAPPDATA%\goblin_nest\gnx_debug.txt (macro GNX_LOG in s_macro.gml, resolved relative to the save dir). Truncated at the top of scr_gnx_load_mods() each run. Boot/loader/test-suite/sanitize lines are always on. High-frequency traces ([GNX] class_spr, REG-STANDARD, [DRINK], [PROP], [GNX-MSO], pool_pick, anal_roll) are gated behind global.gnx_debug_verbose (Settings -> DEBUG -> GNX DEBUG -> VERBOSE LOG). Perf counters gated behind global.gnx_perf_enabled (PERF LOG toggle) -> [GNX-PERF] every 120 frames.
