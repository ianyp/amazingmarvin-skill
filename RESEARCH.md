# Existing options and API findings

Checked 2026-11-13. Web search plus primary documentation reads; no dependencies installed or third-party code audited.

| Option | Evidence | Decision |
| --- | --- | --- |
| [Official marvin-cli](https://github.com/amazingmarvin/marvin-cli) | README supports desktop/public API, warns features may not work; update/delete listed unimplemented; Deno build | Evaluate first; do not assume production readiness or safe secret transport |
| [Community MCP](https://github.com/LucaDeLeo/amazing-marvin-mcp) | README describes ten tools and hosted Smithery HTTP/SSE integration | Evaluate local reuse only; hosted token submission not authorized; claims require verification |
| [Official public API](https://help.amazingmarvin.com/amazing-marvin/api-endpoints) | Documented limited-token operations fit v1 | Small direct adapter is fallback if reuse gate fails |

No dedicated OpenClaw skill appeared in the search results; this is not an exhaustive catalog audit.

Primary references:

- https://help.amazingmarvin.com/amazing-marvin/api-getting-started
- https://help.amazingmarvin.com/amazing-marvin/api-endpoints
- https://github.com/amazingmarvin/MarvinAPI/blob/master/marvin-api.yaml
- https://raw.githubusercontent.com/amazingmarvin/marvin-cli/master/README.md
- https://raw.githubusercontent.com/LucaDeLeo/amazing-marvin-mcp/main/README.md

Official docs confirm HTTPS base https://serv.amazingmarvin.com/api, X-API-Token for the proposed endpoints, burst spacing of 3 seconds, 1440/day average shared across API and database clients, and roughly one minute rejection after throttling. This is not a midnight-reset quota.

Verified v1 mappings: GET todayItems?date=YYYY-MM-DD; GET dueItems?by=YYYY-MM-DD; GET categories; GET labels; GET children?parentId=ID; POST addTask; POST markDone; POST test. Completion is experimental. Today/due lists do not reproduce all client visibility rules. addTask accepts timeEstimate in milliseconds and supports disabling shortcut parsing. +date means scheduled day, not deadline: community README examples must not override official semantics.

Remaining implementation research: full response schema samples and ID availability, timezone offset edge cases, current OpenAPI consistency, dependency licenses/maintenance, existing installed catalog coverage and actual OpenClaw credential injection syntax. Resolve these before coding their respective contracts.
