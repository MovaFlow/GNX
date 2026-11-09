"""Self-check for mon_art_alias_gen.py. Run: python tools/test_mon_art_alias_gen.py"""
from mon_art_alias_gen import ALIASES, OLD_KEYS, filter_aliases, gml_function
import json

DRAFT = {"addresses": {
    "goblin.standard.loop.body.any": ["spr_h_goblin_body_loop_v1_alpha", "spr_h_goblin_body_loop_v2_alpha", "spr_h_goblin_body_loop_v1_alpha"],
    "goblin.birth.loop.body.any": ["spr_h_goblin_v_birth"],
    "goblin.milk.loop.body.any": ["spr_h_goblin_milk_loop_alpha"],
    "goblin.dairy.loop.body.any": ["spr_h_goblin_dairy_pump", "spr_h_goblin_dairy_loop_alpha"],
}}
PICKED = {"spr_h_goblin_body_loop_v1_alpha", "spr_h_goblin_body_loop_v2_alpha", "spr_h_goblin_dairy_loop_alpha"}
out = filter_aliases(DRAFT, PICKED, {"spr_h_goblin_gb_1_loop_alpha"}, {"ogre.carry.walk": ["spr_ogre_walk_carry"]})
assert out["goblin.standard.loop.body.any"] == ["spr_h_goblin_body_loop_v1_alpha", "spr_h_goblin_body_loop_v2_alpha"], out
assert "goblin.birth.loop.body.any" not in out and "goblin.milk.loop.body.any" not in out, out
assert out["goblin.dairy.loop.body.any"] == ["spr_h_goblin_dairy_loop_alpha"], out
assert out["ogre.carry.walk"] == ["spr_ogre_walk_carry"], out
g = gml_function({"a.b": ["spr_x", "spr_y"]})
assert 'variable_struct_set(_t, "a.b", ["spr_x", "spr_y"]);' in g and g.startswith("// GENERATED") and "function gnx_art_aliases_build()" in g, g
g = gml_function({"a.b": ["spr_x"]}, {"spr_x": "x_key"})
assert 'case "spr_x": return "x_key";' in g and "function gnx_art_old_key(arg0)" in g, g
g = gml_function({"a.b": ["spr_x"]}, {"spr_x": "x_key"}, ("y_bg",))
assert "function gnx_art_old_key_known(arg0)" in g and 'case "x_key":' in g and 'case "y_bg":' in g, g
assert "tools/mon_art_alias_gen.py" in g.split("function gnx_art_old_key(arg0)")[0].splitlines()[-2], g
# every old key's sprite has an address (an old key with no address could never be logged)
table = json.loads(ALIASES.read_text(encoding="utf-8"))
named = {n for names in table.values() for n in names}
assert not set(OLD_KEYS) - named, sorted(set(OLD_KEYS) - named)
# the spec's tool check: every monster sprite the vanilla and old_keys dumps picked has an address, or a named reason not to
from mon_art_alias_draft import address_of, observed_uses
from mon_art_alias_gen import LATER_FAMILIES, OUT
from mon_art_diff import load

# props: no one monster owns them, and the guide points to sprite_replace (spec: Phase 1 tests). The dumps do not pick them as monster art,
# so this only keeps the list honest if a dump ever does
PROPS = {"spr_crate", "spr_fence", "spr_low_crate", "spr_small_step_1", "spr_small_step_2", "spr_small_step_3", "spr_bowl", "spr_plank"}


def why_not_addressed(name):
    """None when the sprite has an address; else the reason it has none"""
    if name in named:
        return None
    if name in PROPS:
        return "prop"
    if "_line" in name:  # lines follow their fill (gnx_art_line_name), so the fill must be addressed or excused
        return why_not_addressed(name.replace("_line", "_alpha", 1))
    fam = (address_of(name) or "..").split(".")[1]
    if fam in LATER_FAMILIES:  # birth, milk and the chain cells draw these themselves: hooked in Phase 2, with their cells
        return "Phase 2 family " + fam
    return False


dumps = [OUT / "vanilla.base.txt", OUT / "old_keys.base.txt"]
if all(p.is_file() for p in dumps):
    loose = {}
    for p in dumps:
        for n, uses in observed_uses(load(p)).items():
            if why_not_addressed(n) is False:
                loose[n] = sorted(uses)[:2]
    assert not loose, "monster sprites the dumps picked that have no address and no named reason: " + json.dumps(loose, indent=1)
else:
    print("no base dumps in harness_game/mon_art: sprite coverage check skipped")
print("ok")
