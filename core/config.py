"""
NeuralForge Studio — Configuration & Constants
"""
import os
import json
import platform

APP_NAME = "NeuralForge Studio"
APP_VERSION = "1.0.0"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".neuralforge")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# ── Colour palette ────────────────────────────────────────────────────────────
COLORS = {
    "bg_darkest":   "#0a0b0e",
    "bg_dark":      "#0f1117",
    "bg_panel":     "#141720",
    "bg_card":      "#1a1f2e",
    "bg_input":     "#111318",
    "bg_hover":     "#1e2435",
    "border":       "#252a3a",
    "border_bright":"#333a50",
    "accent":       "#4f8aff",
    "accent_glow":  "#2563eb",
    "accent_dim":   "#1e3a6e",
    "success":      "#22c55e",
    "warning":      "#f59e0b",
    "error":        "#ef4444",
    "text_primary": "#e8ecf4",
    "text_secondary":"#8892a4",
    "text_muted":   "#4a5568",
    "text_code":    "#a8d8a8",
    "highlight":    "#4f8aff22",
    "tool_script":  "#a855f7",
    "tool_read":    "#06b6d4",
    "tool_rename":  "#f59e0b",
    "tool_run":     "#ef4444",
    "user_bubble":  "#1e2d4a",
    "ai_bubble":    "#141a2a",
}

# ── Font stack ────────────────────────────────────────────────────────────────
FONTS = {
    "ui":       ("Segoe UI",    10),
    "ui_bold":  ("Segoe UI",    10, "bold"),
    "ui_sm":    ("Segoe UI",     9),
    "heading":  ("Segoe UI",    13, "bold"),
    "title":    ("Segoe UI",    16, "bold"),
    "mono":     ("Cascadia Code", 10),
    "mono_sm":  ("Cascadia Code",  9),
    "tag":      ("Segoe UI",     8, "bold"),
}

# ── Safe commands that don't need confirmation ────────────────────────────────
SAFE_COMMANDS = {
    "ls", "dir", "cd", "pwd", "echo", "cat", "head", "tail",
    "make", "chmod", "chown", "mkdir", "touch", "cp", "mv",
    "grep", "find", "wc", "sort", "uniq", "diff", "which",
    "python", "python3", "pip", "pip3", "node", "npm",
    "wget", "curl", "git", "cargo", "go", "rustc",
    "gcc", "g++", "clang", "javac", "java",
}

# ── Model catalogue ───────────────────────────────────────────────────────────
MODELS = {
    "scripter": [
        {"id": "qwen2.5-coder:1.5b",   "name": "Qwen2.5 Coder 1.5B",  "vram": "~2GB",  "tier": "low"},
        {"id": "qwen2.5-coder:3b",     "name": "Qwen2.5 Coder 3B",    "vram": "~4GB",  "tier": "mid"},
        {"id": "qwen2.5-coder:7b",     "name": "Qwen2.5 Coder 7B",    "vram": "~6GB",  "tier": "mid"},
        {"id": "qwen2.5-coder:14b",    "name": "Qwen2.5 Coder 14B",   "vram": "~10GB", "tier": "high"},
        {"id": "qwen2.5-coder:32b",    "name": "Qwen2.5 Coder 32B",   "vram": "~20GB", "tier": "server"},
        {"id": "deepseek-coder-v2:16b","name": "DeepSeek Coder V2 16B","vram": "~12GB", "tier": "high"},
    ],
    "agent": [
        {"id": "qwen2.5:1.5b",         "name": "Qwen2.5 1.5B",        "vram": "~2GB",  "tier": "low"},
        {"id": "qwen2.5:7b",           "name": "Qwen2.5 7B",          "vram": "~6GB",  "tier": "mid"},
        {"id": "llama3.2:3b",          "name": "Llama 3.2 3B",        "vram": "~3GB",  "tier": "low"},
        {"id": "llama3.1:8b",          "name": "Llama 3.1 8B",        "vram": "~6GB",  "tier": "mid"},
        {"id": "mistral:7b",           "name": "Mistral 7B",          "vram": "~5GB",  "tier": "mid"},
        {"id": "mixtral:8x7b",         "name": "Mixtral 8x7B",        "vram": "~28GB", "tier": "server"},
        {"id": "llama3.1:70b",         "name": "Llama 3.1 70B",       "vram": "~32GB", "tier": "server"},
    ],
}

# ── Default config ────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "workspace": "",
    "agent_model": "qwen2.5:7b",
    "scripter_model": "qwen2.5-coder:7b",
    "ollama_url": "http://localhost:11434",
    "system_wide_access": False,
    "theme": "dark",
    "github_token": "",
    "context_files": [],
}

def load_config() -> dict:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
            # merge with defaults so new keys are always present
            return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def save_config(cfg: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def is_windows() -> bool:
    return platform.system() == "Windows"
