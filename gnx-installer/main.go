package main

import (
	"embed"
	"os"
	"path/filepath"
)

//go:embed deltas/*.fossil
var embeddedDeltas embed.FS

// STAMP:vanilla_checksums
var vanillaChecksums = map[string]string {
	"64c7c0fb9cb81776fd6f44f1209d12f5e668700c5dc19135f1cc33d63cafc681": "steam",
	"c3178b94cd3af8ab9fc5ec842245b9441c41de1da15f7a6029d4876292ba4637": "itch",
}

// STAMP:delta_files
var deltaFiles = map[string]string {
	"steam": "deltas/gnx_1.40_steam.fossil",
	"itch": "deltas/gnx_1.40_itch.fossil",
}

var config = map[string]string{
	"usecolor": "false",
}

var relExeDir string
var relDataDir string
var relModDir string
var datafile string

func main() {
	exe, err := os.Executable()
	if err != nil {
		showErrorExit(err.Error())
	}
	relExeDir = filepath.Dir(exe)
	os.Remove(exe + ".old") // clean up after self-update
	relDataDir = filepath.Join(relExeDir, DATADIR)
	relModDir = filepath.Join(relExeDir, MODDIR)
	datafile = filepath.Join(relExeDir, "data.win")

	if len(os.Args) > 1 {
		installMod(os.Args[1])
	}

	startUpdateCheck()
	initialize()
	home()
}
