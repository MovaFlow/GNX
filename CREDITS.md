# Credits

## Game

All credit goes to @BadColor for making Goblin Nest.

Go support the developer:
- Steam: https://store.steampowered.com/app/3782910/Goblin_Nest/
- Itch.io: https://badcolor.itch.io/goblin-nest
- Discord (mod support is here): https://discord.gg/7HEAnEmyW2

## Contributors

### @Mav

- Multi-monster cell extensions: per-placement sprite variants, per-placement visual offsets (`mon_positions`), `by_class`/`by_mon_type` sprite dispatch for fixed-mode cells, consolidated `required_class` array support for special vanilla cells, bugfixes for `spr_data` initialization, `start_frame` defaults, and multi-slot unit removal.
- Tower boss support: `tower_boss_condition` for modded classes in endgame tower encounters.
- Locked cells: `"locked": true` to gate cells behind quest rewards.
- XL cells: slot type 6, 150px wide cells with dedicated backgrounds and the `xl_breed` build-menu category.
- Shrine and chains monster sprite overrides: `shrine_bg`, `shrine_dirt`, `shrine_sign`, `ogre_chain_body` per-class keys in `mon_spr_overrides`.
- Cell patch merging: multiple mods patching the same vanilla cell with `required_class`/`by_class` merge logic.
- Dead ref purge: `gnx_slot_purge_dead_refs()` to clean stale monster refs from cell placement and unit lists.
- Milk class generalization: `scr_slot_carry_idle` class check broadened from hardcoded class 9 to any class with `scr_unit == 0`.
- `only_listed_cells` constraint and `clothing_giant` tier for GIANT cell support.
- `gnx_mso_pick()` helper for MSO sprite resolution with vanilla fallback.
- Off-screen culling rework for `obj_slot` Step event with `gnx_cull_sleep` flag.
- Code refactoring: `s_food`, `s_general`, `s_draw_button`, `s_pop_up`, `s_raid_button` split from monolithic files.

### @nevereverever

- Frieren Mod ([link](https://github.com/nevereverever53/GN_Mod_Frieren)). The advanced escape and conditional boss capture mechanics have been generalized for use in GNX.

### @kazull

- Improved `export_class_sprites` and `scaffold_class` scripts, including icon extraction, special class support, and the contributor-submitted codebase extended with GNX feature coverage.

### @Jadwick

- Original Moan Mod ([link](https://jadwick.dev/mods/moan-mod/)). Voices and SFX ported into GNX's sound system.
- [GBF](https://github.com/Jadwick/GBF) (Goblin's Best Friend). Fossil-delta patching architecture inspired the GNX standalone installer.
- Bug reports and fixes that improved GNX stability.

### @Radeonix

- Bug reports and fixes that improved GNX stability.
