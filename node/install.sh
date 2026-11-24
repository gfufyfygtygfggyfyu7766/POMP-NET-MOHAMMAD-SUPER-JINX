#!/usr/bin/env bash
set -Eeuo pipefail

echo "POMP NET - Marzban Node installer"
if [[ $EUID -ne 0 ]]; then echo "Run as root: sudo bash install.sh"; exit 1; fi
command -v docker >/dev/null 2>&1 || { echo "Docker is required. Install Docker first: https://docs.docker.com/engine/install/"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose plugin is required."; exit 1; }

read -r -p "Paste the node client certificate copied from POMP NET > Node Settings: " CERT
[[ "$CERT" == *"BEGIN CERTIFICATE"* && "$CERT" == *"END CERTIFICATE"* ]] || { echo "Invalid PEM certificate. Nothing installed."; exit 1; }

install -d -m 700 /var/lib/marzban-node
printf '%s\n' "$CERT" > /var/lib/marzban-node/ssl_client_cert.pem
chmod 600 /var/lib/marzban-node/ssl_client_cert.pem
cp "$(dirname "$0")/docker-compose.yml" /opt/pompnet-node-compose.yml
cat >/opt/pompnet-node.env <<'ENV'
SERVICE_PORT=62050
XRAY_API_PORT=62051
ENV
cd /opt
docker compose --env-file /opt/pompnet-node.env -f /opt/pompnet-node-compose.yml pull
docker compose --env-file /opt/pompnet-node.env -f /opt/pompnet-node-compose.yml up -d
echo
echo "Node container started. Check with:"
echo "docker compose --env-file /opt/pompnet-node.env -f /opt/pompnet-node-compose.yml ps"
echo "IMPORTANT: Add this server as a Node in POMP NET panel, using this server's public IP and port 62050."
echo "Open TCP 62050 from the panel to this server. Open your configured inbound ports to VPN clients."
