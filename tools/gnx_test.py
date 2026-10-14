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
    python tools/gnx_test.py --all            # boot tests + every scenario (parallel, ~100 s)
    python tools/gnx_test.py --all --quick    # skip scenarios marked "slow": true (~65 s)
    python tools/gnx_test.py --all -j 2       # games at once (default: half the CPUs, max 4)

Runs go to worker copies in <game-dir>/workers/wNN whose data.win carries the game name gnx_hrn_wNN, so
each saves to its own %LOCALAPPDATA%/gnx_hrn_wNN folder: games run side by side, the player's goblin_nest
folder is never used (except by --keep-open), and the real game can stay open meanwhile. A progress
window (tools/gnx_progress_window.py) stays on top for the whole run; --no-window / --no-progress.
Run times are kept in <game-dir>/durations.json to schedule the longest runs first.

Scenarios (tools/scenarios/*.json) are played in-game by scr_gnx_scn_step. They use
save slots 9 / 8 in the worker's own save folder; player saves are never read or written. A
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
SAVE_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "goblin_nest"  # the player's saves (and --keep-open runs)
SCENARIOS = REPO / "tools" / "scenarios"
SAVE_SLOTS = {"a": "save_file_a.json", "1": "save_file_1.json", "2": "save_file_2.json", "3": "save_file_3.json"}
EXE = "GoblinNest.exe"
VANILLA = "data.vanilla.win"
STAMP = ".harness_stamp"

EXIT_PASS, EXIT_FAIL, EXIT_PATCH, EXIT_PREFLIGHT, EXIT_TIMEOUT = 0, 1, 2, 3, 4


class Box:
    """One game copy plus the save folder it writes to. Workers run renamed copies of data.win (the game name
    in GEN8 picks the save folder), so several games can run at once without sharing logs or saves, and
    without ever touching the player's goblin_nest folder. `out` is where logs, screenshots and fixtures go."""

    def __init__(self, out, run_dir, save_dir, wid=0):
        self.out, self.run_dir, self.save_dir, self.wid = out, run_dir, save_dir, wid
        self.log = save_dir / "gnx_debug.txt"
        self.scn_log = save_dir / "gnx_scenario.txt"
        self.harness_save = save_dir / "gnx_harness_save.json"
        self.harness_save_b = save_dir / "gnx_harness_save_b.json"  # slot 8, always starts empty
        self.scn_progress = save_dir / "gnx_scn_progress.txt"  # "step/total", written by scr_gnx_scn_step


def make_workers(game_dir, n):
    """Worker game copies in <game_dir>/workers/wNN, each with data.win renamed to gnx_hrn_wNN (same length
    as goblin_nest, patched in place) so it saves to %LOCALAPPDATA%/gnx_hrn_wNN. Refreshed when data.win changes."""
    src = game_dir / "data.win"
    sig = f"{src.stat().st_size}:{src.stat().st_mtime_ns}"
    data = None
    boxes = []
    for i in range(1, n + 1):
        name = f"gnx_hrn_w{i:02d}"
        wd = game_dir / "workers" / f"w{i:02d}"
        wd.mkdir(parents=True, exist_ok=True)
        for f in (EXE, "options.ini"):
            if (game_dir / f).is_file() and not (wd / f).is_file():
                shutil.copy2(game_dir / f, wd / f)
        stamp = wd / ".data_sig"
        if not stamp.is_file() or stamp.read_text() != sig or not (wd / "data.win").is_file():
            if data is None:
                data = bytearray(src.read_bytes())
                gen8 = data.find(b"GEN8")
                off = int.from_bytes(data[gen8 + 12:gen8 + 16], "little")  # GEN8 FileName (also the game name)
                if data[off:off + 11] != b"goblin_nest":
                    raise HarnessError(EXIT_PREFLIGHT, f"data.win game name is {bytes(data[off:off + 11])!r}, "
                                                       "expected goblin_nest: cannot make isolated workers")
            data[off:off + 11] = name.encode()
            (wd / "data.win").write_bytes(data)
            stamp.write_text(sig)
        save_dir = SAVE_DIR.parent / name
        save_dir.mkdir(exist_ok=True)
        boxes.append(Box(game_dir, wd, save_dir, i))
    return boxes


def fmt_left(s):
    return f"~{int(s // 60)}:{int(s % 60):02d} left"


class Progress:
    """Live progress: a window (tools/gnx_progress_window.py, always on top, for the whole run) and, in a
    terminal, one status line on stderr. Shows runs done/N with ETA, what each worker is doing (boot self-test,
    dispatch check, scenario steps) and every finished run's verdict. Thread-safe (one thread per worker)."""

    def __init__(self, line=False, window=False):
        import threading
        self.lock = threading.Lock()
        self.line, self.window = line, window
        self.on = line or window
        self.uni = line and "utf" in (getattr(sys.stderr, "encoding", "") or "").lower()
        self.n, self.workers, self.results = 0, 1, []
        self.active = {}  # wid -> [name, what, frac, t_start, estimate]
        self.pending_est = 0.0
        self.headline = ""
        self.state = Path(tempfile.gettempdir()) / f"gnx_harness_progress_{os.getpid()}.json"
        if window:
            pyw = Path(sys.executable).with_name("pythonw.exe")
            try:
                subprocess.Popen([str(pyw if pyw.is_file() else sys.executable),
                                  str(Path(__file__).with_name("gnx_progress_window.py")),
                                  str(self.state), str(os.getpid())])
            except OSError:
                self.window = False

    def plan(self, n, workers, pending_est):
        with self.lock:
            self.n, self.workers, self.pending_est = n, workers, pending_est
            self._show()

    def start(self, wid, name, est):
        with self.lock:
            self.pending_est = max(0.0, self.pending_est - est)
            self.active[wid] = [name or "boot tests", "starting", 0.0, time.time(), est]
            self._show()

    def result(self, wid, name, verdict, detail=""):
        with self.lock:
            self.active.pop(wid, None)
            self.results.append([name or "boot tests", verdict, detail])
            self._show()

    def finish(self):
        with self.lock:
            self.active.clear()
            self._clear()
            self._write(finished=True)

    def bar(self, frac, width):
        full, empty = ("█", "░") if self.uni else ("#", "-")
        filled = int(round(max(0.0, min(1.0, frac)) * width))
        return full * filled + empty * (width - filled)

    def tick(self, wid, box, log_text, scn_text):
        if not self.on:
            return
        selftest = len(re.findall(r"^\[GNX-TEST\] (?:PASS|FAIL|SKIP)  T", log_text, re.M))
        droute = len(re.findall(r"DROUTE", log_text))
        bad = len(re.findall(r"^\[GNX-(?:TEST|SCN)\] FAIL", log_text + "\n" + scn_text, re.M))
        what, frac = "booting the game", 0.05
        if selftest:
            what, frac = f"self-test {selftest}", 0.3
        if droute:
            what, frac = f"self-test {selftest}, dispatch {droute}", 0.6
        try:
            step, total = (int(x) for x in box.scn_progress.read_text().split("/"))
        except (OSError, ValueError):
            step = total = 0
        if total:
            ok = len(re.findall(r"^\[GNX-SCN\] PASS", scn_text, re.M))
            what, frac = f"step {step}/{total}, {ok} ok", step / total
        if bad:
            what += f", {bad} FAIL"
        with self.lock:
            if wid in self.active:
                self.active[wid][1:3] = [what, frac]
            self._show()

    def _eta(self, now):
        if not self.n:
            return ""
        running = sum(max(0.0, a[4] - (now - a[3])) for a in self.active.values())
        return fmt_left((self.pending_est + running) / max(1, self.workers)) if self.pending_est + running > 0 else ""

    def _show(self):
        now = time.time()
        if self.window:
            self._write()
        if self.line:
            done = len(self.results)
            act = "  ".join(f"{a[0]} {self.bar(a[2], 6)}" for a in self.active.values())
            line = f"[{done}/{self.n}] {self.bar(done / max(1, self.n), 16)} {act}  {self._eta(now)}"
            width = shutil.get_terminal_size((100, 20)).columns - 1
            sys.stderr.write("\r" + line[:width].ljust(width))
            sys.stderr.flush()

    def _write(self, finished=False):
        if not self.window:
            return
        now = time.time()
        act = [[a[0], f"{a[1]}  ({now - a[3]:.0f}s)", a[2]] for _, a in sorted(self.active.items())]
        tmp = self.state.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps({"n": self.n, "workers": self.workers, "headline": self.headline,
                                       "active": act, "eta": self._eta(now), "results": self.results,
                                       "finished": finished}), encoding="utf-8")
            os.replace(tmp, self.state)
        except OSError:
            pass

    def note(self, headline):
        with self.lock:
            self.headline = headline
            self._show()

    def _clear(self):
        if self.line:
            width = shutil.get_terminal_size((100, 20)).columns - 1
            sys.stderr.write("\r" + " " * width + "\r")
            sys.stderr.flush()

    def clear(self):
        with self.lock:
            self._clear()


PROGRESS = Progress(False)


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


def deploy_mods(game_dir, mods, accepted, allow_incompatible=False):
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
        if not set(vers) & set(accepted) and not allow_incompatible:
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


def boot(box, timeout, keep_open, scenario=None, expect_dialog=None):
    """Launch once. Plain boot: -gnx-autotest, game exits after the boot tests.
    Scenario: -gnx-scenario NAME, game exits when the scenario writes DONE."""
    box.log.unlink(missing_ok=True)  # the game truncates it at boot anyway; this makes stale logs impossible
    box.scn_log.unlink(missing_ok=True)
    box.scn_progress.unlink(missing_ok=True)
    for f in box.save_dir.glob("gnx_shot_*.png"):
        f.unlink()
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 7  # SW_SHOWMINNOACTIVE: don't steal focus
    # -gnx-autotest / -gnx-scenario are read in scr_create_initials (s_initials.gml)
    args = [str(box.run_dir / EXE)]
    if scenario:
        args += ["-gnx-scenario", scenario]
    elif not keep_open:
        args += ["-gnx-autotest"]
    proc = subprocess.Popen(args, cwd=box.run_dir, startupinfo=si)
    t0 = time.time()
    r, crash, done_at = parse_log(""), None, None
    dismissed, seen_dialogs = [], set()
    try:
        while time.time() - t0 < timeout:
            time.sleep(0.25)
            log_text = box.log.read_text(encoding="utf-8", errors="replace") if box.log.is_file() else ""
            if log_text:
                r = parse_log(log_text)
            if PROGRESS.on:
                PROGRESS.tick(box.wid, box, log_text,
                              box.scn_log.read_text(encoding="utf-8", errors="replace") if box.scn_log.is_file() else "")
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
    text = box.log.read_text(encoding="utf-8", errors="replace") if box.log.is_file() else ""
    boot_s, exit_code = r["boot_s"], r["exit_code"]
    r = parse_log(text)  # final read: the game may have written its last lines right before exiting
    if crash:
        crash = crash[:2]  # hwnd is meaningless after the run (and not JSON)
    r.update(boot_s=boot_s, exit_code=exit_code, crash=crash, dismissed_dialogs=dismissed, kept_open=keep_open,
             tail=text.splitlines()[-40:], scenario=scenario)
    game_dir = box.out
    (game_dir / ("last_run.log" if not scenario else f"last_debug_{scenario}.log")).write_text(text, encoding="utf-8")
    if scenario:
        stext = box.scn_log.read_text(encoding="utf-8", errors="replace") if box.scn_log.is_file() else ""
        r["scn"] = parse_scn(stext)
        (game_dir / f"last_scenario_{scenario}.log").write_text(stext, encoding="utf-8")
        shots = sorted(box.save_dir.glob("gnx_shot_*.png"))
        if shots:  # screenshots taken by the scenario's "screenshot" steps
            out = game_dir / "screens" / scenario
            shutil.rmtree(out, ignore_errors=True)
            out.mkdir(parents=True, exist_ok=True)
            for f in shots:
                shutil.move(str(f), out / f.name[len("gnx_shot_"):])
            r["screens"] = [str(out / f.name[len("gnx_shot_"):]) for f in shots]
        if not r["scn"]["done"]:  # keep evidence of incomplete runs; later runs overwrite last_*.log
            stamp = time.strftime("%Y%m%d_%H%M%S")
            (game_dir / f"incomplete_{scenario}_{stamp}.log").write_text(text + "\n\n" + stext, encoding="utf-8")
    return r


def report(r, code):
    PROGRESS.clear()
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


def prepare_scenario(box, sc):
    """Seed save slot 9 from the scenario's fixture, or clear it for a fresh game."""
    for m in sc.get("mods", []):  # local-only mods (harness_game/test_mods) may be absent: SKIP under --all
        if not (REPO / m / "manifest.json").is_file():
            raise HarnessError(EXIT_PREFLIGHT, f"mod '{m}' missing")
    for f in sc.get("local_files", []):  # files the repo must not ship (e.g. audio), copied from local mods
        if not (REPO / f["from"]).is_file():
            raise HarnessError(EXIT_PREFLIGHT, f"local file '{f['from']}' missing")
    if box.save_dir != SAVE_DIR:  # worker folders only: never the player's
        for slot_file in SAVE_SLOTS.values():
            (box.save_dir / slot_file).unlink(missing_ok=True)
        # the mod menu's off-list (game-wide setting in the save folder): empty unless the scenario sets one
        (box.save_dir / "gnx_mods_off.json").unlink(missing_ok=True)
        if sc.get("mods_off"):
            (box.save_dir / "gnx_mods_off.json").write_text(json.dumps(sc["mods_off"]), encoding="utf-8")
        for slot, spec in sc.get("player_slots", {}).items():
            # {"player_slots": {"1": {"fixture": "modded", "on_map": "harness_map"}}}: what the load page lists
            fsrc = box.out / "fixtures" / f"{spec['fixture']}.json"
            if not fsrc.is_file():
                raise HarnessError(EXIT_PREFLIGHT, f"fixture '{spec['fixture']}' missing ({fsrc})")
            data = json.loads(fsrc.read_text(encoding="utf-8-sig"))
            if spec.get("on_map"):
                data["gnx_active_map"] = spec["on_map"]
                data["gnx_maps"] = {"vanilla": "fresh"}
            (box.save_dir / SAVE_SLOTS[slot]).write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    elif sc.get("player_slots"):
        raise HarnessError(EXIT_PREFLIGHT, "player_slots needs a worker (not --keep-open): it writes save slots")
    fx = sc.get("fixture")
    if fx:
        src = box.out / "fixtures" / f"{fx}.json"
        if not src.is_file():
            raise HarnessError(EXIT_PREFLIGHT, f"fixture '{fx}' missing ({src}); "
                                               f"create it with --capture-fixture <slot> {fx}")
        if sc.get("fixture_on_map"):
            # play the fixture's nest as the live state of a mod map; the village waits as a fresh map
            data = json.loads(src.read_text(encoding="utf-8-sig"))
            data["gnx_active_map"] = sc["fixture_on_map"]
            data["gnx_maps"] = {"vanilla": "fresh"}
            box.harness_save.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        else:
            shutil.copy2(src, box.harness_save)
    else:
        box.harness_save.unlink(missing_ok=True)
    box.harness_save_b.unlink(missing_ok=True)


def plan_jobs(runs, scns):
    """Group runs into jobs for the worker pool. A scenario whose fixture another scenario produces
    ("save_fixture_as") must run after it on the same worker: such chains become one job, in run order."""
    producer = {scns[n]["save_fixture_as"]: n for n in runs if n and scns[n].get("save_fixture_as")}
    job_of, jobs = {}, []
    for n in runs:
        dep = producer.get(scns[n].get("fixture")) if n else None
        if dep is not None and dep in job_of:  # (None is the boot run, never a producer)
            job_of[n] = job_of[dep]
            job_of[n].append(n)
        else:
            job_of[n] = [n]
            jobs.append(job_of[n])
    return jobs


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
    ap.add_argument("--no-progress", action="store_true", help="no progress window and no progress line")
    ap.add_argument("--no-window", action="store_true", help="no progress window (the terminal line still shows)")
    ap.add_argument("--scenario", help="comma-separated scenario names from tools/scenarios/")
    ap.add_argument("--all", action="store_true", help="boot tests, then every scenario")
    ap.add_argument("-j", "--jobs", type=int, default=max(1, min(4, (os.cpu_count() or 2) // 2)),
                    help="games run at once, each in its own copy and save folder (default: half the CPUs, max 4)")
    ap.add_argument("--quick", action="store_true", help="skip scenarios marked \"slow\": true")
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
        if a.keep_open and game_running():  # only --keep-open uses the normal save folder; workers are isolated
            raise HarnessError(EXIT_PREFLIGHT, f"{EXE} is already running; close it first "
                                               "(it shares the debug log and saves)")
        for p in (game_dir / EXE, game_dir / VANILLA):
            if not p.is_file():
                raise HarnessError(EXIT_PREFLIGHT, f"{p} missing; run with --init <vanilla game dir>")
        accepted = accepted_versions()
        mods = [Path(m.strip()) for m in a.mods.split(",")] if a.mods else DEFAULT_MODS

        global PROGRESS
        PROGRESS = Progress(line=sys.stderr.isatty() and not a.json and not a.no_progress,
                            window=not a.json and not a.no_progress and not a.no_window)
        PROGRESS.note("checking / patching data.win")
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
        if a.quick:
            slow = [n for n in runs if n and scns[n].get("slow")]
            runs = [n for n in runs if n not in slow]
            if slow:
                print(f"--quick: skipping {len(slow)} slow scenario(s): {', '.join(slow)}", file=sys.stderr)
        jobs = plan_jobs(runs, scns)
        durations_file = game_dir / "durations.json"
        try:
            known = json.loads(durations_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            known = {}
        est = lambda n: known.get(n or "boot", 6.0)
        jobs.sort(key=lambda j: -sum(est(n) for n in j))  # longest first: the pool finishes together

        if a.keep_open:
            boxes = [Box(game_dir, game_dir, SAVE_DIR)]  # a game left open for you uses your normal folders
        else:
            boxes = make_workers(game_dir, max(1, min(a.jobs, len(jobs))))
        if scns:
            for b in boxes:
                dest = b.run_dir / "GNX_scenarios"
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(SCENARIOS, dest)
        PROGRESS.plan(len(runs), len(boxes), sum(est(n) for n in runs))
        PROGRESS.note(f"{len(runs)} runs on {len(boxes)} worker(s)")

        import queue
        import threading
        todo = queue.Queue()
        for j in jobs:
            todo.put(j)
        out_lock = threading.Lock()
        results, failure = {}, []

        def run_one(box, name):
            sc = scns.get(name, {})
            PROGRESS.start(box.wid, name, est(name))
            if name:
                try:
                    prepare_scenario(box, sc)
                except HarnessError as e:
                    if not a.all:
                        raise
                    PROGRESS.result(box.wid, name, "SKIP", str(e)[:60])
                    with out_lock:
                        PROGRESS.clear()
                        print(f"SCENARIO {name}: SKIP  {e}")  # --all: a missing fixture is not a failure
                    return
            run_mods = [REPO / m for m in sc["mods"]] if "mods" in sc else mods
            deploy_mods(box.run_dir, run_mods, accepted, sc.get("allow_incompatible", False))
            for f in sc.get("local_files", []):
                # {"local_files": [{"from": "harness_game/test_mods/x/sounds/a.ogg", "to": "my_mod/sounds/a.ogg"}]}
                dst = box.run_dir / "GNX_mods" / f["to"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO / f["from"], dst)
            r = boot(box, sc.get("timeout", a.timeout), a.keep_open and not name, name, sc.get("expect_dialog"))
            if sc.get("expect_dialog") and not r["dismissed_dialogs"] and r.get("scn"):
                # the scenario relies on that popup appearing: missing it is a failure
                r["scn"]["fails"].append("FAIL  expected dialog containing '" + sc["expect_dialog"] + "' never appeared")
            if sc.get("expect_dialog"):  # the expected problem is also logged as a mod error
                r["mod_errors"] = [m for m in r["mod_errors"] if sc["expect_dialog"] not in m]
            if len(r["dismissed_dialogs"]) > 1 and r.get("scn"):
                r["scn"]["fails"].append(f"FAIL  expected dialog appeared {len(r['dismissed_dialogs'])} times (should show once per session)")
            r["suite_ignored"] = sc.get("check_boot_suite", True) is False
            if sc.get("save_fixture_as") and box.harness_save.is_file():
                # setup scenarios hand their slot-9 save to later scenarios as a fixture
                (game_dir / "fixtures").mkdir(exist_ok=True)
                shutil.copy2(box.harness_save, game_dir / "fixtures" / f"{sc['save_fixture_as']}.json")
            code = verdict(r)
            if r.get("scn") is not None:
                state = "PASS" if code == EXIT_PASS else "FAIL" if r["scn"]["done"] else "INCOMPLETE"
                PROGRESS.result(box.wid, name, state, f"{r['scn']['pass']}/{r['scn']['total']}  {r['boot_s']}s")
            else:
                PROGRESS.result(box.wid, name, "PASS" if code == EXIT_PASS else "FAIL",
                                f"suite {r.get('suite_pass')}/{r.get('suite_total')}  {r['boot_s']}s")
            if code in (EXIT_PASS, EXIT_FAIL) and r.get("boot_s"):
                known[name or "boot"] = r["boot_s"]
            with out_lock:
                results[name] = {k: v for k, v in r.items() if k != "tail"} | {"verdict": code}
                if not a.json:
                    report(r, code)

        def worker(box):
            while not failure:
                try:
                    job = todo.get_nowait()
                except queue.Empty:
                    return
                for name in job:  # a fixture chain runs in order on one worker
                    try:
                        run_one(box, name)
                    except HarnessError as e:
                        # this run could not start: report it as failed and keep going with the others
                        PROGRESS.result(box.wid, name, "FAIL", str(e)[:60])
                        with out_lock:
                            PROGRESS.clear()
                            print(f"SCENARIO {name or 'boot'}: FAIL  could not run: {e}")
                            results[name] = {"scenario": name, "verdict": EXIT_FAIL, "error": str(e)}
                    except Exception as e:  # keep the other workers' results; report this one
                        failure.append(HarnessError(EXIT_TIMEOUT, f"run '{name or 'boot'}': {type(e).__name__}: {e}"))
                        return

        guard = guard_player_saves(game_dir)
        try:
            threads = [threading.Thread(target=worker, args=(b,), daemon=True) for b in boxes]
            for t in threads:
                t.start()
            for t in threads:
                while t.is_alive():
                    t.join(0.5)  # short joins keep Ctrl+C working
        finally:
            PROGRESS.finish()
            for b in boxes:
                if b.save_dir != SAVE_DIR:
                    b.harness_save.unlink(missing_ok=True)
                    b.harness_save_b.unlink(missing_ok=True)
            touched = restore_player_saves(guard)  # workers never write there; checked anyway
            if touched:
                print(f"ERROR: player save(s) {touched} were modified and have been restored", file=sys.stderr)
                failure.append(HarnessError(EXIT_FAIL, f"player save(s) {touched} modified (restored)"))
            try:
                durations_file.write_text(json.dumps(known, indent=0, sort_keys=True), encoding="utf-8")
            except OSError:
                pass
        if failure:
            raise failure[0]
        ordered = [results[n] for n in runs if n in results]
        worst = max([r["verdict"] for r in ordered] or [EXIT_PASS])  # 4 timeout/crash > 1 fail > 0 pass
        if a.json:
            print(json.dumps(ordered if len(ordered) != 1 else ordered[0], indent=1))
        return worst
    except HarnessError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
