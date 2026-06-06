#!/bin/sh
# install.sh — install utility-scripts-cli to ~/.local
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/hunguyen1702/utility-scripts/main/install.sh | sh -s -- --yes
#   sh install.sh --yes
#   sh install.sh --prefix /opt/local --yes
#   sh install.sh --uninstall
#
# This installer is pure POSIX sh. It does not require Python at install
# time for parsing; it only needs python3 + curl. Everything else (deps,
# the CLI itself) lives in a hermetic venv under PREFIX.
set -eu

REPO_RAW="https://raw.githubusercontent.com/hunguyen1702/utility-scripts/main"
PREFIX="${HOME}/.local"
SHARE_DIR="${PREFIX}/share/utility-scripts-cli"
VENV_DIR="${SHARE_DIR}/venv"
LIB_DIR="${SHARE_DIR}/lib"
BIN_DIR="${PREFIX}/bin"
SHIM="${BIN_DIR}/utility-scripts-cli"

ASSUME_YES=0
DO_UNINSTALL=0

log()  { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

# --- arg parsing --------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --yes)        ASSUME_YES=1 ;;
    --prefix)     [ $# -ge 2 ] || die "--prefix requires a value"; PREFIX="$2"; shift ;;
    --prefix=*)   PREFIX="${1#--prefix=}" ;;
    --uninstall)  DO_UNINSTALL=1 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *) die "unknown argument: $1" ;;
  esac
  shift
done

# Recompute paths if --prefix changed.
SHARE_DIR="${PREFIX}/share/utility-scripts-cli"
VENV_DIR="${SHARE_DIR}/venv"
LIB_DIR="${SHARE_DIR}/lib"
BIN_DIR="${PREFIX}/bin"
SHIM="${BIN_DIR}/utility-scripts-cli"

# --- uninstall path -----------------------------------------------------------
if [ "$DO_UNINSTALL" = 1 ]; then
  rm -f "$SHIM"
  rm -rf "$SHARE_DIR"
  log "Removed $SHIM"
  log "Removed $SHARE_DIR"
  exit 0
fi

# --- preflight: tty detection, prompts ---------------------------------------
is_tty() { [ -t 0 ] && [ -t 1 ]; }

prompt_yes() {
  printf '%s [y/N] ' "$1"
  read -r ans || return 1
  case "$ans" in
    y|Y|yes|YES) return 0 ;;
    *) return 1 ;;
  esac
}

if [ "$ASSUME_YES" != 1 ]; then
  if is_tty; then
    prompt_yes "Install utility-scripts-cli to ${PREFIX}?" || die "aborted by user"
  else
    cat <<EOF >&2
utility-scripts-cli installer

This will install to:  ${PREFIX}
  - binary:             ${SHIM}
  - code:               ${LIB_DIR}
  - venv:               ${VENV_DIR}

Re-run with --yes to proceed non-interactively:

  curl -fsSL ${REPO_RAW}/install.sh | sh -s -- --yes
EOF
    exit 1
  fi
fi

# --- prereqs ------------------------------------------------------------------
command -v python3 >/dev/null 2>&1 || die "python3 not found on PATH"
command -v curl    >/dev/null 2>&1 || die "curl not found on PATH"

PY_VERSION=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
case "$PY_VERSION" in
  3.[89]|3.1[0-9]|3.2[0-9]) ;;
  *) die "Python 3.8+ required (found $PY_VERSION)" ;;
esac

# --- create dirs --------------------------------------------------------------
mkdir -p "$SHARE_DIR" "$BIN_DIR"

# --- create or reuse venv -----------------------------------------------------
if [ ! -x "${VENV_DIR}/bin/python" ]; then
  log "Creating venv at ${VENV_DIR}"
  python3 -m venv "$VENV_DIR"
else
  log "Reusing existing venv at ${VENV_DIR}"
fi

# --- download files from raw GitHub into a temp dir ---------------------------
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

log "Downloading utility-scripts-cli from ${REPO_RAW}"

fetch() {
  # fetch <remote-path> <local-path>
  curl -fsSL "${REPO_RAW}/$1" -o "$2" || die "download $1 failed"
}

fetch "requirements.txt" "${TMP}/requirements.txt"
fetch "bin/utility-scripts-cli" "${TMP}/utility-scripts-cli"

for f in __init__.py __main__.py cli.py env.py; do
  fetch "utility_scripts_cli/${f}" "${TMP}/pkg_${f}"
done
for f in __init__.py slack_upload_image.py; do
  fetch "utility_scripts_cli/commands/${f}" "${TMP}/cmd_${f}"
done

# --- install Python deps into the venv ---------------------------------------
log "Installing Python dependencies into venv"
"${VENV_DIR}/bin/pip" install --quiet --disable-pip-version-check \
  -r "${TMP}/requirements.txt" || die "pip install failed"

# --- copy code into the install dir ------------------------------------------
rm -rf "$LIB_DIR"
mkdir -p "${LIB_DIR}/utility_scripts_cli/commands"
cp "${TMP}/utility-scripts-cli" "${LIB_DIR}/utility-scripts-cli"
chmod +x "${LIB_DIR}/utility-scripts-cli"

cp "${TMP}/pkg___init__.py"     "${LIB_DIR}/utility_scripts_cli/__init__.py"
cp "${TMP}/pkg___main__.py"     "${LIB_DIR}/utility_scripts_cli/__main__.py"
cp "${TMP}/pkg_cli.py"          "${LIB_DIR}/utility_scripts_cli/cli.py"
cp "${TMP}/pkg_env.py"          "${LIB_DIR}/utility_scripts_cli/env.py"
cp "${TMP}/cmd___init__.py"     "${LIB_DIR}/utility_scripts_cli/commands/__init__.py"
cp "${TMP}/cmd_slack_upload_image.py" "${LIB_DIR}/utility_scripts_cli/commands/slack_upload_image.py"

# --- write the shell shim -----------------------------------------------------
cat >"$SHIM" <<EOSH
#!/bin/sh
# Generated by utility-scripts-cli installer. Do not edit.
exec "${VENV_DIR}/bin/python" "${LIB_DIR}/utility-scripts-cli" "\$@"
EOSH
chmod +x "$SHIM"

# --- PATH check ---------------------------------------------------------------
case ":$PATH:" in
  *":${BIN_DIR}:"*) ;;
  *) warn "${BIN_DIR} is not on PATH. Add to your shell rc:  export PATH=\"${BIN_DIR}:\$PATH\"" ;;
esac

log ""
log "Installed: ${SHIM}"
log "Try:       ${SHIM} --help"
log "           ${SHIM} slack upload-image --help"
