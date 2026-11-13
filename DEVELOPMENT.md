# Implementation status

2026-11-13: first offline core implemented. Not installed or live-ready.

## Run tests

```sh
python -m unittest discover -s tests -v
```

No packages, credentials or network needed. Standard-library unittest replaces the proposed pytest dependency because pytest is not installed and this initial suite needs no third-party features.

## TDD evidence

- Initial nine contract tests: nine expected NotImplementedError failures from explicit Client stub, then nine passing after implementation. Missing-credential test adjusted to supply the explicit required transport seam.
- Additional validation tests: 13 run, two behavioural failures (header injection and unrecognized write receipt), then all 13 passing after fixes.
- Cases cover exact scheduled/due query construction, invalid dates, title-autocomplete suppression, units, unsupported fields, API errors, read response shape, secret-free timeout reporting, no write replay and unknown write outcomes.

## Current boundary

Client has an injected transport only. No default networking implementation, CLI, installed SKILL.md, real token access or account mutations. Network transport, cross-process rate limiter, complete read/write workflows, packaging and live checks remain outstanding. Feature coverage map remains planned, not implemented.

## Reuse decision status

Official CLI README explicitly warns of incomplete functionality; community MCP README assumes hosted service and has semantics differing from current official API docs. These are reasons to investigate, not sufficient evidence to reject reuse. The small offline operation contract is transport-independent and can be retained with either reuse or direct HTTP. Complete source/license/maintenance and credential-handling audit before choosing production transport. No dependency added or third-party service contacted with private data.

## Next slice

Write failing transport contract tests using a local fake HTTP server: auth redaction, redirects, timeouts, malformed responses, throttling and write uncertainty. Then implement transport and persistent rate accounting, followed by CLI and remaining v1 operations. Do not expose this prototype as an installed skill before those gates pass.
