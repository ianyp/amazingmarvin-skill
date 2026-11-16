> Reminder status superseded by [M reminder report](M_REMINDERS_REPORT.md): current task-linked M workflow replaces the unsuccessful legacy T adapter. Historical results below remain evidence about T only.

# Phases 2/3 + checklist subtasks — 2026-11-16

## Status

**Phase 2 implemented. Phase 3's supported named workflows implemented, with explicit research gates and uneven live evidence below. This is not full Marvin app parity and not a claim that every roadmap row is finished.**

User authorized full-access credentials and clearly labelled synthetic live items. Full-access auth was verified through Gateway protected egress; no token was read, printed or committed. No personal task, habit or reward balance was used as a fixture. No scheduler/config/model-routing changes were made.

## Evidence by workflow

| Workflow | Implementation | Live evidence |
| --- | --- | --- |
| Full token authentication | Explicit --full-access, capability guards | /test succeeded with correct header |
| Project creation / priority / note | Typed API + edits | Synthetic project created; typed edit receipt |
| Completed review | Explicit date, scheduled-day semantics | Completed synthetic task found under its pre-scheduled day |
| Goals / blocks / account / kudos | Read-only, account fields minimized | Successful responses, including empty blocks |
| Habit history + full catalog | Distinct history and raw catalog | Both list routes verified; per-ID branch offline-tested |
| Tracked time / date queries | Read-only POST, correct offset sign | Date read; empty timer; synthetic start/stop and cache reconciliation |
| Task/project typed editing | Whitelist, parent/label validation, timestamps, revision preflight | Synthetic task note/due/priority/planning/backburner read back |
| Checklist subtask creation | Appends unique dotted setters; preserves existing entries | Two synthetic checklist entries read back with correct structure |
| Habit record/undo | updateDB=true; integer values; no history replacement | Offline-tested only; no existing habit altered |
| Reward claim/unclaim/spend | Typed actions; no reset; profile redaction | Offline-tested only; no account reward experiment |
| Standalone reminders | Stable ID, bounded manual set/delete | Synthetic server-list readback and deletion; no notification delivery claim |
| Task-linked reminders | Staged dual-write/recovery code, production gate CLOSED | API receipt + task metadata succeeded, but server-list readback had no T reminder. Cause unresolved; test metadata cleared |
| Events | Typed timezone-aware create | Synthetic event creation receipt passed; calendar sync unverified |
| Notebooks/pages | Full-token read-only branches | Empty catalog and null notebook/pages response for synthetic project verified; no real pages used as fixtures |
| Attachments | Metadata match, private URL, 20 MB exclusive file, no token forwarding | Offline-tested only; no synthetic attachment upload endpoint exists |
| Narrow planning fields | Explicit typed week/month/sections/backburner | Week/month/DST validations offline; month/backburner live readback |
| Project completion/reopening | NOT implemented | Research gate: document flag changes do not reproduce client undo/completion semantics |

## TDD and regression evidence

New tests were run failing before each implementation slice: authentication; phase-2 reads/project creation; typed edits/subtasks/habits/events/rewards/notebooks; timer/manual-reminder recovery; attachment policy; CLI routes; validation hardening; task-reminder staged recovery. Live findings were captured as failing regressions before fixes.

Observed live contracts:

- idle trackedItem: HTTP 204 and empty body, normalized only for that endpoint;
- empty reminders: JSON null, normalized only for that endpoint;
- track issues: null, normalized to empty list;
- current help docs contain doneItems, notebooks/pages and downloadAttachment missing from older OpenAPI;
- reminder data-type docs specify seconds, endpoint example uses milliseconds. Server readback preserved submitted seconds, but actual firing timing is not proven;
- task-linked reminder: no retained server entry despite receipt and task metadata. It is gated rather than silently treated as successful.

Timer first attempt correctly surfaced partial_success on unexpected response shape. The synthetic timer was stopped, source-of-truth times reconciled, then a new start/stop lifecycle passed after the regression fix. No uncertain write was blindly replayed.

## Boundaries and remaining work

- Task-linked reminders need upstream/API behaviour investigation before enabling the staged branch. Due-date/project reminder types are not implemented.
- Project completion/reopening remains a research gate; setting done is not a substitute for client behaviour.
- Habits/rewards/attachments and nonempty notebooks need suitable synthetic fixtures for live proof. They are not labelled live-verified.
- Notification delivery, calendar synchronization and actual client UI rendering need viewer/device evidence, not merely API responses.
- Custom section/time-block IDs are syntax-validated, not checked against strategy configuration. Generic strategy editing is excluded.
- Deferred rows (history resets, permanent deletion, category/label creation, notebook writes, webhooks, database inventory etc.) remain deferred. Full-access credentials do not silently expand scope to those actions.

## Synthetic artifacts

The project `[OpenClaw API TEST] phases 2–3 2026-11-16` is intentionally retained for inspection. Test tasks were completed; standalone test reminder was deleted and failed task-reminder metadata cleared. No permanent deletion was used. The synthetic event create returned a receipt; the clearly labelled event remains, not a real appointment.

Live working state is private and outside source control. No account-content fixtures or private URLs are included in this report.

## Sources

- https://help.amazingmarvin.com/amazing-marvin/api-endpoints
- https://help.amazingmarvin.com/amazing-marvin/api-data-types
- https://github.com/amazingmarvin/MarvinAPI/blob/master/marvin-api.yaml

## Release checks

- 114 offline tests passed on Python 3.14.
- OpenClaw skill validator passed.
- Deterministic source-only zip built; git diff whitespace checks passed.
- New branch CLI tests include London summer/winter offset semantics, capability gates and malformed input.
- Documentation explicitly separates deferred features, closed research gates and live fixture gaps.
- Installed all nine source files to the workspace skill and verified byte equality. Installed CLI authentication succeeded; final timer was idle and reminders list empty.
- Previous installed copy backed up locally before replacement.
