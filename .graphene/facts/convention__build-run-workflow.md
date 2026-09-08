---
category: convention
subject: build-run-workflow
---

Framework dev loop: edit GNX/gml/*.gml -> deploy to the G3M profile at C:\Users\gbichon\AppData\Local\G3M\profiles\Default\GNX_TEST\ (gml/ + install_foundation.csx + GNX_assets/ all live there) -> launch that profile from G3M. Local test rig without G3M: E:\GNX_Work_folder\Game\ (GoblinNest.exe + data.win + Game\GNX_mods\gnx_test_mod). Dev mods also live at E:\TUTORIAL_TEST_GNX\GNX_mods\ and E:\GNX_Work_folder\Game\GNX_mods\. Mod authoring: tools/build_mod.py <mod_dir> <game_dir> packs strips (gnx_pack_strips.py) + verifies + deploys to <game_dir>/GNX_mods/. Boot success = gnx_debug.txt ends with "[GNX-TEST] N/N passed".
