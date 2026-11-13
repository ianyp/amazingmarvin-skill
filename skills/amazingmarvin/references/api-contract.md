# API contract

Source: https://help.amazingmarvin.com/amazing-marvin/api-endpoints (reviewed 2026-11-13).

Base URL: https://serv.amazingmarvin.com/api/ . Requests use X-API-Token. Redirects and alternate origins are rejected. No system HTTP proxy is used. Responses are bounded to 2 MB. Errors omit server response bodies to avoid leaking credentials or task data.

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

Today/due results may contain items hidden by the app (backburner, future start date, dependencies, orphan parent). children returns open immediate children, not a recursive or completed inventory. markDone is experimental; scheduled tasks keep their existing day. Generic readback, full inventory and project completion are not part of this package.

JSON output: success `{ok:true, operation, data}`; failure `{ok:false, operation, error:{code,message,retryable,outcomeUnknown}}`. Exit status 0 for success, 1 for errors. Help is human-readable text. Recognized write receipts are "OK" or an object containing a nonempty _id; other successful HTTP payloads conservatively report unknown outcome pending live contract verification.
