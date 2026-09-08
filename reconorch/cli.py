"""
Command-line entry point.

Usage:
    reconorch scan --config config.yaml            # run every enabled tool once
    reconorch scan --config config.yaml --tool nmap  # run just one tool once
    reconorch watch --config config.yaml            # continuous mode, runs forever
    reconorch results --config config.yaml --tool nmap --target myserver
    reconorch check-tools --config config.yaml       # verify binaries are on PATH
"""
from __future__ import annotations

import argparse
import logging
import shutil
import sys

from .config import AppConfig
from .orchestrator import Orchestrator
from .registry import resolve_adapter
from .scheduler import Scheduler

BANNER = r"""
    ____                           ____             __
   / __ \___  _________  ____  ___/ __ \_________  / /_
  / /_/ / _ \/ ___/ __ \/ __ \/ _/ / / / ___/ __ \/ __ \
 / _, _/  __/ /__/ /_/ / / / /  / /_/ / /__/ / / / / / /
/_/ |_|\___/\___/\____/_/ /_/__/\____/\___/_/ /_/_/ /_/

Reconorch security testing automation. Only scan targets you own or
have explicit written permission to test.
"""


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def cmd_scan(args: argparse.Namespace) -> int:
    config = AppConfig.from_yaml(args.config)
    orch = Orchestrator(config)
    orch.start()
    try:
        if args.tool:
            tool = next((t for t in config.tools if t.name == args.tool), None)
            if tool is None:
                print(f"no such tool in config: {args.tool!r}", file=sys.stderr)
                return 1
            results = orch.run_tool_once(tool)
        else:
            results = orch.run_all_once()
        ok = sum(1 for r in results if r.ok)
        print(f"\n{ok}/{len(results)} scans completed successfully. Results saved to {config.db_path}")
        return 0
    finally:
        orch.stop()


def cmd_watch(args: argparse.Namespace) -> int:
    config = AppConfig.from_yaml(args.config)
    orch = Orchestrator(config)
    orch.start()
    try:
        Scheduler(orch, poll_interval=args.poll_interval).run_forever()
        return 0
    finally:
        orch.stop()


def cmd_results(args: argparse.Namespace) -> int:
    config = AppConfig.from_yaml(args.config)
    from .storage import ResultStore
    store = ResultStore(config.db_path)
    rows = store.latest(tool=args.tool, target=args.target, limit=args.limit)
    for row in rows:
        status = "OK" if row["ok"] else f"FAILED ({row['error']})"
        print(f"[{row['tool']}] {row['target']} -> {status} ({row['duration']:.1f}s) @ {row['started_at']}")
    return 0


def cmd_check_tools(args: argparse.Namespace) -> int:
    config = AppConfig.from_yaml(args.config)
    for tool in config.tools:
        cls = resolve_adapter(tool.adapter)
        found = shutil.which(cls.binary) is not None
        mark = "OK" if found else "MISSING"
        print(f"[{mark}] {tool.name} -> requires {cls.binary!r} on PATH")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reconorch", description="Security scan orchestrator")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="run enabled tools once")
    p_scan.add_argument("--config", required=True)
    p_scan.add_argument("--tool", help="run only this tool (by name from config)")
    p_scan.set_defaults(func=cmd_scan)

    p_watch = sub.add_parser("watch", help="run continuously per configured intervals")
    p_watch.add_argument("--config", required=True)
    p_watch.add_argument("--poll-interval", type=float, default=5.0)
    p_watch.set_defaults(func=cmd_watch)

    p_results = sub.add_parser("results", help="show saved results")
    p_results.add_argument("--config", required=True)
    p_results.add_argument("--tool")
    p_results.add_argument("--target")
    p_results.add_argument("--limit", type=int, default=50)
    p_results.set_defaults(func=cmd_results)

    p_check = sub.add_parser("check-tools", help="verify required binaries are installed")
    p_check.add_argument("--config", required=True)
    p_check.set_defaults(func=cmd_check_tools)

    return parser


def main() -> int:
    print(BANNER)
    parser = build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
