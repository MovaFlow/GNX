package main

const DATADIR = "gnx_data"
const MODDIR = "GNX_mods"
const CONFIGFILE = "config.json"

// Bump GNX_VERSION every release before building the installer.
// The update checker compares this against GitHub releases to offer updates.
const GNX_VERSION = "1.5.4"
const GAME_VERSION = "1.40"
const INSTALLER_VERSION = "1.1.0"

type Color int

const (
	Default Color = iota
	Red
	Green
	Purple
)
