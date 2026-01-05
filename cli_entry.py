#!/usr/bin/env python3
"""
Entry point for DonutAI CLI.

This file can be used as the main entry point for the CLI.
Usage: python cli_entry.py <command> [options]
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cli.main import cli

if __name__ == '__main__':
    cli()

