"""
Continuous mode: repeatedly runs each enabled tool at its configured
interval_seconds, forever, until interrupted (Ctrl+C).

Kept deliberately simple (no external cron dependency) — each tool
tracks its own "next run" time in a single loop.
"""
from __future__ import annotations

import logging
import time

from .config import ToolConfig
from .orchestrator import Orchestrator

logger = logging.getLogger("cyberorch.scheduler")


class Scheduler:
    def __init__(self, orchestrator: Orchestrator, poll_interval: float = 5.0):
        self.orchestrator = orchestrator
        self.poll_interval = poll_interval
        self._next_run: dict[str, float] = {}

    def _due_tools(self, now: float) -> list[ToolConfig]:
        due = []
        for tool in self.orchestrator.config.tools:
            if not tool.enabled:
                continue
            if tool.interval_seconds is None:
                # one-shot tools only ever run once, on the very first pass
                if tool.name not in self._next_run:
                    due.append(tool)
                    self._next_run[tool.name] = float("inf")  # never again
                continue
            next_run = self._next_run.get(tool.name, 0.0)
            if now >= next_run:
                due.append(tool)
                self._next_run[tool.name] = now + tool.interval_seconds
        return due

    def run_forever(self) -> None:
        logger.info("scheduler started (poll every %.1fs, Ctrl+C to stop)", self.poll_interval)
        try:
            while True:
                now = time.time()
                for tool in self._due_tools(now):
                    logger.info("running scheduled tool: %s", tool.name)
                    self.orchestrator.run_tool_once(tool)
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("scheduler stopped by user")
