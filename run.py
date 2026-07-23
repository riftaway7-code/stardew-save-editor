#!/usr/bin/env python3
"""Entry point for running the app from source during development.

    python run.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from svse.gui.app import main

if __name__ == "__main__":
    sys.exit(main())
