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
