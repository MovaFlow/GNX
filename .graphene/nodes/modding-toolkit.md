---
type: subsystem
summary: Modder-facing authoring surface: the public modding guide + tutorial + schema docs, the reference example_mod, and Python scaffolding/packing scripts.
entry_points:
  - docs/GNX_MODDING.md
  - docs/TUTORIAL.md
  - GNX/example_mod/README.txt
covers:
  - docs/
  - GNX/example_mod/
  - tools/scaffold_class.py
  - tools/scaffold_cell.py
  - tools/generate_class.py
  - tools/generate_cell.py
  - tools/build_mod.py
  - tools/export_class_sprites.py
  - tools/gnx_pack_strips.py
  - README.md
  - CHANGELOG.md
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"docs":"GNX_MODDING.md (1798 lines, full schemas), TUTORIAL.md (644), QUESTS_SCHEMA.md (172)","example_mod":"canonical schema reference — classes/cells/props/quests/tools/sounds .json","json_files":"classes.json cells.json props.json quests.json tools.json sounds.json manifest.json","note":"two example_mod copies: docs/example_mod and GNX/example_mod"}
edges:
  - to: gnx-registries type: related_to reason: docs + scaffolding scripts + example_mod define the JSON schemas the registries consume
  - to: atlas-sprites type: related_to reason: gnx_atlas_pack.py and gnx_pack_strips.py are the modder-side of the atlas/sprite pipeline
---

- v1.3.14 added two content types beyond the CLAUDE.md list: props.json (custom decorative props for edit-mode menu, save/load + orphan sanitize, T59) and birth_spr in classes.json (per-cell-type per-species infant/birth sprites, T58). <!-- id:0065 -->
