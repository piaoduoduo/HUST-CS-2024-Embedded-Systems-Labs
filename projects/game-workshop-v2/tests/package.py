"""Package only after the source-bound offline result passes; keep previous releases."""
from pathlib import Path
import hashlib,json,tarfile,zipfile
root=Path(__file__).resolve().parents[1]
result=json.loads((root/'test-results/result.json').read_text())
assert result.get('hostTestsPassed') and result.get('scriptedWindowsEventTestsPassed')
for rel,digest in result['sources'].items():
    assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel
output=root.parent/'resources';output.mkdir(exist_ok=True)
board=output/'lab6-arcade-v2-board-source.tgz'
files=[p for p in sorted(root.rglob('*')) if p.is_file() and p.suffix not in ('.o','.pyc','.ppm') and '__pycache__' not in p.parts and not p.name.startswith('arcade-records-')]
with tarfile.open(board,'w:gz') as archive:
    for p in files:
        if p.relative_to(root).parts[0] not in ('build','preview'):
            archive.add(p,arcname=root.name+'/'+p.relative_to(root).as_posix())
offline=output/'lab6-arcade-v2-offline.zip'
with zipfile.ZipFile(offline,'w',zipfile.ZIP_DEFLATED) as archive:
    for p in files:archive.write(p,root.name+'/'+p.relative_to(root).as_posix())
manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (board,offline)}
(output/'lab6-arcade-v2-packages.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2))
