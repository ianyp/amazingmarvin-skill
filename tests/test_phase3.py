import unittest
from test_client import Client, MarvinError

class RichTests(unittest.TestCase):
    def setUp(self):
        self.calls=[]; self.doc={'_id':'t','_rev':'1','db':'Tasks','title':'Old','note':'keep','subtasks':{'old':{'_id':'old','title':'Keep','rank':1,'done':False}}}
        self.c=Client('fake',transport=self.transport,full_access=True)
    def transport(self,m,p,h,b):
        self.calls.append((m,p,h,b))
        if p.startswith('doc?'): return dict(self.doc)
        if p=='doc/update': return dict(self.doc, _rev='2')
        if p=='labels': return [{'_id':'label','groupId':'g'}]
        if p=='habits?raw=1': return []
        return []
    def test_edit_preserves_fields(self):
        self.c.edit('t',{'title':'New'})
        setters=self.calls[-1][3]['setters']; values={x['key']:x['val'] for x in setters}
        self.assertEqual(values['title'],'New'); self.assertNotIn('note',values)
        self.assertIn('fieldUpdates.title',values); self.assertIn('updatedAt',values)
    def test_reject_arbitrary_fields_before_write(self):
        for fields in [{'done':True},{'deletedAt':1},{'db':'ProfileItems'},{'subtasks':{}},{'duration':30}]:
            with self.assertRaises(MarvinError): self.c.edit('t',fields)
        self.assertFalse(any(c[0]=='POST' for c in self.calls))
    def test_reject_category_edit(self):
        self.doc['db']='Categories'; self.doc['type']='category'
        with self.assertRaises(MarvinError): self.c.edit('t',{'dueDate':'2026-12-01'})
    def test_expected_revision(self):
        with self.assertRaises(MarvinError) as ctx: self.c.edit('t',{'title':'x'},expected_rev='other')
        self.assertEqual(ctx.exception.code,'conflict')
        self.assertFalse(any(c[0]=='POST' for c in self.calls))
    def test_subtasks_append_not_replace(self):
        self.c.add_subtasks('t',['New one','New two'])
        keys=[v['key'] for v in self.calls[-1][3]['setters']]
        self.assertEqual(len([k for k in keys if k.startswith('subtasks.')]),2)
        self.assertNotIn('subtasks',keys); self.assertNotIn('subtasks.old',keys)
        subs=[v['val'] for v in self.calls[-1][3]['setters'] if v['key'].startswith('subtasks.')]
        self.assertEqual([v['rank'] for v in subs],[2,3])
        self.assertEqual([v['title'] for v in subs],['New one','New two'])
    def test_subtasks_task_only(self):
        self.doc.update(db='Categories',type='project')
        with self.assertRaises(MarvinError): self.c.add_subtasks('t',['x'])
    def test_subtask_invalid_no_call(self):
        for v in [[],[''],[{}],'text']:
            with self.assertRaises(MarvinError): self.c.add_subtasks('t',v)
        self.assertEqual(self.calls,[])
    def test_habit_whole_values(self):
        with self.assertRaises(MarvinError): self.c.record_habit('h',1.5,time_ms=1)
        self.assertEqual(self.calls,[])
    def test_habit_no_history_replacement(self):
        with self.assertRaises(TypeError): self.c.record_habit('h',history=[])
    def test_event_timezone_required(self):
        with self.assertRaises(MarvinError): self.c.event({'title':'x','start':'2026-11-16T12:00','length':1000})
        self.assertEqual(self.calls,[])
    def test_event_request(self):
        self.c._transport=lambda *a:self.calls.append(a) or {'_id':'e'}
        self.c.event({'title':'x','start':'2026-11-16T12:00:00Z','length':1000})
        self.assertEqual(self.calls[-1][1],'addEvent')
    def test_reward_bad_inputs(self):
        for op,kwargs in [('claim',{'points':-1,'item_id':'t'}),('unclaim',{'item_id':'MANUAL'}),('reset',{})]:
            with self.assertRaises(MarvinError): self.c.reward(op,'2026-11-16',**kwargs)
        self.assertEqual(self.calls,[])
    def test_notebook_requires_one_selector(self):
        with self.assertRaises(MarvinError): self.c.notebook()
        with self.assertRaises(MarvinError): self.c.notebook(item_id='n',parent_id='p')
    def test_full_permission_before_reads(self):
        self.c.full_access=False
        for fn in [lambda:self.c.edit('t',{'title':'x'}),lambda:self.c.add_subtasks('t',['x']),lambda:self.c.notebooks(),lambda:self.c.reminders()]:
            with self.assertRaises(MarvinError): fn()
        self.assertEqual(self.calls,[])

    def test_empty_reminder_null(self):
        self.c._transport=lambda *args:None
        self.assertEqual(self.c.reminders(),[])
