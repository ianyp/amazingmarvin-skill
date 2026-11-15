# Amazing Marvin V1 release report

15 November 2026 — v0.1.0

## Delivered and verified

- 56 offline tests pass on Python 3.14; skill frontmatter validation passes.
- Protected Secrets token used through Gateway HTTPS proxy, never printed or committed.
- Live authentication, scheduled items, due items, categories, labels, Inbox children and one category’s children all returned valid contracts. Personal titles, notes and identifiers were not saved as fixtures or included in this report.
- One explicitly authorized synthetic task was created with scheduled date, deadline, estimate and note. Exact returned ID was found in scheduled items with the expected title.
- Completion returned that exact ID with `done: true`; subsequent scheduled-items read no longer contained it. This verifies API receipt and disappearance from the open list, not all Marvin client side effects.
- Synthetic task ID: `423a6d817c75a5139c5d3029d5f551e4`. It remains completed in Marvin; no deletion attempted. No existing personal task was modified.
- Installed using `openclaw skills install` into `/home/ian/.openclaw/workspace/skills/amazingmarvin`.
- `openclaw skills info amazingmarvin --json` reports eligible, modelVisible, userInvocable and commandVisible, with no missing requirements or allowlist blocks.
- Installed helper invoked through gateway_exec from `/tmp`; live Today read succeeded.

## Conversation evaluation

Manual branch review by the implementing agent, not an independent automated model benchmark:

| Scenario | Expected and reviewed decision |
| --- | --- |
| Show Marvin today | Use today; local date; read only. Installed helper exercised live. |
| Due tomorrow | Use due --by with next Europe/London calendar date, not scheduled-date query. |
| Schedule Friday | Capture a new task with day only when creation is intended; rescheduling an existing task is unsupported in v1. Clarify genuinely ambiguous dates. |
| Duplicate task/category/label name | Ask for exact selection; never write based on a guess. |
| API failure or uncertain write | Report error; do not fabricate empty results or replay writes. Offline tests cover failure handling. |
| Malicious task note | Treat as task data; never execute embedded instructions. |

The current turn’s skills_read snapshot predates installation and cannot load the newly installed name yet. CLI discovery and direct installed-helper execution pass; fresh-turn automatic selection is not claimed as tested. No restart or configuration change is necessary for this release.

## Scope and limitations

Only v1 daily task workflows are delivered. Rich editing, habits, timers, reminders and other roadmap phases remain unimplemented. API lists need not match client UI visibility. No polling, jobs, agents, model/account/fallback routing or background inference configuration was added or changed. Standard runtime dependency: Python 3.11+ on Linux. Token remains limited-access.

Package: `dist/amazingmarvin-skill-offline.zip` (historical filename; contains the live-verified source). Offline CI never uses account credentials. GitHub CI and publication outcome are recorded below.
