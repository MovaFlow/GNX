---
type: subsystem
summary: Deployment: install_foundation.csx patches all GNX .gml + GNX_assets sprites into data.win via G3M/UMT; diffs/ and gnx.patch hold the vanilla->GNX deltas.
entry_points:
  - GNX/install_foundation.csx
  - README.md
covers:
  - GNX/install_foundation.csx
  - GNX/diffs/
  - GNX/gnx.patch
  - GNX/GNX_assets/
  - fix_nullish.py
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"authoritative_copy":"E:/GNX_Work_folder/GNX/install_foundation.csx — deploy to G3M profile path on every change","phases":"1 GML code import (candidateDirs discovery) 2 GNX_assets PNG->sprite import (spr_ + filename, TextureWorker) 3 timing report to gnx_patch_timing.txt","g3m_quirks":"Project unavailable (CS0103); ScriptMessage suppressed; needs 'using ImageMagick;'","game_version":"1.38 (rebased from 1.33 in v1.3.14)"}
edges:
  - to: gnx-loader type: related_to reason: install_foundation.csx patches all the .gml files these subsystems live in into data.win
---

- CLAUDE.md at repo root is STALE (describes game 1.33 / v1.3.11). Current state: game 1.38, GNX v1.3.14.1 (CHANGELOG.md + README.md are truth). GNX/gml/ = active working set (only files GNX modifies, ~45 .gml + .bak); GNX/gml_138/ = full vanilla 1.38 decompile reference (155 files); GNX/gml_shelved/ = shelved GMLC compiler. <!-- id:a005 -->
