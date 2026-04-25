#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────
# agent-athena bootstrap installer
# ─────────────────────────────────────────────
# One-shot install for a fresh node:
#   1. Ensure Node.js >= 20 is available (install via Homebrew on macOS or
#      NodeSource/apt on Ubuntu/Debian if missing).
#   2. Run claude-setup/setup.sh to register the athena Claude Code plugin.
#
# Usage:
#   ./install.sh             # install
#   ./install.sh --uninstall # forwards to claude-setup/setup.sh --uninstall
#
# Other systems: install Node.js >= 20 manually, then run
# `bash claude-setup/setup.sh` directly.
# ─────────────────────────────────────────────

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETUP_SCRIPT="$ROOT_DIR/claude-setup/setup.sh"

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[bootstrap]${NC} $1"; }
warn()  { echo -e "${YELLOW}[bootstrap]${NC} $1"; }
error() { echo -e "${RED}[bootstrap]${NC} $1" >&2; }

# ── Forward uninstall directly ──
if [[ "${1:-}" == "--uninstall" ]]; then
  if [[ ! -f "$SETUP_SCRIPT" ]]; then
    error "Missing $SETUP_SCRIPT"
    exit 1
  fi
  exec bash "$SETUP_SCRIPT" --uninstall
fi

# ── Detect node >= 20 ──
node_ok() {
  command -v node &>/dev/null || return 1
  local major
  major=$(node -v | sed 's/v//' | cut -d. -f1)
  [[ "$major" -ge 20 ]]
}

# ── macOS: Homebrew ──
install_node_macos() {
  if ! command -v brew &>/dev/null; then
    error "Homebrew not found. Install it first:"
    error '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
  fi
  info "Installing Node.js via Homebrew..."
  brew install node
}

# ── Ubuntu/Debian: NodeSource via apt (requires sudo) ──
install_node_linux() {
  if [[ ! -f /etc/os-release ]]; then
    error "Cannot detect Linux distribution. Install Node.js >= 20 manually."
    exit 1
  fi

  # shellcheck disable=SC1091
  . /etc/os-release

  case "${ID:-}|${ID_LIKE:-}" in
    *ubuntu*|*debian*)
      ;;
    *)
      error "Unsupported Linux distribution: ${ID:-unknown} (${ID_LIKE:-})"
      error "Supported: Ubuntu/Debian. Install Node.js >= 20 manually for others."
      exit 1
      ;;
  esac

  for dep in curl sudo; do
    if ! command -v "$dep" &>/dev/null; then
      error "$dep is required but not installed."
      exit 1
    fi
  done

  info "Installing Node.js LTS via NodeSource (requires sudo)..."
  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  sudo apt-get install -y nodejs
}

# ── Ensure Node.js ──
OS="$(uname -s)"

if node_ok; then
  info "Node.js $(node -v) already available — skipping install."
else
  if command -v node &>/dev/null; then
    warn "Found $(node -v) but version < 20. Will install a newer release."
  else
    info "Node.js not found. Installing for $OS..."
  fi

  case "$OS" in
    Darwin)  install_node_macos ;;
    Linux)   install_node_linux ;;
    *)
      error "Unsupported OS: $OS"
      error "Install Node.js >= 20 manually, then run: bash claude-setup/setup.sh"
      exit 1
      ;;
  esac

  if ! node_ok; then
    error "Node.js install completed but version check still fails. Verify manually."
    exit 1
  fi
  info "Node.js $(node -v) ready."
fi

# ── Run athena plugin setup ──
if [[ ! -f "$SETUP_SCRIPT" ]]; then
  error "Missing $SETUP_SCRIPT — repo may be incomplete."
  exit 1
fi

info "Running athena plugin setup..."
echo ""
bash "$SETUP_SCRIPT"
echo ""
info "Bootstrap complete."
