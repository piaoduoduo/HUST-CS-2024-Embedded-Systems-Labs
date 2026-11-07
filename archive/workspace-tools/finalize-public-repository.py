"""Record checked local-only delivery; export source files, never Git metadata."""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile

WS=Path(__file__).resolve().parents[1];REPO=WS/'hust-embedded-labs-orangepi'
report_path=WS/'evidence/public-repository-preparation.json'
report=json.loads(report_path.read_text(encoding='utf-8'))
report['hostHello']={'compiler':'GCC 8.1 x86_64 MinGW, -std=c11 -O2 -Wall -Wextra -Werror -pedantic',
 'compiled':True,'output':'Hello embedded linux!','exitStatus':0,'isBoardTest':False}
report['localGitInitialized']=True;report['remoteConfigured']=False
for path in (report_path,REPO/'results/preparation-checks.json'):
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(REPO/'tools/check-repository.py')],check=True)
remote=subprocess.run(['git','-C',str(REPO),'remote','-v'],check=True,capture_output=True,text=True)
assert not remote.stdout.strip()
files=[p for p in REPO.rglob('*') if p.is_file() and not any(x in ('.git','.work','__pycache__','out') for x in p.relative_to(REPO).parts)]
archive=WS/'GitHub发布筹备/hust-embedded-labs-orangepi-local-snapshot.zip'
if archive.exists():raise SystemExit('Existing snapshot preserved; choose a new archive name')
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):z.write(p,'hust-embedded-labs-orangepi/'+p.relative_to(REPO).as_posix())
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist())==len(files)
    for p in files:assert z.read('hust-embedded-labs-orangepi/'+p.relative_to(REPO).as_posix())==p.read_bytes()
archive.with_suffix('.zip.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n',encoding='ascii')
print('PASS: local source snapshot, %d files, no Git metadata/build files, no remote'%len(files))
