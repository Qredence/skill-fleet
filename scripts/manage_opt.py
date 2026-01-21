#!/usr/bin/env python3
"""
Unified Optimization Manager for Skill Fleet.

Orchestrates DSPy optimization workflows, including:
- MIPROv2 optimization
- GEPA optimization
- Benchmarking
"""

import argparse
import sys
from pathlib import Path
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def run_script(script_name: str, args: list[str] = None):
    """Run a script with arguments."""
    script_path = Path(__file__).parent / "internal" / "opt" / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    print(f"🚀 Running {script_name}...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
        sys.exit(e.returncode)


def main():
    parser = argparse.ArgumentParser(description="Skill Fleet Optimization Manager")
    subparsers = parser.add_subparsers(dest="command", help="Optimization command")

    # MIPROv2
    mipro_parser = subparsers.add_parser("mipro", help="Run MIPROv2 optimization")
    mipro_parser.add_argument("--trainset", default="config/training/trainset_v4.json")
    mipro_parser.add_argument("--auto", default="medium", choices=["light", "medium", "heavy"])

    # GEPA
    gepa_parser = subparsers.add_parser("gepa", help="Run GEPA optimization")
    gepa_parser.add_argument("--auto", default="light", choices=["light", "medium", "heavy"])

    # Benchmark
    subparsers.add_parser("benchmark", help="Benchmark optimizers")

    args = parser.parse_args()

    if args.command == "mipro":
        # Pass args via env vars or modify run_optimization.py to accept CLI args
        # For now, we'll just run it as-is since it has defaults
        print(f"Running MIPROv2 with auto={args.auto}")
        # Note: run_optimization.py currently hardcodes some values
        run_script("run_optimization.py")

    elif args.command == "gepa":
        print(f"Running GEPA with auto={args.auto}")
        # Pass auto level via env var as supported by run_gepa_optimization.py
        import os

        os.environ["GEPA_AUTO_LEVEL"] = args.auto
        run_script("run_gepa_optimization.py")

    elif args.command == "benchmark":
        run_script("benchmark_optimizers.py")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
