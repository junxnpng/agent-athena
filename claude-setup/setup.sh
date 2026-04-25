#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────
# Athena - Claude Code Multi-Agent Setup
# ─────────────────────────────────────────────
# Registers this directory as a local marketplace and enables the athena plugin.
#
# Usage:
#   ./setup.sh             # install (register + enable)
#   ./setup.sh --uninstall # remove from settings.json
#
# Edit files in this directory directly — Claude Code reads from here on each
# new session, so no copy step is required.
# ─────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

MARKETPLACE_NAME="athena-local"
PLUGIN_QUALIFIED="athena@${MARKETPLACE_NAME}"

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[athena]${NC} $1"; }
warn()  { echo -e "${YELLOW}[athena]${NC} $1"; }
error() { echo -e "${RED}[athena]${NC} $1" >&2; }

# ── Prerequisites ──
if ! command -v node &>/dev/null; then
  error "Node.js is required but not found. Install it first."
  exit 1
fi

NODE_MAJOR=$(node -v | sed 's/v//' | cut -d. -f1)
if [[ "$NODE_MAJOR" -lt 20 ]]; then
  error "Node.js >= 20 required (found v$NODE_MAJOR)"
  exit 1
fi

# ── Ensure settings.json exists ──
mkdir -p "$CLAUDE_DIR"
[[ -f "$SETTINGS_FILE" ]] || echo '{}' > "$SETTINGS_FILE"

# ── Uninstall ──
if [[ "${1:-}" == "--uninstall" ]]; then
  info "Uninstalling athena plugin..."
  node -e "
    const fs = require('fs');
    const path = '$SETTINGS_FILE';
    const s = JSON.parse(fs.readFileSync(path, 'utf-8'));
    let changed = false;
    if (s.extraKnownMarketplaces && s.extraKnownMarketplaces['$MARKETPLACE_NAME']) {
      delete s.extraKnownMarketplaces['$MARKETPLACE_NAME'];
      changed = true;
    }
    if (s.enabledPlugins && Object.prototype.hasOwnProperty.call(s.enabledPlugins, '$PLUGIN_QUALIFIED')) {
      delete s.enabledPlugins['$PLUGIN_QUALIFIED'];
      changed = true;
    }
    if (changed) fs.writeFileSync(path, JSON.stringify(s, null, 2) + '\n');
    console.log(changed ? 'removed' : 'noop');
  " >/tmp/athena-uninstall-result || { error "Failed to update settings.json"; exit 1; }

  if [[ "$(cat /tmp/athena-uninstall-result)" == "removed" ]]; then
    info "Removed marketplace + plugin entries from settings.json"
  else
    warn "Athena entries not found in settings.json (already uninstalled)"
  fi
  rm -f /tmp/athena-uninstall-result
  info "Uninstall complete. Restart Claude Code."
  exit 0
fi

# ── Sanity check plugin structure ──
for required in .claude-plugin/plugin.json .claude-plugin/marketplace.json hooks/hooks.json scripts/run.cjs; do
  if [[ ! -f "$SCRIPT_DIR/$required" ]]; then
    error "Missing required file: $required"
    exit 1
  fi
done

# ── Verify agent-skill consistency (catches dangling athena: refs) ──
if ! node "$SCRIPT_DIR/scripts/check-consistency.mjs" "$SCRIPT_DIR"; then
  warn "Continuing registration anyway — fix the references for healthy plugin state."
fi

# ── Register marketplace + enable plugin in settings.json ──
node -e "
  const fs = require('fs');
  const path = '$SETTINGS_FILE';
  const dir = '$SCRIPT_DIR';
  const marketName = '$MARKETPLACE_NAME';
  const pluginKey = '$PLUGIN_QUALIFIED';

  const s = JSON.parse(fs.readFileSync(path, 'utf-8'));
  if (!s.extraKnownMarketplaces || typeof s.extraKnownMarketplaces !== 'object') {
    s.extraKnownMarketplaces = {};
  }
  if (!s.enabledPlugins || typeof s.enabledPlugins !== 'object') {
    s.enabledPlugins = {};
  }

  s.extraKnownMarketplaces[marketName] = {
    source: { source: 'directory', path: dir }
  };
  s.enabledPlugins[pluginKey] = true;

  fs.writeFileSync(path, JSON.stringify(s, null, 2) + '\n');
" || { error "Failed to update settings.json"; exit 1; }

info "Registered marketplace '$MARKETPLACE_NAME' -> $SCRIPT_DIR"
info "Enabled plugin '$PLUGIN_QUALIFIED'"

# ── Verify ──
echo ""
info "Setup complete."
echo ""
echo "  Source:    $SCRIPT_DIR"
echo "  Settings:  $SETTINGS_FILE"
echo "  Plugin:    $PLUGIN_QUALIFIED"
echo ""
info "Restart Claude Code (or open a new session) to activate athena."
echo ""
echo "  Verify with: /plugin     (should list athena under athena-local)"
