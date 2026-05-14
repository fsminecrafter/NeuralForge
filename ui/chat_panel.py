"""
NeuralForge Studio — Chat Panel
"""
import tkinter as tk
from tkinter import ttk
from core.config import COLORS, FONTS
from ui.widgets import DarkText


TOOL_COLORS = {
    "script": ("#a855f7", "✏"),
    "read":   ("#06b6d4", "📖"),
    "rename": ("#f59e0b", "✏️"),
    "run":    ("#ef4444", "▶"),
    "github_clone": ("#22c55e", "⬇"),
    "default": (COLORS["accent"], "⚙"),
}


class ChatPanel(tk.Frame):
    """Scrollable chat area that renders user/AI messages and tool calls."""

    def __init__(self, master, **kw):
        kw.setdefault("bg", COLORS["bg_dark"])
        super().__init__(master, **kw)
        self._build()

    def _build(self):
        # Canvas + scrollbar
        self.canvas = tk.Canvas(self, bg=COLORS["bg_dark"],
                                highlightthickness=0, bd=0)
        self.sb = ttk.Scrollbar(self, orient="vertical",
                                 command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.sb.set)

        self.sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=COLORS["bg_dark"])
        self._win = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
        )
        self.inner.bind("<Configure>", self._sync_scroll)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self._scroll)
        self.inner.bind("<MouseWheel>", self._scroll)

        self._messages = []

    def _sync_scroll(self, _=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, e):
        self.canvas.itemconfig(self._win, width=e.width)

    def _scroll(self, e):
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def scroll_bottom(self):
        self.after(80, lambda: self.canvas.yview_moveto(1.0))

    # ── Public API ────────────────────────────────────────────────────────────

    def add_user_message(self, text: str):
        self._add_bubble("user", text)

    def add_ai_message_start(self) -> "StreamBubble":
        """Start streaming AI message. Returns a handle to update."""
        bubble = StreamBubble(self.inner, self)
        bubble.frame.pack(fill="x", padx=16, pady=(4, 2))
        self._messages.append(bubble)
        self.scroll_bottom()
        return bubble

    def add_tool_call(self, tool_name: str, params: dict, result: dict = None):
        card = ToolCallCard(self.inner, tool_name, params, result)
        card.pack(fill="x", padx=16, pady=2)
        self.scroll_bottom()
        return card

    def add_system_message(self, text: str, level: str = "info"):
        color_map = {
            "info":    COLORS["text_muted"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error":   COLORS["error"],
        }
        color = color_map.get(level, COLORS["text_muted"])
        lbl = tk.Label(
            self.inner, text=f"  {text}",
            bg=COLORS["bg_dark"], fg=color,
            font=FONTS["ui_sm"], anchor="w", justify="left"
        )
        lbl.pack(fill="x", padx=16, pady=1)
        self.scroll_bottom()

    def clear(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self._messages.clear()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _add_bubble(self, role: str, text: str):
        bubble = MessageBubble(self.inner, role, text)
        bubble.pack(fill="x", padx=16, pady=(4, 2))
        self._messages.append(bubble)
        self.scroll_bottom()


class MessageBubble(tk.Frame):
    def __init__(self, master, role: str, text: str, **kw):
        kw["bg"] = COLORS["bg_dark"]
        super().__init__(master, **kw)
        is_user = role == "user"

        header_color = COLORS["accent"] if is_user else COLORS["success"]
        header_text = "You" if is_user else "NeuralForge"
        bg = COLORS["user_bubble"] if is_user else COLORS["ai_bubble"]

        hdr = tk.Label(self, text=header_text, fg=header_color,
                       bg=COLORS["bg_dark"], font=FONTS["ui_sm"],
                       anchor="w" if is_user else "e")
        hdr.pack(fill="x")

        bubble = tk.Frame(self, bg=bg, bd=0,
                          highlightthickness=1,
                          highlightbackground=COLORS["border"])
        bubble.pack(fill="x", ipady=2)

        txt = tk.Text(bubble, bg=bg, fg=COLORS["text_primary"],
                      font=FONTS["ui"], wrap="word", relief="flat",
                      bd=0, highlightthickness=0,
                      padx=12, pady=8, state="normal",
                      cursor="arrow")
        txt.insert("1.0", text)
        txt.configure(state="disabled")
        # Auto-height
        lines = text.count("\n") + 1 + len(text) // 80
        txt.configure(height=max(1, min(lines, 20)))
        txt.pack(fill="x")


class StreamBubble:
    """AI message bubble that can be updated token by token."""
    def __init__(self, master: tk.Frame, panel: "ChatPanel"):
        self.panel = panel
        self.frame = tk.Frame(master, bg=COLORS["bg_dark"])
        self._text = ""

        hdr = tk.Label(self.frame, text="NeuralForge", fg=COLORS["success"],
                       bg=COLORS["bg_dark"], font=FONTS["ui_sm"], anchor="e")
        hdr.pack(fill="x")

        bubble = tk.Frame(self.frame, bg=COLORS["ai_bubble"], bd=0,
                          highlightthickness=1,
                          highlightbackground=COLORS["border"])
        bubble.pack(fill="x", ipady=2)

        self.txt = tk.Text(bubble, bg=COLORS["ai_bubble"],
                           fg=COLORS["text_primary"],
                           font=FONTS["ui"], wrap="word", relief="flat",
                           bd=0, highlightthickness=0,
                           padx=12, pady=8, state="normal",
                           cursor="arrow", height=2)
        self.txt.pack(fill="x")

    def append(self, token: str):
        self._text += token
        self.txt.configure(state="normal")
        self.txt.insert("end", token)
        # Resize height
        lines = self._text.count("\n") + 1 + len(self._text) // 80
        self.txt.configure(height=max(2, min(lines, 30)))
        self.txt.configure(state="disabled")
        self.txt.see("end")
        self.panel.scroll_bottom()

    def finalize(self):
        self.txt.configure(state="disabled")


class ToolCallCard(tk.Frame):
    """Visual card showing a tool invocation and its result."""
    def __init__(self, master, tool_name: str, params: dict,
                 result: dict = None, **kw):
        kw["bg"] = COLORS["bg_dark"]
        super().__init__(master, **kw)
        color, icon = TOOL_COLORS.get(tool_name, TOOL_COLORS["default"])

        card = tk.Frame(self, bg=COLORS["bg_card"], bd=0,
                        highlightthickness=1,
                        highlightbackground=color + "66")
        card.pack(fill="x")

        # Header row
        hdr = tk.Frame(card, bg=color + "22")
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"  {icon}  {tool_name.upper()}",
                 bg=color + "22", fg=color,
                 font=FONTS["ui_bold"], anchor="w", pady=4).pack(side="left")

        # Params
        import json
        param_str = json.dumps(
            {k: v for k, v in params.items() if k != "content"},
            indent=None
        )
        if "content" in params:
            lines = params["content"].count("\n") + 1
            param_str += f'  content=<{lines} lines>'

        tk.Label(card, text=param_str, bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["mono_sm"],
                 anchor="w", padx=10, pady=2,
                 wraplength=600, justify="left").pack(fill="x")

        # Result
        if result:
            status = result.get("status", "?")
            s_color = COLORS["success"] if status == "ok" else COLORS["error"]
            result_text = self._format_result(result)
            tk.Label(card, text=result_text, bg=COLORS["bg_card"],
                     fg=s_color, font=FONTS["mono_sm"],
                     anchor="w", padx=10, pady=4,
                     wraplength=600, justify="left").pack(fill="x")

    def _format_result(self, r: dict) -> str:
        status = r.get("status", "?")
        if status == "ok":
            if "content" in r:
                preview = r["content"][:200].replace("\n", "↵")
                return f"✓ {preview}"
            if "entries" in r:
                return f"✓ {len(r['entries'])} entries"
            if "stdout" in r:
                out = (r["stdout"] + r.get("stderr", ""))[:200]
                return f"✓ exit={r.get('returncode', 0)}  {out}"
            return f"✓ {status}"
        return f"✗ {r.get('reason', str(r))}"

    def set_result(self, result: dict):
        # Rebuild — easiest approach since card is small
        pass