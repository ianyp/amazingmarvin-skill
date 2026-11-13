import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from test_client import MarvinError
from marvin_transport import Transport

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def handle_request(self):
        self.server.calls.append((self.command, self.path, dict(self.headers), self.rfile.read(int(self.headers.get('Content-Length', 0)))))
        status, headers, body = self.server.reply
        self.send_response(status)
        for key, val in headers.items(): self.send_header(key, val)
        self.end_headers()
        self.wfile.write(body)

class TransportTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.reply = (200, {}, b'[]')
        self.server.calls = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:%d/api/' % self.server.server_port
        self.reservations = []
        self.transport = Transport(base_url=self.base, allow_loopback=True, reserve=lambda: self.reservations.append(True))
    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
    def test_real_http_serialization(self):
        self.server.reply = (200, {}, b'"OK"')
        self.assertEqual(self.transport('POST', 'addTask', {'X-API-Token': 'fake'}, {'title': 'A & B'}), 'OK')
        method, path, headers, body = self.server.calls[0]
        self.assertEqual((method, path), ('POST', '/api/addTask'))
        self.assertEqual(json.loads(body), {'title': 'A & B'})
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(len(self.reservations), 1)
    def test_redirect_not_followed(self):
        self.server.reply = (302, {'Location': self.base + 'stolen'}, b'')
        with self.assertRaises(MarvinError): self.transport('GET', 'todayItems', {'X-API-Token': 'fake'}, None)
        self.assertEqual(len(self.server.calls), 1)
    def test_http_failures_sanitized(self):
        for status in [401, 403, 404, 429, 500]:
            self.server.reply = (status, {}, b'fake-secret')
            with self.subTest(status=status), self.assertRaises(MarvinError) as caught:
                self.transport('POST', 'addTask', {}, {})
            self.assertNotIn('fake-secret', str(caught.exception))
            self.assertEqual(caught.exception.code, 'http_' + str(status))
            self.assertEqual(caught.exception.outcome_unknown, status >= 500)
    def test_invalid_json_write_unknown(self):
        self.server.reply = (200, {}, b'bad json')
        with self.assertRaises(MarvinError) as caught: self.transport('POST', 'addTask', {}, {})
        self.assertTrue(caught.exception.outcome_unknown)
    def test_arbitrary_origin_rejected(self):
        with self.assertRaises(MarvinError): Transport(base_url='https://example.org/api/', reserve=lambda: None)
    def test_absolute_path_rejected(self):
        with self.assertRaises(MarvinError): self.transport('GET', 'https://example.org', {}, None)
        self.assertEqual(self.server.calls, [])
