import unittest
import tempfile
from pathlib import Path
from test_client import Client, MarvinError

class DownloadTests(unittest.TestCase):
    def test_url_policy(self):
        from marvin_download import validate_url
        validate_url('https://s3.eu-central-003.backblazeb2.com/bucket/file?token=private')
        for u in ['http://s3.eu-central-003.backblazeb2.com/file','https://localhost/file','https://evilbackblazeb2.com/file','https://user:pw@s3.eu-central-003.backblazeb2.com/file','https://s3.eu-central-003.backblazeb2.com:99/f']:
            with self.assertRaises(MarvinError):validate_url(u)
    def test_filename_and_limit(self):
        from marvin_download import download
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(MarvinError):download('https://s3.eu-central-003.backblazeb2.com/x',Path(d)/'x',size=30_000_000)
    def test_attachment_must_match_document(self):
        c=Client('fake',transport=lambda *a:{'_id':'t','db':'Tasks'},full_access=True)
        with self.assertRaises(MarvinError):c.download_attachment('t','missing','/tmp/unused')
