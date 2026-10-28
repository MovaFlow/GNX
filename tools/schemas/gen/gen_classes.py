"""Writes classes.schema.json. See gen_quests.py."""
import json, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
U = 'https://raw.githubusercontent.com/MovaFlow/GNX/main/tools/schemas/'
C = 'common.schema.json#/definitions/'

SPR = {"$ref": "#/definitions/spr"}
U_ = {"patternProperties": {"^_": {}}, "additionalProperties": False}


def obj(props, desc=None, required=None):
    o = {"type": "object", "properties": props}
    o.update(U_)
    if desc:
        o["description"] = desc
    if required:
        o["required"] = required
    return o


SPR_ARRAYS = {
    "spr_array": {"type": "array", "maxItems": 7, "items": SPR, "description": "Special-class table: the full body, slot by slot (guide 7.7): [0] unused, [1] head, [2] breast, [3] hand, [4] leg, [5] leg part, [6] cape."},
    "spr_c_array": {"type": "array", "maxItems": 7, "items": SPR, "description": "Special-class table: the clothes (guide 7.7): [0] hair, [1] head overlay, [2] breast, [3] hand, [4] leg, [5] leg part."},
}
LEG_ENTRY = obj({"hair": SPR, "head": SPR, "breast": SPR, "leg": SPR, "leg_part": SPR, "hand": SPR},
                "Sprites for one leg pose (guide 7.3; hand is read in clothing_tent only).")
LEGS = {k: {"$ref": "#/definitions/leg_entry"} for k in ("leg_0", "leg_1", "leg_2", "leg_any")}

# clothing_standard / clothing_tent phase: per-leg entries (normal class) or tables (special class)
phase_std = obj(dict(LEGS, cape=SPR, **SPR_ARRAYS), "A phase: one entry per leg pose (normal class) or spr_array / spr_c_array (special class).")
clothing_std = {"type": "object", "description": "Look in standard cells (guide 7.3): phase_1 idle, phase_2 loop (normal and special classes).",
                "properties": {"max_row": {"type": "integer", "description": "Special classes only (guide 16.2)."}},
                "patternProperties": {"^phase_[12]$": {"$ref": "#/definitions/phase_std"}, "^_": {}}, "additionalProperties": False}
clothing_tent = dict(clothing_std, description="Look in tentacle cells (guide 7.5): phase_1 idle, phase_2 loop, phase_4 birth.",
                     patternProperties={"^phase_[124]$": {"$ref": "#/definitions/phase_std"}, "^_": {}})
# clothing_big: start / idle / loop with sprites directly (normal), or phase_0-2 tables (special)
phase_big = obj({"head": SPR, "breast": SPR, "hair": SPR, "leg_1": SPR, "leg_2": SPR, "leg_any": SPR, **SPR_ARRAYS},
                "A big-cell phase: head, breast, hair and leg sprites (normal class) or spr_array / spr_c_array (special class).")
clothing_big = {"type": "object", "description": "Look in big cells (guide 7.4): start / idle / loop (normal class) or phase_0 / phase_1 / phase_2 (special class).",
                "properties": {k: {"$ref": "#/definitions/phase_big"} for k in ("start", "idle", "loop")},
                "patternProperties": {"^phase_[0-2]$": {"$ref": "#/definitions/phase_big"}, "^_": {}}, "additionalProperties": False}
clothing_giant = {"type": "object", "description": "Look in the vanilla GIANT cell (guide 7.6): phase_0 / 1 / 2 / 4 tables.",
                  "patternProperties": {"^phase_[0124]$": obj(SPR_ARRAYS), "^_": {}}, "additionalProperties": False}
# naked maps
naked_leg = obj({"head": SPR, "breast": SPR, "leg": SPR, "leg_part": SPR})
naked_std = {"type": "object", "description": "Bare body under the clothes in standard cells (guide 7.8): hand + phase_1 / phase_2 leg entries.",
             "properties": {"hand": SPR},
             "patternProperties": {"^phase_[12]$": obj({k: naked_leg for k in ("leg_0", "leg_1", "leg_2", "leg_any")}), "^_": {}},
             "additionalProperties": False}
naked_tent = dict(naked_std, description="Like naked_standard, with phase_1, phase_2, phase_4 (guide 7.8).",
                  patternProperties={"^phase_[124]$": obj({k: naked_leg for k in ("leg_0", "leg_1", "leg_2", "leg_any")}), "^_": {}})
naked_big_phase = obj({"head": SPR, "breast": SPR, "leg_1": SPR, "leg_2": SPR, "leg_any": SPR,
                       "leg_0": obj({"head": SPR, "breast": SPR, "leg": SPR})})
naked_big = obj({"hand": SPR, "start": naked_big_phase, "idle": naked_big_phase, "loop": naked_big_phase},
                "Bare body in big cells (guide 7.8): hand + start / idle / loop.")

SPECIES = {k: SPR for k in ("goblin", "hobgoblin", "tentacle", "ogre")}
STATE_SET = obj({"key": {"type": "string"}, "value": {"type": ["number", "string", "boolean"]}}, required=["key", "value"])
cage_escape = obj({
    "condition": {"$ref": C + "condition"},
    "base_chance": {"type": "number", "description": "Raises (negative: lowers) the escape chance (guide 15.2)."},
    "over_diff_scale": {"type": "number", "description": "How strongly the player's raid power changes the chance (default 300)."},
    "counter_key": {"type": "string", "description": "State key raised by 1 on every escape."},
    "popup": {"type": "string", "description": "Popup from your quests.json popups, shown on escape."},
    "on_escape_event": {"type": "string", "description": "Event fired once the counter reached escape_event_threshold."},
    "escape_event_threshold": {"type": "number"},
    "on_escape_state": STATE_SET,
    "on_survive_state": STATE_SET,
    "on_survive_event": {"type": "string"},
}, "Captives of this class may escape from the cage after a raid (guide 15.1).")

cls = obj({
    "name": {"type": "string", "description": "Class name: used in refs (\"my_mod.Witch\"), for the hash ID and in game."},
    "sprite_prefix": {"type": "string", "description": "Used by the tools (scaffold_class.py, gnx_pack_strips.py); the game ignores it."},
    "class_name": {"type": "string", "description": "Old name of name (birth_classes of old mods)."},
    "override": {"type": ["boolean", "integer"], "description": "true = change an existing class or create one at a fixed class_id (guide 6.2)."},
    "class_id": {"type": "integer", "description": "ID number, read only with \"override\": true."},
    "is_special": {"type": ["boolean", "integer"], "description": "One skin tone and its own clothing format, like Lilith or Nyx (guide 16)."},
    "has_hair": {"type": ["boolean", "integer"], "description": "true = 3 hair variants from the hair sprites; false = no hair layer."},
    "hand_color": SPR,
    "icon": SPR,
    "icon_hair": SPR,
    "default_leg": {"type": "integer", "minimum": 0, "maximum": 2, "description": "Fixed leg pose: 1 or 2, or 0 (kneeling)."},
    "scr_unit": {"type": "integer", "description": "Passive effect in a cell: 0 = milk refills like Hathor, 1 = pregnancies refill (guide 6.6)."},
    "only_listed_cells": {"type": ["boolean", "integer"], "description": "true = enters only cells whose required_class lists it."},
    "voice": obj({"bank": {"type": "string"}, "pitch": {"type": "number"}, "by_mon_type": {"$ref": "sounds.schema.json#/definitions/by_mon_type"}},
                 "Fixed moan voice with a bank of your own sounds.json (guide 18.3)."),
    "fap_mul": {"type": "number", "description": "Enemy HP the class adds to a raid encounter: fap_mul x unit level."},
    "bap_mul": {"type": "number", "description": "Enemy AP added: bap_mul x unit level."},
    "preg_c_override": {"type": "integer", "minimum": -1, "description": "How many times a unit can get pregnant; -1 = unlimited."},
    "preg_mon_type_override": {"type": "integer", "minimum": 0, "maximum": 3, "description": "Species of every child: 0 goblin, 1 hobgoblin, 2 tentacle, 3 ogre."},
    "sprites": {"$ref": C + "sprites"},
    "clothing_standard": clothing_std,
    "clothing_big": clothing_big,
    "clothing_tent": clothing_tent,
    "clothing_giant": clothing_giant,
    "naked_standard": naked_std,
    "naked_big": naked_big,
    "naked_tent": naked_tent,
    "carry_base_spr": {"description": "Ogre carry body: one sprite, or one per leg pose leg_0 / leg_1 / leg_2 (guide 6.5).",
                       "if": {"type": ["string", "integer"]}, "then": {}, "else": obj({"leg_0": SPR, "leg_1": SPR, "leg_2": SPR})},
    "raid_spawns": {"type": "array", "items": obj({
        "stage": {"type": "integer", "minimum": 0, "maximum": 4},
        "level": {"type": "integer", "minimum": 0, "maximum": 2},
        "weight": {"type": "number", "minimum": 0},
        "min_lvl": {"type": "integer", "minimum": 0, "maximum": 7},
        "max_lvl": {"type": "integer", "minimum": 0, "maximum": 7},
        "condition": {"$ref": C + "condition"},
        "max_per_encounter": {"type": "integer", "minimum": 0},
        "ap_override": {"type": "array", "minItems": 2, "maxItems": 2, "items": {"type": "number"}, "description": "[HP, AP] the unit adds instead of fap_mul / bap_mul. Ignored in the Tower."},
    }, "Adds the class to one raid pool (guide 13.2).", ["stage", "level"])},
    "trade_stage": {"type": "integer", "minimum": 0, "maximum": 4, "description": "The trader sells the class from that raid stage on (guide 13.5)."},
    "birth_class": obj({k: {"type": "integer", "minimum": 0, "maximum": 3} for k in ("goblin", "hobgoblin", "tentacle", "ogre")},
                       "Troop type (0-3) of children of each species (guide 14.2)."),
    "birth_classes": {"type": "array", "items": {"type": "integer"}, "description": "Old format of birth_class: [goblin, hobgoblin, tentacle, ogre] (guide 14.3)."},
    "birth_spr": obj({"birth_1": obj(SPECIES), "birth_2": obj(SPECIES), "bind_1": SPR, "bind_2": SPR,
                      "t_wall_1": SPR, "t_wall_2": SPR, "t_wall_3": SPR, "giant": SPR}, "Birth animations (guide 14.4)."),
    "post_raid": obj({"cage_escape": cage_escape}),
    "tower_boss_condition": {"$ref": C + "condition", "description": "The class is a Tower boss only while this holds (guide 15.3)."},
    "gb1_breast_d2": {**SPR, "description": "Second breast sprite in G.BANG 1 (guide 16.3)."},
    "mon_spr_overrides": {"type": "object", "description": "Monster sprites for this class in some vanilla cells, by key (guide 16.4-16.6).", "additionalProperties": SPR},
    "mon_sprite_swap": {"type": "object", "description": "Vanilla monster sprite name -> replacement, wherever it would be drawn on this class (guide 16.7).", "additionalProperties": SPR},
}, "One class (guide 6).")

classes = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": U + "classes.schema.json",
    "title": "GNX classes.json",
    "description": "A list of classes (captive types). Modding guide sections 6, 7, 13-16.",
    "type": "array",
    "items": {"$ref": "#/definitions/class"},
    "definitions": {
        "spr": {"type": ["string", "integer"], "description": "A sprite: \"gnx:<key>\" of this entry's sprites, a vanilla sprite name, or -1 for none (guide 5.4)."},
        "class": cls,
        "leg_entry": LEG_ENTRY,
        "phase_std": phase_std,
        "phase_big": phase_big,
    },
}
json.dump(classes, open('classes.schema.json', 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=False)
print('ok')
