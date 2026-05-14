"""
NeuralForge Studio — Settings Dialog
"""
import tkinter as tk
from tkinter import ttk, messagebox
from core.config import COLORS, FONTS, MODELS, save_config
from ui.widgets import Card, IconButton, DarkText


class SettingsDialog(tk.Toplevel):
    def __init__(self, master, config: dict, ollama, on_save=None):
        super().__init__(master)
        self.config = dict(config)
        self.ollama = ollama
        self.on_save = on_save

        self.title("Settings — NeuralForge Studio")
        self.geometry("680x560")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_dark"])
        self.transient(master)
        self.grab_set()

        self._vars = {}
        self._build()
        self.center()

    def center(self):
        self.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() - 680) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - 560) // 2
        self.geometry(f"+{x}+{y}")

    def _lbl(self, parent, text, size="normal"):
        font = FONTS["ui_bold"] if size == "heading" else FONTS["ui"]
        color = COLORS["text_primary"] if size == "heading" else COLORS["text_secondary"]
        return tk.Label(parent, text=text, bg=COLORS["bg_dark"],
                        fg=color, font=font, anchor="w")

    def _build(self):
        # Title bar
        bar = tk.Frame(self, bg=COLORS["bg_panel"], height=48)
        bar.pack(fill="x")
        tk.Label(bar, text="⚙  Settings", bg=COLORS["bg_panel"],
                 fg=COLORS["text_primary"], font=FONTS["heading"],
                 padx=20).pack(side="left", pady=12)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=12)

        self._tab_models(nb)
        self._tab_ollama(nb)
        self._tab_access(nb)
        self._tab_github(nb)

        # Bottom bar
        btm = tk.Frame(self, bg=COLORS["bg_dark"])
        btm.pack(fill="x", padx=16, pady=(0, 12))
        IconButton(btm, text="Cancel", command=self.destroy).pack(side="right", padx=(4, 0))
        IconButton(btm, text="Save", accent=True,
                   command=self._save).pack(side="right")

    def _section(self, parent, title):
        tk.Label(parent, text=title, bg=COLORS["bg_dark"],
                 fg=COLORS["accent"], font=FONTS["ui_bold"],
                 anchor="w").pack(fill="x", pady=(12, 4))
        sep = tk.Frame(parent, bg=COLORS["border"], height=1)
        sep.pack(fill="x", pady=(0, 8))

    def _tab_models(self, nb):
        frame = tk.Frame(nb, bg=COLORS["bg_dark"])
        nb.add(frame, text="  Models  ")

        self._section(frame, "Agent Model  (reasoning / tool-use AI)")
        agent_ids = [m["id"] for m in MODELS["agent"]]
        agent_names = [f"{m['name']}  [{m['vram']}]" for m in MODELS["agent"]]
        cur_agent = self.config.get("agent_model", agent_ids[0])
        idx_a = agent_ids.index(cur_agent) if cur_agent in agent_ids else 0
        self._vars["agent_model"] = tk.StringVar(value=agent_ids[idx_a])
        self._combo(frame, agent_names, agent_ids, "agent_model")

        self._section(frame, "Scripter Model  (code-writing AI)")
        scr_ids = [m["id"] for m in MODELS["scripter"]]
        scr_names = [f"{m['name']}  [{m['vram']}]" for m in MODELS["scripter"]]
        cur_scr = self.config.get("scripter_model", scr_ids[0])
        idx_s = scr_ids.index(cur_scr) if cur_scr in scr_ids else 0
        self._vars["scripter_model"] = tk.StringVar(value=scr_ids[idx_s])
        self._combo(frame, scr_names, scr_ids, "scripter_model")

        # Download button
        tk.Label(frame, text="Download a model via Ollama:",
                 bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
                 font=FONTS["ui"], anchor="w").pack(fill="x", pady=(16, 4))
        row = tk.Frame(frame, bg=COLORS["bg_dark"])
        row.pack(fill="x")
        self._dl_var = tk.StringVar()
        entry = tk.Entry(row, textvariable=self._dl_var,
                         bg=COLORS["bg_input"], fg=COLORS["text_primary"],
                         insertbackground=COLORS["accent"],
                         relief="flat", font=FONTS["mono"],
                         bd=0, highlightthickness=1,
                         highlightbackground=COLORS["border"],
                         highlightcolor=COLORS["accent"])
        entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        IconButton(row, text="⬇ Pull Model", accent=True,
                   command=self._pull_model).pack(side="left")
        self._dl_status = tk.Label(frame, text="",
                                   bg=COLORS["bg_dark"],
                                   fg=COLORS["text_secondary"],
                                   font=FONTS["ui_sm"], anchor="w")
        self._dl_status.pack(fill="x", pady=4)

    def _combo(self, parent, names, ids, key):
        display_var = tk.StringVar(value=names[ids.index(self._vars[key].get())]
                                   if self._vars[key].get() in ids else names[0])
        cb = ttk.Combobox(parent, textvariable=display_var,
                          values=names, state="readonly", font=FONTS["ui"])
        cb.pack(fill="x", ipady=4, pady=(0, 4))

        def on_change(*_):
            idx = names.index(display_var.get())
            self._vars[key].set(ids[idx])
        cb.bind("<<ComboboxSelected>>", on_change)

    def _pull_model(self):
        model = self._dl_var.get().strip()
        if not model:
            return
        self._dl_status.config(text=f"Pulling {model}…", fg=COLORS["warning"])

        def progress(msg):
            self._dl_status.config(text=msg)

        import threading
        def _run():
            ok, msg = self.ollama.pull_model(model, progress)
            color = COLORS["success"] if ok else COLORS["error"]
            self._dl_status.config(text=msg, fg=color)

        threading.Thread(target=_run, daemon=True).start()

    def _tab_ollama(self, nb):
        frame = tk.Frame(nb, bg=COLORS["bg_dark"])
        nb.add(frame, text="  Ollama  ")
        self._section(frame, "Ollama Server")

        tk.Label(frame, text="API URL:", bg=COLORS["bg_dark"],
                 fg=COLORS["text_secondary"], font=FONTS["ui"],
                 anchor="w").pack(fill="x")
        self._vars["ollama_url"] = tk.StringVar(
            value=self.config.get("ollama_url", "http://localhost:11434")
        )
        entry = tk.Entry(frame, textvariable=self._vars["ollama_url"],
                         bg=COLORS["bg_input"], fg=COLORS["text_primary"],
                         insertbackground=COLORS["accent"],
                         relief="flat", font=FONTS["mono"],
                         bd=0, highlightthickness=1,
                         highlightbackground=COLORS["border"],
                         highlightcolor=COLORS["accent"])
        entry.pack(fill="x", ipady=6, pady=(2, 8))

        row = tk.Frame(frame, bg=COLORS["bg_dark"])
        row.pack(fill="x")
        self._ping_label = tk.Label(row, text="", bg=COLORS["bg_dark"],
                                    fg=COLORS["text_secondary"],
                                    font=FONTS["ui_sm"])
        self._ping_label.pack(side="left")
        IconButton(row, text="Test Connection", command=self._test_conn,
                   small=True).pack(side="right")

    def _test_conn(self):
        url = self._vars["ollama_url"].get().strip()
        self.ollama.base_url = url
        ok, msg = self.ollama.is_available()
        color = COLORS["success"] if ok else COLORS["error"]
        prefix = "✓" if ok else "✗"
        self._ping_label.config(text=f"{prefix} {msg}", fg=color)

    def _tab_access(self, nb):
        frame = tk.Frame(nb, bg=COLORS["bg_dark"])
        nb.add(frame, text="  Access  ")
        self._section(frame, "File System Access")

        self._vars["system_wide_access"] = tk.BooleanVar(
            value=self.config.get("system_wide_access", False)
        )
        cb = ttk.Checkbutton(
            frame,
            text="Enable System-Wide Access (AI can operate outside workspace)",
            variable=self._vars["system_wide_access"]
        )
        cb.pack(anchor="w", pady=4)

        tk.Label(frame,
                 text="⚠  With system-wide access enabled, the AI can read, write,\n"
                      "    and execute commands anywhere on your system.\n"
                      "    Use with caution.",
                 bg=COLORS["bg_dark"], fg=COLORS["warning"],
                 font=FONTS["ui_sm"], justify="left", anchor="w"
                 ).pack(fill="x", pady=8)

    def _tab_github(self, nb):
        frame = tk.Frame(nb, bg=COLORS["bg_dark"])
        nb.add(frame, text="  GitHub  ")
        self._section(frame, "GitHub Integration")

        tk.Label(frame, text="Personal Access Token (for private repos):",
                 bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
                 font=FONTS["ui"], anchor="w").pack(fill="x")
        self._vars["github_token"] = tk.StringVar(
            value=self.config.get("github_token", "")
        )
        entry = tk.Entry(frame, textvariable=self._vars["github_token"],
                         show="*",
                         bg=COLORS["bg_input"], fg=COLORS["text_primary"],
                         insertbackground=COLORS["accent"],
                         relief="flat", font=FONTS["mono"],
                         bd=0, highlightthickness=1,
                         highlightbackground=COLORS["border"],
                         highlightcolor=COLORS["accent"])
        entry.pack(fill="x", ipady=6, pady=(2, 8))
        tk.Label(frame,
                 text="Token is stored locally in ~/.neuralforge/config.json",
                 bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
                 font=FONTS["ui_sm"], anchor="w").pack(fill="x")

    def _save(self):
        for key, var in self._vars.items():
            self.config[key] = var.get()
        save_config(self.config)
        if self.on_save:
            self.on_save(self.config)
        self.destroy()
