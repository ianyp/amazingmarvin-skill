# Adapter decision — 2026-11-13

Use a small original standard-library adapter, not a fork or hosted MCP connection.

Reviewed official marvin-cli src/apiCall.ts and src/localStorage.ts on master: MIT; GitHub reported pushed_at 2023-04-24. It defaults to trying desktop then public, including POST requests, exposes configurable host/protocol, propagates response/error text and stores configuration as plaintext JSON. Public-only configuration helps but does not provide the cross-process rate budget or JSON error/uncertainty contract. No code copied.

Reviewed LucaDeLeo/amazing-marvin-mcp src/amazing_marvin_mcp/server.py on main: GitHub reported pushed_at 2025-11-14 and no detected repository license (despite README's MIT assertion). Transport creates httpx client per call with no shared limiter, depends on Smithery context, and generic errors include exception text. Completion omits timezone offset; timer payload shown uses itemId while official documentation specifies taskId. Hosted account setup is unnecessary for this local skill. No code copied or dependencies adopted.

Sources: https://github.com/amazingmarvin/marvin-cli ; https://github.com/LucaDeLeo/amazing-marvin-mcp . This was targeted suitability review, not a comprehensive security audit. Source branches can change; evidence and review date recorded rather than implying pinned reuse.

Plan adjustment: standard-library unittest instead of pytest; fail-fast read errors instead of automatic retry for this initial release. Integer and HTTP-date Retry-After are handled. Do not call v1 complete until remaining gates in DEVELOPMENT.md pass.
