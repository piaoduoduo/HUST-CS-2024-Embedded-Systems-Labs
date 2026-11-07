"""Build a separate, source-only public repository candidate; never publish."""
from pathlib import Path
import difflib, hashlib, json, shutil

WS=Path(__file__).resolve().parents[1]
DEST=WS/'hust-embedded-labs-orangepi'
COURSE=WS/'course-source/lab-st-2026'
sha=lambda data:hashlib.sha256(data).hexdigest()

def write(name,text):
    path=DEST/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8')

def write_json(name,value):write(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def collect_profile(name,targets):
    entries=[];diffs=[]
    for relative,source in sorted(targets.items()):
        original=COURSE/relative
        before=original.read_bytes() if original.is_file() else b''
        after=source.read_bytes()
        # These profiles contain UTF-8 source only, not binary course assets.
        old=before.decode('utf-8').splitlines(keepends=True)
        new=after.decode('utf-8').splitlines(keepends=True)
        edits=[]
        for tag,i,j,a,b in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
            if tag!='equal':edits.append({'start':i,'end':j,'lines':new[a:b]})
        entries.append({'path':relative,'baseSHA256':sha(before) if original.is_file() else None,
                        'sha256':sha(after),'edits':edits})
        if before!=after:
            diffs.extend(difflib.unified_diff(old,new,fromfile='a/'+relative if original.is_file() else '/dev/null',tofile='b/'+relative))
    folder='experiments/lab3-v9' if name=='v9' else 'labs/'+name
    write_json(folder+'/profile.json',{'format':1,'name':name,'files':entries})
    write(folder+'/changes.patch',''.join(diffs))
    return {'path':folder+'/profile.json','files':len(entries),'modifiedOrAdded':sum(bool(x['edits']) for x in entries)}

def main():
    if DEST.exists():raise SystemExit('Destination already exists; original repository candidate is preserved')
    selected={}
    for n in ('lab1-ready.tgz','lab2-ready.tgz','lab3-ready.tgz','lab4-ready.tgz','lab5-ready.tgz','lab6-gomoku-ready.tgz','lab3-optimized-ready.tgz','resources/lab3-optimized-v8-ready.tgz'):
        selected[n]=sha((WS/n).read_bytes())
    source_inputs={}
    profiles={}
    for lab in ('lab2','lab3','lab4'):
        targets={str(p.relative_to(COURSE)).replace('\\','/'):p for p in (COURSE/'common').iterdir() if p.is_file()}
        for directory in (lab,'test'):
            targets.update({p.relative_to(COURSE).as_posix():p for p in (COURSE/directory).iterdir() if p.is_file() and p.suffix in ('.c','.h') or p.is_file() and p.name=='Makefile'})
        prepared=WS/(lab+'-prepared')
        if lab=='lab2':
            for n in ('common/graphic.c','common/rules.mk'):targets[n]=prepared/n
        else:
            manifest=json.loads((prepared/'manifest.json').read_text(encoding='utf-8'))
            for item in manifest['files']:
                if item['path'].startswith('out/'):continue
                targets[item['path']]=prepared/item['path']
        for p in targets.values():source_inputs[p.relative_to(WS).as_posix()]=sha(p.read_bytes())
        profiles[lab]=collect_profile(lab,targets)
    package=WS/'lab3-optimized-prepared'
    targets={}
    for folder in ('common','test','lab3','tests'):
        for p in (package/folder).iterdir():
            if p.is_file() and p.suffix in ('.c','.h'):targets[p.relative_to(package).as_posix()]=p
    for n in ('board_compare.py','native_checks.py','runtime_controls.py','restore-controls.py','run-sprint.py','preflight.py','prepare_precise_timing.py','flush_probe.c'):
        targets[n]=package/n
    for p in targets.values():source_inputs[p.relative_to(WS).as_posix()]=sha(p.read_bytes())
    profiles['v9']=collect_profile('v9',targets)
    write_json('profiles.json',profiles)
    for n in ('main.c','Makefile'):
        source=WS/'lab1'/n
        text=source.read_text(encoding='utf-8').replace('TARGET = ../out/lab1','TARGET = out/lab1').replace('mkdir -p ../out','mkdir -p out')
        write('labs/lab1/'+n,text)
        source_inputs[source.relative_to(WS).as_posix()]=sha(source.read_bytes())

    results=json.loads((WS/'evidence/lab3/results.json').read_text(encoding='utf-8'))
    results['recordType']='Actual board measurements, copied without path or account data'
    results['originalRecordSHA256']=sha((WS/'evidence/lab3/results.json').read_bytes())
    write_json('results/board/lab3-20261015.json',results)
    write('results/board/lab3-155ms.log',(WS/'evidence/lab3/o3-2.log').read_text(encoding='utf-8'))
    touch=json.loads((WS/'evidence/lab4/status.json').read_text(encoding='utf-8'))
    write_json('results/board/lab4-20261015.json',touch)
    # Inspected framebuffer captures, no camera photographs or raw desktop screenshots.
    for original,target in [('evidence/lab3/performance-final.png','results/board/lab3-173ms.png'),('evidence/lab4/drawing.png','results/board/lab4-five-fingers.png')]:
        path=DEST/target;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(WS/original,path)
        source_inputs[original]=sha((WS/original).read_bytes())
    for name in ('v9-integrated-results.json','v9-png-offline-results.json','v9-text-offline-results.json','v9-geometry-results.json'):
        source=WS/'lab3-optimization-study'/name
        data=json.loads(source.read_text(encoding='utf-8'))
        clean={k:v for k,v in data.items() if k not in ('logs','sourceReports','preservedArchives') and not isinstance(v,str) or k not in ('logs','sourceReports','preservedArchives') and isinstance(v,str) and 'C:\\' not in v}
        clean.update({'originalRecordSHA256':sha(source.read_bytes()),'recordType':'Host-only historical validation; not rerun on ARM during publication preparation'})
        write_json('results/host/'+name,clean)
    status={'updatedOn':'2026-10-18','remotePublished':False,
      'lab1':{'boardTested':True,'taAccepted':True,'acceptanceEvidence':'User report'},
      'lab2':{'boardTested':True,'taAccepted':True,'acceptanceEvidence':'User report'},
      'lab3':{'baselineBoardTested':True,'taAccepted':False,'acceptanceStatus':'Awaiting confirmation'},
      'lab4':{'boardTested':True,'taAccepted':False,'acceptanceStatus':'Awaiting confirmation'},
      'v9':{'boardTested':False,'armCompiled':False,'taAccepted':False,'state':'待板测'},
      'lab5':{'boardTested':False,'taAccepted':False,'state':'待板测'},
      'lab6':{'boardTested':False,'taAccepted':False,'state':'待板测'},
      'nextAcceptanceUpdate':['lab3','lab5','lab6'],'updateTrigger':'User supplies actual acceptance outcomes; no automatic status promotion'}
    write_json('STATUS.json',status)
    write_json('SOURCE_MANIFEST.json',{'snapshotDate':'2026-10-18','sourceFiles':source_inputs,'preservedOriginalArchives':selected,'note':'Paths name private-workspace sources for traceability; originals were read, not modified.'})
    write('.gitignore','.work/\nbuild/\n__pycache__/\n*.py[cod]\n*.o\n*.exe\n*.tgz\n*.img\n*.ttc\n*.ttf\n*.so*\n.env\n*.pem\n*.key\n')
    write('.gitattributes','* text=auto\n*.py text eol=lf\n*.sh text eol=lf\n*.c text eol=lf\n*.h text eol=lf\n*.json -text\n*.patch -text\n*.png binary\n')
    for p,value in source_inputs.items():assert sha((WS/p).read_bytes())==value,p
    for p,value in selected.items():assert sha((WS/p).read_bytes())==value,p
    print('Prepared isolated public candidate:',DEST)
    print('Profiles:',{k:v['files'] for k,v in profiles.items()})

if __name__=='__main__':main()
