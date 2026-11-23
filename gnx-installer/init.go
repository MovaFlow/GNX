package main

import (
	"fmt"
	"os"
)

func initialize() {
	clearscreen()
	printFormattedln(Green, false, true, "   GNX Installer v"+INSTALLER_VERSION+"   ")
	printFormattedln(Green, false, false, "GNX "+GNX_VERSION+" for Goblin Nest "+GAME_VERSION)
	fmt.Println()

	b, err := exists(datafile)
	if b {
		printFormattedln(Green, false, false, "data.win located")
	} else if !b && err == nil {
		showErrorExit("data.win not found. Place this exe in the same folder as GoblinNest.exe.")
	} else {
		showErrorExit("Permission error reading data.win.")
	}

	b, err = exists(relDataDir)
	if b {
		printFormattedln(Green, false, false, "Data directory located")
	} else if !b && err == nil {
		printFormattedln(Green, false, false, "Creating data directory...")
		if err := os.Mkdir(relDataDir, 0755); err != nil && !os.IsExist(err) {
			showErrorExit("Failed to create data directory.")
		}
	} else {
		showErrorExit("Permission error.")
	}

	ex, _ := exists(relDataDir + "/" + CONFIGFILE)
	if !ex {
		initialSetup()
	}
	loadConfig()

	printFormattedln(Green, false, true, "   Ready   ")
}

func initialSetup() {
	os.MkdirAll(relDataDir, 0755)
	config["usecolor"] = "true"
	printFormattedln(Green, false, true, " First launch setup ")
	printFormattedln(Purple, false, false, "Is the line above green, or do you only see weird numbers?")
	options := []string{
		"I can see the different colors.",
		"I can only see numbers.",
	}
	choice := getOption(options)
	switch choice {
	case 0:
		config["usecolor"] = "true"
	case 1:
		config["usecolor"] = "false"
	}
	createConfig()
}
