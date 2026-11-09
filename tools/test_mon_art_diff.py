"""Self-check for mon_art_diff.py. Run: python tools/test_mon_art_diff.py"""
import tempfile
from pathlib import Path

from mon_art_diff import DumpError, compare, field_diff, load

D = Path(tempfile.mkdtemp())


def dump(name, *lines, end=True):
    p = D / name
    body = ["H\trepeats=12\tcells=1\tclasses=0"] + list(lines)
    if end:
        body.append(f"E\t{sum(1 for l in lines if l[0] in 'CS')}")
    p.write_text("\n".join(body) + "\n", encoding="utf-8")
    return p


V = ("V\t0\tbody_b=spr_a;head_b=-1;", "V\t1\tbody_b=spr_a;head_b=spr_h;")
a = load(dump("a", *V, "C\tk1\t0", "C\tk2\t0,1"))
assert a["records"]["k2"] == frozenset(["body_b=spr_a;head_b=-1;", "body_b=spr_a;head_b=spr_h;"]), a

# value ids may differ between runs: only the texts count
b = load(dump("b", "V\t0\tbody_b=spr_a;head_b=spr_h;", "V\t1\tbody_b=spr_a;head_b=-1;", "C\tk1\t1", "C\tk2\t1,0"))
r = compare(a, b)
assert not (r["diff"] or r["subset"] or r["only_a"] or r["only_b"]), r

# a roll that did not come up is a subset, not a real difference
c = load(dump("c", *V, "C\tk1\t0", "C\tk2\t0"))
r = compare(a, c)
assert r["subset"] == ["k2"] and not r["diff"], r

# a different value is a real difference
d = load(dump("d", "V\t0\tbody_b=spr_b;head_b=-1;", "V\t1\tbody_b=spr_a;head_b=-1;", "V\t2\tbody_b=spr_a;head_b=spr_h;", "C\tk1\t0", "C\tk2\t1,2"))
r = compare(a, d)
assert r["diff"] == ["k1"], r
assert field_diff(a["records"]["k1"], d["records"]["k1"]) == ["body_b: spr_a -> spr_b"], r

# a key only one side has
e = load(dump("e", *V, "C\tk1\t0"))
r = compare(a, e)
assert r["only_a"] == ["k2"], r

# Review Focus 2: truncated file
try:
    load(dump("t", *V, "C\tk1\t0", end=False))
    raise AssertionError("truncated file accepted")
except DumpError as err:
    assert "truncated" in str(err), err

# Review Focus 1: empty dump
try:
    load(dump("z"))
    raise AssertionError("empty dump accepted")
except DumpError as err:
    assert "empty" in str(err), err

# different rolls can overlap without either containing the other: sampling, not a proven change
g = load(dump("g", "V	0	body_b=spr_a;head_b=spr_h;", "V	1	body_b=spr_a;head_b=spr_i;", "C	k1	0", "C	k2	0,1"))
r = compare(a, g)
assert r["subset"] == ["k2"] and r["diff"] == ["k1"], r

# Review Focus 2: a killed run can leave a torn line: a bad file (exit 3), not a crash that reads as "real differences"
for torn in ("C\tk1", "C\tk1\t9", "V\t0", "H\trepeats"):
    p = D / "torn"
    p.write_text("H\trepeats=12\tcells=1\tclasses=0\nV\t0\tbody_b=spr_a;\nC\tk0\t0\n" + torn + "\nE\t1\n", encoding="utf-8")
    try:
        load(p)
        raise AssertionError("torn file accepted: " + torn)
    except DumpError as err:
        assert "torn" in str(err), (torn, err)

print("ok")
