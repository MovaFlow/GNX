#!/usr/bin/env python3
"""GNX boot-test harness: patch -> launch -> wait for the in-game test suite -> report.

Runs GNX's own boot tests (scr_gnx_test_suite + dispatch routing check) without
G3M or any manual step. Uses a dedicated game folder so G3M's backup/restore of
its own game folder is never touched.

One-time setup (copies runner exe, vanilla data.win, options.ini):
    python tools/gnx_test.py --init "E:/path/to/vanilla goblin nest"

Every run after that:
    python tools/gnx_test.py                  # patch if GML changed, boot, report
    python tools/gnx_test.py --no-patch       # reuse current data.win
    python tools/gnx_test.py --mods GNX/example_mod,E:/other_mod
    python tools/gnx_test.py --keep-open      # leave game running after tests
    python tools/gnx_test.py --scenario save_roundtrip   # boot + one scenario
    python tools/gnx_test.py --all            # boot tests + every scenario

Scenarios (tools/scenarios/*.json) are played in-game by scr_gnx_scn_step. They use
save slot 9 (gnx_harness_save.json); player saves are never read or written. A
scenario with "fixture": "NAME" starts from harness_game/fixtures/NAME.json:
    python tools/gnx_test.py --capture-fixture 2 nest   # copies save_file_2.json

Exit codes: 0 all pass | 1 test failures | 2 patch failed | 3 preflight | 4 timeout/crash
Full log of the last run: <game-dir>/last_run.log
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
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GNX_SRC = REPO / "GNX"
DEFAULT_GAME_DIR = REPO / "harness_game"
DEFAULT_UTMT = REPO / "UTMT_CLI_v0.9.2.0-Windows" / "UndertaleModCli.exe"
DEFAULT_MODS = [GNX_SRC / "example_mod"]
SAVE_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "goblin_nest"
LOG = SAVE_DIR / "gnx_debug.txt"
SCN_LOG = SAVE_DIR / "gnx_scenario.txt"
HARNESS_SAVE = SAVE_DIR / "gnx_harness_save.json"
HARNESS_SAVE_B = SAVE_DIR / "gnx_harness_save_b.json"  # slot 8, always starts empty
SCENARIOS = REPO / "tools" / "scenarios"
SAVE_SLOTS = {"a": "save_file_a.json", "1": "save_file_1.json", "2": "save_file_2.json", "3": "save_file_3.json"}
EXE = "GoblinNest.exe"
VANILLA = "data.vanilla.win"
STAMP = ".harness_stamp"

EXIT_PASS, EXIT_FAIL, EXIT_PATCH, EXIT_PREFLIGHT, EXIT_TIMEOUT = 0, 1, 2, 3, 4


class HarnessError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


# ---------------------------------------------------------------- log parsing

def parse_log(text):
    """Pull the verdict out of gnx_debug.txt. `done` is True once the dispatch
    routing summary (the last line the boot tests write) is present."""
    r = {"done": False, "suite_pass": None, "suite_total": None,
         "droute": None, "fails": [], "mod_errors": [], "loader_ms": None,
         "mods_loaded": [], "harness_done": False}
    for line in text.splitlines():
        if "[GNX-TEST]" in line and re.search(r"\bFAIL\b", line) and "DROUTE:" not in line \
                and not re.search(r"\d+/\d+ passed", line):
            r["fails"].append(line.split("[GNX-TEST]", 1)[1].strip())
        m = re.search(r"\[GNX-TEST\] (\d+)/(\d+) passed", line)
        if m:
            r["suite_pass"], r["suite_total"] = int(m[1]), int(m[2])
        m = re.search(r"\[GNX-TEST\] DROUTE: (\d+) PASS (\d+) FAIL (\d+) SKIP", line)
        if m:
            r["droute"] = {"pass": int(m[1]), "fail": int(m[2]), "skip": int(m[3])}
            r["done"] = True
        if line.startswith("[GNX] ERROR:"):
            r["mod_errors"].append(line.split("ERROR:", 1)[1].strip())
        m = re.search(r"\[GNX-TIME\] TOTAL loader = ([\d.]+) ms", line)
        if m:
            r["loader_ms"] = float(m[1])
        m = re.match(r"\[GNX\] loading: (.+)", line)
        if m:
            r["mods_loaded"].append(m[1].strip())
        if "[GNX-TEST] HARNESS DONE" in line:
            r["harness_done"] = True
    return r


def parse_scn(text):
    """Scenario result from gnx_scenario.txt. `done` once the DONE line is written."""
    r = {"done": False, "pass": 0, "total": 0, "fails": [], "lines": []}
    for line in text.splitlines():
        if not line.startswith("[GNX-SCN] "):
            continue
        body = line[len("[GNX-SCN] "):]
        r["lines"].append(body)
        if body.startswith("FAIL"):
            r["fails"].append(body)
        m = re.match(r"DONE (\d+)/(\d+) passed", body)
        if m:
            r["done"], r["pass"], r["total"] = True, int(m[1]), int(m[2])
    return r


def verdict(r):
    if not r["done"] or r["suite_total"] is None:
        return EXIT_TIMEOUT
    scn = r.get("scn")
    if scn is not None and not scn["done"]:
        return EXIT_TIMEOUT
    if r["mod_errors"]:
        return EXIT_FAIL
    # a scenario may opt out of the boot suite (e.g. a sprite-less reference mod), never out of mod errors
    if not r.get("suite_ignored") and (r["fails"] or r["suite_pass"] != r["suite_total"] or r["droute"]["fail"]):
        return EXIT_FAIL
    if scn is not None and (scn["fails"] or scn["pass"] != scn["total"]):
        return EXIT_FAIL
    return EXIT_PASS


# ---------------------------------------------------------------- steps

def game_running():
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {EXE}", "/NH", "/FO", "CSV"],
                         capture_output=True, text=True).stdout
    return f'"{EXE}"'.lower() in out.lower()


def accepted_versions():
    """The loader accepts a mod if any of its compatible_game_versions is in this list."""
    src = (GNX_SRC / "gml" / "gml_GlobalScript_s_initials.gml").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"global\.gnx_accepted_versions\s*=\s*\[([^\]]*)\]", src)
    if not m:
        raise HarnessError(EXIT_PREFLIGHT, "could not find global.gnx_accepted_versions in s_initials.gml")
    return re.findall(r'"([^"]+)"', m[1])


def init_game_dir(game_dir, vanilla_dir):
    vanilla_dir = Path(vanilla_dir)
    for name in (EXE, "data.win"):
        if not (vanilla_dir / name).is_file():
            raise HarnessError(EXIT_PREFLIGHT, f"--init: {vanilla_dir / name} not found")
    game_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(vanilla_dir / EXE, game_dir / EXE)
    shutil.copy2(vanilla_dir / "data.win", game_dir / VANILLA)
    if (vanilla_dir / "options.ini").is_file():
        shutil.copy2(vanilla_dir / "options.ini", game_dir / "options.ini")
    (game_dir / STAMP).unlink(missing_ok=True)
    print(f"initialised {game_dir}", file=sys.stderr)


def source_hash(game_dir):
    """Hash of everything that feeds the patch. Same hash = data.win is current."""
    h = hashlib.sha256()
    files = sorted((GNX_SRC / "gml").glob("*.gml")) + [GNX_SRC / "install_foundation.csx"]
    assets = GNX_SRC / "GNX_assets"
    if assets.is_dir():
        files += sorted(p for p in assets.rglob("*") if p.is_file())
    files.append(game_dir / VANILLA)
    for p in files:
        h.update(str(p.relative_to(REPO) if p.is_relative_to(REPO) else p.name).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def patch(game_dir, utmt):
    """Same recipe as gnx-installer/build_installer.py:patch_with_utmt, but errors
    are raised (never falls through to copying an unpatched data.win)."""
    out = game_dir / "data.win"
    (game_dir / STAMP).unlink(missing_ok=True)
    out.unlink(missing_ok=True)  # a failed patch must leave no launchable data.win
    with tempfile.TemporaryDirectory(prefix="gnx_harness_") as tmp:
        tmp = Path(tmp)
        work = tmp / "data.win"
        shutil.copy2(game_dir / VANILLA, work)
        shutil.copytree(GNX_SRC / "gml", tmp / "gml")
        if (GNX_SRC / "GNX_assets").is_dir():
            shutil.copytree(GNX_SRC / "GNX_assets", tmp / "GNX_assets")
        csx = (GNX_SRC / "install_foundation.csx").read_text(encoding="utf-8-sig")
        csx, n = re.subn(r'string\?\[\] candidateDirs\s*=\s*\{[^}]*\};',
                         'string?[] candidateDirs = { Directory.GetCurrentDirectory() };', csx)
        if n != 1:
            raise HarnessError(EXIT_PATCH, "candidateDirs line not found in install_foundation.csx")
        (tmp / "install_foundation.csx").write_text(csx, encoding="utf-8")
        t0 = time.time()
        cmd = [str(utmt), "load", str(work), "-s", str(tmp / "install_foundation.csx"), "-o", str(work), "-f"]
        try:
            # stdin=DEVNULL: a UTMT prompt must fail fast, not wait forever on the console
            res = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True,
                                 stdin=subprocess.DEVNULL, timeout=300)
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            raise HarnessError(EXIT_PATCH, "UTMT patch hung for 300s. Last output:\n  " +
                               "\n  ".join(out.splitlines()[-15:]))
        if res.returncode != 0:
            errs = [l for l in res.stderr.splitlines()
                    if l.startswith("gml_") or "Exception:" in l]
            tail = [l for l in res.stdout.splitlines() if not l.startswith("[GNX Foundation")][-10:]
            raise HarnessError(EXIT_PATCH, "UTMT patch failed:\n  " +
                               "\n  ".join(dict.fromkeys(errs) or res.stderr.splitlines()[:10] or tail))
        shutil.copy2(work, out)
    print(f"patched in {time.time() - t0:.1f}s", file=sys.stderr)


def deploy_mods(game_dir, mods, accepted):
    dest = game_dir / "GNX_mods"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir()
    for mod in mods:
        mod = Path(mod)
        man = mod / "manifest.json"
        if not man.is_file():
            raise HarnessError(EXIT_PREFLIGHT, f"no manifest.json in {mod}")
        vers = json.loads(man.read_text(encoding="utf-8-sig")).get("compatible_game_versions", [])
        if not set(vers) & set(accepted):
            raise HarnessError(EXIT_PREFLIGHT,
                               f"{mod.name}: compatible_game_versions {vers} matches none of {accepted}")
        shutil.copytree(mod, dest / mod.name)


def game_dialog(pid):
    """(title, text) of a modal dialog owned by pid, else None. Any such dialog blocks
    the game: GameMaker's 'Code Error' for a GML runtime error, or a message box
    (e.g. GNX's 'Mod loading problem(s)'). Without this both only show up as a timeout."""
    import ctypes
    import ctypes.wintypes as W
    u = ctypes.windll.user32
    cb_t = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    found = []

    def gettext(h):  # WM_GETTEXTLENGTH / WM_GETTEXT work across processes, GetWindowText doesn't
        n = u.SendMessageW(h, 0x000E, 0, 0)
        buf = ctypes.create_unicode_buffer(n + 1)
        u.SendMessageW(h, 0x000D, n + 1, buf)
        return buf.value

    def clsname(h):
        buf = ctypes.create_unicode_buffer(32)
        u.GetClassNameW(h, buf, 32)
        return buf.value

    def top(h, _):
        owner = W.DWORD()
        u.GetWindowThreadProcessId(h, ctypes.byref(owner))
        if owner.value == pid and u.IsWindowVisible(h) and clsname(h) == "#32770":
            texts = []

            def child(c, _):
                if clsname(c) in ("Edit", "Static"):
                    texts.append(gettext(c))
                return True

            u.EnumChildWindows(h, cb_t(child), 0)
            body = "\n".join(l for l in "\n".join(texts).splitlines() if l.strip() and not set(l) <= set("#_"))
            found.append((gettext(h), body, h))
        return True

    u.EnumWindows(cb_t(top), 0)
    return found[0] if found else None  # (title, text, hwnd)


def boot(game_dir, timeout, keep_open, scenario=None, expect_dialog=None):
    """Launch once. Plain boot: -gnx-autotest, game exits after the boot tests.
    Scenario: -gnx-scenario NAME, game exits when the scenario writes DONE."""
    LOG.unlink(missing_ok=True)  # the game truncates it at boot anyway; this makes stale logs impossible
    SCN_LOG.unlink(missing_ok=True)
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 7  # SW_SHOWMINNOACTIVE: don't steal focus
    # -gnx-autotest / -gnx-scenario are read in scr_create_initials (s_initials.gml)
    args = [str(game_dir / EXE)]
    if scenario:
        args += ["-gnx-scenario", scenario]
    elif not keep_open:
        args += ["-gnx-autotest"]
    proc = subprocess.Popen(args, cwd=game_dir, startupinfo=si)
    t0 = time.time()
    r, crash, done_at = parse_log(""), None, None
    dismissed, seen_dialogs = [], set()
    try:
        while time.time() - t0 < timeout:
            time.sleep(0.25)
            if LOG.is_file():
                r = parse_log(LOG.read_text(encoding="utf-8", errors="replace"))
            if proc.poll() is not None:
                break
            if r["done"] and not scenario:
                if keep_open:
                    break
                done_at = done_at or time.time()
                if time.time() - done_at > 3:
                    break  # build predates -gnx-autotest: fall back to killing it
            crash = game_dialog(proc.pid)
            if crash and expect_dialog and expect_dialog in crash[1]:
                # an expected popup (e.g. a deliberate mod conflict): press OK and keep going
                import ctypes
                ctypes.windll.user32.PostMessageW(crash[2], 0x0111, 1, 0)  # WM_COMMAND, IDOK
                ctypes.windll.user32.PostMessageW(crash[2], 0x0010, 0, 0)  # WM_CLOSE (message boxes honour it)
                if crash[2] not in seen_dialogs:  # count each dialog once, however long it takes to close
                    seen_dialogs.add(crash[2])
                    dismissed.append(crash[1].splitlines()[0] if crash[1] else crash[0])
                crash = None
                time.sleep(0.5)
                continue
            if crash:
                break
        r["boot_s"] = round(time.time() - t0, 1)
        r["exit_code"] = proc.poll()
    finally:
        if not keep_open and proc.poll() is None:
            time.sleep(0.3)  # let the final file_text_close land
            proc.terminate()
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                proc.kill()
    text = LOG.read_text(encoding="utf-8", errors="replace") if LOG.is_file() else ""
    boot_s, exit_code = r["boot_s"], r["exit_code"]
    r = parse_log(text)  # final read: the game may have written its last lines right before exiting
    if crash:
        crash = crash[:2]  # hwnd is meaningless after the run (and not JSON)
    r.update(boot_s=boot_s, exit_code=exit_code, crash=crash, dismissed_dialogs=dismissed, kept_open=keep_open,
             tail=text.splitlines()[-40:], scenario=scenario)
    (game_dir / "last_run.log").write_text(text, encoding="utf-8")
    if scenario:
        stext = SCN_LOG.read_text(encoding="utf-8", errors="replace") if SCN_LOG.is_file() else ""
        r["scn"] = parse_scn(stext)
        (game_dir / f"last_scenario_{scenario}.log").write_text(stext, encoding="utf-8")
        if not r["scn"]["done"]:  # keep evidence of incomplete runs; later runs overwrite last_*.log
            stamp = time.strftime("%Y%m%d_%H%M%S")
            (game_dir / f"incomplete_{scenario}_{stamp}.log").write_text(text + "\n\n" + stext, encoding="utf-8")
    return r


def report(r, code):
    scn = r.get("scn")
    if scn is not None:
        state = "PASS" if code == EXIT_PASS else "FAIL" if scn["done"] else "INCOMPLETE"
        tag = "" if scn["done"] else "  [blocked by a dialog, game killed]" if r.get("crash")             else f"  [game exited, code {r['exit_code']}]" if r["exit_code"] is not None else "  [timed out, game killed]"
        print(f"SCENARIO {r['scenario']}: {state}  {scn['pass']}/{scn['total']}  ({r['boot_s']}s){tag}")
        for f in scn["fails"]:
            print("  " + f)
        if not scn["done"]:
            print("  last scenario steps:")
            for l in scn["lines"][-12:]:
                print("    " + l)
    if code == EXIT_TIMEOUT:
        if r.get("crash"):
            title, body = r["crash"]
            what = "GML runtime error" if title == "Code Error" else f"game showed a blocking dialog '{title}'"
            print(f"BOOT FAILED: {what} after {r['boot_s']}s:")
            for l in body.splitlines():
                print("  " + l)
            tail = r["tail"][-8:]
        else:
            why = f"game exited early (code {r['exit_code']})" if r.get("exit_code") is not None \
                else "timed out waiting for the game"
            print(f"BOOT FAILED: {why} after {r.get('boot_s')}s.")
            tail = r["tail"]
        print("Last log lines:")
        for l in tail:
            print("  " + l)
        return
    if scn is not None and not r["fails"] and not r["mod_errors"]:
        return  # boot suite was clean; the scenario line says it all
    if r.get("suite_ignored") and not r["mod_errors"]:
        print(f"  (boot suite not checked by this scenario: {len(r['fails'])} FAIL line(s), "
              "see last_run.log)")
        return
    d = r["droute"]
    print(f"{'PASS' if code == EXIT_PASS else 'FAIL'}  suite {r['suite_pass']}/{r['suite_total']}"
          f"  droute {d['pass']}/{d['fail']}/{d['skip']} (pass/fail/skip)"
          f"  boot {r['boot_s']}s  loader {r['loader_ms']:.0f}ms")
    exit_how = "left open" if r["kept_open"] \
        else "clean exit" if r["harness_done"] or (scn is not None and r["exit_code"] is not None) \
        else "killed (build lacks -gnx-autotest)"
    print("mods: " + (", ".join(r["mods_loaded"]) or "none") + f"  |  game: {exit_how}")
    for f in r["fails"]:
        print("  FAIL " + f.removeprefix("FAIL").strip())
    for m in r["mod_errors"]:
        print("  MOD ERROR " + m)


def strip_mods(save):
    """Drop GNX/mod state from a save so it loads identically with any mod set.
    Refuses (rather than guesses) if modded cells or units are still referenced."""
    val = save["global_list"]["val"]
    for k in ("gnx_mod_data", "gnx_quest_state"):
        val.pop(k, None)
    for k in ("gnx_maps", "gnx_active_map"):
        save.pop(k, None)
    gl = save["global_list"]
    for k, field in (("quest_list", "quest_type"), ("noti_list", "noti_type")):
        gl[k] = [q for q in gl.get(k, []) if not isinstance(q.get(field), str)]  # GNX quests use string ids
    units = [s["unit_data"] for s in save["slot_list"] if isinstance(s.get("unit_data"), dict)]
    units += [u for u in val.get("cage", []) if isinstance(u, dict)]
    units += [r["unit_data"] for k in ("front_row", "back_row") for r in gl.get(k, [])
              if isinstance(r.get("unit_data"), dict)]
    bad_cells = sum(1 for s in save["slot_list"] if s["slot_data"].get("h_type", 0) >= 43)
    bad_units = sum(1 for u in units if u.get("class", 0) >= 14)
    if bad_cells or bad_units:
        raise HarnessError(EXIT_PREFLIGHT, f"--strip-mods: save still holds {bad_cells} modded cell(s) "
                                           f"and {bad_units} modded unit(s); pick a vanilla-content save")
    return save


def guard_player_saves(game_dir):
    """Copy the player's save slots aside before any run. Returns {name: (sha256 or None, backup path)}."""
    store = game_dir / "save_guard"
    store.mkdir(exist_ok=True)
    guard = {}
    for name in SAVE_SLOTS.values():
        src = SAVE_DIR / name
        if src.is_file():
            shutil.copy2(src, store / name)
            guard[name] = (hashlib.sha256(src.read_bytes()).hexdigest(), store / name)
        else:
            guard[name] = (None, None)
    return guard


def restore_player_saves(guard):
    """Put back any player save that changed (or appeared) since guard_player_saves. Returns the names touched."""
    touched = []
    for name, (sha, backup) in guard.items():
        cur = SAVE_DIR / name
        now = hashlib.sha256(cur.read_bytes()).hexdigest() if cur.is_file() else None
        if now == sha:
            continue
        touched.append(name)
        if sha is None:
            cur.rename(cur.with_name(cur.name + ".harness_created"))  # keep, never delete
        else:
            shutil.copy2(backup, cur)
    return touched


def capture_fixture(game_dir, slot, name, strip=False):
    """slot: a/1/2/3, or a file name in the save folder (e.g. a backup copy).
    The player's save is only read, never modified."""
    src = SAVE_DIR / SAVE_SLOTS.get(slot, slot)
    if not src.is_file():
        raise HarnessError(EXIT_PREFLIGHT, f"{src} does not exist")
    data = json.loads(src.read_text(encoding="utf-8-sig"))  # refuse to capture a broken save
    dest = game_dir / "fixtures" / f"{name}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if strip:
        dest.write_text(json.dumps(strip_mods(data), separators=(",", ":")), encoding="utf-8")
    else:
        shutil.copy2(src, dest)
    print(f"captured {src.name} -> {dest}{' (mods stripped)' if strip else ''}", file=sys.stderr)


def load_scenario(name):
    path = SCENARIOS / f"{name}.json"
    if not path.is_file():
        raise HarnessError(EXIT_PREFLIGHT, f"no scenario {path}")
    sc = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(sc.get("steps"), list):
        raise HarnessError(EXIT_PREFLIGHT, f"{path.name}: needs a \"steps\" list")
    return sc


def prepare_scenario(game_dir, sc):
    """Seed save slot 9 from the scenario's fixture, or clear it for a fresh game."""
    fx = sc.get("fixture")
    if fx:
        src = game_dir / "fixtures" / f"{fx}.json"
        if not src.is_file():
            raise HarnessError(EXIT_PREFLIGHT, f"fixture '{fx}' missing ({src}); "
                                               f"create it with --capture-fixture <slot> {fx}")
        if sc.get("fixture_on_map"):
            # play the fixture's nest as the live state of a mod map; the village waits as a fresh map
            data = json.loads(src.read_text(encoding="utf-8-sig"))
            data["gnx_active_map"] = sc["fixture_on_map"]
            data["gnx_maps"] = {"vanilla": "fresh"}
            HARNESS_SAVE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        else:
            shutil.copy2(src, HARNESS_SAVE)
    else:
        HARNESS_SAVE.unlink(missing_ok=True)
    HARNESS_SAVE_B.unlink(missing_ok=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    ap.add_argument("--utmt", type=Path, default=DEFAULT_UTMT)
    ap.add_argument("--init", metavar="VANILLA_DIR", help="set up game dir from a vanilla install, then exit")
    ap.add_argument("--no-patch", action="store_true", help="skip patching, use existing data.win")
    ap.add_argument("--force-patch", action="store_true", help="patch even if sources are unchanged")
    ap.add_argument("--mods", help="comma-separated mod folders (default: GNX/example_mod)")
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--keep-open", action="store_true", help="leave the game running after the tests")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--scenario", help="comma-separated scenario names from tools/scenarios/")
    ap.add_argument("--all", action="store_true", help="boot tests, then every scenario")
    ap.add_argument("--capture-fixture", nargs=2, metavar=("SLOT", "NAME"),
                    help="copy save slot (a/1/2/3) or a save-folder file name to "
                         "harness_game/fixtures/NAME.json, then exit")
    ap.add_argument("--strip-mods", action="store_true",
                    help="with --capture-fixture: remove GNX/mod state from the copy")
    a = ap.parse_args(argv)
    game_dir = a.game_dir.resolve()
    try:
        if a.init:
            init_game_dir(game_dir, a.init)
            return EXIT_PASS
        if a.capture_fixture:
            capture_fixture(game_dir, *a.capture_fixture, strip=a.strip_mods)
            return EXIT_PASS
        if game_running():
            raise HarnessError(EXIT_PREFLIGHT, f"{EXE} is already running; close it first "
                                               "(it shares the debug log and saves)")
        for p in (game_dir / EXE, game_dir / VANILLA):
            if not p.is_file():
                raise HarnessError(EXIT_PREFLIGHT, f"{p} missing; run with --init <vanilla game dir>")
        accepted = accepted_versions()
        mods = [Path(m.strip()) for m in a.mods.split(",")] if a.mods else DEFAULT_MODS

        if not a.no_patch:
            if not a.utmt.is_file():
                raise HarnessError(EXIT_PREFLIGHT, f"UTMT CLI not found: {a.utmt}")
            h = source_hash(game_dir)
            stamp = game_dir / STAMP
            if a.force_patch or not stamp.is_file() or stamp.read_text() != h \
                    or not (game_dir / "data.win").is_file():
                patch(game_dir, a.utmt)
                stamp.write_text(h)
            else:
                print("sources unchanged, skipping patch", file=sys.stderr)
        elif not (game_dir / "data.win").is_file():
            raise HarnessError(EXIT_PREFLIGHT, "--no-patch but no data.win in game dir")

        # runs: None = plain boot test, else a scenario name
        if a.all:
            runs = [None] + sorted(p.stem for p in SCENARIOS.glob("*.json"))
        elif a.scenario:
            runs = [s.strip() for s in a.scenario.split(",")]
        else:
            runs = [None]
        scns = {name: load_scenario(name) for name in runs if name}  # validate all before launching
        if scns:
            dest = game_dir / "GNX_scenarios"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(SCENARIOS, dest)

        worst, results = EXIT_PASS, []
        guard = guard_player_saves(game_dir)
        try:
            for name in runs:
                sc = scns.get(name, {})
                if name:
                    try:
                        prepare_scenario(game_dir, sc)
                    except HarnessError as e:
                        if not a.all:
                            raise
                        print(f"SCENARIO {name}: SKIP  {e}")  # --all: a missing fixture is not a failure
                        continue
                run_mods = [REPO / m for m in sc["mods"]] if "mods" in sc else mods
                deploy_mods(game_dir, run_mods, accepted)
                r = boot(game_dir, sc.get("timeout", a.timeout), a.keep_open and not name, name, sc.get("expect_dialog"))
                if sc.get("expect_dialog") and not r["dismissed_dialogs"] and r.get("scn"):
                    # the scenario relies on that popup appearing: missing it is a failure
                    r["scn"]["fails"].append("FAIL  expected dialog containing '" + sc["expect_dialog"] + "' never appeared")
                if sc.get("expect_dialog"):  # the expected problem is also logged as a mod error
                    r["mod_errors"] = [m for m in r["mod_errors"] if sc["expect_dialog"] not in m]
                if len(r["dismissed_dialogs"]) > 1 and r.get("scn"):
                    r["scn"]["fails"].append(f"FAIL  expected dialog appeared {len(r['dismissed_dialogs'])} times (should show once per session)")
                r["suite_ignored"] = sc.get("check_boot_suite", True) is False
                if sc.get("save_fixture_as") and HARNESS_SAVE.is_file():
                    # setup scenarios hand their slot-9 save to later scenarios as a fixture
                    (game_dir / "fixtures").mkdir(exist_ok=True)
                    shutil.copy2(HARNESS_SAVE, game_dir / "fixtures" / f"{sc['save_fixture_as']}.json")
                code = verdict(r)
                worst = max(worst, code)  # 4 timeout/crash > 1 fail > 0 pass
                results.append({k: v for k, v in r.items() if k != "tail"} | {"verdict": code})
                if not a.json:
                    report(r, code)
                touched = restore_player_saves(guard)
                if touched:
                    raise HarnessError(EXIT_FAIL, f"run '{name or 'boot'}' modified player save(s) {touched}; "
                                                  "restored from the pre-run copy. Harness must only use slots 8/9.")
        finally:
            HARNESS_SAVE.unlink(missing_ok=True)
            HARNESS_SAVE_B.unlink(missing_ok=True)
            touched = restore_player_saves(guard)  # also after a crash or Ctrl+C mid-run
            if touched:
                print(f"ERROR: player save(s) {touched} were modified and have been restored", file=sys.stderr)
        if a.json:
            print(json.dumps(results if len(results) != 1 else results[0], indent=1))
        return worst
    except HarnessError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
