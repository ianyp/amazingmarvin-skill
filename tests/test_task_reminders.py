import unittest
from test_client import Client,MarvinError

class TaskReminderTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.fail=False
        self.c=Client('fake',transport=self.transport,full_access=True)
        self.c._task_reminders_verified=True  # staged adapter only; live gate remains closed
    def transport(self,m,p,h,b):
        self.calls.append((m,p,h,b))
        if p.startswith('doc?'):return {'_id':'t','db':'Tasks','day':'2026-11-17','title':'test'}
        if p=='reminders':return [{'reminderId':'t','type':'T'}]
        if p=='doc/update':
            if self.fail:raise MarvinError('failed',code='http_500',outcome_unknown=True)
            return {'_id':'t'}
        return 'OK'
    def test_schedule_and_metadata(self):
        self.c.set_task_reminder('t','2026-11-17T10:00:00+00:00',offset=5)
        req=[a for a in self.calls if a[1]=='reminder/set'][0][3]['reminders'][0]
        self.assertEqual(req['type'],'T');self.assertEqual(req['reminderId'],'t')
        values={s['key']:s['val'] for s in self.calls[-1][3]['setters']}
        self.assertEqual(values['taskTime'],'10:00');self.assertEqual(values['reminderOffset'],5)
        self.assertEqual(values['reminderTime'],str(req['time']-300))
    def test_schedule_day_must_match(self):
        with self.assertRaises(MarvinError):self.c.set_task_reminder('t','2026-11-18T10:00:00Z')
        self.assertFalse(any(a[0]=='POST' for a in self.calls))
    def test_partial_metadata_failure(self):
        self.fail=True
        with self.assertRaises(MarvinError) as ctx:self.c.set_task_reminder('t','2026-11-17T10:00:00Z')
        self.assertEqual(ctx.exception.code,'partial_success')
        self.assertEqual(len([a for a in self.calls if a[1]=='reminder/set']),1)
    def test_task_reminder_delete(self):
        self.c.delete_task_reminder('t')
        self.assertEqual([a[1] for a in self.calls if a[0]=='POST'],['reminder/delete','doc/update'])
    def test_reconcile_only_updates_metadata(self):
        original=self.transport
        self.c._transport=lambda m,p,h,b: [] if p=='reminders' else original(m,p,h,b)
        self.c.reconcile_task_reminder('t',deleted=True)
        self.assertFalse(any(a[1]=='reminder/delete' for a in self.calls))

    def test_production_gate_prevents_any_network_action(self):
        self.c._task_reminders_verified=False
        with self.assertRaises(MarvinError) as ctx:self.c.set_task_reminder('t','2026-11-17T10:00:00Z')
        self.assertEqual(ctx.exception.code,'unsupported_capability')
        self.assertEqual(self.calls,[])
