"""Allow `python -m utility_scripts_cli ...` to work the same as the CLI shim."""

import sys

from utility_scripts_cli.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
