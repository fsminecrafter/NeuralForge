# ⬡ NeuralForge Studio

An AI-powered coding assistant with a beautiful dark UI — built on **Ollama** for model inference and **tkinter** for the interface.

---

## Features

- 🤖 **Dual AI pipeline** — Agent AI reasons and calls tools; Scripter AI writes & applies code
- 🛠 **Built-in tools**: `script`, `read`, `rename`, `run`, `github_clone`
- 🔒 **Workspace sandbox** — AI stays inside your project unless you grant system-wide access
- ⚠️ **Command confirmation** — dangerous shell commands require your approval
- 📂 **File tree sidebar** with lazy loading
- 📎 **Context files** — attach any file for the AI to reference
- ⬇ **GitHub clone** directly into workspace
- 🎛 **Model selection** from 1.5B (2GB VRAM) to 70B (32GB VRAM)
- 🔄 **Streaming responses** with real-time token display

---

## Quick Start

### Linux / macOS / WSL
```bash
chmod +x setup.sh
./setup.sh
./launch.sh
```

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
launch.bat
```

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | With tkinter (standard on most installs) |
| [Ollama](https://ollama.com) | Runs models locally |
| A model | e.g. `ollama pull qwen2.5:7b` |

### Minimum VRAM by model tier

| Tier | Model example | VRAM |
|------|--------------|------|
| Low | qwen2.5:1.5b | ~2 GB |
| Mid | qwen2.5:7b | ~6 GB |
| High | qwen2.5-coder:14b | ~10 GB |
| Server | llama3.1:70b | ~32 GB |

> **airllm** (optional): Install for extreme VRAM compression — run 70B models on 16GB GPUs.

---

## Tool Reference

### `script`
Writes code to a file. Automatically triggers the **Applier AI** to intelligently merge the code.
```json
{"tool": "script", "path": "src/main.py", "language": "python", "content": "..."}
```

### `read`
Reads a file or lists a directory.
```json
{"tool": "read", "path": "src/"}
```

### `rename`
Moves or renames a file within the workspace.
```json
{"tool": "rename", "src": "old.py", "dst": "new.py"}
```

### `run`
Executes a shell command. Safe commands run immediately; others require your confirmation.
```json
{"tool": "run", "command": "pytest tests/", "cwd": ""}
```

### `github_clone`
Clones a repository into the workspace.
```json
{"tool": "github_clone", "repo_url": "https://github.com/user/repo"}
```

---

## Project Layout

```
neuralforge-studio/
├── main.py                 # Entry point
├── core/
│   ├── config.py           # App config, colour palette, model catalogue
│   └── ollama_backend.py   # Ollama streaming, tool-call parsing, applier AI
├── tools/
│   └── engine.py           # Tool implementations (script/read/rename/run)
├── ui/
│   ├── app.py              # Main window, orchestration
│   ├── chat_panel.py       # Streaming chat with tool-call cards
│   ├── sidebar.py          # File tree, context, GitHub
│   ├── settings_dialog.py  # Settings (models, Ollama, access, GitHub)
│   └── widgets.py          # Themed tkinter components
├── setup.sh                # Linux/macOS setup
├── setup.ps1               # Windows setup
└── requirements.txt
```

---

## Security

- AI is **sandboxed to the workspace** by default
- The `run` tool **asks for confirmation** on any command not in the safe-list
- Safe commands: `ls`, `cat`, `make`, `git`, `python`, `npm`, `cargo`, etc.
- Enable **System-Wide Access** in Settings only if you trust the model fully

---

## Config

Stored in `~/.neuralforge/config.json`:
```json
{
  "workspace": "/path/to/project",
  "agent_model": "qwen2.5:7b",
  "scripter_model": "qwen2.5-coder:7b",
  "ollama_url": "http://localhost:11434",
  "system_wide_access": false,
  "github_token": "",
  "context_files": []
}
```
