"""Writes the quest conditions (into common.schema.json), quests.schema.json, and the manifest's map_info.unlock.
The schemas are generated where they repeat a lot (one block per condition / action / phase type); manifest,
items, sounds, lang, props and the rest of common are edited by hand. Run order: gen_quests, gen_tools,
gen_classes, gen_cells (tools reads the conditions written by gen_quests). Then run tools/test_schemas.py.
"""
import json, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
U = 'https://raw.githubusercontent.com/MovaFlow/GNX/main/tools/schemas/'
C = 'common.schema.json#/definitions/'


def typed(types, desc):
    """A discriminated union on "type": the enum, then one if/then per type with its own keys."""
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
S = {"type": "string"}
REF = {"$ref": "#/definitions/ref"}
ANY = {"type": ["number", "string", "boolean"]}
STAGE = {"type": "integer", "minimum": 0, "maximum": 4}

common = json.load(open('common.schema.json', encoding='utf-8'))
d = common['definitions']
d['ref'] = {"type": ["integer", "string"], "description": "A number, or a reference such as \"my_mod.NAME\" (\"NAME\" alone for your own mod)."}
d['condition'] = typed({
    "state_equals": ({"key": S, "value": ANY}, ["key", "value"], "The mod's save state key == value."),
    "state_gte": ({"key": S, "value": N}, ["key", "value"], "The mod's save state key >= value."),
    "state_lte": ({"key": S, "value": N}, ["key", "value"], "The mod's save state key <= value."),
    "unit_count": ({"class": REF, "value": N}, [], "Units of that class (all units without class) >= value (default 1)."),
    "gold_gte": ({"value": N}, ["value"], "Gold >= value."),
    "day_gte": ({"value": N}, ["value"], "The day counter >= value."),
    "day_every": ({"value": {"type": "integer", "minimum": 1}, "offset": {"type": "integer"}}, ["value"], "The day is a multiple of value (after subtracting offset). Meant for the day_start hook."),
    "has_item": ({"item": S, "value": N}, ["item"], "The inventory holds at least value (default 1) of that mod item."),
    "floor_gte": ({"value": N}, ["value"], "Floors >= value."),
    "cell_count": ({"h_type": REF, "value": N}, ["h_type"], "Built cells of that type >= value (default 1)."),
    "cell_built": ({"h_type": REF}, ["h_type"], "At least one cell of that type is built."),
    "cell_occupied": ({"h_type": REF}, ["h_type"], "At least one cell of that type has a captive."),
    "stage_discovered": ({"stage": STAGE}, ["stage"], "That raid stage is discovered."),
    "stage_cleared": ({"stage": STAGE, "min_level": {"type": "integer", "minimum": 0}}, ["stage", "min_level"], "That raid stage's highest cleared level >= min_level."),
    "boss_captured": ({"class": REF}, ["class"], "A unit of that class is in the cage."),
    "raid_won": ({}, [], "Always true (meaningful at the post_raid_win hook)."),
    "on_map": ({"map": S}, ["map"], "The player is on that map (\"vanilla\" = the village)."),
    "map_visited": ({"map": S}, ["map"], "The player has been on that map."),
    "map_unlocked": ({"map": S}, ["map"], "That map can be travelled to."),
}, "A quest condition (QUESTS_SCHEMA.md, Condition types).")
d['conditions'] = {"type": "array", "items": {"$ref": "#/definitions/condition"}}
json.dump(common, open('common.schema.json', 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=False)

AMOUNT = {"type": "number"}
side_effect = typed({
    "set_state": ({"key": S, "value": ANY}, ["key", "value"], "Sets the mod's save state key to value."),
    "add_gold": ({"amount": AMOUNT}, ["amount"], "Adds gold."),
    "add_food": ({"amount": AMOUNT}, ["amount"], "Adds food."),
    "give_item": ({"item": S, "amount": {"type": "integer", "minimum": 1}}, ["item"], "Puts that many (default 1) of a mod item into the inventory."),
    "take_item": ({"item": S, "amount": {"type": "integer", "minimum": 1}}, ["item"], "Takes that many (default 1) out."),
    "unlock_cell": ({"h_type": {"$ref": C + "ref"}}, ["h_type"], "Unlocks a cell in the build menu."),
    "unlock_class": ({"class": {"$ref": C + "ref"}}, ["class"], "Adds a class to the raid encounter pools."),
    "unlock_map": ({"map": S}, ["map"], "Opens a mod map in the travel menu for good."),
}, "A side effect, applied when the event fires (QUESTS_SCHEMA.md, Side effect types).")
for a in side_effect['allOf']:
    for k, v in a['then']['properties'].items():
        if v == REF:
            a['then']['properties'][k] = {"$ref": C + "ref"}
reward = typed({
    "gold": ({"amount": AMOUNT}, ["amount"], "Adds gold."),
    "food": ({"amount": AMOUNT}, ["amount"], "Adds food."),
    "blueprint": ({"h_type": {"$ref": C + "ref"}, "fragment": {"type": ["boolean", "integer"]}, "lvl": {"type": "integer", "minimum": 0, "maximum": 3}}, ["h_type"], "A complete blueprint (unlocks the cell), or with fragment: true one piece."),
    "prop": ({"prop_id": {"type": ["integer", "string"]}}, ["prop_id"], "Unlocks a prop in the customization menu."),
    "item": ({"item": S, "amount": {"type": "integer", "minimum": 1}}, ["item"], "A mod item (items.json)."),
}, "A quest reward (QUESTS_SCHEMA.md, Reward types).")

HOOKS = ["post_raid_win", "post_raid", "post_raid_loss", "cell_built", "day_start", "map_arrive"]
quests = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": U + "quests.schema.json",
    "title": "GNX quests.json",
    "description": "Portraits, popups, events (notifications and quests) and triggers. See docs/QUESTS_SCHEMA.md.",
    "type": "object",
    "properties": {
        "$schema": S,
        "portraits": {
            "type": "object",
            "description": "Portrait key -> PNG in the mod's portraits/ folder (133 x 113 per frame).",
            "additionalProperties": {
                "type": "object", "required": ["strip"],
                "properties": {"strip": {"type": "string", "description": "File name inside portraits/."}, "frames": {"type": "integer", "minimum": 1}},
                "patternProperties": {"^_": {}}, "additionalProperties": False}},
        "popups": {"type": "object", "description": "Popup key -> text.", "additionalProperties": {"type": "string"}},
        "events": {"type": "object", "description": "Event ID -> notification or quest.", "additionalProperties": {"$ref": "#/definitions/event"}},
        "triggers": {"type": "array", "items": {"$ref": "#/definitions/trigger"}},
    },
    "patternProperties": {"^_": {}},
    "additionalProperties": False,
    "definitions": {
        "side_effect": side_effect,
        "reward": reward,
        "dialog_line": {
            "type": "object", "required": ["text"],
            "properties": {
                "speaker": S,
                "portrait": {"type": ["string", "integer"], "description": "A key of portraits, -1 = the vanilla Lilith portrait, or 0-94 = a vanilla portrait frame."},
                "text": S},
            "patternProperties": {"^_": {}}, "additionalProperties": False},
        "event": {
            "type": "object", "required": ["type"],
            "properties": {
                "type": {"enum": ["notification", "quest"]},
                "dialog": {"type": "array", "items": {"$ref": "#/definitions/dialog_line"}, "description": "Without dialog, a notification fires silently."},
                "side_effects": {"type": "array", "items": {"$ref": "#/definitions/side_effect"}},
                "next_event": {"type": ["string", "null"], "description": "The event that follows (null = the chain ends)."},
                "quest_text": S,
                "reward": {"$ref": "#/definitions/reward"},
                "completion": {"$ref": C + "condition"},
                "completion_hook": {"enum": ["frame", "post_raid", "post_raid_win", "cell_built", "day_start"], "description": "When the completion condition is checked (default \"frame\": every frame). map_arrive and post_raid_loss are trigger hooks only."},
            },
            "patternProperties": {"^_": {}}, "additionalProperties": False},
        "trigger": {
            "type": "object", "required": ["event", "hook"],
            "description": "Fires the event every time the hook runs and all conditions hold (guard one-time events with a state key).",
            "properties": {
                "event": S,
                "hook": {"enum": HOOKS},
                "conditions": {"$ref": C + "conditions"},
            },
            "patternProperties": {"^_": {}}, "additionalProperties": False},
    },
}
json.dump(quests, open('quests.schema.json', 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=False)

# the manifest's map_info.unlock uses the shared condition now
m = json.load(open('manifest.schema.json', encoding='utf-8'))
m['definitions'].pop('condition', None)
u = m['definitions']['map_info']['properties']['unlock']
u['oneOf'] = [{"$ref": C + "condition"}, {"$ref": C + "conditions"}]
json.dump(m, open('manifest.schema.json', 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=False)
print('ok')
