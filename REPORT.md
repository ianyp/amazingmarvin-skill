# Amazing Marvin skill — delivery report

13 November 2026

## Summary

The **first-release core is implemented and packaged for offline review**. It is not the complete Amazing Marvin feature roadmap, and it has not been installed or tested against a live account.

**Verification:** 49 local tests passed; OpenClaw skill validation passed; seven-file source package verified. All testing used synthetic data, including local HTTP servers. No Marvin account changes were made.

## Delivered functionality

- Show scheduled tasks/projects on a date and items due on/before a date.
- Look up categories and labels; browse immediate open project children.
- Create tasks with explicit scheduled date, deadline, estimate, parent, labels and notes.
- Complete a known task ID, with local timezone offset.
- Check limited-token credentials without changing tasks.
- Structured JSON results and errors; ambiguous writes are not automatically repeated.
- HTTPS public API transport, redirect blocking, response limits and credential-safe errors.
- Shared cross-process rate spacing, conservative local request budget and server cooldown handling.

Task titles are literal. Category/label name resolution is a skill workflow using lookup results; the CLI takes exact IDs. API lists are not guaranteed to mirror all Marvin UI visibility rules. Unknown or duplicated targets must not be guessed.

## Testing and TDD

Feature tests were written and run failing before implementation, then made green. DEVELOPMENT.md records the red/green sequence. Additional verification covers subprocess concurrency, summer/winter timezone offsets, local midnight, malformed input, server errors and a server accepting a write but dropping its reply. That last check verifies one attempt and an explicit unknown outcome.

Tests run locally on Python 3.14. CI is configured for 3.11–3.14 but has not run remotely. Static skill validation and deterministic tests do not prove real OpenClaw conversational execution or live Marvin API compatibility.

## Artifacts

Repository: `/home/ian/.openclaw/workspace/projects/amazingmarvin-skill`

Package: `dist/amazingmarvin-skill-offline.zip`

Skill source: `skills/amazingmarvin/`

Run tests: `python -m unittest discover -s tests -v`

Rebuild package: `python tools/package_skill.py`

## Current blocker and completion boundary

No MARVIN_API_TOKEN is available in the execution environment. Live verification therefore remains blocked. A personal Marvin account's limited token is enough for this core; no full-access token or database credentials are needed.

After secure token configuration: run a non-mutating credential/read check, verify actual response shapes, then perform creation/completion only on a specifically authorized synthetic test task. Installation and a release tag follow successful live and OpenClaw runtime checks. Do not paste credentials into chat.

## Remaining roadmap

Projects, goals, completed-item reviews, time blocks, habits, time tracking, reminders, richer editing, notebooks and attachments remain later phases. FEATURE_COVERAGE.md distinguishes API support, permissions and client-dependent limitations. Full app parity is neither implemented nor claimed.

No paid services, hosted MCP account, background polling, model-routing changes, remote Git publication or personal task mutations were introduced.
