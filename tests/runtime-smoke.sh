#!/usr/bin/env bash
# Runtime integration test for the built POMP NET SUPER JINX image.
# Runs locally inside the ephemeral GitHub Actions runner; it does not deploy publicly.
set -Eeuo pipefail

IMAGE="${1:-pompnet-super-jinx:ci}"
NAME="pompnet-jinx-smoke"
RESET_NAME="pompnet-jinx-reset-admin"
VOLUME="pompnet-jinx-smoke-data"
BASE="http://127.0.0.1:18080"
ADMIN="ciadmin"
PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
USER="jinx_ci_smoke"

AUTO_NAME="pompnet-jinx-auto-admin"
AUTO_VOLUME="pompnet-jinx-auto-admin-data"
AUTO_BASE="http://127.0.0.1:18081"

cleanup() {
  docker rm -f "$NAME" "$AUTO_NAME" "$RESET_NAME" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME" "$AUTO_VOLUME" >/dev/null 2>&1 || true
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

# Verify the independent POMP NET dashboard is served at the panel entry route.
DASHBOARD_HTML="$(curl --fail --silent --show-error "$BASE/panel/")"
grep -q -- "POMP NET MOHAMMAD" <<< "$DASHBOARD_HTML"
grep -q -- "SUPER JINX" <<< "$DASHBOARD_HTML"
grep -q -- "به پنل پمپ نت محمد خوش آمدید" <<< "$DASHBOARD_HTML"
if grep -qi -- "SideRail" <<< "$DASHBOARD_HTML"; then
  echo "Unexpected third-party dashboard branding in the POMP NET UI" >&2
  exit 1
fi
echo "[smoke] independent POMP NET dashboard route: OK"

# Verify the 24-scene animated layer is served from the built image (not only present in GitHub).
MOTION_CSS="$(curl --fail --silent --show-error "$BASE/pompnet-motion.css")"
MOTION_JS="$(curl --fail --silent --show-error "$BASE/pompnet-motion.js")"
grep -q -- "#pompnet-motion" <<< "$MOTION_CSS"
grep -q -- "requestAnimationFrame" <<< "$MOTION_JS"
SCENE_COUNT="$(printf '%s' "$MOTION_JS" | grep -o '\["#' | wc -l)"
test "$SCENE_COUNT" -ge 24 || { echo "Expected 24 animated scenes, found $SCENE_COUNT" >&2; exit 1; }
echo "[smoke] animated dashboard assets + 24 scenes: OK"

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
# Browser subscription page must render the custom Persian POMP NET template, not only raw config text.
SUB_PAGE="$(curl --location --fail --silent --show-error -A 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/124.0 Mobile Safari/537.36' -H 'Accept: text/html,application/xhtml+xml' "$BASE$SUB_PATH")"
grep -q -- "POMP NET MOHAMMAD" <<< "$SUB_PAGE"
grep -q -- "#8B35FF" <<< "$SUB_PAGE"
if grep -qi -- "SideRail" <<< "$SUB_PAGE"; then
  echo "Unexpected third-party subscription branding" >&2
  exit 1
fi
echo "[smoke] custom subscription page + POMP NET theme: OK"
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

# Fresh-install path: no ADMIN_PASSWORD is supplied. The app must generate
# a one-time secret, expose it only in this container's deploy log, and keep
# the same credential after container recreation on the same persistent volume.
docker volume create "$AUTO_VOLUME" >/dev/null
docker run -d --name "$AUTO_NAME" \
  -p 127.0.0.1:18081:8080 \
  -v "$AUTO_VOLUME:/var/lib/marzban" \
  -e XRAY_SUBSCRIPTION_URL_PREFIX="$AUTO_BASE" \
  "$IMAGE" >/dev/null
AUTO_HEALTHY=0
for _ in $(seq 1 120); do
  AUTO_STATUS="$(curl --silent --output /dev/null --write-out '%{http_code}' "$AUTO_BASE/health" 2>/dev/null || true)"
  if [[ "$AUTO_STATUS" == "200" ]]; then AUTO_HEALTHY=1; break; fi
  if ! docker inspect -f '{{.State.Running}}' "$AUTO_NAME" 2>/dev/null | grep -q true; then
    echo "Auto-admin fresh install container exited before becoming healthy" >&2
    exit 1
  fi
  sleep 2
done
test "$AUTO_HEALTHY" = "1" || { echo "Auto-admin fresh install did not become healthy" >&2; exit 1; }

AUTO_CREDENTIAL_LINE="$(docker logs "$AUTO_NAME" 2>&1 | grep -m1 'ONE-TIME LOGIN' || true)"
AUTO_PASSWORD="$(printf '%s' "$AUTO_CREDENTIAL_LINE" | sed -n 's/.*password: //p' | tr -d '\r')"
test -n "$AUTO_PASSWORD" || { echo "Generated one-time admin password was not emitted to deploy logs" >&2; exit 1; }
test "${#AUTO_PASSWORD}" -ge 32 || { echo "Generated admin password is unexpectedly short" >&2; exit 1; }
AUTO_TOKEN="$(curl --fail --silent --show-error -X POST "$AUTO_BASE/api/admin/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=admin" \
  --data-urlencode "password=$AUTO_PASSWORD" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
test -n "$AUTO_TOKEN"
echo "[smoke] automatic first-deploy admin generation + login: OK"

docker rm -f "$AUTO_NAME" >/dev/null
docker run -d --name "$AUTO_NAME" \
  -p 127.0.0.1:18081:8080 \
  -v "$AUTO_VOLUME:/var/lib/marzban" \
  -e XRAY_SUBSCRIPTION_URL_PREFIX="$AUTO_BASE" \
  "$IMAGE" >/dev/null
AUTO_HEALTHY=0
for _ in $(seq 1 120); do
  AUTO_STATUS="$(curl --silent --output /dev/null --write-out '%{http_code}' "$AUTO_BASE/health" 2>/dev/null || true)"
  if [[ "$AUTO_STATUS" == "200" ]]; then AUTO_HEALTHY=1; break; fi
  if ! docker inspect -f '{{.State.Running}}' "$AUTO_NAME" 2>/dev/null | grep -q true; then
    echo "Auto-admin container exited after recreation" >&2
    exit 1
  fi
  sleep 2
done
test "$AUTO_HEALTHY" = "1" || { echo "Auto-admin container did not recover after recreation" >&2; exit 1; }
if docker logs "$AUTO_NAME" 2>&1 | grep -q 'ONE-TIME LOGIN'; then
  echo "Auto-admin password was unexpectedly regenerated on restart" >&2
  exit 1
fi
curl --fail --silent --show-error -X POST "$AUTO_BASE/api/admin/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=admin" \
  --data-urlencode "password=$AUTO_PASSWORD" \
  | python -c 'import json,sys; assert json.load(sys.stdin).get("access_token"); print("[smoke] generated admin credential persists across container recreation: OK")'

# Existing admin recovery path: explicit reset flag rotates the existing owner
# to a fresh strong password without requiring the old password or a weak default.
# Stop the previous container first; never mount the same SQLite volume twice.
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$RESET_NAME" \
  -p 127.0.0.1:18082:8080 \
  -v "$VOLUME:/var/lib/marzban" \
  -e ADMIN_USERNAME="$ADMIN" \
  -e RESET_ADMIN_PASSWORD=1 \
  -e XRAY_SUBSCRIPTION_URL_PREFIX="http://127.0.0.1:18082" \
  "$IMAGE" >/dev/null
for _ in $(seq 1 120); do
  RESET_STATUS="$(curl --silent --output /dev/null --write-out '%{http_code}' "http://127.0.0.1:18082/health" 2>/dev/null || true)"
  if [[ "$RESET_STATUS" == "200" ]]; then break; fi
  if ! docker inspect -f '{{.State.Running}}' "$RESET_NAME" 2>/dev/null | grep -q true; then
    docker logs "$RESET_NAME" || true
    echo "Admin recovery container exited" >&2
    exit 1
  fi
  sleep 2
done
RESET_LINE="$(docker logs "$RESET_NAME" 2>&1 | grep -m1 'ONE-TIME LOGIN' || true)"
RESET_PASSWORD="$(printf '%s' "$RESET_LINE" | sed -n 's/.*password: //p' | tr -d '\r')"
test -n "$RESET_PASSWORD" || { echo "Admin recovery did not emit a one-time password" >&2; exit 1; }
curl --fail --silent --show-error -X POST "http://127.0.0.1:18082/api/admin/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=$ADMIN" \
  --data-urlencode "password=$RESET_PASSWORD" \
  | python -c 'import json,sys; assert json.load(sys.stdin).get("access_token"); print("[smoke] explicit existing-admin password recovery: OK")'
