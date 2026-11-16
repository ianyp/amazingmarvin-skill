# Named command workflows

All commands follow the shared auth/error procedure in SKILL.md. `--input-json -` reads at most 64 KiB from stdin. Dates are YYYY-MM-DD. Explicit IDs are mandatory for mutations. Outputs use the common JSON envelope.

## Read-only (no remote persistence)

| Request | Command | Meaning / verification |
| --- | --- | --- |
| Scheduled / due / completed | `today --date DAY`, `due --by DAY`, `completed --date DAY` | Completed filters scheduled day, not completion timestamp. |
| Browse | `categories`, `labels`, `children --parent-id ID` | Only immediate open children. |
| Goals / blocks | `goals`, `blocks --date DAY` | No goal or block editing implied. |
| Account | `account`, `kudos` | Account omits email and unrelated profile fields. |
| Habit history | `habit --id ID`, `habits` | Unrecorded habits absent; no names guaranteed. |
| Full habit catalog | `habits --raw` | Full token required; includes names and unrecorded habits. |
| Current timer | `tracked` | null means no active timer. |
| Recorded time | `tracks --ids ID ...` or `tracks --date DAY` | 1–100 IDs, or at most 100 date matches; date uses target-day timezone offset. |
| Task/project readback | `item --id ID` | Rejects unrelated document types. |
| Notebooks | `notebooks`; `notebook --id ID` or `--parent-id ID`; `page --id ID` | Full token; empty notebook can be null. |
| Server reminders | `reminders` | Not proof of device notification delivery. |

## Create and edit (persist in Marvin)

`add --input-json -`, `project --input-json -`:

```json
{"title":"Example","parentId":"KNOWN_ID","day":"2026-11-17","dueDate":"2026-11-30","estimateMinutes":20}
```

Allowed: title, day, dueDate, estimateMinutes, parentId, labelIds, note, plannedWeek (Monday), plannedMonth (YYYY-MM), dailySection (Morning/Afternoon/Evening), bonusSection (Essential/Bonus), customSection, timeBlockSection, backburner. Task priority uses isStarred (-1..3); project uses priority (high/mid/low). Project unscheduled day is null; task unscheduled is "unassigned". These are intentionally narrow fields, not every Marvin strategy.

`edit --id ID --input-json - [--expected-rev REV]` accepts the same mutable fields. Full token required. Validates item type, parent ancestry, label existence/exclusive groups; preserves unrelated fields; writes field timestamps. Revision checking detects observed changes but is NOT atomic compare-and-swap. Custom-section/time-block IDs must be resolved from known user data; existence is not currently validated by this adapter.

`subtasks-add --id TASK_ID --input-json -` takes an array of titles, e.g. `["Sort papers","File receipts"]`. Creates unique IDs and increasing ranks, appends dotted setters without replacing existing checklist entries. Read back `item` and match returned subtask IDs. Never replay an uncertain append.

`done --id TASK_ID`: experimental task completion. It may cause repeat/reward effects. A pre-scheduled task remains under its original day in `completed`.

`event --input-json -`: title, optional note, start (ISO datetime with timezone), length (positive milliseconds). Client must run for calendar sync; API receipt alone is not calendar-sync verification.

## Habit and rewards (persist account data)

`habit-record --id ID --value INTEGER [--time-ms TIMESTAMP]` (default now); `habit-undo --id ID`. Sends updateDB=true. No history replacement. Use known habit ID; do not guess from history-only lists.

`reward --action claim --id ID --points N [--date DAY]`; `reward --action unclaim --id ID [--date DAY]`; `reward --action spend --points N [--date DAY]`. Positive points only. MANUAL claims cannot be unclaimed. Responses suppress unrelated profile information. No automatic replay or reward reset.

## Timer workflows (server timer + task cache)

`track --id TASK_ID --action START|STOP`. Full token required so stopped task's times/duration can be updated. Starting may stop another active task: update the returned stopId, not blindly the requested ID.

On partial_success, read `tracked` and `tracks` for exact IDs. Use `reconcile-tracking --id STOPPED_TASK_ID` to repair cache from source-of-truth intervals; this does NOT start/stop timers. Running/odd intervals are rejected for reconciliation rather than inventing duration.

## Reminders (server + optional task metadata)

`reminder-set --input-json -` accepts standalone manual reminders:

```json
{"reminderId":"unique-stable-id","type":"M","time":1794996000,"title":"Example","offset":0,"snooze":0,"autoSnooze":false,"canTrack":false}
```

`time` is unix seconds per the data-type documentation; live server-list readback preserves this value. Actual firing/delivery timing has not been verified (the endpoint example contradicts the type docs). `reminder-delete --id ID` requires a unique existing manual reminder. Deletion is scoped to that reminder, not all reminders.

**Task-linked reminder branch is gated, not shipped as working.** The staged adapter received an API receipt and successfully wrote task metadata, but live server-list readback contained no corresponding T reminder. Cause is not established. `task-reminder-set` and `task-reminder-delete` return unsupported_capability before network access in production. Offline tests exercise the staged dual-write/recovery design only, not app parity.

`reminder-reconcile --id TASK_ID` or `--deleted` remains available for repairing known partial metadata states from server truth. It never resends a server action. Do not use it to manufacture a working reminder. The synthetic test's stale metadata was cleared.

## Attachment download (local file persistence)

Read the exact task/project's attach_UID metadata. `download --id ITEM_ID --uid UID --output /absolute/new-file` verifies metadata, obtains a temporary URL privately and saves at most 20 MB with mode 0600. No overwriting, redirects or token forwarding. Requires subscription and full token. A new hosting domain is an explicit unsupported-host error, not a silent fallback.

## Task start/end dates

Task capture (`add --input-json FILE`) also accepts optional `startDate` and
`endDate` as exact YYYY-MM-DD dates. These are independent of the scheduled
`day` and deadline `dueDate`; do not substitute one for another.
Example input:

```json
{"title":"Prepare notes","startDate":"2026-11-17","day":"2026-11-18","dueDate":"2026-11-19","endDate":"2026-11-20"}
```

Both token modes support this creation route. Omit unused dates; null and
natural-language strings are rejected. These fields are currently supported
only for task creation, not project creation or edits. The API documents
preserving them; app strategy visibility and live readback have not been
verified. Today/due API results are not filtered to emulate the app.
