#!/usr/bin/env python3
"""Self-check of tools/schemas/ and tools/check_mod.py.

    python tools/test_schemas.py

1. Every mod under GNX/example_mod, tools/scenarios/mods and harness_game/test_mods (the local
   community mods, when present) checks clean, apart from the deliberately broken entries in EXPECTED.
2. A misspelled key is caught in each file type (one typo per type, in a temporary copy).
3. Each schema has a property for every key its loader reads (variable_struct_exists in the GNX GML,
   when GNX/gml is present), apart from GML_ONLY (internal fields that are not written in mod files).
Exit 0 = all good.
"""
import copy
import glob
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_mod  # noqa: E402

# deliberately broken test-mod entries: (mod folder name, file name, path) -> they must be reported
EXPECTED = {
    ("harness_lang", "de.json", "LANG CELL"),
    ("harness_map_nocap", "manifest.json", "map_info.no_capture[3].stage"),
    ("harness_map_start", "manifest.json", "map_start.troops[3].type"),
    ("harness_props_bad", "props.json", "props[0].category"),
    ("harness_bad_spr", "cells.json", "[0].human_spr.phase_1.spr_array"),
    ("harness_spawn_bad", "cells.json", "[0].spawn_info"),
    ("harness_mav1505", "classes.json", "[2].milk_lvl"),
    ("harness_mav1505", "quests.json", "events.count_no_h.completion"),
    ("harness_mav1505", "quests.json", "events.hook_object.completion_hook"),
    ("harness_mav1505", "quests.json", "events.text_cond.completion"),
    ("harness_mav1505", "quests.json", "triggers[0].conditions[0]"),
    ("harness_mav1505", "quests.json", "triggers[0].conditions[1]"),
    ("moan_mod", "manifest.json", "(top)"),  # community mod: "display_name", which GNX never reads
}
# real problems found in community mods, reported and waiting for their authors: exact paths, so a new
# problem in the same files still fails the test
KNOWN = {
    ('Emira', 'quests.json', 'triggers[2]'),
    ('Jezebel', 'classes.json', '[0]'),
    ('cowgirls', 'classes.json', '[0]'),
    ('cowgirls', 'classes.json', '[0].naked_standard.phase_1.leg_any'),
    ('cowgirls', 'classes.json', '[0].naked_standard.phase_2.leg_any'),
    ('cowgirls', 'classes.json', '[0].naked_tent.phase_1.leg_any'),
    ('cowgirls', 'classes.json', '[0].naked_tent.phase_2.leg_any'),
    ('cowgirls', 'classes.json', '[0].naked_tent.phase_4.leg_any'),
    ('heroine_conquest', 'cells.json', '[0]'),
    ('heroine_conquest', 'cells.json', '[1]'),
    ('heroine_conquest', 'classes.json', '[0]'),
    ('heroine_conquest', 'classes.json', '[1]'),
    ('heroine_conquest', 'quests.json', 'events.azure_intro.dialog[0]'),
    ('heroine_conquest', 'quests.json', 'events.azure_intro.dialog[1]'),
    ('heroine_conquest', 'quests.json', 'events.azure_intro.dialog[2]'),
    ('heroine_conquest', 'quests.json', 'events.azure_quest'),
    ('heroine_conquest', 'quests.json', 'events.azure_win.dialog[0]'),
    ('heroine_conquest', 'quests.json', 'events.azure_win.dialog[1]'),
    ('heroine_conquest', 'quests.json', 'events.mel_intro.dialog[0]'),
    ('heroine_conquest', 'quests.json', 'events.mel_intro.dialog[1]'),
    ('heroine_conquest', 'quests.json', 'events.mel_intro.dialog[2]'),
    ('heroine_conquest', 'quests.json', 'events.mel_quest'),
    ('heroine_conquest', 'quests.json', 'events.mel_win.dialog[0]'),
    ('heroine_conquest', 'quests.json', 'events.mel_win.dialog[1]'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_hob_p0.loop.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_hob_p0.start.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_hob_p1.loop.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_hob_p1.start.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_hob_p2.loop.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_hob_p2.start.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_p0.loop.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_p0.start.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_p1.loop.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_p1.start.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_p2.loop.body'),
    ('py_more_cells_mod', 'cells.json', '[3].mon_spr_p2.start.body'),
    ('shiny_cleric', 'classes.json', '[0].carry_base_spr'),
    ('shiny_cleric', 'classes.json', '[0].naked_standard.phase_1.leg_1'),
    ('shiny_cleric', 'classes.json', '[0].naked_standard.phase_1.leg_2'),
    ('shiny_cleric', 'classes.json', '[0].naked_standard.phase_2.leg_1'),
    ('shiny_cleric', 'classes.json', '[0].naked_standard.phase_2.leg_2'),
    ('shiny_cleric', 'classes.json', '[0].naked_tent.phase_1.leg_1'),
    ('shiny_cleric', 'classes.json', '[0].naked_tent.phase_1.leg_2'),
    ('shiny_cleric', 'classes.json', '[0].naked_tent.phase_2.leg_1'),
    ('shiny_cleric', 'classes.json', '[0].naked_tent.phase_2.leg_2'),
    ('shiny_cleric', 'classes.json', '[0].naked_tent.phase_4.leg_1'),
    ('shiny_cleric', 'classes.json', '[0].naked_tent.phase_4.leg_2'),
    ('shiny_knight', 'classes.json', '[0].carry_base_spr'),
    ('shiny_knight', 'classes.json', '[0].naked_standard.phase_1.leg_1'),
    ('shiny_knight', 'classes.json', '[0].naked_standard.phase_1.leg_2'),
    ('shiny_knight', 'classes.json', '[0].naked_standard.phase_2.leg_1'),
    ('shiny_knight', 'classes.json', '[0].naked_standard.phase_2.leg_2'),
    ('shiny_knight', 'classes.json', '[0].naked_tent.phase_1.leg_1'),
    ('shiny_knight', 'classes.json', '[0].naked_tent.phase_1.leg_2'),
    ('shiny_knight', 'classes.json', '[0].naked_tent.phase_2.leg_1'),
    ('shiny_knight', 'classes.json', '[0].naked_tent.phase_2.leg_2'),
    ('shiny_knight', 'classes.json', '[0].naked_tent.phase_4.leg_1'),
    ('shiny_knight', 'classes.json', '[0].naked_tent.phase_4.leg_2'),
    ('shiny_peasant', 'classes.json', '[0].carry_base_spr'),
    ('shiny_peasant', 'classes.json', '[0].naked_standard.phase_1.leg_1'),
    ('shiny_peasant', 'classes.json', '[0].naked_standard.phase_1.leg_2'),
    ('shiny_peasant', 'classes.json', '[0].naked_standard.phase_2.leg_1'),
    ('shiny_peasant', 'classes.json', '[0].naked_standard.phase_2.leg_2'),
    ('shiny_peasant', 'classes.json', '[0].naked_tent.phase_1.leg_1'),
    ('shiny_peasant', 'classes.json', '[0].naked_tent.phase_1.leg_2'),
    ('shiny_peasant', 'classes.json', '[0].naked_tent.phase_2.leg_1'),
    ('shiny_peasant', 'classes.json', '[0].naked_tent.phase_2.leg_2'),
    ('shiny_peasant', 'classes.json', '[0].naked_tent.phase_4.leg_1'),
    ('shiny_peasant', 'classes.json', '[0].naked_tent.phase_4.leg_2'),
}

# one typo per file type: (file kind, json path to an object in a known-good file, key to misspell)
TYPOS = [
    ("manifest", "GNX/example_mod/manifest.json", [], "compatible_game_versions"),
    ("sounds", "tools/scenarios/mods/harness_music/sounds.json", ["music"], "tracks"),
    ("props", "tools/scenarios/mods/harness_props/props.json", ["props", 0], "position"),
    ("items", "tools/scenarios/mods/harness_items/items.json", ["loot", 0], "stage"),
    ("raids", "tools/scenarios/mods/harness_raid_a/raids.json", ["stages", 0], "raid_time"),
    ("quests", "tools/scenarios/mods/harness_quests/quests.json", ["events", "q_gold"], "completion_hook"),
    ("tools", "GNX/example_mod/tools.json", ["categories", 0], "label"),
    ("classes", "GNX/example_mod/classes.json", [0], "has_hair"),
    ("classes", "GNX/example_mod/classes.json", [0, "clothing_standard", "phase_1"], "leg_1"),
    ("cells", "GNX/example_mod/cells.json", [0], "category"),
    ("cells", "GNX/example_mod/cells.json", [0, "physical"], "max_mon_num"),
    ("cells", "GNX/example_mod/cells.json", [0, "mon_spr", "loop"], "body"),
]


def corpus():
    dirs = ["GNX/example_mod"] + glob.glob("tools/scenarios/mods/*") + glob.glob("harness_game/test_mods/*") + glob.glob("harness_game/test_mods/*/*")
    return [Path(d) for d in dirs if (ROOT / d / "manifest.json").exists()]


def test_corpus(js):
    got = []
    for mod in corpus():
        check_mod.check_mod(ROOT / mod, js, lambda p, where, msg, b: got.append((Path(p), where, msg)))
    seen = set()
    bad = []
    for p, where, msg in got:
        key = (p.parent.name if p.parent.name != "lang" else p.parent.parent.name, p.name, where)
        if key in EXPECTED:
            seen.add(key)
        elif key in KNOWN:
            pass
        else:
            bad.append(f"  unexpected: {p}: {where}: {msg}")
    have_community = (ROOT / "harness_game/test_mods").exists()
    missing = [k for k in EXPECTED - seen if have_community or k[0] != "moan_mod"]
    bad += [f"  not reported any more: {k}" for k in missing]
    print(f"corpus: {len(corpus())} mods, {len(got)} problem(s), {len(bad)} unexpected")
    return bad


def test_typos(js):
    bad = []
    for kind, rel, path, key in TYPOS:
        data = json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))
        obj = data
        for part in path:
            obj = obj[part]
        assert key in obj, (rel, path, key)
        obj[key[:-1] + key[-1] * 2] = obj.pop(key)  # "stage" -> "stagee"
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / Path(rel).name
            f.write_text(json.dumps(data), encoding="utf-8")
            got = []
            check_mod.check_file(f, kind, js, lambda p, where, msg, b: got.append(msg))
        if not any("unknown key" in m for m in got):
            bad.append(f"  typo not caught: {kind} {rel} {key}")
    print(f"typos: {len(TYPOS)} file types, {len(bad)} missed")
    return bad


# loader function -> (schema, json pointer of the object schema whose properties must cover the keys read
# from GML variable `var`)
SYNC = [
    ("s_gnx_mods", "_manifest", "manifest", []),
    ("s_gnx_mods", "_m", "manifest", []),
    ("s_gnx_travel", "_mb", "manifest", ["definitions", "map_info"]),
    ("s_gnx_travel", "_ms", "manifest", ["definitions", "map_start"]),
    ("s_gnx_items", "_it", "items", ["definitions", "item"]),
    ("s_gnx_items", "_l", "items", ["definitions", "loot"]),
    ("s_gnx_sound", "_data", "sounds", []),
    ("s_gnx_sound", "_bank_def", "sounds", ["properties", "voice_banks", "additionalProperties"]),
    ("s_gnx_sound", "_sd", "sounds", ["properties", "settings_defaults"]),
    ("s_gnx_sound", "_amb", "sounds", ["properties", "ambience"]),
    ("s_gnx_sound", "_mu", "sounds", ["properties", "music"]),
    ("s_gnx_quests", "_data", "quests", []),
    ("s_gnx_quests", "_edef", "quests", ["definitions", "event"]),
    ("s_gnx_quests", "_evt", "quests", ["definitions", "event"]),
    ("s_gnx_quests", "_tdef", "quests", ["definitions", "trigger"]),
    ("s_gnx_quests", "_pdef", "quests", ["properties", "portraits", "additionalProperties"]),
]
# (topic, var, schema, pointer, function): when the variable name is generic (arg0), only that function's code is read
SYNC += [
    ("s_gnx_tools", "_data", "tools", [], "scr_gnx_load_tools"),
    ("s_gnx_raid", "_json", "raids", [], "scr_gnx_load_raids"),
    ("s_gnx_raid", "_s", "raids", ["definitions", "stage"], "scr_gnx_load_raids"),
    ("s_gnx_tools", "_kb", "tools", ["definitions", "keybind"], "scr_gnx_load_tools"),
    ("s_gnx_tools", "arg0", "tools", ["definitions", "button"], "scr_gnx_parse_tool_button"),
    ("s_gnx_tools", "arg0", "tools", ["definitions", "category"], "scr_gnx_parse_tool_category"),
    ("s_gnx_content", "arg0", "classes", ["definitions", "class"], "gnx_resolve_class"),
    ("s_gnx_content", "_rs_e", "classes", ["definitions", "class", "properties", "raid_spawns", "items"], "gnx_resolve_class"),
    ("s_gnx_content", "_ce", "classes", ["definitions", "class", "properties", "post_raid", "properties", "cage_escape"], "gnx_resolve_class"),
    ("s_gnx_content", "_cbs_def", "classes", ["definitions", "class", "properties", "carry_base_spr", "else"], "gnx_resolve_class"),
    ("s_gnx_content", "arg0", "classes", ["definitions", "phase_std"], "gnx_resolve_class_phase"),
    ("s_gnx_content", "arg0", "classes", ["definitions", "phase_big"], "gnx_resolve_class_big_phase"),
    ("s_gnx_content", "arg0", "cells", ["definitions", "cell"], "scr_gnx_register_cell"),
    ("s_gnx_content", "_phys", "cells", ["definitions", "cell", "properties", "physical"], "scr_gnx_register_cell"),
    ("s_gnx_content", "arg1", "cells", ["definitions", "cell"], "scr_gnx_patch_cell"),
    ("s_gnx_content", "_phys", "cells", ["definitions", "cell", "properties", "physical"], "scr_gnx_patch_cell"),
    ("s_gnx_content", "_hspr", "cells", ["definitions", "cell", "properties", "human_spr"], "scr_gnx_register_cell"),
    ("s_gnx_content", "_s", "cells", ["definitions", "mon_start"], "gnx_resolve_mon_spr"),
    ("s_gnx_content", "_lo", "cells", ["definitions", "mon_phase"], "gnx_resolve_mon_spr"),
    ("s_gnx_content", "arg0", "cells", ["definitions", "cell", "properties", "mon_spr"], "gnx_resolve_mon_spr"),
]
GML_ONLY = {"mod_name"}  # filled in by the loader


def test_sync():
    gml = ROOT / "GNX/gml"
    if not gml.exists():
        print("sync: GNX/gml not present, skipped")
        return []
    bad = []
    for topic, var, kind, ptr, *fn in SYNC:
        src = "".join(open(f, encoding="utf-8").read() for f in glob.glob(str(gml / f"gml_GlobalScript_{topic}.gml")))
        if fn:
            src = re.search(r"function " + fn[0] + r"\(.*?\n}\n", src, re.S).group(0)
        keys = set(re.findall(r"variable_struct_exists\(" + re.escape(var) + r', "([A-Za-z_0-9]+)"\)', src))
        node = check_mod.schema_for(kind)
        for part in ptr:
            node = node[part]
        props = set(node.get("properties", {}))
        if "else" in node:
            props |= set(node["else"].get("properties", {}))
        pats = list(node.get("patternProperties", {}))
        for k in sorted(k for k in keys - props - GML_ONLY if not any(re.search(p, k) for p in pats)):
            bad.append(f"  {kind} {'/'.join(map(str, ptr)) or '(top)'}: the loader reads '{k}' ({topic} {var}), the schema does not list it")
    print(f"sync: {len(SYNC)} loader objects, {len(bad)} key(s) missing from the schemas")
    return bad


def main():
    os.chdir(ROOT)
    import jsonschema
    bad = test_corpus(jsonschema) + test_typos(jsonschema) + test_sync()
    for b in bad:
        print(b)
    print("test_schemas: " + ("OK" if not bad else f"{len(bad)} FAIL"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
