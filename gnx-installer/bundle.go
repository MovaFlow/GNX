package main

import (
	"embed"
	"encoding/json"
	"io/fs"
	"os"
	"path"
	"path/filepath"

	"github.com/google/uuid"
	"github.com/otiai10/copy"
)

// Mods that come with the installer: each folder in bundle/ (empty in the repository, see build_installer.py --bundle).
//
//go:embed all:bundle
var bundledMods embed.FS

// BUNDLEFILE (in gnx_data) lists the bundled mods this installer wrote: mod_id -> folder in GNX_mods. An entry whose
// mod is gone was deleted by the player: it is not written again.
const BUNDLEFILE = "bundle.json"

func readBundleRecord() map[string]string {
	rec := map[string]string{}
	if data, err := os.ReadFile(filepath.Join(relDataDir, BUNDLEFILE)); err == nil {
		json.Unmarshal(data, &rec)
	}
	if rec == nil { // the file holds "null"
		rec = map[string]string{}
	}
	return rec
}

func writeBundleRecord(rec map[string]string) {
	if data, err := json.Marshal(rec); err == nil {
		os.WriteFile(filepath.Join(relDataDir, BUNDLEFILE), data, 0644)
	}
}

// installBundled writes the mods of src (bundle/<folder>/...) to GNX_mods: new ones, and newer versions of installed ones.
// A mod that cannot be written is left out: it must not fail the GNX install.
func installBundled(src fs.FS) {
	entries, err := fs.ReadDir(src, "bundle")
	if err != nil {
		return
	}
	rec := readBundleRecord()
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		root := path.Join("bundle", e.Name())
		var manifest struct {
			ModID   string `json:"mod_id"`
			Version string `json:"version"`
		}
		data, err := fs.ReadFile(src, path.Join(root, "manifest.json"))
		if err != nil || json.Unmarshal(data, &manifest) != nil || manifest.ModID == "" {
			continue
		}

		_, known := rec[manifest.ModID]
		folder := findInstalledMod(manifest.ModID)
		ours := known || folder == ""
		if folder == "" {
			folder = e.Name()
			taken, _ := exists(filepath.Join(relModDir, folder))
			if known || taken { // deleted by the player, or another mod's folder
				continue
			}
		} else if _, v := readExistingManifest(filepath.Join(relModDir, folder)); !isNewer(manifest.Version, v) {
			continue
		}

		// whole first, then in place: a failed write leaves the installed copy alone
		tmp := filepath.Join(relDataDir, uuid.New().String())
		dest := filepath.Join(relModDir, folder)
		if err := writeTree(src, root, tmp); err == nil && os.RemoveAll(dest) == nil && copy.Copy(tmp, dest) == nil && ours {
			rec[manifest.ModID] = folder
		}
		os.RemoveAll(tmp)
	}
	if len(rec) > 0 {
		writeBundleRecord(rec)
	}
}

func writeTree(src fs.FS, root, dest string) error {
	return fs.WalkDir(src, root, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		out := filepath.Join(dest, filepath.FromSlash(p[len(root):]))
		if d.IsDir() {
			return os.MkdirAll(out, 0755)
		}
		data, err := fs.ReadFile(src, p)
		if err != nil {
			return err
		}
		return os.WriteFile(out, data, 0644)
	})
}

// removeBundled takes the mods this installer wrote out of GNX_mods (uninstall).
func removeBundled() {
	rec := readBundleRecord()
	for id, folder := range rec {
		if folder != "" && findInstalledMod(id) == folder && os.RemoveAll(filepath.Join(relModDir, folder)) == nil {
			delete(rec, id)
		}
	}
	if len(rec) > 0 {
		writeBundleRecord(rec)
	} else {
		os.Remove(filepath.Join(relDataDir, BUNDLEFILE))
	}
}
