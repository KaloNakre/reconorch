"""
Example adapter: gobuster (directory/file brute-forcer).
Requires a wordlist path to be set in config args.
"""
from __future__ import annotations

from typing import Any

from .base import ToolAdapter


class GobusterAdapter(ToolAdapter):
    name = "gobuster"
    binary = "gobuster"
    timeout_seconds = 1200

    def build_command(self, target: str) -> list[str]:
        scheme = self.args.get("scheme", "http")
        wordlist = self.args.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        threads = str(self.args.get("threads", 20))
        return [
            self.binary, "dir",
            "-u", f"{scheme}://{target}",
            "-w", wordlist,
            "-t", threads,
            "-q",
        ]

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
        hits = [ln.strip() for ln in stdout.splitlines() if ln.strip().startswith("/")]
        return {"paths_found": hits, "path_count": len(hits)}
