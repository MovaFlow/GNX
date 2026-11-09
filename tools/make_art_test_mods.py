"""Writes the test mods for the monster_art scenarios to tools/scenarios/mods, and the art_cell_bad scenario that goes with the
bad cells (their h_types and expected errors are built together). Run: python tools/make_art_test_mods.py"""
import copy
import json
import shutil
import struct
import zlib
from pathlib import Path

MODS = Path(__file__).resolve().parent / "scenarios" / "mods"


def png(path, w, h, frames, margin=0):
    """a strip of `frames` frames, each w x h and one red per frame; `margin` pixels all round each frame are transparent"""
    rows = []
    for y in range(h):
        row = bytearray([0])
        for f in range(frames):
            red = 10 * (f + 1) % 256
            if margin and (y < margin or y >= h - margin):
                row += bytes((red, 0, 0, 0)) * w
            elif margin:
                row += bytes((red, 0, 0, 0)) * margin + bytes((red, 0, 0, 255)) * (w - 2 * margin) + bytes((red, 0, 0, 0)) * margin
            else:
                row += bytes((red, 0, 0, 255)) * w
        rows.append(bytes(row))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w * frames, h, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))


def write(mod, **files):
    d = MODS / mod
    d.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (d / f"{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def manifest(mod, **keys):
    return {"mod_id": mod, "name": f"GNX Harness {mod}", "version": "1.0.0", "_about": "Test mod for the monster_art scenarios. Not for players.",
            "compatible_game_versions": ["1.40"], **keys}


# every strip is its own file, so a wrong pick can never pass for the right one: name -> frames
STRIPS = {n: 5 for n in (
    "lp_fill lp_line lp_l2 lp_cow hd_one hd_any hd_a hd_f hd_l lp_pen lp_enter ej_body an_body p1_body p1_pen gb_loop gb_line co_cow bc_loop bc_anal "
    "kn_0 kn_1 kn_2 kn_hand pa_loop pa_p1 og_fill og_line og_ej ph_start ph_loop ph_ej ph_idle ph_sl ph_le ph_eb ph_ee ph_pen "
    "c1_start c1_loop c1_touch c2_loop c2_anal").split()}
STRIPS.update(st_body=2, st_hand=2, st_touch=2, c1_start=2)  # a patch of a vanilla cell takes one row: start 2 frames
shutil.rmtree(MODS / "harness_art_cell" / "strips", ignore_errors=True)
for n, frames in STRIPS.items():
    png(MODS / "harness_art_cell" / "strips" / f"{n}.png", 8, 8, frames)


def names(node):
    """every gnx:NAME a monster_art tree uses"""
    if isinstance(node, str):
        return {node[4:]} if node.startswith("gnx:") else set()
    kids = node.values() if isinstance(node, dict) else node if isinstance(node, list) else []
    return set().union(*(names(k) for k in kids)) if kids else set()


def sprs(art):
    return {n: {"strip": f"strips/{n}.png", "frames": STRIPS[n]} for n in sorted(names(art))}


FULL = {
    "_note": "comment keys are ignored at every level",
    "start": {"body": "gnx:st_body", "hand": "gnx:st_hand", "touch": "gnx:st_touch", "hand_xscale": "random"},
    "loop": {"_note": "x", "body": {"_note": "x", "leg_1": {"_note": "x", "fill": "gnx:lp_fill", "line": "gnx:lp_line"}, "leg_2": "gnx:lp_l2", "cow": "gnx:lp_cow"},
             "hand": {"leg_1": "gnx:hd_one", "any": "gnx:hd_any", "leg_2": "none"}, "head": ["gnx:hd_a", {"fill": "gnx:hd_f", "line": "gnx:hd_l"}],
             "pen": "gnx:lp_pen", "enter": "gnx:lp_enter"},
    "ej": {"body": "gnx:ej_body", "touch": "none", "enter": "none"},
    "anal": {"loop": {"body": "gnx:an_body", "pen": "none"}},
    "placement": {"_note": "x", "1": {"_note": "x", "loop": {"body": "gnx:p1_body", "pen": "gnx:p1_pen"}}},
}
own = json.loads((MODS / "harness_own_art" / "cells.json").read_text(encoding="utf-8"))[0]
mod_cell = copy.deepcopy(own)
for k in ("mon_spr", "mon_spr_hob", "mon_spr_ogr"):
    mod_cell.pop(k, None)
mod_cell["physical"]["max_mon_num"] = 2


def cell(h, label, art, inter=None, **keys):
    c = copy.deepcopy(mod_cell)
    if inter:
        c["physical"]["intermissions"] = inter
        for k in inter:  # the captive's own table per intermission, so only the monsters' rule is in play
            c["human_spr"]["default"]["phase_" + k] = copy.deepcopy(c["human_spr"]["default"]["phase_2"])
    c.update(name="ART " + label, h_type=h, sprites=sprs(art), monster_art=art, **keys)
    return c


BASE_CLASS = {"human_spr": {"mode": "base+class", "base_body": "standard"}}
GOBLIN = {"goblin": {"loop": {"body": "gnx:gb_loop"}}}
cells = [
    cell(9070, "CELL", {"goblin": FULL}),
    cell(9071, "GOBLIN ONLY", GOBLIN),
    cell(9074, "BASE CLASS", {"goblin": {"loop": {"body": {"fill": "gnx:gb_loop", "line": "gnx:gb_line"}}}}, **BASE_CLASS),
    cell(9072, "COW ONLY", {"goblin": {"loop": {"body": {"cow": "gnx:co_cow"}}}}),
    cell(9075, "BASE CLASS ANAL", {"goblin": {"loop": {"body": "gnx:bc_loop"}, "anal": {"loop": {"body": "gnx:bc_anal"}}}}, **BASE_CLASS),
    cell(9076, "KNEEL", {"goblin": {"loop": {"body": {"leg_0": "gnx:kn_0", "leg_1": "gnx:kn_1", "leg_2": "gnx:kn_2"}, "hand": {"leg_1": "gnx:kn_hand"}}}}),
    cell(9079, "PLACEMENT ANAL", {"goblin": {"loop": {"body": "gnx:pa_loop"}, "placement": {"1": {"anal": {"loop": {"body": "gnx:pa_p1"}}}}}}),
    cell(9078, "OGRE", {"ogre": {"loop": {"body": {"fill": "gnx:og_fill", "line": "gnx:og_line"}}, "ej": {"body": "gnx:og_ej"}}}, mon_types=[0, 3]),
    # intermission blocks need the cell to declare the intermission (gnx_art_inter_hits), so 9110 declares three and 9113 (independent places) ej_end. ej_birth needs a cell with a birth scene (tentacle or underground), too heavy for a test cell: no cell here plays it
    cell(9110, "PHASES", {"goblin": {"start": {"body": "gnx:ph_start"}, "loop": {"body": "gnx:ph_loop"}, "ej": {"body": "gnx:ph_ej"}, "idle_start": {"body": "gnx:ph_idle"},
                                     "start_loop": {"body": "gnx:ph_sl"}, "loop_ej": {"body": "gnx:ph_le"}}},
         {"idle_start": {}, "start_loop": {}, "loop_ej": {}}),
    cell(9111, "PHASES FALL BACK", {"goblin": {"start": {"body": "gnx:ph_start"}, "loop": {"body": "gnx:ph_loop", "pen": "gnx:ph_pen"}, "ej": {"body": "gnx:ph_ej"}}}),
    cell(9112, "PHASES NO START", {"goblin": {"loop": {"body": "gnx:ph_loop"}, "ej": {"body": "gnx:ph_ej"}}}),
]
# independent places, which play ej_end after the ej; a copy of the places test cell (its own captive tables) with the strips of this mod
places_cell = json.loads((MODS / "harness_places" / "cells.json").read_text(encoding="utf-8"))[0]
ee_art = {"goblin": {"loop": {"body": "gnx:ph_loop"}, "ej_end": {"body": "gnx:ph_ee"}}}
for k in ("mon_spr", "mon_spr_hob", "mon_spr_ogr"):
    places_cell.pop(k, None)
places_cell["physical"].update(max_mon_num=2, mon_placements=[[0], [0]], intermissions={"ej_end": {"frames": 5}})
places_cell.update(name="ART PHASES EJ END", h_type=9113, mon_types=[0], monster_art=ee_art, sprites=sprs(ee_art))
cells.append(places_cell)
patch1 = {"start": {"body": "gnx:c1_start"}, "loop": {"body": "gnx:c1_loop", "touch": "gnx:c1_touch"}}
patch2 = {"loop": {"body": "gnx:c2_loop"}, "anal": {"loop": {"body": "gnx:c2_anal"}}}
for h, art in ((1, patch1), (2, patch2)):
    cells.append({"h_type": h, "sprites": sprs(art), "monster_art": {"goblin": art}})
write("harness_art_cell", cells=cells, manifest=manifest("harness_art_cell", cells="cells.json"))

# frame rules (art_cell_frames). Strip aN has N frames. Cells carry their own physical.frames; the monster is a goblin only, so a
# phase of another length than the vanilla one needs the art's strips, which is what the checker must see
places = json.loads((MODS / "harness_places" / "cells.json").read_text(encoding="utf-8"))[0]
VAN = {"start": 2, "idle": 2, "loop": 5, "ej": 5}
OWN6 = {"start": 3, "idle": 3, "loop": 6, "ej": 6}


def fsprs(art):
    return {n: {"strip": f"strips/{n}.png", "frames": int(n[1:])} for n in sorted(names(art))}


def fcell(h, label, art, frames, inter=None, base=None, types=(0,), placements=None):
    c = copy.deepcopy(base or own)
    for k in ("mon_spr", "mon_spr_hob", "mon_spr_ogr"):
        c.pop(k, None)
    c["physical"]["max_mon_num"] = 2
    if base is None:
        c["physical"]["frames"] = frames
    if inter:
        c["physical"]["intermissions"] = inter
        for k in inter:  # the captive's own table per intermission, so only the monsters' rule is in play
            if k != "ej_end" and base is None:
                c["human_spr"]["default"]["phase_" + k] = copy.deepcopy(c["human_spr"]["default"]["phase_2"])
    c.update(name="ART FRAMES " + label if label else "ART FRAMES", h_type=h, mon_types=list(types), monster_art=art, sprites=fsprs(art))
    if placements:
        c["physical"]["mon_placements"] = placements
    elif base is not None:
        c["physical"]["mon_placements"] = [[0], [0]]
    return c


def frame_mod(mod, cells):
    shutil.rmtree(MODS / mod / "strips", ignore_errors=True)
    for n in set().union(*(set(c["sprites"]) for c in cells)):
        png(MODS / mod / "strips" / f"{n}.png", 8, 8, int(n[1:]))
    write(mod, cells=cells, manifest=manifest(mod, cells="cells.json"))


def A(n):
    return {"body": f"gnx:{n}"}


frame_mod("harness_art_frames_ok", [
    fcell(9072, "", {"goblin": {"start": A("a2"), "loop": A("a5")}}, VAN),
    # no mon_spr: the art's strips are the only monster strips for the 3 and 6 frame phases; anal and placement blocks count
    fcell(9073, "OK OWN", {"goblin": {"start": A("a3"), "loop": A("a6"), "ej": A("a6"), "anal": {"loop": A("a6")},
                                      "placement": {"1": {"loop": A("a6"), "anal": {"start": A("a3")}}}}}, OWN6),
    # loop_ej comes from the placement blocks, one for each of the two places
    fcell(9074, "OK INTER", {"goblin": {"loop": A("a5"), "placement": {"0": {"loop_ej": A("a4")}, "1": {"loop_ej": A("a4")}}}}, VAN, {"loop_ej": {"frames": 4}}),
    fcell(9075, "OK EJ END", {"goblin": {"loop": A("a5"), "ej_end": A("a3"), "placement": {"1": {"ej_end": A("a3")}}}}, None, {"ej_end": {"frames": 3}}, places),
    # a goblin at place 0 and a hobgoblin at place 1, each with art in its own placement block only (3 / 6 frames, loop_ej of 4)
    fcell(9083, "OK PLACE SPECIES", {"goblin": {"placement": {"0": {"start": A("a3"), "loop": A("a6"), "ej": A("a6"), "loop_ej": A("a4")}}},
                                      "hobgoblin": {"placement": {"1": {"start": A("a3"), "loop": A("a6"), "ej": A("a6"), "loop_ej": A("a4")}}}},
          OWN6, {"loop_ej": {"frames": 4}}, types=(0, 1), placements=[[0], [1]]),
])
FR = "Cell 'ART FRAMES "
frame_mod("harness_art_frames_bad", [
    # vanilla cells: one row of the phase, in every pick of a list, a line, and every kind of block
    {"h_type": 1, "sprites": fsprs(A("a5")), "monster_art": {"goblin": {"start": A("a5"), "loop": A("a5")}}},
    {"h_type": 2, "sprites": fsprs({"x": ["gnx:a5", "gnx:a3"]}), "monster_art": {"goblin": {"loop": {"body": ["gnx:a5", "gnx:a3"]}}}},
    {"h_type": 3, "sprites": fsprs({"x": ["gnx:a5", "gnx:a3"]}), "monster_art": {"goblin": {"loop": {"body": {"fill": "gnx:a5", "line": "gnx:a3"}}}}},
    {"h_type": 6, "sprites": fsprs({"x": ["gnx:a5", "gnx:a3"]}), "monster_art": {"goblin": {"loop": A("a5"), "anal": {"loop": A("a3")}}}},
    {"h_type": 7, "sprites": fsprs({"x": ["gnx:a5", "gnx:a3"]}), "monster_art": {"goblin": {"loop": A("a5"), "placement": {"1": {"loop": A("a3")}}}}},
    {"h_type": 8, "sprites": fsprs({"x": ["gnx:a5", "gnx:a2"]}), "monster_art": {"goblin": {"loop": A("a5"), "placement": {"1": {"anal": {"start": A("a5")}}}}}},
    {"h_type": 9, "sprites": fsprs(A("a3")), "monster_art": {"goblin": {"ej": A("a3")}}},
    # a multiple of the phase's frames is only logged, the exact count is fine
    {"h_type": 13, "sprites": fsprs(A("a10")), "monster_art": {"goblin": {"loop": A("a10")}}},
    {"h_type": 14, "sprites": fsprs({"x": ["gnx:a2", "gnx:a5"]}), "monster_art": {"goblin": {"start": A("a2"), "loop": A("a5"), "ej": A("a5")}}},
    # a single frame is a still image and fits every phase
    {"h_type": 15, "sprites": fsprs(A("a1")), "monster_art": {"goblin": {"start": A("a1"), "loop": A("a1")}}},
    # mod cells: strips with fewer frames than one row, in each kind of block
    fcell(9076, "BAD ANAL", {"goblin": {"start": A("a3"), "loop": A("a6"), "ej": A("a6"), "anal": {"loop": A("a5")}}}, OWN6),
    fcell(9077, "BAD PLACEMENT", {"goblin": {"start": A("a3"), "loop": A("a6"), "ej": A("a6"),
                                              "placement": {"1": {"loop": A("a5"), "anal": {"ej": A("a5")}}}}}, OWN6),
    fcell(9078, "BAD LIST", {"goblin": {"start": A("a3"), "loop": {"body": ["gnx:a6", "gnx:a5"]}, "ej": A("a6")}}, OWN6),
    # the art covers loop and ej, not start: the start of 3 frames has no strips
    fcell(9079, "BAD NO START", {"goblin": {"loop": A("a6"), "ej": A("a6")}}, OWN6),
    # loop_ej for one of the two places only: the other plays its loop art (5 frames, the intermission has 6)
    fcell(9080, "BAD INTER", {"goblin": {"loop": A("a5"), "placement": {"0": {"loop_ej": A("a6")}}}}, VAN, {"loop_ej": {"frames": 6}}),
    fcell(9081, "BAD INTER STRIP", {"goblin": {"loop": A("a5"), "loop_ej": A("a5")}}, VAN, {"loop_ej": {"frames": 6}}),
    # ej_end plays ej_end, else ej, else loop, from the place's block (placement over monster), anal scenes from the anal blocks
    fcell(9082, "BAD EJ END", {"goblin": {"loop": A("a5"), "ej_end": A("a3"), "anal": {"ej_end": A("a2")}, "placement": {"1": {"ej_end": A("a2")}}}},
          None, {"ej_end": {"frames": 3}}, places),
    # ej_end 8 frames with only a head of its own: the body comes from the loop block, which has 5
    fcell(9084, "BAD EJ END PART", {"goblin": {"loop": A("a5"), "ej_end": {"head": "gnx:a8"}}}, None, {"ej_end": {"frames": 8}}, places),
    # the same for an intermission: loop_ej has a head only, the body comes from the loop block
    fcell(9085, "BAD INTER PART", {"goblin": {"loop": A("a5"), "loop_ej": {"head": "gnx:a6"}}}, VAN, {"loop_ej": {"frames": 6}}),
    # a block with a head only is no body: place 1 has no body for loop_ej in any block
    fcell(9086, "BAD INTER NO BODY", {"goblin": {"placement": {"0": {"loop": A("a5"), "loop_ej": A("a6")}, "1": {"loop_ej": {"head": "gnx:a6"}}}}}, VAN, {"loop_ej": {"frames": 6}}),
])

# a patch of a mod cell: the cell is registered by one mod and patched by a mod whose folder name sorts later (patches apply in load order,
# alphabetical by folder), so the patch always finds it. Each bad patch has a good twin
PA = "monster_art.goblin"
BASES = [  # (h_type, label, frames, intermissions, base cell, art of the cell itself, art of the patch, error of the patch or None)
    (9090, "PATCH STRIPS", OWN6, None, None, {"start": A("a3"), "loop": A("a6"), "ej": A("a6")}, {"start": A("a3"), "loop": A("a5"), "ej": A("a6")},
     "strip 'a5' (" + PA + ".loop) has 5 frames, it needs 6 per row"),
    (9091, "PATCH STRIPS OK", OWN6, None, None, {"start": A("a3"), "loop": A("a6"), "ej": A("a6")},
     {"start": A("a3"), "loop": A("a6"), "ej": A("a6"), "anal": {"loop": A("a6")}, "placement": {"1": {"loop": A("a6")}}}, None),
    (9092, "PATCH INTER", VAN, {"loop_ej": {"frames": 6}}, None, {"loop": A("a5"), "loop_ej": A("a6")}, {"loop": A("a5"), "loop_ej": A("a5")},
     "strip 'a5' (" + PA + ".loop_ej) has 5 frames, it needs 6 per row"),
    (9093, "PATCH INTER FALL BACK", VAN, {"loop_ej": {"frames": 6}}, None, {"loop": A("a5"), "loop_ej": A("a6")},
     {"loop": A("a5"), "placement": {"0": {"loop_ej": A("a6")}}},
     "strip 'a5' (" + PA + ".loop.body (played for loop_ej)) has 5 frames, it needs 6 per row"),
    (9094, "PATCH INTER OK", VAN, {"loop_ej": {"frames": 6}}, None, {"loop": A("a5"), "loop_ej": A("a6")},
     {"loop": A("a5"), "placement": {"0": {"loop_ej": A("a6")}, "1": {"loop_ej": A("a6")}}}, None),
    (9095, "PATCH EJ END", None, {"ej_end": {"frames": 3}}, places, {"loop": A("a5"), "ej_end": A("a3")}, {"loop": A("a5"), "ej_end": A("a2")},
     "strip 'a2' (" + PA + ".ej_end) has 2 frames, it needs 3 per row"),
    (9096, "PATCH EJ END OK", None, {"ej_end": {"frames": 3}}, places, {"loop": A("a5"), "ej_end": A("a3")}, {"loop": A("a5"), "ej_end": A("a3")}, None),
    (9097, "PATCH EJ END PART", None, {"ej_end": {"frames": 8}}, places, {"loop": A("a5"), "ej_end": A("a8")}, {"loop": A("a5"), "ej_end": {"head": "gnx:a8"}},
     "strip 'a5' (" + PA + ".loop.body (played for ej_end)) has 5 frames, it needs 8 per row"),
]
frame_mod("harness_art_frames_base", [fcell(h, lbl, {"goblin": own_art}, fr, inter, base) for h, lbl, fr, inter, base, own_art, _, _ in BASES])
frame_mod("harness_art_frames_patch", [{"h_type": h, "sprites": fsprs({"goblin": art}), "monster_art": {"goblin": art}} for h, _, _, _, _, _, art, _ in BASES])

# atlas-packed strips on vanilla cells: at3 has 3 frames, at5 has 5, both in the mod's atlas page and in no file
ATLAS = MODS / "harness_art_frames_atlas"
shutil.rmtree(ATLAS, ignore_errors=True)
png(ATLAS / "atlas" / "atlas_0.png", 8, 8, 8)
(ATLAS / "atlas" / "uv.json").write_text(json.dumps({"atlas_files": ["atlas_0.png"], "entries": {
    "at3": {"frames": [{"atlas": 0, "x": 8 * i, "y": 0, "w": 8, "h": 8} for i in range(3)]},
    "at5": {"frames": [{"atlas": 0, "x": 24 + 8 * i, "y": 0, "w": 8, "h": 8} for i in range(5)]}}}, indent=2), encoding="utf-8")
write("harness_art_frames_atlas", manifest=manifest("harness_art_frames_atlas", cells="cells.json"), cells=[
    {"h_type": h, "sprites": {n: {"strip": f"strips/{n}.png", "frames": int(n[2:])}}, "monster_art": {"goblin": {"loop": {"body": f"gnx:{n}"}}}}
    for h, n in ((5, "at3"), (10, "at5"))])

# species the game never calls into a vanilla cell (scr_mon_find_placement): cell -> species names, one patch each. Cells 1, 2, 3, 7, 8
# (art_cell_scene) only appear with the ogre, which none of the plain cells call
NEVER_CALLED = {4: ("hobgoblin", "ogre"), 17: ("goblin", "ogre"), 19: ("hobgoblin", "ogre"), 20: ("goblin", "hobgoblin"),
                **{h: ("ogre",) for h in (1, 2, 3, 6, 7, 8, 9, 13, 14, 15)}}
LIMIT_SPECIES_CELLS = [{"h_type": h, "monster_art": {m: {"loop": {"body": "spr_sp_drip_1"}}}} for h, ms in NEVER_CALLED.items() for m in ms]
# vanilla cells where a monster_art part is not drawn (gnx_art_limit): patches of cells 36, 21, 22 and 23, and cell 3 as the control
D = "spr_sp_drip_1"
PAIR = {"fill": D, "line": D}
write("harness_art_limits", cells=[
    {"h_type": 36, "monster_art": {"goblin": {"loop": {"body": D}}}},
    # ogres never stand in cell 36 (the game calls goblins and hobgoblins there), so they are refused too
    {"h_type": 36, "monster_art": {"ogre": {"loop": {"body": PAIR}}}},
    {"h_type": 21, "monster_art": {"ogre": {"loop": {"body": PAIR, "hand": D}}}},
    # a line on any pick of a list is not drawn, not only on the first
    {"h_type": 21, "monster_art": {"ogre": {"start": {"body": [{"fill": D}, PAIR]}}}},
    # the per-part limit also reads anal blocks, placement blocks and a placement's anal blocks
    {"h_type": 22, "monster_art": {"ogre": {"loop": {"body": PAIR}, "anal": {"loop": {"body": PAIR, "hand": D}},
                                            "placement": {"1": {"loop": {"body": PAIR, "head": D}, "anal": {"loop": {"body": PAIR, "pen": D}}}}}}},
    # cell 23 hides its first monster only: a set for the second is drawn, a block for the first is not
    {"h_type": 23, "monster_art": {"goblin": {"loop": {"body": D}}}},
    {"h_type": 23, "monster_art": {"hobgoblin": {"loop": {"body": D}, "placement": {"0": {"loop": {"body": D}}}}}},
    # an ogre stands at place 0 of cell 23, which draws only its body: a body is drawn, a hand or a line is not, place 1 never has an ogre
    {"h_type": 23, "monster_art": {"ogre": {"loop": {"body": D}, "placement": {"0": {"loop": {"body": D}}}}}},
    {"h_type": 23, "monster_art": {"ogre": {"loop": {"body": PAIR, "hand": D}}}},
    {"h_type": 23, "monster_art": {"ogre": {"loop": {"body": D}, "placement": {"1": {"loop": {"body": D}}}}}},
    {"h_type": 3, "monster_art": {"goblin": {"loop": {"body": "spr_h_goblin_body_loop_v1_alpha"}}}},
] + LIMIT_SPECIES_CELLS, manifest=manifest("harness_art_limits", cells="cells.json"))

L1 = "spr_sp_drip_1"
# label -> (monster_art, error text that must be logged, blocks the cell keeps). Error texts start with the cell's label.
BAD = {
    "unknown part": ({"goblin": {"loop": {"body": L1, "tail": L1}}}, "unknown part 'tail'", 0),
    "unknown monster": ({"dragon": {"loop": {"body": L1}}}, "unknown monster 'dragon'", 0),
    "start head": ({"goblin": {"start": {"body": L1, "head": L1}}}, "start has no head", 0),
    "no body": ({"goblin": {"loop": {"pen": L1}}}, "needs a body", 0),
    "mixed": ({"goblin": {"loop": {"body": {"fill": L1, "leg_1": L1}}}}, "mixes fill and variants", 0),
    "line only": ({"goblin": {"loop": {"body": {"line": L1}}}}, "pair needs fill", 0),
    "empty list": ({"goblin": {"loop": {"body": []}}}, "empty list", 0),
    "none in list": ({"goblin": {"loop": {"body": ["none", L1]}}}, "\"none\" inside a list", 0),
    "family in a cell": ({"goblin": {"standard": {"loop": {"body": L1}}}}, "unknown key 'standard'", 0),
    "world in a cell": ({"goblin": {"world": {"idle": "x.png"}}}, "unknown key 'world'", 0),
    "placement 3": ({"goblin": {"placement": {"3": {"loop": {"body": L1}}}}}, "placement must be 0, 1 or 2", 0),
    "pair on pen": ({"goblin": {"loop": {"body": L1, "pen": {"fill": L1}}}}, "pen takes no pair", 0),
    "ogre hand no line": ({"ogre": {"loop": {"body": L1, "hand": L1}}}, "monster_art.ogre.loop: an ogre's", 0),
    "ogre ej falls back to a lineless loop": ({"ogre": {"loop": {"body": L1}, "ej": {"hand": L1}}}, "monster_art.ogre.ej: an ogre's", 0),
    "ogre ej no body no loop": ({"ogre": {"ej": {"hand": L1}}}, "no loop body to fall back on", 0),
    "missing sprite": ({"goblin": {"loop": {"body": "gnx:nope"}}}, "gnx:nope", 0),
    # wrong JSON types
    "monster_art not object": (5, "monster_art must be an object", 0),
    "monster not object": ({"goblin": 5}, "monster_art.goblin: must be an object", 0),
    "phase not object": ({"goblin": {"loop": 5}}, "monster_art.goblin.loop: must be an object", 0),
    "placement not object": ({"goblin": {"loop": {"body": L1}, "placement": 5}}, "monster_art.goblin.placement: must be an object", 0),
    "placement block not object": ({"goblin": {"loop": {"body": L1}, "placement": {"1": 5}}}, "monster_art.goblin.placement.1: must be an object", 0),
    "anal not object": ({"goblin": {"loop": {"body": L1}, "anal": 5}}, "monster_art.goblin.anal: must be an object", 0),
    # the ogre line rule in every block
    "ogre anal no line": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}}, "anal": {"loop": {"body": L1, "pen": L1}}}}, "monster_art.ogre.anal.loop: an ogre's", 0),
    "ogre placement no line": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}}, "placement": {"1": {"loop": {"body": L1, "head": L1}}}}}, "monster_art.ogre.placement.1.loop: an ogre's", 0),
    "ogre placement anal no line": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}}, "placement": {"1": {"anal": {"loop": {"body": L1, "hand": L1}}}}}}, "monster_art.ogre.placement.1.anal.loop: an ogre's", 0),
    # other shapes
    "empty part": ({"goblin": {"loop": {"body": {}}}}, "monster_art.goblin.loop.body: empty part", 0),
    "comment only part": ({"goblin": {"loop": {"body": {"_note": "x"}}}}, "monster_art.goblin.loop.body: empty part", 0),
    "anal in anal": ({"goblin": {"loop": {"body": L1}, "anal": {"anal": {"loop": {"body": L1}}}}}, "monster_art.goblin.anal: anal is not allowed inside anal", 0),
    "list in list": ({"goblin": {"loop": {"body": [[L1, L1], L1]}}}, "monster_art.goblin.loop.body: a list inside a list", 0),
    "number sprite": ({"goblin": {"loop": {"body": 7}}}, "monster_art.goblin.loop.body: a sprite must be a name", 0),
    "hand_xscale number": ({"goblin": {"start": {"body": L1, "hand_xscale": 1}}}, "monster_art.goblin.start: hand_xscale is", 0),
    "hand_xscale wrong": ({"goblin": {"loop": {"body": L1, "hand_xscale": "left"}}}, "monster_art.goblin.loop: hand_xscale is", 0),
    "body none in a variant": ({"goblin": {"loop": {"body": {"leg_1": L1, "leg_2": "none"}}}}, "monster_art.goblin.loop.body: \"none\" is not allowed here", 0),
    "hand_xscale on ej": ({"goblin": {"loop": {"body": L1}, "ej": {"body": L1, "hand_xscale": "random"}}}, "monster_art.goblin.ej: hand_xscale is", 0),
    "pair line not a name": ({"goblin": {"loop": {"body": {"fill": L1, "line": 7}}}}, "monster_art.goblin.loop.body: a sprite must be a name, not 7", 0),
    "unknown variant": ({"goblin": {"loop": {"body": {"leg_7": L1}}}}, "unknown variant 'leg_7'", 0),
    # the cell does not take this monster (a fourth entry: more cell keys)
    "not in mon_types": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}}}}, "this monster is not in the cell's mon_types", 0, {"mon_types": [0]}),
    "in mon_types": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}}}}, None, 1, {"mon_types": [0, 3]}),
    # the check reads the list the cell will keep: a number in text counts, and an empty list means every species
    "string number in mon_types": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}}}}, None, 1, {"mon_types": ["3"]}),
    # the game calls only goblins and hobgoblins into a mod cell with neither mon_types nor mon_placements (an empty list is the same)
    "empty mon_types": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}}}}, "the game never calls this monster to this cell", 0, {"mon_types": []}),
    "no mon_types": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}}}}, "the game never calls this monster to this cell", 0, {"mon_types": None}),
    "goblin without mon_types": ({"goblin": {"loop": {"body": L1}}, "hobgoblin": {"loop": {"body": L1}}}, None, 2),
    "ogre in mon_placements": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}}}}, None, 1, {"physical_extra": {"mon_placements": [[3]]}}),
    "ogre not in mon_placements": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}}}}, "the game never calls this monster to this cell", 0, {"physical_extra": {"mon_placements": [[0, 1]]}}),
    # a good form that looks like a bad one
    "good ogre ej falls back to loop": ({"ogre": {"loop": {"body": {"fill": L1, "line": L1}, "hand": L1}, "ej": {"hand": L1}}}, None, 1),
    "good comment in placement": ({"goblin": {"loop": {"body": L1}, "placement": {"_note": "x", "1": {"loop": {"body": L1}}}}}, None, 1),
    # a bad monster does not take a good one down with it
    "good and bad monster": ({"goblin": {"loop": {"body": L1}}, "wyrm": {"loop": {"body": L1}}}, "unknown monster 'wyrm'", 1),
    # intermission and ej_end blocks need the cell to play them (gnx_art_inter_hits): this cell declares no intermissions, in any kind of block
    "undeclared idle_start": ({"goblin": {"loop": {"body": L1}, "idle_start": {"body": L1}}}, "monster_art.goblin.idle_start: not played on this cell", 0),
    "undeclared start_loop in anal": ({"goblin": {"loop": {"body": L1}, "anal": {"start_loop": {"body": L1}}}}, "monster_art.goblin.anal.start_loop: not played on this cell", 0),
    "undeclared loop_ej in placement": ({"goblin": {"loop": {"body": L1}, "placement": {"1": {"loop_ej": {"body": L1}}}}}, "monster_art.goblin.placement.1.loop_ej: not played on this cell", 0),
    "undeclared ej_birth in placement anal": ({"goblin": {"loop": {"body": L1}, "placement": {"1": {"anal": {"ej_birth": {"body": L1}}}}}}, "monster_art.goblin.placement.1.anal.ej_birth: not played on this cell (needs physical.intermissions.ej_birth", 0),
    # ej_end needs independent places and an ej_end table, not only an intermissions block
    "undeclared ej_end": ({"goblin": {"loop": {"body": L1}, "ej_end": {"body": L1}}}, "monster_art.goblin.ej_end: not played on this cell (needs physical.intermissions.ej_end and independent places)", 0),
    "ej_end without places": ({"goblin": {"loop": {"body": L1}, "ej_end": {"body": L1}}}, "monster_art.goblin.ej_end: not played on this cell (needs physical.intermissions.ej_end and independent places)", 0, {"physical_extra": {"intermissions": {"ej_end": {}}}}),
    # only the declared one plays: loop_ej is declared, idle_start is not
    "other intermission declared": ({"goblin": {"loop": {"body": L1}, "loop_ej": {"body": L1}, "idle_start": {"body": L1}}}, "monster_art.goblin.idle_start: not played on this cell", 0, {"physical_extra": {"intermissions": {"loop_ej": {}}}}),
    # ej_birth is declared but the cell has no birth scene, so the cell ignores it (its own error) and the art would never play
    "ej_birth without birth": ({"goblin": {"loop": {"body": L1}, "ej_birth": {"body": L1}}}, "monster_art.goblin.ej_birth: not played on this cell (needs physical.intermissions.ej_birth, which only a cell with a birth scene plays)", 0,
                               {"physical_extra": {"intermissions": {"ej_birth": {}}}}),
    # a declared intermission accepts its art in every kind of block
    "good declared intermissions": ({"goblin": {"loop": {"body": L1}, "idle_start": {"body": L1}, "loop_ej": {"body": L1}, "anal": {"start_loop": {"body": L1}},
                                                "placement": {"1": {"idle_start": {"body": L1}, "anal": {"loop_ej": {"body": L1}}}}}}, None, 1,
                                    {"physical_extra": {"intermissions": {"idle_start": {}, "start_loop": {}, "loop_ej": {}}}}),
}
cells = []
steps = [{"wait": 10}]
expect = []
for i, (label, (art, err, kept, *more)) in enumerate(BAD.items()):
    c = copy.deepcopy(own)
    for k in ("mon_spr", "mon_spr_hob", "mon_spr_ogr"):
        c.pop(k, None)
    extra = dict(more[0]) if more else {}
    if isinstance(art, dict) and "ogre" in art and "mon_types" not in extra and "physical_extra" not in extra:
        extra["mon_types"] = [0, 1, 3]  # the game calls ogres only into a cell that lists them
    if extra.get("mon_types", 0) is None:
        del extra["mon_types"]
    c["physical"] = {**c["physical"], **extra.pop("physical_extra", {})}
    for k in c["physical"].get("intermissions", {}):  # the captive's own table per intermission, so only the monsters' rule is in play
        if k != "ej_end":
            c["human_spr"]["default"]["phase_" + k] = copy.deepcopy(c["human_spr"]["default"]["phase_2"])
    c.update(name=("BAD " if err else "GOOD ") + label, h_type=9080 + i, monster_art=art, **extra)
    cells.append(c)
    if err:
        expect.append(f"'BAD {label}' monster_art.ogre: " + err if err.startswith("the game never calls") else f"'BAD {label}': " + err if err.startswith("monster_art must") else f"'BAD {label}' " + err if err.startswith("monster_art") else err)
    steps.append({"assert": "fn", "name": "gnx_scn_art_blocks", "args": [9080 + i], "is": kept,
                  "why": f"{label}: registered (-1 would mean not), keeps {kept} block(s)"})
# a vanilla cell never plays intermissions or ej_end, and a patch cannot add them; the whole block is refused (cell 3: 75-frame art, a whole multiple)
cells.append({"h_type": 3, "monster_art": {"goblin": {"loop": {"body": "spr_h_goblin_body_loop_v1_alpha"}, "idle_start": {"body": "spr_h_goblin_body_loop_v1_alpha"},
                                                      "ej_end": {"body": "spr_h_goblin_body_loop_v1_alpha"}}}})
expect += ["'BAD ej_end without places': intermissions.ej_end works only with scr_slot_h_gnx_places",  # the cell's own, older errors
           "'BAD ej_birth without birth': intermissions.ej_birth is ignored: the captive does not give birth",
           "Cell 3 monster_art.goblin.idle_start: not played on this cell (a vanilla cell has no intermissions)",
           "Cell 3 monster_art.goblin.ej_end: not played on this cell (a vanilla cell has no intermissions)"]
steps.append({"assert": "fn", "name": "gnx_scn_art_blocks", "args": [3], "is": 0, "why": "vanilla cell 3: the block with intermission art is refused"})
write("harness_art_bad", cells=cells, manifest=manifest("harness_art_bad", cells="cells.json"))
(MODS.parent / "art_cell_bad.json").write_text(json.dumps({
    "about": "monster_art: every wrong shape is a mod error naming the entry, and the entry is left out (a good monster in the same block is kept).",
    "mods": ["tools/scenarios/mods/harness_art_bad"], "check_boot_suite": False, "expect_dialog": "monster_art",
    "expect_mod_errors": expect, "steps": steps}, indent=2) + chr(10), encoding="utf-8")

GOB = "monster_art.goblin"
FRAMES_BAD = [  # (cell, blocks kept, error text; None = no error)
    (1, 0, "Cell 1 " + GOB + ".start.body: has 5 frames, one row here is 2"),
    (2, 0, "Cell 2 " + GOB + ".loop.body: has 3 frames, one row here is 5"),
    (3, 0, "Cell 3 " + GOB + ".loop.body line: has 3 frames, one row here is 5"),
    (6, 0, "Cell 6 " + GOB + ".anal.loop.body: has 3 frames, one row here is 5"),
    (7, 0, "Cell 7 " + GOB + ".placement.1.loop.body: has 3 frames, one row here is 5"),
    (8, 0, "Cell 8 " + GOB + ".placement.1.anal.start.body: has 5 frames, one row here is 2"),
    (9, 0, "Cell 9 " + GOB + ".ej.body: has 3 frames, one row here is 5"),
    (13, 1, None), (14, 1, None), (15, 1, None),
    (9076, 1, FR + "BAD ANAL': strip 'a5' (" + GOB + ".anal.loop) has 5 frames, it needs 6 per row"),
    (9077, 1, FR + "BAD PLACEMENT': strip 'a5' (" + GOB + ".placement.1.loop) has 5 frames, it needs 6 per row"),
    (9077, 1, FR + "BAD PLACEMENT': strip 'a5' (" + GOB + ".placement.1.anal.ej) has 5 frames, it needs 6 per row"),
    (9078, 1, FR + "BAD LIST': strip 'a5' (" + GOB + ".loop) has 5 frames, it needs 6 per row"),
    (9079, 1, FR + "BAD NO START': the start has 3 frames but goblins have no start strips"),
    (9080, 1, FR + "BAD INTER': strip 'a5' (" + GOB + ".loop.body (played for loop_ej)) has 5 frames, it needs 6 per row"),
    (9081, 1, FR + "BAD INTER STRIP': strip 'a5' (" + GOB + ".loop_ej) has 5 frames, it needs 6 per row"),
    (9082, 1, FR + "BAD EJ END': strip 'a2' (" + GOB + ".placement.1.ej_end) has 2 frames, it needs 3 per row"),
    (9082, 1, FR + "BAD EJ END': strip 'a2' (" + GOB + ".anal.ej_end) has 2 frames, it needs 3 per row"),
    (9084, 1, FR + "BAD EJ END PART': strip 'a5' (" + GOB + ".loop.body (played for ej_end)) has 5 frames, it needs 8 per row"),
    (9085, 1, FR + "BAD INTER PART': strip 'a5' (" + GOB + ".loop.body (played for loop_ej)) has 5 frames, it needs 6 per row"),
    (9086, 1, FR + "BAD INTER NO BODY': intermission loop_ej has 6 frames but " + GOB + " has no body for it at every place"),
    (5, 0, "Cell 5 " + GOB + ".loop.body: has 3 frames, one row here is 5"),
    (10, 1, None),
] + [(h, 1, FR + lbl + "': " + err) for h, lbl, _, _, _, _, _, err in BASES if err]
(MODS.parent / "art_cell_frames.json").write_text(json.dumps({
    "about": "Frame rules: an art-only mod cell with its own frames gives no false errors; art on a vanilla cell needs one row of the phase's frames, "
             "in every pick, line and block; a mod cell's art strips (every block) fit their phase, intermission and ej_end.",
    "mods": ["tools/scenarios/mods/harness_art_frames_atlas", "tools/scenarios/mods/harness_art_frames_bad", "tools/scenarios/mods/harness_art_frames_base",
             "tools/scenarios/mods/harness_art_frames_ok", "tools/scenarios/mods/harness_art_frames_patch"],
    "check_boot_suite": False, "expect_dialog": "monster_art",
    "expect_mod_errors": [e for _, _, e in FRAMES_BAD if e],
    "steps": [{"wait": 10}] + [{"assert": "fn", "name": "gnx_scn_art_blocks", "args": [h], "is": 1, "why": f"mod cell {h} loads"} for h in (9072, 9073, 9074, 9075)]
             + [{"assert": "fn", "name": "gnx_scn_art_blocks", "args": [9083], "is": 2, "why": "the per-place species cell keeps both blocks"},
                {"assert": "fn", "name": "gnx_scn_art_frames_legacy", "args": ["spr_sp_drip_1"], "is": 1, "why": "a legacy SprRef has a frame count too"}]
             + [{"assert": "fn", "name": "gnx_scn_art_blocks", "args": [h], "is": k, "why": f"cell {h} keeps {k} block(s)"} for h, k in dict((h, k) for h, k, _ in FRAMES_BAD).items()]},
    indent=2) + chr(10), encoding="utf-8")

# class and global swaps (art_class_swap, art_global_swap, art_class_over_global, art_special_shrine, art_swap_bad). Swap art is mostly other vanilla
# sprites with the same layout, so the asserts can name them. spr_h_goblin_body_loop_v1_alpha and _v2_ have 75 frames, goblin touch_loop_v1 and _v2 225
V1, V2 = "spr_h_goblin_body_loop_v1_alpha", "spr_h_goblin_body_loop_v2_alpha"
L2 = "spr_h_goblin_body_loop_v2_line"
SHRINE5 = "spr_h_goblin_shrine_enter"  # 5 frames, like the goblin shrine body, touch and enter
for mod, strip, frames in (("harness_art_class", "sk3_touch", 225), ("harness_art_global", "g_pen", 75), ("harness_art_global", "g_walk", 8)):
    png(MODS / mod / "strips" / f"{strip}.png", 8, 8, frames)
write("harness_art_class", classes=[
    {"name": "KNIGHT", "class_id": 2, "override": True, "_about": "only monster_art: the map must survive the override merge",
     "monster_art": {
         "goblin": {"standard": {
             "loop": {
                 "body": {"leg_1": {"fill": V2, "line": L2}},
                 "hand": {"leg_1": "none"},
                 "head": ["spr_h_goblin_head_loop_d2_alpha", "spr_h_goblin_head_loop_d1_alpha"],
                 "touch": {"leg_1": "spr_h_goblin_touch_loop_v2"},
                 "enter": {"any": "none"}},
             "anal": {"ej": {"body": {"any": V1}}}}},
         "hobgoblin": {"standard": {"loop": {"body": {"leg_0": "spr_h_hobgoblin_body_loop_v2_alpha"}}}},
         "ogre": {"standard": {"loop": {"body": {"leg_0": "spr_h_ogre_body_loop"}}}}}},
    {"name": "COW", "class_id": 9, "override": True,
     "monster_art": {"goblin": {"standard": {"loop": {"body": {"cow": V1}}}}}},
    {"name": "ART BAD", "override": False, "is_special": False, "has_hair": False,
     "monster_art": {"goblin": {"standard": {"loop": {"body": {"leg_7": V1}, "hand": {"cow": V1}, "tail": V1}}, "nowhere": {"loop": {"body": V1}}}}},
    {"name": "SKIN3", "override": False, "is_special": False, "has_hair": False, "_about": "swap art that is not in the skin-3 list must be flagged",
     "sprites": {"sk3_touch": {"strip": "strips/sk3_touch.png", "frames": 225}},
     "monster_art": {"goblin": {"standard": {"loop": {"touch": {"leg_2": "gnx:sk3_touch"}}}}}},
    {"name": "BOTH SWAPS", "override": False, "is_special": False, "has_hair": False, "_about": "mon_sprite_swap and monster_art for one sprite: monster_art wins, the log says so",
     "mon_sprite_swap": {V1: "spr_sp_drip_1"},
     "monster_art": {"goblin": {"standard": {"loop": {"body": {"leg_1": V2}}}}}},
    {"name": "OLD AND NEW", "override": False, "is_special": False, "has_hair": False,
     "_about": "mon_spr_overrides goblin_shrine_body_alpha and monster_art goblin.shrine.loop.body for one sprite: the old key wins; touch has no old key, so monster_art applies",
     "mon_spr_overrides": {"goblin_shrine_body_alpha": "spr_sp_drip_1", "goblin_wall_touch_loop": "spr_sp_drip_1", "shrine_sign": "spr_sp_drip_1"},
     "monster_art": {"goblin": {"shrine": {"loop": {"body": SHRINE5, "touch": SHRINE5}}}}},
], manifest=manifest("harness_art_class", classes="classes.json"))
# a resized world walk in the mods of art_dates, art_mod_off and art_travel: the game sprite must go back when the mod is off today, turned
# off, or not on the map. The global mod's is 64 x 80, 10 frames; the travel map mod's another size so each side is seen by its own geometry
WALK_G = {"goblin": {"world": {"walk": {"strip": "world/walk.png", "frames": 10, "xorig": 32, "yorig": 72}}}}
WALK_T = {"goblin": {"world": {"walk": {"strip": "world/walk.png", "frames": 6, "xorig": 24, "yorig": 56}}}}
# the map mod also resizes a walk the boot mod leaves alone: after the trip back nothing replaces it, so only a restore can bring it back
HOB_T = {"world": {"walk": {"strip": "world/hob.png", "frames": 4, "xorig": 20, "yorig": 56}}}
png(MODS / "harness_art_global" / "world" / "walk.png", 64, 80, 10)
png(MODS / "harness_art_dates" / "world" / "walk.png", 64, 80, 10)
png(MODS / "harness_art_travel" / "world" / "walk.png", 48, 60, 6)
png(MODS / "harness_art_travel" / "world" / "hob.png", 40, 60, 4)
write("harness_art_global", manifest=manifest("harness_art_global", monster_art={
    "sprites": {"g_pen": {"strip": "strips/g_pen.png", "frames": 75}, "g_walk": {"strip": "strips/g_walk.png", "frames": 8}},
    "goblin": {"standard": {"loop": {"body": {"any": {"fill": "spr_h_goblin_body_ej_alpha", "line": "spr_h_goblin_body_ej_line"}}, "pen": "gnx:g_pen"}},
               "shrine": {"loop": {"touch": SHRINE5}}, **WALK_G["goblin"]},
    "hobgoblin": {"shrine": {"start": {"body": "spr_h_goblin_shrine_start_body_alpha"}}},
    "ogre": {"carry": {"walk": "gnx:g_walk"}, "shrine": {"start": {"pen": "spr_h_goblin_shrine_start_pen"}}},
}))
write("harness_art_special", classes=[
    {"name": "SPECIAL OLD KEY", "override": False, "is_special": True, "has_hair": False, "mon_spr_overrides": {"goblin_shrine_touch": "spr_sp_drip_1"}},
    {"name": "SPECIAL PLAIN", "override": False, "is_special": True, "has_hair": False},
], manifest=manifest("harness_art_special", classes="classes.json"))
write("harness_art_swap_bad", classes=[
    {"name": "BAD SPECIAL", "override": False, "is_special": True, "has_hair": False, "_about": "touch and enter of the shrine loop never show for a special class",
     "monster_art": {"goblin": {"shrine": {"loop": {"body": SHRINE5, "touch": SHRINE5, "enter": SHRINE5}}}, "ogre": {"shrine": {"loop": {"enter": SHRINE5}}}}},
    {"name": "BAD SHAPE", "override": False, "is_special": False, "has_hair": False, "monster_art": {"goblin": 5, "ogre": {"carry": {"walk": 5}}}},
    {"name": "BAD FRAMES", "override": False, "is_special": False, "has_hair": False,
     "monster_art": {"goblin": {"standard": {"loop": {
         "body": {"leg_1": "spr_sp_drip_1", "leg_2": {"fill": V2, "line": "spr_sp_drip_1"}},
         "head": ["spr_h_goblin_head_loop_d2_alpha", "spr_sp_drip_1"]}}}}},
    {"name": "BAD LINE", "override": False, "is_special": False, "has_hair": False, "_about": "a line on an address with no line sprite would never draw",
     "monster_art": {"ogre": {"standard": {"loop": {"body": {"leg_0": {"fill": "spr_h_ogre_body_loop_v3", "line": "spr_h_ogre_body_loop_v3"}}}}}}},
    {"name": "DRINK PAIR", "override": False, "is_special": False, "has_hair": False,
     "_about": "a pair on an address that mixes a name with no line sprite (drink_base) and one with a line (drink_loop_alpha): no line error, only drink_base's frame count (6 against 2)",
     "monster_art": {"goblin": {"drink": {"loop": {"body": {"any": {"fill": "spr_h_goblin_drink_loop_alpha", "line": "spr_h_goblin_drink_loop_line"}}}}}}},
    {"name": "OGRE TOUCH", "override": False, "is_special": False, "has_hair": False, "_about": "the ogre touch art is drawn only on the G.BANG goblin: the address names the goblin, not the ogre",
     "monster_art": {"ogre": {"standard": {"loop": {"touch": {"any": "spr_h_ogre_touch_loop"}}}}}},
    {"name": "GBANG TOUCH", "override": False, "is_special": False, "has_hair": False,
     "monster_art": {"goblin": {"gbang_1": {"loop": {"touch": {"any": "spr_h_ogre_touch_loop"}}}}}},
    {"name": "BAD WALK LIST", "override": False, "is_special": False, "has_hair": False, "_about": "the carrying ogre's walk is read with no monster roll",
     "monster_art": {"ogre": {"carry": {"walk": ["spr_ogre_walk_carry", "spr_ogre_walk_carry"]}}}},
    {"name": "BAD PARTS", "override": False, "is_special": False, "has_hair": False,
     "monster_art": {"birth": {}, "goblin": {"standard": {"loop": {"prop": "none", "hand_xscale": "random", "body": {"leg_0": V1}, "pen": ["none", V1]}}},
                    "ogre": {"chains": {"loop": {"body": {"morrigan": V1}}}, "standard": {"loop": {"body": {"morrigan": V1}}}}}},
], manifest=manifest("harness_art_swap_bad", classes="classes.json"))

# lists in a class's swap map at the draw sites that pick their own sprite (GIANT head, DRINK cow, second G.BANG goblin): game sprites of
# the same layout, so the draw spy names the entry. The class is the Cow, because the drink and G.BANG sprites are class-shaped
write("harness_art_lists", classes=[
    {"name": "COW", "class_id": 9, "override": True,
     "monster_art": {"goblin": {
         "giant": {"loop": {"head": ["spr_h_hobgoblin_head_alpha_giant", "spr_h_goblin_head_alpha_giant"]}},
         "drink": {"loop": {"body": {"cow": ["spr_h_goblin_drink_nyx", "spr_h_goblin_drink_lilith"]}}},
         "gbang_1": {"loop": {"body": {"cow": ["spr_h_goblin_gb_1_lilith_loop_alpha", "spr_h_goblin_gb_1_v3_loop_alpha"]}}}}}},
], manifest=manifest("harness_art_lists", classes="classes.json"))
# a global swap that blanks the carrying ogre's walk: after a reload the ogre must still use the game's walk as its sprite_index
write("harness_art_carry_none", manifest=manifest("harness_art_carry_none", monster_art={"ogre": {"carry": {"walk": "none"}}}))
write("harness_art_a_base", classes=[
    {"name": "KNIGHT", "class_id": 2, "override": True, "_about": "loads before harness_art_class: its mon_sprite_swap is the base map that the Knight of harness_art_class replaces",
     "mon_sprite_swap": {V1: "spr_sp_drip_1"}},
], manifest=manifest("harness_art_a_base", classes="classes.json"))

# world art: another size, frame count and origin on walking monsters (art_world), a later sprite_replace of the same sprite at the game's
# size (art_world_order), every value form and every bad one (art_world_forms), and atlas art through the shared loader (art_replace_atlas)
png(MODS / "harness_art_world" / "world" / "walk.png", 64, 80, 10)
png(MODS / "harness_art_world" / "world" / "ogre.png", 128, 128, 8, margin=40)  # transparent margins: a precise mask would shrink the box
png(MODS / "harness_art_world" / "world" / "log2.png", 136, 11, 2)  # the log keeps its 1 frame
png(MODS / "harness_art_world" / "world" / "idle_same.png", 29, 45, 8)
write("harness_art_world", manifest=manifest("harness_art_world", monster_art={
    "goblin": {"world": {
        "walk": {"strip": "world/walk.png", "frames": 10, "xorig": 32, "yorig": 72},
        "walk_back": {"strip": "world/nope.png", "frames": 10, "xorig": 1, "yorig": 1},
    }},
    "hobgoblin": {"world": {"carry": {"strip": "world/walk.png", "frames": 10, "xorig": 32, "yorig": 72},
                            "log": {"strip": "world/log2.png", "frames": 2, "xorig": 63, "yorig": 11}}},
    "ogre": {"world": {"walk": {"strip": "world/ogre.png", "frames": 8, "xorig": 64, "yorig": 120}, "idle": {"strip": "world/walk.png", "frames": 10},
                       "walk_carry": {"strip": "world/ogre.png", "frames": 8, "xorig": 64, "yorig": 120}}},
}))
png(MODS / "harness_art_world_late" / "art" / "walk_same.png", 29, 45, 8)
write("harness_art_world_late", manifest=manifest("harness_art_world_late", sprite_replace={"spr_goblin_walk": "art/walk_same.png"}))
png(MODS / "harness_art_world_ten" / "world" / "walk.png", 64, 80, 10)
write("harness_art_world_ten", manifest=manifest("harness_art_world_ten", map="harness_art_ten", map_button={"label": "Art Ten", "return_label": "Village", "nest": [250, 100]}, monster_art={"goblin": {"world": {"walk": {"strip": "world/walk.png", "frames": 10, "xorig": 32, "yorig": 72}}}}))

# every form of a world value, and the bad ones. Its swaps (goblin body, the carrying ogre's walk) load beside the world entries
png(MODS / "harness_art_world_forms" / "world" / "walk_same.png", 29, 45, 8)
png(MODS / "harness_art_world_forms" / "world" / "big.png", 40, 60, 8)
for _f in (0, 1):
    png(MODS / "harness_art_world_forms" / "world" / "frames" / f"{_f}.png", 29, 45, 1)
write("harness_art_world_forms", classes=[
    {"name": "WORLD CLASS", "override": False, "is_special": False, "has_hair": False, "_about": "world belongs to the global file only",
     "monster_art": {"goblin": {"world": {"walk": "world/walk_same.png"}}}},
], manifest=manifest("harness_art_world_forms", classes="classes.json", monster_art={
    "sprites": {"unused": {"strip": "world/big.png", "frames": 8}},
    "goblin": {
        "standard": {"loop": {"body": {"any": "spr_h_goblin_body_ej_alpha"}}},
        "world": {
            "_note": "comment keys are ignored",
            "//note": 5,
            "walk": "world/walk_same.png",
            "idle": "gnx:unused",
            "walk_back": "spr_goblin_walk",
            "milk_walk_empty": 5,
            "milk_walk_full": ["world/walk_same.png", "world/walk_same.png"],
            "bogus": "world/walk_same.png",
        }},
    "hobgoblin": {"world": "world/walk_same.png"},
    "ogre": {
        "carry": {"walk": "spr_ogre_walk"},
        "world": {
            "walk": {"strip": "world/big.png", "frames": 8, "xorig": 20},
            "idle": {"strip": "world/big.png", "frames": 8, "xorig": 20, "yorig": 55},
            "walk_carry": {"strip": "world/big.png", "frames": 8, "xorig": 20, "yorig": 55},
        }},
}))
# the frames folder form (numbered PNGs) and a folder name
png(MODS / "harness_art_world_folder" / "art" / "walk_same.png", 29, 45, 8)
write("harness_art_world_folder", manifest=manifest("harness_art_world_folder", sprite_replace={"spr_goblin_walk": "art/walk_same.png"}, monster_art={
    "goblin": {"world": {"walk": "world/frames"}}}))
shutil.rmtree(MODS / "harness_art_world_folder" / "world", ignore_errors=True)
shutil.copytree(MODS / "harness_art_world_forms" / "world" / "frames", MODS / "harness_art_world_folder" / "world" / "frames")

# wrong types inside a sprite entry object are mod errors (the resolver would stop the game), and a strip with no frames takes the
# game sprite's count. Loaded after harness_art_world_forms, the errors leave that mod's art as it was
png(MODS / "harness_art_world_objs" / "world" / "hidle.png", 39, 69, 4)
png(MODS / "harness_art_world_objs" / "world" / "any.png", 40, 60, 8)
write("harness_art_world_objs", manifest=manifest("harness_art_world_objs", monster_art={
    "hobgoblin": {"world": {
        "idle": {"strip": "world/hidle.png", "xorig": 19, "yorig": 69},
        "walk_back": {"strip": 5, "xorig": 1, "yorig": 1},
        "walk": {"path": 5, "xorig": 1, "yorig": 1},
        "carry": {"strip": "world/any.png", "frames": 0, "xorig": 1, "yorig": 1},
        "log": {"strip": "world/any.png", "frames": "1", "xorig": 1, "yorig": 1},
    }},
    "ogre": {"world": {
        "walk": {"strip": "world/any.png", "frames": 2.5, "xorig": 1, "yorig": 1},
        "idle": {"folder": 7, "xorig": 1, "yorig": 1},
    }},
    # a list of file names holds strings only, and at least one (the resolver adds each to the folder name)
    "goblin": {"world": {
        "idle": {"frames": [1, 2], "xorig": 1, "yorig": 1},
        "walk_back": {"frames": [], "xorig": 1, "yorig": 1},
    }},
}))

# an earlier ogre.carry.walk that is a list (art_global_swap's list form), then world.walk_carry of the same mod overwrites it: the
# overwrite is compared with the list without an error, and warned. The art has its own size (30 x 50) to tell it from the forms mod's
png(MODS / "harness_art_world_list" / "world" / "carry.png", 30, 50, 8)
write("harness_art_world_list", manifest=manifest("harness_art_world_list", monster_art={
    "ogre": {"carry": {"walk": ["spr_ogre_walk", "spr_ogre_walk"]},
             "world": {"walk_carry": {"strip": "world/carry.png", "frames": 8, "xorig": 15, "yorig": 45}}},
}))

# sprite_replace: a same-size replacement keeps the game sprite's own collision box (a manual one inside the image), and half an
# origin still means 0 on the other axis
R = MODS / "harness_replace"
png(R / "art" / "box_same.png", 45, 90, 5)
png(R / "art" / "idle_half.png", 31, 44, 5)
_rj = json.loads((R / "sprite_replace.json").read_text(encoding="utf-8"))
_rj["spr_h_tent_nyx_bind_1_birth"] = "art/box_same.png"
_rj["spr_goblin_idle"] = {"strip": "art/idle_half.png", "frames": 5, "xorig": 3}
(R / "sprite_replace.json").write_text(json.dumps(_rj, indent=2), encoding="utf-8")

# atlas art: sprite_replace at another size than the entry is a size error that names the entry's size (4 x 8), and world takes the entry
atlas_mod = MODS / "harness_art_replace_atlas"
shutil.rmtree(atlas_mod, ignore_errors=True)
shutil.copytree(MODS / "harness_atlas", atlas_mod)
write("harness_art_replace_atlas", manifest=manifest("harness_art_replace_atlas", classes="classes.json",
      sprite_replace={"spr_title_top": {"strip": "strips/spr_atlas_case.png", "frames": 1}},
      monster_art={"goblin": {"world": {"walk": {"strip": "strips/spr_atlas_case.png", "frames": 1, "xorig": 2, "yorig": 7},
                                         "idle": {"strip": "strips/spr_atlas_case.png", "frames": 1, "xorig": 0, "yorig": 0}}}}))
# M4: an atlas entry the size of a game sprite whose origin is 0,0, with a non-zero xo/yo in uv.json and no origin in the JSON entry
# keeps the game sprite's origin (0,0). ZERO_SPR is a sprite of the shipped game with origin 0,0 (read at runtime)
ZERO_SPR, ZW, ZH = "spr_infinity", 7, 3
_uv_path = atlas_mod / "atlas" / "uv.json"
_uv = json.loads(_uv_path.read_text(encoding="utf-8"))
_uv["entries"]["spr_atlas_zero"] = {"frames": [{"atlas": 0, "x": 0, "y": 16, "w": ZW, "h": ZH}], "xo": 2, "yo": 3}
_uv_path.write_text(json.dumps(_uv, indent=2), encoding="utf-8")
_man = json.loads((atlas_mod / "manifest.json").read_text(encoding="utf-8"))
_man["sprite_replace"][ZERO_SPR] = {"strip": "strips/spr_atlas_zero.png", "frames": 1}
(atlas_mod / "manifest.json").write_text(json.dumps(_man, indent=2), encoding="utf-8")

# the same atlas art on a map: each load (boot, every trip) runs the loader again, and an atlas entry given another origin than its own
# must not be baked again each time (gnx_runtime_sprites would grow with every trip)
trip_mod = MODS / "harness_art_atlas_trip"
shutil.rmtree(trip_mod, ignore_errors=True)
shutil.copytree(MODS / "harness_atlas", trip_mod)
write("harness_art_atlas_trip", manifest=manifest("harness_art_atlas_trip", classes="classes.json",
      map=["vanilla", "harness_art_atrip"], map_button={"label": "Atlas Trip", "return_label": "Village", "nest": [250, 100]},
      monster_art={"goblin": {"world": {"walk": {"strip": "strips/spr_atlas_case.png", "frames": 1, "xorig": 2, "yorig": 7}}}}))

# art_dates: active_dates gates the manifest's (global) monster_art only. The same mod's class art and cell art stay on out of season, which
# is also what shows that the mod loaded when the global art is off. The scenario moves "today" with gnx_scn_set_today + reload_mods
DATES_ART = {"goblin": {"standard": {"loop": {"body": {"any": {"fill": "spr_h_goblin_body_ej_alpha", "line": "spr_h_goblin_body_ej_line"}}}}, **WALK_G["goblin"]}}
CLASS_ART = {"goblin": {"standard": {"loop": {"body": {"leg_1": {"fill": "spr_h_goblin_body_loop_v2_alpha", "line": "spr_h_goblin_body_loop_v2_line"}}}}}}
shutil.rmtree(MODS / "harness_art_dates" / "strips", ignore_errors=True)
png(MODS / "harness_art_dates" / "strips" / "gb_loop.png", 8, 8, STRIPS["gb_loop"])
write("harness_art_dates", cells=[cell(9073, "DATES", GOBLIN)],
      classes=[{"name": "DATES", "override": False, "is_special": False, "has_hair": False, "monster_art": CLASS_ART}],
      manifest=manifest("harness_art_dates", cells="cells.json", classes="classes.json", active_dates=["01-01", "01-02"], monster_art=DATES_ART))

# art_old_and_new: one cell with both keys (monster_art beats the old mon_spr for what the art lists; the old key still gives what it does not),
# and old mon_spr patches of a vanilla cell loaded before and after a mod's monster_art patch of it (art_cell's cells 1 and 2). Mods load by folder name: a_old < cell < old_late: the art wins
# either way, whatever the load order
OLD_LOOP = {"body": {"leg_any": {"alpha": "spr_sp_drip_1", "line": "spr_sp_drip_1"}}}
shutil.rmtree(MODS / "harness_art_old_new" / "strips", ignore_errors=True)
png(MODS / "harness_art_old_new" / "strips" / "gb_loop.png", 8, 8, STRIPS["gb_loop"])
# the old tables only draw for a mod class (14 or more) or a mod cell, so the PLAIN class is what makes the old patches of cells 1 and 2 live
write("harness_art_old_new", cells=[cell(9073, "OLD AND NEW", GOBLIN, mon_types=[0, 1], mon_spr={"loop": OLD_LOOP, "start": OLD_LOOP})],
      classes=[{"name": "PLAIN", "override": False, "is_special": False, "has_hair": False}],
      manifest=manifest("harness_art_old_new", cells="cells.json", classes="classes.json"))
write("harness_art_a_old", cells=[{"h_type": 2, "mon_spr": {"loop": OLD_LOOP, "start": OLD_LOOP}}], manifest=manifest("harness_art_a_old", cells="cells.json"))
write("harness_art_old_late", cells=[{"h_type": 1, "mon_spr": {"loop": OLD_LOOP}}], manifest=manifest("harness_art_old_late", cells="cells.json"))

# art_world_carry: the carrying ogre's walk is one entry of the global swap store, written by world.walk_carry (harness_art_world, 128 x 128)
# and by an ogre.carry.walk swap. A later mod's swap overwrites the world entry (last loaded wins); a class's own swap beats both
png(MODS / "harness_art_world_carry" / "strips" / "cw.png", 36, 52, 8)
write("harness_art_world_carry", manifest=manifest("harness_art_world_carry", monster_art={
    "sprites": {"cw": {"strip": "strips/cw.png", "frames": 8}}, "ogre": {"carry": {"walk": "gnx:cw"}}}))
png(MODS / "harness_art_world_class" / "strips" / "cc.png", 24, 40, 8)
write("harness_art_world_class", classes=[
    {"name": "CARRY", "override": False, "is_special": False, "has_hair": False, "sprites": {"cc": {"strip": "strips/cc.png", "frames": 8}},
     "monster_art": {"ogre": {"carry": {"walk": "gnx:cc"}}}}], manifest=manifest("harness_art_world_class", classes="classes.json"))

# art_travel: a map mod's global art is on that map only, and the boot mods' art (map "vanilla", the default) is off there. The map mod swaps
# the same sprite harness_art_global does (body of leg 1), to another sprite, so each side is seen by its own name. It also swaps the leg 1 hand,
# which the boot mod leaves alone: a map mod's art left in the store after the trip back would show there
write("harness_art_travel", manifest=manifest("harness_art_travel", map="harness_art_tmap",
      map_button={"label": "Art Travel", "return_label": "Village", "nest": [250, 100]},
      monster_art={"goblin": {"standard": {"loop": {"body": {"leg_1": {"fill": "spr_h_goblin_body_loop_v2_alpha", "line": "spr_h_goblin_body_loop_v2_line"}},
                                                         "hand": {"leg_1": "spr_h_goblin_hand_loop_v2_alpha"}}}, **WALK_T["goblin"]}, "hobgoblin": HOB_T}))
print("wrote")
