---
type: subsystem
summary: Boot-time self-test: scr_gnx_test_suite (T01-T59) validates DS structures, registries, all cells/classes, sprite validity; plus DROUTE dispatch-routing coverage check.
entry_points:
  - GNX/gml/gml_GlobalScript_s_initials.gml
covers:
  - GNX/gml/gml_GlobalScript_s_initials.gml
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"entry":"scr_gnx_test_suite (~7654), scr_gnx_test_dispatch_routing (~9022), scr_gnx_dump_coverage (~8908)","output":"[GNX-TEST] PASS/FAIL lines + summary to gnx_debug.txt, then DROUTE","helpers":"scr_gnx_spr_ok (~7207), scr_gnx_collect_bad_spr (~7222) — use sprite_exists never is_real","skip_semantics":"tests SKIP (not FAIL) when their feature is absent, e.g. T27 no mods, T41-43 no sounds, T54-57 multimap disabled"}
---

- Test count grew past the CLAUDE.md's T57: v1.3.14 adds T58 (birth_spr resolution) and T59 (prop registry). ATLAS_SYSTEM_README cites 42/42 tests + 549 DROUTE PASS as the passing baseline in atlas mode. <!-- id:5880 -->
- Current test range is T01-T59 (game 1.38 / GNX v1.3.14). T58 = birth_spr sprite resolution, T59 = prop_registry validity (sprite + display_name_key + position). T54-T57 (multi-map) log SKIP because global.gnx_multimap_enabled is false. Earlier T46-T53 (GMLC) were REMOVED, not skipped — GMLC is not shipped. <!-- id:f16d -->
