#!/usr/bin/env bash
# Install and start the Vertex LLM gateway as a systemd --user unit.
#
# Idempotent: re-running regenerates the unit and restarts the service, but
# keeps an existing shared secret so consumer configs already holding it stay
# valid. Pass --rotate to mint a new one.
#
# One thing this script cannot do for you (it needs root):
#     sudo loginctl enable-linger "$USER"
# Without lingering, systemd tears down your user manager at logout and the
# gateway dies mid-run. It warns if that is still unset.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR="$HOME/.config/p2p"
ENV_FILE="$ENV_DIR/gateway.env"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT_NAME="p2p-llm-gateway.service"

ROTATE=0
[[ "${1:-}" == "--rotate" ]] && ROTATE=1

: "${GCP_PROJECT:?set GCP_PROJECT (source export.sh) before installing}"
GATEWAY_HOST="${P2P_GATEWAY_HOST:-${HEAD_IP:-127.0.0.1}}"
GATEWAY_PORT="${P2P_GATEWAY_PORT:-8900}"

mkdir -p "$ENV_DIR" "$UNIT_DIR" "$HOME/.local/state"

# Preserve the existing secret unless asked to rotate: consumer configs and
# any running job carry it, so silently changing it would 401 them.
if [[ -f "$ENV_FILE" && $ROTATE -eq 0 ]]; then
    TOKEN="$(grep -E '^P2P_GATEWAY_TOKEN=' "$ENV_FILE" | cut -d= -f2-)"
fi
if [[ -z "${TOKEN:-}" ]]; then
    TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
    echo "minted a new gateway secret"
fi

umask 077
cat >"$ENV_FILE" <<EOF
# Written by scripts/install_llm_gateway.sh. Mode 0600: this secret is what
# lets a caller spend the project's Vertex credits.
GCP_PROJECT=$GCP_PROJECT
P2P_GATEWAY_HOST=$GATEWAY_HOST
P2P_GATEWAY_PORT=$GATEWAY_PORT
P2P_GATEWAY_TOKEN=$TOKEN
EOF
chmod 600 "$ENV_FILE"

install -m 644 "$REPO_ROOT/scripts/$UNIT_NAME" "$UNIT_DIR/$UNIT_NAME"

systemctl --user daemon-reload
systemctl --user enable --now "$UNIT_NAME"
systemctl --user restart "$UNIT_NAME"

if [[ "$(loginctl show-user "$USER" --property=Linger --value 2>/dev/null)" != "yes" ]]; then
    echo
    echo "WARNING: lingering is off, so this unit dies when you log out."
    echo "         Run:  sudo loginctl enable-linger $USER"
fi

echo
echo "gateway:  http://$GATEWAY_HOST:$GATEWAY_PORT/v1"
echo "secret:   stored in $ENV_FILE (not echoed here on purpose)"
echo
echo "Export it before submitting a job, so loop/constants.py forwards it"
echo "into the EvolverNode actor's runtime_env:"
echo "    export P2P_GATEWAY_TOKEN=\"\$(grep P2P_GATEWAY_TOKEN $ENV_FILE | cut -d= -f2-)\""
