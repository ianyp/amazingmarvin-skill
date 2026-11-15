import os
import ssl
import unittest
from unittest.mock import patch
from test_client import MarvinError
from marvin_transport import Transport
import urllib.request

class ProtectedProxyTests(unittest.TestCase):
    def env(self, **extra):
        return patch.dict(os.environ, {'MARVIN_API_TOKEN': 'oc-sent-v2.fake.end',
            'HTTPS_PROXY': 'http://openclaw:fake-password@127.0.0.1:12345',
            'SSL_CERT_FILE': ssl.get_default_verify_paths().cafile or '/etc/ssl/certs/ca-certificates.crt', **extra}, clear=True)

    def test_missing_proxy_fails_closed(self):
        with self.env(HTTPS_PROXY=''), self.assertRaises(MarvinError):
            Transport(reserve=lambda: None)

    def test_remote_proxy_rejected(self):
        with self.env(HTTPS_PROXY='http://openclaw:fake@example.com:1234'), self.assertRaises(MarvinError):
            Transport(reserve=lambda: None)

    def test_missing_ca_fails_closed(self):
        with self.env(SSL_CERT_FILE=''), self.assertRaises(MarvinError):
            Transport(reserve=lambda: None)

    def test_no_proxy_cannot_bypass_protected_route(self):
        with self.env(NO_PROXY='*'):
            transport = Transport(reserve=lambda: None)
            handler = next(h for h in transport.opener.handlers if isinstance(h, urllib.request.ProxyHandler))
            request = urllib.request.Request('https://serv.amazingmarvin.com/api/test')
            handler.proxy_open(request, handler.proxies['https'], 'https')
            self.assertEqual(request.host, '127.0.0.1:12345')
            self.assertEqual(request._tunnel_host, 'serv.amazingmarvin.com')
            self.assertTrue(request.has_header('Proxy-authorization'))

    def test_protected_token_never_uses_loopback_test_origin(self):
        with self.env(), self.assertRaises(MarvinError):
            Transport(reserve=lambda: None, base_url='http://127.0.0.1/api/', allow_loopback=True)
