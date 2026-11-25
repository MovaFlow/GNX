package main

import (
	"os"
	"path/filepath"
	"testing"
	"testing/fstest"
)

func bundleOf(version string) fstest.MapFS {
	return fstest.MapFS{
		"bundle/.gitkeep":               {Data: nil},
		"bundle/00_mod/manifest.json":   {Data: []byte(`{"mod_id": "m", "version": "` + version + `"}`)},
		"bundle/00_mod/atlas/a.png":     {Data: []byte("png " + version)},
		"bundle/broken/manifest.json":   {Data: []byte(`{`)},
		"bundle/no_manifest/readme.txt": {Data: []byte("x")},
	}
}

func setup(t *testing.T) {
	dir := t.TempDir()
	relDataDir, relModDir = filepath.Join(dir, DATADIR), filepath.Join(dir, MODDIR)
	os.Mkdir(relDataDir, 0755)
	os.Mkdir(relModDir, 0755)
}

func installedVersion(folder string) string {
	_, v := readExistingManifest(filepath.Join(relModDir, folder))
	return v
}

func want(t *testing.T, what string, got, want any) {
	t.Helper()
	if got != want {
		t.Errorf("%s: got %v, want %v", what, got, want)
	}
}

func folders() int {
	e, _ := os.ReadDir(relModDir)
	return len(e)
}

func TestBundleInstallUpdateUninstall(t *testing.T) {
	setup(t)
	installBundled(bundleOf("0.2.3"))
	want(t, "written", installedVersion("00_mod"), "0.2.3")
	want(t, "only the readable mod", folders(), 1)
	os.WriteFile(filepath.Join(relModDir, "00_mod", "old.txt"), nil, 0644)
	installBundled(bundleOf("0.2.3"))
	left, _ := exists(filepath.Join(relModDir, "00_mod", "old.txt"))
	want(t, "same version: left alone", left, true)
	installBundled(bundleOf("0.2.10"))
	want(t, "newer: replaced", installedVersion("00_mod"), "0.2.10")
	left, _ = exists(filepath.Join(relModDir, "00_mod", "old.txt"))
	want(t, "newer: no leftovers", left, false)
	installBundled(bundleOf("0.2.3"))
	want(t, "older: not downgraded", installedVersion("00_mod"), "0.2.10")
	data, _ := os.ReadDir(relDataDir)
	want(t, "no temporary folders", len(data), 1)
	os.Mkdir(filepath.Join(relModDir, "player_mod"), 0755)
	removeBundled()
	want(t, "uninstall leaves the player's mods", folders(), 1)
	installBundled(bundleOf("0.2.3"))
	want(t, "back after a reinstall", installedVersion("00_mod"), "0.2.3")
}

func TestBundleDeletedByPlayer(t *testing.T) {
	setup(t)
	installBundled(bundleOf("0.2.3"))
	os.RemoveAll(filepath.Join(relModDir, "00_mod"))
	installBundled(bundleOf("0.3.0"))
	removeBundled()
	installBundled(bundleOf("0.3.0"))
	want(t, "stays deleted", folders(), 0)
}

func TestBundlePlayersOwnCopy(t *testing.T) {
	setup(t)
	own := filepath.Join(relModDir, "own")
	os.Mkdir(own, 0755)
	os.WriteFile(filepath.Join(own, "manifest.json"), []byte(`{"mod_id": "m", "version": "0.1"}`), 0644)
	installBundled(bundleOf("0.2.3"))
	want(t, "updated in its own folder", installedVersion("own"), "0.2.3")
	want(t, "no second copy", folders(), 1)
	removeBundled()
	want(t, "not removed: the player put it there", folders(), 1)
}

func TestBundleFolderTaken(t *testing.T) {
	setup(t)
	other := filepath.Join(relModDir, "00_mod")
	os.Mkdir(other, 0755)
	os.WriteFile(filepath.Join(other, "manifest.json"), []byte(`{"mod_id": "other", "version": "1"}`), 0644)
	installBundled(bundleOf("0.2.3"))
	want(t, "another mod's folder", installedVersion("00_mod"), "1")
}

func TestBundleBadRecord(t *testing.T) {
	setup(t)
	os.WriteFile(filepath.Join(relDataDir, BUNDLEFILE), []byte(`null`), 0644)
	installBundled(bundleOf("0.2.3"))
	want(t, "written", installedVersion("00_mod"), "0.2.3")
	os.WriteFile(filepath.Join(relDataDir, BUNDLEFILE), []byte(`{"m": "..", "x": ""}`), 0644)
	removeBundled()
	want(t, "nothing outside GNX_mods is removed", folders(), 1)
}
