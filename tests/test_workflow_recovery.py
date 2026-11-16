import unittest
from test_client import Client, MarvinError

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.fail=False
        self.c=Client('fake',transport=self.transport,full_access=True)
    def transport(self,m,p,h,b):
        self.calls.append((m,p,h,b))
        if p.startswith('doc?'): return {'_id':p.split('=')[1],'db':'Tasks','_rev':'1','title':'test'}
        if p=='trackedItem': return None
        if p=='track': return {'startId':'a','startTimes':[10],'stopId':'b','stopTimes':[1,5,7,9],'issues':[]}
        if p=='tracks': return [{'taskId':'b','times':[1,5,7,9]}]
        if p=='doc/update':
            if self.fail: raise MarvinError('network',code='transport_error',outcome_unknown=True)
            return {'_id':b['itemId']}
        if p in ('reminder/set','reminder/delete'): return 'OK'
        if p=='reminders': return [{'reminderId':'r','type':'M'}]
        return []
    def test_timer_updates_stopped_id(self):
        result=self.c.track('a','START')
        writes=[c for c in self.calls if c[1]=='doc/update']
        self.assertEqual(writes[0][3]['itemId'],'b')
        values={v['key']:v['val'] for v in writes[0][3]['setters']}
        self.assertEqual(values['duration'],6)
        self.assertTrue(result['cacheUpdated'])
    def test_timer_partial_not_replayed(self):
        self.fail=True
        with self.assertRaises(MarvinError) as ctx:self.c.track('a','START')
        self.assertEqual(ctx.exception.code,'partial_success')
        self.assertEqual(ctx.exception.details['stoppedTaskId'],'b')
        self.assertEqual(len([c for c in self.calls if c[1]=='track']),1)
    def test_timer_invalid_interval_blocks_cache(self):
        with self.assertRaises(MarvinError):self.c._duration([10,5])
        with self.assertRaises(MarvinError):self.c._duration([1,2,3])
    def test_reconcile_does_not_toggle_timer(self):
        self.c.reconcile_tracking('b')
        self.assertFalse(any(c[1]=='track' for c in self.calls))
    def test_manual_reminder_not_task_metadata(self):
        self.c.set_reminder({'reminderId':'r','time':1800000000,'title':'test','type':'M','offset':0,'snooze':0,'autoSnooze':False,'canTrack':False})
        self.assertEqual(self.calls[-1][1],'reminder/set')
        self.assertFalse(any(c[1]=='doc/update' for c in self.calls))
    def test_millisecond_reminder_rejected(self):
        with self.assertRaises(MarvinError):self.c.set_reminder({'reminderId':'r','time':1800000000000,'title':'test','type':'M'})
        self.assertEqual(self.calls,[])
    def test_task_reminder_requires_task_id_and_safe_type(self):
        with self.assertRaises(MarvinError):self.c.set_reminder({'reminderId':'r','time':1800000000,'title':'x','type':'T'})
    def test_delete_manual_known_only(self):
        self.c.delete_reminder('r')
        self.assertEqual(self.calls[-1][3],{'reminderIds':['r']})
        with self.assertRaises(MarvinError):self.c.delete_reminder('missing')
    def test_full_capability_required_before_timer_changes(self):
        self.c.full_access=False
        with self.assertRaises(MarvinError):self.c.track('a','START')
        self.assertEqual(self.calls,[])

    def test_timer_null_issues_is_empty(self):
        original=self.transport
        def transport(m,p,h,b):
            if p=='track':return {'startId':'a','startTimes':[1],'stopId':'','stopTimes':None,'issues':None}
            return original(m,p,h,b)
        self.c._transport=transport
        self.assertFalse(self.c.track('a','START')['cacheUpdated'])
