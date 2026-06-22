#!/usr/bin/env python3
"""
generate_cell.py - interactive cells.json entry generator (GNX)

Asks the modder a series of questions about a new cell (h_type >= 43) or a
vanilla cell patch (h_type 0-42) and writes a standalone JSON file containing
one cell entry, ready to be copy-pasted into a mod's cells.json array.

Field semantics and defaults are sourced from docs/GNX_MODDING.md (sections
6-8: Custom Cells, Cell Physical Block, Cell Sprite Blocks) and
docs/example_mod/cells.json (the "RITUAL" h_type 43 entry and the h_type 1
vanilla-patch entry). The "Advanced physical fields" table in
docs/GNX_MODDING.md §7 (read individually by scr_gnx_register_cell /
scr_set_slot_h_data) is not covered here - add those fields by hand if your
cell needs DAIRY/DRINK/tent/shrine-style mechanics.

Run with no arguments:

    python3 generate_cell.py
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


def slugify(name):
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


# ---------------------------------------------------------------------------
# physical.layers helpers (GNX_MODDING.md §7)
# Standard 6-layer pattern, used by both RITUAL (h_type 43) and the WALL2
# patch (h_type 1) in docs/example_mod/cells.json. Layers 0/2/5 are 4-element
# arrays (no trailing flag); layers 12/7/8 are 5-element (trailing `false`).
# ---------------------------------------------------------------------------

def standard_layers(dirt_sprite, bg_sprite, bg_animated, handc_sprite, handc_animated,
                     extra_sprite, extra_animated):
    return [
        [12, dirt_sprite, False, -1, False],
        [0, bg_sprite, bg_animated, -1],
        [2, handc_sprite, handc_animated, -1],
        [5, extra_sprite, extra_animated, -1],
        [7, -1, False, -1, False],
        [8, -1, False, -1, False],
    ]


def standard_scr_h():
    """7-script h-scene state machine (GNX_MODDING.md §7)."""
    return [
        "scr_slot_h_base_start",
        "scr_slot_h_base_wait",
        "scr_slot_h_base_sloop",
        "scr_slot_h_base_floop",
        "scr_slot_h_base_wait",
        "scr_slot_h_base_ej",
        "scr_slot_h_base_wait",
    ]


# ---------------------------------------------------------------------------
# sprites dict helpers
# ---------------------------------------------------------------------------

def sprite_def(folder, frames, xorig, yorig):
    return {
        "strip": f"strips/{folder}.png",
        "frames": frames,
        "xorig": xorig,
        "yorig": yorig,
        "folder": folder,
    }


# Cell-background sprite defaults: (frames, xorig, yorig), from RITUAL's
# wall/handc/extra entries (all 2-frame strips).
CELL_BG_DEFAULTS = {
    "wall": (2, 0, 75),
    "handc": (2, 0, 66),
    "extra": (2, 0, 66),
}


# ---------------------------------------------------------------------------
# mon_spr (goblin h-scene sprites) - standard pattern from RITUAL.
# Frame counts: *_start*/pen_start = 30 (3 species x 10), touch_start = 90
# (3x30); loop sprites/pen_loop = 75 (3 species x 25), touch_loop/enter_loop
# = 225 (3x75). Confirmed for slot_type 0 (RITUAL) only - re-check frame
# counts for big/tent cells against gnx_debug.txt or a vanilla reference.
# ---------------------------------------------------------------------------

def gen_mon_spr_and_sprites(mon_prefix, n_head_variants):
    sprites = {}
    mon_spr = {"start": {}, "loop": {}}

    mon_spr["start"]["body"] = {
        "leg_1": {"alpha": "gnx:body_start_v1", "line": "gnx:body_start_v1_l"},
        "leg_2": {"alpha": "gnx:body_start_v2", "line": "gnx:body_start_v2_l"},
    }
    for v in (1, 2):
        sprites[f"body_start_v{v}"] = sprite_def(f"{mon_prefix}_start_v{v}_alpha", 30, 0, 90)
        sprites[f"body_start_v{v}_l"] = sprite_def(f"{mon_prefix}_start_v{v}_line", 30, 0, 90)

    mon_spr["start"]["hand"] = {"alpha": "gnx:hand_start", "line": "gnx:hand_start_l"}
    sprites["hand_start"] = sprite_def(f"{mon_prefix}_hand_start_alpha", 30, 0, 90)
    sprites["hand_start_l"] = sprite_def(f"{mon_prefix}_hand_start_line", 30, 0, 90)

    mon_spr["start"]["pen"] = "gnx:pen_start"
    sprites["pen_start"] = sprite_def(f"{mon_prefix}_pen_start", 30, 0, 90)

    mon_spr["start"]["touch"] = {"default": "gnx:touch_start"}
    sprites["touch_start"] = sprite_def(f"{mon_prefix}_touch_start", 90, 0, 90)

    mon_spr["start"]["hand_xscale"] = "random"

    head_list = []
    for i in range(1, n_head_variants + 1):
        head_list.append({"alpha": f"gnx:head_loop_{i}", "line": f"gnx:head_loop_{i}_l"})
        sprites[f"head_loop_{i}"] = sprite_def(f"{mon_prefix}_head_loop_{i}_alpha", 75, 0, 90)
        sprites[f"head_loop_{i}_l"] = sprite_def(f"{mon_prefix}_head_loop_{i}_line", 75, 0, 90)
    mon_spr["loop"]["head"] = head_list

    mon_spr["loop"]["body"] = {
        "leg_1": {"alpha": "gnx:body_loop_v1", "line": "gnx:body_loop_v1_l"},
        "leg_2": {"alpha": "gnx:body_loop_v2", "line": "gnx:body_loop_v2_l"},
    }
    for v in (1, 2):
        sprites[f"body_loop_v{v}"] = sprite_def(f"{mon_prefix}_body_loop_v{v}_alpha", 75, 0, 90)
        sprites[f"body_loop_v{v}_l"] = sprite_def(f"{mon_prefix}_body_loop_v{v}_line", 75, 0, 90)

    mon_spr["loop"]["hand"] = {
        "leg_1": {"alpha": "gnx:hand_loop_v1", "line": "gnx:hand_loop_v1_l"},
        "leg_2": {"alpha": "gnx:hand_loop_v2", "line": "gnx:hand_loop_v2_l"},
    }
    for v in (1, 2):
        sprites[f"hand_loop_v{v}"] = sprite_def(f"{mon_prefix}_hand_loop_v{v}_alpha", 75, 0, 90)
        sprites[f"hand_loop_v{v}_l"] = sprite_def(f"{mon_prefix}_hand_loop_v{v}_line", 75, 0, 90)

    mon_spr["loop"]["pen"] = "gnx:pen_loop"
    sprites["pen_loop"] = sprite_def(f"{mon_prefix}_pen_loop", 75, 0, 90)

    mon_spr["loop"]["touch"] = {"default": "gnx:touch_loop"}
    sprites["touch_loop"] = sprite_def(f"{mon_prefix}_touch_loop", 225, 0, 90)

    mon_spr["loop"]["enter"] = {"default": "gnx:enter_loop"}
    sprites["enter_loop"] = sprite_def(f"{mon_prefix}_enter_loop", 225, 0, 90)

    return mon_spr, sprites


# ---------------------------------------------------------------------------
# Vanilla patch mode (h_type 0-42)
# ---------------------------------------------------------------------------

def build_patch():
    print("--- Vanilla patch (h_type 0-42) ---")
    print("Only physical.layers is generated. Per GNX_MODDING.md §10: 'Only")
    print("physical.layers is replaced; all other cell properties remain vanilla.'")
    print()
    h_type = ask_int("h_type (vanilla, 0-42)", 1)

    print()
    print("Standard 6-layer pattern: dirt / background / handcolor / extra / (reserved) / (reserved)")
    print("Enter sprite names (vanilla spr_... names - confirmed to work in patches per")
    print("the example_mod h_type 1 patch). Leave blank for -1 (no sprite).")
    dirt = ask("Layer 0 (dirt) sprite", "spr_dirt_wall")
    bg = ask("Layer 1 (background) sprite", "")
    bg_animated = ask_bool("  background animated?", False) if bg else False
    handc = ask("Layer 2 (handcolor) sprite", "")
    handc_animated = ask_bool("  handcolor animated?", True) if handc else False
    extra = ask("Layer 3 (extra) sprite", "")
    extra_animated = ask_bool("  extra animated?", False) if extra else False

    layers = standard_layers(
        dirt or -1,
        bg or -1, bg_animated,
        handc or -1, handc_animated,
        extra or -1, extra_animated,
    )

    entry = {
        "_note": "VANILLA PATCH - only physical.layers is overridden; everything else "
                 "(price, income, h-scene logic) stays vanilla. Generated by tools/generate_cell.py.",
        "h_type": h_type,
        "physical": {"layers": layers},
    }

    if any(isinstance(v, str) and v.startswith("gnx:") for v in (bg, handc, extra)):
        print()
        print("  NOTE: 'gnx:' sprite refs were entered. The only patch example in")
        print("  docs/example_mod/cells.json uses vanilla sprite names (no gnx: refs, no")
        print("  'sprites' dict). Whether a patch entry can declare its own 'sprites' dict")
        print("  for gnx: refs is not confirmed by the docs - add a 'sprites' block")
        print("  yourself and verify in gnx_debug.txt before relying on it.")

    return entry, f"patch_h{h_type}.json"


# ---------------------------------------------------------------------------
# New cell mode (h_type >= 43)
# ---------------------------------------------------------------------------

def build_new_cell():
    print("--- New cell (h_type >= 43) ---")
    name = ask("Cell name (in-game, UPPERCASE)", "MY CELL")
    name = name.upper()
    slug = slugify(name)

    h_type = ask_int("h_type (mod range, >=43)", 43)
    if h_type < 43:
        print("  WARNING: h_type < 43 for a new cell -> possible collision with vanilla or another mod.")

    category = ask("category (breed / utility / pleasure)", "breed")

    print()
    mon_types_raw = ask("mon_types (comma list, 0=goblin 1=hobgoblin 2=ogre)", "0")
    mon_types = [int(x.strip()) for x in mon_types_raw.split(",") if x.strip() != ""]

    print()
    print("slot_type: 0=standard wall slot, 2=large cell, 3=tent")
    slot_type = ask_int("slot_type", 0)

    price = ask_int("price (gold cost to build)", 200)

    print()
    print("--- spawn_info ---")
    coin = ask_int("coin (income per cycle)", 2)
    mood = ask_int("mood (income per cycle)", 1)
    coin_mul = ask_bool("coin_mul (multiply by upgrades)?", False)
    mood_mul = ask_bool("mood_mul (multiply by upgrades)?", False)

    print()
    required_class = None
    if ask_bool("Restrict to specific class_ids (required_class)?", False):
        rc_raw = ask("class_id list (comma)", "")
        required_class = [int(x.strip()) for x in (rc_raw or "").split(",") if x.strip() != ""]

    print()
    has_h_scene = ask_bool("Does this cell have an h-scene (mon_spr/goblin sprites)?", True)

    # --- physical core ---
    print()
    print("--- physical (gameplay) ---")
    allow_preg = ask_bool("allow_preg (can result in pregnancy)?", True)
    max_mon_num = ask_int("max_mon_num (simultaneous goblins, usually 1)", 1)
    anal = ask_bool("anal (uses anal variants)?", False)
    slot_dirt_init = ask_int("slot_dirt_init (0 = clean)", 0)
    character_row = ask_int("character_row (0=front, 1=back)", 0)

    # --- layers / cell-bg sprites ---
    print()
    print("--- physical.layers / cell background sprites ---")
    print("Standard pattern: dirt overlay, background, handcolor overlay, extra foreground.")
    use_custom_bg = ask_bool("Use custom (gnx:) sprites for background/handcolor/extra?", True)

    sprites = {}

    if use_custom_bg:
        bg_prefix = ask("Cell-background sprite prefix", f"spr_slot_{slug}")
        for key in ("wall", "handc", "extra"):
            frames, xo, yo = CELL_BG_DEFAULTS[key]
            sprites[key] = sprite_def(f"{bg_prefix}_{key}", frames, xo, yo)
        bg_ref, handc_ref, extra_ref = "gnx:wall", "gnx:handc", "gnx:extra"
        bg_animated, handc_animated, extra_animated = False, True, False
    else:
        bg_ref = ask("Layer 1 (background) sprite (vanilla name or -1)", "-1")
        bg_animated = ask_bool("  background animated?", False)
        handc_ref = ask("Layer 2 (handcolor) sprite (vanilla name or -1)", "-1")
        handc_animated = ask_bool("  handcolor animated?", True)
        extra_ref = ask("Layer 3 (extra) sprite (vanilla name or -1)", "-1")
        extra_animated = ask_bool("  extra animated?", False)
        bg_ref = -1 if bg_ref == "-1" else bg_ref
        handc_ref = -1 if handc_ref == "-1" else handc_ref
        extra_ref = -1 if extra_ref == "-1" else extra_ref

    layers = standard_layers("spr_dirt_wall", bg_ref, bg_animated, handc_ref, handc_animated, extra_ref, extra_animated)

    physical = {
        "allow_preg": allow_preg,
        "max_mon_num": max_mon_num,
        "anal": anal,
        "slot_dirt_init": slot_dirt_init,
        "character_row": character_row,
        "_note_layers": "Rendering layers. Each: [layer_type, sprite, animated, shift_index, opt_flag]. See GNX_MODDING.md §7.",
        "layers": layers,
    }

    if has_h_scene:
        physical["scr_idle"] = "scr_slot_h_state_idle"
        physical["_note_scr_h"] = ("7 scripts for the 7 h-scene phases: start, wait, slow-loop, "
                                    "fast-loop, wait, ejaculation, wait.")
        physical["scr_h"] = standard_scr_h()
    else:
        physical["scr_idle"] = ask("scr_idle (state machine script)", "scr_slot_h_state_idle")
        physical["slot_h"] = False
        print("  NOTE: slot_h=false - see GNX_MODDING.md §7 'Advanced physical fields' for")
        print("  scr_slot_step / scr_slot_base overrides used by no-h-scene vanilla cells")
        print("  (S.SHRINE, F.SHRINE, R.SHRINE, CLEAN, CLONE_B).")

    physical["scr_draw"] = "scr_draw_slot_gnx"
    physical["slot_range"] = ask_int("slot_range (adjacent slots occupied)", 1)

    if required_class:
        physical["required_class"] = required_class

    if ask_bool("Add scr_unoccupy logging (scr_gnx_unoccupy_log)?", True):
        physical["scr_unoccupy"] = "scr_gnx_unoccupy_log"

    if ask_bool("Custom range_draw_func (range indicator)?", False):
        physical["range_draw_func"] = ask("range_draw_func script name", "scr_draw_l_shrine_range")

    if has_h_scene:
        print()
        print("--- Hand positioning (per leg variant 1/2) ---")
        if ask_bool("Use RITUAL preset (hand_x=[17,6] hand_y=[-42,-40] hand_angle=[90,0])?", True):
            hand_x, hand_y, hand_xscale, hand_angle = [17, 6], [-42, -40], [1, 1], [90, 0]
        else:
            hand_x = [ask_int("hand_x leg_1", 17), ask_int("hand_x leg_2", 6)]
            hand_y = [ask_int("hand_y leg_1", -42), ask_int("hand_y leg_2", -40)]
            hand_xscale = [ask_int("hand_xscale leg_1", 1), ask_int("hand_xscale leg_2", 1)]
            hand_angle = [ask_int("hand_angle leg_1", 90), ask_int("hand_angle leg_2", 0)]

        physical["hand_x"] = hand_x
        physical["hand_y"] = hand_y
        physical["hand_xscale"] = hand_xscale
        physical["hand_angle"] = hand_angle
        physical["_note_hand_frames"] = "Which animation frame indices trigger each hand pose."
        physical["hand_frames"] = {"frame_1": [1], "frame_2": [2, 3], "frame_3": [2, 3]}

        if ask_bool("Add splash/squirt VFX (sp_spr, sq_x/y, sp_x/y)?", True):
            physical["sp_spr"] = ask("sp_spr (splash sprite)", "spr_sp_v_start")
            physical["sq_x"], physical["sq_y"] = 22, [-31, -30]
            physical["sp_x"], physical["sp_y"] = 22, [-28, -33]
            physical["sp_anim_x"], physical["sp_anim_y"] = 0, -1
            physical["_note_vfx"] = "Squirt/splash positions copied from the RITUAL preset - tune visually in-game."

    # --- human_spr ---
    base_body = "big" if slot_type == 2 else "standard"
    human_spr = {"mode": "base+class", "base_body": base_body}
    if slot_type == 3:
        print("  NOTE: base_body for tent cells (slot_type 3) defaults to 'standard' here -")
        print("  this is not separately confirmed in the docs; verify against a vanilla tent cell.")

    # --- mon_spr + goblin sprites ---
    mon_spr = None
    if has_h_scene:
        print()
        print("--- mon_spr (goblin h-scene sprites) ---")
        mon_prefix = ask("Goblin sprite prefix", f"spr_h_goblin_{slug}")
        n_heads = ask_int("Number of loop head variants (random per encounter)", 2)
        mon_spr, mon_sprites = gen_mon_spr_and_sprites(mon_prefix, n_heads)
        sprites.update(mon_sprites)
        print("  NOTE: frame counts (30/90 start, 75/225 loop) match RITUAL (slot_type 0).")
        print("  Re-check against gnx_debug.txt for big/tent cells.")

    # --- assemble ---
    entry = {
        "_note": "NEW CELL - h_type 43+ is the mod range. Generated by tools/generate_cell.py.",
        "h_type": h_type,
        "name": name,
        "category": category,
        "mon_types": mon_types,
        "slot_type": slot_type,
        "price": price,
        "spawn_info": {
            "coin": coin, "mood": mood, "coin_mul": coin_mul, "mood_mul": mood_mul,
        },
        "physical": physical,
        "human_spr": human_spr,
    }
    if mon_spr is not None:
        entry["mon_spr"] = mon_spr
    entry["sprites"] = sprites

    return entry, f"cell_{slug}.json"


# ---------------------------------------------------------------------------
# Main interactive flow
# ---------------------------------------------------------------------------

def main():
    print("=== GNX cells.json - cell entry generator ===")
    print("Answer the questions. Empty input = default value shown in [].")
    print()

    is_patch = ask_bool("Vanilla patch (override an existing h_type 0-42)?", False)
    entry, default_out = build_patch() if is_patch else build_new_cell()

    output = [entry]

    print()
    out_path = ask("Output file", default_out)
    out_file = Path(out_path)
    out_file.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print()
    print(f"Written: {out_file.resolve()}")
    print("To do before integration:")
    print("  - copy this object into the mod's cells.json array")
    if not is_patch:
        print("  - replace the 'strips/...' placeholders with your real strips (gnx_pack_strips.py)")
        print("  - verify xorig/yorig for each declared sprite, pad with canvas_w/canvas_h if needed")
        print("  - review mon_spr / sprites against GNX_MODDING.md §8 before painting frames")
        print("  - if h_type collides with vanilla or another mod, GNX silently 'patches'")
        print("    your entry instead of registering a new cell (GNX_MODDING.md §6)")
    print("  - check required_class / scr_idle / scr_h against your intended gameplay")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        sys.exit(1)
