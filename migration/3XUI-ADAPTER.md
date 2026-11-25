# POMP NET 3X-UI adapter module

- Pinned upstream contract: **MHSanaei/3x-ui v3.11.0**.
- Client endpoints are the v3 first-class-client routes under
  `/panel/api/clients`: list, get, add, update, delete, traffic and subscription links.
- Configure `XUI_BASE_URL` and either `XUI_API_TOKEN` or
  `XUI_USERNAME` + `XUI_PASSWORD` as server-side secrets.
- The adapter never sends credentials to browser JavaScript.

## Deliberate staging boundary

This module is an isolated transport/client layer only. It is **not** yet wired
into `start.sh`, `nginx.conf`, `jinx_api.py`, login, dashboard or
`/sub/{token}`. The production Marzban image/database remain untouched.

Before integration, add the persistent legacy-token/client mapping, normalize
the exact current dashboard response shapes, and migrate users/inbounds from a
verified export. The 3X-UI update endpoint replaces the full client row, so
partial update payloads are unsafe. Do not point this at the production volume
or deploy it as a cutover.


## Dashboard bridge deployment variables (staging only)

Required Railway service variables:
- `POMPNET_3XUI_BRIDGE=1`
- `XUI_BASE_URL`: the HTTPS origin/base URL of the 3X-UI panel (including its web base path if configured).
- `XUI_USERNAME` and `XUI_PASSWORD`: dashboard owner credentials used to validate the existing login form.
- `POMPNET_ADAPTER_SECRET`: long random secret used to sign POMP NET adapter access tokens.

Optional:
- `XUI_API_TOKEN`: use a supported 3X-UI bearer API token for API requests.
- `XUI_VLESS_INBOUND_TAG`, `XUI_VMESS_INBOUND_TAG`, `XUI_TROJAN_INBOUND_TAG`: exact existing inbound tags; defaults are the legacy JinX labels.

The staging startup now fails closed if these values are absent. It must not be deployed to the production service or its existing volume.

## Current bridge coverage and known gaps

Implemented dashboard endpoints: login token, list users, create user, delete user, and system counters. The dashboard HTML is not edited.

Not yet migrated: legacy `/sub/{token}` URL resolution and subscription rendering, per-user reset/revoke/extend actions, QR/deep links, reseller permissions and legacy Marzban-to-3X-UI data import. The existing Nginx `/sub/` route still targets the old Marzban app; therefore the overall migration is not complete and client subscriptions must not be considered cut over.
