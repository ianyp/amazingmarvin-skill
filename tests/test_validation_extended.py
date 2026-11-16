import unittest
from test_client import Client,MarvinError

class ValidationExtended(unittest.TestCase):
    def setUp(self):self.calls=[]
    def client(self,reply):
        def transport(*a):self.calls.append(a);return reply(*a) if callable(reply) else reply
        return Client('fake',transport=transport,full_access=True)
    def test_auth_rejects_bad_receipt(self):
        with self.assertRaises(MarvinError):self.client([]).check_auth()
    def test_create_task_planning_fields(self):
        c=self.client({'_id':'t'})
        c.add({'title':'x','plannedWeek':'2026-11-16','backburner':True})
        self.assertEqual(self.calls[-1][3]['plannedWeek'],'2026-11-16')
    def test_project_validates_parent_before_write(self):
        c=self.client({'_id':'parent','db':'Tasks'})
        with self.assertRaises(MarvinError):c.project({'title':'x','parentId':'parent'})
        self.assertFalse(any(a[0]=='POST' for a in self.calls))
    def test_exclusive_labels(self):
        def reply(m,p,h,b):
            if p=='labels':return [{'_id':'a','groupId':'g'},{'_id':'b','groupId':'g'}]
            return {'_id':'strategySettings.labelSettings.groups','val':{'g':{'isExclusive':True}}}
        c=self.client(reply)
        with self.assertRaises(MarvinError):c._references({'labelIds':['a','b']})
        self.assertFalse(any(a[0]=='POST' for a in self.calls))
    def test_unknown_parent_cycle(self):
        c=self.client({'_id':'p','db':'Categories','parentId':'p'})
        with self.assertRaises(MarvinError):c._references({'parentId':'p'})
    def test_write_object_response_unknown(self):
        c=self.client([])
        with self.assertRaises(MarvinError) as ctx:c.record_habit('h',1,time_ms=123)
        self.assertTrue(ctx.exception.outcome_unknown)
    def test_no_retry_ambiguous_subtask_write(self):
        def reply(m,p,h,b):
            if m=='GET':return {'_id':'t','db':'Tasks'}
            raise OSError('synthetic secret')
        c=self.client(reply)
        with self.assertRaises(MarvinError) as ctx:c.add_subtasks('t',['x'])
        self.assertTrue(ctx.exception.outcome_unknown)
        self.assertEqual(len([a for a in self.calls if a[0]=='POST']),1)
        self.assertNotIn('synthetic secret',str(ctx.exception))
