//go:build windows

package main

import (
	"os"
	"os/exec"
)

func systemClearscreen() {
	cmd := exec.Command("cmd", "/c", "cls")
	cmd.Stdout = os.Stdout
	cmd.Run()
}
