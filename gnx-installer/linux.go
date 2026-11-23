//go:build linux

package main

import (
	"os"
	"os/exec"
)

func systemClearscreen() {
	cmd := exec.Command("clear")
	cmd.Stdout = os.Stdout
	cmd.Run()
}
