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
        except Exception:
            raise MarvinError('Request failed; verify remote state before repeating a write',
                              code='transport_error', outcome_unknown=method != 'GET') from None
        if isinstance(result, dict) and result.get('error'):
            raise MarvinError('Marvin returned an API error', code='api_error')
        if array and not isinstance(result, list):
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
            if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or not math.isfinite(minutes) or minutes < 0:
                raise MarvinError('Estimate must be finite nonnegative minutes')
            body['timeEstimate'] = round(minutes * 60000)
        return self._call('POST', 'addTask', body, literal=True)
