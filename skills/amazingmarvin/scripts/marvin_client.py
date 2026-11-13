"""Validated Marvin operations. Network transport is injected explicitly."""
from datetime import date
import math


class MarvinError(Exception):
    def __init__(self, message, *, code='invalid_input', outcome_unknown=False):
        super().__init__(message)
        self.code = code
        self.outcome_unknown = outcome_unknown


def valid_date(value):
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError:
        raise MarvinError('Date must be a valid YYYY-MM-DD') from None
    return value


class Client:
    def __init__(self, token, *, transport):
        if not isinstance(token, str) or not token.strip() or any(ord(c) < 32 or ord(c) == 127 for c in token):
            raise MarvinError('Configure MARVIN_API_TOKEN', code='missing_credentials')
        self._token = token
        self._transport = transport

    def _call(self, method, path, body=None, *, literal=False, array=False):
        headers = {'X-API-Token': self._token}
        if literal:
            headers['X-Auto-Complete'] = 'false'
        try:
            result = self._transport(method, path, headers, body)
        except MarvinError:
            raise
        except Exception:
            raise MarvinError('Request failed; verify remote state before repeating a write',
                              code='transport_error', outcome_unknown=method != 'GET') from None
        if isinstance(result, dict) and result.get('error'):
            raise MarvinError('Marvin returned an API error', code='api_error')
        if array and (not isinstance(result, list) or any(not isinstance(item, dict) for item in result)):
            raise MarvinError('Unexpected API response', code='invalid_response')
        if method != 'GET' and not (result == 'OK' or isinstance(result, dict) and isinstance(result.get('_id'), str) and result['_id']):
            raise MarvinError('Unrecognized write receipt; verify remote state', code='invalid_response', outcome_unknown=True)
        return result

    def today(self, day):
        return self._call('GET', 'todayItems?date=' + valid_date(day), array=True)

    def due(self, day):
        return self._call('GET', 'dueItems?by=' + valid_date(day), array=True)

    def add(self, fields):
        allowed = {'title', 'day', 'dueDate', 'estimateMinutes', 'parentId', 'labelIds', 'note'}
        if not isinstance(fields, dict) or set(fields) - allowed:
            raise MarvinError('Unsupported task fields')
        title = fields.get('title')
        if not isinstance(title, str) or not title.strip():
            raise MarvinError('Task title is required')
        body = dict(fields)
        for key in ('day', 'dueDate'):
            if key in body:
                valid_date(body[key])
        for key in ('parentId', 'note'):
            if key in body and not isinstance(body[key], str):
                raise MarvinError('Invalid text field')
        if 'labelIds' in body and (not isinstance(body['labelIds'], list) or
                any(not isinstance(x, str) or not x for x in body['labelIds'])):
            raise MarvinError('labelIds must be a list of nonempty IDs')
        if 'estimateMinutes' in body:
            minutes = body.pop('estimateMinutes')
            if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or minutes < 0 or minutes > 9007199254740991 / 60000 or not math.isfinite(minutes):
                raise MarvinError('Estimate must be finite nonnegative minutes')
            body['timeEstimate'] = round(minutes * 60000)
        return self._call('POST', 'addTask', body, literal=True)

    def check_auth(self):
        return self._call('POST', 'test')

    def categories(self):
        return self._call('GET', 'categories', array=True)

    def labels(self):
        return self._call('GET', 'labels', array=True)

    def children(self, parent_id):
        from urllib.parse import urlencode
        if not isinstance(parent_id, str) or not parent_id.strip():
            raise MarvinError('Parent ID required')
        return self._call('GET', 'children?' + urlencode({'parentId': parent_id}), array=True)

    def done(self, item_id, *, offset):
        if not isinstance(item_id, str) or not item_id.strip():
            raise MarvinError('Task ID required')
        if isinstance(offset, bool) or not isinstance(offset, int) or not -840 <= offset <= 840:
            raise MarvinError('Invalid timezone offset')
        return self._call('POST', 'markDone', {'itemId': item_id, 'timeZoneOffset': offset})

    @staticmethod
    def resolve_task(items, query):
        matches = [item for item in items if isinstance(item, dict) and
                   (item.get('_id') == query or item.get('title') == query)]
        if len(matches) != 1 or matches[0].get('db') != 'Tasks' or not matches[0].get('_id'):
            raise MarvinError('Choose one unambiguous task ID', code='ambiguous_target')
        return matches[0]['_id']
