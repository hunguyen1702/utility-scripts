#!/bin/sh
# uninstall.sh — remove utility-scripts-cli from ~/.local
#
# Equivalent to: sh install.sh --uninstall
set -eu
PREFIX="${HOME}/.local"
SHIM="${PREFIX}/bin/utility-scripts-cli"
SHARE_DIR="${PREFIX}/share/utility-scripts-cli"

rm -f "$SHIM"
rm -rf "$SHARE_DIR"
echo "Removed $SHIM"
echo "Removed $SHARE_DIR"
