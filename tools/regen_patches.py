#!/usr/bin/env python3
"""Regenerate GNX/diffs/*.patch and GNX/gnx.patch before committing.

Only GNX/gml/*.gml files are diffed, each against its GNX/gml_138 counterpart (or as
a new file). Untouched vanilla files, backups (*.bak*), editor temp files and anything
that is not .gml are never included, so no decompiled code beyond GNX's own changes
ends up in the public patches.

    python tools/regen_patches.py
"""
import pathlib
import subprocess
import sys

GNX = pathlib.Path(__file__).resolve().parent.parent / "GNX"


def main():
    gml, base, out = GNX / "gml", GNX / "gml_138", GNX / "diffs"
    combined, written = [], []
    for f in sorted(gml.glob("*.gml")):
        # run from GNX/ so the headers read gml_138/<file> and gml/<file>
        rel_base, rel_new = f"gml_138/{f.name}", f"gml/{f.name}"
        r = subprocess.run(["diff", "-uN", rel_base, rel_new], cwd=GNX, capture_output=True)
        if r.returncode == 0:
            continue  # identical to vanilla: no patch
        if r.returncode != 1:
            sys.exit(f"diff failed on {f.name}: {r.stderr.decode(errors='replace')}")
        text = r.stdout.decode("utf-8").replace("\r\n", "\n")
        (out / f"{f.name}.patch").write_bytes(text.encode("utf-8"))
        written.append(f.name)
        combined.append(f"diff -uN {rel_base} {rel_new}\n" + text)
    stale = [p for p in out.glob("*.patch") if p.name[: -len(".patch")] not in written]
    for p in stale:
        p.unlink()
    (GNX / "gnx.patch").write_bytes("".join(combined).encode("utf-8"))
    print(f"{len(written)} patches written, {len(stale)} stale removed")


if __name__ == "__main__":
    main()
