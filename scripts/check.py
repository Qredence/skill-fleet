#!/usr/bin/env python3
"""
Unified Development & Quality Checker.

Wraps various dev scripts:
- quality.sh (Lint, Test, Typecheck)
- run_dev.sh (Start Dev Server)
- cleanup-technical-debt.sh
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_shell_script(script_name: str, args: list[str] = None):
    """Run a shell script from scripts/internal/dev/."""
    script_path = Path(__file__).parent / "internal" / "dev" / script_name
    cmd = [str(script_path)]
    if args:
        cmd.extend(args)

    print(f"🚀 Running {script_name}...")
    try:
        # Check if executable
        if not os.access(script_path, os.X_OK):
            os.chmod(script_path, 0o700)

        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


import os


def main():
    parser = argparse.ArgumentParser(description="Skill Fleet Dev Tools")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Quality
    subparsers.add_parser("quality", help="Run full quality suite (lint, test, typecheck)")

    # Dev Server
    subparsers.add_parser("dev", help="Start development server & TUI")

    # Cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="Run technical debt cleanup")
    cleanup_parser.add_argument(
        "mode", nargs="?", default="all", help="Cleanup mode (quick, all, verify)"
    )

    args = parser.parse_args()

    if args.command == "quality":
        run_shell_script("quality.sh")
    elif args.command == "dev":
        run_shell_script("run_dev.sh")
    elif args.command == "cleanup":
        run_shell_script("cleanup-technical-debt.sh", [args.mode])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
