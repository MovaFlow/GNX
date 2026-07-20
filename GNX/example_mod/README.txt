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
                  icon + icon_hair, fap_mul/bap_mul, preg_c_override, "folder" field
                - SIREN: special (is_special:true), gb1_breast_d2, cage_escape,
                  mon_spr_overrides (patrol + ogre_touch), spr_array/spr_c_array clothing_big,
                  "max_row" field
                - PEASANT override: override:true with class_id:0, partial clothing
cells.json      4 cells demonstrating all slot types and modes:
                - HEX ROOM: standard (slot_type 0), base+class mode, full goblin sprites
                - RITUAL: standard (slot_type 0), fixed mode, spr_array/spr_c_array
                - SIREN POOL: large (slot_type 2), birth_classes
                - BINDING: tent (slot_type 3)
quests.json     Quest chain with all features:
                - Portraits (133x113 px) and popups
                - Notification and quest event types
                - Event chaining via next_event
                - All 12 condition types listed (disabled reference trigger)
                - All 5 side effect types used (set_state, add_gold, add_food,
                  unlock_cell, unlock_class)
                - All hooks: post_raid_win, post_raid, post_raid_loss, cell_built, frame
                - Cage escape event (siren_hint, fired from classes.json)
                - Frame completion hook quest (passive_gold_quest)
tools.json      Debug menu with all 38 action types across 9 categories.
                - Toggle buttons with save_key persistence
                - Guard conditions on buttons
                - Keybinds: single key, modifier key, range with {n} substitution
                - Continuous effects (mood_lock, inf_food)


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

These are resolved at load time. Never hardcode numeric IDs.
