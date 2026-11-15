# Protected proxy adaptation — 15 November 2026

Implemented OpenClaw protected-sentinel routing through its authenticated loopback HTTPS proxy. The helper loads the injected CA bundle, keeps TLS verification and redirect blocking, ignores NO_PROXY for protected requests, and refuses missing/invalid proxy configuration without direct fallback. Ordinary token behaviour is unchanged.

Verification: 54 offline tests pass, including five new red-to-green proxy checks. Offline package rebuilt.

Gateway configuration helper enabled secrets.egressProxy.enabled and scheduled the required restart. A subsequent gateway_exec authentication attempt returned missing_credentials before making an API request: this run still has no MARVIN_API_TOKEN injection. Live proxy/authentication is NOT verified. Resume from a fresh turn after restart and run the non-mutating check-auth command via gateway_exec. Do not re-enter or print the stored token.

No Marvin tasks were read, created, completed or modified. Full runtime installation and broader feature work remain outside this adaptation.
