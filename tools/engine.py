"""
NeuralForge Studio — Tool Engine
Implements: script, read, rename, run, github_clone
"""
import os
import subprocess
import shutil
import tempfile
import json
import platform
import stat
from typing import Optional, Tuple

from core.config import SAFE_COMMANDS


class ToolError(Exception):
    pass


class WorkspaceGuard:
    """Enforces that all file operations stay inside the workspace."""

    def __init__(self, workspace: str, system_wide: bool = False):
        self.workspace = os.path.realpath(workspace) if workspace else ""
        self.system_wide = system_wide

    def resolve(self, path: str) -> str:
        """Resolve path relative to workspace and validate it."""
        if not path:
            raise ToolError("Empty path provided.")
        if os.path.isabs(path):
            resolved = os.path.realpath(path)
        else:
            resolved = os.path.realpath(os.path.join(self.workspace, path))
        if not self.system_wide and self.workspace:
            if not resolved.startswith(self.workspace):
                raise ToolError(
                    f"Access denied: '{path}' is outside the workspace.\n"
                    f"Enable 'System-Wide Access' to allow this."
                )
        return resolved


class ToolEngine:
    def __init__(self, workspace: str = "", system_wide: bool = False,
                 confirm_callback=None, log_callback=None):
        self.workspace = workspace
        self.system_wide = system_wide
        self.guard = WorkspaceGuard(workspace, system_wide)
        # callbacks
        self.confirm_callback = confirm_callback   # (title, msg) -> bool
        self.log_callback = log_callback           # (level, msg)

    def _log(self, level: str, msg: str):
        if self.log_callback:
            self.log_callback(level, msg)

    # ── SCRIPT ────────────────────────────────────────────────────────────────
    def tool_script(self, path: str, content: str,
                    language: str = "python") -> dict:
        """Write script content to a file inside the workspace."""
        resolved = self.guard.resolve(path)
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)
        # make executable if shell script
        if language in ("bash", "sh", "shell"):
            os.chmod(resolved, os.stat(resolved).st_mode | stat.S_IEXEC)
        self._log("success", f"Script written → {resolved}")
        return {"status": "ok", "path": resolved, "bytes": len(content)}

    # ── READ ──────────────────────────────────────────────────────────────────
    def tool_read(self, path: str, start_line: int = 0,
                  end_line: int = -1) -> dict:
        """Read a file (or directory listing) from workspace."""
        resolved = self.guard.resolve(path)
        if os.path.isdir(resolved):
            entries = []
            for name in sorted(os.listdir(resolved)):
                full = os.path.join(resolved, name)
                kind = "dir" if os.path.isdir(full) else "file"
                size = os.path.getsize(full) if kind == "file" else 0
                entries.append({"name": name, "type": kind, "size": size})
            return {"status": "ok", "type": "directory", "entries": entries}
        if not os.path.exists(resolved):
            raise ToolError(f"File not found: {resolved}")
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        if end_line == -1:
            end_line = len(lines)
        selected = lines[start_line:end_line]
        content = "".join(selected)
        self._log("info", f"Read {len(selected)} lines from {resolved}")
        return {"status": "ok", "type": "file", "content": content,
                "total_lines": len(lines), "path": resolved}

    # ── RENAME ────────────────────────────────────────────────────────────────
    def tool_rename(self, src: str, dst: str) -> dict:
        """Rename or move a file within the workspace."""
        r_src = self.guard.resolve(src)
        r_dst = self.guard.resolve(dst)
        if not os.path.exists(r_src):
            raise ToolError(f"Source not found: {r_src}")
        os.makedirs(os.path.dirname(r_dst), exist_ok=True)
        shutil.move(r_src, r_dst)
        self._log("success", f"Renamed: {r_src} → {r_dst}")
        return {"status": "ok", "src": r_src, "dst": r_dst}

    # ── RUN ───────────────────────────────────────────────────────────────────
    def tool_run(self, command: str, cwd: str = "") -> dict:
        """Execute a shell command, with confirmation for dangerous ones."""
        # Determine working directory
        work_dir = self.guard.resolve(cwd) if cwd else self.workspace
        if not work_dir or not os.path.isdir(work_dir):
            work_dir = self.workspace or os.getcwd()

        # Check if command needs confirmation
        base_cmd = command.strip().split()[0].lower() if command.strip() else ""
        needs_confirm = base_cmd not in SAFE_COMMANDS

        if needs_confirm and self.confirm_callback:
            ok = self.confirm_callback(
                "⚠  Confirm Command Execution",
                f"The AI wants to run:\n\n  {command}\n\n"
                f"Working directory: {work_dir}\n\n"
                "Allow execution?"
            )
            if not ok:
                return {"status": "denied", "command": command,
                        "reason": "User denied execution."}

        # Guard: if not system-wide, block absolute paths outside workspace
        if not self.system_wide and self.workspace:
            resolved_cwd = os.path.realpath(work_dir)
            if not resolved_cwd.startswith(os.path.realpath(self.workspace)):
                raise ToolError("Run cwd is outside the workspace.")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self._log("info", f"RUN: {command} → exit {result.returncode}")
            return {
                "status": "ok",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command,
            }
        except subprocess.TimeoutExpired:
            raise ToolError("Command timed out after 120 seconds.")

    # ── GITHUB CLONE ──────────────────────────────────────────────────────────
    def tool_github_clone(self, repo_url: str, token: str = "",
                          dest: str = "") -> dict:
        """Clone a GitHub repository into the workspace."""
        if not self.workspace:
            raise ToolError("No workspace selected.")
        if token and "github.com" in repo_url:
            # inject token into URL
            repo_url = repo_url.replace(
                "https://github.com",
                f"https://{token}@github.com"
            )
        if not dest:
            dest = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        resolved_dest = self.guard.resolve(dest)
        cmd = f"git clone {repo_url} {resolved_dest}"
        result = self.tool_run(cmd, cwd=self.workspace)
        return {**result, "clone_path": resolved_dest}
