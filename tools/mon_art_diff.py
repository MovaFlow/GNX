"""Compares two monster art dumps (monster art rework). Run: python tools/mon_art_diff.py A B
Exit: 0 identical, 1 real differences, 2 only subset differences: results overlap, so different rolls or one changed random arm (rerun with more repeats), 3 bad or mismatched files."""
import sys
from pathlib import Path


class DumpError(Exception):
    pass


def load(path):
    header = None
    values = {}
    records = {}
    end = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split("	")
        try:
            if parts[0] == "H":
                header = dict(p.split("=", 1) for p in parts[1:])
            elif parts[0] == "V":
                values[parts[1]] = parts[2]
            elif parts[0] in ("C", "S"):
                records[parts[0] + ":" + parts[1] if parts[0] == "S" else parts[1]] = frozenset(values[i] for i in parts[2].split(","))
            elif parts[0] == "E":
                end = int(parts[1])
        except (IndexError, KeyError, ValueError):
            raise DumpError(f"{path}: torn line: {line[:80]}") from None
    if header is None:
        raise DumpError(f"{path}: no header")
    if end is None or end != len(records):
        raise DumpError(f"{path}: truncated (end marker {end}, {len(records)} records)")
    if not records:
        raise DumpError(f"{path}: empty dump")
    return {"header": header, "records": records}


def compare(a, b):
    ra, rb = a["records"], b["records"]
    r = {"diff": [], "subset": [], "only_a": sorted(set(ra) - set(rb)), "only_b": sorted(set(rb) - set(ra))}
    for k in sorted(set(ra) & set(rb)):
        if ra[k] == rb[k]:
            continue
        r["subset" if ra[k] & rb[k] else "diff"].append(k)  # shared results: different rolls, unproven
    return r


def _fields(text):
    return dict(p.split("=", 1) for p in text.split(";") if "=" in p)


def field_diff(sa, sb):
    """Readable difference between the first values of two sets."""
    fa, fb = _fields(sorted(sa)[0]), _fields(sorted(sb)[0])
    return [f"{k}: {fa.get(k)} -> {fb.get(k)}" for k in sorted(set(fa) | set(fb)) if fa.get(k) != fb.get(k)]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    try:
        a, b = load(sys.argv[1]), load(sys.argv[2])
    except DumpError as e:
        print(e)
        sys.exit(3)
    for key in ("cells", "classes"):
        if a["header"].get(key) != b["header"].get(key):
            print(f"not comparable: {key} differ\n  A: {a['header'].get(key)}\n  B: {b['header'].get(key)}")
            sys.exit(3)
    if a["header"].get("repeats") != b["header"].get("repeats"):
        print(f"note: repeats differ ({a['header'].get('repeats')} and {b['header'].get('repeats')}), so the rolls differ: expect subset lines")
    r = compare(a, b)
    print(f"{len(a['records'])} records: {len(r['diff'])} diff, {len(r['subset'])} subset, {len(r['only_a'])} only A, {len(r['only_b'])} only B")
    for k in r["diff"][:20]:
        print(" DIFF", k, field_diff(a["records"][k], b["records"][k]))
    for k in (r["only_a"] + r["only_b"])[:20]:
        print(" ONLY", k)
    if r["subset"]:
        cells = sorted({k.split(":")[-1].split("|")[0] for k in r["subset"]}, key=int)
        print(" SUBSET in cells", ",".join(cells), "- rerun both sides with a higher \"repeats\" and \"cells\" set to these")
    if r["diff"] or r["only_a"] or r["only_b"]:
        sys.exit(1)
    sys.exit(2 if r["subset"] else 0)


if __name__ == "__main__":
    main()
