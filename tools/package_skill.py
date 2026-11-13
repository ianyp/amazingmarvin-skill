"""Create a source-only, deterministic OpenClaw skill zip; no credentials/config."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/amazingmarvin'
OUTPUT = ROOT / 'dist/amazingmarvin-skill-offline.zip'
OUTPUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUTPUT, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for source in sorted(SKILL.rglob('*')):
        if not source.is_file() or source.suffix not in ('.md', '.py') or '__pycache__' in source.parts:
            continue
        info = zipfile.ZipInfo(str(Path('amazingmarvin') / source.relative_to(SKILL)))
        info.date_time = (2026, 1, 1, 0, 0, 0)
        info.external_attr = 0o100644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, source.read_bytes())
print(OUTPUT)
