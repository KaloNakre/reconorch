"""
Loads and validates the YAML configuration that drives the orchestrator.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import yaml


@dataclasses.dataclass
class TargetConfig:
    name: str
    host: str
    tags: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ToolConfig:
    name: str
    adapter: str                 # dotted path to ToolAdapter subclass, e.g. "cyberorch.tools.nmap.NmapAdapter"
    enabled: bool = True
    interval_seconds: int | None = None   # None = run once, int = repeat every N seconds
    args: dict[str, Any] = dataclasses.field(default_factory=dict)
    targets: list[str] = dataclasses.field(default_factory=list)   # target names, empty = all targets


@dataclasses.dataclass
class AppConfig:
    ray_address: str | None       # None = start local Ray cluster; "auto" or "ray://host:10001" to connect
    max_concurrent: int
    db_path: str
    targets: list[TargetConfig]
    tools: list[ToolConfig]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppConfig":
        data = yaml.safe_load(Path(path).read_text())

        targets = [TargetConfig(**t) for t in data.get("targets", [])]
        tools = [ToolConfig(**t) for t in data.get("tools", [])]

        return cls(
            ray_address=data.get("ray_address"),
            max_concurrent=data.get("max_concurrent", 8),
            db_path=data.get("db_path", "results.db"),
            targets=targets,
            tools=tools,
        )

    def targets_for(self, tool: ToolConfig) -> list[TargetConfig]:
        if not tool.targets:
            return self.targets
        wanted = set(tool.targets)
        return [t for t in self.targets if t.name in wanted]
