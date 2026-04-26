#!/usr/bin/env python3
from __future__ import annotations
import json
import shutil
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import wlmp_offline_tool as core
from app_settings import load_settings

SETTINGS = load_settings()
APP_TITLE = SETTINGS.app_title
LOGO_PATH = Path(SETTINGS.logo_path)
SUCCESS_IMAGE_PATH = Path("assets/success_dude.png")
LIMITATION_TEXT = (
    "Important: WLMP files are project files. This app validates and converts renderable media outputs "
    "(such as WMV/MOV exports) to MP4."
)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x740")
        self.configure(bg="#f5f6f7")
        self.logo_image = None
        self._build()

    def _build(self):
        header = tk.Frame(self, bg="#111827")
        header.pack(fill="x")
        tk.Label(header, text=APP_TITLE, font=("Segoe UI", 16, "bold"), fg="white", bg="#111827", pady=12).pack()

        tk.Label(
            self, text=LIMITATION_TEXT, font=("Segoe UI", 10, "bold"),
            bg="#fff7ed", fg="#9a3412", wraplength=930, justify="center", pady=8
        ).pack(fill="x", padx=20, pady=(10, 0))

        top = tk.Frame(self, bg="#f5f6f7")
        top.pack(fill="x", padx=20, pady=(8, 0))
        tk.Button(top, text="Run First-Run Health Check", command=self.health).pack(anchor="w")

        body = tk.Frame(self, bg="#f5f6f7")
        body.pack(fill="both", expand=True, padx=20, pady=20)
        nb = ttk.Notebook(body)
        nb.pack(fill="both", expand=True)

        nb.add(PackageTab(nb), text="1) Build Package")
        nb.add(ValidateTab(nb), text="2) Validate Package")
        nb.add(ConvertTab(nb), text="3) Admin Best Quality")

    def health(self):
        checks = []
        checks.append(f"Logo file: {'OK' if LOGO_PATH.exists() else 'MISSING'} ({LOGO_PATH})")
        checks.append(f"ffmpeg on PATH: {'OK' if shutil.which('ffmpeg') else 'MISSING'}")
        t = Path("healthcheck_write_test.tmp")
        try:
            t.write_text("ok", encoding="utf-8")
            t.unlink(missing_ok=True)
            checks.append("Output directory write test: OK")
        except Exception:
            checks.append("Output directory write test: FAILED")
        messagebox.showinfo("Health Check", "\n".join(checks))

class BaseTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.status = tk.StringVar(value="Ready")

    def row(self, label, var, browse):
        r = tk.Frame(self, bg="white")
        r.pack(fill="x", padx=20, pady=8)
        tk.Label(r, text=label, width=20, anchor="w", bg="white", font=("Segoe UI", 11)).pack(side="left")
        tk.Entry(r, textvariable=var, font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Button(r, text="Browse", command=browse, width=10).pack(side="left")

    def status_line(self):
        tk.Label(self, textvariable=self.status, bg="white", fg="#1f2937", font=("Segoe UI", 10, "italic")).pack(
            fill="x", padx=20, pady=(10, 16)
        )

    def set_status(self, text): self.after(0, lambda: self.status.set(text))
    def info(self, title, text): self.after(0, lambda: messagebox.showinfo(title, text))
    def warn(self, title, text): self.after(0, lambda: messagebox.showwarning(title, text))
    def err(self, title, text): self.after(0, lambda: messagebox.showerror(title, text))
    def run_async(self, fn): threading.Thread(target=fn, daemon=True).start()

class PackageTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        tk.Label(self, text="Build a Shareable School Package", font=("Segoe UI", 15, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(18, 8)
        )
        self.w = tk.StringVar()
        self.m = tk.StringVar()
        self.o = tk.StringVar()
        self.row("WLMP File", self.w, self.pick_w)
        self.row("Media Folder", self.m, self.pick_m)
        self.row("Output ZIP", self.o, self.pick_o)
        tk.Button(self, text="Create Package ZIP", font=("Segoe UI", 11, "bold"), command=self.go).pack(
            anchor="w", padx=20, pady=(8, 0)
        )
        self.status_line()

    def pick_w(self):
        p = filedialog.askopenfilename(filetypes=[("WLMP Project", "*.wlmp"), ("All files", "*.*")])
        if p: self.w.set(p)

    def pick_m(self):
        p = filedialog.askdirectory()
        if p: self.m.set(p)

    def pick_o(self):
        p = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP Archive", "*.zip")])
        if p: self.o.set(p)

    def go(self):
        wlmp, media, out = Path(self.w.get().strip()), Path(self.m.get().strip()), Path(self.o.get().strip())
        def worker():
            self.set_status("Creating package...")
            try:
                c = core.package_project(wlmp, media, out)
                self.set_status(f"Package created with {c} media files: {out}")
                self.info("Done", f"Package created:\n{out}")
            except Exception as e:
                self.set_status(f"Error: {e}")
                self.err("Package Error", str(e))
        self.run_async(worker)

class ValidateTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        tk.Label(self, text="Validate Package Before Sharing", font=("Segoe UI", 15, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(18, 8)
        )
        self.p = tk.StringVar()
        self.r = tk.StringVar()
        self.row("Package ZIP", self.p, self.pick_p)
        self.row("JSON Report", self.r, self.pick_r)
        tk.Button(self, text="Run Validation", font=("Segoe UI", 11, "bold"), command=self.go).pack(
            anchor="w", padx=20, pady=(8, 0)
        )
        self.status_line()

    def pick_p(self):
        p = filedialog.askopenfilename(filetypes=[("ZIP Archive", "*.zip"), ("All files", "*.*")])
        if p: self.p.set(p)

    def pick_r(self):
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON File", "*.json")])
        if p: self.r.set(p)

    def go(self):
        pkg, report = Path(self.p.get().strip()), self.r.get().strip()
        def worker():
            self.set_status("Validating package...")
            try:
                res = core.validate_package(pkg)
                summary = f"Referenced: {len(res.referenced_paths)} | Found: {len(res.found_paths)} | Missing: {len(res.missing_paths)}"
                if report:
                    rp = Path(report)
                    rp.parent.mkdir(parents=True, exist_ok=True)
                    rp.write_text(json.dumps(core._result_to_json_payload(res), indent=2), encoding="utf-8")
                if res.missing_paths:
                    self.set_status(f"Validation completed with missing files. {summary}")
                    self.warn("Missing Media Found", f"{summary}\n\nExamples:\n" + "\n".join(res.missing_paths[:15]))
                else:
                    self.set_status(f"Validation passed. {summary}")
                    self.info("Validation Passed", summary)
            except Exception as e:
                self.set_status(f"Error: {e}")
                self.err("Validation Error", str(e))
        self.run_async(worker)

class ConvertTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        tk.Label(self, text="Admin Best Quality Conversion (Fixed Preset)", font=("Segoe UI", 15, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(18, 8)
        )
        self.i = tk.StringVar()
        self.o = tk.StringVar()
        self.f = tk.StringVar(value="ffmpeg")
        self.row("Input Media", self.i, self.pick_i)
        self.row("Output MP4", self.o, self.pick_o)

        r = tk.Frame(self, bg="white")
        r.pack(fill="x", padx=20, pady=8)
        tk.Label(r, text="FFmpeg Binary", width=20, anchor="w", bg="white", font=("Segoe UI", 11)).pack(side="left")
        tk.Entry(r, textvariable=self.f, font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True)

        tk.Label(
            self, text="Preset locked to: best (CRF 14, veryslow, AAC 320k)",
            bg="white", fg="#1f2937", font=("Segoe UI", 10, "italic")
        ).pack(anchor="w", padx=20, pady=(2, 8))

        tk.Button(self, text="Start Admin Best Quality Conversion", font=("Segoe UI", 11, "bold"), command=self.go).pack(
            anchor="w", padx=20, pady=(8, 0)
        )
        self.status_line()

    def pick_i(self):
        p = filedialog.askopenfilename(filetypes=[("Media Files", "*.*")])
        if p: self.i.set(p)

    def pick_o(self):
        p = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4"), ("All files", "*.*")])
        if p: self.o.set(p)

    def _celebrate(self, out: Path, log: Path):
        def ui():
            w = tk.Toplevel(self)
            w.title("Conversion Complete")
            w.configure(bg="white")
            tk.Label(w, text="Now thats a good looking dude 😉", font=("Segoe UI", 16, "bold"), bg="white", fg="#111827", pady=10).pack()
            if SUCCESS_IMAGE_PATH.exists():
                try:
                    img = tk.PhotoImage(file=str(SUCCESS_IMAGE_PATH))
                    sx = max(1, (img.width() + 419) // 420)
                    sy = max(1, (img.height() + 319) // 320)
                    s = max(sx, sy)
                    if s > 1: img = img.subsample(s, s)
                    l = tk.Label(w, image=img, bg="white")
                    l.image = img
                    l.pack(padx=12, pady=8)
                except tk.TclError:
                    tk.Label(w, text="Success image exists but could not be loaded by Tkinter PhotoImage.", bg="white", fg="#b45309").pack(padx=12, pady=8)
            else:
                tk.Label(w, text="Add assets/success_dude.png to show the completion photo.", bg="white", fg="#b45309").pack(padx=12, pady=8)
            tk.Label(w, text=f"Conversion complete:\n{out}\n\nLog: {log}", bg="white", fg="#1f2937", justify="left", padx=12, pady=8).pack()
            tk.Button(w, text="Awesome", command=w.destroy).pack(pady=(0, 12))
        self.after(0, ui)

    def go(self):
        inp, out, ff = Path(self.i.get().strip()), Path(self.o.get().strip()), (self.f.get().strip() or "ffmpeg")
        def worker():
            self.set_status("Converting in Admin Best Quality mode...")
            log = _log_path()
            try:
                cmd = core.ffmpeg_command(inp, out, "best", ff)
                _log_write(log, "START", inp, out, "best", cmd, None)
                core.run_conversion(inp, out, "best", ff)
                _log_write(log, "SUCCESS", inp, out, "best", cmd, None)
                self.set_status(f"Conversion complete: {out}")
                self._celebrate(out, log)
            except Exception as e:
                _log_write(log, "ERROR", inp, out, "best", [], str(e))
                self.set_status(f"Error: {e}")
                self.err("Conversion Error", f"{e}\n\nLog: {log}")
        self.run_async(worker)

def _log_path() -> Path:
    d = Path("logs")
    d.mkdir(parents=True, exist_ok=True)
    return d / f"conversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def _log_write(path: Path, status: str, inp: Path, out: Path, mode: str, cmd: list[str], err: str | None):
    lines = [
        f"timestamp={datetime.now().isoformat()}",
        f"status={status}",
        f"input={inp}",
        f"output={out}",
        f"mode={mode}",
    ]
    if cmd:
        lines.append("command=" + " ".join(cmd))
    if err:
        lines.append(f"error={err}")
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n\n")

if __name__ == "__main__":
    App().mainloop()
