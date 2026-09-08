---
type: subsystem
summary: Runtime sprite loading and the optional texture atlas: sprite cache, SprRef indirection, uv.json loader, gnx_draw_sprite_* wrappers, and the modder-side atlas packer.
entry_points:
  - tools/gnx_atlas_pack/gnx_atlas_pack.py
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - ATLAS_SYSTEM_README.md
covers:
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - tools/gnx_atlas_pack/
  - tools/gnx_pack_strips.py
  - ATLAS_SYSTEM_README.md
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"cache":"global.gnx_sprite_cache ds_map keyed base_dir+key; global.gnx_runtime_sprites tracking array; scr_gnx_cleanup_sprites on exit","resolve":"gnx_resolve_sprite (~3378), gnx_load_sprite_frames (~3478)","atlas_runtime":"gnx_atlas_resolve_ref (~10655), gnx_load_atlas_mod (~10698); draw/query wrappers gnx_draw_sprite_ext/gnx_sprite_get_number/width/height (~10529-10820)","atlas_rule":"sprite validity uses sprite_exists() NEVER is_real (sprites are a ref type)","regression_history":"v1.3.14 restored gnx_draw_sprite_ext + gnx_sprite_get_* wrappers on registry-sourced draw calls — invisible sprites when 4+ mods in atlas mode"}
edges:
  - to: modding-toolkit type: related_to reason: gnx_atlas_pack.py and gnx_pack_strips.py are the modder-side of the atlas/sprite pipeline
---

- Two modes: non-atlas (per-frame PNG strips -> sprite_add per sprite, ~160+ sprites/mod, slow boot) and atlas (gnx_atlas_pack.py pre-packs strips into atlas_N.png + uv.json, 4+ mods drop from ~373 texture pages to ~7, boot 94s->1.8s). Runtime auto-detects atlas/ folder in the mod. <!-- id:0ff5 -->
- Sprite cache (global.gnx_sprite_cache ds_map) + runtime tracking array persist across scr_create_initials() calls so returning to menu is instant and game_end cleanup is ~1-2s instead of 10s. Cache destroyed only on true game exit (s_button_activate case 51/button 2). <!-- id:56b3 -->
