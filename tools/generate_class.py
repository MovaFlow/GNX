#!/usr/bin/env python3
"""
generate_class.py — interactive classes.json entry generator (GNX)

Asks the modder a series of questions about a new (or override) class and
writes a standalone JSON file containing one class entry, ready to be
copy-pasted into a mod's classes.json array.

Field semantics are sourced from gnx_resolve_class / gnx_resolve_class_phase /
gnx_resolve_class_big_phase / gnx_resolve_special_phase / gnx_resolve_class_leg_variant
(s_initials.gml) and docs/GNX_MODDING.md. Run with no arguments:

    python3 generate_class.py
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
# Frame counts / canvas per docs/GNX_MODDING.md §4 (Standard frame counts).
# Each entry: (key, frames, xorig, yorig, note)
# ---------------------------------------------------------------------------

def standard_sprite_keys(has_hair, has_legp, has_cape):
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
    if has_hair:
        keys += [
            ("idle_hair", 90, 0, 90, "Hair layer (has_hair=true)."),
            ("loop_hair", 225, 0, 90, None),
        ]
    if has_legp:
        keys += [
            ("idle_legp", 90, 0, 90, "Cloth hem/skirt overlay."),
            ("loop_legp", 225, 0, 90, None),
        ]
    if has_cape:
        keys += [
            ("idle_cape", 90, 0, 90, "Cape/cloak overlay."),
            ("loop_cape", 225, 0, 90, None),
        ]
    return keys


def big_sprite_keys(has_hair):
    keys = [
        ("big_start_head", 36, 0, 90, "Big cell start, 36 = 3 skins x 12."),
        ("big_start_breast", 36, 0, 90, None),
        ("big_start_leg", 36, 0, 90, "Single leg sprite (leg_any) for start."),
        ("big_idle_head", 48, 0, 90, "Big cell idle, 48 = 3 skins x 16 (or 42 = 3x14, check vanilla ref)."),
        ("big_idle_breast", 48, 0, 90, None),
        ("big_idle_leg_1", 48, 0, 90, None),
        ("big_idle_leg_2", 48, 0, 90, None),
        ("big_loop_head", 105, 0, 90, "Big cell loop, 105 = 3 skins x 35."),
        ("big_loop_breast", 105, 0, 90, None),
        ("big_loop_leg", 105, 0, 90, "Single leg sprite (leg_any) for loop."),
    ]
    if has_hair:
        keys += [
            ("big_start_hair", 36, 0, 90, None),
            ("big_idle_hair", 48, 0, 90, None),
            ("big_loop_hair", 105, 0, 90, None),
        ]
    return keys


def tent_sprite_keys(has_hair):
    keys = []
    for phase, frames in (("idle", 42), ("loop", 105), ("birth", 42)):
        keys += [
            (f"tent_{phase}_head", frames, 0, 90, f"Tent {phase}, {frames} = 3 skins x {frames // 3}."),
            (f"tent_{phase}_breast", frames, 0, 90, None),
            (f"tent_{phase}_leg_1", frames, 0, 90, None),
            (f"tent_{phase}_leg_2", frames, 0, 90, None),
            (f"tent_{phase}_legp", frames, 0, 90, "Cloth hem/skirt overlay."),
        ]
        if has_hair:
            keys.append((f"tent_{phase}_hair", frames, 0, 90, None))
    return keys


def icon_sprite_key():
    return ("icon_head", 3, 10, 13, "Unit portrait icon. 3 frames (one per skin), canvas 21x26, origin 10x13.")


def carry_sprite_keys(has_hair):
    keys = [("carry_head", 24, 55, 114, "Ogre patrol carry portrait. 24 frames, canvas 115x115, origin 55,114.")]
    if has_hair:
        keys.append(("carry_hair", 24, 55, 114, None))
    return keys


def sprite_def(prefix, key, frames, xorig, yorig, canvas=None, note=None):
    folder = f"{prefix}_{key}"
    d = {
        "strip": f"strips/{folder}.png",
        "frames": frames,
        "xorig": xorig,
        "yorig": yorig,
        "folder": folder,
    }
    if canvas:
        d["canvas_w"], d["canvas_h"] = canvas
    if note:
        d = {"_note": note, **d}
    return d


# ---------------------------------------------------------------------------
# Clothing map skeletons (gnx_resolve_class_phase / _big_phase / _leg_variant)
# ---------------------------------------------------------------------------

def leg_variant(prefix_idle_or_loop, has_hair, has_legp, with_hand=False):
    out = {
        "hair": f"gnx:{prefix_idle_or_loop}_hair" if has_hair else -1,
        "head": f"gnx:{prefix_idle_or_loop}_head",
        "breast": f"gnx:{prefix_idle_or_loop}_breast",
    }
    if with_hand:
        out["hand"] = "gnx:hand"
    out["leg"] = None  # filled by caller (leg_1 / leg_2)
    out["leg_part"] = f"gnx:{prefix_idle_or_loop}_legp" if has_legp else -1
    return out


def clothing_standard_skeleton(has_hair, has_legp, has_cape):
    out = {}
    for phase, prefix in (("phase_1", "idle"), ("phase_2", "loop")):
        block = {}
        for legkey in ("leg_1", "leg_2"):
            lv = leg_variant(prefix, has_hair, has_legp, with_hand=True)
            lv["leg"] = f"gnx:{prefix}_{legkey}"
            block[legkey] = lv
        if has_cape:
            block["cape"] = f"gnx:{prefix}_cape"
        out[phase] = block
    return out


def clothing_big_skeleton(has_hair):
    out = {}
    for sub, prefix in (("start", "big_start"), ("loop", "big_loop")):
        d = {"head": f"gnx:{prefix}_head", "breast": f"gnx:{prefix}_breast", "leg_any": f"gnx:{prefix}_leg"}
        if has_hair:
            d["hair"] = f"gnx:{prefix}_hair"
        out[sub] = d
    d = {"head": "gnx:big_idle_head", "breast": "gnx:big_idle_breast",
         "leg_1": "gnx:big_idle_leg_1", "leg_2": "gnx:big_idle_leg_2"}
    if has_hair:
        d["hair"] = "gnx:big_idle_hair"
    out["idle"] = d
    return out


def clothing_tent_skeleton(has_hair, has_legp):
    out = {}
    for phase, prefix in (("phase_1", "tent_idle"), ("phase_2", "tent_loop"), ("phase_4", "tent_birth")):
        block = {}
        for legkey in ("leg_1", "leg_2"):
            lv = leg_variant(prefix, has_hair, has_legp, with_hand=True)
            lv["leg"] = f"gnx:{prefix}_{legkey}"
            block[legkey] = lv
        out[phase] = block
    return out


# ---------------------------------------------------------------------------
# Main interactive flow
# ---------------------------------------------------------------------------

def main():
    print("=== GNX classes.json — class entry generator ===")
    print("Answer the questions. Empty input = default value shown in [].")
    print()

    name = ask("Class name (in-game, UPPERCASE)", "MY_CLASS")
    name = name.upper()

    override = ask_bool("Reskin an existing vanilla class (override)?", False)
    if override:
        print("  -> class_id must be an existing vanilla class (0-13).")
        class_id = ask_int("class_id (vanilla, 0-13)", 0)
    else:
        class_id = ask_int("class_id (mod range, >=14)", 14)
        if class_id < 14:
            print("  WARNING: class_id < 14 without override = possible collision with a vanilla class.")

    is_special = ask_bool("is_special (Nyx/Lilith tier: different spawn caps)?", False)
    has_hair = ask_bool("has_hair (separate hair layer)?", True)

    default_prefix = f"spr_h_{slugify(name)}"
    sprite_prefix = ask("sprite_prefix (runtime sprite name prefix)", default_prefix)

    print()
    print("--- Stats (leave blank = game default behavior) ---")
    fap_mul = ask_float("fap_mul (fap income multiplier)", 1.0)
    bap_mul = ask_float("bap_mul (birth income multiplier, engine default = 0)", 0.0)
    preg_c_override = ask_int("preg_c_override (pregnancy capacity, -1 = class default)", -1, allow_blank=True)
    preg_mon_type_override = ask_int(
        "preg_mon_type_override (0=goblin,1=hobgoblin,2=ogre, blank = omitted)", None, allow_blank=True)

    print()
    print("--- Special sprites ---")
    want_hand_color = ask_bool("Include hand_color (hand color overlay, gnx:hand)?", True)
    want_icon = ask_bool("Include a unit icon (gnx:icon_head)?", True)
    want_icon_hair = has_hair and want_icon and ask_bool("  + icon_hair (hair overlay on the icon)?", False)
    want_carry = ask_bool("Include ogre carry sprites (gnx:carry_head/carry_hair)?", False)

    print()
    print("--- Cell types used (for the sprites/clothing skeleton) ---")
    want_standard = ask_bool("Standard cells (slot_type 0: WALL, RIDE...)?", True)
    has_legp = want_standard and ask_bool("  + leg_part (skirt/cloth hem)?", False)
    has_cape = want_standard and ask_bool("  + cape/cloak overlay?", False)
    want_big = ask_bool("Big cells (slot_type 2: DAIRY, GIANT, G.BANG...)?", False)
    want_tent = ask_bool("Tent cells (slot_type 3: T.WALL, RECOVER...)?", False)

    print()
    print("--- Raid spawns ---")
    raid_spawns = []
    if ask_bool("Add raid_spawns entries?", True):
        n = ask_int("How many entries?", 1)
        for i in range(n):
            print(f"  Entry {i + 1}:")
            stage = ask_int("    stage (0=first)", 0)
            level = ask_int("    level (0 = disables this entry)", 1)
            weight = ask_int("    weight (vanilla ~100-200)", 100)
            min_lvl = ask_int("    min_lvl", 0)
            max_lvl = ask_int("    max_lvl", 1)
            raid_spawns.append({
                "stage": stage, "level": level, "weight": weight,
                "min_lvl": min_lvl, "max_lvl": max_lvl,
            })

    print()
    print("--- Pregnancy / birth / trade ---")
    birth_classes = None
    if ask_bool("Can this class get pregnant (define birth_classes)?", False):
        print("  birth_classes[mon_type] = vanilla mon_class (0-3) assigned at birth.")
        print("  mon_type: 0=goblin 1=hobgoblin 2=ogre 3=?")
        birth_classes = [ask_int(f"  birth_classes[{i}]", 0) for i in range(4)]

    trade_stage = ask_int(
        "trade_stage (0-4, stage at which this class appears in the raid trader; blank = never)",
        None, allow_blank=True)

    # -----------------------------------------------------------------
    # Assemble class entry
    # -----------------------------------------------------------------
    entry = {
        "_note": "Generated by tools/generate_class.py — review before integration.",
        "class_id": class_id,
        "name": name,
        "override": override,
        "is_special": is_special,
        "has_hair": has_hair,
        "sprite_prefix": sprite_prefix,
    }

    if want_hand_color:
        entry["hand_color"] = "gnx:hand"
    if want_icon:
        entry["icon"] = "gnx:icon_head"
        entry["icon_hair"] = "gnx:icon_hair" if want_icon_hair else -1
    elif not override:
        entry["icon"] = -1
        entry["icon_hair"] = -1

    entry["fap_mul"] = fap_mul
    entry["bap_mul"] = bap_mul
    if preg_c_override is not None and preg_c_override != -1:
        entry["preg_c_override"] = preg_c_override
    if preg_mon_type_override is not None:
        entry["preg_mon_type_override"] = preg_mon_type_override

    if raid_spawns:
        entry["raid_spawns"] = raid_spawns
    if birth_classes is not None:
        entry["birth_classes"] = birth_classes
    if trade_stage is not None:
        entry["trade_stage"] = trade_stage

    # -----------------------------------------------------------------
    # sprites dict + clothing maps
    # -----------------------------------------------------------------
    sprites = {}

    def add_keys(keylist):
        for key, frames, xo, yo, note in keylist:
            canvas = None
            if key == "icon_head":
                canvas = (21, 26)
            if key in ("carry_head", "carry_hair"):
                canvas = (115, 115)
            sprites[key] = sprite_def(sprite_prefix, key, frames, xo, yo, canvas, note)

    if want_hand_color:
        add_keys([("hand", 2, 3, 1, "Hand sprite, 2 frames (open/closed).")])
    if want_icon:
        add_keys([icon_sprite_key()])
        if want_icon_hair:
            add_keys([("icon_hair", 3, 10, 13, "Hair overlay for icon, same canvas as icon_head.")])
    if want_carry:
        add_keys(carry_sprite_keys(has_hair))

    if want_standard:
        add_keys(standard_sprite_keys(has_hair, has_legp, has_cape))
        entry["clothing_standard"] = clothing_standard_skeleton(has_hair, has_legp, has_cape)
    if want_big:
        add_keys(big_sprite_keys(has_hair))
        entry["clothing_big"] = clothing_big_skeleton(has_hair)
    if want_tent:
        add_keys(tent_sprite_keys(has_hair))
        entry["clothing_tent"] = clothing_tent_skeleton(has_hair, True)

    # Reorder: keep top-level scalars first, sprites + clothing_* last
    ordered = {}
    for k in ("_note", "class_id", "name", "override", "is_special", "has_hair",
              "hand_color", "icon", "icon_hair", "sprite_prefix",
              "preg_c_override", "preg_mon_type_override", "fap_mul", "bap_mul",
              "raid_spawns", "birth_classes", "trade_stage"):
        if k in entry:
            ordered[k] = entry[k]
    ordered["sprites"] = sprites
    for k in ("clothing_standard", "clothing_big", "clothing_tent"):
        if k in entry:
            ordered[k] = entry[k]

    output = [ordered]

    print()
    default_out = f"class_{slugify(name)}.json"
    out_path = ask("Output file", default_out)
    out_file = Path(out_path)
    out_file.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print()
    print(f"Written: {out_file.resolve()}")
    print("To do before integration:")
    print("  - copy this object into the mod's classes.json array")
    print("  - replace the 'strips/...' placeholders with your real strips (gnx_pack_strips.py)")
    print("  - verify xorig/yorig/canvas for each declared sprite")
    if want_standard or want_big or want_tent:
        print("  - fill in the generated clothing_* maps (review docs/GNX_MODDING.md §5)")
    if not override and class_id < 14:
        print("  - WARNING: class_id < 14 without override -> likely vanilla collision")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        sys.exit(1)
