#!/usr/bin/env python3
"""
scaffold_cell.py — GNX cell scaffold generator.

Generates a complete cells.json entry stub for a custom GNX cell.
Unlike the class scaffold (which detects existing sprite folders), the cell
scaffold is a category-aware template: it defines the sprite folder naming
convention and pre-wires all mon_spr / layer refs. Modder creates those
folders, puts art in them, then runs gnx_pack_strips.py.

── Full modding workflow ────────────────────────────────────────────────────────

  Step 1 — Generate the cell scaffold:
    python scaffold_cell.py --name "Vampire Cell" \\
        --category breed --cell-prefix vampire --mod-dir mods/my_mod
    # Omit --h-type: GNX assigns a stable hash-based ID from mod name + cell name.

  Step 2 — Create the sprite folders listed in the output under mod/sprites/
            and place your art frames in them.

  Step 3 — Fill in pixel positions (hand_x/y, sp_x/y, sq_x/y, hand_frames)
            and stats (price, mon_types, spawn_info) to match your art.

  Step 4 — Merge the entry into cells.json.

  Step 5 — Pack strips:
    python gnx_pack_strips.py mods/my_mod --force

────────────────────────────────────────────────────────────────────────────────

h_type: omit entirely to let GNX hash-assign a stable ID ≥ 100 from your mod
folder name + cell name (recommended). Supply an explicit value ≥ 43 only if
you have a specific reason (e.g. cross-mod references by integer).
Vanilla uses 1–42, so mod cells never collide with vanilla regardless.

Output: <mod_dir>/cell_<cell_prefix>_scaffold.json
"""

import argparse
import json
from pathlib import Path


# ─── Category templates ───────────────────────────────────────────────────────

# Phase scripts (scr_h) per category
SCR_H = {
    "breed": [
        "scr_slot_h_base_start",
        "scr_slot_h_base_wait",
        "scr_slot_h_base_sloop",
        "scr_slot_h_base_floop",
        "scr_slot_h_base_wait",
        "scr_slot_h_base_ej",
        "scr_slot_h_base_wait",
    ],
    # Add big / tent / drink / dairy templates here when needed
}

SCR_IDLE = {
    "breed": "scr_slot_h_state_idle",
}

# Layer stack per category — mirrors the vanilla WALL1/2 layout
# Format: [layer_id, sprite_or_gnx_ref, is_static, tint] or [..., 5th_flag]
LAYERS = {
    "breed": [
        [12, "spr_dirt_wall", False, -1, False],   # dirt overlay (vanilla shared)
        [0,  "gnx:back",      False, -1],           # background
        [2,  "gnx:handc",     True,  -1],           # hand/contact overlay
        [5,  "gnx:extra",     False, -1],           # extra decorative
        [7,  -1,              False, -1, False],    # reserved (unused)
        [8,  -1,              False, -1, False],    # reserved (unused)
    ],
}

# Goblin sprite slots per category
# Each entry: (gnx_key, has_linework)
GOB_SLOTS = {
    "breed": [
        # Start phase
        ("body_start_v1",  True),
        ("body_start_v2",  True),
        ("hand_start",     True),
        ("pen_start",      False),
        ("touch_start",    False),
        # Loop phase — head (two directions)
        ("head_d1",        True),
        ("head_d2",        True),
        # Loop phase — body / hand
        ("body_loop_v1",   True),
        ("body_loop_v2",   True),
        ("hand_loop_v1",   True),
        ("hand_loop_v2",   True),
        # Loop phase — action sprites
        ("pen_loop",       False),
        ("touch_loop_v1",  False),
        ("enter_loop",     False),
    ],
}

# Cell background sprite slots per category
BG_SLOTS = {
    "breed": ["wall", "back", "handc", "extra"],
}


# ─── Builders ─────────────────────────────────────────────────────────────────

def build_sprites(prefix: str, category: str) -> dict:
    """
    Return pre-pack sprites dict with suggested folder names.
    Naming convention:
      - Cell bg sprites : spr_slot_{prefix}_{key}/
      - Goblin alpha    : spr_h_goblin_{prefix}_{key}_alpha/
      - Goblin linework : spr_h_goblin_{prefix}_{key}_line/
      - Goblin single   : spr_h_goblin_{prefix}_{key}/
    """
    sprites = {}

    # Background (cell) sprites
    for key in BG_SLOTS.get(category, []):
        folder = f"spr_slot_{prefix}_{key}"
        sprites[key] = {"xorig": 0, "yorig": 75, "folder": folder}

    # Goblin sprites
    for key, has_line in GOB_SLOTS.get(category, []):
        if has_line:
            alpha_folder = f"spr_h_goblin_{prefix}_{key}_alpha"
            sprites[key] = {"xorig": 0, "yorig": 90, "folder": alpha_folder}
            line_folder  = f"spr_h_goblin_{prefix}_{key}_line"
            sprites[f"{key}_l"] = {"xorig": 0, "yorig": 90, "folder": line_folder}
        else:
            folder = f"spr_h_goblin_{prefix}_{key}"
            sprites[key] = {"xorig": 0, "yorig": 90, "folder": folder}

    return sprites


def build_mon_spr(category: str) -> dict:
    if category == "breed":
        return {
            "start": {
                "body": {
                    "leg_1": {"alpha": "gnx:body_start_v1", "line": "gnx:body_start_v1_l"},
                    "leg_2": {"alpha": "gnx:body_start_v2", "line": "gnx:body_start_v2_l"},
                },
                "hand":       {"alpha": "gnx:hand_start", "line": "gnx:hand_start_l"},
                "pen":        "gnx:pen_start",
                "touch":      {"default": "gnx:touch_start"},
                "hand_xscale": "random",
            },
            "loop": {
                "head": [
                    {"alpha": "gnx:head_d1", "line": "gnx:head_d1_l"},
                    {"alpha": "gnx:head_d2", "line": "gnx:head_d2_l"},
                ],
                "body": {
                    "leg_1": {"alpha": "gnx:body_loop_v1", "line": "gnx:body_loop_v1_l"},
                    "leg_2": {"alpha": "gnx:body_loop_v2", "line": "gnx:body_loop_v2_l"},
                },
                "hand": {
                    "leg_1": {"alpha": "gnx:hand_loop_v1", "line": "gnx:hand_loop_v1_l"},
                    "leg_2": {"alpha": "gnx:hand_loop_v2", "line": "gnx:hand_loop_v2_l"},
                },
                "pen":   "gnx:pen_loop",
                "touch": {"default": "gnx:touch_loop_v1"},
                "enter": {"default": "gnx:enter_loop"},
            },
        }
    raise ValueError(f"No mon_spr template for category: {category}")


def build_physical(category: str) -> dict:
    return {
        "allow_preg":     True,
        "max_mon_num":    1,
        "anal":           False,
        "slot_dirt_init": 0,
        "character_row":  0,
        "layers":         LAYERS[category],
        "scr_idle":       SCR_IDLE[category],
        "scr_h":          SCR_H[category],
        "scr_draw":       "scr_draw_slot_gnx",
        "slot_range":     1,
        # ── Pixel positions — set these to match your art ─────────────────────
        # hand_x/y: [leg_1_offset, leg_2_offset] in pixels from cell origin
        "hand_x":       [0, 0],
        "hand_y":       [0, 0],
        "hand_xscale":  [1, 1],
        "hand_angle":   [90, 0],
        # hand_frames: which animation frames correspond to each h-scene sub-phase
        "hand_frames": {
            "frame_1": [1],
            "frame_2": [2, 3],
            "frame_3": [2, 3],
        },
        # sp_spr: the splat/climax sprite (vanilla: spr_sp_v_start or spr_sp_h_start)
        "sp_spr":    "spr_sp_v_start",
        # sq / sp: position of the squirt and splat effects
        "sq_x":      0,
        "sq_y":      [0, 0],
        "sp_x":      0,
        "sp_y":      [0, 0],
        "sp_anim_x": 0,
        "sp_anim_y": 0,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Generate a GNX cell scaffold JSON entry.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (omit --h-type for recommended hash-based ID assignment):
  python scaffold_cell.py --name "Vampire Cell" --category breed \\
      --cell-prefix vampire --mod-dir mods/my_mod

  python scaffold_cell.py --name "Cursed Altar" --category breed \\
      --cell-prefix altar --mod-dir mods/my_mod --output altar_cell.json

  # Explicit h_type only if you have a specific reason:
  python scaffold_cell.py --name "Vampire Cell" --h-type 44 --category breed \\
      --cell-prefix vampire --mod-dir mods/my_mod
        """,
    )
    ap.add_argument("--name",        required=True,
                    help="Display name shown in the game UI, e.g. 'Vampire Cell'")
    ap.add_argument("--h-type",      default=None, type=int, dest="h_type",
                    help="Explicit h_type ID (≥ 43). Omit to let GNX hash-assign a stable "
                         "ID ≥ 100 from your mod folder name + cell name (recommended).")
    ap.add_argument("--category",    required=True, choices=list(SCR_H.keys()),
                    help="Cell category: " + ", ".join(SCR_H.keys()))
    ap.add_argument("--cell-prefix", required=True, dest="cell_prefix",
                    help="Short lowercase identifier used in sprite folder names, e.g. vampire. "
                         "Folders will be named spr_slot_{prefix}_* and spr_h_goblin_{prefix}_*.")
    ap.add_argument("--mod-dir",     required=True, dest="mod_dir",
                    help="Path to the mod folder (contains manifest.json)")
    ap.add_argument("--output",      default=None,
                    help="Output path (default: <mod_dir>/cell_<prefix>_scaffold.json)")
    args = ap.parse_args()

    mod_dir = Path(args.mod_dir).resolve()
    prefix  = args.cell_prefix
    cat     = args.category

    if not mod_dir.is_dir():
        ap.error(f"Not a directory: {mod_dir}")

    sprites  = build_sprites(prefix, cat)
    mon_spr  = build_mon_spr(cat)
    physical = build_physical(cat)

    entry = {}
    if args.h_type is not None:
        entry["h_type"] = args.h_type
    entry.update({
        "name":     args.name,
        "category": cat,
        # ── Fill these in ─────────────────────────────────────────────────────
        # mon_types: class_ids allowed in this cell (0 = vanilla goblin, 14+ = mod classes)
        "mon_types":  [0],
        "slot_type":  0,
        "price":      100,
        "spawn_info": {
            "coin":     1,
            "mood":     1,
            "coin_mul": False,
            "mood_mul": False,
        },
        "physical":  physical,
        "human_spr": {
            "mode":      "base+class",
            "base_body": "standard",
        },
        "mon_spr":  mon_spr,
        "sprites":  sprites,
    })

    out = Path(args.output) if args.output else mod_dir / f"cell_{prefix}_scaffold.json"
    out.write_text(json.dumps([entry], indent="\t", ensure_ascii=False), encoding="utf-8")

    # Report
    bg_keys  = BG_SLOTS.get(cat, [])
    gob_keys = GOB_SLOTS.get(cat, [])
    all_folders = [sprites[k]["folder"] for k in list(sprites)]

    print(f"Cell scaffold written: {out}")
    print(f"\n{len(bg_keys)} background sprite folders + "
          f"{len(gob_keys)} goblin slots ({sum(1 + h for _, h in gob_keys)} folders total):")
    print(f"\nCreate these folders under {mod_dir / 'sprites'}/:")
    for folder in all_folders:
        print(f"  {folder}/")
    print(f"\nOptional physical extensions (add to physical manually if needed):")
    print(f"  required_class   — restrict to specific class_ids, e.g. [14, 15]")
    print(f"  range_draw_func  — custom range indicator, e.g. \"scr_draw_l_shrine_range\"")
    print(f"  scr_unoccupy     — called when goblin leaves, e.g. \"scr_gnx_unoccupy_log\"")
    print(f"\nThen: fill hand_x/y + sp_x/y positions → merge into cells.json → "
          f"python gnx_pack_strips.py {mod_dir} --force")


if __name__ == "__main__":
    main()
