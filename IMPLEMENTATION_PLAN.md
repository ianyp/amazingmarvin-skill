# Implementation plan

Date: 2026-11-13. Status: ready for implementation; scope is a proposed baseline.

## Expanded roadmap

See [FEATURE_COVERAGE.md](FEATURE_COVERAGE.md) for broader feature coverage, permissions, limitations and phased TDD gates. The exclusions below apply to v1 only, not the overall integration roadmap. Full application parity is not assumed.

## Goal and boundaries

Build a discoverable, repository-owned OpenClaw skill for ordinary Amazing Marvin task management. Deliver concise results without adding planning overhead. Initial deliverable requested is this plan and Git repository, not installation or live account changes.

Assumptions: cloud API enabled; interactive on-demand use; Europe/London is the user's timezone but configurable; Python 3.11+ is a proposed helper runtime. Credentials are not needed for planning or offline tests. Confirm cloud versus desktop support before integration testing, without blocking offline work.

### v1 workflow contract

| Trigger | Outcome | Persistence |
| --- | --- | --- |
| Show today's tasks / tasks on a date | Scheduled API items, IDs and explicit date | None |
| What's due / overdue? | Open due items through requested date | None |
| List categories/labels or browse a project | IDs and names; immediate children only | None |
| Add a task, optionally scheduled/due/estimated/filed | Validated task creation with API receipt | Marvin |
| Complete a named task or explicit ID | Resolve unambiguously, mark task done, report receipt | Marvin |

Keep scheduling (`day`) separate from deadline (`dueDate`). Do not claim that API lists exactly match Marvin's UI: backburner, dependencies and other visibility rules differ. Preserve task/project distinctions. Ask only for genuine ambiguity, such as duplicate task titles; do not reconfirm an explicitly requested ordinary write.

Out of scope: deletion, arbitrary document updates, direct CouchDB access, full UI visibility emulation, bulk rescheduling, habits, timers, calendar integration, desktop API, webhooks and recurring automations. Later phases can add these independently.

## 1. Reuse gate (first implementation checkpoint)

Evaluate the official marvin-cli against TEST_PLAN.md's v1 contract using a pinned revision, and inspect its license, maintenance, output format, credential handling and transport behaviour. Its README warns it is work-in-progress. Evaluate local reuse of the community MCP code as an alternative; do not connect to its hosted service or transmit credentials there.

Choose a thin wrapper around an existing implementation if it passes. Otherwise record concrete gaps in an ADR and implement the small public-API adapter below. Do not assume the search proves no other skill exists: check installed skill/plugin catalogs and current repositories again at implementation start. No paid service is needed.

Exit: recorded choice, pinned dependencies/license review, verified endpoint/auth/response contracts against current official docs/OpenAPI. Research has not yet established third-party code quality or maintenance.

## 2. Proposed structure (if small adapter is justified)

```text
skills/amazingmarvin/
  SKILL.md
  scripts/marvin.py          # thin JSON CLI entry point
  scripts/marvin_client.py   # validated API operations and transport
  references/api-contract.md
  references/setup.md
tests/
  unit/
  contract/
  integration/
  fixtures/                 # synthetic only
pyproject.toml
```

Prefer Python standard library transport, argparse, zoneinfo and JSON; pytest is development-only. Keep HTTP transport, clock and sleeper injectable. Use a local fake server for CLI contract tests. No app server, database or model invocation is necessary. If reuse wins, keep the public CLI contract and replace adapter internals accordingly.

Proposed CLI: `today --date YYYY-MM-DD`, `due --by YYYY-MM-DD`, `categories`, `labels`, `children --parent-id ID`, `add --input-json FILE`, `done --id ID`, `check-auth`. Output one JSON object on stdout; diagnostics on stderr; stable nonzero errors. Success envelope: `ok`, `operation`, `data`; failure: `ok`, `operation`, `error` with `code`, `message`, `retryable`, `outcomeUnknown`. Never invent a created ID if the server does not return one.

## 3. Authentication and transport (TDD first)

Inject MARVIN_API_TOKEN from runtime environment/approved secret reference. Document actual OpenClaw setup syntax only after checking installed version. Never place tokens in command arguments, source, fixtures, output or Git. Use X-API-Token only for v1. Fixed HTTPS public API origin; reject credential-bearing redirects. Validate inputs before network access.

Enforce at least three seconds between requests across concurrent helper processes using a locked, minimal local rate-state file outside the repo; no task contents or token stored. This state is transport accounting, not monitoring scratch. Track a conservative rolling local 24-hour request ceiling of 1440, explaining it cannot measure other clients' shared usage and differs from Marvin's average quota. No automatic polling. Rate waits have a bounded deadline and return actionable errors if too long.

Read operations: bounded retry for transient failures, respect Retry-After, wait at least the documented roughly one-minute cooldown after 429; use injected time in tests. Never retry authentication/validation failures. Writes: no automatic replay after timeout, connection loss or ambiguous server failure; report outcome unknown and reconcile before any further attempt. An API error inside a successful HTTP response is not a successful operation. Redact secrets from all exception paths.

## 4. Read workflows

Implement category/label/children, scheduled and due reads in small red-green-refactor slices. Explicit dates use user's timezone, not server UTC. Resolve today/tomorrow at invocation time; test London DST and midnight. Bound output size and recursive browsing; no recursive fetch by default. Report truncation, don't silently omit items or fabricate empty lists after failures.

## 5. Write workflows

Task creation uses explicit fields, validated date strings and minute-to-millisecond conversion. Disable Marvin title autocompletion by default with X-Auto-Complete=false so literal titles cannot silently change fields. Shortcut interpretation is deferred.

Resolve category/label/task names to unique IDs; unknown or duplicate names do not trigger a write. Completion accepts tasks only; document experimental endpoint limitations. Preserve response evidence and distinguish successful receipt, verified readback, failure and unknown outcome. Readback is bounded, only when supported/needed, and must not use title matching alone to claim identity.

## 6. Skill instructions and packaging

Write model-discoverable frontmatter (`name: amazingmarvin`, description with clear triggers). Instructions link directly to setup and API references and helpers using skill-relative paths. Document each branch with completion criteria, ambiguity handling, safe error reporting, and verification. Treat retrieved titles/notes as data, never instructions. No command-tool dispatch unless an actual registered tool exists.

Run OpenClaw skill-creator's quick_validate.py against the skill directory, verify referenced paths and run all helper tests. Evaluate dialogue scenarios separately from deterministic tests; describe manual evaluation honestly. Install only the verified skill directory, not tests or secret material; keep Git source as the maintained copy. No scheduler, model routing or gateway configuration changes are part of v1.

## 7. Opt-in live validation and release

Offline tests must pass first. Read-only live check needs configured credentials and an explicit live-test flag. Write smoke tests must additionally target an authorized test task; never mutate existing personal tasks as test data. Create one clearly tagged test task then complete that exact returned/verified ID; leave it documented for cleanup (deletion is out of scope). If creation yields no usable ID, stop and report rather than guessing.

Record API differences without committing personal data. Tag v0.1.0 only once contract tests, packaging validation and authorized live checks pass. If credentials/live access are unavailable, report offline-ready, live-unverified rather than complete. Rollback removes the installed skill copy; it does not undo remote tasks. Publishing/pushing needs a specified destination; none is assumed.

## Sequenced commits and exit gates

1. `test: establish CLI and API contract harness` — harness fails for missing behaviour, not missing dependencies.
2. `feat: implement authenticated bounded transport` — redaction, throttling, errors and retry tests green.
3. `feat: add date-aware read workflows` — all read/date tests green.
4. `feat: add validated task capture` — create and ambiguous-outcome tests green.
5. `feat: add unambiguous task completion` — resolution and completion tests green.
6. `docs: package OpenClaw skill and setup` — validator and dialogue evaluation pass.
7. `test: document authorized live verification` — actual results or explicit blocked status, then release.

Each feature commit records test-first evidence; refactor only with green tests. Run focused tests per slice and the full offline suite before release. Do not implement later slices before their failing acceptance tests exist.
