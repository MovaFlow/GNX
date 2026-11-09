"""Compares the shape of two saves: key sets per path, the lengths of the type arrays, and the per-type data. Positions and timers are not compared, because the game is not frame-deterministic.
Run: python tools/save_shape_diff.py A B
Exit: 0 same shape, 1 differences, 3 bad files."""
import json
import sys
from pathlib import Path

TYPE_LENGTHS = ("mon_num", "nest_num", "br_unlock", "gnx_br_unlock")
TYPE_VALUES = ("mon_num", "br_unlock", "gnx_br_unlock", "goblin", "hobgoblin", "tentacle", "ogre")


def shape(node, path="", out=None):
    """{path: set of keys} for the whole save. List items share one path, so their keys are a union."""
    out = {} if out is None else out
    if isinstance(node, dict):
        out.setdefault(path, set()).update(node)
        for k, v in node.items():
            shape(v, f"{path}.{k}", out)
    elif isinstance(node, list):
        for v in node:
            shape(v, path + "[]", out)
    return out


def compare(a, b):
    sa, sb = shape(a), shape(b)
    r = []
    for p in sorted(set(sa) | set(sb)):
        only_a, only_b = sa.get(p, set()) - sb.get(p, set()), sb.get(p, set()) - sa.get(p, set())
        if only_a or only_b:
            r.append(f"keys {p or '(top)'}: only A {sorted(only_a)}, only B {sorted(only_b)}")
    va, vb = a["global_list"]["val"], b["global_list"]["val"]
    for k in TYPE_LENGTHS:
        la, lb = len(va.get(k, [])), len(vb.get(k, []))
        if la != lb:
            r.append(f"length val.{k}: A {la}, B {lb}")
    for k in TYPE_VALUES:
        if va.get(k) != vb.get(k):
            r.append(f"values val.{k}: A {json.dumps(va.get(k))}, B {json.dumps(vb.get(k))}")
    return r


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "val" not in data.get("global_list", {}):
        raise ValueError(f"{path}: no global_list.val")
    return data


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 3
    try:
        a, b = load(sys.argv[1]), load(sys.argv[2])
    except (OSError, ValueError) as e:
        print(f"bad file: {e}")
        return 3
    r = compare(a, b)
    print("\n".join(r) if r else "same shape")
    return 1 if r else 0


if __name__ == "__main__":
    sys.exit(main())
