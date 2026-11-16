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
        parser.add_argument('--full-access', action='store_true', help='Use full-access token header; never inferred from token')
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
        for name in ('completed','blocks'):
            subs.add_parser(name).add_argument('--date')
        for name in ('goals','kudos','account','tracked','notebooks','reminders'):
            subs.add_parser(name)
        subs.add_parser('habits').add_argument('--raw',action='store_true')
        for name in ('habit','item','page','reconcile-tracking','reminder-delete'):
            subs.add_parser(name).add_argument('--id',required=True)
        for name in ('project','event','reminder-set'):
            subs.add_parser(name).add_argument('--input-json',required=True)
        for name in ('edit','subtasks-add'):
            sub=subs.add_parser(name); sub.add_argument('--id',required=True); sub.add_argument('--input-json',required=True)
            if name=='edit': sub.add_argument('--expected-rev')
        sub=subs.add_parser('tracks');group=sub.add_mutually_exclusive_group(required=True)
        group.add_argument('--date');group.add_argument('--ids',nargs='+')
        sub=subs.add_parser('track');sub.add_argument('--id',required=True);sub.add_argument('--action',required=True,choices=['START','STOP'])
        sub=subs.add_parser('habit-record');sub.add_argument('--id',required=True);sub.add_argument('--value',type=int,required=True);sub.add_argument('--time-ms',type=int)
        subs.add_parser('habit-undo').add_argument('--id',required=True)
        sub=subs.add_parser('notebook');group=sub.add_mutually_exclusive_group(required=True);group.add_argument('--id');group.add_argument('--parent-id')
        sub=subs.add_parser('reward');sub.add_argument('--action',required=True,choices=['claim','unclaim','spend']);sub.add_argument('--date');sub.add_argument('--id');sub.add_argument('--points',type=float)
        sub=subs.add_parser('download');sub.add_argument('--id',required=True);sub.add_argument('--uid',required=True);sub.add_argument('--output',required=True)
        sub=subs.add_parser('task-reminder-set');sub.add_argument('--id',required=True);sub.add_argument('--at',required=True);sub.add_argument('--offset',type=int,default=0)
        subs.add_parser('task-reminder-delete').add_argument('--id',required=True)
        sub=subs.add_parser('reminder-reconcile');sub.add_argument('--id',required=True);sub.add_argument('--deleted',action='store_true')
        args = parser.parse_args(argv)
        operation = args.command
        now = datetime.now(ZoneInfo(args.timezone))
        state_root = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state')))
        limiter = RateLimiter(state_root / 'openclaw-amazingmarvin/rate.json')
        transport = Transport(reserve=limiter.reserve, defer=limiter.defer)
        client = Client(os.environ.get('MARVIN_API_TOKEN', ''), transport=transport, full_access=args.full_access)
        if operation == 'today':
            data = client.today(args.date or now.date().isoformat())
        elif operation == 'due':
            data = client.due(args.by or now.date().isoformat())
        elif operation == 'check-auth': data = client.check_auth()
        elif operation == 'categories': data = client.categories()
        elif operation == 'labels': data = client.labels()
        elif operation == 'children': data = client.children(args.parent_id)
        elif operation == 'done': data = client.done(args.id, offset=int(now.utcoffset().total_seconds() / 60))
        elif operation in ('completed','blocks'): data=getattr(client,operation)(args.date or now.date().isoformat())
        elif operation in ('goals','kudos','account','tracked','notebooks','reminders'): data=getattr(client,operation)()
        elif operation=='habits': data=client.habits(raw=args.raw)
        elif operation=='habit': data=client.habit(args.id)
        elif operation=='item': data=client._item(args.id)
        elif operation=='page': data=client.page(args.id)
        elif operation=='tracks':
            if args.date:
                from datetime import datetime as DateTime
                target=DateTime.fromisoformat(args.date+'T12:00:00').replace(tzinfo=ZoneInfo(args.timezone))
                data=client.tracks(day=args.date,offset=int(target.utcoffset().total_seconds()/60))
            else: data=client.tracks(args.ids)
        elif operation=='track': data=client.track(args.id,args.action)
        elif operation=='reconcile-tracking': data=client.reconcile_tracking(args.id)
        elif operation=='habit-record': data=client.record_habit(args.id,args.value,time_ms=args.time_ms if args.time_ms is not None else int(now.timestamp()*1000))
        elif operation=='habit-undo': data=client.record_habit(args.id,undo=True)
        elif operation=='notebook': data=client.notebook(item_id=args.id,parent_id=args.parent_id)
        elif operation=='reward': data=client.reward(args.action,args.date or now.date().isoformat(),item_id=args.id,points=args.points)
        elif operation=='reminder-delete': data=client.delete_reminder(args.id)
        elif operation=='task-reminder-set': data=client.set_task_reminder(args.id,args.at,offset=args.offset)
        elif operation=='task-reminder-delete': data=client.delete_task_reminder(args.id)
        elif operation=='reminder-reconcile': data=client.reconcile_task_reminder(args.id,deleted=args.deleted,timezone=args.timezone)
        elif operation=='download': data=client.download_attachment(args.id,args.uid,args.output)
        else:
            if args.input_json == '-':
                text = sys.stdin.read(65537)
            else:
                with open(args.input_json, encoding='utf-8') as file: text = file.read(65537)
            if len(text) > 65536: raise MarvinError('Input exceeds size limit')
            fields=json.loads(text)
            if operation=='add': data=client.add(fields)
            elif operation=='project': data=client.project(fields)
            elif operation=='event': data=client.event(fields)
            elif operation=='edit': data=client.edit(args.id,fields,expected_rev=args.expected_rev)
            elif operation=='subtasks-add': data=client.add_subtasks(args.id,fields)
            elif operation=='reminder-set': data=client.set_reminder(fields)
            else: raise MarvinError('Unsupported operation')
        print(json.dumps({'ok': True, 'operation': operation, 'data': data}, ensure_ascii=False, allow_nan=False))
        return 0
    except MarvinError as error:
        result = {'code': error.code, 'message': str(error), 'retryable': error.code in ('rate_busy', 'rate_cooldown', 'http_429'), 'outcomeUnknown': error.outcome_unknown}
        if error.details is not None: result["details"]=error.details
    except (OSError, ValueError, ZoneInfoNotFoundError):
        result = {'code': 'invalid_input', 'message': 'Cannot read input or configuration; check JSON, paths and timezone', 'retryable': False, 'outcomeUnknown': False}
    print(json.dumps({'ok': False, 'operation': operation, 'error': result}))
    return 1


if __name__ == '__main__':
    sys.exit(main())
