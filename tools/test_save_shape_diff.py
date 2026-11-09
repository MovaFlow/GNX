"""Self-check for save_shape_diff.py. Run: python tools/test_save_shape_diff.py"""
import copy

from save_shape_diff import compare


def save():
    return {
        "global_list": {"val": {"mon_num": [0, -1, -1, -1], "nest_num": [5, 0, 0, 0, 0], "br_unlock": [[]], "goblin": {"num": [3, -1, -1, -1]}, "day_timer": 10}},
        "mon_list": [{"x_pos": 1, "mon_data": {"mon_type": 0}}, {"x_pos": 2, "mon_data": {"mon_type": 1, "carry_wait": 0}}],
    }


a = save()
assert compare(a, copy.deepcopy(a)) == []

# positions and timers are not compared
b = copy.deepcopy(a)
b["mon_list"][0]["x_pos"] = 99
b["global_list"]["val"]["day_timer"] = 11
assert compare(a, b) == [], compare(a, b)

# a new key, however deep, is a difference, also in only one list item
b = copy.deepcopy(a)
b["global_list"]["val"]["gnx_types"] = []
assert any("gnx_types" in l for l in compare(a, b))
b = copy.deepcopy(a)
b["mon_list"][1]["mon_data"]["new"] = 1
assert any("mon_list[].mon_data" in l and "new" in l for l in compare(a, b))
b = copy.deepcopy(a)
del b["mon_list"][1]["mon_data"]["carry_wait"]
assert any("carry_wait" in l for l in compare(a, b))

# a longer type array is a difference, though it holds no new key
b = copy.deepcopy(a)
b["global_list"]["val"]["nest_num"].append(0)
assert any(l.startswith("length val.nest_num") for l in compare(a, b))

# per-type data must stay equal
b = copy.deepcopy(a)
b["global_list"]["val"]["goblin"]["num"][0] = 4
assert any(l.startswith("values val.goblin") for l in compare(a, b))

print("ok")
