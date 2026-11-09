"""Drafts the monster art alias table from sprite names, checked against the dump (monster art rework, Phase 0).
Run: python tools/mon_art_alias_draft.py   (after mon_art_inventory.py and the dump baselines)
A draft for hand review in Phase 1: it lists shared sprites and any monster sprite it could not address."""
import json
import re
from pathlib import Path

from mon_art_diff import load

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "harness_game" / "mon_art"
CLASSES = ("cow", "lilith", "nyx", "morrigan", "cat")
FAMILIES = (("gb_1", "gbang_1"), ("gb_2", "gbang_2"), ("gb_3", "gbang_3"), ("giant", "giant"), ("dairy", "dairy"),
            ("drink", "drink"), ("milk", "milk"), ("shrine", "shrine"), ("chain", "chains"), ("birth", "birth"))
PARTS = ("body", "hand", "head", "pen", "touch", "enter")
NO_LEGS = ("pen", "head")
PHASE_NAMES = {"-1": "contact", "0": "start", "1": "loop", "2": "loop", "3": "ej", "6": "idle_start", "7": "start_loop", "8": "loop_ej", "9": "ej_birth", "10": "ej_end"}


def line_name(fill):
    if "_alpha" not in fill:
        return None
    return fill.replace("_alpha", "_line")


# vanilla names that are scene art without the usual spr_h_ prefix, and sprites drawn as another part than their name says
UNPREFIXED = r"spr_(hobgoblin)_(shrine_.+)"
DRAWN_AS = {"spr_h_ogre_shrine_start_enter": "pen", "spr_h_goblin_body_start_pen_giant": "pen", "spr_h_hobgoblin_body_start_pen_giant": "pen"}  # s_mon_data: case 39 and the GIANT cell draw these as the pen
FAMILY_OF = {"spr_h_ogre_body_loop_morrigan": "chains", "spr_h_ogre_body_loop_morrigan_extra": "chains"}  # drawn by the chain cell, s_slot_draw
# the ogre touch art is picked only in the goblin G.BANG 1 branch (s_mon_data, placement 0), so the address names the goblin that draws it
TOUCHED_BY_GOBLIN = {"spr_h_ogre_touch_loop" + s for s in ("", "_cow", "_nyx", "_lilith", "_morrigan", "_cat")}


def is_scene_art(name):
    return name.startswith("spr_h_") or re.fullmatch(UNPREFIXED, name) is not None


def address_of(name):
    m = re.fullmatch(r"spr_h_(goblin|hobgoblin|ogre)_(.+)", name) or re.fullmatch(UNPREFIXED, name)
    if not m or name.endswith("_line") or "_line_" in name:
        return None
    monster, rest = m.groups()
    toks = rest.split("_")
    if name in TOUCHED_BY_GOBLIN:
        monster = "goblin"
    family = "gbang_1" if name in TOUCHED_BY_GOBLIN else FAMILY_OF.get(name, "standard")
    for key, fam in FAMILIES:
        if key in rest:
            family = fam
            break
    phase = "start" if "start" in toks else ("ej" if "ej" in toks else "loop")
    part = DRAWN_AS.get(name) or next((p for p in PARTS if p in toks), "body")
    cls = next((c for c in CLASSES if c in toks), None)
    if cls:
        variant = cls
    elif "v1" in toks:
        variant = "leg_1"
    elif "v2" in toks:
        variant = "leg_2"
    elif "v3" in toks:
        variant = "leg_0"
    else:
        variant = "any"
    anal = ".anal" if "anal" in toks else ""
    tail = "" if part in NO_LEGS and variant == "any" else "." + variant
    return f"{monster}.{family}{anal}.{phase}.{part}{tail}"


def observed_uses(dump):
    """sprite name -> set of 'monster.phase.field' it was picked for, from a dump."""
    mons = {"0": "goblin", "1": "hobgoblin", "3": "ogre"}
    uses = {}
    for key, values in dump["records"].items():
        if key.startswith("S:"):
            continue
        h, m, ph = key.split("|")[:3]
        for text in values:
            for part in text.split(";"):
                if "=" not in part or part.startswith(("sd.", "depth", "xscale", "sx", "sy", "mx", "my", "oa", "draw")):
                    continue
                field, val = part.split("=", 1)
                if is_scene_art(val):
                    uses.setdefault(val, set()).add(f"{mons[m]}.{PHASE_NAMES[ph]}.{field}")
    return uses


def main():
    inv = json.loads((OUT / "inventory.json").read_text(encoding="utf-8"))
    uses = {}
    for base in ("vanilla.base.txt", "old_keys.base.txt", "real.base.txt"):
        p = OUT / base
        if p.is_file():
            for k, v in observed_uses(load(p)).items():
                uses.setdefault(k, set()).update(v)
    names = set(inv["sprites"]) | set(uses)
    addresses = {}
    unaddressed = []
    for n in sorted(names):
        a = address_of(n)
        if a:
            addresses.setdefault(a, []).append(n)
        elif is_scene_art(n) and not n.endswith("_line") and "_line_" not in n:
            unaddressed.append(n)
    for a in list(addresses):
        parts = a.split(".")
        if parts[-1].startswith("leg_"):
            addresses.setdefault(".".join(parts[:-1] + ["any"]), [])
            addresses[".".join(parts[:-1] + ["any"])] += addresses[a]
    shared = {n: sorted(u) for n, u in sorted(uses.items()) if len({x.split(".")[0] + "." + x.split(".")[1] for x in u}) > 1}
    missing_from_addresses = sorted(n for n in uses if address_of(n) is None and not n.endswith("_line") and "_line_" not in n)
    out = {"addresses": addresses, "shared": shared, "unaddressed": unaddressed, "picked_but_unaddressed": missing_from_addresses}
    (OUT / "alias_draft.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{len(addresses)} addresses, {len(shared)} shared sprites, {len(unaddressed)} unaddressed, {len(missing_from_addresses)} picked but unaddressed")


if __name__ == "__main__":
    main()
