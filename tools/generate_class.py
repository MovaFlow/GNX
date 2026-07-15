#!/usr/bin/env python3
"""
generate_class.py - interactive classes.json entry generator (GNX)

Asks the modder a series of questions about a new (or override) class and
writes a standalone JSON file containing one class entry, ready to be
copy-pasted into a mod's classes.json array.

Run with no arguments:  python generate_class.py
"""

import json
import sys
from pathlib import Path


def ask(prompt, default=None):
    suffix = f" [{default}]" if default is not None else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val if val else default


def ask_bool(prompt, default=False):
    d = "y" if default else "n"
    while True:
        val = input(f"{prompt} (y/n) [{d}]: ").strip().lower()
        if not val:
            return default
        if val in ("y", "yes"):
            return True
        if val in ("n", "no"):
            return False
        print("  -> answer y/n")


def ask_int(prompt, default=None, allow_blank=False):
    while True:
        d = "" if default is None else str(default)
        val = input(f"{prompt}{f' [{d}]' if d else ''}: ").strip()
        if not val:
            if allow_blank:
                return None
            if default is not None:
                return default
            continue
        try:
            return int(val)
        except ValueError:
            print("  -> expected an integer")


def ask_float(prompt, default):
    while True:
        val = input(f"{prompt} [{default}]: ").strip()
        if not val:
            return default
        try:
            return float(val)
        except ValueError:
            print("  -> expected a number")


def slugify(name):
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


# ---------------------------------------------------------------------------
# Sprite-key skeleton helpers
# ---------------------------------------------------------------------------

def standard_sprite_keys(has_hair, has_legp, has_cape, want_c):
    keys = [
        ("hand", 2, 3, 1, "Hand sprite, 2 frames (open/closed)."),
        ("idle_head", 90, 0, 90, "Idle phase (phase_1), 90 = 3 skins x 30."),
        ("idle_breast", 90, 0, 90, None),
        ("idle_leg_1", 90, 0, 90, None),
        ("idle_leg_2", 90, 0, 90, None),
        ("loop_head", 225, 0, 90, "Loop phase (phase_2), 225 = 3 skins x 75."),
        ("loop_breast", 225, 0, 90, None),
        ("loop_leg_1", 225, 0, 90, None),
        ("loop_leg_2", 225, 0, 90, None),
    ]
    if want_c:
        keys += [
            ("hand_c", 2, 3, 1, "Clothed hand variant."),
            ("idle_breast_c", 90, 0, 90, "Clothed breast (phase_1)."),
            ("idle_leg_c", 90, 0, 90, "Clothed leg (phase_1)."),
            ("loop_breast_c", 225, 0, 90, "Clothed breast (phase_2)."),
            ("loop_leg_c", 225, 0, 90, "Clothed leg (phase_2)."),
        ]
    if has_hair:
        keys += [("idle_hair", 90, 0, 90, "Hair layer."), ("loop_hair", 225, 0, 90, None)]
    if has_legp:
        keys += [("idle_legp", 90, 0, 90, "Cloth hem/skirt overlay."), ("loop_legp", 225, 0, 90, None)]
        if want_c:
            keys += [("idle_legp_c", 90, 0, 90, None), ("loop_legp_c", 225, 0, 90, None)]
    if has_cape:
        keys += [("idle_cape", 90, 0, 90, "Cape/cloak overlay."), ("loop_cape", 225, 0, 90, None)]
    return keys


def big_sprite_keys(has_hair, want_c):
    keys = [
        ("big_start_head", 36, 0, 90, "Big cell start."),
        ("big_start_breast", 36, 0, 90, None),
        ("big_start_leg", 36, 0, 90, "Single leg (leg_any) for start."),
        ("big_idle_head", 48, 0, 90, "Big cell idle."),
        ("big_idle_breast", 48, 0, 90, None),
        ("big_idle_leg_1", 48, 0, 90, None),
        ("big_idle_leg_2", 48, 0, 90, None),
        ("big_loop_head", 105, 0, 90, "Big cell loop."),
        ("big_loop_breast", 105, 0, 90, None),
        ("big_loop_leg", 105, 0, 90, "Single leg (leg_any) for loop."),
    ]
    if want_c:
        keys += [
            ("big_start_breast_c", 36, 0, 90, None), ("big_start_leg_c", 36, 0, 90, None),
            ("big_idle_breast_c", 48, 0, 90, None), ("big_idle_leg_c", 48, 0, 90, None),
            ("big_loop_breast_c", 105, 0, 90, None), ("big_loop_leg_c", 105, 0, 90, None),
        ]
    if has_hair:
        keys += [("big_start_hair", 36, 0, 90, None), ("big_idle_hair", 48, 0, 90, None),
                 ("big_loop_hair", 105, 0, 90, None)]
    return keys


def tent_sprite_keys(has_hair, has_legp, want_c):
    keys = []
    for phase, frames in (("idle", 42), ("loop", 105), ("birth", 42)):
        keys += [
            (f"tent_{phase}_head", frames, 0, 90, f"Tent {phase}."),
            (f"tent_{phase}_breast", frames, 0, 90, None),
            (f"tent_{phase}_leg_1", frames, 0, 90, None),
            (f"tent_{phase}_leg_2", frames, 0, 90, None),
        ]
        if want_c:
            keys += [(f"tent_{phase}_breast_c", frames, 0, 90, None),
                     (f"tent_{phase}_leg_c", frames, 0, 90, None)]
        if has_legp:
            keys.append((f"tent_{phase}_legp", frames, 0, 90, None))
            if want_c:
                keys.append((f"tent_{phase}_legp_c", frames, 0, 90, None))
        if has_hair:
            keys.append((f"tent_{phase}_hair", frames, 0, 90, None))
    return keys


def naked_sprite_keys(cell_type):
    keys = []
    if cell_type == "standard":
        keys += [
            ("naked_idle_head", 90, 0, 90, "Naked base body (phase_1)."),
            ("naked_idle_breast", 90, 0, 90, None), ("naked_idle_leg", 90, 0, 90, None),
            ("naked_idle_legp", 90, 0, 90, None),
            ("naked_loop_head", 225, 0, 90, "Naked base body (phase_2)."),
            ("naked_loop_breast", 225, 0, 90, None), ("naked_loop_leg", 225, 0, 90, None),
            ("naked_loop_legp", 225, 0, 90, None),
            ("naked_hand", 2, 3, 1, "Naked hand."),
        ]
    elif cell_type == "big":
        keys += [
            ("naked_big_start_head", 36, 0, 90, "Naked big start."),
            ("naked_big_start_breast", 36, 0, 90, None), ("naked_big_start_leg", 36, 0, 90, None),
            ("naked_big_idle_head", 48, 0, 90, "Naked big idle."),
            ("naked_big_idle_breast", 48, 0, 90, None),
            ("naked_big_idle_leg_1", 48, 0, 90, None), ("naked_big_idle_leg_2", 48, 0, 90, None),
            ("naked_big_loop_head", 105, 0, 90, "Naked big loop."),
            ("naked_big_loop_breast", 105, 0, 90, None), ("naked_big_loop_leg", 105, 0, 90, None),
            ("naked_big_hand", 2, 3, 1, "Naked hand (big)."),
        ]
    elif cell_type == "tent":
        for phase, frames in (("idle", 42), ("loop", 105), ("birth", 42)):
            keys += [
                (f"naked_tent_{phase}_head", frames, 0, 90, f"Naked tent {phase}."),
                (f"naked_tent_{phase}_breast", frames, 0, 90, None),
                (f"naked_tent_{phase}_leg", frames, 0, 90, None),
                (f"naked_tent_{phase}_legp", frames, 0, 90, None),
            ]
        keys.append(("naked_tent_hand", 2, 3, 1, "Naked hand (tent)."))
    return keys


def carry_sprite_keys(has_hair):
    keys = [("carry_head", 24, 55, 114, "Ogre carry portrait.")]
    if has_hair:
        keys.append(("carry_hair", 24, 55, 114, None))
    keys.append(("carry_base", 24, 55, 114, "Ogre carry base body."))
    return keys


def sprite_def(prefix, key, frames, xorig, yorig, canvas=None, note=None):
    folder = f"{prefix}_{key}"
    d = {"strip": f"strips/{folder}.png", "frames": frames,
         "xorig": xorig, "yorig": yorig, "folder": folder}
    if canvas:
        d["canvas_w"], d["canvas_h"] = canvas
    if note:
        d = {"_note": note, **d}
    return d


# ---------------------------------------------------------------------------
# Clothing map skeletons
# ---------------------------------------------------------------------------

def R(key):
    return f"gnx:{key}"


def leg_variant(prefix, has_hair, has_legp, with_hand=False, has_cape=False):
    out = {}
    if has_hair:
        out["hair"] = R(f"{prefix}_hair")
    out["head"] = R(f"{prefix}_head")
    out["breast"] = R(f"{prefix}_breast")
    if with_hand:
        out["hand"] = R("hand")
    out["leg"] = None
    out["leg_part"] = R(f"{prefix}_legp") if has_legp else -1
    if has_cape:
        out["cape"] = R(f"{prefix}_cape")
    return out


def clothing_standard_skeleton(has_hair, has_legp, has_cape):
    out = {}
    for phase, prefix in (("phase_1", "idle"), ("phase_2", "loop")):
        block = {}
        for legkey in ("leg_1", "leg_2"):
            lv = leg_variant(prefix, has_hair, has_legp, with_hand=True, has_cape=has_cape)
            lv["leg"] = R(f"{prefix}_{legkey}")
            block[legkey] = lv
        out[phase] = block
    return out


def _spr_array(hair, head, breast, hand, leg, legp, cape):
    return [hair, head, breast, hand, leg, legp, cape]


def clothing_standard_special():
    out = {}
    for phase, p in (("phase_1", "idle"), ("phase_2", "loop")):
        out[phase] = {
            "spr_array": _spr_array(R(f"{p}_hair"), R(f"{p}_head"), R(f"{p}_breast"),
                                    R("hand"), R(f"{p}_leg"), R(f"{p}_legp"), R(f"{p}_cape")),
            "spr_c_array": _spr_array(R(f"{p}_hair"), R(f"{p}_head"), R(f"{p}_breast_c"),
                                      R("hand_c"), R(f"{p}_leg_c"), R(f"{p}_legp_c"), R(f"{p}_cape")),
        }
    return out


def clothing_big_skeleton(has_hair):
    out = {}
    for sub, p in (("start", "big_start"), ("loop", "big_loop")):
        d = {"head": R(f"{p}_head"), "breast": R(f"{p}_breast"), "leg_any": R(f"{p}_leg")}
        if has_hair: d["hair"] = R(f"{p}_hair")
        out[sub] = d
    d = {"head": R("big_idle_head"), "breast": R("big_idle_breast"),
         "leg_1": R("big_idle_leg_1"), "leg_2": R("big_idle_leg_2")}
    if has_hair: d["hair"] = R("big_idle_hair")
    out["idle"] = d
    return out


def clothing_big_special():
    out = {}
    for phase, p in (("phase_0", "big_start"), ("phase_1", "big_idle"), ("phase_2", "big_loop")):
        out[phase] = {
            "spr_array": _spr_array(R(f"{p}_hair"), R(f"{p}_head"), R(f"{p}_breast"),
                                    R("hand"), R(f"{p}_leg"), R(f"{p}_legp"), R(f"{p}_cape")),
            "spr_c_array": _spr_array(R(f"{p}_hair"), R(f"{p}_head"), R(f"{p}_breast_c"),
                                      R("hand_c"), R(f"{p}_leg_c"), R(f"{p}_legp_c"), R(f"{p}_cape")),
        }
    return out


def clothing_tent_skeleton(has_hair, has_legp):
    out = {}
    for phase, p in (("phase_1", "tent_idle"), ("phase_2", "tent_loop"), ("phase_4", "tent_birth")):
        block = {}
        for legkey in ("leg_1", "leg_2"):
            lv = leg_variant(p, has_hair, has_legp, with_hand=True)
            lv["leg"] = R(f"{p}_{legkey}")
            block[legkey] = lv
        out[phase] = block
    return out


def clothing_tent_special():
    out = {}
    for phase, p in (("phase_1", "tent_idle"), ("phase_2", "tent_loop"), ("phase_4", "tent_birth")):
        out[phase] = {
            "spr_array": _spr_array(R(f"{p}_hair"), R(f"{p}_head"), R(f"{p}_breast"),
                                    R("hand"), R(f"{p}_leg"), R(f"{p}_legp"), R(f"{p}_cape")),
            "spr_c_array": _spr_array(R(f"{p}_hair"), R(f"{p}_head"), R(f"{p}_breast_c"),
                                      R("hand_c"), R(f"{p}_leg_c"), R(f"{p}_legp_c"), R(f"{p}_cape")),
        }
    return out


# ---------------------------------------------------------------------------
# Naked-layer skeletons
# ---------------------------------------------------------------------------

def naked_standard_skeleton():
    out = {}
    for phase, p in (("phase_1", "idle"), ("phase_2", "loop")):
        out[phase] = {
            "leg_any": {
                "head": R(f"naked_{p}_head"),
                "breast": R(f"naked_{p}_breast"),
                "leg": R(f"naked_{p}_leg"),
                "leg_part": R(f"naked_{p}_legp"),
            }
        }
    out["hand"] = R("naked_hand")
    return out


def naked_big_skeleton():
    out = {}
    for phase, p in (("start", "naked_big_start"), ("idle", "naked_big_idle"), ("loop", "naked_big_loop")):
        d = {"head": R(f"{p}_head"), "breast": R(f"{p}_breast")}
        if phase == "idle":
            d["leg_1"] = R(f"{p}_leg_1")
            d["leg_2"] = R(f"{p}_leg_2")
        else:
            d["leg_any"] = R(f"{p}_leg")
        out[phase] = d
    out["hand"] = R("naked_big_hand")
    return out


def naked_tent_skeleton():
    out = {}
    for phase, p in (("phase_1", "naked_tent_idle"), ("phase_2", "naked_tent_loop"),
                     ("phase_4", "naked_tent_birth")):
        out[phase] = {
            "leg_any": {
                "head": R(f"{p}_head"),
                "breast": R(f"{p}_breast"),
                "leg": R(f"{p}_leg"),
                "leg_part": R(f"{p}_legp"),
            }
        }
    out["hand"] = R("naked_tent_hand")
    return out


def carry_base_spr_skeleton():
    return R("carry_base")


# ---------------------------------------------------------------------------
# Main interactive flow
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  GNX classes.json Entry Generator")
    print("=" * 60)
    print()

    # --- Identity ---
    name = ask("Class display name (e.g. 'Witch')")
    if not name:
        print("Name is required.")
        sys.exit(1)

    prefix = ask("Sprite prefix (e.g. spr_h_witch)", f"spr_h_{slugify(name)}")

    is_override = ask_bool("Is this an override of a vanilla class?")
    if is_override:
        class_id = ask_int("Vanilla class_id to override (0-13)")
    else:
        use_hash = ask_bool("Auto-assign class_id via hash? (recommended for new classes)", True)
        if use_hash:
            class_id = None
            print("  -> class_id will be auto-assigned by GNX at load time.")
        else:
            class_id = ask_int("Manual class_id (>= 14)")

    is_special = ask_bool("Is this an is_special class? (like Lilith, Nyx, etc.)")

    # --- Layers ---
    has_hair = ask_bool("Has hair layer?")
    has_legp = ask_bool("Has leg_part (cloth hem/skirt)?")
    has_cape = ask_bool("Has cape/cloak?") if not is_special else False
    want_c = ask_bool("Has _c clothing variants (breast_c, leg_c, etc.)?")
    want_naked = ask_bool("Has naked layer overrides?")
    want_carry = ask_bool("Has ogre carry sprites?")
    want_gb1 = ask_bool("Has gb1_breast_d2 (G.BANG 1 breast)?") if is_special else False

    # --- Raid ---
    want_raid = ask_bool("Configure raid spawns?")
    want_birth = ask_bool("Configure birth_class mapping?")

    # --- Build sprite defs ---
    sprites = {}
    all_keys = []

    # Standard
    for key, frames, xo, yo, note in standard_sprite_keys(has_hair, has_legp, has_cape, want_c):
        sprites[key] = sprite_def(prefix, key, frames, xo, yo, note=note)
        all_keys.append(key)

    # Big
    for key, frames, xo, yo, note in big_sprite_keys(has_hair, want_c):
        sprites[key] = sprite_def(prefix, key, frames, xo, yo, note=note)
        all_keys.append(key)

    # Tent
    for key, frames, xo, yo, note in tent_sprite_keys(has_hair, has_legp, want_c):
        sprites[key] = sprite_def(prefix, key, frames, xo, yo, note=note)
        all_keys.append(key)

    # Carry
    if want_carry:
        for key, frames, xo, yo, note in carry_sprite_keys(has_hair):
            sprites[key] = sprite_def(prefix, key, frames, xo, yo, note=note)
            all_keys.append(key)

    # Naked
    if want_naked:
        for cell_type in ("standard", "big", "tent"):
            for key, frames, xo, yo, note in naked_sprite_keys(cell_type):
                sprites[key] = sprite_def(prefix, key, frames, xo, yo, note=note)
                all_keys.append(key)

    # GB1
    if want_gb1:
        sprites["gb1_blb"] = sprite_def(prefix, "gb1_blb", 105, 0, 90,
                                        note="G.BANG 1 big_loop breast override.")
        all_keys.append("gb1_blb")

    # Icon (always)
    sprites["icon_head"] = {
        "strip": f"strips/spr_unit_icon_{slugify(name)}_head.png",
        "frames": 3, "xorig": 10, "yorig": 13,
        "canvas_w": 21, "canvas_h": 26,
        "_note": "Icon head (21x26 canvas).",
    }
    sprites["icon_hair"] = {
        "strip": f"strips/spr_unit_icon_{slugify(name)}_hair.png",
        "frames": 3, "xorig": 10, "yorig": 13,
        "canvas_w": 21, "canvas_h": 26,
    }

    # --- Clothing ---
    if is_special:
        clothing_standard = clothing_standard_special()
        clothing_big = clothing_big_special()
        clothing_tent = clothing_tent_special()
    else:
        clothing_standard = clothing_standard_skeleton(has_hair, has_legp, has_cape)
        clothing_big = clothing_big_skeleton(has_hair)
        clothing_tent = clothing_tent_skeleton(has_hair, has_legp)

    # --- Build class entry ---
    entry = {"name": name}
    if class_id is not None:
        entry["class_id"] = class_id
    if is_override:
        entry["override"] = True
    if is_special:
        entry["is_special"] = True

    entry["sprites"] = sprites
    entry["clothing_standard"] = clothing_standard
    entry["clothing_big"] = clothing_big
    entry["clothing_tent"] = clothing_tent

    # Naked layers
    if want_naked:
        entry["naked_standard"] = naked_standard_skeleton()
        entry["naked_big"] = naked_big_skeleton()
        entry["naked_tent"] = naked_tent_skeleton()

    # Carry base
    if want_carry:
        entry["carry_base_spr"] = carry_base_spr_skeleton()

    # GB1
    if want_gb1:
        entry["gb1_breast_d2"] = R("gb1_blb")

    # Birth class
    if want_birth:
        print()
        print("  Goblin class mapping per species (0-3):")
        print("  0=weakest(peasant-like) 1 2 3=strongest(ranger-like)")
        bc = {}
        for sp in ("goblin", "hobgoblin", "tentacle", "ogre"):
            bc[sp] = ask_int(f"  {sp}", default=0)
        entry["birth_class"] = bc

    # Raid spawns
    if want_raid:
        print()
        print("  Raid spawn configuration.")
        spawns = []
        while True:
            print(f"\n  --- Spawn entry #{len(spawns)+1} ---")
            stage = ask_int("  Stage (0-4)", default=0)
            level = ask_int("  Level within stage", default=0)
            weight = ask_int("  Weight (higher = more frequent)", default=50)
            min_lvl = ask_int("  Min unit level", default=1)
            max_lvl = ask_int("  Max unit level", default=3)

            sp = {"stage": stage, "level": level, "weight": weight,
                  "min_lvl": min_lvl, "max_lvl": max_lvl}

            if ask_bool("  Add spawn condition?"):
                cond_type = ask("  Condition type (state_equals/state_gte/floor_gte)", "state_equals")
                cond = {"type": cond_type}
                if cond_type.startswith("state"):
                    cond["key"] = ask("  State key")
                cond["value"] = ask_int("  Value", default=0)
                sp["condition"] = cond

            mpe = ask_int("  max_per_encounter (blank=unlimited)", allow_blank=True)
            if mpe is not None:
                sp["max_per_encounter"] = mpe

            if ask_bool("  Add ap_override? (custom boss AP)"):
                fap = ask_int("  Front AP", default=100)
                bap = ask_int("  Back AP", default=100)
                sp["ap_override"] = [fap, bap]

            spawns.append(sp)
            if not ask_bool("  Add another spawn entry?"):
                break
        entry["raid_spawns"] = spawns

    # --- Output ---
    out_name = f"{slugify(name)}_class.json"
    out_path = Path(out_name)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print(f"  Written: {out_path.resolve()}")
    print(f"  {len(sprites)} sprite defs, {len(all_keys)} keys")
    if want_naked:
        print("  Includes naked_standard / naked_big / naked_tent skeletons")
    if want_carry:
        print("  Includes carry_base_spr")
    if want_gb1:
        print("  Includes gb1_breast_d2")
    print()
    print("  Copy this entry into your mod's classes.json array.")
    print("  Replace gnx:KEY refs with actual sprite strip paths if needed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
