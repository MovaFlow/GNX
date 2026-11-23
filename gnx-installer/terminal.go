package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

var stdinReader = bufio.NewReader(os.Stdin)

func clearscreen() {
	systemClearscreen()
}

func waitForEnterKey() {
	fmt.Println("\nPress Enter to continue...")
	stdinReader.ReadString('\n')
}

func showErrorExit(msg string) {
	printFormattedln(Red, false, true, " ERROR ")
	printFormattedln(Red, false, false, msg)
	waitForEnterKey()
	os.Exit(1)
}

func printFormattedln(color Color, bold bool, highlight bool, text string) {
	if config["usecolor"] == "true" {
		var code string
		switch color {
		case Red:
			code = "31"
		case Green:
			code = "32"
		case Purple:
			code = "35"
		default:
			code = "0"
		}
		if bold {
			code = "1;" + code
		}
		if highlight {
			fmt.Printf("\033[%sm\033[7m %s \033[0m\n", code, text)
		} else {
			fmt.Printf("\033[%sm%s\033[0m\n", code, text)
		}
	} else {
		if highlight {
			fmt.Printf("[ %s ]\n", text)
		} else {
			fmt.Println(text)
		}
	}
}

func getOption(options []string) int {
	for {
		for i, opt := range options {
			printFormattedln(Purple, false, false, fmt.Sprintf("  %d. %s", i+1, opt))
		}
		fmt.Print("\nChoice: ")
		input, _ := stdinReader.ReadString('\n')
		input = strings.TrimSpace(input)
		if input == "" {
			return 0
		}
		num, err := strconv.Atoi(input)
		if err == nil && num >= 1 && num <= len(options) {
			return num - 1
		}
		printFormattedln(Red, false, false, "Invalid choice.")
	}
}

func getString(prompt string) string {
	fmt.Print(prompt)
	input, _ := stdinReader.ReadString('\n')
	return strings.TrimSpace(input)
}

func getYesNo(defaultYes bool) bool {
	prompt := "(y/N): "
	if defaultYes {
		prompt = "(Y/n): "
	}
	fmt.Print(prompt)
	input, _ := stdinReader.ReadString('\n')
	input = strings.TrimSpace(strings.ToLower(input))
	if input == "" {
		return defaultYes
	}
	return input == "y" || input == "yes"
}
