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
print("ok")
