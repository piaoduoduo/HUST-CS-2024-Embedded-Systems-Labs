"""Reconstruct a source snapshot from the user's matching course template.

Never edits the course project or an existing output directory. No network,
service, compiler or framebuffer access. Python 3.8+ standard library only.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def safe_path(root,relative):
    if not isinstance(relative,str) or '\\' in relative or ':' in relative:
        raise ValueError('Invalid relative path')
    parts=PurePosixPath(relative)
    if parts.is_absolute() or not parts.parts or '..' in parts.parts or str(parts)!=relative:
        raise ValueError('Invalid relative path: '+relative)
    path=root.joinpath(*parts.parts)
    try:path.resolve().relative_to(root.resolve())
    except ValueError:raise ValueError('Path leaves its root: '+relative)
    return path

def rebuild(before,entry):
    expected=entry['baseSHA256']
    if expected is not None and digest(before)!=expected:
        raise ValueError('Course file differs: '+entry['path'])
    if expected is None and before:
        raise ValueError('New-file input must be empty')
    lines=before.decode('utf-8').splitlines(keepends=True)
    result=[];cursor=0
    for edit in entry['edits']:
        start,end=edit['start'],edit['end']
        if not isinstance(start,int) or not isinstance(end,int) or not cursor<=start<=end<=len(lines):
            raise ValueError('Invalid or overlapping edit')
        if not isinstance(edit['lines'],list) or any(not isinstance(s,str) for s in edit['lines']):
            raise ValueError('Invalid replacement lines')
        result.extend(lines[cursor:start]);result.extend(edit['lines']);cursor=end
    result.extend(lines[cursor:]);after=''.join(result).encode('utf-8')
    if digest(after)!=entry['sha256']:
        raise ValueError('Reconstructed hash differs: '+entry['path'])
    return after

def materialize(profile,course,output,include_assets=False):
    course=Path(course).resolve(strict=True);output=Path(output).resolve()
    if output.exists():raise ValueError('Output already exists; choose a new directory')
    if output==course or course in output.parents or output in course.parents:
        raise ValueError('Output and original course tree must be separate')
    catalog=json.loads((ROOT/'profiles.json').read_text(encoding='utf-8'))
    if profile not in catalog:raise ValueError('Unknown profile')
    source=safe_path(ROOT,catalog[profile]['path'])
    data=json.loads(source.read_text(encoding='utf-8'))
    if data['format']!=1 or data['name']!=profile:raise ValueError('Profile format/name mismatch')
    prepared={}
    for entry in data['files']:
        relative=entry['path'];safe_path(output,relative)
        if relative in prepared:raise ValueError('Duplicate output file')
        if entry['baseSHA256'] is None:
            before=b''
        else:
            base=safe_path(course,relative)
            before=base.read_bytes()
        prepared[relative]=rebuild(before,entry)
    assets=[]
    if include_assets:
        for name in ('font.ttc','test.jpg','test.png'):
            path=safe_path(course,'out/'+name)
            if not path.is_file():raise ValueError('Missing course asset: '+name)
            assets.append((name,path))
        if profile not in ('v9','v10'):
            external=safe_path(course,'common/external')
            if not external.is_dir():raise ValueError('Missing course common/external')
            # Refuse source symlinks escaping the user-selected project.
            for p in external.rglob('*'):
                try:p.resolve().relative_to(course)
                except ValueError:raise ValueError('External dependency link leaves course tree')
    # Every source/hash/path is checked before creating an output directory.
    output.mkdir(parents=True)
    for relative,content in prepared.items():
        path=safe_path(output,relative);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
    (output/'out').mkdir(exist_ok=True)
    for name,path in assets:shutil.copy2(path,output/'out'/name)
    if include_assets and profile not in ('v9','v10'):
        shutil.copytree(course/'common/external',output/'common/external')
    if profile in ('v9','v10'):
        # board_compare uses only this manifest's sourceHashes and metadata.
        hashes={p.relative_to(output).as_posix():digest(p.read_bytes()) for p in output.rglob('*') if p.is_file()}
        manifest={'version':'public-'+profile+'-20261019','sourceHashes':hashes,
                  'hardwareValidated':False,'armNativeCompileValidated':False,'performanceMeasured':False,
                  'courseTestUnmodified':False,'baselineTestLoopsAndTimersRetained':True,
                  'baselineMainChanges':'Missing-asset failure guard and bounded result-table formatting; original test loops and timer positions retained'}
        (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return len(prepared)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',required=True,choices=('lab2','lab3','lab4','v9','v10','lab5','lab6'))
    p.add_argument('--course',required=True,help='Matching original 2026 course template')
    p.add_argument('--output',required=True,help='New directory outside the original course tree')
    p.add_argument('--include-assets',action='store_true',help='Copy locally supplied course font/images and stable-profile external libraries; these are not distributed by this repository')
    a=p.parse_args()
    try:
        count=materialize(a.profile,a.course,a.output,a.include_assets)
        print('Prepared %d source files in %s; original course tree unchanged.'%(count,a.output))
        if not a.include_assets:print('Source only: supply course font/images/libraries before building/running.')
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as error:
        p.exit(1,'STOP: %s\n'%error)

if __name__=='__main__':main()
