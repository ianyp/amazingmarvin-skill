#!/usr/bin/env python3
"""On-demand Marvin CLI. Credentials come from environment, never arguments."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from marvin_client import Client, MarvinError
from marvin_rate import RateLimiter
from marvin_transport import Transport


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise MarvinError('Invalid arguments; run --help')


def main(argv=None):
    operation = 'unknown'
    try:
        parser = Parser(description=__doc__)
        parser.add_argument('--timezone', default='Europe/London')
        subs = parser.add_subparsers(dest='command', required=True)
        subs.add_parser('today').add_argument('--date')
        subs.add_parser('due').add_argument('--by')
        subs.add_parser('check-auth')
        subs.add_parser('categories')
        subs.add_parser('labels')
        subs.add_parser('children').add_argument('--parent-id', required=True)
        subs.add_parser('add').add_argument('--input-json', required=True, help='JSON file, or - for stdin')
        subs.add_parser('done').add_argument('--id', required=True, help='Known task ID; projects are not supported')
        args = parser.parse_args(argv)
        operation = args.command
        now = datetime.now(ZoneInfo(args.timezone))
        state_root = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state')))
        limiter = RateLimiter(state_root / 'openclaw-amazingmarvin/rate.json')
        transport = Transport(reserve=limiter.reserve, defer=limiter.defer)
        client = Client(os.environ.get('MARVIN_API_TOKEN', ''), transport=transport)
        if operation == 'today':
            data = client.today(args.date or now.date().isoformat())
        elif operation == 'due':
            data = client.due(args.by or now.date().isoformat())
        elif operation == 'check-auth': data = client.check_auth()
        elif operation == 'categories': data = client.categories()
        elif operation == 'labels': data = client.labels()
        elif operation == 'children': data = client.children(args.parent_id)
        elif operation == 'done': data = client.done(args.id, offset=int(now.utcoffset().total_seconds() / 60))
        else:
            if args.input_json == '-':
                text = sys.stdin.read(65537)
            else:
                with open(args.input_json, encoding='utf-8') as file: text = file.read(65537)
            if len(text) > 65536: raise MarvinError('Input exceeds size limit')
            data = client.add(json.loads(text))
        print(json.dumps({'ok': True, 'operation': operation, 'data': data}, ensure_ascii=False, allow_nan=False))
        return 0
    except MarvinError as error:
        result = {'code': error.code, 'message': str(error), 'retryable': error.code in ('rate_busy', 'rate_cooldown', 'http_429'), 'outcomeUnknown': error.outcome_unknown}
    except (OSError, ValueError, ZoneInfoNotFoundError):
        result = {'code': 'invalid_input', 'message': 'Cannot read input or configuration; check JSON, paths and timezone', 'retryable': False, 'outcomeUnknown': False}
    print(json.dumps({'ok': False, 'operation': operation, 'error': result}))
    return 1


if __name__ == '__main__':
    sys.exit(main())
