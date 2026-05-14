"""
NeuralForge Studio — Left Sidebar
Workspace selector, file tree, context files, GitHub clone
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from core.config import COLORS, FONTS
from ui.widgets import IconButton, Card


class Sidebar(tk.Frame):
    def __init__(self, master, config: dict,
                 on_workspace_change=None,
                 on_context_change=None,
                 on_github_clone=None,
                 **kw):
        kw["bg"] = COLORS["bg_panel"]
        kw["width"] = 260
        super().__init__(master, **kw)
        self.pack_propagate(False)

        self.config = config
        self.on_workspace_change = on_workspace_change
        self.on_context_change = on_context_change
        self.on_github_clone = on_github_clone

        self._context_files: list[str] = list(config.get("context_files", []))

        self._build()
        if config.get("workspace"):
            self._refresh_tree()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Workspace section ──
        self._section_header("WORKSPACE")

        ws_row = tk.Frame(self, bg=COLORS["bg_panel"])
        ws_row.pack(fill="x", padx=8, pady=(0, 4))
        self._ws_label = tk.Label(ws_row, text=self._short_path(),
                                  bg=COLORS["bg_panel"],
                                  fg=COLORS["text_secondary"],
                                  font=FONTS["ui_sm"], anchor="w",
                                  wraplength=170, justify="left")
        self._ws_label.pack(side="left", fill="x", expand=True)
        IconButton(ws_row, icon="📁", small=True,
                   command=self._pick_folder,
                   tooltip="Open folder").pack(side="right")

        # File tree
        tree_outer = tk.Frame(self, bg=COLORS["bg_panel"])
        tree_outer.pack(fill="both", expand=True, padx=8)

        self._tree = ttk.Treeview(tree_outer, show="tree",
                                   selectmode="browse")
        self._tree.column("#0", width=220)
        tsb = ttk.Scrollbar(tree_outer, orient="vertical",
                             command=self._tree.yview)
        self._tree.configure(yscrollcommand=tsb.set)
        tsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Treeview",
                         background=COLORS["bg_panel"],
                         foreground=COLORS["text_primary"],
                         fieldbackground=COLORS["bg_panel"],
                         borderwidth=0,
                         font=FONTS["ui_sm"],
                         rowheight=22)
        style.map("Treeview",
                  background=[("selected", COLORS["accent_dim"])],
                  foreground=[("selected", COLORS["text_primary"])])
        style.configure("Treeview.Heading",
                         background=COLORS["bg_card"],
                         foreground=COLORS["text_secondary"],
                         borderwidth=0)

        self._tree.bind("<<TreeviewOpen>>", self._on_tree_open)
        self._tree.bind("<Double-1>", self._on_tree_dbl)

        # Refresh button
        IconButton(self, text="⟳ Refresh", small=True,
                   command=self._refresh_tree).pack(anchor="e", padx=8)

        # ── Context files ──
        self._sep()
        self._section_header("CONTEXT FILES")
        ctx_row = tk.Frame(self, bg=COLORS["bg_panel"])
        ctx_row.pack(fill="x", padx=8, pady=(0, 4))
        IconButton(ctx_row, text="+ Add File", small=True,
                   command=self._add_context).pack(side="left")
        IconButton(ctx_row, text="Clear", small=True,
                   command=self._clear_context).pack(side="right")

        self._ctx_list = tk.Frame(self, bg=COLORS["bg_panel"])
        self._ctx_list.pack(fill="x", padx=8)
        self._refresh_ctx_list()

        # ── GitHub ──
        self._sep()
        self._section_header("GITHUB")

        gh_inner = tk.Frame(self, bg=COLORS["bg_panel"])
        gh_inner.pack(fill="x", padx=8, pady=(0, 8))

        self._gh_url = tk.Entry(gh_inner,
                                 bg=COLORS["bg_input"],
                                 fg=COLORS["text_primary"],
                                 insertbackground=COLORS["accent"],
                                 relief="flat", font=FONTS["ui_sm"],
                                 bd=0, highlightthickness=1,
                                 highlightbackground=COLORS["border"],
                                 highlightcolor=COLORS["accent"])
        self._gh_url.insert(0, "https://github.com/user/repo")
        self._gh_url.pack(fill="x", ipady=5, pady=(0, 4))

        IconButton(gh_inner, text="⬇ Clone to Workspace", small=True,
                   accent=True, command=self._clone).pack(fill="x")

    # ── Section helpers ───────────────────────────────────────────────────────

    def _section_header(self, title: str):
        tk.Label(self, text=title, bg=COLORS["bg_panel"],
                 fg=COLORS["text_muted"],
                 font=FONTS["tag"]).pack(fill="x", padx=10, pady=(10, 2))

    def _sep(self):
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x", padx=6, pady=4)

    # ── Workspace ─────────────────────────────────────────────────────────────

    def _short_path(self) -> str:
        ws = self.config.get("workspace", "")
        if not ws:
            return "(none selected)"
        parts = ws.replace("\\", "/").split("/")
        return "/" + "/".join(parts[-2:]) if len(parts) > 2 else ws

    def _pick_folder(self):
        path = filedialog.askdirectory(title="Select Workspace Folder")
        if path:
            self.config["workspace"] = path
            self._ws_label.config(text=self._short_path())
            self._refresh_tree()
            if self.on_workspace_change:
                self.on_workspace_change(path)

    def _refresh_tree(self):
        self._tree.delete(*self._tree.get_children())
        ws = self.config.get("workspace", "")
        if not ws or not os.path.isdir(ws):
            return
        root_id = self._tree.insert("", "end",
                                     text=f"📁 {os.path.basename(ws)}",
                                     open=True, iid="root",
                                     values=[ws])
        self._populate_tree(root_id, ws)

    def _populate_tree(self, parent_id: str, path: str):
        try:
            entries = sorted(os.scandir(path),
                              key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return
        for e in entries[:200]:  # limit for performance
            icon = "📁" if e.is_dir() else self._file_icon(e.name)
            iid = self._tree.insert(parent_id, "end",
                                     text=f"{icon} {e.name}",
                                     values=[e.path])
            if e.is_dir():
                # Placeholder for lazy loading
                self._tree.insert(iid, "end", text="…")

    def _on_tree_open(self, _):
        sel = self._tree.focus()
        children = self._tree.get_children(sel)
        if children and self._tree.item(children[0])["text"] == "…":
            self._tree.delete(children[0])
            path = self._tree.item(sel)["values"]
            if path:
                self._populate_tree(sel, path[0])

    def _on_tree_dbl(self, _):
        sel = self._tree.focus()
        vals = self._tree.item(sel)["values"]
        if vals:
            path = vals[0]
            if os.path.isfile(path):
                self._add_context_file(path)

    def _file_icon(self, name: str) -> str:
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        icons = {
            "py": "🐍", "js": "📜", "ts": "📘", "jsx": "⚛", "tsx": "⚛",
            "html": "🌐", "css": "🎨", "json": "📋", "md": "📝",
            "txt": "📄", "sh": "⚙", "yml": "⚙", "yaml": "⚙",
            "toml": "⚙", "rs": "🦀", "go": "🐹", "cpp": "⚙",
            "c": "⚙", "h": "⚙", "java": "☕", "rb": "💎",
        }
        return icons.get(ext, "📄")

    # ── Context files ─────────────────────────────────────────────────────────

    def _add_context(self):
        path = filedialog.askopenfilename(title="Add Context File")
        if path:
            self._add_context_file(path)

    def _add_context_file(self, path: str):
        if path not in self._context_files:
            self._context_files.append(path)
            self._refresh_ctx_list()
            if self.on_context_change:
                self.on_context_change(self._context_files)

    def _clear_context(self):
        self._context_files.clear()
        self._refresh_ctx_list()
        if self.on_context_change:
            self.on_context_change(self._context_files)

    def _refresh_ctx_list(self):
        for w in self._ctx_list.winfo_children():
            w.destroy()
        for path in self._context_files:
            row = tk.Frame(self._ctx_list, bg=COLORS["bg_panel"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"📄 {os.path.basename(path)}",
                     bg=COLORS["bg_panel"], fg=COLORS["text_secondary"],
                     font=FONTS["ui_sm"], anchor="w").pack(side="left", fill="x", expand=True)
            IconButton(row, text="✕", small=True, danger=True,
                       command=lambda p=path: self._remove_ctx(p)).pack(side="right")
        if not self._context_files:
            tk.Label(self._ctx_list, text="(no context files)",
                     bg=COLORS["bg_panel"], fg=COLORS["text_muted"],
                     font=FONTS["ui_sm"]).pack(anchor="w")

    def _remove_ctx(self, path: str):
        if path in self._context_files:
            self._context_files.remove(path)
            self._refresh_ctx_list()
            if self.on_context_change:
                self.on_context_change(self._context_files)

    # ── GitHub ────────────────────────────────────────────────────────────────

    def _clone(self):
        url = self._gh_url.get().strip()
        if not url or url == "https://github.com/user/repo":
            messagebox.showwarning("No URL", "Enter a GitHub repository URL.")
            return
        if not self.config.get("workspace"):
            messagebox.showwarning("No Workspace",
                                   "Select a workspace folder first.")
            return
        if self.on_github_clone:
            self.on_github_clone(url)

    def get_context_files(self) -> list[str]:
        return list(self._context_files)

    def update_config(self, cfg: dict):
        self.config = cfg
