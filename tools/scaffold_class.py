#!/usr/bin/env python3
"""
scaffold_class.py — GNX class scaffold generator.

Original by @kazull. Extended with GNX feature coverage (naked layer detection,
carry_base_spr, naked_standard/big/tent builders).

Scans a mod's sprites/ folder and generates a complete classes.json entry stub
with all sprite slots detected, all clothing sections pre-wired, and stat fields
set to sensible defaults. Modder only needs to fill in stats and merge into classes.json.

── Full modding workflow ────────────────────────────────────────────────────────

  Step 1 — Copy sprites from a vanilla class (skip if using fully custom art):
    python export_class_sprites.py --src ranger --src-id 3 --dst vampire \\
        --sprites "GN Project/Sprites" --output "mods/my_mod/sprites"

  Step 2 — Generate the full classes.json entry from detected sprites:
    python scaffold_class.py --name Vampire \\
        --prefix spr_h_vampire --mod-dir mods/my_mod

  Step 3 — Fill in stats (birth_classes, trade_stage, raid_spawns) in the
            scaffold JSON, then merge the entry into classes.json.

  Step 4 — Pack sprite strips:
    python gnx_pack_strips.py mods/my_mod --force

────────────────────────────────────────────────────────────────────────────────

Output: <mod_dir>/class_<name>_scaffold.json
"""

import argparse
import json
from pathlib import Path

# ─── Sprite key catalogue ─────────────────────────────────────────────────────
# key → (xorig, yorig, folder_template | None)
# None      → default folder is "{prefix}_{key}"
# template  → {prefix} and {name} are substituted at runtime
SPRITES = {
    # Misc
    "hand":                (3,   1,   None),
    "hand_c":              (3,   1,   None),
    # Icon (different prefix convention)
    "icon_head":           (10,  13,  "spr_unit_icon_{name}_head"),
    "icon_hair":           (10,  13,  "spr_unit_icon_{name}_hair"),
    # Carry (different prefix convention)
    "carry_head":          (55,  114, "spr_ogre_carry_head_{name}"),
    # Standard / idle
    "idle_hair":           (0,   90,  None),
    "idle_head":           (0,   90,  None),
    "idle_breast":         (0,   90,  None),
    "idle_breast_c":       (0,   90,  None),
    "idle_leg":            (0,   90,  None),
    "idle_leg_1":          (0,   90,  None),
    "idle_leg_2":          (0,   90,  None),
    "idle_leg_c":          (0,   90,  None),
    "idle_legp":           (0,   90,  "{prefix}_idle_leg_part"),
    "idle_legp_c":         (0,   90,  "{prefix}_idle_leg_part_c"),
    "idle_cape":           (0,   90,  None),
    # Standard / loop
    "loop_hair":           (0,   90,  None),
    "loop_head":           (0,   90,  None),
    "loop_breast":         (0,   90,  None),
    "loop_breast_c":       (0,   90,  None),
    "loop_leg":            (0,   90,  None),
    "loop_leg_1":          (0,   90,  None),
    "loop_leg_2":          (0,   90,  None),
    "loop_leg_c":          (0,   90,  None),
    "loop_legp":           (0,   90,  "{prefix}_loop_leg_part"),
    "loop_legp_c":         (0,   90,  "{prefix}_loop_leg_part_c"),
    "loop_cape":           (0,   90,  None),
    # Big / start
    "big_start_hair":      (0,   90,  None),
    "big_start_head":      (0,   90,  None),
    "big_start_breast":    (0,   90,  None),
    "big_start_breast_c":  (0,   90,  None),
    "big_start_leg":       (0,   90,  None),
    "big_start_leg_c":     (0,   90,  None),
    # Big / idle
    "big_idle_hair":       (0,   90,  None),
    "big_idle_head":       (0,   90,  None),
    "big_idle_breast":     (0,   90,  None),
    "big_idle_breast_c":   (0,   90,  None),
    "big_idle_leg":        (0,   90,  None),
    "big_idle_leg_1":      (0,   90,  None),
    "big_idle_leg_2":      (0,   90,  None),
    "big_idle_leg_c":      (0,   90,  None),
    # Big / loop
    "big_loop_hair":       (0,   90,  None),
    "big_loop_head":       (0,   90,  None),
    "big_loop_breast":     (0,   90,  None),
    "big_loop_breast_c":   (0,   90,  None),
    "big_loop_leg":        (0,   90,  None),
    "big_loop_leg_c":      (0,   90,  None),
    "gb1_breast_d2":       (0,   90,  "spr_h_gb_1_big_loop_breast_{name}"),
    # Tent / idle
    "tent_idle_hair":      (0,   90,  None),
    "tent_idle_head":      (0,   90,  None),
    "tent_idle_breast":    (0,   90,  None),
    "tent_idle_breast_c":  (0,   90,  None),
    "tent_idle_leg":       (0,   90,  None),
    "tent_idle_leg_1":     (0,   90,  "{prefix}_tent_idle_leg_v1"),
    "tent_idle_leg_2":     (0,   90,  "{prefix}_tent_idle_leg_v2"),
    "tent_idle_leg_c":     (0,   90,  None),
    "tent_idle_legp":      (0,   90,  "{prefix}_tent_idle_leg_part"),
    "tent_idle_legp_c":    (0,   90,  "{prefix}_tent_idle_leg_part_c"),
    # Tent / loop
    "tent_loop_hair":      (0,   90,  None),
    "tent_loop_head":      (0,   90,  None),
    "tent_loop_breast":    (0,   90,  None),
    "tent_loop_breast_c":  (0,   90,  None),
    "tent_loop_leg":       (0,   90,  None),
    "tent_loop_leg_1":     (0,   90,  "{prefix}_tent_loop_leg_v1"),
    "tent_loop_leg_2":     (0,   90,  "{prefix}_tent_loop_leg_v2"),
    "tent_loop_leg_c":     (0,   90,  None),
    "tent_loop_legp":      (0,   90,  "{prefix}_tent_loop_leg_part"),
    "tent_loop_legp_c":    (0,   90,  "{prefix}_tent_loop_leg_part_c"),
    # Tent / birth
    "tent_birth_hair":     (0,   90,  None),
    "tent_birth_head":     (0,   90,  None),
    "tent_birth_breast":   (0,   90,  None),
    "tent_birth_breast_c": (0,   90,  None),
    "tent_birth_leg":      (0,   90,  None),
    "tent_birth_leg_1":    (0,   90,  "{prefix}_tent_birth_leg_v1"),
    "tent_birth_leg_2":    (0,   90,  "{prefix}_tent_birth_leg_v2"),
    "tent_birth_leg_c":    (0,   90,  None),
    "tent_birth_legp":     (0,   90,  "{prefix}_tent_birth_leg_part"),
    "tent_birth_legp_c":   (0,   90,  "{prefix}_tent_birth_leg_part_c"),
    # Carry
    "carry_hair":          (55,  114, "spr_ogre_carry_hair_{name}"),
    "carry_base":          (55,  114, "spr_ogre_carry_base_{name}"),
    # Naked / standard
    "naked_idle_head":     (0,   90,  None),
    "naked_idle_breast":   (0,   90,  None),
    "naked_idle_leg":      (0,   90,  None),
    "naked_idle_legp":     (0,   90,  "{prefix}_naked_idle_leg_part"),
    "naked_loop_head":     (0,   90,  None),
    "naked_loop_breast":   (0,   90,  None),
    "naked_loop_leg":      (0,   90,  None),
    "naked_loop_legp":     (0,   90,  "{prefix}_naked_loop_leg_part"),
    "naked_hand":          (3,   1,   None),
    # Naked / big
    "naked_big_start_head":   (0, 90, None),
    "naked_big_start_breast": (0, 90, None),
    "naked_big_start_leg":    (0, 90, None),
    "naked_big_idle_head":    (0, 90, None),
    "naked_big_idle_breast":  (0, 90, None),
    "naked_big_idle_leg_1":   (0, 90, None),
    "naked_big_idle_leg_2":   (0, 90, None),
    "naked_big_loop_head":    (0, 90, None),
    "naked_big_loop_breast":  (0, 90, None),
    "naked_big_loop_leg":     (0, 90, None),
    "naked_big_hand":         (3, 1,  None),
    # Naked / tent
    "naked_tent_idle_head":     (0, 90, None),
    "naked_tent_idle_breast":   (0, 90, None),
    "naked_tent_idle_leg":      (0, 90, None),
    "naked_tent_idle_legp":     (0, 90, "{prefix}_naked_tent_idle_leg_part"),
    "naked_tent_loop_head":     (0, 90, None),
    "naked_tent_loop_breast":   (0, 90, None),
    "naked_tent_loop_leg":      (0, 90, None),
    "naked_tent_loop_legp":     (0, 90, "{prefix}_naked_tent_loop_leg_part"),
    "naked_tent_birth_head":    (0, 90, None),
    "naked_tent_birth_breast":  (0, 90, None),
    "naked_tent_birth_leg":     (0, 90, None),
    "naked_tent_birth_legp":    (0, 90, "{prefix}_naked_tent_birth_leg_part"),
    "naked_tent_hand":          (3, 1,  None),
}

ICON_CANVAS = {"canvas_w": 21, "canvas_h": 26}


# ─── Detection ────────────────────────────────────────────────────────────────

def folder_for(key: str, prefix: str, name: str) -> str:
    """Return the expected sprites/ subfolder name for a given sprite key."""
    _, _, tmpl = SPRITES[key]
    return (tmpl or "{prefix}_{key}").format(prefix=prefix, name=name, key=key)


def scan_sprites(mod_dir: Path, prefix: str, name: str) -> dict:
    """Scan mod_dir/sprites/ and return sprite entries for all detected keys."""
    sprites_dir = mod_dir / "sprites"
    detected = {}
    for key, (xo, yo, _) in SPRITES.items():
        folder = folder_for(key, prefix, name)
        if (sprites_dir / folder).is_dir():
            entry = {"xorig": xo, "yorig": yo}
            # Record non-default folder so gnx_pack_strips can find the frames
            if folder != f"{prefix}_{key}":
                entry["folder"] = folder
            # Icon sprites need canvas dimensions for sprite_add padding
            if key in ("icon_head", "icon_hair"):
                entry.update(ICON_CANVAS)
            detected[key] = entry
    return detected


# ─── Clothing builders ────────────────────────────────────────────────────────

def R(key: str, det: dict):
    """Return gnx:key ref if sprite detected, else -1."""
    return f"gnx:{key}" if key in det else -1


def _std_leg(det, has_hair, has_cape, hd, br, leg, legp, hr, cp):
    d = {}
    if has_hair:
        d["hair"] = R(hr, det)
    d["head"] = R(hd, det)
    d["breast"] = R(br, det)
    d["hand"] = R("hand", det)
    d["leg"] = R(leg, det)
    d["leg_part"] = R(legp, det)
    if has_cape:
        d["cape"] = R(cp, det)
    return d


def build_clothing_standard(det: dict, has_hair: bool, has_cape: bool) -> dict:
    def phase(hd, br, l1, l2, lp, hr, cp):
        return {
            "leg_1": _std_leg(det, has_hair, has_cape, hd, br, l1, lp, hr, cp),
            "leg_2": _std_leg(det, has_hair, has_cape, hd, br, l2, lp, hr, cp),
        }
    return {
        "phase_1": phase(
            "idle_head", "idle_breast",
            "idle_leg_1", "idle_leg_2", "idle_legp",
            "idle_hair", "idle_cape",
        ),
        "phase_2": phase(
            "loop_head", "loop_breast",
            "loop_leg_1", "loop_leg_2", "loop_legp",
            "loop_hair", "loop_cape",
        ),
    }


def _spr_array_helper(det, hair, head, breast, hand, leg, leg_part, cape):
    d = []
    d.append(R(hair, det))
    d.append(R(head, det))
    d.append(R(breast, det))
    d.append(R(hand, det))
    d.append(R(leg, det))
    d.append(R(leg_part, det))
    d.append(R(cape, det))
    return d


def build_clothing_standard_special(det: dict) -> dict:
    def phase(hair, head, breast, breast_c, hand, hand_c, leg, leg_c, legp, legp_c, cp):
        return {
            "spr_array": _spr_array_helper(det, hair, head, breast, hand, leg, legp, cp),
            "spr_c_array": _spr_array_helper(det, hair, head, breast_c, hand_c, leg_c, legp_c, cp),
        }
    return {
        "phase_1": phase("idle_hair",
                         "idle_head",
                         "idle_breast",
                         "idle_breast_c",
                         "hand",
                         "hand_c",
                         "idle_leg",
                         "idle_leg_c",
                         "idle_leg_part",
                         "idle_leg_part_c",
                         "cape"),
        "phase_2": phase("loop_hair",
                         "loop_head",
                         "loop_breast",
                         "loop_breast_c",
                         "hand",
                         "hand_c",
                         "loop_leg",
                         "loop_leg_c",
                         "loop_leg_part",
                         "loop_leg_part_c",
                         "cape"),
    }


def build_clothing_big(det: dict, has_hair: bool) -> dict:
    def slot(hr, hd, br, l1=None, l2=None, la=None):
        d = {}
        if has_hair:
            d["hair"] = R(hr, det)
        d["head"] = R(hd, det)
        d["breast"] = R(br, det)
        if la:
            d["leg_any"] = R(la, det)
        if l1:
            d["leg_1"] = R(l1, det)
        if l2:
            d["leg_2"] = R(l2, det)
        return d
    return {
        "start": slot("big_start_hair", "big_start_head", "big_start_breast",
                      la="big_start_leg"),
        "idle":  slot("big_idle_hair",  "big_idle_head",  "big_idle_breast",
                      l1="big_idle_leg_1", l2="big_idle_leg_2"),
        "loop":  slot("big_loop_hair",  "big_loop_head",  "big_loop_breast",
                      la="big_loop_leg"),
    }


def build_clothing_big_special(det: dict) -> dict:
    def phase(hair, head, breast, breast_c, hand, hand_c, leg, leg_c, legp, legp_c, cp):
        return {
            "spr_array": _spr_array_helper(det, hair, head, breast, hand, leg, legp, cp),
            "spr_c_array": _spr_array_helper(det, hair, head, breast_c, hand_c, leg_c, legp_c, cp),
        }
    return {
        "phase_0": phase("big_start_hair",
                         "big_start_head",
                         "big_start_breast",
                         "big_start_breast_c",
                         "hand",
                         "hand_c",
                         "big_start_leg",
                         "big_start_leg_c",
                         "big_start_leg_part",
                         "big_start_leg_part_c",
                         "cape"),
        "phase_1": phase("big_idle_hair",
                         "big_idle_head",
                         "big_idle_breast",
                         "big_idle_breast_c",
                         "hand",
                         "hand_c",
                         "big_idle_leg",
                         "big_idle_leg_c",
                         "big_idle_leg_part",
                         "big_idle_leg_part_c",
                         "cape"),
        "phase_2": phase("big_loop_hair",
                         "big_loop_head",
                         "big_loop_breast",
                         "big_loop_breast_c",
                         "hand",
                         "hand_c",
                         "big_loop_leg",
                         "big_loop_leg_c",
                         "big_loop_leg_part",
                         "big_loop_leg_part_c",
                         "cape"),
    }


def _tent_leg(det, has_hair, hd, br, leg, legp, hr):
    d = {}
    if has_hair:
        d["hair"] = R(hr, det)
    d["head"] = R(hd, det)
    d["breast"] = R(br, det)
    d["hand"] = R("hand", det)
    d["leg"] = R(leg, det)
    d["leg_part"] = R(legp, det)
    return d


def build_clothing_tent(det: dict, has_hair: bool) -> dict:
    def phase(hd, br, l1, l2, lp, hr):
        return {
            "leg_1": _tent_leg(det, has_hair, hd, br, l1, lp, hr),
            "leg_2": _tent_leg(det, has_hair, hd, br, l2, lp, hr),
        }
    return {
        "phase_1": phase(
            "tent_idle_head",  "tent_idle_breast",
            "tent_idle_leg_1", "tent_idle_leg_2", "tent_idle_legp",
            "tent_idle_hair",
        ),
        "phase_2": phase(
            "tent_loop_head",  "tent_loop_breast",
            "tent_loop_leg_1", "tent_loop_leg_2", "tent_loop_legp",
            "tent_loop_hair",
        ),
        "phase_4": phase(
            "tent_birth_head",  "tent_birth_breast",
            "tent_birth_leg_1", "tent_birth_leg_2", "tent_birth_legp",
            "tent_birth_hair",
        ),
    }


def build_clothing_tent_special(det: dict) -> dict:
    def phase(hair, head, breast, breast_c, hand, hand_c, leg, leg_c, legp, legp_c, cp):
        return {
            "spr_array": _spr_array_helper(det, hair, head, breast, hand, leg, legp, cp),
            "spr_c_array": _spr_array_helper(det, hair, head, breast_c, hand_c, leg_c, legp_c, cp),
        }
    return {
        "phase_1": phase("tent_idle_hair",
                         "tent_idle_head",
                         "tent_idle_breast",
                         "tent_idle_breast_c",
                         "hand",
                         "hand_c",
                         "tent_idle_leg",
                         "tent_idle_leg_c",
                         "tent_idle_leg_part",
                         "tent_idle_leg_part_c",
                         "cape"),
        "phase_2": phase("tent_loop_hair",
                         "tent_loop_head",
                         "tent_loop_breast",
                         "tent_loop_breast_c",
                         "hand",
                         "hand_c",
                         "tent_loop_leg",
                         "tent_loop_leg_c",
                         "tent_loop_leg_part",
                         "tent_loop_leg_part_c",
                         "cape"),
        "phase_4": phase("tent_birth_hair",
                         "tent_birth_head",
                         "tent_birth_breast",
                         "tent_birth_breast_c",
                         "hand",
                         "hand_c",
                         "tent_birth_leg",
                         "tent_birth_leg_c",
                         "tent_birth_leg_part",
                         "tent_birth_leg_part_c",
                         "cape"),
    }


def build_gb1_breast(det: dict):
    return R("gb1_breast_d2", det)


# ─── Naked layer builders ──────────────────────────────────────────────────────────────

def _naked_phase(det, phase_prefix):
    keys = {"head": f"{phase_prefix}_head", "breast": f"{phase_prefix}_breast",
            "leg": f"{phase_prefix}_leg", "legp": f"{phase_prefix}_legp"}
    block = {}
    for part, spr_key in keys.items():
        ref = R(spr_key, det)
        if ref != -1:
            real_part = "leg_part" if part == "legp" else part
            block[real_part] = ref
    return block if block else None


def build_naked_standard(det):
    out = {}
    for phase_key, pfx in (("phase_1", "naked_idle"), ("phase_2", "naked_loop")):
        phase = _naked_phase(det, pfx)
        if phase:
            out[phase_key] = {"leg_any": phase}
    if "naked_hand" in det:
        out["hand"] = R("naked_hand", det)
    return out if out else None


def build_naked_big(det):
    out = {}
    for phase_key, pfx in (("start", "naked_big_start"), ("idle", "naked_big_idle"),
                            ("loop", "naked_big_loop")):
        d = {}
        for part in ("head", "breast"):
            ref = R(f"{pfx}_{part}", det)
            if ref != -1:
                d[part] = ref
        if phase_key == "idle":
            for lk in ("leg_1", "leg_2"):
                ref = R(f"{pfx}_{lk}", det)
                if ref != -1:
                    d[lk] = ref
        else:
            ref = R(f"{pfx}_leg", det)
            if ref != -1:
                d["leg_any"] = ref
        if d:
            out[phase_key] = d
    if "naked_big_hand" in det:
        out["hand"] = R("naked_big_hand", det)
    return out if out else None


def build_naked_tent(det):
    out = {}
    for phase_key, pfx in (("phase_1", "naked_tent_idle"), ("phase_2", "naked_tent_loop"),
                            ("phase_4", "naked_tent_birth")):
        phase = _naked_phase(det, pfx)
        if phase:
            out[phase_key] = {"leg_any": phase}
    if "naked_tent_hand" in det:
        out["hand"] = R("naked_tent_hand", det)
    return out if out else None


def build_carry_base_spr(det):
    ref = R("carry_base", det)
    return ref if ref != -1 else None


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Generate a GNX class scaffold JSON entry from detected sprites.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scaffold_class.py --name Vampire --prefix spr_h_vampire --mod-dir mods/test_mod
  python scaffold_class.py --name Orc --prefix spr_h_orc --mod-dir mods/orc_mod --output orc_class.json
  python scaffold_class.py --name Peasant --class-id 0 --prefix spr_h_mypeasant --mod-dir mods/test_mod  # override vanilla
        """,
    )
    ap.add_argument("--name",     required=True, help="Class name, e.g. Vampire")
    ap.add_argument("--class-id", type=int, dest="class_id", default=None,
                    help="Only needed for override: true classes — the vanilla slot (0–13) "
                         "to replace. New classes get a stable ID auto-assigned by the GNX "
                         "loader via hash; omit this arg for new classes.")
    ap.add_argument("--prefix",   required=True, help="Sprite prefix, e.g. spr_h_vampire")
    ap.add_argument("--mod-dir",  required=True, dest="mod_dir")
    ap.add_argument("--output",   default=None,
                    help="Output path (default: <mod_dir>/class_<name>_scaffold.json)")
    ap.add_argument("--is_special", action="store_true", help="Clothing sprites are in spr_array format")
    args = ap.parse_args()

    mod_dir  = Path(args.mod_dir).resolve()
    name     = args.name.lower()
    prefix   = args.prefix

    if not mod_dir.is_dir():
        ap.error(f"Not a directory: {mod_dir}")

    # Detect sprites
    det = scan_sprites(mod_dir, prefix, name)

    has_hair  = "idle_hair"  in det
    has_cape  = "idle_cape"  in det
    has_icon  = "icon_head"  in det
    has_icon_hair = "icon_hair" in det

    # Report
    print(f"Mod dir : {mod_dir}")
    print(f"Sprites : {mod_dir / 'sprites'}")
    print(f"Prefix  : {prefix}")
    print(f"Detected: {len(det)}/{len(SPRITES)} sprite slots\n")

    for key in SPRITES:
        folder = folder_for(key, prefix, name)
        mark   = "✓" if key in det else "✗"
        print(f"  {mark} {key:<22} sprites/{folder}/")

    naked_count = sum(1 for k in det if k.startswith("naked_"))
    has_carry_base = "carry_base" in det

    print(f"\nauto-detected:  has_hair={has_hair}  has_cape={has_cape}  "
          f"has_icon={has_icon}  has_icon_hair={has_icon_hair}  "
          f"naked={naked_count}  carry_base={has_carry_base}")

    # Build entry
    # class_id is omitted for new classes — GNX loader assigns a stable ID via hash.
    # Only add it if --class-id was supplied (i.e., override: true targeting a vanilla slot).
    entry = {}
    if args.class_id is not None:
        entry["class_id"] = args.class_id
    entry.update({
        "name":              args.name,
        "override":          False,         # set true to replace a vanilla class (requires class_id)
        "is_special":        args.is_special,
        "has_hair":          has_hair,
        "hand_color":        "gnx:hand",
        "icon":              ("gnx:icon_head" if has_icon else -1),
        "icon_hair":         ("gnx:icon_hair" if has_icon_hair else -1),
        "sprite_prefix":     prefix,
        "sprites":           det,
	"gb1_breast_d2":     build_gb1_breast(det),
        "clothing_standard": (build_clothing_standard_special(det) if args.is_special else build_clothing_standard(det, has_hair, has_cape)),
        "clothing_big":      (build_clothing_big_special(det) if args.is_special else build_clothing_big(det, has_hair)),
        "clothing_tent":     (build_clothing_tent_special(det) if args.is_special else build_clothing_tent(det, has_hair)),
    })

    # Naked layer overrides (only added if sprites detected)
    ns = build_naked_standard(det)
    if ns:
        entry["naked_standard"] = ns
    nb = build_naked_big(det)
    if nb:
        entry["naked_big"] = nb
    nt = build_naked_tent(det)
    if nt:
        entry["naked_tent"] = nt
    cbs = build_carry_base_spr(det)
    if cbs:
        entry["carry_base_spr"] = cbs

    entry.update({
        # ── Fill these in before merging into classes.json ─────────────────
        # birth_class: which class_id each of the 4 offspring slots produce
        "birth_class":       {"goblin": 0, "hobgoblin": 0, "tentacle": 0, "ogre": 0},
        # trade_stage: shop stage at which this class becomes available (1-3)
        "trade_stage":       2,
        # raid_spawns: list of {stage, level, weight, min_lvl, max_lvl} entries
        "raid_spawns":       [],
        # preg_mon_type_override: override which pregnancy monster type is used (int)
        # preg_c_override:        override pregnancy capacity (int)
        # (omit both if using vanilla defaults for this class)
    })

    out = Path(args.output) if args.output else mod_dir / f"class_{name}_scaffold.json"
    out.write_text(json.dumps([entry], indent="\t", ensure_ascii=False), encoding="utf-8")

    print(f"\nWrote: {out}")
    print("""
Next steps:
  1. Review the scaffold — check -1 refs for slots you expect to be filled.
  2. Set birth_classes, trade_stage, raid_spawns.
  3. Optionally add preg_mon_type_override / preg_c_override.
  4. Merge the entry into classes.json (append to the array).
  5. Run:  python gnx_pack_strips.py <mod_dir> --force
""")


if __name__ == "__main__":
    main()
