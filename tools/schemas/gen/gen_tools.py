"""Writes tools.schema.json (needs common.schema.json from gen_quests.py). See gen_quests.py."""
import json, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
U = 'https://raw.githubusercontent.com/MovaFlow/GNX/main/tools/schemas/'
C = 'common.schema.json#/definitions/'


def typed(types, desc):
    allof = []
    for t, (params, req, tdesc) in types.items():
        props = {"type": {"const": t}}
        props.update(params)
        allof.append({"if": {"properties": {"type": {"const": t}}, "required": ["type"]},
                      "then": {"description": tdesc, "properties": props, "required": ["type"] + req,
                               "patternProperties": {"^_": {}}, "additionalProperties": False}})
    return {"type": "object", "description": desc, "required": ["type"],
            "properties": {"type": {"enum": list(types)}}, "allOf": allof}


N = {"type": "number"}
I = {"type": "integer"}
S = {"type": "string"}
B = {"type": ["boolean", "integer"]}
REF = {"$ref": C + "ref"}
SPECIES = {"type": "integer", "minimum": 0, "maximum": 3, "description": "0 goblin, 1 hobgoblin, 2 tentacle, 3 ogre."}
CLS = {"type": "integer", "minimum": 0, "maximum": 3, "description": "The troop class 0-3 of that species."}
SET_VAL = ["mood", "food", "money", "orb_num", "day_timer", "day", "cart_spd", "add_range", "sfx_vol", "bgm_vol", "alpha_type", "crate_alpha_type", "mon_alpha", "crate_alpha", "show_head", "ui_place"]
SET_VAR = ["w_spd", "gnx_perf_enabled", "gnx_debug_verbose", "gnx_force_capture_100", "gnx_free_floor_copy", "gnx_trace_entities", "gnx_perf_hud", "gnx_cull_step_off", "gnx_econ_on"]

action = typed({
    "add_gold": ({"amount": N}, ["amount"], "Adds gold; negative values subtract."),
    "add_food": ({"amount": N}, ["amount"], "Adds food."),
    "add_milk": ({"rarity": {"type": "integer", "minimum": -1, "maximum": 4}, "amount": N}, [], "Adds milk of rarity 0-4; -1 adds amount of every rarity."),
    "add_orbs": ({"amount": N}, ["amount"], "Adds orbs."),
    "give_item": ({"item": S, "amount": {"type": "integer", "minimum": 1}, "item_type": I, "data": N, "level": N}, [], "Gives a mod item (item, amount); or with item_type, data, level one inventory item."),
    "give_blueprint": ({"h_type": REF, "fragment": B, "lvl": {"type": "integer", "minimum": 0, "maximum": 3}}, ["h_type"], "Gives a complete blueprint, or with fragment: true a fragment."),
    "give_prop": ({"prop_id": {"type": ["string", "integer"]}}, ["prop_id"], "Unlocks a prop in the edit-mode menu."),
    "spawn_mon": ({"species": SPECIES, "class": CLS, "amount": N}, ["species", "amount"], "Adds monsters to that class, or without class to each of the four."),
    "set_troop_level": ({"species": SPECIES, "class": CLS, "value": N}, ["species", "class", "value"], "Sets the level of that monster class."),
    "add_troop_exp": ({"species": SPECIES, "class": CLS, "amount": N}, ["species", "class", "amount"], "Adds experience through the normal level-up logic."),
    "set_skill_level": ({"species": SPECIES, "class": CLS, "value": N}, ["species", "class", "value"], "Sets the skill level of that monster class."),
    "set_troop_size": ({"value": {"type": "integer", "minimum": 0, "maximum": 7}}, ["value"], "Sets the maximum troop size: 0 = 10 ... 7 = unlimited."),
    "create_unit": ({"class_id": REF, "level": N}, ["class_id"], "Puts a new captive in the first free prison slot."),
    "create_unit_cage": ({"class_id": REF, "level": N}, ["class_id"], "Adds a new cage slot holding a new captive."),
    "unlock_boss": ({"index": {"type": "integer", "minimum": 0, "maximum": 4}}, ["index"], "Starts the intro of a locked boss: 0 cow, 1 Nyx, 2 goddess, 3 Morrigan, 4 Lilith."),
    "unlock_stage_next": ({"stage": {"type": "integer", "minimum": 0, "maximum": 3}}, ["stage"], "Discovers a raid stage, or raises its highest level by one."),
    "unlock_breeds": ({}, [], "Unlocks all breeding tips."),
    "unlock_cell": ({"h_type": REF}, ["h_type"], "Adds the cell to its build menu tab."),
    "unlock_prop": ({"prop_id": {"type": ["string", "integer"]}}, ["prop_id"], "Same as give_prop."),
    "unlock_raid": ({}, [], "Enables the raid button."),
    "unlock_all_cells": ({}, [], "Unlocks every cell in every build list."),
    "add_floor": ({}, [], "Adds a cave floor."),
    "set_day": ({"value": {"type": "number", "minimum": 1}}, ["value"], "Sets the day counter."),
    "add_day_time": ({"amount": N}, ["amount"], "Adds to the day timer."),
    "set_speed": ({"target": {"enum": ["world", "cart", "range"]}, "value": N}, ["target", "value"], "world: game speed 0-10; cart: raid cart speed 0-10; range: extra cell range 0-20."),
    "swap_mouse": ({}, [], "Swaps the mouse buttons for moving the camera and selecting."),
    "show_debug_overlay": ({"enable": B}, [], "Shows or hides GameMaker's debug overlay."),
    "set_val": ({"key": {"enum": SET_VAL}, "value": N}, ["key", "value"], "Sets one game value (guide 17.6)."),
    "set_var": ({"key": {"enum": SET_VAR}, "value": N}, ["key", "value"], "Sets one global setting (guide 17.6)."),
    "reload_mods": ({}, [], "Autosaves, reads every mod's files again and loads the autosave back (guide 17.3)."),
    "reroll_shop": ({}, [], "Re-rolls the raid shop stock (raid screen open)."),
    "reroll_trade": ({}, [], "Re-rolls the trade stock (raid screen open)."),
    "reroll_encounters": ({}, [], "Re-rolls the encounters of the open stage (raid screen open)."),
    "set_state": ({"key": S, "value": {"type": ["number", "string", "boolean"]}}, ["key", "value"], "Sets a key in your mod's save state."),
    "set_continuous": ({"key": S, "value": B}, ["key", "value"], "Starts or stops a continuous effect (guide 17.9). The field is value, not enable."),
    "fire_event": ({"event_id": {"type": ["string", "integer"]}}, ["event_id"], "Fires a quest event, written with your folder name (\"my_mod.witch_intro\")."),
    "fire_trigger": ({"hook": S}, ["hook"], "Runs the quest triggers of that hook now, from all mods."),
    "popup": ({"text": S}, ["text"], "Shows a popup; can be a popup key (\"my_mod.<key>\")."),
    "play_sfx": ({"sfx_type": I}, ["sfx_type"], "Plays a vanilla sound (sfx_type, not type)."),
    "travel_map": ({"target": S, "label": S}, ["target"], "Opens the travel selector for that map (guide 21)."),
}, "A tool action (guide 17.6).")

guard = typed({
    "boss_locked": ({"index": {"type": "integer", "minimum": 0, "maximum": 4}}, ["index"], "That boss is still locked."),
    "boss_unlocked": ({"index": {"type": "integer", "minimum": 0, "maximum": 4}}, ["index"], "That boss is unlocked."),
    "stage_undiscovered": ({"stage": {"type": "integer", "minimum": 0, "maximum": 4}}, ["stage"], "That raid stage is not discovered yet."),
    "has_unit_slot": ({}, [], "The prison has a free slot."),
    "on_screen": ({"screen": {"description": "Ignored."}}, [], "The raid screen is open."),
}, "One condition checked before a button runs (guide 17.7).")

# a guard of another type is read as a quest condition (scr_gnx_eval_tool_guard -> scr_gnx_eval_condition)
_cond = json.load(open('common.schema.json', encoding='utf-8'))['definitions']['condition']
guard['properties']['type']['enum'] += _cond['properties']['type']['enum']
guard['allOf'] += json.loads(json.dumps(_cond['allOf']).replace('"#/definitions/ref"', '"' + C + 'ref"'))
guard['description'] += " A guard of another type is a quest condition (QUESTS_SCHEMA.md)."

KEY = {"type": "string", "pattern": "^(F([1-9]|1[0-2])|[A-Z]|[0-9]|space|tab|escape|0-9)$",
       "description": "F1-F12, A-Z (capitals), 0-9 (number row), space, tab, escape, or the range \"0-9\"."}

tools = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": U + "tools.schema.json",
    "title": "GNX tools.json",
    "description": "Buttons in the settings window's DEBUG > TOOLS menu, and keybinds. Modding guide section 17.",
    "type": "object",
    "properties": {
        "$schema": S,
        "categories": {"type": "array", "items": {"$ref": "#/definitions/category"}},
        "keybinds": {"type": "array", "items": {"$ref": "#/definitions/keybind"}},
    },
    "patternProperties": {"^_": {}},
    "additionalProperties": False,
    "definitions": {
        "action": action,
        "guard": guard,
        "category": {
            "type": "object", "required": ["label"],
            "description": "A TOOLS entry: buttons, or sub-menus (categories). Without label the game errors.",
            "properties": {
                "label": S,
                "buttons": {"type": "array", "items": {"$ref": "#/definitions/button"}},
                "categories": {"type": "array", "items": {"$ref": "#/definitions/category"}},
            },
            "patternProperties": {"^_": {}}, "additionalProperties": False},
        "button": {
            "type": "object", "required": ["label"],
            "description": "Without label the game errors (guide 17.4).",
            "properties": {
                "label": S,
                "actions": {"type": "array", "items": {"$ref": "#/definitions/action"}},
                "popup": S,
                "toggle": {"type": "string", "description": "Makes it an ON/OFF button; the save-state key that stores ON or OFF."},
                "undo_actions": {"type": "array", "items": {"$ref": "#/definitions/action"}},
                "undo_popup": S,
                "guard": {"$ref": "#/definitions/guard"},
                "guard_fail_popup": S,
            },
            "patternProperties": {"^_": {}}, "additionalProperties": False},
        "keybind": {
            "type": "object", "required": ["key"],
            "properties": {
                "key": KEY,
                "modifier": {"enum": ["none", "shift", "ctrl", "alt"]},
                "actions": {"type": "array", "items": {"$ref": "#/definitions/action"}},
                "action_per_key": {"type": "object", "required": ["type"], "properties": {"type": action["properties"]["type"]}, "description": "One action for \"0-9\"; its value is replaced with the pressed digit (so \"{key}\" is fine there)."},
                "popup": S,
                "popup_template": {"type": "string", "description": "Message for \"0-9\"; the first {key} becomes the digit."},
            },
            "patternProperties": {"^_": {}}, "additionalProperties": False},
    },
}
json.dump(tools, open('tools.schema.json', 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=False)
print('ok')
