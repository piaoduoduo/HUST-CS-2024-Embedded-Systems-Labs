"""Portable content/link/status checks; does not contact devices or network."""
from pathlib import Path
import ast
import json
import re
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]

def main():
    errors=[];checked=0;links=0
    for path in ROOT.rglob('*'):
        rel=path.relative_to(ROOT)
        if not path.is_file() or any(p in ('.git','.work','__pycache__','out') for p in rel.parts):continue
        checked+=1
        if path.suffix.lower() in ('.ttc','.ttf','.so','.img','.tgz','.exe','.pem','.key'):
            errors.append('Excluded asset found: '+str(rel))
        if path.suffix=='.json':json.loads(path.read_text(encoding='utf-8'))
        if path.suffix=='.py':ast.parse(path.read_text(encoding='utf-8'),feature_version=(3,8))
        if path.suffix=='.md':
            text=path.read_text(encoding='utf-8')
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
                if target.startswith(('https://','http://','#','mailto:')):continue
                target=unquote(target.split('#',1)[0]);links+=1
                resolved=(path.parent/target).resolve()
                try:resolved.relative_to(ROOT)
                except ValueError:errors.append('Link leaves repository: '+str(rel));continue
                if not resolved.exists():errors.append('Broken link in %s: %s'%(rel,target))
        if path.suffix in ('.json','.md','.patch','.log'):
            text=path.read_text(encoding='utf-8')
            for forbidden in ('C:/Us'+'ers/','C:\\Us'+'ers\\','hust-embedded-20261008','E0:51:D8:','-----BEGIN '+'OPENSSH PRIVATE KEY-----'):
                if forbidden in text:errors.append('Private workspace/device marker: '+str(rel))
    status=json.loads((ROOT/'STATUS.json').read_text(encoding='utf-8'))
    trial=json.loads((ROOT/'results/board/trial-20261019.json').read_text(encoding='utf-8'))
    assert trial['lab3']['runsMs']==[22,21,17] and trial['lab3']['medianMs']==21
    for name in ('v10','lab5','lab6'):
        assert status[name]['boardTested'] and not status[name]['taAccepted']
    results=json.loads((ROOT/'results/board/lab3-20261015.json').read_text(encoding='utf-8'))
    totals=[r['total'] for r in results['variants']['o3']['runs']]
    assert totals==[160,155,173] and results['variants']['o3']['medianMs']==160
    for path in ROOT.rglob('profile.json'):
        data=json.loads(path.read_text(encoding='utf-8'))
        for entry in data['files']:
            assert re.fullmatch('[0-9a-f]{64}',entry['sha256'])
            if entry['baseSHA256'] is None and entry['path'].endswith('.py'):
                source=''.join(line for edit in entry['edits'] for line in edit['lines'])
                ast.parse(source,feature_version=(3,8))
    if errors:raise SystemExit('\n'.join(errors))
    print('PASS: %d repository files; %d local documentation links; JSON, Python 3.8 syntax, source-only scope and pending statuses'%(checked,links))

if __name__=='__main__':main()
