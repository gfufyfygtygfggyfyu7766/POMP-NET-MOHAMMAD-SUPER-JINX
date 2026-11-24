#!/usr/bin/env bash
# Runtime integration test for the built POMP NET SUPER JINX image.
# Runs locally inside the ephemeral GitHub Actions runner; it does not deploy publicly.
set -Eeuo pipefail

IMAGE="${1:-pompnet-super-jinx:ci}"
NAME="pompnet-jinx-smoke"
RESET_NAME="pompnet-jinx-reset-admin"
VOLUME="pompnet-jinx-smoke-data"
BASE="http://127.0.0.1:18080"
ADMIN="ADMIN_tanel9990"
PASSWORD="$(sed -n 's/^export ADMIN_PASSWORD="\(.*\)"$/\1/p' start.sh | head -n 1)"
if [[ -z "$PASSWORD" ]]; then echo "Could not read configured owner password from start.sh" >&2; exit 1; fi
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
    -e ALLOW_INSECURE_ADMIN_PASSWORD=1 \
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

# Railway terminates public TLS at its HTTPS edge (443); the container listens on HTTP 8080.
# Port 2096 is not assumed to exist on Railway. VPS/Compose and Caddy deployments keep
# their own separately configured 2096 listeners and are not used to build Railway links.
grep -q 'XRAY_SUBSCRIPTION_URL_PREFIX="https://\$PUBLIC_DOMAIN"' start.sh
if grep -q 'XRAY_SUBSCRIPTION_URL_PREFIX="https://\$PUBLIC_DOMAIN:2096"' start.sh; then
  echo "Railway subscription URL must use the TLS edge hostname without an unexposed :2096 port" >&2
  exit 1
fi
grep -q 'listen 8080' nginx.conf
echo "[smoke] Railway HTTPS edge -> internal port 8080 subscription routing: OK"
grep -q -- 'POMP NET legibility and mobile performance overrides' jinx.css
grep -q -- 'POMP NET readable subscription view' sub.html
grep -q -- 'prefers-reduced-motion:reduce' jinx.css
echo "[smoke] readable high-contrast low-motion styles: OK"

start_panel
wait_panel

# Verify the real PasarGuard dashboard is served and receives the POMP NET skin.
DASHBOARD_HTML="$(curl --fail --silent --show-error "$BASE/dashboard/")"
grep -q -- 'href="/jinx.css"' <<< "$DASHBOARD_HTML"
grep -q -- 'src="/jinx.js"' <<< "$DASHBOARD_HTML"
JINX_SCRIPT="$(curl --fail --silent --show-error "$BASE/jinx.js")"
grep -q -- "POMP NET MOHAMMAD" <<< "$JINX_SCRIPT"
grep -q -- "به پنل پمپ نت محمد خوش آمدید" <<< "$JINX_SCRIPT"
JINX_STYLE="$(curl --fail --silent --show-error "$BASE/jinx.css")"
grep -q -- "Vazirmatn" <<< "$JINX_STYLE"
echo "[smoke] native PasarGuard dashboard + POMP NET skin: OK"
# Telegram bot settings are served, but configuration stays owner-only.
BOT_PAGE="$(curl --fail --silent --show-error "$BASE/bot/")"
grep -q "ربات مدیریت POMP NET MOHAMMAD" <<< "$BOT_PAGE"
BOT_UNAUTH="$(curl --silent --output /dev/null --write-out '%{http_code}' "$BASE/jinx-api/bot-config")"
test "$BOT_UNAUTH" = "401"
OWNER_TOKEN="$(login)"
curl --fail --silent --show-error "$BASE/jinx-api/bot-config" -H "Authorization: Bearer $OWNER_TOKEN" \
  | python -c 'import json,sys; d=json.load(sys.stdin); assert d["ok"] and "token_set" in d; print("[smoke] owner-only Telegram bot settings endpoint: OK")'

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

# Verify the real reseller sub-panel: isolated admin account, enforced limits, and its own subscription.
RESELLER="jinx_ci_reseller"
RESELLER_PASS="Reseller-Super-123!"
curl --fail --silent --show-error -X POST "$BASE/jinx-api/resellers" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  --data "{\"username\":\"$RESELLER\",\"password\":\"$RESELLER_PASS\",\"max_users\":10,\"quota_gb\":2,\"expire\":$(($(date +%s)+2592000)),\"title\":\"POMP NET CI reseller\",\"domain\":\"\"}" \
  | python -c 'import json,sys; assert json.load(sys.stdin)["ok"] is True'
RESELLER_TOKEN="$(curl --fail --silent --show-error -X POST "$BASE/api/admin/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=$RESELLER" --data-urlencode "password=$RESELLER_PASS" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
curl --fail --silent --show-error "$BASE/api/admin" -H "Authorization: Bearer $RESELLER_TOKEN" \
  | python -c 'import json,sys; a=json.load(sys.stdin); assert a["username"]=="jinx_ci_reseller" and not a["is_sudo"]'
echo "[smoke] reseller account creation + independent login: OK"

# A reseller must not be able to read the owner's user.
OWNER_USER_STATUS="$(curl --silent --output /dev/null --write-out '%{http_code}' \
  "$BASE/api/user/$USER" -H "Authorization: Bearer $RESELLER_TOKEN")"
[[ "$OWNER_USER_STATUS" == "403" || "$OWNER_USER_STATUS" == "404" ]] || { echo "Reseller accessed another admin's user (HTTP $OWNER_USER_STATUS)" >&2; exit 1; }

RESELLER_USER_JSON="$(curl --fail --silent --show-error -X POST "$BASE/api/user" \
  -H "Authorization: Bearer $RESELLER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"username":"jinx_ci_reseller_user","proxies":{"vless":{}},"inbounds":{"vless":["VLESS WS"]},"expire":0,"data_limit":536870912,"data_limit_reset_strategy":"no_reset","status":"active"}')"
echo "$RESELLER_USER_JSON" | python -c 'import json,sys; u=json.load(sys.stdin); assert u["username"]=="jinx_ci_reseller_user" and u.get("subscription_url"); print("[smoke] reseller creates own Xray user + real subscription URL: OK")'
RESELLER_SUB="$(printf '%s' "$RESELLER_USER_JSON" | python -c 'import json,sys; print(json.load(sys.stdin)["subscription_url"])')"
RESELLER_PATH="$(python -c 'import sys,urllib.parse; print(urllib.parse.urlsplit(sys.argv[1]).path)' "$RESELLER_SUB")"
RESELLER_BODY="$(curl --location --fail --silent --show-error "$BASE$RESELLER_PATH")"
test -n "$RESELLER_BODY" || { echo "Reseller subscription endpoint returned an empty body" >&2; exit 1; }
echo "[smoke] reseller subscription endpoint: OK"

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

# Fresh-install path: the image entrypoint configures the fixed POMP NET owner.
# Read the expected password from start.sh rather than duplicating a credential in this test.
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
    echo "Fixed-admin fresh install container exited before becoming healthy" >&2
    docker logs "$AUTO_NAME" || true
    exit 1
  fi
  sleep 2
done
test "$AUTO_HEALTHY" = "1" || { docker logs "$AUTO_NAME" || true; echo "Fixed-admin fresh install did not become healthy" >&2; exit 1; }

AUTO_TOKEN="$(curl --fail --silent --show-error -X POST "$AUTO_BASE/api/admin/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=$ADMIN" \
  --data-urlencode "password=$PASSWORD" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
test -n "$AUTO_TOKEN"
echo "[smoke] configured POMP NET owner login on fresh install: OK"

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
    echo "Fixed-admin container exited after recreation" >&2
    docker logs "$AUTO_NAME" || true
    exit 1
  fi
  sleep 2
done
test "$AUTO_HEALTHY" = "1" || { docker logs "$AUTO_NAME" || true; echo "Fixed-admin container did not recover after recreation" >&2; exit 1; }
curl --fail --silent --show-error -X POST "$AUTO_BASE/api/admin/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=$ADMIN" \
  --data-urlencode "password=$PASSWORD" \
  | python -c 'import json,sys; assert json.load(sys.stdin).get("access_token"); print("[smoke] configured owner login survives container recreation: OK")'

# Existing admin recovery path: an explicitly requested reset changes the existing owner password.
# Stop the previous container first; never mount the same SQLite volume twice.
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$RESET_NAME" \
  -p 127.0.0.1:18082:8080 \
  -v "$VOLUME:/var/lib/marzban" \
  -e ADMIN_USERNAME="$ADMIN" \
  -e ADMIN_PASSWORD="$PASSWORD" \
  -e ALLOW_INSECURE_ADMIN_PASSWORD=1 \
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
curl --fail --silent --show-error -X POST "http://127.0.0.1:18082/api/admin/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=$ADMIN" \
  --data-urlencode "password=$PASSWORD" \
  | python -c 'import json,sys; assert json.load(sys.stdin).get("access_token"); print("[smoke] one-time existing-admin recovery: OK")'
