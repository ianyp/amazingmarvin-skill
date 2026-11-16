import unittest
from test_client import Client, MarvinError

class DateBoundaries(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.client = Client('synthetic', transport=self.transport)
    def transport(self, *args):
        self.calls.append(args)
        return {'_id': 'synthetic-task'}
    def test_task_dates_preserved_separately(self):
        fields = {'title': 'test', 'startDate': '2026-11-17',
                  'endDate': '2026-11-20', 'dueDate': '2026-11-19',
                  'day': '2026-11-18'}
        self.client.add(fields)
        self.assertEqual(self.calls[0][3], fields)
        self.assertIn('X-API-Token', self.calls[0][2])
    def test_each_boundary_independent(self):
        for key in ('startDate', 'endDate'):
            with self.subTest(key=key):
                self.client.add({'title': 'test', key: '2028-02-29'})
                self.assertEqual(self.calls[-1][3][key], '2028-02-29')
    def test_bad_dates_never_write(self):
        for key in ('startDate', 'endDate'):
            for value in ('2026-02-29', 'tomorrow', '2026-1-01', 123, True, None):
                with self.subTest(key=key, value=value):
                    with self.assertRaises(MarvinError):
                        self.client.add({'title': 'test', key: value})
        self.assertEqual(self.calls, [])
    def test_not_enabled_for_unverified_project_route(self):
        with self.assertRaises(MarvinError):
            self.client.project({'title': 'test', 'startDate': '2026-11-17'})
        self.assertEqual(self.calls, [])
    def test_edits_accept_dates_and_explicit_clear(self):
        for project in (False, True):
            for key in ('startDate', 'endDate'):
                for value in ('2026-11-17', None):
                    with self.subTest(project=project,key=key,value=value):
                        self.assertEqual(self.client._fields({key:value},project=project),{key:value})
