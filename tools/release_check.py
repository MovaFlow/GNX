#!/usr/bin/env python3
"""Before publishing a release: is everything built from the current sources? Exit 0 = ready, 1 = the list of what is not.

    python tools/release_check.py
"""
import glob, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def p(*a):
    return os.path.join(ROOT, *a)


def newest(paths):
    """(mtime, path) of the most recently changed file."""
    return max(((os.path.getmtime(f), f) for f in paths if os.path.isfile(f)), default=(0, ""))


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()


def built_after(label, built, sources, problems):
    """built must exist and be newer than every source."""
    if not os.path.isfile(built):
        problems.append(f"{label}: {os.path.relpath(built, ROOT)} is missing")
        return
    t, src = newest(sources)
    if t > os.path.getmtime(built):
        problems.append(f"{label}: stale, {os.path.relpath(src, ROOT)} changed after {os.path.basename(built)} was built")


def main():
    problems = []
    with open(p("CHANGELOG.md"), encoding="utf-8") as f:
        m = re.search(r"^## (.+)$", f.read(), re.M)
    head = m.group(1).strip()
    if not head.startswith("v"):
        problems.append(f"CHANGELOG: the top section is '{head}', not a version")
    ver = head.lstrip("v")

    with open(p("GNX", "gml", "gml_GlobalScript_s_initials.gml"), encoding="utf-8") as f:
        m = re.search(r'global\.gnx_version = "([^"]+)"', f.read())
    if not m or m.group(1) != ver:
        problems.append(f"gnx_version is {m.group(1) if m else '?'}, the changelog says {ver}")

    with open(p("gnx-installer", "constants.go"), encoding="utf-8") as f:
        m = re.search(r'GNX_VERSION = "([^"]+)"', f.read())
    if not m or m.group(1) != ver:
        problems.append(f"constants.go GNX_VERSION is {m.group(1) if m else '?'}, the changelog says {ver}")

    game = glob.glob(p("GNX", "gml", "*.gml")) + [p("GNX", "install_foundation.csx")] + glob.glob(p("GNX", "GNX_assets", "**", "*"), recursive=True)
    installer = glob.glob(p("gnx-installer", "*.go"))
    built_after("installer", p("gnx-installer", f"GNX_v{ver}.exe"), game + installer, problems)
    built_after("Mav sources", p("mav_handoff", f"GNX_{ver}_sources.zip"), game, problems)
    built_after("atlas packer", p("tools", "gnx_atlas_pack", "dist", "gnx_atlas_pack.exe"), [p("tools", "gnx_atlas_pack", "gnx_atlas_pack.py")], problems)
    for f in ("github_release.md", "discord_post.md"):
        if not os.path.isfile(p(f"release_v{ver}", f)):
            problems.append(f"release text release_v{ver}/{f} is missing")

    dirty = git("status", "--short")
    if dirty:
        problems.append(f"git: {len(dirty.splitlines())} uncommitted change(s), run regen_patches first if GML changed")
    git("fetch", "-q", "origin")
    ahead = git("rev-list", "--count", "origin/main..HEAD")
    if ahead not in ("", "0"):
        problems.append(f"git: {ahead} commit(s) not pushed")

    if problems:
        print(f"NOT READY to publish v{ver}:")
        for x in problems:
            print("  - " + x)
        return 1
    print(f"ready to publish v{ver}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
