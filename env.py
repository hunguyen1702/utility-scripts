"""Project-wide env loader.

Import this at the top of any script in this repo to load `.env` from the
project root. Variables already set in the shell win (so `export` for
debug/temp overrides continues to work without editing `.env`).
"""

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
