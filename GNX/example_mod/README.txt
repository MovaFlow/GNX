GNX Example Mod
================

A reference mod showcasing every GNX JSON feature. Not playable (sprites are
paths only), but every field and structure a modder might need is represented.


FILES
-----

manifest.json   Entry point. Declares mod_id, version, content files, save_state fields.
classes.json    3 classes demonstrating all variants:
                - WITCH: standard, non-special, has_hair, cape, full clothing (std+big+tent),
                  full naked layer (std+big+tent) with leg_0/leg_1/leg_2 variants,
                  carry_base_spr (per-leg struct form), raid_spawns, birth_class,
                  icon + icon_hair, fap_mul/bap_mul, preg_c_override, "folder" field,
                  voice (fixed moan bank + pitch), milk_lvl, sell_lvl 2 (the trader buys
                  her from level 2; 1.5.2)
                  and a class monster_art swap (1.5.2, guide 16.7)
                - SIREN: special (is_special:true), gb1_breast_d2, cage_escape,
                  mon_spr_overrides (patrol + ogre_touch + shrine_bg/dirt/sign +
                  ogre_chain_body), spr_array/spr_c_array clothing_big, "max_row" field,
                  sell_lvl -1 (never sold to the trader; 1.5.2)
                - PEASANT override: override:true with class_id:0, partial clothing
cells.json      9 cells and an extend entry demonstrating all slot types, dispatch modes, and v1.4.5+ features:
                - HEX ROOM: standard (slot_type 0), base+class mode, full goblin sprites
                  and a monster_art block (1.5.2; game sprite names, as this mod ships no strips;
                  guide 10.8)
                - RITUAL: standard (slot_type 0), fixed mode, spr_array/spr_c_array,
                  sfx_type:"bj" (marks it an oral cell for the BJ sound pools)
                - ARENA: standard (slot_type 0), class_map mode, per-class sprite dispatch
                  with default fallback and a WITCH-specific entry. Demonstrates cross-mod
                  string refs in class keys. 1.5.2: a clothing variant list in the WITCH's
                  loop (guide 7.7a), by_mon_type in a class_map phase (guide 10.4) and a
                  leg_2 entry for Peasants (guide 10.5)
                - SIREN POOL: large (slot_type 2), birth_classes
                - BINDING: tent (slot_type 3)
                - GRAND HALL: XL (slot_type 6), category "xl_breed"
                - PLEASURE PIT patch: patches vanilla h_type 2, by_class SIREN override
                - DUET STAGE: required_class as array (["WITCH", "SIREN"])
                - extend entry: adds the WITCH to another mod's class_map cell
                  (another_mod.ALTAR, not installed here, so only a log line; guide 12.4a)
quests.json     Quest chain with all features:
                - Portraits (133x113 px) and popups
                - Notification and quest event types
                - Event chaining via next_event
                - All 22 condition types listed in _all_condition_types (a reference, never
                  read), including h_type lists, category and label (1.5.2)
                - Side effects set_state, add_gold, add_food, unlock_cell, unlock_class and
                  create_unit (1.5.2)
                - A quest with several objectives and a captive as reward
                  (arena_builder_quest, 1.5.2)
                - All hooks: post_raid_win, post_raid, post_raid_loss, cell_built, frame
                - Cage escape event (siren_hint, fired from classes.json)
                - Frame completion hook quest (passive_gold_quest)
tools.json      Debug menu with all 38 action types across 9 categories.
                - Toggle buttons (toggle = save_state key string)
                - Guard conditions on buttons
                - Keybinds: single key, modifier key, range with {n} substitution
                - Continuous effects (mood_lock)
                NOTE: tool actions use numeric IDs only (no string ref resolution).
                Use numeric class_id and h_type values.
sounds.json     Sound system reference:
                - voice_banks (soft, loud): named moan-clip pools
                - sfx pools (orgasm, bj_slurp, bj_gag, bj_moan, bj_breathe)
                - voice_map: fixed voice for vanilla classes 10 (Nyx) and 13 (Cat)
                - settings_defaults: initial SOUND-page slider values
                Clips are .ogg paths only (like the sprites). NOTE: audio MUST be
                OGG Vorbis; runtime loading (audio_create_stream) rejects .wav.
                See also classes.json WITCH "voice" and cells.json RITUAL "sfx_type".

raids.json      Raid stages of the example map (modding guide 27):
                - WITCH HUT: open from the start, two levels, Witch pool, finds,
                  win rewards, per-level xp, a blueprint piece as loot, a cart path
                - SIREN COVE: unlocked by stage_cleared on WITCH HUT (a bare stage
                  name), on_discover event, curved cart route, Siren boss
                manifest.json map_info also shows nest and vanilla_stages (the
                Mountain hidden, the Castle's reward replaced on this map).


CELL DISPATCH MODES
-------------------

The 5 cells demonstrate all 3 dispatch modes:

  base+class (HEX ROOM): Cell provides base_body type, class_registry provides
    clothing sprites. Standard approach for most cells.

  fixed (RITUAL): Cell controls human sprites directly via spr_array/spr_c_array.
    Class clothing ignored. Good for shrines, single-pose scenes.

  class_map (ARENA): Per-class sprite dispatch. Each class_id can have its own
    spr_array/spr_c_array entry. Classes not listed fall back to "default".
    Solves multi-mod row conflicts. Cross-mod string refs in class keys are
    resolved automatically after all mods load.


NAKED LAYER NOTES
-----------------

The WITCH class demonstrates the full naked layer system for non-special classes:

  naked_standard: phase_1 + phase_2, each with leg_1/leg_2/leg_0
  naked_big:      start/idle/loop, each with head/breast (shared) + leg_1/leg_2 (flat)
                  + leg_0 (sub-object with own head/breast/leg)
  naked_tent:     phase_1/phase_2/phase_4, each with leg_1/leg_2/leg_0

leg_0 always uses different head/breast sprites (_3 suffix in vanilla) because
that variant has a distinct base body pose.

carry_base_spr uses the per-leg struct form: {"leg_1": ..., "leg_2": ..., "leg_0": ...}
The simple string form is also valid when all legs share the same sprite.


SPRITES
-------

All sprite paths are placeholders. To make this mod functional:

1. Create strips/ and portraits/ folders
2. Supply horizontal sprite strips as PNG files at the referenced paths
3. Frame dimensions: standard cells 200x200, large 300x200, portraits 133x113
4. Frame counts must match the "frames" value in the sprites dict
5. Use gnx_pack_strips.py to pack per-frame folders into strips

Optional sprite dict fields:
  "folder"   - override folder name for gnx_pack_strips (see WITCH idle_hair)
  "max_row"  - limit rows for special classes with fewer skins (see SIREN idle_head)
  "canvas_w" / "canvas_h" - pad sprite to target canvas size (see WITCH icons)


STRING REFS
-----------

Cross-references between files use "mod_id.Name" format:
  "example_mod.WITCH"      -> resolves to WITCH's hash-assigned class_id
  "example_mod.HEX ROOM"   -> resolves to HEX ROOM's hash-assigned h_type

These are resolved at load time in classes.json, cells.json, and quests.json.
NOTE: tools.json actions do NOT support string refs. Use numeric IDs there.
