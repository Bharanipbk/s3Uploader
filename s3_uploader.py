"""
S3 Upload Desktop Application
Simple, compact UI — no scrolling, two inputs per row.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
import queue

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
except ImportError:
    print("boto3 is not installed. Run: pip install boto3")
    sys.exit(1)


# ─── Theme ───────────────────────────────────────────────────────────────────
BG       = "#1e1e2e"
BG_CARD  = "#282840"
BG_INPUT = "#1c1c30"
FG       = "#cdd6f4"
FG_DIM   = "#6c7086"
ACCENT   = "#89b4fa"
GREEN    = "#a6e3a1"
RED      = "#f38ba8"
YELLOW   = "#f9e2af"
BORDER   = "#45475a"
FONT     = ("Segoe UI", 10)
FONT_B   = ("Segoe UI", 10, "bold")
FONT_SM  = ("Consolas", 9)
FONT_H   = ("Segoe UI", 16, "bold")


# ─── Application ─────────────────────────────────────────────────────────────

class S3UploaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("☁  S3 Uploader")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.is_uploading = False
        self.cancel_flag = threading.Event()
        self.log_queue = queue.Queue()

        self._build_ui()
        self._poll_queue()

    # ── Build UI ─────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = dict(padx=14, pady=6)
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # Header
        tk.Label(main, text="☁  S3 Uploader", font=FONT_H, bg=BG, fg=ACCENT).pack(anchor="w")
        tk.Frame(main, bg=BORDER, height=1).pack(fill="x", pady=(4, 10))

        # ── Row 1: Access Key + Secret Key ──
        row1 = tk.Frame(main, bg=BG)
        row1.pack(fill="x", pady=4)
        self.access_key = self._input(row1, "Access Key ID", side="left", expand=True)
        self.secret_key = self._input(row1, "Secret Access Key", side="left", expand=True, show="•")

        # ── Row 2: Bucket + Region ──
        row2 = tk.Frame(main, bg=BG)
        row2.pack(fill="x", pady=4)
        self.bucket = self._input(row2, "Bucket Name", side="left", expand=True)
        self.region = self._input(row2, "Region (default: us-east-1)", side="left", expand=True)

        # ── Row 3: Prefix + Folder ──
        row3 = tk.Frame(main, bg=BG)
        row3.pack(fill="x", pady=4)
        self.prefix = self._input(row3, "Key Prefix (optional)", side="left", expand=True)

        folder_frame = tk.Frame(row3, bg=BG)
        folder_frame.pack(side="left", fill="x", expand=True, padx=(6, 0))
        tk.Label(folder_frame, text="Source Folder", font=FONT_B, bg=BG, fg=FG).pack(anchor="w")
        btn_row = tk.Frame(folder_frame, bg=BG)
        btn_row.pack(fill="x")
        self.folder_var = tk.StringVar(value="No folder selected")
        tk.Label(btn_row, textvariable=self.folder_var, font=FONT_SM, bg=BG_INPUT,
                 fg=FG_DIM, anchor="w", padx=6, pady=5, relief="flat",
                 borderwidth=1, highlightbackground=BORDER, highlightthickness=1
                 ).pack(side="left", fill="x", expand=True)
        tk.Button(btn_row, text="📁 Browse", font=FONT, bg=BG_CARD, fg=FG,
                  activebackground=BORDER, activeforeground=FG, bd=0,
                  padx=10, pady=3, command=self._browse, cursor="hand2"
                  ).pack(side="right", padx=(6, 0))

        # ── Buttons ──
        btn_frame = tk.Frame(main, bg=BG)
        btn_frame.pack(fill="x", pady=(12, 6))

        self.upload_btn = tk.Button(
            btn_frame, text="🚀  Upload to S3", font=FONT_B,
            bg=ACCENT, fg="#1e1e2e", activebackground="#74c7ec",
            bd=0, padx=20, pady=6, cursor="hand2", command=self._start_upload
        )
        self.upload_btn.pack(side="left")

        self.cancel_btn = tk.Button(
            btn_frame, text="✖ Cancel", font=FONT_B,
            bg=RED, fg="#1e1e2e", activebackground="#eba0ac",
            bd=0, padx=14, pady=6, state="disabled", command=self._cancel_upload
        )
        self.cancel_btn.pack(side="left", padx=(10, 0))

        # Status + counter
        stat_row = tk.Frame(main, bg=BG)
        stat_row.pack(fill="x", pady=(2, 0))
        self.status_var = tk.StringVar(value="Ready")
        self.status_lbl = tk.Label(stat_row, textvariable=self.status_var, font=FONT_B, bg=BG, fg=ACCENT)
        self.status_lbl.pack(side="left")
        self.counter_var = tk.StringVar()
        tk.Label(stat_row, textvariable=self.counter_var, font=FONT_SM, bg=BG, fg=FG_DIM).pack(side="right")

        # Progress bar
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("c.Horizontal.TProgressbar", troughcolor=BG_INPUT,
                        background=ACCENT, thickness=6, bordercolor=BG, lightcolor=ACCENT, darkcolor=ACCENT)
        self.progress = ttk.Progressbar(main, style="c.Horizontal.TProgressbar", maximum=100)
        self.progress.pack(fill="x", pady=(4, 6))

        # ── Log Area ──
        log_border = tk.Frame(main, bg=BORDER, padx=1, pady=1)
        log_border.pack(fill="both", expand=True)
        self.log_text = tk.Text(
            log_border, font=FONT_SM, bg=BG_INPUT, fg=FG_DIM,
            relief="flat", bd=0, padx=8, pady=6, height=10, wrap="word",
            insertbackground=ACCENT, state="disabled"
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(log_border, orient="vertical", command=self.log_text.yview
                       ).pack(side="right", fill="y")
        self.log_text.tag_config("ok", foreground=GREEN)
        self.log_text.tag_config("err", foreground=RED)
        self.log_text.tag_config("warn", foreground=YELLOW)
        self.log_text.tag_config("info", foreground=ACCENT)

    # ── Helper: labelled entry ───────────────────────────────────────────

    def _input(self, parent, label, side="left", expand=False, show=""):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(side=side, fill="x", expand=expand, padx=(0 if side == "left" and not expand else 0, 0))
        if side == "left" and expand:
            frame.pack_configure(padx=(0, 6))
        tk.Label(frame, text=label, font=FONT_B, bg=BG, fg=FG).pack(anchor="w")
        entry = tk.Entry(
            frame, font=FONT, bg=BG_INPUT, fg=FG,
            insertbackground=ACCENT, relief="flat", bd=0,
            highlightbackground=BORDER, highlightthickness=1,
            highlightcolor=ACCENT, show=show
        )
        entry.pack(fill="x", ipady=4)
        return entry

    # ── Browse ───────────────────────────────────────────────────────────

    def _browse(self):
        path = filedialog.askdirectory(title="Select Folder to Upload")
        if path:
            self.folder_var.set(path)
            count = sum(1 for _, _, f in os.walk(path) for _ in f)
            self._log(f"Selected: {path}  ({count} files)", "info")

    # ── Upload ───────────────────────────────────────────────────────────

    def _start_upload(self):
        if self.is_uploading:
            return

        # Validate
        access = self.access_key.get().strip()
        secret = self.secret_key.get().strip()
        bucket = self.bucket.get().strip()
        folder = self.folder_var.get()

        errs = []
        if not access:  errs.append("Access Key is required")
        if not secret:  errs.append("Secret Key is required")
        if not bucket:  errs.append("Bucket Name is required")
        if folder == "No folder selected" or not os.path.isdir(folder):
            errs.append("Select a valid folder")
        if errs:
            for e in errs:
                self._log(f"✗ {e}", "err")
            return

        region = self.region.get().strip() or "us-east-1"
        prefix = self.prefix.get().strip().strip("/")

        self.is_uploading = True
        self.cancel_flag.clear()
        self.upload_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress["value"] = 0

        # Clear log
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

        cfg = dict(access=access, secret=secret, bucket=bucket,
                   region=region, prefix=prefix, folder=folder)
        threading.Thread(target=self._worker, args=(cfg,), daemon=True).start()

    def _cancel_upload(self):
        if self.is_uploading:
            self.cancel_flag.set()
            self._q("log", "⚠ Cancelling…", "warn")

    def _worker(self, cfg):
        try:
            self._q("log", "Connecting to AWS S3…", "info")
            s3 = boto3.client(
                "s3",
                aws_access_key_id=cfg["access"],
                aws_secret_access_key=cfg["secret"],
                region_name=cfg["region"],
            )

            # Check bucket
            try:
                s3.head_bucket(Bucket=cfg["bucket"])
                self._q("log", f"✓ Bucket OK: {cfg['bucket']}", "ok")
            except ClientError as e:
                code = e.response["Error"]["Code"]
                msg = "Access denied" if code == "403" else "Bucket not found" if code == "404" else str(e)
                self._q("log", f"✗ {msg}", "err")
                self._q("done", False)
                return
            except EndpointConnectionError:
                self._q("log", "✗ Cannot connect. Check region/network.", "err")
                self._q("done", False)
                return

            # Collect files
            root = Path(cfg["folder"])
            files = [Path(d) / f for d, _, fs in os.walk(root) for f in fs]
            total = len(files)

            if total == 0:
                self._q("log", "⚠ Folder is empty.", "warn")
                self._q("done", True)
                return

            self._q("log", f"Uploading {total} file(s)…", "info")
            self._q("status", "Uploading…")

            ok = fail = 0
            for fp in files:
                if self.cancel_flag.is_set():
                    self._q("log", f"Cancelled. {ok} uploaded, {total - ok - fail} skipped.", "warn")
                    self._q("done", False)
                    return

                rel = fp.relative_to(root).as_posix()
                key = f"{cfg['prefix']}/{rel}" if cfg["prefix"] else rel

                try:
                    s3.upload_file(str(fp), cfg["bucket"], key)
                    ok += 1
                    self._q("log", f"  ✓ {rel}", "ok")
                except Exception as e:
                    fail += 1
                    self._q("log", f"  ✗ {rel} — {e}", "err")

                self._q("progress", int((ok + fail) / total * 100))
                self._q("counter", f"{ok + fail} / {total}")

            tag = "ok" if fail == 0 else "warn"
            self._q("log", f"Done! {ok} uploaded" + (f", {fail} failed" if fail else ""), tag)
            self._q("done", fail == 0)

        except NoCredentialsError:
            self._q("log", "✗ Invalid credentials.", "err")
            self._q("done", False)
        except Exception as e:
            self._q("log", f"✗ Error: {e}", "err")
            self._q("done", False)

    # ── Thread-safe queue ────────────────────────────────────────────────

    def _q(self, kind, data, extra=None):
        self.log_queue.put((kind, data, extra))

    def _poll_queue(self):
        try:
            while True:
                kind, data, extra = self.log_queue.get_nowait()
                if kind == "log":
                    self._log(data, extra)
                elif kind == "status":
                    self.status_var.set(data)
                elif kind == "progress":
                    self.progress["value"] = data
                elif kind == "counter":
                    self.counter_var.set(data)
                elif kind == "done":
                    self.is_uploading = False
                    self.upload_btn.config(state="normal")
                    self.cancel_btn.config(state="disabled")
                    if data:
                        self.status_var.set("✓ Complete")
                        self.status_lbl.config(fg=GREEN)
                    else:
                        self.status_var.set("✗ Finished with errors")
                        self.status_lbl.config(fg=RED)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _log(self, msg, tag=""):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n", tag or ())
        self.log_text.see("end")
        self.log_text.config(state="disabled")


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = S3UploaderApp(root)
    root.mainloop()
