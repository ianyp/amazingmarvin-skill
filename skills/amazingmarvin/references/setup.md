# Setup

Requires Linux, Python 3.11+ and system timezone data. Helpers use only the standard library. No package install, external service, background process or scheduler is needed.

Provide the limited-access API token as MARVIN_API_TOKEN in the helper process environment using the host's approved secret-injection mechanism. Do not place the token in shell command arguments, skill source or Git. Exact OpenClaw secret configuration is version-dependent and is not automated by this skill. No full-access token is used.

Run `python3 scripts/marvin.py --help` from this skill directory (or use its absolute path from another directory). A non-mutating credential check is `python3 scripts/marvin.py check-auth` (this still makes a network request). A normal read example is `python3 scripts/marvin.py today`. It contacts the public Marvin API, so don't use it as an offline setup check.

Rate-accounting timestamps live at `$XDG_STATE_HOME/openclaw-amazingmarvin/rate.json`, default `~/.local/state/openclaw-amazingmarvin/rate.json`. It contains no token or task data. Shared processes use a nonblocking file lock. Requests wait up to five seconds for spacing; cooldowns/budget exhaustion return errors rather than sleeping indefinitely. Do not delete the file to bypass throttling. Corrupt state fails closed.

Local rolling 24-hour ceiling: 1440 requests, spacing: three seconds. This cannot see other apps' shared Marvin API usage. HTTP 429 sets a shared cooldown of at least 60 seconds; integer and HTTP-date Retry-After values are respected. No automatic HTTP retries are currently implemented. Reissue reads deliberately after cooldown; never blindly repeat uncertain writes.

Install only after offline validation and authorized live verification. Copy the entire amazingmarvin directory to an approved OpenClaw skill directory; retain this repository as the source. This repository has not installed or enabled the skill.
