"""Env loader for the installed utility-scripts-cli.

Priority (highest wins):
  1. process env (already-set vars)
  2. $XDG_CONFIG_HOME/utility-scripts-cli/.env  (if XDG_CONFIG_HOME is set)
  3. ~/.config/utility-scripts-cli/.env        (XDG default)
  4. nothing — caller must validate required keys
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "utility-scripts-cli"


def load_env() -> Optional[Path]:
    """Load the XDG config .env if present. Returns the path used, or None."""
    cfg = config_dir() / ".env"
    if cfg.is_file():
        load_dotenv(cfg, override=False)
        return cfg
    return None
