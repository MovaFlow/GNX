"""Progress window for tools/gnx_test.py. Started by the harness for the whole run (pythonw, no console);
polls the state file the harness writes and shows: overall runs k/N with ETA, what the current run is doing
(self-test / dispatch / scenario steps), and every finished run's verdict. Closes a few seconds after the
harness writes "finished", or when the harness process is gone.

    pythonw tools/gnx_progress_window.py <state.json> <harness pid>
"""
import json
import os
import sys
import tkinter as tk
from tkinter import ttk

STATE = sys.argv[1]
HARNESS_PID = int(sys.argv[2]) if len(sys.argv) > 2 else 0

BG, FG, DIM, OK, BAD, SKIP = "#2b1712", "#f2e6d8", "#b39a86", "#7fc66b", "#e0563b", "#d6b04a"


def harness_alive():
    if not HARNESS_PID:
        return True
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, HARNESS_PID)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == 259  # STILL_ACTIVE
    except Exception:
        return True


root = tk.Tk()
root.title("GNX test harness")
root.configure(bg=BG)
root.attributes("-topmost", True)
root.resizable(False, False)
w, h = 520, 400
root.geometry(f"{w}x{h}+{root.winfo_screenwidth() - w - 24}+40")

style = ttk.Style(root)
style.theme_use("clam")
style.configure("All.Horizontal.TProgressbar", troughcolor="#4a2a20", background="#d6b04a", bordercolor=BG,
                lightcolor="#d6b04a", darkcolor="#d6b04a")
style.configure("Run.Horizontal.TProgressbar", troughcolor="#4a2a20", background="#7fc66b", bordercolor=BG,
                lightcolor="#7fc66b", darkcolor="#7fc66b")

title = tk.Label(root, text="Starting...", bg=BG, fg=FG, font=("Segoe UI", 11, "bold"), anchor="w")
title.pack(fill="x", padx=12, pady=(10, 2))
all_bar = ttk.Progressbar(root, style="All.Horizontal.TProgressbar", maximum=1.0, length=w - 24)
all_bar.pack(padx=12)
eta = tk.Label(root, text="", bg=BG, fg=DIM, font=("Segoe UI", 9), anchor="w")
eta.pack(fill="x", padx=12, pady=(2, 8))

run_name = tk.Label(root, text="", bg=BG, fg=FG, font=("Segoe UI", 10, "bold"), anchor="w")
run_name.pack(fill="x", padx=12)
run_bar = ttk.Progressbar(root, style="Run.Horizontal.TProgressbar", maximum=1.0, length=w - 24)
run_bar.pack(padx=12)
run_what = tk.Label(root, text="", bg=BG, fg=DIM, font=("Consolas", 9), anchor="w", justify="left")
run_what.pack(fill="x", padx=12, pady=(2, 8))

results = tk.Text(root, height=9, bg="#1f100c", fg=FG, font=("Consolas", 9), relief="flat", highlightthickness=0)
results.pack(fill="both", expand=True, padx=12, pady=(0, 12))
for tag, col in (("PASS", OK), ("FAIL", BAD), ("INCOMPLETE", BAD), ("SKIP", SKIP)):
    results.tag_configure(tag, foreground=col)

shown = 0
close_at = None


def poll():
    global shown, close_at
    try:
        with open(STATE, encoding="utf-8") as f:
            s = json.load(f)
    except (OSError, ValueError):
        s = None
    if s:
        n = max(1, s.get("n", 1))
        res = s.get("results", [])
        fails = sum(1 for r in res if r[1] in ("FAIL", "INCOMPLETE"))
        title.config(text=f"{len(res)}/{n} runs done" + (f"   {fails} failed" if fails else ""), fg=BAD if fails else FG)
        all_bar["value"] = len(res) / n
        eta.config(text="   ".join(x for x in (s.get("headline", ""), s.get("eta", "")) if x))
        act = s.get("active", [])
        run_name.config(text=f"Running ({len(act)}):" if act else "")
        run_bar["value"] = sum(a[2] for a in act) / len(act) if act else 0
        run_what.config(text="\n".join(f"{a[0]}  -  {a[1]}" for a in act))
        for name, verdict, detail in res[shown:]:
            results.insert("end", f"{verdict:<5} ", verdict)
            results.insert("end", f"{name}  {detail}\n")
            results.see("end")
        shown = len(res)
        if s.get("finished") and close_at is None:
            title.config(text=("ALL PASSED" if not fails else f"{fails} FAILED") + f"   ({len(res)} runs)",
                         fg=OK if not fails else BAD)
            run_name.config(text="")
            run_what.config(text="")
            run_bar["value"] = 1.0
            all_bar["value"] = 1.0
            close_at = 800 if not fails else 20000  # all green: close at once; failures stay up to be read
            root.after(close_at, root.destroy)
    if close_at is None and not harness_alive():
        root.after(3000, root.destroy)
        close_at = 3000
    root.after(250, poll)


poll()
root.mainloop()
try:
    os.unlink(STATE)
except OSError:
    pass
