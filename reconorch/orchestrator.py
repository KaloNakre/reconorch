"""
Core orchestrator: uses Ray to run tool adapters in parallel across targets.

Design:
- Each (tool, target) pair becomes one Ray remote task.
- max_concurrent limits how many run at once (via Ray's resource scheduling).
- Results stream back and get persisted immediately, so a crash mid-run
  doesn't lose already-finished scans.
"""
from __future__ import annotations

import logging

import ray

from .config import AppConfig, ToolConfig
from .registry import resolve_adapter
from .storage import ResultStore
from .tools.base import ScanResult

logger = logging.getLogger("reconorch.orchestrator")


@ray.remote
def _run_one(adapter_path: str, adapter_args: dict, target_host: str) -> ScanResult:
    """Runs inside a Ray worker process. Must be a plain function (not a method)
    so Ray can pickle and ship it to any worker."""
    cls = resolve_adapter(adapter_path)
    adapter = cls(**adapter_args)
    return adapter.run(target_host)


class Orchestrator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.store = ResultStore(config.db_path)
        self._ray_started = False

    def start(self) -> None:
        if ray.is_initialized():
            self._ray_started = True
            return
        if self.config.ray_address:
            ray.init(address=self.config.ray_address)
        else:
            ray.init(num_cpus=self.config.max_concurrent, ignore_reinit_error=True)
        self._ray_started = True

    def stop(self) -> None:
        if self._ray_started and ray.is_initialized():
            ray.shutdown()
            self._ray_started = False

    def run_tool_once(self, tool: ToolConfig) -> list[ScanResult]:
        """Fires off one Ray task per target for this tool, waits for all, saves results."""
        if not tool.enabled:
            logger.info("skipping disabled tool: %s", tool.name)
            return []

        targets = self.config.targets_for(tool)
        if not targets:
            logger.warning("tool %s has no matching targets, skipping", tool.name)
            return []

        futures = [
            _run_one.remote(tool.adapter, tool.args, t.host)
            for t in targets
        ]

        results: list[ScanResult] = []
        for future in futures:
            result: ScanResult = ray.get(future)
            self.store.save(result)
            results.append(result)
            status = "OK" if result.ok else f"FAILED ({result.error or result.returncode})"
            logger.info("[%s] %s -> %s (%.1fs)", result.tool, result.target, status, result.duration)

        return results

    def run_all_once(self) -> list[ScanResult]:
        """Runs every enabled tool (one-shot pass) across its targets."""
        all_results: list[ScanResult] = []
        for tool in self.config.tools:
            all_results.extend(self.run_tool_once(tool))
        return all_results
