# Amazing Marvin feature coverage and phased roadmap

Researched 2026-11-13 against the official [endpoint reference](https://help.amazingmarvin.com/amazing-marvin/api-endpoints). This is an API capability map, not a claim of implemented or exhaustively verified app parity. Current delivery is recorded below and in [V2_V3_REPORT.md](V2_V3_REPORT.md). Phase numbers are sequencing, NOT completion status. Deferred remains outside phases 2/3; research gates are explicit.

L = limited API token; F = full-access token; D = direct database credentials. A personal account supplies these; no separate developer account is required. Mock-based development needs none. Credentials are separate capabilities, never automatic fallbacks. An API token labelled limited still permits writes.

## Coverage matrix

| Feature / workflow | Documented route | Permission | Limitations and tests required before delivery | Phase | Current status |
| --- | --- | --- | --- | --- | --- |
| Task capture | POST addTask | L | Explicit day vs dueDate; literal title; estimates in ms; missing ID/timeout handling | 1 | Implemented (V1) |
| Today / due / project children | GET todayItems, dueItems, children | L | Explicit dates; children only open immediate descendants; API lists differ from UI | 1 | Implemented (V1) |
| Categories and labels lookup | GET categories, labels | L | Duplicate names; retain IDs; do not claim these endpoints create categories/labels | 1 | Implemented (V1) |
| Task completion | POST markDone | L | Tasks only; experimental; pinned/echo/reward side effects; not full client parity | 1 | Implemented (V1) |
| Project creation | POST addProject | L | priority is high/mid/low, not task isStarred; scheduled/unscheduled contracts | 2 | Implemented; live route checked |
| Completion review | GET doneItems | L | Filters scheduled day, not necessarily completion timestamp; test pre-scheduled completion | 2 | Implemented; live route checked |
| Goal listing | GET goals | L | Listing is not goal creation, progress editing or complete goal workflow | 2 | Implemented; live route checked |
| Time-block viewing | GET todayTimeBlocks | L | Explicit date; experimental; creation/editing not exposed by this route | 2 | Implemented; live route checked |
| Current timer and recorded time | GET trackedItem; POST tracks | L | Up to 100 tasks; running/empty timers; tracks timezone sign differs from timeZoneOffset | 2 | Implemented; live route checked |
| Habit history by known ID | GET habit, habits | L | Returns history, not names; never-recorded habits absent | 2 | Implemented; live route checked |
| Kudos / account summary | GET kudos, me | L | Minimise account fields; no email or profile dumps in logs | 2 | Implemented; live route checked |
| Habit names and complete catalog | GET habits?raw=1 | F | Needed for unrecorded habits and names; reject missing F, never silently degrade to misleading empty catalog | 3 | Implemented; see per-workflow live evidence |
| Habit record / undo | POST updateHabit with updateDB=true | L | Whole-number values; database synchronization; ambiguous write not replayed | 3 | Implemented + offline tests; live writes/download unverified |
| Habit history replacement | POST updateHabit with history | L | Destructive replacement; defer until explicit workflow and recovery design | Deferred | Deferred; not implemented |
| Task/project editing, rescheduling, notes, labels, priority | GET doc; POST doc/update | F | Field whitelist, type validation, parent/label existence, fieldUpdates and updatedAt; server does not validate shape | 3 | Implemented; see per-workflow live evidence |
| Complete/reopen projects; reopen tasks | POST doc/update | F | Setting done alone is not proof of client completion/undo side effects; require semantic investigation | 3 research gate | Research gate CLOSED; not implemented |
| Time tracking start/stop | POST track | L for timer; F for task-cache updates | Caller must update stopped task times/duration; partial-success reconciliation, switching timers and no duplicate intervals | 3 | Implemented; see per-workflow live evidence |
| Reminder listing | GET reminders | F | Server state distinct from task UI metadata | 3 | Implemented; see per-workflow live evidence |
| Reminder set/delete | POST reminder/set, reminder/delete | L; F for matching task metadata | Mobile notification delivery requires logged-in app; partial-success recovery; timezone and stable reminder IDs | 3 | Standalone M: live readback/delete passed. Linked M: implemented; see M_REMINDERS_REPORT.md for verification. Legacy T remains unsupported |
| Calendar event creation | POST addEvent | L | Experimental; client must run for calendar sync; receipt is not sync/delivery proof | 3 | Implemented; see per-workflow live evidence |
| Notebook reading | GET notebooks, notebook; GET doc for page | F | Experimental; notebook/page IDs, empty notebook; project note maps to first page | 3 | Implemented; empty catalog live-checked, nonempty pages unverified |
| Notebook/page writing | POST doc/create or doc/update | F | Requires verified data-type schemas; do not treat arbitrary document writes as supported notebooks | Deferred | Deferred; not implemented |
| Attachment download | POST downloadAttachment | F + active subscription | Returns temporary bearer URL; keep private, bounded downloads; no documented upload route here | 3 | Implemented + offline tests; live writes/download unverified |
| Reward claim/unclaim/spend | POST claimRewardPoints, unclaimRewardPoints, spendRewardPoints | L | Positive points; MANUAL claims cannot be unclaimed; overspend errors; ambiguous response never replayed | 3 | Implemented + offline tests; live writes/download unverified |
| Reward history reset | POST resetRewardPoints | F | Permanently loses earn/spend history; excluded from default skill | Deferred | Deferred; not implemented |
| Category/label creation and editing | Generic doc routes / data-type schemas | F | No dedicated creation route in reviewed reference; validate nesting, exclusivity, allowed fields | Deferred | Deferred; not implemented |
| Delete items | POST doc/delete | F | Permanent API deletion; no Marvin Trash recovery; setting deletedAt does not emulate Trash | Deferred | Deferred; not implemented |
| Delete all reminders | POST reminder/deleteAll | F | Requires matching task metadata cleanup; bulk destructive operation | Deferred | Deferred; not implemented |
| Full inventory/search/archive/history | Database queries or bounded tree traversal | D or limited partial reads | No universal search endpoint verified; partial traversal must not claim complete search | Research | Research; not implemented |
| Recurring tasks, subtasks, dependencies, start/end dates | Some create fields; otherwise document schemas/client logic | Varies | Fields existing in data is not complete behaviour support; test recurrence and dependency semantics individually | Research | Checklist subtask creation implemented + live readback. Task creation startDate/endDate live readback verified; typed task/project date edits and clearing live-verified. Other features remain research |
| Planned weeks/months, daily sections, backburner | Some addTask/addProject fields; doc/update for edits | L create / F edit | Strategy settings and client visibility differ; preserve exact date/section meaning | 3 narrow fields | Implemented; see per-workflow live evidence |
| Smart lists, custom strategies, planning views, auto-scheduling, dashboards | No dedicated routes verified in reviewed reference | Unverified | Do not emulate client algorithms or write strategy settings speculatively | Research | Research; not implemented |
| Webhook integrations | Separate official webhook API docs | Unverified here | Separate design: authenticity, replay protection, delivery, deployment and inference costs | Deferred | Deferred; not implemented |
| Local-only desktop integration | Official CLI/local API | Separate local setup | Cloud API assumptions do not apply; separate endpoint/auth/capability audit | Deferred | Deferred; not implemented |

## Delivery sequence (historical plan; current status above)

1. **Foundation and daily task workflow:** original v1 with offline-first TDD; stable JSON adapter, auth and rate control.
2. **Broader read-only coverage plus project creation:** goals, blocks, completed items, timer/track reads and habit history. Clearly label incomplete limited-token habit catalog. Project creation is a separate write slice.
3. **Typed richer workflows:** enable narrowly scoped full-token features independently; no generic arbitrary-document command exposed to the assistant. Add named habit workflows, whitelisted edits, tracking reconciliation, reminders, events, notebooks and downloads in independently tested slices.
4. **Research-gated features:** only promote unsupported/client-dependent operations after documented semantics and tests exist. Direct database access and irreversible operations are not implied by enabling a full-access token.

Phases are dependency order, not time estimates or a promise that every Marvin UI feature can be replicated. Each new branch needs a trigger, expected result, persistence target and verification step in SKILL.md before release.

## Expanded TDD gates

For each feature add failing tests for endpoint/method/auth, request schema, representative response, denied permission, absent/duplicate target, rate budget, malformed/error response and unknown write outcome. Then implement the smallest behaviour, run tests, refactor and record evidence.

Special contracts:

- **Capabilities:** L-only configuration cannot execute F routes; missing full access returns an actionable unsupported-capability result, not a generic empty result.
- **Timezones:** tracks.timeZone uses the documented opposite sign convention to creation/completion timeZoneOffset; test both winter and summer in London.
- **Dual-write workflows:** simulate first write succeeding and second failing. Return partial success and exact recovery state; never claim complete synchronization or replay the first write blindly.
- **Edits:** preserve unrelated fields, validate document type and setter whitelist, include change timestamps, test concurrent changes and re-read before reconciliation. Verify actual server conflict semantics before promising atomic compare-and-swap.
- **Habit catalog:** distinguish no recorded history from no habits; titles require raw catalog/full token or a user-provided ID.
- **Timers:** handle switching from another task and update returned stopped task, not only requested task. Do not manufacture duration when intervals are incomplete.
- **Reminders/events:** distinguish API receipt, synchronized task metadata and actual phone/calendar delivery. A mock cannot prove notification delivery.
- **Attachment URLs:** never log bearer links; no API token forwarded to file host; size/type limits and safe filenames.
- **Destructive operations:** excluded until explicitly scoped. Tests must prove no destructive call is reachable through ordinary editing.

Offline CI never uses a personal token. Live test data must be dedicated synthetic items, and account-wide history/reset operations are not live smoke tests. A personal account is sufficient but not a sandbox: retain read-only live defaults and require explicit authorized test-item selection for writes.

## Known blockers, not user homework

Implementation must resolve third-party reuse suitability, current OpenAPI/response consistency and client-side semantics as each phase reaches them. No key is needed to do this research or write offline tests. Ask the user only for genuine workflow priorities, unavailable account capabilities or live-test authorization, not for an exhaustive feature specification.
