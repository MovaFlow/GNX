package main

import (
	"os"
	"path/filepath"
)

func restoreBackup() {
	clearscreen()
	printFormattedln(Green, false, true, "   Restore Backup   ")
	printFormattedln(Green, false, false, "Scanning for backups...")

	type backup struct {
		variant string
		path    string
	}
	var backups []backup

	entries, err := os.ReadDir(relDataDir)
	if err != nil {
		showErrorExit("Cannot read " + DATADIR + " directory.")
	}
	for _, e := range entries {
		if e.IsDir() || filepath.Ext(e.Name()) != ".win" {
			continue
		}
		fp := filepath.Join(relDataDir, e.Name())
		hash, err := hashFile(fp)
		if err != nil {
			continue
		}
		if variant, ok := vanillaChecksums[hash]; ok {
			backups = append(backups, backup{variant, fp})
		}
	}

	if len(backups) == 0 {
		printFormattedln(Red, false, false, "No valid backups found.")
		waitForEnterKey()
		return
	}

	var chosen backup
	if len(backups) == 1 {
		chosen = backups[0]
		printFormattedln(Green, false, false, "Found backup: "+chosen.variant)
	} else {
		options := make([]string, len(backups))
		for i, b := range backups {
			options[i] = b.variant
		}
		printFormattedln(Purple, false, false, "Multiple backups found. Which to restore?")
		idx := getOption(options)
		chosen = backups[idx]
	}

	printFormattedln(Purple, false, false, "Restore vanilla "+chosen.variant+"? This will remove GNX.")
	if !getYesNo(false) {
		printFormattedln(Red, false, false, "Restore cancelled.")
		waitForEnterKey()
		return
	}

	printFormattedln(Green, false, false, "Restoring...")
	if err := copyFile(chosen.path, datafile); err != nil {
		showErrorExit("Failed to restore: " + err.Error())
	}

	printFormattedln(Green, false, true, "   Vanilla "+chosen.variant+" restored successfully   ")
	printFormattedln(Purple, false, false, "GNX has been uninstalled. Your mods in GNX_mods/ are untouched.")
	waitForEnterKey()
}
