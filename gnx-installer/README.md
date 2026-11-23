# GNX installer

Source of `GNX_v<version>.exe`, the installer attached to each GNX release. It is a small Go console
program: it backs up the vanilla `data.win`, applies the GNX patch, restores the backup on uninstall,
installs mod zips dropped on it, and offers newer releases from GitHub.

## What the exe contains

- this Go code, the Go runtime and the modules in `go.mod` (licenses in `THIRD_PARTY_NOTICES.txt`)
- `deltas/gnx_<game version>_<steam|itch>.fossil`: a binary diff (fossil delta) from the vanilla
  `data.win` of each store build to the GNX-patched one, embedded with `go:embed`

No game files and no UndertaleModTool code are in the exe or in the repository.

## Building

Needs Go 1.21 or newer, Python 3, UndertaleModCLI (UTMT) and vanilla `data.win` files of the
supported game version (not in the repository).

1. Bump `GNX_VERSION` (and `GAME_VERSION` on a game update) in `constants.go`.
2. Run, from this folder:

   ```
   python build_installer.py --vanilla-steam <steam data.win> --vanilla-itch <itch data.win> --utmt <UndertaleModCLI.exe>
   ```

   The script patches a copy of each `data.win` with `../GNX/install_foundation.csx` and `../GNX/gml`
   through UTMT, makes the deltas with `cmd/mkdelta`, writes the checksums and delta names into
   `main.go`, builds the exe and checks that each delta turns vanilla into the patched file.
   `goversioninfo`, when installed, adds the Windows version resource (`versioninfo.json`, `GNX.manifest`).

Build outputs (exe, `.win`, `.fossil`, `resource.syso`, `patched_history.json`) are not tracked, so a
plain `go build` in a fresh clone stops at the `go:embed` line until the script has made the deltas.

## License

Same as the rest of GNX: see `LICENSE` at the root of the repository. Ship `THIRD_PARTY_NOTICES.txt`
with the exe.
