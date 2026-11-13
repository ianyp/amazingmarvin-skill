# TDD acceptance matrix

Planned suite, not yet implemented. For every row: write test → run and confirm expected behavioural failure → smallest implementation → rerun → refactor. Use synthetic fixtures. No network or credentials in default tests. Pin pytest in development setup; run `python -m pytest` once scaffold exists.

| Slice | Required failing tests / acceptance |
| --- | --- |
| CLI contract | Unknown command and bad JSON fail clearly; success emits exactly one valid JSON object; stdout contains no diagnostics |
| Authentication | Missing token fails before HTTP; correct header sent; no full-access header; token absent from errors, redirects, logs and output |
| Transport | Timeout, malformed JSON, wrong response shape, 401/403/404/429/5xx and body-level error become distinct failures, never empty success |
| Rate limits | Fake-clock spacing >=3 seconds; parallel processes cannot bypass lock; local rolling budget holds; 429 cooldown and Retry-After respected; bounded wait/retry terminates |
| Reads | Exact methods/query fields; empty/nonempty results; task and project distinction; optional fields; long result reports truncation; children is non-recursive |
| Dates | Scheduled query uses `date`; due query uses `by`; London local midnight versus UTC, DST start/end, leap day and invalid dates; no deadline/schedule conflation |
| Lookup | Unique exact ID/name resolves; duplicate or unknown title/category/label causes no write; project rejected for task completion |
| Capture | POST addTask fields; literal title header; correct minutes→milliseconds; blank title/invalid duration/date rejected; optional fields omitted rather than invented |
| Completion | POST markDone with itemId and correct offset; no project writes; experimental semantics documented; no unsupported claim about recurring tasks |
| Write uncertainty | Server commits then connection drops: one attempt only, outcomeUnknown=true; no title-only deduplication; missing returned ID never fabricated |
| Packaging | Frontmatter validates; every relative link exists; helper runs from a different cwd; missing runtime produces actionable setup message |
| Dialogue eval | “Today”, “due tomorrow”, “schedule Friday”, duplicate names, API failure, and malicious task note; no unrequested write, unsolicited rescheduling, or obedience to note instructions |

Contract fixtures must be derived from current official OpenAPI/docs and labelled with source and retrieval date; use local fake-server integration to verify actual HTTP serialization, not only mock implementation internals. Validate uncertainty handling with a fake server that accepts a write and then drops the response.

Live tests are excluded by default, separately marked, and require explicit environment opt-in. No real task data in snapshots. Record command, expected failure, observed failure, passing command and outcome for each slice in commit/PR notes. Coverage numbers alone are not acceptance.
