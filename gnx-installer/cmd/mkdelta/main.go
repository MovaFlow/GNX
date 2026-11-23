package main

import (
	"fmt"
	"os"

	fdelta "github.com/shadowspore/fossil-delta"
)

func main() {
	if len(os.Args) != 4 {
		fmt.Fprintf(os.Stderr, "Usage: mkdelta <source.win> <target.win> <output.fossil>\n")
		os.Exit(1)
	}

	src, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading source: %v\n", err)
		os.Exit(1)
	}

	tgt, err := os.ReadFile(os.Args[2])
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading target: %v\n", err)
		os.Exit(1)
	}

	delta := fdelta.Create(src, tgt)

	if err := os.WriteFile(os.Args[3], delta, 0644); err != nil {
		fmt.Fprintf(os.Stderr, "Error writing delta: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Delta: %s (%d bytes) + %s (%d bytes) -> %s (%d bytes)\n",
		os.Args[1], len(src), os.Args[2], len(tgt), os.Args[3], len(delta))
}
