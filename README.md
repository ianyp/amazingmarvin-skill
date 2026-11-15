# Amazing Marvin OpenClaw skill

**V1 implemented, live-verified and installed in the OpenClaw workspace.** 56 offline tests pass. Protected-secret reads and synthetic task creation/completion verified. See [V1 report](V1_REPORT.md).

## Implemented

Today/due lists, category/label lookup, immediate project children, task capture, known-ID task completion and credential check. JSON CLI, limited-token authentication, rate accounting and uncertain-write protection.

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

The broader roadmap is not implemented. Source: https://github.com/ianyp/amazingmarvin-skill (private). Release: v0.1.0. The current conversation skill snapshot predates installation; CLI discovery and installed-helper execution are verified.
