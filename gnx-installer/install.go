package main

import (
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"path/filepath"

	fdelta "github.com/shadowspore/fossil-delta"
)

func installGNX() {
	clearscreen()
	printFormattedln(Green, false, true, "   Installing GNX "+GNX_VERSION+"   ")

	printFormattedln(Green, false, false, "Checking data.win...")
	hash, err := hashFile(datafile)
	if err != nil {
		showErrorExit("Unable to read data.win.")
	}

	// Vanilla data.win — back it up and patch
	variant, isVanilla := vanillaChecksums[hash]
	if isVanilla {
		printFormattedln(Green, false, false, "Found vanilla Goblin Nest "+GAME_VERSION+" ("+variant+")")
		freshInstall(variant)
		return
	}

	// An older Goblin Nest (vanilla or with an older GNX): this GNX only patches GAME_VERSION
	if oldVer, isOld := olderGameChecksums[hash]; isOld {
		printFormattedln(Red, false, false, "This data.win is "+oldVer+".")
		printFormattedln(Purple, false, false, "GNX "+GNX_VERSION+" needs Goblin Nest "+GAME_VERSION+". Update the game first:")
		printFormattedln(Purple, false, false, "Steam: let Steam update it, or right-click game > Properties > Installed Files > Verify integrity")
		printFormattedln(Purple, false, false, "itch: download and install "+GAME_VERSION)
		printFormattedln(Purple, false, false, "Then run this installer again.")
		waitForEnterKey()
		return
	}

	// Not vanilla — restore from backup first
	printFormattedln(Purple, false, false, "data.win is not vanilla "+GAME_VERSION+".")
	printFormattedln(Purple, false, false, "Restoring from backup before patching...")

	variant, backupPath := findBackup()
	if variant != "" {
		printFormattedln(Green, false, false, "Found vanilla backup: "+variant+".win")
		printFormattedln(Purple, false, false, "Restore backup and install GNX "+GNX_VERSION+"?")
		if !getYesNo(true) {
			printFormattedln(Red, false, false, "Install cancelled.")
			waitForEnterKey()
			return
		}
		restoreAndPatch(variant, backupPath)
		return
	}

	// No backup — tell user to reinstall
	printFormattedln(Red, false, false, "No vanilla backup found in "+DATADIR+"/")
	fmt.Println()
	printFormattedln(Purple, false, false, "GNX needs a clean Goblin Nest "+GAME_VERSION+" data.win to patch from.")
	printFormattedln(Purple, false, false, "Steam: right-click game > Properties > Local Files > Verify integrity")
	printFormattedln(Purple, false, false, "itch: reinstall the game")
	printFormattedln(Purple, false, false, "Then run this installer again.")
	waitForEnterKey()
}

// data.win files from older game versions (vanilla, or patched by an older GNX installer)
var olderGameChecksums = map[string]string{
	"666ca0c093b29a4267a743a81e3588e03a9dca9cfc901d4cd9aaf4f52d0f8110": "Goblin Nest 1.39 (Steam)",
	"adb436bd7303a87d710f043f24e9a8146989e25cb3426664fff8b7b58e2ed9aa": "Goblin Nest 1.39 (itch)",
	"400b3d18863f94155cf88a40f713d1f25de07304cfc185265e349aa5146e23d6": "GNX 1.4.4 on an older Goblin Nest",
	"ebdb2a960ddd6778346e2584ae043e564be5456d4790e8f2eb95e647c980f898": "GNX 1.4.5 on an older Goblin Nest",
	"fbb2cfeb333cdfa35ee262be2105c1665ac42594a253c9747f54fcccc499b0a2": "GNX 1.4.5 on an older Goblin Nest",
	"dbbc61cd3d81e6202097e49cfb6624e16b0147c2b99abf1a24fa80c4f1bdea1d": "GNX 1.4.6 on Goblin Nest 1.39",
	"37f689efe1d9a34d0d6c1751512d7d5478be513e6344f5dc09f9116ee0d7f6d2": "GNX 1.4.6 on Goblin Nest 1.39",
	"60e02062fb94083be0a9b2372643b301625ab5f905b7d4f1e0e234c644c08784": "GNX 1.4.6 on Goblin Nest 1.39",
	"512c1749002f9744472bc7dab9d1bef79f6266d2daac4c8f2a6f8ee097702713": "GNX 1.4.6 on Goblin Nest 1.39",
	"59af03a951f1da00049d9575d16984db71cdd25c16136c6c1df889ece55a71a8": "GNX 1.4.7 on Goblin Nest 1.39",
	"55c2c11d9faa4669bee77c118a5f4f430cf7bf30f055a7e57722081cc65d2c79": "GNX 1.4.7 on Goblin Nest 1.39",
}

func freshInstall(variant string) {
	backupPath := filepath.Join(relDataDir, variant+".win")

	printFormattedln(Green, false, false, "Backing up data.win...")
	if err := copyFile(datafile, backupPath); err != nil {
		showErrorExit("Failed to back up data.win: " + err.Error())
	}
	printFormattedln(Green, false, false, "Backup saved to "+DATADIR+"/"+variant+".win")

	applyDelta(variant, datafile)
}

func restoreAndPatch(variant string, backupPath string) {
	printFormattedln(Green, false, false, "Restoring vanilla data.win from backup...")
	if err := copyFile(backupPath, datafile); err != nil {
		showErrorExit("Failed to restore backup: " + err.Error())
	}

	// Verify restored file
	hash, err := hashFile(datafile)
	if err != nil {
		showErrorExit("Failed to verify restored data.win: " + err.Error())
	}
	if _, ok := vanillaChecksums[hash]; !ok {
		showErrorExit("Restored data.win does not match any known vanilla hash. Backup may be corrupted.")
	}

	applyDelta(variant, datafile)
}

func applyDelta(variant string, sourcePath string) {
	deltaPath, ok := deltaFiles[variant]
	if !ok {
		showErrorExit("No delta file for variant: " + variant)
	}

	printFormattedln(Green, false, false, "Loading embedded patch...")
	patchData, err := embeddedDeltas.ReadFile(deltaPath)
	if err != nil {
		showErrorExit("Failed to read embedded delta: " + err.Error())
	}

	printFormattedln(Green, false, false, "Reading data.win...")
	srcData, err := os.ReadFile(sourcePath)
	if err != nil {
		showErrorExit("Failed to read data.win: " + err.Error())
	}

	printFormattedln(Green, false, false, "Applying patch...")
	result, err := fdelta.Apply(srcData, patchData)
	if err != nil {
		showErrorExit("Failed to apply patch: " + err.Error())
	}

	if err := os.WriteFile(datafile, result, 0644); err != nil {
		showErrorExit("Failed to write patched data.win: " + err.Error())
	}

	ensureModDir()

	printFormattedln(Green, false, true, "   GNX "+GNX_VERSION+" installed successfully!   ")
	printFormattedln(Purple, false, false, "Drop mod .zip files onto this exe to install them.")
	waitForEnterKey()
}

func ensureModDir() {
	b, _ := exists(relModDir)
	if b {
		return
	}
	os.Mkdir(relModDir, 0755)
}


func findBackup() (string, string) {
	entries, err := os.ReadDir(relDataDir)
	if err != nil {
		return "", ""
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
			return variant, fp
		}
	}
	return "", ""
}

func hashFile(path string) (string, error) {
	file, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer file.Close()
	h := sha256.New()
	if _, err = io.Copy(h, file); err != nil {
		return "", err
	}
	return fmt.Sprintf("%x", h.Sum(nil)), nil
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}
