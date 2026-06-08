"""Env loader for the installed utility-scripts-cli.

Priority (highest wins):
  1. process env (already-set vars)
  2. $XDG_CONFIG_HOME/utility-scripts-cli/profiles/<profile>.env
     or ~/.config/utility-scripts-cli/profiles/<profile>.env
     where <profile> comes from --profile or UTILITY_SCRIPTS_PROFILE
  3. $XDG_CONFIG_HOME/utility-scripts-cli/.env  (if XDG_CONFIG_HOME is set)
  4. ~/.config/utility-scripts-cli/.env        (XDG default)
  5. nothing — caller must validate required keys
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


def _profile_name(explicit_profile: Optional[str]) -> Optional[str]:
    profile = explicit_profile or os.environ.get("UTILITY_SCRIPTS_PROFILE")
    if not profile:
        return None

    trimmed = profile.strip()
    if not trimmed:
        return None

    if "/" in trimmed or "\\" in trimmed or trimmed in {".", ".."}:
        raise ValueError(
            "Invalid profile name. Use a simple profile such as 'agent-a' or 'personal'."
        )

    return trimmed


def _profile_env_path(profile: str) -> Path:
    return config_dir() / "profiles" / f"{profile}.env"


def load_env(profile: Optional[str] = None) -> Optional[Path]:
    """Load the configured .env if present. Returns the path used, or None."""
    resolved_profile = _profile_name(profile)
    if resolved_profile:
        cfg = _profile_env_path(resolved_profile)
        if cfg.is_file():
            load_dotenv(cfg, override=False)
            return cfg

    cfg = config_dir() / ".env"
    if cfg.is_file():
        load_dotenv(cfg, override=False)
        return cfg
    return None
