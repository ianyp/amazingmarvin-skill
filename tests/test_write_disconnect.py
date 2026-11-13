import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from test_client import Client, MarvinError
from marvin_transport import Transport

class DropHandler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_POST(self):
        self.rfile.read(int(self.headers.get('Content-Length',0)))
        self.server.accepted += 1
        self.connection.shutdown(socket.SHUT_RDWR)
        self.connection.close()

class WriteDisconnectTests(unittest.TestCase):
    def test_accepted_write_lost_response_not_replayed(self):
        server = ThreadingHTTPServer(('127.0.0.1',0), DropHandler)
        server.accepted = 0
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            transport = Transport(reserve=lambda: None, base_url='http://127.0.0.1:%d/api/' % server.server_port, allow_loopback=True)
            client = Client('synthetic', transport=transport)
            with self.assertRaises(MarvinError) as caught: client.add({'title':'synthetic'})
            self.assertTrue(caught.exception.outcome_unknown)
            self.assertEqual(server.accepted, 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
