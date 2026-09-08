---
type: subsystem
summary: Runtime sound loading: moddable voice banks and SFX pools, per-unit voice assignment, positional playback, BJ-cell detection, and the 6-slider sound settings UI.
entry_points:
  - GNX/gml/gml_GlobalScript_s_sfx.gml
  - GNX/gml/gml_GlobalScript_s_initials.gml
covers:
  - GNX/gml/gml_GlobalScript_s_sfx.gml
  - GNX/gml/gml_GlobalScript_s_initials.gml
  - GNX/gml/gml_GlobalScript_s_window_alpha.gml
  - GNX/example_mod/sounds.json
last_commit: 03ff8ced27b460b4c06cbb314338491c63e4390c
metadata: {"key_functions":"scr_gnx_load_sounds (~10121), gnx_resolve_sound (~10073), scr_gnx_generate_voice (~10258), scr_gnx_check_voice (~10303), scr_gnx_is_bj_cell (~10328); playback fns in s_sfx.gml","format":"sound files MUST be OGG Vorbis (audio_create_stream rejects WAV — fails silently)","voice_precedence":"sounds.json voice_map -> class_registry.voice_bank -> random; lvl 6/7 always random","gated":"global.gnx_has_sounds (false when no mod ships sounds.json)"}
edges:
  - to: ui-integration type: depends_on reason: sound settings sub-page (button 16, interact 9020) hooks the alpha settings window
---
