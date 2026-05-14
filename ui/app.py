"""
NeuralForge Studio — Main Application Window
"""
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import threading

from core.config import (COLORS, FONTS, load_config, save_config,
                          APP_NAME, APP_VERSION)
from core.ollama_backend import (OllamaBackend, ApplierAI,
                                  parse_tool_calls, _make_tool_prompt)
from tools.engine import ToolEngine, ToolError
from ui.widgets import apply_theme, DarkText, IconButton, StatusBar
from ui.chat_panel import ChatPanel
from ui.sidebar import Sidebar
from ui.settings_dialog import SettingsDialog


class NeuralForgeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME}  v{APP_VERSION}")
        self.root.geometry("1280x800")
        self.root.minsize(900, 600)

        self.config = load_config()
        self.ollama = OllamaBackend(self.config.get("ollama_url",
                                                     "http://localhost:11434"))
        self.engine: ToolEngine | None = None
        self._rebuild_engine()

        self._conversation: list[dict] = []
        self._context_files: list[str] = self.config.get("context_files", [])
        self._streaming = False

        apply_theme(root)
        self._build_ui()
        self._check_ollama()

    # ── Engine ────────────────────────────────────────────────────────────────

    def _rebuild_engine(self):
        self.engine = ToolEngine(
            workspace=self.config.get("workspace", ""),
            system_wide=self.config.get("system_wide_access", False),
            confirm_callback=self._confirm_dialog,
            log_callback=self._tool_log,
        )

    def _confirm_dialog(self, title: str, msg: str) -> bool:
        return messagebox.askyesno(title, msg, parent=self.root)

    def _tool_log(self, level: str, msg: str):
        if hasattr(self, "status_bar"):
            color_map = {
                "success": COLORS["success"],
                "warning": COLORS["warning"],
                "error":   COLORS["error"],
                "info":    COLORS["text_secondary"],
            }
            self.status_bar.set("tool", msg, color_map.get(level, COLORS["text_secondary"]))

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Title bar ──
        self._build_titlebar()

        # ── Main pane ──
        main = tk.Frame(self.root, bg=COLORS["bg_darkest"])
        main.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = Sidebar(
            main, self.config,
            on_workspace_change=self._on_workspace_change,
            on_context_change=self._on_context_change,
            on_github_clone=self._clone_github,
        )
        self.sidebar.pack(side="left", fill="y")

        # Vertical divider
        tk.Frame(main, bg=COLORS["border"], width=1).pack(side="left", fill="y")

        # Right side
        right = tk.Frame(main, bg=COLORS["bg_dark"])
        right.pack(side="left", fill="both", expand=True)

        self._build_chat_area(right)
        self._build_input_area(right)

        # ── Status bar ──
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.set("app", f"NeuralForge Studio {APP_VERSION}")
        self.status_bar.set("model", self.config.get("agent_model", "—"))
        self.status_bar.set("workspace", self._short_ws())

    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=COLORS["bg_panel"], height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Logo
        tk.Label(bar, text="⬡  NeuralForge",
                 bg=COLORS["bg_panel"], fg=COLORS["accent"],
                 font=FONTS["heading"], padx=16).pack(side="left", pady=8)
        tk.Label(bar, text=f"v{APP_VERSION}",
                 bg=COLORS["bg_panel"], fg=COLORS["text_muted"],
                 font=FONTS["ui_sm"]).pack(side="left")

        # Right buttons
        IconButton(bar, text="⚙ Settings", small=True,
                   command=self._open_settings).pack(side="right", padx=8, pady=8)
        IconButton(bar, text="🗑 Clear Chat", small=True,
                   command=self._clear_chat).pack(side="right", pady=8)

        # Ollama status indicator
        self._ollama_dot = tk.Label(bar, text="●",
                                     bg=COLORS["bg_panel"],
                                     fg=COLORS["text_muted"],
                                     font=FONTS["ui"])
        self._ollama_dot.pack(side="right", padx=(8, 0))
        tk.Label(bar, text="Ollama",
                 bg=COLORS["bg_panel"], fg=COLORS["text_muted"],
                 font=FONTS["ui_sm"]).pack(side="right")

    def _build_chat_area(self, parent: tk.Frame):
        self.chat = ChatPanel(parent)
        self.chat.pack(fill="both", expand=True)

        # Welcome message
        self.chat.add_system_message(
            "Welcome to NeuralForge Studio. Select a workspace and start prompting.",
            "info"
        )

    def _build_input_area(self, parent: tk.Frame):
        bottom = tk.Frame(parent, bg=COLORS["bg_panel"])
        bottom.pack(fill="x", side="bottom")

        sep = tk.Frame(bottom, bg=COLORS["border"], height=1)
        sep.pack(fill="x")

        inner = tk.Frame(bottom, bg=COLORS["bg_panel"])
        inner.pack(fill="x", padx=12, pady=8)

        # Model selector strip
        model_row = tk.Frame(inner, bg=COLORS["bg_panel"])
        model_row.pack(fill="x", pady=(0, 6))
        tk.Label(model_row, text="Agent:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_muted"], font=FONTS["ui_sm"]).pack(side="left")
        self._agent_var = tk.StringVar(value=self.config.get("agent_model", ""))
        from core.config import MODELS
        agent_opts = [m["id"] for m in MODELS["agent"]]
        ttk.Combobox(model_row, textvariable=self._agent_var,
                     values=agent_opts, state="readonly",
                     width=22, font=FONTS["ui_sm"]
                     ).pack(side="left", padx=(4, 12))

        tk.Label(model_row, text="Scripter:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_muted"], font=FONTS["ui_sm"]).pack(side="left")
        self._scr_var = tk.StringVar(value=self.config.get("scripter_model", ""))
        scr_opts = [m["id"] for m in MODELS["scripter"]]
        ttk.Combobox(model_row, textvariable=self._scr_var,
                     values=scr_opts, state="readonly",
                     width=24, font=FONTS["ui_sm"]
                     ).pack(side="left", padx=4)

        # Prompt box
        prompt_outer = tk.Frame(inner, bg=COLORS["bg_input"],
                                highlightthickness=1,
                                highlightbackground=COLORS["border"],
                                highlightcolor=COLORS["accent"])
        prompt_outer.pack(fill="x")

        self.prompt_box = tk.Text(
            prompt_outer,
            bg=COLORS["bg_input"], fg=COLORS["text_primary"],
            insertbackground=COLORS["accent"],
            relief="flat", bd=0, highlightthickness=0,
            font=FONTS["ui"], wrap="word",
            height=4, padx=12, pady=10,
        )
        self.prompt_box.pack(fill="x", expand=True)
        self.prompt_box.bind("<Return>", self._on_enter)
        self.prompt_box.bind("<Shift-Return>", lambda e: None)

        # Send / stop row
        btn_row = tk.Frame(inner, bg=COLORS["bg_panel"])
        btn_row.pack(fill="x", pady=(6, 0))

        tk.Label(btn_row, text="⏎ Enter to send  ·  Shift+Enter for newline",
                 bg=COLORS["bg_panel"], fg=COLORS["text_muted"],
                 font=FONTS["ui_sm"]).pack(side="left")

        self._stop_btn = IconButton(btn_row, text="⏹ Stop", danger=True,
                                     command=self._stop_stream, small=True)
        self._stop_btn.pack(side="right", padx=(4, 0))
        self._stop_btn.config(state="disabled")

        self._send_btn = IconButton(btn_row, text="Send ▶", accent=True,
                                     command=self._send)
        self._send_btn.pack(side="right")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_enter(self, event):
        if event.state & 0x1:  # Shift held
            return  # allow newline
        self._send()
        return "break"

    def _on_workspace_change(self, path: str):
        self.config["workspace"] = path
        save_config(self.config)
        self._rebuild_engine()
        self.status_bar.set("workspace", self._short_ws())
        self.chat.add_system_message(f"Workspace set: {path}", "success")

    def _on_context_change(self, files: list[str]):
        self._context_files = files
        self.config["context_files"] = files
        save_config(self.config)

    def _open_settings(self):
        def on_save(new_cfg):
            self.config = new_cfg
            self.ollama.base_url = new_cfg.get("ollama_url",
                                                "http://localhost:11434")
            self._rebuild_engine()
            self._agent_var.set(new_cfg.get("agent_model", ""))
            self._scr_var.set(new_cfg.get("scripter_model", ""))
            self.status_bar.set("model", new_cfg.get("agent_model", "—"))
            self.sidebar.update_config(new_cfg)
            self.chat.add_system_message("Settings saved.", "success")

        SettingsDialog(self.root, self.config, self.ollama, on_save=on_save)

    def _clear_chat(self):
        self.chat.clear()
        self._conversation.clear()
        self.chat.add_system_message("Chat cleared.", "info")

    def _stop_stream(self):
        self._streaming = False

    # ── Send / AI loop ────────────────────────────────────────────────────────

    def _send(self):
        if self._streaming:
            return
        text = self.prompt_box.get("1.0", "end").strip()
        if not text:
            return
        self.prompt_box.delete("1.0", "end")
        self.chat.add_user_message(text)
        self._conversation.append({"role": "user", "content": text})
        self._run_agent()

    def _run_agent(self):
        self._streaming = True
        self._send_btn.config(state="disabled")
        self._stop_btn.config(state="normal")

        model = self._agent_var.get() or self.config.get("agent_model", "")
        system = _make_tool_prompt(
            self.config.get("workspace", ""),
            self._build_context_string()
        )

        bubble = self.chat.add_ai_message_start()
        full_response = {"text": ""}
        stopped = [False]

        def on_token(token):
            if not self._streaming:
                stopped[0] = True
                return
            full_response["text"] += token
            bubble.append(token)

        def on_done(full_text):
            bubble.finalize()
            self._conversation.append({"role": "assistant", "content": full_text})
            self._process_tool_calls(full_text)
            self._streaming = False
            self.root.after(0, self._restore_buttons)

        def on_error(err):
            self.root.after(0, lambda: self.chat.add_system_message(
                f"Error: {err}", "error"))
            self._streaming = False
            self.root.after(0, self._restore_buttons)

        self.ollama.chat_stream(
            model=model,
            messages=self._conversation,
            system=system,
            on_token=lambda t: self.root.after(0, lambda: on_token(t)),
            on_done=lambda t: self.root.after(0, lambda: on_done(t)),
            on_error=lambda e: self.root.after(0, lambda: on_error(e)),
        )

    def _restore_buttons(self):
        self._send_btn.config(state="normal")
        self._stop_btn.config(state="disabled")

    def _process_tool_calls(self, response_text: str):
        calls = parse_tool_calls(response_text)
        if not calls:
            return
        for call in calls:
            self._execute_tool(call)

    def _execute_tool(self, call: dict):
        tool = call.get("tool", "")
        params = {k: v for k, v in call.items() if k != "tool"}
        card = self.chat.add_tool_call(tool, params)

        try:
            result = self._dispatch_tool(tool, call)
            self.chat.add_system_message(
                f"Tool '{tool}' completed.", "success"
            )
            # If script tool, invoke the applier AI
            if tool == "script" and result.get("status") == "ok":
                self._run_applier(call, result)
        except ToolError as e:
            self.chat.add_system_message(f"Tool error: {e}", "error")
        except Exception as e:
            self.chat.add_system_message(f"Unexpected error: {e}", "error")

    def _dispatch_tool(self, tool: str, call: dict) -> dict:
        if tool == "script":
            return self.engine.tool_script(
                call.get("path", "output.py"),
                call.get("content", ""),
                call.get("language", "python")
            )
        elif tool == "read":
            return self.engine.tool_read(
                call.get("path", "."),
                call.get("start_line", 0),
                call.get("end_line", -1),
            )
        elif tool == "rename":
            return self.engine.tool_rename(
                call.get("src", ""), call.get("dst", "")
            )
        elif tool == "run":
            return self.engine.tool_run(
                call.get("command", ""),
                call.get("cwd", ""),
            )
        elif tool == "github_clone":
            return self.engine.tool_github_clone(
                call.get("repo_url", ""),
                self.config.get("github_token", ""),
                call.get("dest", ""),
            )
        else:
            raise ToolError(f"Unknown tool: {tool}")

    # ── Applier AI ────────────────────────────────────────────────────────────

    def _run_applier(self, call: dict, script_result: dict):
        path = script_result.get("path", "")
        new_code = call.get("content", "")
        model = self._scr_var.get() or self.config.get("scripter_model", "")

        self.chat.add_system_message(
            f"Applier AI reviewing code for {os.path.basename(path)}…", "info"
        )

        def _apply():
            # Read original if exists
            original = ""
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        original = f.read()
                except Exception:
                    pass

            applier = ApplierAI(self.ollama, model)
            ok, result = applier.apply(path, original, new_code)
            if ok and result.strip():
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(result)
                    self.root.after(0, lambda: self.chat.add_system_message(
                        f"✓ Applier wrote {len(result)} chars to {os.path.basename(path)}",
                        "success"
                    ))
                except Exception as e:
                    self.root.after(0, lambda: self.chat.add_system_message(
                        f"Applier write error: {e}", "error"
                    ))
            else:
                self.root.after(0, lambda: self.chat.add_system_message(
                    "Applier returned no changes.", "warning"
                ))

        threading.Thread(target=_apply, daemon=True).start()

    # ── GitHub clone ──────────────────────────────────────────────────────────

    def _clone_github(self, url: str):
        self.chat.add_system_message(f"Cloning {url}…", "info")

        def _run():
            try:
                result = self.engine.tool_github_clone(
                    url, self.config.get("github_token", "")
                )
                msg = f"Cloned to {result.get('clone_path', '?')}"
                lvl = "success" if result.get("status") == "ok" else "error"
            except ToolError as e:
                msg, lvl = str(e), "error"
            self.root.after(0, lambda: self.chat.add_system_message(msg, lvl))
            self.root.after(200, self.sidebar._refresh_tree)

        threading.Thread(target=_run, daemon=True).start()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_context_string(self) -> str:
        parts = []
        for path in self._context_files:
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read(8000)  # limit per file
                    parts.append(f"=== {path} ===\n{content}")
                except Exception:
                    pass
        return "\n\n".join(parts) if parts else ""

    def _short_ws(self) -> str:
        ws = self.config.get("workspace", "")
        if not ws:
            return "No workspace"
        return os.path.basename(ws) or ws

    def _check_ollama(self):
        def _run():
            ok, msg = self.ollama.is_available()
            color = COLORS["success"] if ok else COLORS["error"]
            self.root.after(0, lambda: self._ollama_dot.config(fg=color))
            if not ok:
                self.root.after(0, lambda: self.chat.add_system_message(
                    f"Ollama not found: {msg} — Start Ollama or update URL in Settings.",
                    "warning"
                ))
        threading.Thread(target=_run, daemon=True).start()
