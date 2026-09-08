"""
Example adapter: nmap.
Demonstrates the pattern — build_command() returns a safe argv list,
parse_output() extracts a light structured summary from stdout.
"""
from __future__ import annotations

import re
from typing import Any

from .base import ToolAdapter


class NmapAdapter(ToolAdapter):
    name = "nmap"
    binary = "nmap"
    timeout_seconds = 900

    def build_command(self, target: str) -> list[str]:
        ports = self.args.get("ports", "1-1000")
        extra_flags = self.args.get("flags", ["-sV", "-T4"])
        cmd = [self.binary, "-p", str(ports), *extra_flags, target]

        # NSE (Nmap Scripting Engine) support.
        # config example:
        #   args:
        #     scripts: ["default", "vuln"]        # script categories or names
        #     script_args: {"http.useragent": "reconorch"}   # optional --script-args
        scripts = self.args.get("scripts")
        if scripts:
            cmd.insert(1, f"--script={','.join(scripts)}")
            script_args = self.args.get("script_args")
            if script_args:
                kv = ",".join(f"{k}={v}" for k, v in script_args.items())
                cmd.insert(2, f"--script-args={kv}")

        return cmd

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
        open_ports = []
        for line in stdout.splitlines():
            m = re.match(r"^(\d+)/(tcp|udp)\s+open\s+(\S+)(.*)$", line.strip())
            if m:
                open_ports.append({
                    "port": int(m.group(1)),
                    "proto": m.group(2),
                    "service": m.group(3),
                    "detail": m.group(4).strip(),
                })
        # NSE script output lines look like "|_http-title: Example" or "| vulners:"
        script_findings = [
            ln.strip() for ln in stdout.splitlines()
            if ln.strip().startswith("|") or ln.strip().startswith("|_")
        ]

        return {
            "open_ports": open_ports,
            "open_port_count": len(open_ports),
            "script_findings": script_findings,
        }
