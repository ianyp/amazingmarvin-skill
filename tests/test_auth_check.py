import unittest
from test_client import Client
class AuthCheckTests(unittest.TestCase):
    def test_auth_check_contract(self):
        calls = []
        def transport(*args):
            calls.append(args)
            return 'OK'
        self.assertEqual(Client('fake', transport=transport).check_auth(), 'OK')
        self.assertEqual(calls[0][0:2], ('POST','test'))
        self.assertIsNone(calls[0][3])
