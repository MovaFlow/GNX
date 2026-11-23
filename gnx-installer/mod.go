package main

import (
	"encoding/json"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	"github.com/google/uuid"
	"github.com/otiai10/copy"
)

func installMod(path string) {
	loadConfigSilent()

	if !strings.HasSuffix(strings.ToLower(path), ".zip") {
		showErrorExit("Only .zip files are supported.")
	}

	b, _ := exists(datafile)
	if !b {
		showErrorExit("data.win not found.")
	}
	b, _ = exists(relModDir)
	if !b {
		showErrorExit("GNX_mods directory not found. Is GNX installed?")
	}

	printFormattedln(Green, false, false, "Installing mod from:")
	printFormattedln(Green, false, false, path)

	tempdir := filepath.Join(relDataDir, uuid.New().String())
	os.MkdirAll(tempdir, 0755)

	if err := unzip(path, tempdir); err != nil {
		os.RemoveAll(tempdir)
		showErrorExit("Failed to unzip: " + err.Error())
	}

	var manifestRoot string
	var modName, modID, modVersion string
	var found bool

	filepath.WalkDir(tempdir, func(p string, d fs.DirEntry, err error) error {
		if err != nil || found {
			return filepath.SkipAll
		}
		if !strings.EqualFold(filepath.Base(p), "manifest.json") {
			return nil
		}
		printFormattedln(Green, false, false, "Manifest found!")
		manifestRoot = filepath.Dir(p)

		file, err := os.Open(p)
		if err != nil {
			printFormattedln(Red, false, false, "Failed to read manifest.")
			return filepath.SkipAll
		}
		defer file.Close()

		var jsonMap map[string]interface{}
		if err := json.NewDecoder(file).Decode(&jsonMap); err != nil {
			printFormattedln(Red, false, false, "Failed to parse manifest JSON.")
			return filepath.SkipAll
		}

		if v, ok := jsonMap["mod_id"].(string); ok {
			modID = v
		}
		if v, ok := jsonMap["name"].(string); ok {
			modName = v
		}
		if v, ok := jsonMap["version"].(string); ok {
			modVersion = v
		}
		if modID == "" {
			modID = modName
		}
		if modName == "" {
			return filepath.SkipAll
		}
		found = true
		return filepath.SkipAll
	})

	if !found {
		os.RemoveAll(tempdir)
		showErrorExit("No readable manifest.json found. Is this a GNX mod?")
	}

	// The mod's folder is part of its class/cell IDs and of "folder.NAME" references, so it must match a
	// manual extract: the zip's own folder. An installed copy of the same mod keeps its folder (saves use those IDs).
	modFolder := modID
	if manifestRoot != tempdir {
		modFolder = filepath.Base(manifestRoot)
	}
	if installed := findInstalledMod(modID); installed != "" {
		modFolder = installed
	}
	modPath := filepath.Join(relModDir, modFolder)

	b, _ = exists(modPath)
	if b {
		oldName, oldVersion := readExistingManifest(modPath)
		printFormattedln(Red, false, true, " Mod already installed ")
		printFormattedln(Red, false, false, "Old: "+oldName+" v"+oldVersion)
		printFormattedln(Green, false, false, "New: "+modName+" v"+modVersion)
		printFormattedln(Purple, false, false, "Overwrite?")
		if !getYesNo(false) {
			os.RemoveAll(tempdir)
			showErrorExit("Mod install cancelled.")
		}
		os.RemoveAll(modPath)
	}

	printFormattedln(Green, false, false, "Copying mod files...")
	if err := copy.Copy(manifestRoot, modPath); err != nil {
		os.RemoveAll(tempdir)
		showErrorExit("Failed to copy mod: " + err.Error())
	}
	os.RemoveAll(tempdir)

	printFormattedln(Green, false, true, "   "+modName+" v"+modVersion+" installed!   ")
	waitForEnterKey()
	os.Exit(0)
}

// findInstalledMod returns the folder in GNX_mods holding the mod with this mod_id (or name, for a manifest without one).
func findInstalledMod(modID string) string {
	entries, err := os.ReadDir(relModDir)
	if err != nil {
		return ""
	}
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		file, err := os.Open(filepath.Join(relModDir, e.Name(), "manifest.json"))
		if err != nil {
			continue
		}
		var jsonMap map[string]interface{}
		err = json.NewDecoder(file).Decode(&jsonMap)
		file.Close()
		if err != nil {
			continue
		}
		id, _ := jsonMap["mod_id"].(string)
		if id == "" {
			id, _ = jsonMap["name"].(string)
		}
		if strings.EqualFold(id, modID) {
			return e.Name()
		}
	}
	return ""
}

func readExistingManifest(modPath string) (string, string) {
	file, err := os.Open(filepath.Join(modPath, "manifest.json"))
	if err != nil {
		return "Unknown", "?"
	}
	defer file.Close()
	var jsonMap map[string]interface{}
	if err := json.NewDecoder(file).Decode(&jsonMap); err != nil {
		return "Unknown", "?"
	}
	name := "Unknown"
	version := "?"
	if v, ok := jsonMap["name"].(string); ok {
		name = v
	}
	if v, ok := jsonMap["version"].(string); ok {
		version = v
	}
	return name, version
}
