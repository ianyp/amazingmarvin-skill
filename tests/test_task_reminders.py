import copy
import unittest
from test_client import Client,MarvinError

class TaskReminderTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.fail=False;self.drop=False;self.keep=False
        self.other={'reminderId':'other','time':1800000000,'extra':'preserve'}
        self.doc={'_id':'t','_rev':'1','db':'Tasks','day':'unassigned','title':'test','reminders':[self.other.copy()]}
        self.rows=[]
        self.c=Client('fake',transport=self.transport,full_access=True)
    def transport(self,m,p,h,b):
        self.calls.append((m,p,h,b))
        if p.startswith('doc?'):return copy.deepcopy(self.doc)
        if p=='reminders':return copy.deepcopy(self.rows)
        if p=='reminder/set' and not self.drop:
            row=copy.deepcopy(b['reminders'][0]);self.rows=[r for r in self.rows if r['reminderId']!=row['reminderId']]+[row]
        if p=='reminder/delete' and not self.keep:self.rows=[r for r in self.rows if r['reminderId'] not in b['reminderIds']]
        if p=='doc/update':
            if self.fail:raise MarvinError('failed',code='http_500',outcome_unknown=True)
            for f in b['setters']:
                if f['key']=='reminders':self.doc['reminders']=copy.deepcopy(f['val'])
            self.doc['_rev']=str(int(self.doc['_rev'])+1)
            return {'_id':'t'}
        return 'OK'
    def set(self,at='2026-11-18T10:00:00Z'):
        return self.c.set_task_reminder('t',at,reminder_id='r')
    def count(self,path):return len([c for c in self.calls if c[1]==path])
    def test_create_preserves_metadata_and_day(self):
        result=self.set()
        self.assertTrue(result['serverVerified']);self.assertTrue(result['metadataVerified'])
        self.assertEqual(self.rows[0]['type'],'M');self.assertEqual(self.rows[0]['taskId'],'t')
        self.assertEqual(self.rows[0]['reminderId'],'r');self.assertEqual(self.doc['reminders'][0],self.other)
        self.assertEqual(self.doc['reminders'][1],{'reminderId':'r','time':self.rows[0]['time']})
        self.assertEqual(self.doc['day'],'unassigned');self.assertNotIn('taskTime',self.doc)
    def test_update_without_duplicates(self):
        self.set();self.set('2026-11-19T10:00:00Z')
        self.assertEqual(len(self.rows),1);self.assertEqual(len(self.doc['reminders']),2)
        self.assertEqual(self.doc['reminders'][1]['time'],self.rows[0]['time'])
    def test_timezone_required(self):
        with self.assertRaises(MarvinError):self.set('2026-11-18T10:00:00')
        self.assertEqual(self.calls,[])
    def test_minimal_no_network(self):
        self.c.full_access=False
        with self.assertRaises(MarvinError):self.set()
        self.assertEqual(self.calls,[])
    def test_collisions_no_writes(self):
        for row in ({'reminderId':'r','type':'M'},{'reminderId':'r','type':'M','taskId':'else'},{'reminderId':'r','type':'T','taskId':'t'}):
            self.rows=[row]
            with self.assertRaises(MarvinError):self.set()
        self.assertFalse(any(c[0]=='POST' for c in self.calls))
    def test_bad_metadata_no_write(self):
        self.doc['reminders']={}
        with self.assertRaises(MarvinError):self.set()
        self.assertFalse(any(c[0]=='POST' for c in self.calls))
    def test_missing_retention_no_metadata_write(self):
        self.drop=True
        with self.assertRaises(MarvinError) as e:self.set()
        self.assertEqual(e.exception.code,'partial_success');self.assertEqual(self.count('doc/update'),0)
    def test_partial_set_reconcile_no_replay(self):
        self.fail=True
        with self.assertRaises(MarvinError) as e:self.set()
        self.assertEqual(e.exception.code,'partial_success')
        self.fail=False;self.c.reconcile_task_reminder('t',reminder_id='r')
        self.assertEqual(self.count('reminder/set'),1);self.assertEqual(len(self.doc['reminders']),2)
    def test_delete_preserves_other(self):
        self.set();self.c.delete_task_reminder('t',reminder_id='r')
        self.assertEqual(self.rows,[]);self.assertEqual(self.doc['reminders'],[self.other])
    def test_retained_delete_no_metadata_clear(self):
        self.set();self.keep=True
        with self.assertRaises(MarvinError):self.c.delete_task_reminder('t',reminder_id='r')
        self.assertEqual(len(self.doc['reminders']),2)
    def test_standalone_delete_rejects_linked_m(self):
        self.set()
        with self.assertRaises(MarvinError):self.c.delete_reminder('r')
        self.assertEqual(self.count('reminder/delete'),0)
    def test_reconcile_deleted_refuses_live(self):
        self.set()
        with self.assertRaises(MarvinError):self.c.reconcile_task_reminder('t',reminder_id='r',deleted=True)
    def test_partial_delete_reconcile_no_replay(self):
        self.set();self.fail=True
        with self.assertRaises(MarvinError):self.c.delete_task_reminder('t',reminder_id='r')
        self.fail=False;self.c.reconcile_task_reminder('t',reminder_id='r',deleted=True)
        self.assertEqual(self.count('reminder/delete'),1);self.assertEqual(self.doc['reminders'],[self.other])
    def test_read_failure_no_replay(self):
        original=self.transport
        def fail(m,p,h,b):
            if p=='reminders' and self.rows:raise MarvinError('bad',code='http_500')
            return original(m,p,h,b)
        self.c._transport=fail
        with self.assertRaises(MarvinError):self.set()
        self.assertEqual(self.count('reminder/set'),1);self.assertEqual(self.count('doc/update'),0)
    def test_metadata_readback_required(self):
        original=self.transport
        self.c._transport=lambda m,p,h,b: {'_id':'t'} if p=='doc/update' else original(m,p,h,b)
        with self.assertRaises(MarvinError) as e:self.set()
        self.assertEqual(e.exception.code,'partial_success')
    def test_task_id_not_reminder_id(self):
        with self.assertRaises(MarvinError):self.c.set_task_reminder('t','2026-11-18T10:00:00Z',reminder_id='t')
        self.assertEqual(self.calls,[])
    def test_concurrent_revision_detected(self):
        original=self.transport;reads=0
        def changing(m,p,h,b):
            nonlocal reads
            result=original(m,p,h,b)
            if p.startswith('doc?'):
                reads+=1
                if reads==3:result['_rev']='changed'
            return result
        self.c._transport=changing
        with self.assertRaises(MarvinError) as e:self.set()
        self.assertEqual(e.exception.code,'partial_success');self.assertEqual(self.count('doc/update'),0)
    def test_cli_roundtrip_and_explicit_ids(self):
        import contextlib,io,json,os
        from unittest.mock import patch
        import marvin
        commands=[['task-reminder-set','--id','t','--reminder-id','r','--at','2026-11-18T10:00:00Z'],
                  ['reminder-reconcile','--id','t','--reminder-id','r'],
                  ['task-reminder-delete','--id','t','--reminder-id','r'],
                  ['reminder-reconcile','--id','t','--reminder-id','r','--deleted']]
        for command in commands:
            out=io.StringIO()
            with patch.dict(os.environ,{'MARVIN_API_TOKEN':'fake'}),patch.object(marvin,'Transport',return_value=self.transport),contextlib.redirect_stdout(out):
                status=marvin.main(['--full-access']+command)
            self.assertEqual(status,0,out.getvalue());self.assertTrue(json.loads(out.getvalue())['ok'])
        self.assertEqual(self.rows,[]);self.assertEqual(self.doc['reminders'],[self.other])
