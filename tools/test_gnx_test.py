"""Self-check for the gnx_test.py log parser. Run: python tools/test_gnx_test.py"""
from gnx_test import parse_log, verdict, EXIT_PASS, EXIT_FAIL, EXIT_TIMEOUT

GOOD = """[GNX] loader start
[GNX] loading: GNX Example Mod v1.0.0
[GNX-TIME] TOTAL loader = 440.54 ms
[GNX-TEST] Suite start
[GNX-TEST] PASS  T01 cell_registry is a map
[GNX-TEST] SKIP  T27 no mods
[GNX-TEST] 2/2 passed
[GNX-TEST] === DISPATCH ROUTING CHECK ===
[GNX-TEST] SKIP  DROUTE h=25 NO_HUMAN_SPR
[GNX-TEST] DROUTE: 422 PASS 0 FAIL 20 SKIP
"""

r = parse_log(GOOD)
assert r["done"] and r["suite_pass"] == r["suite_total"] == 2, r
assert r["droute"] == {"pass": 422, "fail": 0, "skip": 20}, r
assert r["fails"] == [] and r["loader_ms"] == 440.54, r
assert r["mods_loaded"] == ["GNX Example Mod v1.0.0"], r
assert verdict(r) == EXIT_PASS
assert not r["harness_done"] and parse_log(GOOD + "[GNX-TEST] HARNESS DONE\n")["harness_done"]

# suite failure: per-test FAIL line collected, summary line with "FAILED" not double-counted
bad = GOOD.replace("[GNX-TEST] 2/2 passed",
                   "[GNX-TEST] FAIL  T69 missing return: example_mod(no_return) \n"
                   "[GNX-TEST] 1/2 passed  *** 1 FAILED ***")
r = parse_log(bad)
assert r["fails"] == ["FAIL  T69 missing return: example_mod(no_return)"], r["fails"]
assert verdict(r) == EXIT_FAIL

# dispatch failure only
r = parse_log(GOOD.replace("422 PASS 0 FAIL", "421 PASS 1 FAIL")
              .replace("DROUTE h=25", "x\n[GNX-TEST] FAIL  DROUTE h=9 c=3 wrong spr\n[GNX-TEST] SKIP  DROUTE h=25"))
assert verdict(r) == EXIT_FAIL and any("h=9" in f for f in r["fails"]), r

# mod load error (e.g. version skip): tests may pass but run is still a failure
r = parse_log(GOOD + "[GNX] ERROR: Mod 'foo': incompatible with game version 1.39\n")
assert r["mod_errors"] == ["Mod 'foo': incompatible with game version 1.39"], r
assert verdict(r) == EXIT_FAIL

# suite never finished (crash / hang)
r = parse_log(GOOD.split("[GNX-TEST] 2/2")[0])
assert not r["done"] and verdict(r) == EXIT_TIMEOUT
assert verdict(parse_log("")) == EXIT_TIMEOUT

# scenario log
from gnx_test import parse_scn
SCN = """[GNX-SCN] START save_roundtrip steps=3
[GNX-SCN] PASS  min floor=3 want >= 3
[GNX-SCN] snapshot 'before' {"floor":3.0}
[GNX-SCN] FAIL  same_as 'before' units: 5.0 -> 4.0;
[GNX-SCN] DONE 1/2 passed
"""
s = parse_scn(SCN)
assert s["done"] and (s["pass"], s["total"]) == (1, 2), s
assert len(s["fails"]) == 1 and s["fails"][0].startswith("FAIL  same_as 'before' units"), s
r = parse_log(GOOD); r["scn"] = s
assert verdict(r) == EXIT_FAIL
clean = "\n".join(l for l in SCN.splitlines() if "FAIL" not in l).replace("1/2", "1/1")
r["scn"] = parse_scn(clean)
assert verdict(r) == EXIT_PASS
r["scn"] = parse_scn(SCN.split("[GNX-SCN] DONE")[0])  # game died mid-scenario
assert verdict(r) == EXIT_TIMEOUT

# player-save guard: a modified slot is restored, a created slot is moved aside, untouched slots stay
import tempfile, pathlib, gnx_test
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    saves, game = tmp / "saves", tmp / "game"
    saves.mkdir(); game.mkdir()
    gnx_test.SAVE_DIR = saves
    (saves / "save_file_1.json").write_text("REAL")
    (saves / "save_file_2.json").write_text("KEEP")
    g = gnx_test.guard_player_saves(game)
    (saves / "save_file_1.json").write_text("HARNESS")   # overwritten by a bad scenario
    (saves / "save_file_3.json").write_text("NEW")       # created by a bad scenario
    touched = gnx_test.restore_player_saves(g)
    assert sorted(touched) == ["save_file_1.json", "save_file_3.json"], touched
    assert (saves / "save_file_1.json").read_text() == "REAL"
    assert (saves / "save_file_2.json").read_text() == "KEEP"
    assert not (saves / "save_file_3.json").exists() and (saves / "save_file_3.json.harness_created").exists()
    assert gnx_test.restore_player_saves(g) == []

print("ok")

# live progress line: bar fill, and one rendered line (forced on; normally terminal-only)
import io, sys as _sys
from pathlib import Path as _P
from gnx_test import Progress, Box, plan_jobs
p = Progress(line=True)
p.uni = False
assert p.bar(0.5, 4) == "##--" and p.bar(2, 3) == "###" and p.bar(-1, 2) == "--"
_err, _sys.stderr = _sys.stderr, io.StringIO()
try:
    p.plan(10, 2, 60.0)
    p.start(1, "raid_all_stages", 9.0)
    p.tick(1, Box(_P("."), _P("."), _P("no_such_dir")), "[GNX-TEST] PASS  T01 x" + chr(10), "[GNX-SCN] PASS  a" + chr(10) + "[GNX-SCN] FAIL  b" + chr(10))
    p.result(1, "raid_all_stages", "FAIL", "1/2")
    line = _sys.stderr.getvalue()
finally:
    _sys.stderr = _err
assert "[0/10]" in line and "raid_all_stages" in line and "[1/10]" in line, line
assert p.results == [["raid_all_stages", "FAIL", "1/2"]]

# job planning: a fixture chain (save_fixture_as -> fixture) stays one job, in order
sc = {"a": {"save_fixture_as": "fx"}, "b": {"fixture": "fx", "save_fixture_as": "fx2"}, "c": {"fixture": "fx2"},
      "d": {"fixture": "nest"}}
assert plan_jobs([None, "a", "b", "c", "d"], sc) == [[None], ["a", "b", "c"], ["d"]]
# a fixture used through player_slots chains too (mod_menu_b_walkthrough reads mod_menu_a_setup's save that way)
sc = {"m_a": {"save_fixture_as": "fx"}, "m_b": {"player_slots": {"1": {"fixture": "fx"}}}, "z": {}}
assert plan_jobs([None, "m_a", "m_b", "z"], sc) == [[None], ["m_a", "m_b"], ["z"]]
