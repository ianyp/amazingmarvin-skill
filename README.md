# Amazing Marvin OpenClaw skill

**Core offline build ready; not live-verified or installed.** 49 tests pass locally. No real account accessed.

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

The broader roadmap is not implemented. Live API tests, actual agent invocation and installation remain pending; no release tag or remote repository exists.
