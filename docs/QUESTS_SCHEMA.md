# GNX Quest System  - JSON Schema

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
[GNX_MODDING.md §15](GNX_MODDING.md#15-bosses-cage-escape-and-tower)) and by
the tool action `popup` (`"text": "my_mod.<key>"`, modding guide 17.6).

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

#### silent notification (no dialog)

If `dialog` is omitted or an empty array, the notification fires silently: side
effects apply immediately, `next_event` chains, and no bell icon or dialog is
shown. Use this for invisible quest steps (e.g. moving a storyline on).

```json
"story_step_2": {
  "type": "notification",
  "side_effects": [
    {"type": "set_state", "key": "story", "value": 2}
  ],
  "next_event": null
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

A trigger fires **every time** its hook runs and its conditions hold. For a one-time event, add a state key guard (`state_equals` on a key the event's side effects then change). A notification without dialog applies its side effects each time; one with dialog is not queued twice while the first is still waiting.

## Condition types

Used in triggers, quest completion, and conditional raid_spawns.

| Type | Params | True when |
|------|--------|-----------|
| `state_equals` | `key`, `value` | mod save state key == value |
| `state_gte` | `key`, `value` | mod save state key >= value |
| `state_lte` | `key`, `value` | mod save state key <= value |
| `unit_count` | `class` (optional), `value` (default 1) | units of that class >= value. Omit `class` to count all units |
| `gold_gte` | `value` | `global.val.money >= value` |
| `day_gte` | `value` | the day counter (shown under the clock) >= value |
| `day_every` | `value`, `offset` (default 0) | the day is a multiple of `value` (after subtracting `offset`): `{"value": 7}` on days 7, 14, 21...; `{"value": 1}` every day. Meant for the `day_start` hook |
| `has_item` | `item`, `value` (default 1) | the inventory holds at least `value` of that mod item (items.json; `"NAME"` of the quest's mod or `"mod.NAME"`) |
| `floor_gte` | `value` | `global.val.floor >= value` |
| `cell_count` | `h_type`, `value` (default 1) | count of built cells with that h_type >= value |
| `cell_built` | `h_type` (string ref or int) | at least one cell with that h_type exists |
| `cell_occupied` | `h_type` | at least one cell with that h_type has a unit |
| `stage_discovered` | `stage`: 0-4, `"vanilla.FOREST"`, a mod stage `"mod.ID"` or your own `"ID"` (modding guide 27.3) | that stage is discovered on the map the player is on (a stage not on it: false) |
| `stage_cleared` | `stage` (as above), `min_level` | that stage's highest open level >= min_level (`stage_info[stage].max_lvl`) |
| `boss_captured` | `class` (string ref or int) | unit with that class exists in cage |
| `class_unlocked` | `class` (string ref or int) | an `unlock_class` side effect has unlocked that class in this save |
| `raid_won` | (none) | always true (only meaningful at post_raid_win hook) |
| `on_map` | `map` | the player is on that map (`"vanilla"` = the village) |
| `map_visited` | `map` | the player has been on that map (or is on it now) |
| `map_unlocked` | `map` | that map can be travelled to: the village always; a mod map once its `map_info.unlock` held or `unlock_map` opened it (or when it has no `unlock`) |

String refs (`"mod_id.ClassName"`) are pre-resolved to integer IDs at load
time. You can use string refs or integer IDs interchangeably in `class` and
`h_type` fields.

## Side effect types

| Type | Params | Effect |
|------|--------|--------|
| `set_state` | `key`, `value` | sets mod save state key to value |
| `add_gold` | `amount` | adds gold |
| `add_food` | `amount` | adds food |
| `give_item` | `item`, `amount` (default 1) | puts that many of a mod item (items.json) into the inventory |
| `take_item` | `item`, `amount` (default 1) | takes that many out (as many as there are) |
| `unlock_cell` | `h_type` (string ref or int) | unlocks cell in build menu |
| `unlock_class` | `class` (string ref or int) | unlocks the class: saved, and shared by every map like the game's own unlocks. On its own it changes nothing in raids; gate a `raid_spawns` entry on it with `"condition": {"type": "class_unlocked", "class": "my_mod.NAME"}` so the class only appears once unlocked |
| `unlock_map` | `map` | opens a mod map in the travel menu for good, as its `map_info.unlock` would (saved, shared by every map, announced with `New map: <label>`). A map without a travel entry (its mod is off) is logged and ignored |

Side effects are applied **immediately** (synchronous) when a notification
event fires, before the dialog is displayed.

## Reward types

| Type | Params | Notes |
|------|--------|-------|
| `gold` | `amount` | Adds gold |
| `food` | `amount` | Adds food |
| `blueprint` | `h_type`, optional `fragment`, optional `lvl` | Default: complete blueprint (instant unlock, lvl=3). With `"fragment": true`: single fragment (need 3 to combine), `lvl` controls pip display (default 1) |
| `prop` | `prop_id` | Unlocks a prop in the customization menu |
| `item` | `item`, `amount` (default 1) | A mod item (items.json), `"NAME"` of the quest's mod or `"mod.NAME"` |

## Hook points (triggers)

| Hook | When evaluated | Use for |
|------|---------------|---------|
| `post_raid_win` | after winning a raid | boss intro triggers, post-victory events |
| `post_raid` | after any raid return | stage-based quest completions |
| `post_raid_loss` | after losing a raid | loss-specific events |
| `cell_built` | when any cell is placed via build menu | construction-gated triggers |
| `day_start` | when a new day starts (the clock wraps; only once the game's day clock runs, after the early tutorial quest), before that day's autosave. Days skipped at once (a trip's day cost, the SET DAY tool) do not fire it | daily income or upkeep, events on a given day: combine with `day_every` / `day_gte`. Quests with `"completion_hook": "day_start"` are checked then too |
| `map_arrive` | once after every trip, when the destination is up (after its `map_start` and what was taken along) | map storylines: combine with `on_map` / `map_visited`, and guard with a state key for once-only events |

A mod's triggers only run on the maps the mod loads on (its manifest `map`), and
its save state is kept **per map**, like the rest of a map's game state: a
`set_state` on the Outpost is not seen in the village. A storyline that spans
maps reads where the player has been with `map_visited` / `map_unlocked`, which
are shared, rather than with state keys.

## Completion hooks (for quest events)

`completion_hook` determines when the quest's completion condition is checked:
- `"frame"`  - checked every frame during gameplay
- `"post_raid"`  - checked after any raid return
- `"post_raid_win"`  - checked after winning a raid only
- `"cell_built"`  - checked when any cell is placed via build menu

## Event chaining

Events chain via `next_event`. When a notification is dismissed (textbox closed), the next event fires. When a quest is completed and reward claimed, the next event fires. Silent notifications (no dialog) chain immediately without player interaction. This replicates vanilla's `event_after` pattern.
