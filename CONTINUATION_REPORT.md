# Continuation verification — 2026-11-16

## Completed
- Explicit minimal/full token CLI options retained; minimal remains default.
- Task creation startDate/endDate passed live readback independently of day/dueDate. Labelled synthetic task completed afterwards.
- Typed task/project startDate/endDate edits and null clearing implemented after official data-type schema review; failing tests preceded implementation.
- Staged task-reminder adapter now checks retained type/time/offset before writing task metadata. Missing, mismatched or failed readback reports partial success/unknown outcome, never replays the server write. Production gate remains closed.
- Task and project date editing and null clearing both passed live readback on labelled fixtures; original date fields restored afterwards.
- 124 offline tests pass; skill validator and diff whitespace checks pass.

## Concrete remaining blockers
- Task reminder retention: repeated paired M/T experiments with a future timestamp. Manual reminder retained, T reminder absent, both with metadata absent and metadata written first. Both cases used the same documented seconds/offset payload. Cleanup verified and synthetic task completed. This rules out write order as a sufficient fix, not all potential causes. Do not enable or claim notification delivery.
- Complete/reopen: official markDone supports tasks only. Generic document setters do not reproduce completion side effects. Community reopening recipe explicitly leaves kudos unchanged; no supported faithful undo route established. Do not ship raw done toggles as app-equivalent completion.
- Habit write verification: read-only fixture audit found no labelled synthetic habit. Existing personal habits are not test fixtures; creating habits via generic documents remains outside implemented scope.
- Notebook verification: notebook catalog is empty. No nonempty notebook/page fixture exists.
- Attachment verification: no dedicated synthetic uploaded attachment; upload has no documented route in this adapter. Do not use personal files as implicit fixtures.
- Reward verification: claim/spend mutates account-wide history/balance; no isolated test account supplied. Reversal does not make a real account an isolated fixture.
- Phone delivery/calendar sync require client evidence; server receipts do not prove these.
- Repository push remains separately blocked by the previously observed Git credential context.

No credential values, personal task content, account profiles or temporary download URLs are included here. No new configuration, scheduler or inference-routing changes.

## Research sources
- https://help.amazingmarvin.com/amazing-marvin/api-endpoints
- https://help.amazingmarvin.com/amazing-marvin/api-data-types
- https://github.com/amazingmarvin/MarvinAPI/issues/52 (reopen recipe and kudos limitation)
- https://github.com/amazingmarvin/MarvinAPI/issues/46 (server-side reminders)
- https://github.com/amazingmarvin/MarvinAPI/issues/67 (dual-write reminders and nonreversible manual reward claims)

Community claims are research evidence, not guarantees of complete client semantics.
