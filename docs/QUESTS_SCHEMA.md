# GNX Quest System — JSON Schema

## manifest.json

Add `"quests": "quests.json"` to your manifest. Quest state keys should be declared in `save_state.fields` with default values (typically 0 or -1).

## quests.json structure

```json
{
  "portraits": { ... },
  "popups": { ... },
  "events": { ... },
  "triggers": [ ... ]
}
```

### portraits

Map of portrait key → sprite definition. Loaded at mod init via `sprite_add`.
The loader auto-prefixes `portraits/` to the strip filename, so just use the
filename directly.

```json
"portraits": {
  "my_face": {"strip": "my_portrait.png"},
  "my_face_2": {"strip": "my_portrait_2.png", "frames": 2}
}
```

`frames` defaults to 1 if omitted. Portrait PNGs must be **133x113** (vanilla
`spr_portrait` frame size). Place them in `{mod_root}/portraits/`.

In dialog lines, reference by key: `"portrait": "my_face"`. Use `-1` for
vanilla Lilith portrait, or an integer (0-94) for vanilla sub-image indices.
Portrait keys are mod-scoped (no cross-mod collisions).

### popups

Map of popup key → text string. Creates vanilla-style toast notifications.

```json
"popups": {
  "escape_popup": "The captive has vanished from the cage...",
  "quest_complete": "You have completed the quest!"
}
```

Referenced by `post_raid.cage_escape.popup` (see
[GNX_MODDING.md §13](GNX_MODDING.md#13-post-raid-cage-escape)) and by
the `popup` side effect type.

### events

Map of event_id → event definition. Two types: `notification` and `quest`.

#### notification event

```json
"my_intro": {
  "type": "notification",
  "dialog": [
    {"speaker": "Character Name", "portrait": "portrait_key", "text": "Dialog line."},
    {"speaker": "Character Name", "portrait": -1, "text": "Uses vanilla portrait."}
  ],
  "side_effects": [
    {"type": "set_state", "key": "boss_state", "value": 0}
  ],
  "next_event": "my_quest"
}
```

#### quest event

```json
"my_quest": {
  "type": "quest",
  "quest_text": "Capture the boss in the Village.",
  "reward": {"type": "gold", "amount": 500},
  "completion": {"type": "boss_captured", "class": "test_mod.Frieren"},
  "completion_hook": "post_raid",
  "next_event": "my_win_dialog"
}
```

`next_event` can be `null` to end the chain.

### triggers

Array of trigger definitions. Each trigger fires an event when all conditions are met at a specific hook point.

```json
"triggers": [
  {
    "event": "my_intro",
    "hook": "post_raid_win",
    "conditions": [
      {"type": "state_equals", "key": "boss_state", "value": -1},
      {"type": "stage_cleared", "stage": 2, "min_level": 2}
    ]
  }
]
```

A trigger fires at most once per save (use a state key guard to prevent re-firing).

## Condition types

Used in triggers, quest completion, and conditional raid_spawns.

| Type | Params | True when |
|------|--------|-----------|
| `state_equals` | `key`, `value` | mod save state key == value |
| `state_gte` | `key`, `value` | mod save state key >= value |
| `unit_count` | `class` (optional), `value` | units of that class >= value. Omit `class` to count all units |
| `gold_gte` | `value` | `global.val.money >= value` |
| `floor_gte` | `value` | `global.val.floor >= value` |
| `cell_count` | `h_type`, `value` | count of built cells with that h_type >= value |
| `cell_built` | `h_type` (string ref or int) | at least one cell with that h_type exists |
| `cell_occupied` | `h_type` | at least one cell with that h_type has a unit |
| `stage_discovered` | `stage` (0-4) | `stage_info[stage] != -1` |
| `stage_cleared` | `stage`, `min_level` | `stage_info[stage].max_lvl >= min_level` |
| `boss_captured` | `class` (string ref or int) | unit with that class exists in cage |
| `raid_won` | (none) | always true (only meaningful at post_raid_win hook) |

String refs (`"mod_id.ClassName"`) are pre-resolved to integer IDs at load
time. You can use string refs or integer IDs interchangeably in `class` and
`h_type` fields.

## Side effect types

| Type | Params | Effect |
|------|--------|--------|
| `set_state` | `key`, `value` | sets mod save state key to value |
| `add_gold` | `amount` | adds gold |
| `add_food` | `amount` | adds food |
| `unlock_cell` | `h_type` (string ref or int) | unlocks cell in build menu |
| `unlock_class` | `class` (string ref or int) | adds class to raid encounter pools |

Side effects are applied **immediately** (synchronous) when a notification
event fires, before the dialog is displayed.

## Reward types

| Type | Params | Notes |
|------|--------|-------|
| `gold` | `amount` | Adds gold |
| `food` | `amount` | Adds food |
| `blueprint` | `h_type`, optional `fragment`, optional `lvl` | Default: complete blueprint (instant unlock, lvl=3). With `"fragment": true`: single fragment (need 3 to combine), `lvl` controls pip display (default 1) |
| `prop` | `prop_id` | Unlocks a prop in the customization menu |

## Hook points (triggers)

| Hook | When evaluated | Use for |
|------|---------------|---------|
| `post_raid_win` | after winning a raid | boss intro triggers, post-victory events |
| `post_raid` | after any raid return | stage-based quest completions |
| `post_raid_loss` | after losing a raid | loss-specific events |
| `cell_built` | when any cell is placed via build menu | construction-gated triggers |

## Completion hooks (for quest events)

`completion_hook` determines when the quest's completion condition is checked:
- `"frame"` — checked every frame during gameplay
- `"post_raid"` — checked after any raid return
- `"post_raid_win"` — checked after winning a raid only
- `"cell_built"` — checked when any cell is placed via build menu

## Event chaining

Events chain via `next_event`. When a notification is dismissed (textbox closed), the next event fires. When a quest is completed and reward claimed, the next event fires. This replicates vanilla's `event_after` pattern.
