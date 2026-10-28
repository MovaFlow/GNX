# Changelog

## Unreleased

**Game version:** 1.40

### New Features

- **Mod music** (`sounds.json` `music`): a mod can add tracks to the gameplay music, or replace the game's tracks with its own. On a map mod's map the music is that map's own (modding guide 18.9).
- **Mod items and raid loot** (`items.json`): a mod can add inventory items (a name and a 20 x 20 picture) and put them, or blueprint pieces and complete blueprints of its cells, into the finds of raid stages. Each find is added once per save, old saves included. Quests check, give and take items (`has_item`, `give_item`, `take_item`, reward `item`) and tools give them. The names of mod items and of mod-cell blueprints now show in every language (modding guide 25).
- **Mod translations**: a mod can ship `lang/<code>.json` files (`fr`, `ja`, `zh`, `de`, ... ) mapping its English texts to another language. Cell, prop and class names, quest texts and dialogs, popups, tool menus, map names and the MODS menu then show in the player's language, and follow a language change at once; names used as references are not affected (modding guide 4.6).
- **`min_gnx_version`** (manifest key): the oldest GNX a mod works with. An older GNX does not load the mod (it would silently miss the newer keys), shows it as "needs GNX x" in the MODS menu and asks the player to update GNX; mods that require it are skipped too (modding guide 4.2).

### Bug Fixes

- COPY DOWN refused to copy a floor built partly to the left (cells added from the starting pillar with the build side on the left) with "the floor below is not empty", even onto an empty floor. It now copies the whole layout, and also builds the cell of the floor's start slot, which it left out before.
- Wording: the FLOOR button is on each floor's starting pillar (the one every new floor comes with, also the one with UP / DOWN), not on the vanilla entrance; that pillar is not always the leftmost one.
- In any language but English, the quest log showed mod quests through the game's own quest list, which only knows vanilla quests; it now shows their own text.

## v1.5.0

**Game version:** 1.40

### New Features

- **From Mav (1.4.9.5):**
  - **Underground cells** (`"category": "ug_breed"`): the captive sits in a pit below the floor and a tentacle works her from below, with its own scene: start, loop, ej, birth rounds, milking while she has milk. The floor holding one gets a deeper band and the floors below move down. Built from CUSTOM. GNX ships the pit's walls, floor, tentacle and band. See the modding guide, section 24.
  - **Own frame counts per phase** (`physical.frames`) for any mod cell with its own art, with `loop_scale`, `start_loops`, `ej_holds`, `ej_start` and `ej_hold`; a load-time check names every strip whose frame count does not fit its phase.
  - **Intermissions**: short phases between idle and start, start and loop, loop and ej, ej and birth (`physical.intermissions`), with their own captive and monster art.
  - **A second wall** (`sprites.wall_2`), switched with the cell's swap button, and **`physical.transfer`** to keep TRANSFER hobgoblins away from a cell.
  - **Independent places**: in a cell with several monsters, each place can run its own scene. A monster comes in, plays its start, loops and ejaculates on its own clock and leaves alone while the others go on (modding guide 11.5).
  - **Decoration props come alive**: multi-frame props loop on their own, and props can pulse, float, rotate, swing, cycle colours and glow (light or pixel-art rings). They can react to the cell next to them (a monster leaving, a scene starting or ending, a birth, milk) and show a counter, saved with the game. Props are named by name in quest rewards and tools, and placed props are saved by name, so they survive a change in mod load order (modding guide 19.7 to 19.12).
  - **Sprite origins by name** (`"xorig": "center"`, `"yorig": "bottom"`...) for any GNX sprite.
  - Mod values written as text (`"400"`) are read as numbers in more places, `map_start` and the quest map conditions skip a missing `map` with a log line instead of failing, a mod cell without `spawn_info` no longer stops the game at the end of a scene, and an atlas entry on a page that did not load is rejected (the vanilla sprite is used) instead of drawing nothing. Many more crashes on malformed mod data are now mod errors instead (birth class lists, prop entries, glows, atlas files without frames, monster places without species), and a save whose placed props belong to a removed mod loads and keeps them for when the mod comes back.
- **Edit a whole floor**: the entrance's menu has a FLOOR button. It opens the usual edit menu, and the style, the top / middle / bottom props and CLEAR then apply to the entrance and every passage of that floor. A style that would not fit changes nothing; a prop every passage already has is taken off all of them. Moving a floor UP or DOWN is now on its entrance only (from the second floor on); passages offer NEW and EDIT.
- **Documented:** how a mod cell offers a hand pose, a leg pose and clothing on/off in its MOD window (modding guide 9.4), with a test cell.
- **Raids with nothing to capture** (map mods): `map_info.no_capture` lists raid encounters of the mod's own map that can be won for loot and quest progress but capture nobody (bosses excepted, so boss progress is never blocked); the player is told when the raid ends (modding guide 21.2).
- **Copy a floor down**: COPY DOWN in the entrance's FLOOR menu builds the floor's layout on the empty floor below (every slot with the same cell, the passages' styles and props) for the price of building it by hand. Refused, with a message, when the floor below is not empty, when there is none, or when gold is short. The GNX DEBUG toggle FREE COPY makes it free. Captives, monsters and cell upgrades are not copied.
- **Prison sorting**: a sort button on the prison window. Each press sorts by the next order: class, level, milk ready, fertility (can get pregnant now, most pregnancies left first). Empty places go last.
- **6 save slots**: the in-game save buttons and the main menu's load page show 3 slots per page, with page arrows (slots 4-6 are `save_file_4.json` ... next to the vanilla files). The mod menu's "used by" list counts every slot.
- **Own ejaculation pose**: a `fixed` or `class_map` cell's `human_spr` can have a `phase_3` table; the captive's ejaculation is then drawn with it instead of the loop art (it plays the loop's frames). Before, only underground cells could do this (modding guide §10).
- **Prop menu groups**: a prop row that holds props of several mods or categories first lists the groups (VANILLA, then each prop's `category`, else its mod's name), so the long prop list is split into short pages. New prop key `category` (modding guide 19.4).
- **`mon_sprite_swap`** (class key): replace vanilla monster sprites by name wherever they are drawn on a captive of the class, in every cell and phase, like the game does for the Cow. Lets a class with another body shape get goblins, hobgoblins and ogres that fit it. It also reaches the sprites the GIANT, DRINK and G.BANG cells pick themselves and the ogre carrying the captive.

### Bug Fixes

- `preg_mon_type_override` must be 0 to 3; another value is now reported and ignored (`-1`, used by the example mod, made the class never get pregnant).
- A new class that defines no `clothing_standard`, `clothing_big` or `clothing_tent` no longer crashes the game when it enters a cell of that size (`scr_set_class_spr_data`: `clothing_standard` not set); it wears the vanilla Peasant's clothes there, with a warning in the log.
- The GNX DEBUG toggle CAPTURE100 did nothing: its flag was set but the raid's capture roll never read it. Every capture roll now succeeds while it is on.
- In a mod cell with several monsters, monsters still walking to the cell when the scene ended were moved into it and sent back out as if they had taken part; they now just wander off from where they are. A monster call also no longer picks a place no free monster can fill (from Mav).
- A captive taken out for a trip that is cancelled goes back to the first free prison place when her old place has been taken since. Before, she was let go.
- The monster guide's hover again shows the mod girls who gave birth to that monster after you load a save. The list was never saved, so those portraits only came back after a new birth.

## v1.4.9

**Game version:** 1.40

### New Features

- **Shared inventory across maps**: items (milk, blueprints and their torn pieces, bells, orbs) travel with the player on every trip and join the destination's inventory, so pieces found on different maps can complete a blueprint. Saves that already hold separate inventories per map merge them on the next trip.
- **Modded cells in existing slots**: an empty slot's menu ends with CUSTOM when a modded cell fits its size, so a modded cell can go into a slot already built (the NEW menu's CUSTOM still builds slot and cell together).
- **Travel cost and time** (`map_info.travel_cost`): a map can make trips to or from it cost gold and food and take days. The selector shows the cost; a trip that cannot be paid is refused, and the selector's warning line says why.
- **`map_info`**: the manifest key `map_button` is renamed `map_info`, since it now holds the map's settings (name, picture, travel tier, unlock) rather than a button. `map_button` still works; a mod declaring both gets `map_info` and a warning.
- **Map-aware quests**: trigger hook `map_arrive` (once after every trip), conditions `on_map`, `map_visited` and `map_unlocked`, and side effect `unlock_map` (opens a map from a quest, saved and shared like a `map_info.unlock`). `build_mod.py` knows the new conditions.
- **`map` can be a list**: `"map": ["vanilla", "outpost"]` loads a mod on each listed map and nowhere else; its classes and cells keep their hash IDs across those maps. `map_info` / `map_start` need exactly one mod map in the list.
- **Richer `map_start`**: `troops` (hobgoblins, tentacles, ogres and any goblin kind), `prisoners` (captives by class and level) and `unlock_cells`; `cells` and `unlock_cells` accept cell names (`"my_mod.MY CELL"`) as well as numbers. `build_mod.py` checks the new fields.

### Documentation

- **New modding guide** by Mav: `docs/GNX_MODDING.md` is rewritten for beginners, with a glossary, an example for every feature, field tables with types and defaults, the exact log line for common mistakes, and vanilla ID tables. The tutorial and quest schema link to its sections.

### Bug Fixes

- Removed `scr_gnx_claim_quest_reward`, never called: wiring it up would have fired a quest's next event twice (completion already fires it).
- The `give_item` and `give_blueprint` tool actions gave nothing: they never passed the item to the game.
- Extra-large (XL) cell unlocks are synced between maps with the same check as the other categories, so a map mod's XL cell no longer reaches the village's build lists.
- **Modded cells missing from the build menu** (reported by players after 1.4.8): cells whose `h_type` is hash-assigned (no `h_type` in `cells.json`, the usual case) were left out of the NEW > CUSTOM list, so only cells with a fixed `h_type` could be built. Hash-assigned class, cell and prop IDs were stored as 64-bit integers, which the CUSTOM list's check rejected; they are plain numbers again.
- Fixed a crash (`scr_ogre_spd_b`: `slot_data` not set) when a patrolling ogre passes an idle transfer hobgoblin whose cell no longer exists.
- Fixed a crash on load or when a captive enters a cell (`scr_set_slot_spr_part`: "trying to index a variable which is not an array", or index out of range) when a mod cell's `spr_array` / `spr_c_array` is not a list or has fewer than 7 places. Missing places now draw nothing.
- Fixed the frame rate dropping the longer the game stays open, worst in big nests: drips and +/- pop-ups spawned by off-screen cells never finished, so they piled up (about one per frame). They now only pause off-screen when cell culling is turned on, like the cells themselves.
- Fixed goblins getting stuck in a cell after loading a save (pacing in a birth or service cell until the captive is removed, mood dropping). A goblin saved on its way into a cell was put straight inside it on load without the cell starting, so both waited forever. It now finishes walking in and the cell starts normally, and saves already in that state are repaired on load.
- Fixed a second, vanilla goblin drawn over the captive's face in mod cells with their own art (e.g. service cells). It happened on anal scenes with vanilla captives (cells declaring `"anal": false` still roll it, like vanilla WALL 1-4) and for kneeling captives (Shaman, Warrior) when the cell's goblin sprites only cover leg poses 1 and 2. Cells with their own art (`fixed`, `class_map`) now keep their goblin sprites, and a missing leg pose uses the cell's other leg sprites.
- Fixes from Mav's review of 1.4.8:
  - Overriding another mod's class now replaces its `carry_head` / `carry_hair` sprites; the old ones used to stay.
  - `physical.mon_positions` in a patch of a vanilla cell now moves its monsters. It was stored where nothing read it.
  - Two sprite entries using the same PNG with different `frames` or origins are now two sprites; both used to get the settings of the first one loaded.
  - The `unlock_all_cells` tool action now unlocks XL cells too.
  - Fixed a rare crash (`.skin not set`) when a hobgoblin carries a captive whose data is incomplete.
  - Fixed an error when an infant in BIRTH 2 or in a tentacle birth cell is restored from a save without its mother (BIRTH 1 already handled it).
  - The quest log and inventory scroll bars no longer break with many quests (22 or more) or item types (about 75 or more): the bar keeps a minimum size and still scrolls to the last row.

## v1.4.8

**Game version:** 1.40

### New Features

- **Game version 1.40**: GNX is rebased on Goblin Nest 1.40 and keeps the game's own fixes (tentacle cells' mood, the coin number on the shaman goblin). Mods made for 1.38 and 1.39 still load without manifest changes; new mods can declare `"1.40"`.
- **Multi-map travel re-enabled**: `global.gnx_multimap_enabled` is on again. Mods declaring `map`, `map_button` and `map_start` in `manifest.json` get a travel button on the vanilla map.
- **Travel menu**: a map button in the top-left corner of the raid panel's world map, on every map, opens a menu listing every other map, so you can travel from any map to any other (not just between the village and a map). Picking one opens the usual pre-travel selector. The per-map buttons on the world map are gone: the menu replaces them, and `map_button.x` / `y` are ignored.
- **Mod menu** (main menu > MODS): turn mods on and off without touching `GNX_mods`, applied instantly. It is a game-wide setting. Saves now record the mods they were made with and what they use from each; the mod menu shows which saves use a mod and asks before turning a used one off, mods that saves use but are no longer installed are listed as missing, and the load page warns (and asks) before loading a save whose mods are off or missing. Saves from before this version get a count of content no installed mod owns instead.
- **`requires`** in `manifest.json`: mods a mod needs. If one is off the mod is skipped with it; if one is not installed it is skipped and reported.
- **Clearer travel and mod screens**: the pre-travel selector has ALL / NONE per row and shows what stays behind; the travel menu names the map you are on and marks each destination "new" or "last here day N"; the mod page names mods instead of folder ids, says "used by Save 1, autosave", shows details (author, what a mod adds, what it needs) for the mod under the mouse, lights APPLY up while changes are pending and asks before BACK discards them, and shows a mod that failed to load (e.g. made for another game version) as "not loaded" instead of ON. The main menu corner counts mods on and off.
- **Guide entry**: RAIDING > TRAVEL explains travelling between maps (shown when map mods are installed).
- **Pre-travel selector, three tiers** (`map_button.travel`): BASIC (gold, food; goblins on simple maps) with -100/-10/-1/+1/+10/+100, ALL and 0; TROOPS on advanced maps (goblins, hobgoblins, tentacles and ogres, one section per type with every kind side by side; the number under a kind opens the game's number pad); CAPTIVES on complex maps (drag prisoners into the destination's free prison slots). Tabs, a "stays here" line and a warning when the map left would keep no food or no monsters. One layout for every tab: tabs in their own band, bordered panels, a single hint line and the warning above CANCEL / TRAVEL.
- **Shared unlocks**: anything unlocked on one map (cells, raid, shop, timer...) is unlocked on every map, merged in on arrival. A map mod's own cells stay out of other maps' build menus, and boss progress stays with each map.
- **Maps that unlock later**: `map_button.unlock` takes a quest-style condition (or an array of them). The map stays hidden from the world map and the travel menu until it holds once; then it unlocks for good on every map, with a notice.
- **`build_mod.py` checks map mods**: map/map_button/map_start fields, unlock condition types, button positions, map_start cells on floors that do not exist, and the map image. It now also deploys a mod's quests, tools, sounds and props files, its map image, and its `atlas/`, `sounds/` and `portraits/` folders (it only copied classes, cells and strips before, so sound mods and portrait quests deployed broken).
- **Tutorial chapter 8, "A map of your own"**; GNX_MODDING section 20 corrected (map_start `floors` is extra floors below floor 0, default 0; `cells` documented).
- **Travel transition**: travelling fades to black while a goblin with a backpack walks along a dotted route ("Travelling to ..."). It stops and waits while the map loads (the load freezes the picture for a moment, which then reads as a pause instead of a stutter), then walks off as the destination fades in ("Arrived at ...").
- **`human_spr` is now optional on new cells**: omitting it gives `base+class` mode, with `base_body` picked from the cell kind (`b_*` categories / slot type 2 = `big`, `t_*` / slot type 3 = `tent`, otherwise `standard`). This matches what the docs already said.

- **Voice by monster type**: `by_mon_type` in a class's `voice` (or a `sounds.json` `voice_map` entry) picks the moan bank from the monster using her cell: goblin, hobgoblin, tentacle or ogre, each with an optional pitch. Unlisted types keep her usual voice; captured bosses use it too. Voice banks can also carry their own `orgasm` clips, which follow the same choice (banks without them use the shared orgasm pool).

### Contributed by Mav (1.4.7.5)

- **CUSTOM build list**: modded cells get their own CUSTOM button in an empty spot's NEW menu instead of mixing into the vanilla build lists. Picking one builds the slot and the cell together.
- **Staged mod loading**: mods load in three phases (classes of every mod, then cells, then quests, tools, sounds and props), so a cell's `required_class` or a quest condition can name a class or cell from any mod, whatever the folder names. Conditions in `classes.json` that name cells are resolved once every cell exists. IDs and saves are unchanged.
- **Modded classes go to their own cell**: TRANSFER, birth and milking send a modded class to any cell whose `required_class` lists it (like Lilith to the SHRINE or the cow to the DAIRY).
- **Ogres with a line layer** on modded cells: an ogre given `alpha` + `line` sprites by the cell JSON is drawn like goblins (outline, monster transparency settings). Ogres without `line` keep the vanilla look.
- **Shrine loop hands for modded classes**: `mon_spr_overrides.shrine_loop_hand` (and `shrine_loop_hand_c`) draws a modded class's hands during the LILITH SHRINE loop.
- **Atlas fixes**: case-insensitive atlas lookup; folder-only sprite entries use the atlas; a JSON origin (`origin_from`, `xorig`/`yorig`) wins over uv.json without changing other entries; a missing atlas page no longer shifts later pages; rotated atlas sprites turn around their origin; atlas sprites now work for birth sprites, `carry_base_spr`, naked layers, raid boss icons, cell decoration buttons, the BIRTH infant prop and a carrying ogre after loading.
- **Crash fix**: a hobgoblin delivering from a TRANSFER cell that lost its unit crashed (`skin not set before reading it`). The delivery is now cancelled.

### Bug Fixes

- Clicking a newborn in a cell where it was not the last prop (seen in DRINK cells) crashed with `Variable Index [1] out of range [1]` in `scr_mouse_click`. A vanilla bug: the game deleted props while walking the list forwards.
- Loading a save from an older game version now runs the game's own save upgrade steps again: GNX's copy of them had stopped at 1.33.
- The selector's Goblins row counted every kind of goblin but only took basic ones, so taking many could leave a negative count. It now counts basic goblins; other kinds travel through TROOPS.
- **Load and map-change lag**: loading a save or changing maps with many mods took ~2 s, almost all of it writing the GNX debug log (each line re-opened the log file, ~20 ms a time, and the loader writes ~600 lines on every load and map change). The log is now buffered and written once per frame: the loader goes from ~1.9 s to ~0.1 s with 14 mods, a map change from ~2.3 s to ~0.45 s.
- Load page and "map not available" notice: a map whose mod is off or gone is named after its mod (from the save's mod record) instead of its internal id.
- Removed a debug log line written on every mouse click while the pre-travel selector was open.
- The menus parse each save file once (the load page and the mod page share it) instead of every time a page opens.
- The load page's map label (e.g. "Harness Map" for a save made on a mod map) overlapped the slot title and the day count; it now sits left of the save panel.
- **Vanilla sprite fallback**: a mod with missing or unloadable sprite files no longer crashes the game. A class override takes whatever it leaves out, or fails to load, from the vanilla class it replaces (a new class from the vanilla peasant); a fixed-mode cell entry with nothing usable falls back to the cell's normal sprites; and a sprite that does not exist is skipped when drawn. Each case is logged as a `[GNX-WARN]` naming the mod. Before, loading a save on a map where such a mod applied could crash on the first cell holding a peasant.
- The pre-travel selector's buttons shared an id with the build menu's side toggle, so every +/- click also flipped which side the build menu opens on. Opening the selector from outside the raid map also opened the raid window on Cancel.

All of these were in code that only runs when a map mod loads (map mods are deferred at boot), so they crashed the game the first time a player travelled to a map:

- Fixed crash when a new cell has no `physical` block. The cell is now skipped and reported in the "Mod loading problem(s)" popup, together with the list of missing required fields.
- Fixed crash when a new cell has no `human_spr` block (see above).
- Fixed crash when a new cell has no `category` or `name`. A missing `category` is now reported as a mod error; a missing `name` falls back to the cell's h_type in logs.
- Fixed crash when `by_class`, `by_mon_type` or class_map `classes` sections contain `"_comment"` notes. Non-object entries are now skipped.
- Fixed hobgoblins multiplying and a crash (`scr_draw_hobgoblin_carry`) after loading a save made while transfer cells were mid-transfer. The v1.4.7 load fix restarted every transfer cage, so each cage spawned a second hobgoblin team next to the restored one; when one team delivered the prisoner, the other was left carrying an empty cage. Now a cage whose team survived the load just finishes its transfer; only a cage with no team or half a team is cancelled and restarted.
- Two mods declaring a travel button or `map_start` for the same map no longer produce two buttons with the last-loaded `map_start` silently winning: the first mod in load order owns the map, the other's button and `map_start` are ignored (its content still loads there) and the conflict is reported.
- The "Mod loading problem(s)" popup is shown once per session instead of again on every travel and every return to the menu.
- Removed leftover debug text (green button numbers) drawn over the pre-travel selector's +/- buttons.
- The pre-travel selector no longer opens when travel is impossible (raid out, a blocking window open, something held, travel already under way): it used to take the chosen gold, food and goblins and hide the raid window before the travel was refused. A short notice now says why.
- Fixed gold, food and goblins taken along with the pre-travel selector being lost: they were deducted at departure but never arrived (a travel reset the carried amounts, and they were applied before the destination map loaded, which overwrote them). The day counter now also carries over to a map visited for the first time.
- Loading a save made on a mod map whose mod is no longer installed now puts the player back in their village (the vanilla map stored in the save) instead of stranding them on a map with no way back. The missing map is kept in the save untouched, so reinstalling the mod brings it back as it was. A short in-game notice tells the player why they are back in the village.
- Fixed modded content disappearing when loading a save made on a mod map. The save's map is now restored, and that map's mods loaded, before the load-time sanitizer runs; previously the sanitizer saw the map mod's cells and units as orphans and replaced them. The old menu-time "peek" workaround read the wrong save slot in practice and has been removed.
- Fixed crash on first visit to a map whose `map_start` lists `cells`: the cell data was written to the separator slot instead of the new cell.
- T69 (return entries) now checks the map you are actually on. On the vanilla map it is skipped instead of failing for every map mod, since return buttons only exist while on a modded map.

### Example Mod

- Every cell in `GNX/example_mod` and `docs/example_mod` now has a complete `physical` block (standard, large, tent and XL templates). Previously most cells had none and could not load.
- The example map's travel button moved from x 185 to 210, so its label is no longer cut off by the raid panel's edge.
- `compatible_game_versions` updated to `1.39`. Doc examples in `GNX_MODDING.md` and `TUTORIAL.md` updated to match.
- `GNX_MODDING.md` section 7 now lists the required `physical` fields for new cells.

### Tooling

- **`tools/gnx_test.py`**: automated test harness. Patches `GNX/gml` into a dedicated test copy of the game with the UTMT CLI, boots it, and reports the in-game test suite. A GML compile error, a runtime error, or a mod-loading popup is reported with its full text instead of hanging.
- **Scenarios** (`tools/scenarios/*.json`): scripted in-game tests (save/reload round-trip, multi-map travel, save/load and menu flows, followers staying attached to off-screen cells, off-screen cells keeping running, transfer cells across save/reload, loading a save whose mods were removed, example mod loading). The harness backs up and checks the player's save slots around every run. They use their own save slot and never touch player saves. A small `harness_map` test mod covers multi-map without depending on the example mod.
- Patch files (`GNX/diffs/`, `GNX/gnx.patch`) are now generated per changed `.gml` file only, by `tools/regen_patches.py`. The previous `gnx.patch` also contained unmodified vanilla files, backup copies and a local settings file.

## v1.4.7

**Game version:** 1.39

### New Features

- **`only_listed_cells` class constraint**: classes declaring `"only_listed_cells": true` in `classes.json` can only enter cells whose `required_class` includes them. Enforced across all slot availability checks, carry range checks, and type checks.
- **`clothing_giant` tier**: new clothing sprite set for GIANT cells (h_type 37), alongside the existing `clothing_standard`, `clothing_big`, and `clothing_tent` tiers. Declare `clothing_giant` in `classes.json` with the same phase/sprite structure as the other tiers.
- **Dairy and giant cell sprite overrides**: modded classes can now override sprites on dairy cells (`dairy_blink` key in `mon_spr_overrides`) and giant cells (body, pen, touch, enter, head sprites for goblin, hobgoblin, and ogre). Giant cell clothing is also overridable via `giant_cloth`.
- **Folder sprite loading**: `gnx_resolve_sprite` now supports `"mode": "folder"` to load numbered PNGs from a subdirectory as animation frames, sorted numerically. Also adds `"origin_from"` to copy origin from a vanilla sprite, and `"from_game"` to reference sprites already in data.win.

### Bug Fixes

- Fixed transfer cells not working after loading a save. Carry state (`char_state`, `h_step`) and carry/load flags are now reset on load so the cell re-dispatches transfers from scratch.
- Fixed "only 1 hobgoblin" bug on transfer cells after load. Saved `h_step=1` skipped the load phase that spawns the second hobgoblin.
- Added `instance_exists()` guards on all 5 sites that dereference `carry_start_id` / `carry_end_id` without checking the instance is alive (s_mouse_action, s_slot_function x2, s_mon_remove, s_mon_draw).
- Fixed two vanilla copy-paste bugs in `scr_occupy_slot` case 17: the `carry_end_id` cleanup block wrote to `carry_start_id.slot_data.carry` instead of `carry_end_id`, leaving the end cell's carry flag stuck.
- Added carry/load flag sweep on save load. Clears orphaned flags on cells that no hobgoblin actually references.
- Added `gnx_slot_purge_dead_refs()` to clean dead monster refs from cell placement and unit lists. Runs on cell wake-up from off-screen sleep, unit removal, and monster arrival.
- Fixed `scr_slot_carry_idle` milk class check: any class with `scr_unit == 0` now qualifies, not just hardcoded class 9.
- Relaxed T16 test so classes providing `clothing_giant` instead of `clothing_standard` pass mod class validation.
- Reverted the off-screen culling from v1.4.6 that broke gameplay: buttons, monsters, tents and props now follow their cell every frame again, on or off screen (prisoners no longer disappear or end up on the wrong floor), and step culling is off by default (`gnx_cull_step_off`), so mood, prison and cell logic no longer depend on where the camera is. Draw culling stays, which keeps most of the FPS gain.

## v1.4.6

**Game version:** 1.39

### New Features

- **XL Cell** (slot type 6): 150px wide cell with dedicated background sprites. Build menu adds a 5th option "XL CELL" (500 gold). Clicking an empty XL cell opens the `xl_breed` category list; occupied XL cells open the cell mod window. Background cycles between default, pillar, rock, and brick styles. Mod cells opt in via `"category": "xl_breed"` in `cells.json`.
- **Shrine monster sprite overrides**: goblin, hobgoblin and ogre sprites (body, hand, pen, outlines, touch, enter) on the shrine cell can be replaced per class via `mon_spr_overrides` in `classes.json`. Shrine background, dirt and sign are also replaceable per class (`shrine_bg`, `shrine_dirt`, `shrine_sign`).
- **Chains ogre body override**: the ogre body on the chains cell can be replaced per class (`ogre_chain_body` in `mon_spr_overrides`).
- **Cell patch merging**: multiple mods can now patch the same vanilla cell. `required_class` and `by_class` entries merge instead of being overwritten; the later-loaded mod wins only for classes it explicitly defines. A phase without `spr_array` keeps existing arrays.

### Performance

- Camera Y culling on `obj_slot` Draw and Step events — skips all processing for off-screen slots. On a 74-floor save (4883 slots), only ~100 slots per frame run draw/step logic instead of all 4883.
- Camera Y culling on `obj_mon` Draw and Step events — same treatment for ~880 monster instances.
- Camera Y culling on `obj_button` Draw and Step events — 1625 world-space buttons culled, GUI buttons unaffected.
- Camera Y culling on `obj_empty` Draw and Step events — ~250 empty slot instances culled.
- Camera Y culling on five per-frame `with()` loops in `scr_main_end_step` (button follow, mon follow, tent position, prop position, slot cleanup).
- Throttled ambient speaker scan (`scr_gnx_goblin_visible_speakers`) from every frame to every 15 frames.
- Replaced vanilla zoom-based 4-condition bounds check with fast Y check in slot and mon draw.
- Perf counters moved from individual draw functions to Draw_0 event level for accurate culling stats.
- Net result on a 74-floor endless tower save: **12 FPS → 35-38 FPS** (1080 Ti / i7 / 16GB).

### Bug Fixes

- Fixed crash when loading a save with a goblin mid-drink: `spr_data` is now restored for every `mon_step` value (added `default` case to the restore switch).
- Fixed crash when clicking a quest notification whose event lost its dialog (e.g. after editing `quests.json` between saving and loading). Silent notifications are now skipped during restore, and `scr_gnx_dialog_render` exits cleanly when the event has no `dialog` field.
- Fixed watchdog spamming hundreds of log lines every 60 frames for walking/wandering monsters. Walking monsters (state 5/6) legitimately use `draw_self()` and no longer trigger the repair loop.
- Fixed `instance_exists(-1)` bug in watchdog and monster draw code. In GameMaker, `instance_exists(-1)` returns true (means "all instances"), so slot_id must be checked for -1 before calling `instance_exists()`.
- Fixed crash in tent draw function when `mon_data.h_type` is not set on orphaned tent monsters.
- Fixed monsters walking in place after loading a save. Post-sanitize sweep now snaps walk/wander-state monsters within 10px of their slot to the slot position and sets them to hold state.
- Fixed crash when toggling UI debug unit trace on monsters without `slot_width` in their `spr_data`.
- Shrine touch/enter sprites are no longer drawn for `is_special` classes without their own override (they picked the wrong frame because of `skin = -1`).
- Lilith's vanilla breast overlay on shrine is now drawn only for class 8.
- Fixed false `required_class ref 'N' not found` warning on cell patches. Class numbers are stored as numbers, no longer looked up as names.
- Fixed scrollbar not rendering: `instance_exists(obj_window)` always returned true because the raid window singleton is permanently alive. Removed the window check; scrollbar now shows whenever the nest is taller than the viewport.
- Fixed scrollbar color leak: `scr_gnx_draw_scrollbar` set brown `draw_set_color` without resetting to `c_white`, causing gold amounts, unit names, and other text to render in wrong color.
- Fixed carry/transfer cell regression: watchdog was detaching carry hobgoblins (states 7/8/9) and repairing walking goblins (state 0), breaking carry animations and causing invisible/teleporting goblins.
- Fixed crash in `scr_mon_state_carry_idle` when the lead hobgoblin was destroyed mid-carry (`mon_placement[0]` held a dead instance ref).
- Watchdog hardened: simplified skip logic from fragile state skip-list to `mon_state != 1` (only state 1 goblins need repair/detach). Added `continue` after DETACH to prevent cascade into later checks.
- Watchdog moved from per-frame (every 60 frames) to once-after-load in `scr_patch_update_post` — the only time broken draw states exist is right after save restore.
- Fixed dead watchdog Block 4: was checking `slot_data.unit_data` (never exists) instead of instance-level `unit_data` on `obj_slot`.
- Fixed tool action crash when spawning modded classes: `int64` hash IDs from `gnx_class_name_to_id` caused type mismatch. Now cast to `real()`.
- Tool `spawn_unit` action now accepts string class refs (`"mod_name.ClassName"`) in addition to numeric IDs.
- Fixed `class_name` display in tool/debug UI: resolves numeric class_id to registry name.
- Tool actions on unknown class IDs now show an error popup instead of crashing silently.
- Added `mod_name` field to cell and class registry entries for better debug traceability.
- Fixed `mon_step` save guard: drink-state goblins no longer crash on load when `mon_step` has an unrecognized value.
- Fixed crash on malformed atlas `uv.json`: `json_parse` in `gnx_load_atlas_mod` now wrapped in try/catch with logged error, preventing crash on corrupted mod atlases.
- Fixed potential crash in `scr_unit_removal` for multi-monster cell (h_type 36): `mon_placement` swap now guards each slot access with `!= -1` check before accessing `.mon_data`.
- Fixed `scr_unit_removal` missing `break` after `h_unit_list` placement match — loop continued iterating unnecessarily after finding the target.
- Fixed `scr_set_mon_spr_data` crash when `anim_struct` is uninitialized (-1): now falls back to `frame_c = 0`.
- Added `default: return` to `scr_delete_save` switch to guard against out-of-range save slot index.
- Removed dead `var _spr = spr_idle` assignment in save-load hobgoblin state restore.

## v1.4.5

**Game version:** 1.39

### New Features

- **Multi-monster cells**: cells can hold 2+ goblins. Set `max_mon_num` in the `physical` block, use `mon_placements` to control which species goes in each slot, and `mon_positions` to offset draw positions. Per-slot sprite overrides via `mon_spr_p1`/`mon_spr_p2`/etc.
- Modded classes can now appear as **tower bosses**. Add a `tower_boss_condition` to `classes.json` (state_equals, has_unit, quest_complete, etc.) and the class enters both floor 1 and endless tower encounter pools.
- **Locked cells**: set `"locked": true` in `cells.json` to keep a cell out of the build menu until an `unlock_cell` quest side effect grants it.
- Fixed-mode cells now support `by_class` and `by_mon_type` in phase sprite blocks, overriding the `spr_array`/`spr_c_array` when a specific class or monster type occupies the cell. Nest `by_mon_type` inside `by_class` for class + monster combos.
- `required_class` accepts an array of class refs, so one cell can allow multiple specific classes. Also fixes vanilla special cell class restrictions not recognising modded classes.
- `compatible_game_versions` now uses intersection matching against `gnx_accepted_versions`. Mods targeting `"1.39"` keep working on future 1.39.x patches without manifest updates.

### Bug Fixes

- Fixed invisible goblins on pleasure and tittyfuck cells: the last goblin wasn't drawing. Touched `s_mon_data.gml`, `obj_mon_Draw_0.gml`, and several sprite dispatch/draw files.
- Uninitialized `spr_data` on modded cells was causing fallback to wrong sprites.
- Missing `start_frame` defaults for multi-phase cells. Animation started at frame 0.
- Unit removal on cells with 2+ monsters wasn't cleaning up all slots.

### Documentation

- Modding reference updated: multi-monster cells, tower boss condition (new section 14), locked cells, by_class/by_mon_type overrides, per-placement sprites, required_class arrays.
- Tutorial updated with tower boss, locked cells, and multi-monster cell examples.
- Example mod updated: new DOUBLE PIT multi-monster cell, locked SIREN POOL, tower_boss_condition on SIREN class, by_class/by_mon_type on RITUAL cell.

## v1.4.2

**Game version:** 1.38

### Bug Fixes

- **Atlas packer: wrong frame counts**: the packer looked for `"path"` in classes.json but GNX uses `"strip"`, causing every sprite to fall through to heuristic frame-count inference. Most multi-frame strips got wrong counts, producing misaligned frames, wrong cell types, and skin-tone cycling in atlas mode.
- **Atlas packer: trailing comma tolerance**: classes.json files with trailing commas (valid in JS, not JSON) caused a silent parse failure, compounding the frame-count bug.
- **Atlas packer: missing sprite origins**: the packer did not read `xorig`/`yorig` from classes.json, so all atlas sprites rendered with (0,0) origin instead of their declared offsets (typically bottom-aligned). Origins are now written into uv.json and applied at load time.
- **Atlas runtime: origin fallback**: if an atlas SprRef has no origin but the caller's JSON declares one, the resolver now applies it. Covers atlases packed before the origin fix.

### Tools

- Updated `gnx_atlas_pack.py` with all fixes above. Mods using atlas mode should re-pack with the updated tool.

## v1.4.1

**Game version:** 1.38 (rebased from 1.33)

Everything below is new since the last public release (v1.3.11, game 1.33).

### New Features

- **Rebased to game version 1.38**: full rebase of all 49 patched scripts from vanilla 1.33 to 1.38. All new vanilla content (cells, sprites, UI changes) is preserved. Existing mods only need to update `compatible_game_versions` in their manifest.

- **Standalone Installer**: GNX now ships as a single `.exe` that patches the game directly  - no mod manager, no downloads, no command line. Drop it next to `GoblinNest.exe` and run. Supports install, update-in-place (run a newer exe), restore/uninstall, and drag-and-drop mod `.zip` install. Based on fossil-delta binary patching (inspired by Jadwick's GBF).

- **Multi-Map Travel** (`map`, `map_button`, `map_start` in `manifest.json`): mods can declare a second map  - a fully independent dungeon the player travels to and from via a button on the gameplay screen. Each map has its own floor layout, cells, monsters, raid state, quests, and economy. State is frozen on departure and restored on return. Day counter is shared across all maps. First visit applies configurable starting state (floors, gold, food, mood, goblins). Deferred mod loading ensures map-specific content only loads when needed. Save/load fully supported with map label shown on save-select screen.

- **Custom Decorative Props** (`props.json`): mods can now add custom props to the edit-mode menu with custom sprites, placement offsets, random flip, and per-group positioning (top/mid/bot). Full save/load support with orphan sanitize on mod removal.

- **Custom Birth Sprites** (`birth_spr` in `classes.json`): modded classes can define per-cell-type, per-species infant/birth prop sprites. Supports birth_1, birth_2, bind, tent walls, and giant cells.

- **Unsaved Progress Warning**: "Return to Menu" now shows a confirmation dialog ("Unsaved progress will be lost!") before quitting to the menu.

- **Atlas Packing** (optional performance): texture atlas system (`gnx_atlas_pack.py`) packs sprite strips into large atlas PNGs, cutting texture pages from hundreds to single digits, VRAM by ~45%, and boot time from 94s to 1.8s. Fully backwards-compatible.

### Bug Fixes

- **SprRef/Atlas draw regression** (Bug #7/#9): fixed invisible sprites when 4+ mods loaded in atlas mode. Restored `gnx_draw_sprite_ext` wrappers on all registry-sourced draw calls.
- **Hand position regression** (Bug #10): custom `hand_x`/`hand_y` values now apply correctly.
- **Birth sprite regression** (Bug #17): SprRef-aware infant prop rendering via `scr_draw_prop_infant_gnx`.
- **Debug overlay removed**: disabled `show_debug_overlay(true)` that was causing the GameMaker debug menu bar and FPS counter to appear.

### Documentation

- Full modding reference updated for 1.38 (all JSON schemas, new sections for props, birth sprites, multi-map, atlas packing).
- Fixed `cells.json` schema errors in docs.
- Updated tutorial and example mod compatibility from 1.33 to 1.38.
- Updated README with standalone installer as recommended install path.
