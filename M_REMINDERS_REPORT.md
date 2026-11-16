# Task-linked M reminders — 2026-11-16

## Corrected contract

A user-created reminder observed read-only in the current Marvin app has:

```json
{"reminderId":"REMINDER_ID","taskId":"TASK_ID","type":"M","time":1794937800,"offset":0,"snooze":5,"autoSnooze":false,"canTrack":false}
```

The corresponding task contains:

```json
{"reminders":[{"reminderId":"REMINDER_ID","time":1794937800}]}
```

Identifiers above are placeholders. No personal task titles, IDs or account data
are published. The task's scheduled day differed from the reminder date, and
there were no legacy reminderTime/reminderOffset fields.

The previous implementation incorrectly treated all M reminders as standalone
and all task linkage as type T. The official data-type reference still describes
M as unrelated to a task and T as a task with a time; it omits the observed
`taskId` and task `reminders` array. The old failed tests establish failure of
that T payload, not inability to create task-linked M reminders.

## Implementation

- Full-access-only linked-M set/update/delete with explicit task ID and separate,
  stable reminder ID. Multiple reminders per task; absolute timezone-aware time.
- Retention/ownership readback before task metadata mutation; reread and merge
  metadata, preserve other reminders, reject observed revision conflicts, and
  verify metadata readback. Never blindly replay an uncertain write.
- Reconciliation changes only task metadata using the existing server entry, or
  confirms server absence before clearing the exact intended deleted entry.
- Standalone delete rejects M reminders with taskId. Legacy T, due-date/project
  reminders and recurring reminders remain unsupported.
- No atomic compare-and-swap is available. Concurrent app edits still present a
  race; revision checks reduce but cannot eliminate it.

## Verification

134 offline tests pass, including CLI set/reconcile/delete, ownership collisions,
missing retention, partial writes, no replay, multi-reminder preservation,
timezone/full-access validation and observed revision conflict handling.
Skill structure validator passes.

Live synthetic create, in-place update, second reminder, scoped deletion preserving
the second reminder, metadata reconciliation and final deletion all passed. Both
synthetic server entries and task metadata were cleared, and the test task was
completed with readback. The final server list contained only the original user
reminder, unchanged.
App rendering and phone notification delivery are not verified by API readback.
The user's original reminder was not mutated.

## Sources

- https://help.amazingmarvin.com/amazing-marvin/api-data-types
- https://github.com/amazingmarvin/MarvinAPI/issues/46#issuecomment-1049358147
- https://github.com/amazingmarvin/MarvinAPI/issues/67

Issue 67 describes dual storage but not this exact newer M linkage contract.
The actual current app-created data, not that issue's standalone terminology,
is the implementation reference.

## Community follow-up

An independent integration documents the same newer format: a task `reminders`
list plus one type M server entry per custom reminder. It distinguishes this from
clock-time/T reminders. This independently corroborates the app sample and our
live results:

https://github.com/andreasd083/amazing-marvin-complete-mcp#marvin-api-quirks--findings

Searches of the public Marvin subreddit found the author's integration discussion
and an older question about importing reminder times via the API. No exact
M/taskId question surfaced on the official community domain. Search coverage is
not exhaustive; private Facebook/Discord discussions were not searched.

Community links surfaced by search:
- https://www.reddit.com/r/amazingmarvin/comments/1vsy02w/i_built_an_mcp_server_with_complete_marvin_api/
- https://www.reddit.com/r/amazingmarvin/comments/16bw5uq/ios_shortcuts_and_the_amazingmarvin_api/

Direct browser inspection confirmed the official community homepage is a
roadmap/changelog/feature-voting hub, not a searchable discussion forum.
Reddit blocked full-thread browser access with a human-verification challenge;
these thread summaries are search-derived, not a verified reading of all comments.
The independent integration's GitHub README was directly read and explicitly
confirms the task-list + M-server-entry format. No exact prior forum question
about M/taskId was confirmed, and no posts or comments were sent.
