"""Self-check for mon_art_alias_draft.py. Run: python tools/test_mon_art_alias_draft.py"""
from mon_art_alias_draft import address_of, line_name

CASES = {
    "spr_h_goblin_body_loop_v1_alpha": "goblin.standard.loop.body.leg_1",
    "spr_h_goblin_body_loop_v2_alpha": "goblin.standard.loop.body.leg_2",
    "spr_h_goblin_body_loop_cow_alpha": "goblin.standard.loop.body.cow",
    "spr_h_goblin_pen_loop": "goblin.standard.loop.pen",
    "spr_h_goblin_body_ej_alpha": "goblin.standard.ej.body.any",
    "spr_h_goblin_touch_start_nyx": "goblin.standard.start.touch.nyx",
    "spr_h_goblin_touch_loop_anal": "goblin.standard.anal.loop.touch.any",
    "spr_h_hobgoblin_body_start_v3_alpha": "hobgoblin.standard.start.body.leg_0",
    "spr_h_goblin_gb_1_loop_alpha": "goblin.gbang_1.loop.body.any",
    "spr_h_goblin_gb_3_cow_loop_hand_alpha": "goblin.gbang_3.loop.hand.cow",
    "spr_h_goblin_head_alpha_giant": "goblin.giant.loop.head",
    "spr_h_goblin_body_start_alpha_giant": "goblin.giant.start.body.any",
    "spr_h_ogre_giant_loop_alpha": "ogre.giant.loop.body.any",
    "spr_h_goblin_dairy_loop_alpha": "goblin.dairy.loop.body.any",
    "spr_h_goblin_milk_loop_alpha": "goblin.milk.loop.body.any",
    "spr_h_goblin_drink_loop_touch_cat": "goblin.drink.loop.touch.cat",
    "spr_h_ogre_body_loop": "ogre.standard.loop.body.any",
    "spr_h_ogre_body_loop_lilith": "ogre.standard.loop.body.lilith",
    # hobgoblin shrine start art has no "_h_" in its name
    "spr_hobgoblin_shrine_start_body_alpha": "hobgoblin.shrine.start.body.any",
    "spr_hobgoblin_shrine_start_hand_alpha": "hobgoblin.shrine.start.hand.any",
    "spr_hobgoblin_shrine_start_pen": "hobgoblin.shrine.start.pen",
    # drawn as the pen (s_mon_data, case 39), not as an enter
    "spr_h_ogre_shrine_start_enter": "ogre.shrine.start.pen",
    "spr_h_ogre_shrine_loop_enter": "ogre.shrine.loop.enter.any",
    # "body" comes first in the name, but the GIANT cell draws these as the start pen (s_mon_data L589, L1628)
    "spr_h_goblin_body_start_pen_giant": "goblin.giant.start.pen",
    "spr_h_hobgoblin_body_start_pen_giant": "hobgoblin.giant.start.pen",
    "spr_h_goblin_body_start_alpha_giant": "goblin.giant.start.body.any",
    # the Morrigan ogre of the chain cell: the cell draws it itself (s_slot_draw), so it belongs to chains (Phase 2), not to standard
    "spr_h_ogre_body_loop_morrigan": "ogre.chains.loop.body.morrigan",
    "spr_h_ogre_body_loop_morrigan_extra": "ogre.chains.loop.body.morrigan",
    # the G.BANG goblin is touched with the ogre art (s_mon_data, goblin G.BANG 1 branch): only a goblin draws these
    "spr_h_ogre_touch_loop": "goblin.gbang_1.loop.touch.any",
    "spr_h_ogre_touch_loop_cow": "goblin.gbang_1.loop.touch.cow",
    "spr_h_ogre_touch_loop_nyx": "goblin.gbang_1.loop.touch.nyx",
    "spr_h_ogre_touch_loop_lilith": "goblin.gbang_1.loop.touch.lilith",
    "spr_h_ogre_touch_loop_morrigan": "goblin.gbang_1.loop.touch.morrigan",
    "spr_h_ogre_touch_loop_cat": "goblin.gbang_1.loop.touch.cat",
}
for name, want in CASES.items():
    assert address_of(name) == want, (name, address_of(name), want)

# Lines are not addresses: they follow their fill
assert address_of("spr_h_goblin_body_loop_v1_line") is None
assert line_name("spr_h_goblin_body_loop_v1_alpha") == "spr_h_goblin_body_loop_v1_line"
assert line_name("spr_h_goblin_head_alpha_giant") == "spr_h_goblin_head_line_giant"
assert line_name("spr_h_ogre_body_loop") is None
# Not monster scene art
assert address_of("spr_goblin_walk") is None
assert address_of("spr_hobgoblin_walk") is None and address_of("spr_hobgoblin_log") is None
print("ok")
