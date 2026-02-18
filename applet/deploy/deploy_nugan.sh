#!/usr/bin/env bash
set -euo pipefail

# Deploy script for nuGAN backend
# Usage: sudo ./deploy_nugan.sh

INSTALL_DIR="/data/projects_website/nugan"
USER_NAME="prasingh"
SERVICE_NAME="nugan"
SERVICE_SRC="$(cd "$(dirname "$0")" && pwd)/nuGAN-backend.service"
SERVICE_DST="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Installing nuGAN backend to ${INSTALL_DIR} as ${USER_NAME}"

if [ "$EUID" -ne 0 ]; then
  echo "This script requires sudo/root. Re-run with sudo." >&2
  exit 2
fi

if [ ! -d "${INSTALL_DIR}" ]; then
  echo "Install directory ${INSTALL_DIR} does not exist. Create and set ownership to ${USER_NAME}."
  mkdir -p "${INSTALL_DIR}"
  chown ${USER_NAME}:${USER_NAME} "${INSTALL_DIR}"
fi

cd "${INSTALL_DIR}/applet/backend"

echo "Creating virtualenv (if missing) and installing requirements as ${USER_NAME}..."
if [ ! -d "venv" ]; then
  sudo -u ${USER_NAME} python3 -m venv venv
fi
sudo -u ${USER_NAME} ./venv/bin/pip install --upgrade pip
sudo -u ${USER_NAME} ./venv/bin/pip install -r requirements.txt

echo "Creating default /etc/nugan.env (overwrite if not present)..."
if [ ! -f /etc/nugan.env ]; then
  cat > /etc/nugan.env <<EOF
# nuGAN production env
FLASK_ENV=production
PORT=2224
ALLOWED_ORIGINS=*
NUGAN_SEED=42
EOF
  chmod 640 /etc/nugan.env
  chown root:root /etc/nugan.env
  echo "/etc/nugan.env created (edit to secure allowed origins)."
else
  echo "/etc/nugan.env already exists; leaving it in place."
fi

echo "Copying service file to ${SERVICE_DST} and enabling systemd service..."
cp "${SERVICE_SRC}" "${SERVICE_DST}"
systemctl daemon-reload
systemctl enable --now ${SERVICE_NAME}.service

echo "Service ${SERVICE_NAME} enabled and started. Showing status..."
systemctl status ${SERVICE_NAME}.service --no-pager

echo "Tail logs (press Ctrl+C to exit):"
journalctl -u ${SERVICE_NAME}.service -f
