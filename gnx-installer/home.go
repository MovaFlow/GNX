package main

import (
	"fmt"
	"os"
)

func home() {
	// Wait for update check on first run
	printFormattedln(Green, false, false, "Checking for updates...")
	<-updateDone

	for {
		clearscreen()
		printFormattedln(Green, false, true, "   GNX Installer   ")
		printFormattedln(Green, false, false, "GNX "+GNX_VERSION+" | Goblin Nest "+GAME_VERSION)

		newVer, _ := getUpdate()
		hasUpdate := newVer != ""
		if hasUpdate {
			fmt.Println()
			printFormattedln(Purple, false, true, " Update available: "+newVer+" ")
		}

		fmt.Println()
		printFormattedln(Purple, false, false, "What would you like to do?")
		options := []string{
			"Install / Update GNX",
			"Restore Backup (Uninstall GNX)",
		}
		if hasUpdate {
			options = append(options, "Update Installer to "+newVer)
		}
		options = append(options, "Quit")
		choice := getOption(options)

		quitIdx := len(options) - 1
		updateIdx := -1
		if hasUpdate {
			updateIdx = quitIdx - 1
		}

		switch {
		case choice == 0:
			installGNX()
		case choice == 1:
			restoreBackup()
		case hasUpdate && choice == updateIdx:
			selfUpdate()
		case choice == quitIdx:
			os.Exit(0)
		}
	}
}
