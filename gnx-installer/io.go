package main

import (
	"archive/zip"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

func exists(path string) (bool, error) {
	_, err := os.Stat(path)
	if err == nil {
		return true, nil
	}
	if errors.Is(err, fs.ErrNotExist) {
		return false, nil
	}
	return false, err
}

func unzip(src, dest string) error {
	r, err := zip.OpenReader(src)
	if err != nil {
		return err
	}
	defer r.Close()
	os.MkdirAll(dest, 0755)

	for _, f := range r.File {
		path := filepath.Join(dest, f.Name)
		if !strings.HasPrefix(path, filepath.Clean(dest)+string(os.PathSeparator)) {
			return fmt.Errorf("illegal file path: %s", path)
		}
		if f.FileInfo().IsDir() {
			os.MkdirAll(path, f.Mode())
			continue
		}
		os.MkdirAll(filepath.Dir(path), f.Mode())
		outFile, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
		if err != nil {
			return err
		}
		rc, err := f.Open()
		if err != nil {
			outFile.Close()
			return err
		}
		_, err = io.Copy(outFile, rc)
		rc.Close()
		outFile.Close()
		if err != nil {
			return err
		}
	}
	return nil
}

func loadConfig() {
	fp := filepath.Join(relDataDir, CONFIGFILE)
	fileExists, err := exists(fp)
	if err != nil || !fileExists {
		initialSetup()
		return
	}
	file, err := os.Open(fp)
	if err != nil {
		return
	}
	defer file.Close()
	var jsonMap map[string]interface{}
	if err := json.NewDecoder(file).Decode(&jsonMap); err != nil {
		return
	}
	if val, ok := jsonMap["usecolor"]; ok {
		config["usecolor"] = strings.ToLower(val.(string))
	}
}

func loadConfigSilent() {
	fp := filepath.Join(relDataDir, CONFIGFILE)
	fileExists, _ := exists(fp)
	if !fileExists {
		return
	}
	file, err := os.Open(fp)
	if err != nil {
		return
	}
	defer file.Close()
	var jsonMap map[string]interface{}
	if err := json.NewDecoder(file).Decode(&jsonMap); err != nil {
		return
	}
	if val, ok := jsonMap["usecolor"]; ok {
		config["usecolor"] = strings.ToLower(val.(string))
	}
}

func createConfig() {
	fp := filepath.Join(relDataDir, CONFIGFILE)
	file, err := os.Create(fp)
	if err != nil {
		printFormattedln(Red, false, false, "Failed to create config file.")
		return
	}
	defer file.Close()
	data, err := json.Marshal(config)
	if err != nil {
		os.Remove(fp)
		return
	}
	file.Write(data)
}
