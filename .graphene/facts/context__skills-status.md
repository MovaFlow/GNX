---
category: context
subject: skills-status
---

Skills consolidated 2026-09-08 to ONE deep skill + companions. Updated .skill bundles in C:\Users\gbichon\Downloads\gnx-skills-updated\ (user must re-import; canonical authoring source unknown — the installed copies live only at a session-scoped cache path).
- `gnx-system` (~649 lines): THE deep skill. Rebuilt current for game 1.38 / GNX v1.3.14. Absorbed gn-modding's vanilla-architecture reference (sprite arrays, goblin classes 0-3, cell/class tables, core rules, sprite naming, diff-output format). Added: props.json/prop_registry/s_slot_prop.gml, birth_spr (T58/T59), correct test range (T01-T45 + T54-T59), atlas regression history, ej-dispatch gate, class_map skin fix, auto-injected body layers, shelved-features notes. Description broadened to also catch gn-modding's triggers.
- `gn-modding`: retired -> 14-line deprecation stub pointing to gnx-system. User can delete.
- `gnx-mod-building` (~273 lines): kept as the JSON-modder companion. Staleness fixed: version ["1.38"], props.json + portraits/ in folder layout + manifest keys + schema, birth_spr in classes.json, Python 3.9+, test range, gml/travel_map noted as shelved no-ops, fixed/class_map draw notes.
- `gmlc-integration` (~218 lines): kept SEPARATE per user. Added SHELVED banner (not shipped since v1.3.11, files in gml_shelved/, revive steps). Integration record retained as revival reference. Description updated so it triggers on "revive GMLC" not general scripting.
Graphene now owns the subsystem map / globals / gotchas; skills own procedural workflows + curated reference shapes + auto-trigger + offline fallback.
