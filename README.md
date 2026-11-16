# Amazing Marvin OpenClaw skill

**Phase 2 and supported phase-3 workflows implemented; checklist subtask creation live-verified.** Task-linked reminders and project completion/reopening remain explicitly gated. See [delivery and limitations](V2_V3_REPORT.md) and the [current coverage matrix](FEATURE_COVERAGE.md).

## Implemented

Tasks/projects, checklist append, whitelisted edits and planning fields; broader date-aware reads; habit catalog/history/record/undo; timer start/stop and cache reconciliation; manual reminders; events; read-only notebooks/pages; bounded attachment downloads; typed reward actions. Protected full/limited token authentication, shared rate accounting, JSON errors and partial-success recovery. No arbitrary document mutation CLI.

Implementation is not the same as live verification: habits/rewards/attachments/nonempty notebooks are offline-tested, with live fixture gaps clearly recorded. No full Marvin UI parity claim.

## Verify and package

Requires Linux and Python 3.11+ with timezone data; locally tested on Python 3.14. No third-party runtime dependencies.

```sh
python -m unittest discover -s tests -v
python tools/package_skill.py
python skills/amazingmarvin/scripts/marvin.py --help
```

Output: `dist/amazingmarvin-skill-offline.zip`. Live commands require MARVIN_API_TOKEN injected securely into the process environment; do not pass it in arguments or commit it. See [setup](skills/amazingmarvin/references/setup.md).

## Documents

- [Delivery report](REPORT.md)
- [Implementation and TDD evidence](DEVELOPMENT.md)
- [Implementation plan](IMPLEMENTATION_PLAN.md)
- [Feature coverage and future phases](FEATURE_COVERAGE.md)
- [Acceptance matrix](TEST_PLAN.md)
- [Research](RESEARCH.md) and [reuse decision](REUSE_DECISION.md)

Source: https://github.com/ianyp/amazingmarvin-skill (private). V1 release evidence remains in V1_REPORT.md; current delivery evidence is in V2_V3_REPORT.md.
