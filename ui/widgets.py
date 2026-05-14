"""
NeuralForge Studio — Custom Themed Widgets
"""
import tkinter as tk
from tkinter import ttk
from core.config import COLORS, FONTS


def apply_theme(root: tk.Tk):
    """Apply global ttk theme overrides."""
    style = ttk.Style(root)
    style.theme_use("clam")

    bg = COLORS["bg_dark"]
    fg = COLORS["text_primary"]
    sel = COLORS["accent"]

    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg,
                    font=FONTS["ui"])
    style.configure("TButton",
                    background=COLORS["bg_card"],
                    foreground=fg,
                    borderwidth=1,
                    relief="flat",
                    font=FONTS["ui"],
                    padding=(12, 6))
    style.map("TButton",
              background=[("active", COLORS["bg_hover"]),
                          ("pressed", COLORS["accent_dim"])],
              foreground=[("active", fg)])

    style.configure("Accent.TButton",
                    background=COLORS["accent"],
                    foreground="#ffffff",
                    font=FONTS["ui_bold"],
                    padding=(14, 8))
    style.map("Accent.TButton",
              background=[("active", COLORS["accent_glow"])])

    style.configure("TCombobox",
                    background=COLORS["bg_input"],
                    foreground=fg,
                    fieldbackground=COLORS["bg_input"],
                    selectbackground=COLORS["accent_dim"],
                    borderwidth=1,
                    relief="flat")
    style.map("TCombobox",
              fieldbackground=[("readonly", COLORS["bg_input"])],
              background=[("readonly", COLORS["bg_input"])])

    style.configure("TScrollbar",
                    background=COLORS["bg_panel"],
                    troughcolor=COLORS["bg_darkest"],
                    borderwidth=0,
                    arrowsize=12)
    style.map("TScrollbar",
              background=[("active", COLORS["border_bright"])])

    style.configure("TNotebook",
                    background=COLORS["bg_dark"],
                    tabmargins=[0, 0, 0, 0])
    style.configure("TNotebook.Tab",
                    background=COLORS["bg_panel"],
                    foreground=COLORS["text_secondary"],
                    padding=[14, 6],
                    font=FONTS["ui"])
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["bg_card"])],
              foreground=[("selected", COLORS["text_primary"])])

    style.configure("TCheckbutton",
                    background=bg,
                    foreground=fg,
                    font=FONTS["ui"])
    style.map("TCheckbutton",
              background=[("active", bg)])

    style.configure("TSeparator", background=COLORS["border"])

    # Root window bg
    root.configure(bg=COLORS["bg_darkest"])


class DarkText(tk.Text):
    """Pre-styled dark text widget."""
    def __init__(self, master, mono=False, **kw):
        font = FONTS["mono"] if mono else FONTS["ui"]
        defaults = dict(
            bg=COLORS["bg_input"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["accent"],
            selectbackground=COLORS["accent_dim"],
            selectforeground=COLORS["text_primary"],
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=COLORS["accent"],
            highlightbackground=COLORS["border"],
            font=font,
            wrap="word",
            padx=10,
            pady=8,
        )
        defaults.update(kw)
        super().__init__(master, **defaults)


class Card(tk.Frame):
    """Rounded-ish card panel."""
    def __init__(self, master, **kw):
        kw.setdefault("bg", COLORS["bg_card"])
        kw.setdefault("relief", "flat")
        kw.setdefault("bd", 0)
        super().__init__(master, **kw)
        # Inner highlight border via a wrapper
        self.configure(highlightthickness=1,
                        highlightbackground=COLORS["border"])


class IconButton(tk.Button):
    """Flat icon/text button with hover effect."""
    def __init__(self, master, text="", icon="", accent=False, danger=False,
                 small=False, tooltip="", **kw):
        label = f"{icon} {text}".strip() if icon else text
        fg = "#ffffff" if accent else COLORS["text_primary"]
        bg = COLORS["accent"] if accent else (
            COLORS["error"] if danger else COLORS["bg_card"]
        )
        hover_bg = COLORS["accent_glow"] if accent else (
            "#c0392b" if danger else COLORS["bg_hover"]
        )
        font = FONTS["ui_sm"] if small else FONTS["ui"]
        defaults = dict(
            text=label, bg=bg, fg=fg, activebackground=hover_bg,
            activeforeground=fg, relief="flat", bd=0, cursor="hand2",
            font=font, padx=10 if not small else 6,
            pady=5 if not small else 3,
        )
        defaults.update(kw)
        super().__init__(master, **defaults)
        self._bg = bg
        self._hover = hover_bg
        self.bind("<Enter>", lambda e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg))


class StatusBar(tk.Frame):
    def __init__(self, master, **kw):
        kw["bg"] = COLORS["bg_darkest"]
        super().__init__(master, **kw)
        self._items: dict[str, tk.Label] = {}

    def set(self, key: str, text: str, color: str = None):
        color = color or COLORS["text_secondary"]
        if key not in self._items:
            sep = tk.Label(self, text=" │ ", bg=COLORS["bg_darkest"],
                           fg=COLORS["border_bright"], font=FONTS["ui_sm"])
            sep.pack(side="left")
            lbl = tk.Label(self, text=text, bg=COLORS["bg_darkest"],
                           fg=color, font=FONTS["ui_sm"])
            lbl.pack(side="left")
            self._items[key] = lbl
        else:
            self._items[key].config(text=text, fg=color)


class ScrolledFrame(tk.Frame):
    """A frame with an internal canvas + scrollbar for vertical scrolling."""
    def __init__(self, master, **kw):
        bg = kw.pop("bg", COLORS["bg_dark"])
        super().__init__(master, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(self, orient="vertical",
                            command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win_id = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
        )
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.inner.bind("<MouseWheel>", self._on_mousewheel)

    def _on_inner_configure(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas.itemconfig(self._win_id, width=e.width)

    def _on_mousewheel(self, e):
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")