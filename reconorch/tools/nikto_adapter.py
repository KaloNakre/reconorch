"""
Example adapter: nikto (web server scanner).
"""
from __future__ import annotations

from typing import Any

from .base import ToolAdapter


class NiktoAdapter(ToolAdapter):
    name = "nikto"
    binary = "nikto"
    timeout_seconds = 900

    def build_command(self, target: str) -> list[str]:
        scheme = self.args.get("scheme", "http")
        return [self.binary, "-h", f"{scheme}://{target}", "-Tuning", "x6", "-nointeractive"]

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
        findings = [ln.strip() for ln in stdout.splitlines() if ln.strip().startswith("+")]
        return {"findings": findings, "finding_count": len(findings)}
