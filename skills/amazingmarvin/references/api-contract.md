# API contract

Source: https://help.amazingmarvin.com/amazing-marvin/api-endpoints (reviewed 2026-11-16).

Base URL: https://serv.amazingmarvin.com/api/ . Requests use X-API-Token, or X-Full-Access-Token with explicit --full-access. Redirects and alternate origins are rejected. Ordinary tokens do not use system proxies. OpenClaw protected sentinels require the Gateway-injected authenticated loopback HTTPS proxy and CA bundle; bypass and direct fallback are disabled. Responses are bounded to 2 MB. Errors omit server response bodies to avoid leaking credentials or task data.

| Command | Endpoint |
| --- | --- |
| check-auth | POST test (credential check; no task change) |
| today | GET todayItems?date=YYYY-MM-DD |
| due | GET dueItems?by=YYYY-MM-DD |
| categories | GET categories |
| labels | GET labels |
| children | GET children?parentId=ID |
| add | POST addTask, X-Auto-Complete=false |
| done | POST markDone, itemId and timeZoneOffset |

Estimate minutes convert to milliseconds. Completion offset is local UTC offset in minutes, not JavaScript getTimezoneOffset's opposite sign. Creation uses explicit dates and disabled shortcuts, avoiding server-relative date parsing.

Today/due results may contain items hidden by the app (backburner, future start date, dependencies, orphan parent). children returns open immediate children, not a recursive or completed inventory. markDone is experimental; scheduled tasks keep their existing day. Task/project readback is supported; full inventory and project completion/reopening are not.

JSON output: success `{ok:true, operation, data}`; failure `{ok:false, operation, error:{code,message,retryable,outcomeUnknown}}`. Exit status 0 for success, 1 for errors. Help is human-readable text. Recognized write receipts are "OK" or an object containing a nonempty _id; Endpoint-specific object receipts are accepted for track, updateHabit and rewards; read-only POST tracks/downloadAttachment never imply an uncertain mutation. Other unexpected write receipts report unknown outcome.

## Expanded workflows

See [workflows](workflows.md) for phases 2/3 endpoints and recovery contracts. Live corrections: trackedItem returns empty HTTP 204 when idle; reminders can return null; track issues can be null. The data-type docs specify reminder seconds and server readback echoes seconds; an endpoint example uses milliseconds. Delivery timing remains unverified, and task-linked reminders failed live retention and are gated. Notebook/page and attachment routes are in current help docs but absent from the older OpenAPI file. No API token is forwarded to attachment storage.
