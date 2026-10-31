"""Writes cells.schema.json. See gen_quests.py."""
import json, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
U = 'https://raw.githubusercontent.com/MovaFlow/GNX/main/tools/schemas/'
C = 'common.schema.json#/definitions/'
OPEN = {"patternProperties": {"^_": {}}, "additionalProperties": False}


def obj(props, desc=None, **extra):
    o = {"type": "object", "properties": props}
    o.update(OPEN)
    if desc:
        o["description"] = desc
    o.update(extra)
    return o


N = {"type": "number"}
INT = {"type": "integer"}
S = {"type": "string"}
B = {"type": ["boolean", "integer"]}
L = {"type": "array"}
SPR = {"$ref": "#/definitions/spr"}
NUM_OR_LIST = {"type": ["number", "array"]}


def d(x, desc):
    y = dict(x)
    y["description"] = desc
    return y


CATS = ["breed", "utility", "pleasure", "b_breed", "b_utility", "b_other", "t_breed", "t_utility", "xl_breed", "ug_breed"]
PHASE_KEYS = r"^phase_([0-5]|idle_start|start_loop|loop_ej|ej_birth)$"

# underground class_map entries: own milk / newborn strips, written as the cell's own (guide 24)
UG_ART = {"description": "Underground cells: this class's own strips, written as the cell's own.", "type": ["object", "string", "integer"]}

# per phase of a fixed / class_map human_spr: special-class style tables, optional by_class (fixed mode)
hum_phase = obj({
    "spr_array": d(L, "The captive's body, slot by slot (guide 10.3)."),
    "spr_c_array": d(L, "Her clothes, slot by slot."),
    "by_class": d({"type": "object"}, "Fixed mode: some classes get their own sprites (guide 10.4)."),
    "by_mon_type": d({"type": "object"}, "Inside a by_class entry: per monster type (guide 10.4)."),
})
human_spr = {
    "type": "object",
    "description": "How the captive is drawn (guide 10.1): mode base+class (with base_body), fixed (phase tables) or class_map (default + classes).",
    "properties": {
        "mode": {"enum": ["base+class", "fixed", "class_map"]},
        "base_body": {"enum": ["standard", "big", "tent"]},
        "default": {"type": "object", "description": "class_map: the phases for classes not listed.",
                    "properties": {"milk_spr": UG_ART, "infant_spr": UG_ART},
                    "patternProperties": {PHASE_KEYS: {"$ref": "#/definitions/hum_phase"}, "^_": {}}, "additionalProperties": False},
        "classes": {"type": "object", "description": "class_map: class ID or reference -> phases (guide 10.5).",
                    "additionalProperties": {"type": "object", "properties": {"milk_spr": UG_ART, "infant_spr": UG_ART}, "patternProperties": {PHASE_KEYS: {"$ref": "#/definitions/hum_phase"}, "^_": {}}, "additionalProperties": False}},
    },
    "patternProperties": {PHASE_KEYS: {"$ref": "#/definitions/hum_phase"}, "^_": {}},
    "additionalProperties": False,
}
PAIR = {"description": "A sprite, or a pair { alpha (fill), line (outline, optional) } (guide 10.9).",
        "if": {"type": "object"}, "then": obj({"alpha": SPR, "line": SPR}), "else": SPR}
VARIANTS = obj({k: PAIR for k in ("leg_any", "leg_1", "leg_2", "cow", "lilith")},
               "Variants: the class (cow, lilith), then the captive's leg (leg_1, leg_2), then leg_any (guide 10.9). A pair directly here is ignored.")
HEAD = {"description": "One pair, or a list of which the first two are used 50/50.",
        "if": {"type": "array"}, "then": {"items": PAIR}, "else": PAIR}
CLASS_V = {"description": "One sprite, or class variants default / cow / nyx / lilith / morrigan / cat (guide 10.9).",
           "if": {"type": "object"}, "then": obj({k: SPR for k in ("default", "cow", "nyx", "lilith", "morrigan", "cat")}), "else": SPR}
mon_start = obj({"body": VARIANTS, "hand": PAIR, "pen": SPR, "touch": CLASS_V,
                 "hand_xscale": {"const": "random", "description": "Mirror the hand at random (start only)."}},
                "Monster sprites of the start step (guide 10.9): no head or enter here.")
mon_phase = obj({"head": HEAD, "body": VARIANTS, "hand": VARIANTS, "pen": SPR, "touch": CLASS_V, "enter": CLASS_V},
                "Monster sprites of a loop / ej / intermission phase (guide 10.9).")
mon_spr = {"type": "object", "description": "Monster sprites per phase (guide 10.8).",
           "properties": dict({"start": {"$ref": "#/definitions/mon_start"}},
                              **{k: {"$ref": "#/definitions/mon_phase"} for k in ("loop", "ej", "idle_start", "start_loop", "loop_ej", "ej_birth", "ej_end")}),
           **OPEN}

physical = obj({
    "allow_preg": d(B, "Captives can get pregnant here."),
    "max_mon_num": d(INT, "How many monsters fit."),
    "anal": d({"type": ["boolean", "integer"]}, "-1 = never, or true / false (guide 9.2)."),
    "slot_dirt_init": N,
    "layers": d(L, "What gets drawn (guide 9.4)."),
    "scr_idle": d(S, "Idle scene script (guide 9.5)."),
    "scr_h": d({"type": "array", "items": S}, "Scene scripts in order (guide 9.5)."),
    "scr_draw": d(S, "Draw script (guide 9.6)."),
    "hand_x": L, "hand_y": L, "hand_xscale": L, "hand_angle": L,
    "hand_frames": d({"type": "object"}, "Hand frames per phase (guide 9.7)."),
    "sq_x": N, "sq_y": L, "sp_x": N, "sp_y": L, "sp_anim_x": N, "sp_anim_y": N,
    "sp_spr": SPR,
    "fx_floor": N,
    "character_row": d(N, "Row of the captive's strips (guide 9.3)."),
    "required_class": d({"type": ["number", "string", "array"]}, "Classes allowed in (guide 9.9)."),
    "slot_range": N, "range_draw_func": S, "scr_unoccupy": S,
    "sign_y_base": N, "sign_y_jitter": N,
    "mon_placements": d(L, "Places for several monsters (guide 11.1)."),
    "mon_positions": d(L, "Where each place is drawn (guide 11.3)."),
    "transfer": B,
    "frames": d({"type": ["object", "number", "array"]}, "Frame counts per phase (guide 22.1)."),
    "start_loops": NUM_OR_LIST, "ej_start": N, "ej_hold": N, "ej_holds": NUM_OR_LIST,
    "ej_return": d(N, "Frame the ej goes back to for its next hold (default ej_start), counted from 0."),
    "join_skip": d(B, "Independent places: a monster coming in later starts where the captive is."),
    "loop_scale": B,
    "intermissions": d({"type": "object"}, "One-shot sub-phases (guide 23)."),
    "underground": N, "underground_gap": N,
    "speed": d({"type": ["object", "number"]}, "Frames per second per phase (guide 24.3)."),
    "milk_items": N, "milk_interval": N, "milk_step": N, "milk_num": N,
    "birth_rounds": N, "birth_rest": N,
    "infant_labour_frames": N, "infant_speed": N, "infant_time": N,
    "bar_glow_rep": N, "drink_num": N, "mon_index": L,
    "blink_spr": SPR, "anim_struct_overrides": {"type": "object"},
    "visual": B, "slot_front": SPR, "sp_place_init": B, "set_timer": N, "slot_h": B,
    "scr_slot_step": S, "scr_slot_base": S,
    "candle_index": N, "clone_wait": N, "extra_spawn_part": B, "dirt_fix_inc": B, "death_fix_inc": B, "del_item_type": N,
}, "How the cell behaves (guide 9).")

ART = {"description": "One sprite or an object of sprites (guide 24).", "type": ["object", "string", "integer"]}
cell = obj({
    "h_type": {"type": ["integer", "string"], "description": "The cell's ID; a vanilla number makes the entry a patch (guide 8.3, 12)."},
    "name": d(S, "Cell name: references (\"my_mod.ALTAR\"), the hash ID, the build menu."),
    "category": {"enum": CATS, "description": "Build menu tab and cell size (guide 8.4)."},
    "locked": d(B, "Not in the build menu until unlocked."),
    "mon_types": {"type": "array", "items": {"type": "integer", "minimum": 0, "maximum": 3}, "description": "Which monsters come: 0 goblin, 1 hobgoblin, 2 tentacle, 3 ogre (guide 8.5)."},
    "slot_type": d(INT, "Only affects the default base_body (guide 8.4)."),
    "price": N,
    "code_text": S,
    "spawn_info": obj({"coin": N, "mood": N, "coin_mul": B, "mood_mul": B}, "Gold and mood (guide 8.6)."),
    "physical": physical,
    "human_spr": human_spr,
    "mon_spr": mon_spr, "mon_spr_hob": mon_spr, "mon_spr_ogr": mon_spr,
    "sfx_type": d(S, "Sound set (guide 18.5)."),
    "tent_spr": ART, "milk_spr": ART, "infant_spr": ART, "band_spr": ART,
    "sprites": {"$ref": C + "sprites"},
}, "One cell, or a patch of a vanilla cell (guide 8, 12).",
    patternProperties={"^mon_spr(_hob|_ogr)?_p[0-9]+$": mon_spr, "^_": {}})

cells = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": U + "cells.schema.json",
    "title": "GNX cells.json",
    "description": "New cells and patches of vanilla cells. Modding guide sections 8-12, 22-24.",
    "if": {"type": "array"},
    "then": {"items": {"$ref": "#/definitions/cell"}},
    "else": obj({"$schema": S, "cells": {"type": "array", "items": {"$ref": "#/definitions/cell"}}}),
    "definitions": {
        "spr": {"type": ["string", "integer"], "description": "\"gnx:<key>\", a vanilla sprite name, or -1 for none."},
        "cell": cell,
        "hum_phase": hum_phase,
        "mon_phase": mon_phase,
        "mon_start": mon_start,
    },
}
json.dump(cells, open('cells.schema.json', 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=False)
print('ok')
