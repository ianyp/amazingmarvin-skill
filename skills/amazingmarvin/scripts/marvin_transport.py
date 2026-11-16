"""Bounded public API transport; no automatic replay of writes."""
import json
import os
import ssl
import base64
import time
from email.utils import parsedate_to_datetime
import urllib.error
import urllib.parse
import urllib.request
from marvin_client import MarvinError

PUBLIC_BASE = 'https://serv.amazingmarvin.com/api/'


def reject_constant(value):
    raise ValueError('Nonfinite JSON number')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class ProtectedProxy(urllib.request.ProxyHandler):
    """Mandatory HTTPS tunnel; NO_PROXY must not bypass protected egress."""
    def proxy_open(self, request, proxy, scheme):
        parsed = urllib.parse.urlsplit(proxy)
        credentials = (urllib.parse.unquote(parsed.username) + ':' +
                       urllib.parse.unquote(parsed.password)).encode()
        request.add_header('Proxy-authorization', 'Basic ' +
                           base64.b64encode(credentials).decode('ascii'))
        request.set_proxy(parsed.hostname + ':' + str(parsed.port), 'http')
        return None


def make_opener(base_url):
    token = os.environ.get('MARVIN_API_TOKEN', '')
    if not token.startswith('oc-sent-'):
        return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        proxy = os.environ.get('HTTPS_PROXY', '')
        parsed = urllib.parse.urlsplit(proxy)
        ca = os.environ.get('SSL_CERT_FILE', '')
        if (base_url != PUBLIC_BASE or parsed.scheme != 'http' or
                parsed.hostname != '127.0.0.1' or not parsed.port or
                parsed.username != 'openclaw' or not parsed.password or
                parsed.path not in ('', '/') or parsed.query or parsed.fragment or not ca):
            raise ValueError()
        context = ssl.create_default_context(cafile=ca)
        return urllib.request.build_opener(ProtectedProxy({'https': proxy}),
            urllib.request.HTTPSHandler(context=context), NoRedirect())
    except (ValueError, OSError):
        raise MarvinError('Protected token requires Gateway HTTPS proxy and trusted CA',
                          code='protected_proxy_unavailable') from None


class Transport:
    def __init__(self, *, reserve, defer=lambda seconds: None, clock=time.time, base_url=PUBLIC_BASE, allow_loopback=False, timeout=20):
        parsed = urllib.parse.urlsplit(base_url)
        loopback = allow_loopback and parsed.scheme == 'http' and parsed.hostname == '127.0.0.1' and not parsed.username and not parsed.password and parsed.path == '/api/' and not parsed.query and not parsed.fragment
        if base_url != PUBLIC_BASE and not loopback:
            raise MarvinError('Only the Marvin public API origin is allowed')
        self.base = base_url
        self.reserve = reserve
        self.defer = defer
        self.clock = clock
        self.timeout = timeout
        self.opener = make_opener(base_url)

    def __call__(self, method, path, headers, body):
        if method not in ('GET', 'POST') or not path or path.startswith('/') or ':' in path or '..' in path or '#' in path:
            raise MarvinError('Invalid API request path or method')
        data = None if body is None else json.dumps(body, allow_nan=False).encode()
        request_headers = dict(headers)
        if data is not None:
            request_headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(self.base + path, data=data, headers=request_headers, method=method)
        self.reserve()
        write = method == 'POST' and path not in ('test', 'tracks', 'downloadAttachment')
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read(2_000_001)
                if method == 'GET' and path == 'trackedItem' and response.status == 204 and raw == b'':
                    return None
                if len(raw) > 2_000_000:
                    raise MarvinError('Response exceeds size limit', code='response_too_large', outcome_unknown=write)
                if method == 'POST' and path in ('test', 'reminder/set', 'reminder/delete') and raw == b'OK':
                    return 'OK'
                if path == 'downloadAttachment':
                    try: return raw.decode('utf-8').strip()
                    except UnicodeError: raise MarvinError('Invalid download response', code='invalid_response') from None
                try:
                    return json.loads(raw, parse_constant=reject_constant)
                except (ValueError, UnicodeError):
                    raise MarvinError('Response is not valid JSON', code='invalid_response', outcome_unknown=write) from None
        except urllib.error.HTTPError as error:
            status = error.code
            if status == 429:
                try:
                    delay = max(60, int(error.headers.get('Retry-After', '60')))
                except ValueError:
                    try:
                        delay = max(60, parsedate_to_datetime(error.headers.get('Retry-After', '')).timestamp() - self.clock())
                    except (ValueError, TypeError, OverflowError):
                        delay = 60
                self.defer(delay)
            error.close()
            raise MarvinError('API returned HTTP ' + str(status), code='http_' + str(status), outcome_unknown=write and status >= 500) from None
        except MarvinError:
            raise
        except (OSError, ValueError):
            raise MarvinError('Network request failed', code='transport_error', outcome_unknown=write) from None
