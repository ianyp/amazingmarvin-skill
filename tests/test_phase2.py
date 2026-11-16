import unittest
from test_client import Client, MarvinError

class Phase2Tests(unittest.TestCase):
    def setUp(self):
        self.calls=[]; self.reply=[]
        self.c=Client('fake', transport=self.transport, full_access=True)
    def transport(self,*a): self.calls.append(a); return self.reply
    def test_read_routes(self):
        for name,args,path in [('completed',('2026-11-16',),'doneItems?date=2026-11-16'),('blocks',('2026-11-16',),'todayTimeBlocks?date=2026-11-16'),('goals',(),'goals'),('habits',(),'habits')]:
            getattr(self.c,name)(*args); self.assertEqual(self.calls[-1][1],path)
    def test_tracks_read_post(self):
        self.c.tracks(['a']); self.assertEqual(self.calls[-1][3],{'taskIds':['a']})
    def test_tracks_date_offset(self):
        self.c.tracks(day='2026-07-01',offset=60)
        self.assertEqual(self.calls[-1][3],{'date':'2026-07-01','timeZone':-60})
    def test_tracks_invalid(self):
        for ids in [[],['a']*101,[''],[True]]:
            with self.assertRaises(MarvinError): self.c.tracks(ids)
        self.assertEqual(self.calls,[])
    def test_tracks_failure_not_unknown_write(self):
        self.c._transport=lambda *a: (_ for _ in ()).throw(OSError())
        with self.assertRaises(MarvinError) as ctx: self.c.tracks(['a'])
        self.assertFalse(ctx.exception.outcome_unknown)
    def test_project(self):
        self.reply={'_id':'p'}
        self.c.project({'title':'Literal #text','priority':'high','day':None})
        self.assertEqual(self.calls[-1][1],'addProject')
        self.assertEqual(self.calls[-1][2]['X-Auto-Complete'],'false')
    def test_bad_project(self):
        for fields in [{'title':'x','priority':'urgent'},{'title':'x','isStarred':3},{'title':'x','day':'bad'}]:
            with self.assertRaises(MarvinError): self.c.project(fields)
        self.assertEqual(self.calls,[])
    def test_summary_no_profile_leak(self):
        self.reply={'email':'private','password':'secret','kudos':12,'level':2}
        self.assertEqual(self.c.account(),{'kudos':12,'level':2})
    def test_raw_habits_permission(self):
        c=Client('fake',transport=self.transport)
        with self.assertRaises(MarvinError): c.habits(raw=True)
        self.assertEqual(self.calls,[])
    def test_malformed_read(self):
        self.reply={'unexpected':True}
        with self.assertRaises(MarvinError): self.c.goals()
