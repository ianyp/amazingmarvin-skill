# Setup

Requires Linux, Python 3.11+ and system timezone data. Helpers use only the standard library. No package install, external service, background process or scheduler is needed.

Provide the limited-access or full-access API token as MARVIN_API_TOKEN in the helper process environment using the host's approved secret-injection mechanism. Do not place the token in shell command arguments, skill source or Git. Exact OpenClaw secret configuration is version-dependent and is not automated by this skill. Choose the matching access mode before the command. Never infer token permissions from its text.

| Token configuration | CLI option | Header |
| --- | --- | --- |
| Minimal (Marvin limited-access token) | `--minimal-access`, or omit both flags | `X-API-Token` |
| Full-access token | `--full-access` | `X-Full-Access-Token` |

The flags are mutually exclusive. Both modes use the same protected `MARVIN_API_TOKEN` environment variable. There is no automatic upgrade or fallback. Minimal access supports core workflows such as today, task capture and task completion; it is not read-only. Full-only operations fail locally with `missing_capability` in minimal mode. See the repository's FEATURE_COVERAGE.md for per-operation requirements.

Run `python3 scripts/marvin.py --help` from this skill directory (or use its absolute path from another directory). A non-mutating credential check is `python3 scripts/marvin.py --minimal-access check-auth` (this still makes a network request). A normal read example is `python3 scripts/marvin.py --minimal-access today`. For a full token, replace `--minimal-access` with `--full-access` in those examples. It contacts the public Marvin API, so don't use it as an offline setup check.

Rate-accounting timestamps live at `$XDG_STATE_HOME/openclaw-amazingmarvin/rate.json`, default `~/.local/state/openclaw-amazingmarvin/rate.json`. It contains no token or task data. Shared processes use a nonblocking file lock. Requests wait up to five seconds for spacing; cooldowns/budget exhaustion return errors rather than sleeping indefinitely. Do not delete the file to bypass throttling. Corrupt state fails closed.

Local rolling 24-hour ceiling: 1440 requests, spacing: three seconds. This cannot see other apps' shared Marvin API usage. HTTP 429 sets a shared cooldown of at least 60 seconds; integer and HTTP-date Retry-After values are respected. No automatic HTTP retries are currently implemented. Reissue reads deliberately after cooldown; never blindly repeat uncertain writes.

Install only after offline validation and authorized live verification. Copy the entire amazingmarvin directory to an approved OpenClaw skill directory; retain this repository as the source. The maintained source is this repository; the installed workspace copy must match the released source. See V1_REPORT.md in the repository for deployment evidence.

## OpenClaw protected Secrets store

Store `MARVIN_API_TOKEN` as a protected secret with allowed host
`serv.amazingmarvin.com`. Enable `secrets.egressProxy.enabled` on the Gateway
and apply any required Gateway restart. Run the helper through OpenClaw
`gateway_exec`, not Codex-native shell, sandbox or remote node execution.
Newly saved secrets may require a new agent turn to refresh the run snapshot.

The helper detects OpenClaw's opaque sentinel and requires the injected
`HTTPS_PROXY` (authenticated loopback endpoint) and `SSL_CERT_FILE` trust bundle.
It verifies TLS and forces that proxy even if `NO_PROXY` is set. Missing or
invalid proxy configuration fails closed; there is no direct retry. Ordinary
non-sentinel environment tokens retain the original direct-HTTPS behaviour.
Never print the token, proxy URL, or complete environment.
