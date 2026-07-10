# GNX Naked Layer Override Schema

**Status: IMPLEMENTED** (2026-07-10)

New optional fields on class entries in `classes.json`. All sprite values use the same `"gnx:key"` reference system as `clothing_*`.

### GML Implementation

| Function | File | Purpose |
|----------|------|---------|
| `gnx_resolve_naked_big_phase` | `s_initials.gml` | Resolves big cell naked phase (flat legs + leg_0 sub-object) |
| `gnx_get_carry_base` | `s_initials.gml` | Resolves carry_base_spr (struct or single) for a class+leg |
| Naked loaders (inline) | `s_initials.gml` | Parse naked_standard/big/tent/carry_base_spr, store on `_rclass` |
| Naked dispatch (3 blocks) | `s_unit_data.gml` | Override `_rspr`/`_rbspr`/`_rtspr` slots in `scr_set_class_spr_data` |
| Carry dispatch (2 calls) | `s_unit_data.gml` | `gnx_get_carry_base` in `scr_set_patrol_spr_data` |
| T40 | `s_initials.gml` | Validates all naked layer sprites resolve correctly |

## Summary

| Field | Overrides | For |
|-------|-----------|-----|
| `naked_standard` | Base body on standard (1-slot) cells | Non-special classes |
| `naked_big` | Base body on big (2-slot) cells | Non-special classes |
| `naked_tent` | Base body on tent cells | Non-special classes |
| `carry_base_spr` | Ogre carry base body | All classes |

These are **only relevant for non-special classes** (`is_special: false`). Special classes already control both layers via `spr_array`/`spr_c_array`.

## Vanilla base body sprites replaced

Standard: `spr_h_base_idle_head`, `spr_h_base_idle_breast`, `spr_h_base_idle_leg_1/2`, `spr_h_base_idle_leg_part`, `spr_h_base_hand` (and `_3` variants for leg_0, and loop equivalents).

Big: `spr_h_base_big_start_head`, `spr_h_base_big_start_breast`, `spr_h_base_big_start_leg_1/2`, `spr_h_base_hand` (and idle/loop equivalents, and `_3` variants).

Tent: `spr_h_tent_idle_head`, `spr_h_tent_idle_breast`, `spr_h_tent_idle_leg_1/2`, `spr_h_tent_idle_leg_part`, `spr_h_base_hand` (and loop/birth equivalents, and `_3` variants).

Carry: `spr_ogre_carry_base` / `spr_ogre_carry_base_v3`.

---

## naked_standard

Mirrors `clothing_standard` structure. Per-phase, per-leg-variant.

Leg 0 is the variant that uses completely different head/breast sprites in vanilla (`_3` suffix), so each leg variant specifies all body parts independently.

```json
"naked_standard": {
  "hand": "gnx:base_hand",
  "phase_1": {
    "leg_1": {
      "head": "gnx:base_idle_head",
      "breast": "gnx:base_idle_breast",
      "leg": "gnx:base_idle_leg_1",
      "leg_part": "gnx:base_idle_legp"
    },
    "leg_2": {
      "head": "gnx:base_idle_head",
      "breast": "gnx:base_idle_breast",
      "leg": "gnx:base_idle_leg_2",
      "leg_part": "gnx:base_idle_legp"
    },
    "leg_0": {
      "head": "gnx:base_idle_head_3",
      "breast": "gnx:base_idle_breast_3",
      "leg": "gnx:base_idle_leg_3",
      "leg_part": "gnx:base_idle_legp_3"
    }
  },
  "phase_2": {
    "leg_1": {
      "head": "gnx:base_loop_head",
      "breast": "gnx:base_loop_breast",
      "leg": "gnx:base_loop_leg_1",
      "leg_part": "gnx:base_loop_legp"
    },
    "leg_2": {
      "head": "gnx:base_loop_head",
      "breast": "gnx:base_loop_breast",
      "leg": "gnx:base_loop_leg_2",
      "leg_part": "gnx:base_loop_legp"
    },
    "leg_0": {
      "head": "gnx:base_loop_head_3",
      "breast": "gnx:base_loop_breast_3",
      "leg": "gnx:base_loop_leg_3",
      "leg_part": "gnx:base_loop_legp_3"
    }
  }
}
```

All fields optional. Omitted fields keep the vanilla base sprite. This lets a modder override just breasts without touching head/legs.

---

## naked_big

Mirrors `clothing_big` structure. Phases are `start`/`idle`/`loop`.

Big cells have no `leg_part`. Leg variants work the same way (leg_0 = different head/breast).

```json
"naked_big": {
  "hand": "gnx:base_hand",
  "start": {
    "head": "gnx:base_big_start_head",
    "breast": "gnx:base_big_start_breast",
    "leg_1": "gnx:base_big_start_leg_1",
    "leg_2": "gnx:base_big_start_leg_2",
    "leg_0": {
      "head": "gnx:base_big_start_head_3",
      "breast": "gnx:base_big_start_breast_3",
      "leg": "gnx:base_big_start_leg_3"
    }
  },
  "idle": {
    "head": "gnx:base_big_idle_head",
    "breast": "gnx:base_big_idle_breast",
    "leg_1": "gnx:base_big_idle_leg_1",
    "leg_2": "gnx:base_big_idle_leg_2",
    "leg_0": {
      "head": "gnx:base_big_idle_head_3",
      "breast": "gnx:base_big_idle_breast_3",
      "leg": "gnx:base_big_idle_leg_3"
    }
  },
  "loop": {
    "head": "gnx:base_big_loop_head",
    "breast": "gnx:base_big_loop_breast",
    "leg_1": "gnx:base_big_loop_leg_1",
    "leg_2": "gnx:base_big_loop_leg_2",
    "leg_0": {
      "head": "gnx:base_big_loop_head_3",
      "breast": "gnx:base_big_loop_breast_3",
      "leg": "gnx:base_big_loop_leg_3"
    }
  }
}
```

`leg_1`/`leg_2` are flat sprite refs (they share the same head/breast). `leg_0` is a sub-object because vanilla uses different head/breast sprites for that variant (`_3` suffix). This keeps the schema compact while handling the asymmetry.

---

## naked_tent

Mirrors `clothing_tent` structure. Phases are `phase_1`/`phase_2`/`phase_4`.

```json
"naked_tent": {
  "hand": "gnx:base_hand",
  "phase_1": {
    "leg_1": {
      "head": "gnx:tent_idle_head",
      "breast": "gnx:tent_idle_breast",
      "leg": "gnx:tent_idle_leg_1",
      "leg_part": "gnx:tent_idle_legp"
    },
    "leg_2": {
      "head": "gnx:tent_idle_head",
      "breast": "gnx:tent_idle_breast",
      "leg": "gnx:tent_idle_leg_2",
      "leg_part": "gnx:tent_idle_legp"
    },
    "leg_0": {
      "head": "gnx:tent_idle_head_3",
      "breast": "gnx:tent_idle_breast_3",
      "leg": "gnx:tent_idle_leg_3",
      "leg_part": "gnx:tent_idle_legp_3"
    }
  },
  "phase_2": {
    "leg_1": {
      "head": "gnx:tent_loop_head",
      "breast": "gnx:tent_loop_breast",
      "leg": "gnx:tent_loop_leg_1",
      "leg_part": "gnx:tent_loop_legp"
    },
    "leg_2": {
      "head": "gnx:tent_loop_head",
      "breast": "gnx:tent_loop_breast",
      "leg": "gnx:tent_loop_leg_2",
      "leg_part": "gnx:tent_loop_legp"
    },
    "leg_0": {
      "head": "gnx:tent_loop_head_3",
      "breast": "gnx:tent_loop_breast_3",
      "leg": "gnx:tent_loop_leg_3",
      "leg_part": "gnx:tent_loop_legp_3"
    }
  },
  "phase_4": {
    "leg_1": {
      "head": "gnx:tent_birth_head",
      "breast": "gnx:tent_birth_breast",
      "leg": "gnx:tent_birth_leg_1",
      "leg_part": "gnx:tent_birth_legp"
    },
    "leg_2": {
      "head": "gnx:tent_birth_head",
      "breast": "gnx:tent_birth_breast",
      "leg": "gnx:tent_birth_leg_2",
      "leg_part": "gnx:tent_birth_legp"
    },
    "leg_0": {
      "head": "gnx:tent_birth_head_3",
      "breast": "gnx:tent_birth_breast_3",
      "leg": "gnx:tent_birth_leg_3",
      "leg_part": "gnx:tent_birth_legp_3"
    }
  }
}
```

---

## carry_base_spr

Replaces `spr_ogre_carry_base` (legs 1-2) and/or `spr_ogre_carry_base_v3` (leg 0). Accepts either a string (one sprite for all legs) or a struct (per-leg variants).

Simple form (all legs):
```json
"carry_base_spr": "gnx:ogre_carry_base"
```

Per-leg form:
```json
"carry_base_spr": {
  "leg_1": "gnx:ogre_carry_base",
  "leg_2": "gnx:ogre_carry_base",
  "leg_0": "gnx:ogre_carry_base_v3"
}
```

The loader checks `is_struct(carry_base_spr)`: if true, resolves per-leg; if string, resolves once for all legs.

---

## Design decisions

- **Asymmetric leg_0:** `leg_0` is a sub-object (with its own head/breast) because vanilla uses different sprites. `leg_1`/`leg_2` stay flat. Keeps JSON compact.
- **Granular overrides:** All body part fields are optional. Omitted fields keep the vanilla base sprite. A modder can override just breasts without touching head/legs.
- **carry_base_spr:** Accepts string or struct. String is simpler; struct is available when leg variants matter.
- **Hand sprite:** Top-level only (`naked_*.hand`), shared across all phases. Vanilla `spr_h_base_hand` is the same for all phases; no need for per-phase complexity.
