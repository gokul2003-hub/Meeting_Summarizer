#!/usr/bin/env python3
"""Root CLI entry point for AI Meeting Intelligence Suite."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from cli.cli import run_cli

if __name__ == "__main__":
    run_cli()
