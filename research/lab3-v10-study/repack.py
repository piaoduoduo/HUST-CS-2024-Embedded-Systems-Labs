"""Repack this validated v10 snapshot; never regenerate it from older sources."""
from pathlib import Path
import argparse,hashlib,json,shutil,tarfile

ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--promote-latest',action='store_true',help='Also update lab3-optimized-ready.tgz after checking the preserved v9 archive')
    args=p.parse_args()
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['version']=='20261018-integrated-candidate-10'
    for name,value in manifest['sourceHashes'].items():assert sha(ROOT/name)==value,('file changed after validation',name)
    if args.promote_latest:
        backup=ROOT.parent/'resources/lab3-optimized-v9-ready.tgz'
        assert sha(backup)=='a6bfb3e6336bcee2c7197164fc1c3fce0dc455d52243463e241a78136a9b9877','v9 backup not verified'
    archive=ROOT.parent/'lab3-optimized-v10-ready.tgz'
    with tarfile.open(archive,'w:gz') as tar:
        for name in sorted(list(manifest['sourceHashes'])+['manifest.json']):tar.add(ROOT/name,arcname=ROOT.name+'/'+name,recursive=False)
    with tarfile.open(archive) as tar:
        for name,value in manifest['sourceHashes'].items():assert hashlib.sha256(tar.extractfile(ROOT.name+'/'+name).read()).hexdigest()==value
    archive.with_suffix('.tgz.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
    if args.promote_latest:
        latest=ROOT.parent/'lab3-optimized-ready.tgz';shutil.copy2(archive,latest)
        latest.with_suffix('.tgz.sha256').write_text(sha(latest)+'  '+latest.name+'\n',encoding='ascii')
        assert sha(latest)==sha(archive)
    print('PASS v10 archive member hashes; versioned package:',archive.name)
    if args.promote_latest:print('Latest package now v10; preserved v9 archive verified.')

if __name__=='__main__':main()
