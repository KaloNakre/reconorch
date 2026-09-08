"""
Base class every tool adapter implements. An "adapter" wraps a single
external CLI tool (nmap, nikto, gobuster, sqlmap, ...) behind a common
interface: build a command, run it via subprocess, parse the output into
a structured result.

Adding a new tool = subclass ToolAdapter, implement build_command() and
parse_output(). Nothing else in the orchestrator needs to change.
"""
from __future__ import annotations

import dataclasses
import shlex
import subprocess
import time
from typing import Any


@dataclasses.dataclass
class ScanResult:
    tool: str
    target: str
    started_at: float
    finished_at: float
    returncode: int
    command: str
    stdout: str
    stderr: str
    parsed: dict[str, Any] = dataclasses.field(default_factory=dict)
    error: str | None = None

    @property
    def duration(self) -> float:
        return self.finished_at - self.started_at

    @property
    def ok(self) -> bool:
        return self.error is None and self.returncode == 0


class ToolAdapter:
    """Override `name`, `build_command`, and `parse_output` in subclasses."""

    name: str = "base"
    binary: str = ""            # e.g. "nmap" — must be on PATH
    timeout_seconds: int = 600  # hard kill-switch so one hung tool can't stall a worker

    def __init__(self, **args: Any):
        self.args = args

    def build_command(self, target: str) -> list[str]:
        """Return the argv list to execute. Never build this with shell=True."""
        raise NotImplementedError

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
        """Turn raw stdout/stderr into a structured dict. Default: pass-through."""
        return {"raw_lines": stdout.splitlines()[:500]}

    def run(self, target: str) -> ScanResult:
        cmd = self.build_command(target)
        started = time.time()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                shell=False,          # never shell=True: avoids injection via target/args
                check=False,
            )
            parsed = self.parse_output(proc.stdout, proc.stderr, proc.returncode)
            return ScanResult(
                tool=self.name,
                target=target,
                started_at=started,
                finished_at=time.time(),
                returncode=proc.returncode,
                command=" ".join(shlex.quote(c) for c in cmd),
                stdout=proc.stdout[-20000:],   # cap stored size
                stderr=proc.stderr[-5000:],
                parsed=parsed,
            )
        except subprocess.TimeoutExpired as e:
            return ScanResult(
                tool=self.name, target=target, started_at=started, finished_at=time.time(),
                returncode=-1, command=" ".join(shlex.quote(c) for c in cmd),
                stdout=(e.stdout or ""), stderr=(e.stderr or ""),
                error=f"timeout after {self.timeout_seconds}s",
            )
        except FileNotFoundError:
            return ScanResult(
                tool=self.name, target=target, started_at=started, finished_at=time.time(),
                returncode=-1, command=" ".join(shlex.quote(c) for c in cmd),
                stdout="", stderr="",
                error=f"binary not found on PATH: {self.binary!r}",
            )
