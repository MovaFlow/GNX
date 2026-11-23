#!/usr/bin/env python3
"""
GNX Installer Build Companion

Automates: vanilla data.win -> patched data.win -> fossil delta -> embedded Go binary

Before building: bump GNX_VERSION in constants.go to match the release tag.
The installer's update checker uses this to detect newer versions on GitHub.

Usage:
  # Both variants:
  python build_installer.py --vanilla-steam steam.win --vanilla-itch itch.win

  # Single variant with pre-patched:
  python build_installer.py --vanilla-steam vanilla.win --patched-steam patched.win

Options:
  --vanilla-steam PATH    Vanilla data.win from Steam install
  --vanilla-itch PATH     Vanilla data.win from itch.io install
  --patched-steam PATH    Pre-patched data.win for Steam (skips UTMT)
  --patched-itch PATH     Pre-patched data.win for itch (skips UTMT)
  --utmt PATH             Path to UndertaleModCLI.exe (or set UTMT_CLI env var)
  --gnx-source PATH       Path to GNX source root (default: ../GNX)
  --gnx-version VER       GNX version string (default: read from constants.go)
  --output NAME           Output exe name (default: GNX_v<version>.exe)
  --skip-verify           Skip round-trip verification step
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd, **kwargs):
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        print(f"FAILED: {result.stderr.strip()}")
        sys.exit(1)
    if result.stdout.strip():
        print(f"  {result.stdout.strip()}")
    return result


def patch_with_utmt(utmt_path, vanilla_path, gnx_source, output_path):
    """Run install_foundation.csx against a copy of vanilla data.win."""
    csx = os.path.join(gnx_source, "install_foundation.csx")
    gml_dir = os.path.join(gnx_source, "gml")
    assets_dir = os.path.join(gnx_source, "GNX_assets")

    for p, name in [(csx, "install_foundation.csx"), (gml_dir, "gml/")]:
        if not os.path.exists(p):
            print(f"ERROR: {name} not found at {p}")
            sys.exit(1)

    with tempfile.TemporaryDirectory(prefix="gnx_build_") as tmpdir:
        work_data = os.path.join(tmpdir, "data.win")
        shutil.copy2(vanilla_path, work_data)

        work_gml = os.path.join(tmpdir, "gml")
        shutil.copytree(gml_dir, work_gml)
        if os.path.isdir(assets_dir):
            shutil.copytree(assets_dir, os.path.join(tmpdir, "GNX_assets"))

        work_csx = os.path.join(tmpdir, "install_foundation.csx")
        shutil.copy2(csx, work_csx)

        with open(work_csx, "r", encoding="utf-8-sig") as f:
            csx_src = f.read()
        csx_src = re.sub(
            r'string\?\[\] candidateDirs\s*=\s*\{[^}]*\};',
            'string?[] candidateDirs = { Directory.GetCurrentDirectory() };',
            csx_src
        )
        with open(work_csx, "w", encoding="utf-8") as f:
            f.write(csx_src)

        print("  Running UTMT patcher (this may take a minute)...")
        run([utmt_path, "load", work_data, "-s", work_csx, "-o", work_data, "-f"], cwd=tmpdir)

        shutil.copy2(work_data, output_path)
    print(f"  Patched data.win written to {output_path}")


def generate_delta(vanilla_path, patched_path, delta_path, installer_root):
    """Generate a fossil delta using cmd/mkdelta."""
    mkdelta = os.path.join(installer_root, "cmd", "mkdelta")
    run(["go", "run", ".", vanilla_path, patched_path, delta_path], cwd=mkdelta)


def stamp_source(main_go_path, vanilla_checksums, delta_files, upgrade_checksums=None):
    """Replace STAMP markers in main.go with actual values."""
    with open(main_go_path, "r", encoding="utf-8") as f:
        src = f.read()

    def map_literal(d):
        lines = []
        for k, v in d.items():
            lines.append(f'\t"{k}": "{v}",')
        return "{\n" + "\n".join(lines) + "\n}"

    src = re.sub(
        r'(// STAMP:vanilla_checksums\nvar vanillaChecksums = map\[string\]string)\s*\{[^}]*\}',
        r'\1 ' + map_literal(vanilla_checksums),
        src
    )

    src = re.sub(
        r'(// STAMP:delta_files\nvar deltaFiles = map\[string\]string)\s*\{[^}]*\}',
        r'\1 ' + map_literal(delta_files),
        src
    )

    src = re.sub(
        r'(// STAMP:upgrade_checksums\nvar upgradeChecksums = map\[string\]string)\s*\{[^}]*\}',
        r'\1 ' + map_literal(upgrade_checksums or {}),
        src
    )

    with open(main_go_path, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"  Stamped {main_go_path}")


def stamp_versioninfo(installer_root, gnx_version):
    """Update versioninfo.json with the current GNX version and generate resource."""
    vi_path = os.path.join(installer_root, "versioninfo.json")
    if not os.path.exists(vi_path):
        return

    with open(vi_path, "r", encoding="utf-8") as f:
        vi = json.load(f)

    numeric_ver = re.sub(r'[^0-9.]', '', gnx_version.split('_')[0])
    parts = numeric_ver.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0

    vi["FixedFileInfo"]["FileVersion"] = {"Major": major, "Minor": minor, "Patch": patch, "Build": 0}
    vi["FixedFileInfo"]["ProductVersion"] = {"Major": major, "Minor": minor, "Patch": patch, "Build": 0}
    vi["StringFileInfo"]["FileVersion"] = f"{major}.{minor}.{patch}.0"
    vi["StringFileInfo"]["ProductVersion"] = f"{major}.{minor}.{patch}.0"

    with open(vi_path, "w", encoding="utf-8") as f:
        json.dump(vi, f, indent=2)

    # the assembly identity in the exe's manifest carries the version too (it stayed at 1.4.6.0 until 1.5.2)
    mf_path = os.path.join(installer_root, vi.get("ManifestPath", "GNX.manifest"))
    if os.path.exists(mf_path):
        with open(mf_path, "r", encoding="utf-8") as f:
            mf = f.read()
        mf = re.sub(r'(<assemblyIdentity[^>]*\bversion=")[0-9.]+(")', r'\g<1>' + f"{major}.{minor}.{patch}.0" + r'\g<2>', mf, count=1)
        with open(mf_path, "w", encoding="utf-8") as f:
            f.write(mf)

    goversioninfo = os.path.join(os.environ.get("GOPATH", os.path.join(os.path.expanduser("~"), "go")), "bin", "goversioninfo.exe")
    if os.path.exists(goversioninfo):
        run([goversioninfo, "-o", "resource.syso"], cwd=installer_root)
    else:
        print("  SKIP: goversioninfo not found, no Windows version info embedded")


def build_exe(installer_root, output_name):
    """go build the installer."""
    run(["go", "build", "-trimpath", "-ldflags=-s -w", "-o", output_name, "."], cwd=installer_root)
    out_path = os.path.join(installer_root, output_name)
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"  Built {output_name} ({size_mb:.1f} MB)")
    return out_path


def verify_roundtrip(installer_root, vanilla_path, delta_path, patched_path):
    """Apply the delta to vanilla and verify the result matches the patched file."""
    expected_hash = sha256_file(patched_path)
    with tempfile.TemporaryDirectory(prefix="gnx_verify_") as tmpdir:
        verify_go = os.path.join(tmpdir, "verify.go")
        out_path = os.path.join(tmpdir, "result.win")

        with open(verify_go, "w") as f:
            f.write("""package main

import (
    "fmt"
    "os"
    fdelta "github.com/shadowspore/fossil-delta"
)

func main() {
    src, _ := os.ReadFile(os.Args[1])
    delta, _ := os.ReadFile(os.Args[2])
    result, err := fdelta.Apply(src, delta)
    if err != nil { fmt.Println("APPLY FAILED:", err); os.Exit(1) }
    os.WriteFile(os.Args[3], result, 0644)
}
""")
        go_mod = os.path.join(tmpdir, "go.mod")
        with open(go_mod, "w") as f:
            f.write("module verify\ngo 1.21\nrequire github.com/shadowspore/fossil-delta v0.0.0-20241213113458-1d797d70cbe3\n")

        run(["go", "mod", "tidy"], cwd=tmpdir)
        run(["go", "run", ".", vanilla_path, delta_path, out_path], cwd=tmpdir)

        actual = sha256_file(out_path)
        if actual == expected_hash:
            print("  Round-trip verification PASSED")
            return True
        else:
            print(f"  Round-trip verification FAILED!")
            print(f"    Expected: {expected_hash}")
            print(f"    Got:      {actual}")
            return False


def read_go_const(installer_root, name):
    """Read a const string value from constants.go."""
    path = os.path.join(installer_root, "constants.go")
    with open(path, "r") as f:
        for line in f:
            m = re.search(rf'const {name} = "([^"]*)"', line)
            if m:
                return m.group(1)
    return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Build the GNX self-installing package")
    parser.add_argument("--vanilla-steam", help="Path to vanilla Steam data.win")
    parser.add_argument("--vanilla-itch", help="Path to vanilla itch.io data.win")
    parser.add_argument("--patched-steam", help="Pre-patched Steam data.win (skips UTMT)")
    parser.add_argument("--patched-itch", help="Pre-patched itch.io data.win (skips UTMT)")
    parser.add_argument("--utmt", default=os.environ.get("UTMT_CLI", ""), help="Path to UndertaleModCLI.exe")
    parser.add_argument("--gnx-source", default="../GNX", help="Path to GNX source root")
    parser.add_argument("--gnx-version", help="Override GNX version string")
    parser.add_argument("--output", help="Output exe name (default: GNX_v<version>.exe)")
    parser.add_argument("--skip-verify", action="store_true", help="Skip round-trip verification")
    args = parser.parse_args()

    installer_root = os.path.dirname(os.path.abspath(__file__))
    main_go = os.path.join(installer_root, "main.go")
    deltas_dir = os.path.join(installer_root, "deltas")
    os.makedirs(deltas_dir, exist_ok=True)

    gnx_version = args.gnx_version or read_go_const(installer_root, "GNX_VERSION")
    game_version = read_go_const(installer_root, "GAME_VERSION")
    output_name = args.output or f"GNX_v{gnx_version}.exe"

    if not args.vanilla_steam and not args.vanilla_itch:
        print("ERROR: need at least one of --vanilla-steam or --vanilla-itch.")
        sys.exit(1)

    variants = {}  # variant -> (vanilla_path, patched_path)

    for variant, vanilla_arg, patched_arg in [
        ("steam", args.vanilla_steam, args.patched_steam),
        ("itch", args.vanilla_itch, args.patched_itch),
    ]:
        if vanilla_arg is None:
            continue
        vanilla_path = os.path.abspath(vanilla_arg)
        if not os.path.exists(vanilla_path):
            print(f"ERROR: vanilla {variant} not found: {vanilla_path}")
            sys.exit(1)

        if patched_arg:
            patched_path = os.path.abspath(patched_arg)
            if not os.path.exists(patched_path):
                print(f"ERROR: patched {variant} not found: {patched_path}")
                sys.exit(1)
        else:
            if not args.utmt:
                print(f"ERROR: no --patched-{variant} and no --utmt specified.")
                sys.exit(1)
            if not os.path.exists(args.utmt):
                print(f"ERROR: UTMT not found: {args.utmt}")
                sys.exit(1)
            print(f"\n=== Patching {variant} data.win via UTMT ===")
            patched_path = os.path.join(deltas_dir, f"patched_{variant}.win")
            patch_with_utmt(args.utmt, vanilla_path, os.path.abspath(args.gnx_source), patched_path)

        variants[variant] = (vanilla_path, patched_path)

    # --- Hash ---

    print("\n=== Hashing ===")
    vanilla_checksums = {}
    delta_file_map = {}

    for variant, (vanilla_path, patched_path) in variants.items():
        vh = sha256_file(vanilla_path)
        ph = sha256_file(patched_path)
        print(f"  {variant} vanilla: {vh}")
        print(f"  {variant} patched: {ph}")
        if vh in vanilla_checksums:
            print(f"  WARNING: {variant} vanilla hash collides with {vanilla_checksums[vh]} (identical data.win)")
            print(f"  Keeping first variant '{vanilla_checksums[vh]}' in checksum map")
        else:
            vanilla_checksums[vh] = variant

    # --- Generate deltas ---

    print("\n=== Generating fossil deltas ===")
    for variant, (vanilla_path, patched_path) in variants.items():
        delta_name = f"gnx_{game_version}_{variant}.fossil"
        delta_path = os.path.join(deltas_dir, delta_name)
        generate_delta(vanilla_path, patched_path, os.path.abspath(delta_path), installer_root)
        delta_file_map[variant] = f"deltas/{delta_name}"
        size_kb = os.path.getsize(delta_path) / 1024
        print(f"  {delta_name}: {size_kb:.0f} KB")

    # --- Upgrade deltas from old patched versions ---

    history_path = os.path.join(deltas_dir, "patched_history.json")
    upgrade_checksums = {}

    if os.path.exists(history_path):
        with open(history_path, "r") as f:
            history = json.load(f)

        # Each variant upgrades to the current build of the same variant (an itch install must
        # not receive the Steam data.win); entries of the version being built are skipped.
        print("\n=== Generating upgrade deltas ===")
        for ver, ver_variants in history.items():
            if ver == gnx_version:
                print(f"  SKIP {ver}: the version being built")
                continue
            for var_name, info in ver_variants.items():
                if var_name not in variants:
                    print(f"  SKIP {ver}/{var_name}: no current {var_name} build")
                    continue
                target_variant = var_name
                _, target_patched = variants[target_variant]
                target_hash = sha256_file(target_patched)
                old_hash = info["hash"]
                old_file = os.path.join(deltas_dir, info["file"])

                if old_hash == target_hash:
                    print(f"  SKIP {ver}/{var_name}: same hash as current {target_variant}")
                    continue
                if not os.path.exists(old_file):
                    print(f"  SKIP {ver}/{var_name}: file not found ({info['file']})")
                    continue

                delta_name = f"upgrade_{ver}_{var_name}.fossil"
                delta_path = os.path.join(deltas_dir, delta_name)
                print(f"  Generating {delta_name}...")
                generate_delta(old_file, target_patched, os.path.abspath(delta_path), installer_root)
                size_kb = os.path.getsize(delta_path) / 1024
                print(f"  {delta_name}: {size_kb:.0f} KB")
                upgrade_checksums[old_hash] = f"deltas/{delta_name}"
    else:
        print("\n=== No patched_history.json — skipping upgrade deltas ===")

    # --- Stamp Go source ---

    print("\n=== Stamping source ===")
    stamp_source(main_go, vanilla_checksums, delta_file_map, upgrade_checksums)

    # --- Version info ---

    print("\n=== Embedding version info ===")
    stamp_versioninfo(installer_root, gnx_version)

    # --- Build ---

    print("\n=== Building ===")
    exe_path = build_exe(installer_root, output_name)

    # --- Verify ---

    if not args.skip_verify:
        print("\n=== Verifying round-trip ===")
        for variant, (vanilla_path, patched_path) in variants.items():
            delta_path = os.path.join(deltas_dir, f"gnx_{game_version}_{variant}.fossil")
            print(f"  Verifying {variant}...")
            if not verify_roundtrip(installer_root, vanilla_path, delta_path, patched_path):
                print("BUILD FAILED: verification error")
                sys.exit(1)

    # --- Save patched history for future upgrades ---

    print("\n=== Saving patched history ===")
    if not os.path.exists(history_path):
        history = {}
    current_entry = {}
    for variant, (vanilla_path, patched_path) in variants.items():
        ph = sha256_file(patched_path)
        saved_name = f"patched_{gnx_version}_{variant}.win"
        saved_path = os.path.join(deltas_dir, saved_name)
        if os.path.abspath(patched_path) != os.path.abspath(saved_path):
            shutil.copy2(patched_path, saved_path)
        current_entry[variant] = {"hash": ph, "file": saved_name}
        print(f"  Saved {saved_name} ({ph[:16]}...)")

    history[gnx_version] = current_entry
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"  Updated {history_path}")

    # --- Report ---

    print("\n" + "=" * 50)
    print(f"  GNX Version:       {gnx_version}")
    print(f"  Game Version:      {game_version}")
    print(f"  Installer:         {output_name}")
    print(f"  Exe size:          {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
    for variant in variants:
        delta_path = os.path.join(deltas_dir, f"gnx_{game_version}_{variant}.fossil")
        print(f"  Delta ({variant}):    {os.path.getsize(delta_path) / 1024:.0f} KB")
    print(f"  Variants:          {', '.join(variants.keys())}")
    if upgrade_checksums:
        print(f"  Upgrade paths:     {len(upgrade_checksums)}")
    print("=" * 50)
    print(f"\n  {output_name} is ready to ship.")


if __name__ == "__main__":
    main()
