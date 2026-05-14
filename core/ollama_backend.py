"""
NeuralForge Studio — Ollama AI Backend
Handles model management, streaming, and tool-call parsing.
"""
import json
import re
import threading
import urllib.request
import urllib.error
import urllib.parse
from typing import Callable, Optional

TOOL_SCHEMA = """
You are NeuralForge, an AI coding assistant with access to the following tools.
Always respond with tool calls as JSON blocks when you need to do something.

## Available Tools

### script
Write code to a file.
```json
{{"tool": "script", "path": "relative/path/file.py", "language": "python", "content": "...code..."}}
```

### read
Read a file or list a directory.
```json
{{"tool": "read", "path": "relative/path"}}
```

### rename
Rename or move a file.
```json
{{"tool": "rename", "src": "old/path.py", "dst": "new/path.py"}}
```

### run
Execute a shell command.
```json
{{"tool": "run", "command": "python main.py", "cwd": ""}}
```

## Rules
- ALWAYS confine operations to the workspace.
- When you need to create or modify code, use the `script` tool.
- Explain what you're doing in plain text before and after tool calls.
- After using the `script` tool, a separate applier AI will apply the code automatically.
- Combine multiple tool calls in one response when logical.

## Workspace
{workspace}

## Context Files
{context}
"""


def _make_tool_prompt(workspace: str, context: str) -> str:
    return TOOL_SCHEMA.format(workspace=workspace or "(none selected)",
                              context=context or "(none)")


def parse_tool_calls(text: str) -> list[dict]:
    """Extract all JSON tool calls from AI response text."""
    calls = []
    # Match ```json ... ``` blocks or bare { "tool": ... } objects
    patterns = [
        r"```json\s*(\{.*?\})\s*```",
        r"```\s*(\{[^`]*?\"tool\"[^`]*?\})\s*```",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.DOTALL):
            try:
                obj = json.loads(match.group(1))
                if "tool" in obj:
                    calls.append(obj)
            except json.JSONDecodeError:
                pass
    return calls


class OllamaBackend:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> tuple[bool, str]:
        try:
            with urllib.request.urlopen(
                f"{self.base_url}/api/tags", timeout=3
            ) as r:
                return True, "Ollama is running"
        except Exception as e:
            return False, str(e)

    def list_models(self) -> list[str]:
        try:
            with urllib.request.urlopen(
                f"{self.base_url}/api/tags", timeout=5
            ) as r:
                data = json.loads(r.read())
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def pull_model(self, model: str, progress_cb: Callable[[str], None] = None):
        """Pull (download) a model from Ollama. Blocking."""
        url = f"{self.base_url}/api/pull"
        payload = json.dumps({"name": model}).encode()
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=3600) as r:
                for line in r:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        status = obj.get("status", "")
                        if progress_cb:
                            progress_cb(status)
                        if obj.get("error"):
                            return False, obj["error"]
                    except Exception:
                        pass
            return True, "Download complete"
        except Exception as e:
            return False, str(e)

    def chat_stream(self, model: str, messages: list[dict],
                    system: str = "",
                    on_token: Callable[[str], None] = None,
                    on_done: Callable[[str], None] = None,
                    on_error: Callable[[str], None] = None):
        """Stream a chat completion. Runs in a background thread."""

        def _run():
            url = f"{self.base_url}/api/chat"
            msgs = []
            if system:
                msgs.append({"role": "system", "content": system})
            msgs.extend(messages)
            payload = json.dumps({
                "model": model,
                "messages": msgs,
                "stream": True,
            }).encode()
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            full_text = ""
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    for line in r:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                            token = obj.get("message", {}).get("content", "")
                            full_text += token
                            if on_token and token:
                                on_token(token)
                            if obj.get("done"):
                                break
                        except Exception:
                            pass
                if on_done:
                    on_done(full_text)
            except Exception as e:
                if on_error:
                    on_error(str(e))

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def generate(self, model: str, prompt: str, system: str = "") -> tuple[bool, str]:
        """Blocking generate for the applier AI."""
        url = f"{self.base_url}/api/generate"
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read())
                return True, data.get("response", "")
        except Exception as e:
            return False, str(e)


APPLIER_SYSTEM = """
You are a code applier. The user will give you a file path, original content, and new code.
Your job is to output ONLY the final merged file content — no explanation, no markdown, no backticks.
Just the raw file content that should be written to disk.
If the new code is a complete replacement, output it as-is.
If it is a patch or partial snippet, intelligently merge it into the original.
"""


class ApplierAI:
    """Secondary AI that applies code from the scripter."""

    def __init__(self, backend: OllamaBackend, model: str):
        self.backend = backend
        self.model = model

    def apply(self, path: str, original: str, new_code: str) -> tuple[bool, str]:
        prompt = (
            f"File: {path}\n\n"
            f"=== ORIGINAL CONTENT ===\n{original}\n\n"
            f"=== NEW CODE TO APPLY ===\n{new_code}\n\n"
            "Output the final file content:"
        )
        return self.backend.generate(self.model, prompt, system=APPLIER_SYSTEM)