import unittest
from test_client import Client, MarvinError

class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.reply = []
        self.client = Client('fake', transport=self.transport)
    def transport(self, *args):
        self.calls.append(args)
        return self.reply
    def test_catalogs(self):
        self.client.categories()
        self.client.labels()
        self.assertEqual([x[1] for x in self.calls], ['categories', 'labels'])
    def test_children_encoding(self):
        self.client.children('id &/?')
        self.assertEqual(self.calls[0][1], 'children?parentId=id+%26%2F%3F')
    def test_complete_task(self):
        self.reply = 'OK'
        self.client.done('task-1', offset=60)
        self.assertEqual(self.calls[0][0:2], ('POST', 'markDone'))
        self.assertEqual(self.calls[0][3], {'itemId': 'task-1', 'timeZoneOffset': 60})
    def test_invalid_id_no_write(self):
        with self.assertRaises(MarvinError): self.client.done('', offset=0)
        self.assertEqual(self.calls, [])
    def test_resolve_unique_task(self):
        self.assertEqual(self.client.resolve_task([{'_id': 'a', 'title': 'Call', 'db': 'Tasks'}], 'Call'), 'a')
    def test_resolve_ambiguous_or_project(self):
        for items in [[{'_id': 'a', 'title': 'Call', 'db': 'Projects'}],
                      [{'_id': 'a', 'title': 'Call', 'db': 'Tasks'}, {'_id': 'b', 'title': 'Call', 'db': 'Tasks'}]]:
            with self.assertRaises(MarvinError): self.client.resolve_task(items, 'Call')
        self.assertEqual(self.calls, [])
