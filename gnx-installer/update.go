package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
)

const releasesAPI = "https://api.github.com/repos/MovaFlow/GNX/releases?per_page=10"

var (
	updateVersion string // empty = no update
	updateURL     string // asset download URL
	updateMu      sync.Mutex
	updateDone    chan struct{}
)

func startUpdateCheck() {
	updateDone = make(chan struct{})
	go func() {
		defer close(updateDone)
		ver, url := fetchLatestRelease()
		if ver == "" {
			return
		}
		if !isNewer(ver, GNX_VERSION) {
			return
		}
		updateMu.Lock()
		updateVersion = ver
		updateURL = url
		updateMu.Unlock()
	}()
}

func getUpdate() (version, url string) {
	select {
	case <-updateDone:
	default:
		// not done yet, don't block
		return "", ""
	}
	updateMu.Lock()
	defer updateMu.Unlock()
	return updateVersion, updateURL
}

func fetchLatestRelease() (version, assetURL string) {
	resp, err := http.Get(releasesAPI)
	if err != nil {
		return "", ""
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return "", ""
	}

	var releases []struct {
		TagName    string `json:"tag_name"`
		Draft      bool   `json:"draft"`
		Prerelease bool   `json:"prerelease"`
		Assets     []struct {
			Name               string `json:"name"`
			BrowserDownloadURL string `json:"browser_download_url"`
		} `json:"assets"`
	}
	if json.NewDecoder(resp.Body).Decode(&releases) != nil {
		return "", ""
	}

	var bestVer string
	var bestURL string
	for _, rel := range releases {
		if rel.Draft || rel.Prerelease {
			continue
		}
		tag := strings.TrimPrefix(rel.TagName, "v")
		if tag == "" {
			continue
		}
		if bestVer == "" || isNewer(tag, bestVer) {
			for _, a := range rel.Assets {
				if strings.HasSuffix(strings.ToLower(a.Name), ".exe") && strings.HasPrefix(strings.ToLower(a.Name), "gnx_v") {
					bestVer = tag
					bestURL = a.BrowserDownloadURL
					break
				}
			}
		}
	}
	return bestVer, bestURL
}

func isNewer(remote, local string) bool {
	rp := splitVersion(remote)
	lp := splitVersion(local)
	for i := 0; i < len(rp) || i < len(lp); i++ {
		r, l := 0, 0
		if i < len(rp) {
			r = rp[i]
		}
		if i < len(lp) {
			l = lp[i]
		}
		if r > l {
			return true
		}
		if r < l {
			return false
		}
	}
	return false
}

func splitVersion(v string) []int {
	parts := strings.Split(v, ".")
	nums := make([]int, len(parts))
	for i, p := range parts {
		nums[i], _ = strconv.Atoi(p)
	}
	return nums
}

func selfUpdate() {
	_, url := getUpdate()
	if url == "" {
		printFormattedln(Red, false, false, "No update URL available.")
		waitForEnterKey()
		return
	}

	clearscreen()
	printFormattedln(Green, false, true, "   Updating GNX Installer   ")
	printFormattedln(Green, false, false, "Downloading "+updateVersion+"...")

	resp, err := http.Get(url)
	if err != nil {
		printFormattedln(Red, false, false, "Download failed: "+err.Error())
		waitForEnterKey()
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		printFormattedln(Red, false, false, fmt.Sprintf("Download failed: HTTP %d", resp.StatusCode))
		waitForEnterKey()
		return
	}

	exe, err := os.Executable()
	if err != nil {
		printFormattedln(Red, false, false, "Cannot locate self: "+err.Error())
		waitForEnterKey()
		return
	}
	exeDir := filepath.Dir(exe)

	// Use the asset's filename so the exe gets the correct name
	assetName := filepath.Base(url)
	targetExe := filepath.Join(exeDir, assetName)

	tmpFile := targetExe + ".new"
	out, err := os.Create(tmpFile)
	if err != nil {
		printFormattedln(Red, false, false, "Cannot write update: "+err.Error())
		waitForEnterKey()
		return
	}
	_, err = io.Copy(out, resp.Body)
	out.Close()
	if err != nil {
		os.Remove(tmpFile)
		printFormattedln(Red, false, false, "Download incomplete: "+err.Error())
		waitForEnterKey()
		return
	}

	// Rename old exe so Windows lets go of the lock
	oldExe := exe + ".old"
	os.Remove(oldExe)
	if err := os.Rename(exe, oldExe); err != nil {
		os.Remove(tmpFile)
		printFormattedln(Red, false, false, "Cannot replace exe: "+err.Error())
		waitForEnterKey()
		return
	}
	if err := os.Rename(tmpFile, targetExe); err != nil {
		os.Rename(oldExe, exe)
		printFormattedln(Red, false, false, "Cannot replace exe: "+err.Error())
		waitForEnterKey()
		return
	}

	printFormattedln(Green, false, true, "   Updated to "+updateVersion+"!   ")
	printFormattedln(Purple, false, false, "Please re-run the installer.")
	waitForEnterKey()
	os.Exit(0)
}
