#!/usr/bin/env bash
# Runtime integration test for the built POMP NET SUPER JINX image.
# Runs locally inside the ephemeral GitHub Actions runner; it does not deploy publicly.
set -Eeuo pipefail

IMAGE="${1:-pompnet-super-jinx:ci}"
NAME="pompnet-jinx-smoke"
VOLUME="pompnet-jinx-smoke-data"
BASE="http://127.0.0.1:18080"
ADMIN="ciadmin"
PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
USER="jinx_ci_smoke"

cleanup() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker volume create "$VOLUME" >/dev/null

start_panel() {
  docker run -d --name "$NAME" \
    -p 127.0.0.1:18080:8080 \
    -v "$VOLUME:/var/lib/marzban" \
    -e ADMIN_USERNAME="$ADMIN" \
    -e ADMIN_PASSWORD="$PASSWORD" \
    -e XRAY_SUBSCRIPTION_URL_PREFIX="$BASE" \
    -e SUB_PROFILE_TITLE="POMP NET MOHAMMAD" \
    "$IMAGE" >/dev/null
}

wait_panel() {
  for _ in $(seq 1 120); do
    STATUS="$(curl --silent --output /dev/null --write-out '%{http_code}' "$BASE/health" 2>/dev/null || true)"
    if [[ "$STATUS" == "200" ]]; then return 0; fi
    if ! docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null | grep -q true; then
      docker logs "$NAME" || true
      return 1
    fi
    sleep 2
  done
  docker logs "$NAME" || true
  echo "Panel did not become healthy within 240 seconds" >&2
  return 1
}

login() {
  curl --fail --silent --show-error --retry 10 --retry-all-errors --retry-delay 2 \
    -X POST "$BASE/api/admin/token" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=$ADMIN" \
    --data-urlencode "password=$PASSWORD" \
    | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
}

start_panel
wait_panel
set -x

# Verify the independent POMP NET dashboard is served at the panel entry route.
DASHBOARD_HTML="$(curl --fail --silent --show-error "$BASE/panel/")"
grep -q -- "POMP NET MOHAMMAD" <<< "$DASHBOARD_HTML"
grep -q -- "SUPER JINX CONTROL" <<< "$DASHBOARD_HTML"
if grep -qi -- "SideRail" <<< "$DASHBOARD_HTML"; then
  echo "Unexpected third-party dashboard branding in the POMP NET UI" >&2
  exit 1
fi
echo "[smoke] independent POMP NET dashboard route: OK"

TOKEN="$(login)"
echo "[smoke] admin login: OK"

USER_JSON="$(curl --fail --silent --show-error --retry 10 --retry-all-errors --retry-delay 2 \
  -X POST "$BASE/api/user" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"username":"jinx_ci_smoke","proxies":{"vless":{}},"inbounds":{"vless":["VLESS WS"]},"expire":0,"data_limit":0,"data_limit_reset_strategy":"no_reset","status":"active"}')"
echo "$USER_JSON" | python -c 'import json,sys; u=json.load(sys.stdin); assert u["username"]=="jinx_ci_smoke"; assert u.get("subscription_url"); print("[smoke] create user + subscription URL: OK")'

SUB_URL="$(printf '%s' "$USER_JSON" | python -c 'import json,sys; print(json.load(sys.stdin)["subscription_url"])')"
SUB_PATH="$(python -c 'import sys,urllib.parse; u=urllib.parse.urlsplit(sys.argv[1]); print(u.path if u.path else sys.argv[1])' "$SUB_URL")"
if [[ "$SUB_PATH" == http* ]]; then
  SUB_BODY="$(curl --location --fail --silent --show-error "$SUB_PATH")"
else
  SUB_BODY="$(curl --location --fail --silent --show-error "$BASE$SUB_PATH")"
fi
test -n "${SUB_BODY:-}" || { echo "Subscription endpoint returned an empty body" >&2; exit 1; }
echo "[smoke] subscription endpoint returned a non-empty body: OK"

# Confirm that Nginx can complete a real WebSocket upgrade to the Xray VLESS inbound.
JX_ID="$(docker exec "$NAME" cat /var/lib/marzban/jinx_path)"
python - "$BASE" "$JX_ID" <<'PY'
import http.client, sys
from urllib.parse import urlsplit
base, secret = sys.argv[1], sys.argv[2]
u = urlsplit(base)
c = http.client.HTTPConnection(u.hostname, u.port, timeout=12)
c.request("GET", f"/cdn/{secret}/v", headers={
    "Host": u.netloc, "Upgrade": "websocket", "Connection": "Upgrade",
    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==", "Sec-WebSocket-Version": "13"
})
r = c.getresponse()
assert r.status == 101, f"WebSocket upgrade returned HTTP {r.status}"
c.close()
print("[smoke] Nginx -> Xray WebSocket handshake: OK")
PY

# Stop and recreate the container against the SAME named volume.
docker rm -f "$NAME" >/dev/null
start_panel
wait_panel
TOKEN="$(login)"
curl --fail --silent --show-error "$BASE/api/user/$USER" \
  -H "Authorization: Bearer $TOKEN" \
  | python -c 'import json,sys; assert json.load(sys.stdin)["username"]=="jinx_ci_smoke"'
JX_ID_AFTER="$(docker exec "$NAME" cat /var/lib/marzban/jinx_path)"
test "$JX_ID" = "$JX_ID_AFTER"
echo "[smoke] database + secret subscription path survive container recreation: OK"
