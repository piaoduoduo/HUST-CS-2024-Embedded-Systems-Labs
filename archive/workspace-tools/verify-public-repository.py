"""Private workspace integration check; no board or original-tree mutation."""
from pathlib import Path
import importlib.util,json,subprocess,sys,hashlib,tempfile

WS=Path(__file__).resolve().parents[1]
REPO=WS/'hust-embedded-labs-orangepi'
COURSE=WS/'course-source/lab-st-2026'
spec=importlib.util.spec_from_file_location('public_materialize',REPO/'tools/materialize.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    evidence={'passed':False,'boardTestsRun':False,'ARMCompilerRun':False,'remotePublished':False,'profiles':{}}
    manifest=json.loads((REPO/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
    work=REPO/'.work';work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work) as temp:
        for profile in ('lab2','lab3','lab4','v9'):
            destination=Path(temp)/profile
            count=m.materialize(profile,COURSE,destination)
            data=json.loads((REPO/json.loads((REPO/'profiles.json').read_text(encoding='utf-8'))[profile]['path']).read_text(encoding='utf-8'))
            for entry in data['files']:
                assert sha(destination/entry['path'])==entry['sha256']
                if entry['baseSHA256'] is not None:assert sha(COURSE/entry['path'])==entry['baseSHA256']
            if profile=='v9':
                v9=json.loads((destination/'manifest.json').read_text(encoding='utf-8'))
                for name,value in v9['sourceHashes'].items():assert sha(destination/name)==value
                assert (destination/'tests/test_sprint_v9_replay.c').is_file()
            evidence['profiles'][profile]={'filesReconstructed':count,'allOutputHashesMatch':True}
        # Failure must not leave output, mutate course inputs or overwrite a prior result.
        bad=Path(temp)/'bad-course';bad.mkdir();(bad/'common').mkdir()
        (bad/'common/common.h').write_bytes(b'not the course header')
        failed=Path(temp)/'failed-output'
        try:m.materialize('lab3',bad,failed)
        except (ValueError,FileNotFoundError):pass
        else:raise AssertionError('Invalid course accepted')
        assert not failed.exists()
        evidence['badInputLeavesNoOutput']=True
        # Exercise the optional local-assets path with a tiny supplied input tree.
        for profile in ('lab3','v9'):
            base=Path(temp)/('asset-input-'+profile);base.mkdir()
            folder='experiments/lab3-v9' if profile=='v9' else 'labs/lab3'
            data=json.loads((REPO/folder/'profile.json').read_text(encoding='utf-8'))
            for entry in data['files']:
                if entry['baseSHA256'] is not None:
                    p=base/entry['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((COURSE/entry['path']).read_bytes())
            for n in ('font.ttc','test.jpg','test.png'):
                p=base/'out'/n;p.parent.mkdir(exist_ok=True);p.write_bytes(('mock-'+n).encode())
            ext=base/'common/external/include';ext.mkdir(parents=True,exist_ok=True);(ext/'example.h').write_text('/* test */')
            dest=Path(temp)/('asset-output-'+profile)
            m.materialize(profile,base,dest,True)
            for n in ('font.ttc','test.jpg','test.png'):assert (dest/'out'/n).read_bytes()==('mock-'+n).encode()
            if profile!='v9':assert (dest/'common/external/include/example.h').is_file()
        evidence['optionalAssetCopyWithSyntheticInputsPassed']=True
    for key in ('sourceFiles','preservedOriginalArchives'):
        for name,value in manifest[key].items():assert sha(WS/name)==value,('original changed',name)
    evidence['originalSourcesAndArchivesUnchanged']=True
    for args in (['-m','unittest','discover','-s','tests','-v'],['tools/check-repository.py']):
        result=subprocess.run([sys.executable]+args,cwd=REPO,capture_output=True,text=True,encoding='utf-8',errors='replace')
        assert result.returncode==0,result.stdout+result.stderr
        print(result.stdout+result.stderr)
    evidence['unitTestsAndContentChecksPassed']=True
    evidence['passed']=True
    target=WS/'evidence/public-repository-preparation.json'
    target.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (REPO/'results/preparation-checks.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS publication preparation; original source/assets unchanged; no board or remote action')

if __name__=='__main__':main()
