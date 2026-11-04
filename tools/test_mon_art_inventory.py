"""Self-check for mon_art_inventory.py. Run: python tools/test_mon_art_inventory.py"""
from mon_art_inventory import scan

TEXT = """function scr_a(arg0)
{
    x = spr_h_goblin_body_loop_v1_alpha;
    // spr_h_ogre_body_loop in a comment does not count
    y = spr_goblin_walk;
}

function scr_b()
{
    z = spr_mon_icon_head + spr_title_top;
    s = "spr_hobgoblin_idle";
}
"""

r = scan(TEXT, "gml_GlobalScript_s_x.gml")
names = [(e["sprite"], e["func"], e["line"]) for e in r]
assert ("spr_h_goblin_body_loop_v1_alpha", "scr_a", 3) in names, names
assert ("spr_goblin_walk", "scr_a", 5) in names, names
assert ("spr_mon_icon_head", "scr_b", 10) in names, names
assert ("spr_hobgoblin_idle", "scr_b", 11) in names, names
assert not any(e["sprite"] == "spr_title_top" for e in r), names
assert not any(e["sprite"] == "spr_h_ogre_body_loop" for e in r), names
print("ok")
