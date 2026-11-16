"""Bounded attachment fetch. Never forwards API credentials or emits bearer URLs."""
from pathlib import Path
from urllib.parse import urlsplit
import urllib.request
from marvin_client import MarvinError
from marvin_transport import NoRedirect

MAX_SIZE=20_000_000

def validate_url(url):
    try:
        p=urlsplit(url)
        if p.scheme!='https' or not p.hostname or not p.hostname.endswith('.backblazeb2.com') or p.username or p.password or p.port not in (None,443) or p.fragment:
            raise ValueError()
    except (ValueError,TypeError):
        raise MarvinError('Unsupported attachment download host or URL',code='unsupported_download_host') from None

def download(url,output,*,size):
    validate_url(url)
    if isinstance(size,bool) or not isinstance(size,int) or not 0<=size<=MAX_SIZE: raise MarvinError('Attachment exceeds 20 MB limit or size is unknown')
    path=Path(output)
    if path.exists(): raise MarvinError('Output file already exists')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    created=False
    try:
        with opener.open(urllib.request.Request(url,method='GET'),timeout=30) as response:
            length=response.headers.get('Content-Length')
            if length is not None and int(length)>MAX_SIZE: raise MarvinError('Attachment exceeds size limit')
            with path.open('xb') as out:
                created=True;path.chmod(0o600);total=0
                while True:
                    block=response.read(min(65536,MAX_SIZE+1-total))
                    if not block: break
                    total+=len(block)
                    if total>MAX_SIZE: raise MarvinError('Attachment exceeds size limit')
                    out.write(block)
            if total!=size: raise MarvinError('Attachment size differs from metadata',code='invalid_response')
        return {'path':str(path.resolve()),'bytes':total}
    except Exception:
        if created: path.unlink(missing_ok=True)
        raise MarvinError('Attachment download failed; no complete file saved',code='download_failed') from None
