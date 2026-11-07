"""Verify the frozen archive and mock board command planning; never run GCC/SSH.

The evidence is written OUTSIDE the archive/package to avoid a self-referential
manifest.  Mock success is dependency/plumbing validation, not ARM execution.
"""
from pathlib import Path,PurePosixPath
import argparse,contextlib,hashlib,io,json,os,re,runpy,subprocess,sys,tarfile,tempfile
from unittest.mock import patch

WS=Path(__file__).resolve().parents[1]
PACKAGE=WS/'lab3-optimized-prepared'
PRESERVED={
    'lab3-ready.tgz':'349c9483f99cab1ac9d4edc7512928fe1f3004b16ed2325609a47ebfb3861984',
    'resources/lab3-optimized-v6-ready.tgz':'04c9413f1b57c2e12a1ca105caf15ed8dacd527d8731a5e0c37e13486ac58f30',
    'resources/lab3-optimized-v7-ready.tgz':'144d594f9f8a844ae1dfb616da073b1d212b17383e1b65ad5d5e59629fcc4ddd',
    'resources/lab3-optimized-v8-ready.tgz':'4936a6db6269fd3e054b95050ebd5feda578cf7e141665dbf62ab475d001ddae',
}
V8_SOURCE_PATHS=('common/graphic-v8-batch.c','common/fast_pixels_v8.h',
                 'common/prepared_image_v8.h','test/sprint-v6-main.c')
VARIANTS='baseline,v8-packed,v8-sprint,v9-core,v9-sprint'

def require(condition,message):
    if not condition:raise AssertionError(message)

def digest(data):return hashlib.sha256(data).hexdigest()

def archive_files(path):
    result={}
    with tarfile.open(path,'r:gz') as tar:
        for member in tar.getmembers():
            name=PurePosixPath(member.name)
            require(not name.is_absolute() and '..' not in name.parts,'Unsafe archive member: '+member.name)
            if member.isdir():continue
            require(member.isfile(),'Unexpected non-file archive member: '+member.name)
            require(member.name not in result,'Duplicate archive member: '+member.name)
            stream=tar.extractfile(member)
            require(stream is not None,'Unreadable archive member: '+member.name)
            result[member.name]=stream.read()
    return result

def archived_suffix(files,suffix):
    matches=[v for k,v in files.items() if k==suffix or k.endswith('/'+suffix)]
    require(len(matches)==1,'Archive suffix is missing or ambiguous: '+suffix)
    return matches[0]

def check_archive(archive,report):
    files=archive_files(archive)
    prefix=PACKAGE.name+'/'
    require(all(n.startswith(prefix) for n in files),'Unexpected archive root')
    relative={n[len(prefix):]:data for n,data in files.items()}
    require('manifest.json' in relative,'Missing manifest')
    manifest=json.loads(relative['manifest.json'].decode('utf-8'))
    require(manifest['version']=='20261018-integrated-candidate-9','Not the v9 package')
    hashes=manifest['sourceHashes']
    require(set(relative)==set(hashes)|{'manifest.json'},'Archive and manifest file lists differ')
    for name,expected in hashes.items():
        require(digest(relative[name])==expected,'Archive hash mismatch: '+name)
        require((PACKAGE/name).is_file(),'Local packaged file is missing: '+name)
        require((PACKAGE/name).read_bytes()==relative[name],'Local package differs from frozen archive: '+name)
    require((PACKAGE/'manifest.json').read_bytes()==relative['manifest.json'],'Local manifest mismatch')
    require(not any(PurePosixPath(n).name=='arm_neon.h' or 'neon-emulation' in PurePosixPath(n).parts for n in files),
            'Host NEON emulation leaked into board package')
    archive_hash=digest(archive.read_bytes())
    sidecar=Path(str(archive)+'.sha256')
    require(sidecar.is_file() and sidecar.read_text(encoding='ascii').split()[0]==archive_hash,'Archive sidecar SHA256 mismatch')
    report['archive']={'path':str(archive.relative_to(WS)),'sha256':archive_hash,'files':len(relative),
                       'manifestVersion':manifest['version'],'manifestAndLocalFilesMatch':True,'hostNeonEmulationAbsent':True}
    preserved={}
    for name,expected in PRESERVED.items():
        p=WS/name;require(p.is_file(),'Missing preserved archive: '+name)
        actual=digest(p.read_bytes());require(actual==expected,'Preserved archive changed: '+name)
        preserved[name]=actual
    report['preservedArchives']=preserved
    v8=archive_files(WS/'resources/lab3-optimized-v8-ready.tgz')
    sources={}
    for name in V8_SOURCE_PATHS:
        before=archived_suffix(v8,name)
        require(relative[name]==before,'V8 source changed inside v9: '+name)
        study=WS/'lab3-optimization-study'/('sprint-v6-main.c' if name.startswith('test/') else name)
        require(study.read_bytes()==before,'V8 research source changed: '+str(study))
        sources[name]=digest(before)
    original=archive_files(WS/'lab3-ready.tgz')
    require(relative['test/main.c']==archived_suffix(original,'test/main.c'),'Original course main.c changed')
    report['preservedV8Sources']=sources
    required=('run-sprint.py','board_compare.py','native_checks.py','prepare_precise_timing.py',
              'common/graphic-v9-batch.c','common/fast_pixels_v9.h','common/prepared_image_v9.h',
              'common/geometry_batch_api_v9.h','common/geometry_batch_v9.h','common/text_batch_api_v9.h','common/text_batch_v9.h',
              'test/sprint-v9-main.c','tests/test_original_replay.c','tests/test_sprint_v9_replay.c',
              'tests/test_v9_rows.c','tests/test_v9_pixels.c','tests/test_v9_cull.c','tests/test_v9_alloc.c',
              'tests/test_v9_geometry.c','tests/test_v9_text_real.c','tests/test_v9_text_cases.h',
              'common/image-fast.c','out/font.ttc','out/test.jpg','out/test.png')
    for name in required:require(name in hashes,'Required v9 dependency missing from manifest/archive: '+name)
    report['requiredV9Dependencies']=list(required)

def forbid_process(*args,**kwargs):
    raise AssertionError('Real subprocess execution is forbidden by this verifier')

def mock_runner(report):
    tests=[]
    project=str(WS/'mock-project-with spaces')
    cases=[([],5,0),(['--build-only'],5,0),(['--precise-timing'],5,0),
           (['--build-only','--precise-timing','--runs','7'],7,0),([],5,23)]
    for options,runs,returncode in cases:
        captured=[]
        def fake_call(command,*args,**kwargs):captured.append(list(map(str,command)));return returncode
        argv=[str(PACKAGE/'run-sprint.py'),'--project',project,*options]
        with patch.object(sys,'argv',argv),patch.object(subprocess,'call',fake_call),patch.object(subprocess,'Popen',forbid_process),patch.object(subprocess,'run',forbid_process):
            try:runpy.run_path(str(PACKAGE/'run-sprint.py'),run_name='__main__')
            except SystemExit as ex:require(ex.code==returncode,'run-sprint failed to forward exit status')
            else:raise AssertionError('run-sprint did not terminate through sys.exit')
        require(len(captured)==1,'run-sprint should dispatch exactly once')
        command=captured[0]
        require(command[:2]==[sys.executable,str(PACKAGE/'board_compare.py')],'Unexpected board_compare command')
        for flag,value in (('--project',project),('--variants',VARIANTS),('--runs',str(runs)),('--threads','2'),('--threshold','4096')):
            require(command.count(flag)==1 and command[command.index(flag)+1]==value,'Runner option mismatch: '+flag)
        for flag in ('--build-only','--precise-timing'):
            require((flag in command)==(flag in options),'Runner forwarding mismatch: '+flag)
        require(all(x in command for x in ('--lto','--native-cpu','--vector-report','--no-stats','--active-wait')),'Missing native profile flags')
        tests.append({'options':options,'forwardedCommand':command,'exitStatus':returncode})
    report['runnerDispatchMocks']=tests

def check_quote_dependencies(path,include_dirs,seen):
    path=path.resolve()
    if path in seen:return
    seen.add(path)
    source=path.read_text(encoding='utf-8')
    for header in re.findall(r'^\s*#\s*include\s*"([^"]+)"',source,re.MULTILINE):
        choices=[path.parent/header]+[d/header for d in include_dirs]
        resolved=next((p.resolve() for p in choices if p.is_file()),None)
        require(resolved is not None,'Unresolved quoted native include %r from %s'%(header,path))
        check_quote_dependencies(resolved,include_dirs,seen)

def mock_native(report):
    all_commands=[];profiles=[];seen=set();compiled={};font_runs=[]
    original_write_text=Path.write_text
    def utf8_write_text(self,data,*args,**kwargs):
        if not args and kwargs.get('encoding') is None:kwargs['encoding']='utf-8'
        return original_write_text(self,data,*args,**kwargs)
    def fake_run(command,*args,**kwargs):
        command=list(map(str,command));all_commands.append(command)
        require(not kwargs.get('shell'),'Native checker attempted a shell')
        require(not any('FB_TEST_NEON' in x or 'neon-emulation' in x for x in command),'Native checker selected host emulation')
        if command[0]=='gcc':
            sources=[Path(x) for x in command[1:] if x.endswith('.c') and not x.startswith('-')]
            require(sources,'Native build has no C source')
            includes=[Path(x[2:]) for x in command if x.startswith('-I')]
            for source in sources:
                require(source.is_file(),'Native source missing: '+str(source))
                check_quote_dependencies(source,includes,seen)
            test=sources[0].stem
            if test not in ('test_fast_rows','test_v8_rows','test_v9_rows'):
                require(PACKAGE/'common/image-fast.c' in sources,'Native test omitted real image-fast.c: '+test)
            require(all(lib in command for lib in ('-ljpeg','-lpng','-lfreetype','-lz')),'Native test omitted real image/font libraries')
            output=Path(command[command.index('-o')+1]);compiled[str(output)]=test
            return subprocess.CompletedProcess(command,0,stdout='MOCK compile planning only\n',stderr='')
        require(command[0] in compiled,'Attempt to run an unplanned native executable: '+command[0])
        test=compiled[command[0]]
        if test in ('test_text_real','test_v9_text_real'):
            require(command[1:]==[str(PACKAGE/'out/font.ttc')],'Native font argument missing/wrong')
            require(Path(command[1]).is_file(),'Course font file missing');font_runs.append(test)
        if test=='test_opaque_batch':
            require(command[1:]==[str(PACKAGE/'out/test.jpg')],'Native opaque batch asset argument missing/wrong')
        if 'replay' in test:
            require(Path(kwargs['cwd'])==PACKAGE/'out','Replay did not use packaged asset cwd')
            output=''.join('STAGE_HASH %d %016x\n'%(i,i+1) for i in range(9))
        else:output='MOCK native execution skipped\n'
        return subprocess.CompletedProcess(command,0,stdout=output,stderr='')
    temporary_root=WS/'evidence';temporary_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='v9-package-native-mock-',dir=temporary_root) as temp:
        temporary=Path(temp).resolve()
        require(temporary_root.resolve() in temporary.parents,'Temporary cleanup path escaped evidence workspace')
        project=temporary/'project'
        (project/'common/external/include').mkdir(parents=True);(project/'common/external/lib').mkdir(parents=True)
        configs=[('baseline','graphic-baseline.c',[]),('v8-packed','graphic-v8-batch.c',['-DFB_DISABLE_PRODUCTS']),
                 ('v8-sprint','graphic-v8-batch.c',[]),('v9-core','graphic-v9-batch.c',['-DFB_DISABLE_GEOMETRY_BATCH']),
                 ('v9-sprint','graphic-v9-batch.c',[]),('v9-dsu','graphic-v9-batch.c',['-DFB_GEOMETRY_DSU'])]
        with patch.object(subprocess,'run',fake_run),patch.object(subprocess,'call',forbid_process),patch.object(subprocess,'Popen',forbid_process),patch.object(Path,'write_text',utf8_write_text),contextlib.redirect_stdout(io.StringIO()):
            module=runpy.run_path(str(PACKAGE/'native_checks.py'),run_name='v9_native_mock')
            for name,graphic,flags in configs:
                record=temporary/name;record.mkdir()
                flags=['-O3','-Wall','-fopenmp','-DFB_DISABLE_STATS',*flags]
                start=len(all_commands)
                result=module['native_checks'](project,record,dict(os.environ),graphic,flags)
                if name!='baseline':result+=module['native_batch_checks'](project,record,dict(os.environ),graphic,flags)
                calls=all_commands[start:]
                if name.startswith('v9'):
                    builds=[Path(c[c.index('-o')+1]).name for c in calls if c[0]=='gcc']
                    for test in ('test_v9_pixels','test_v9_cull','test_v9_alloc','test_v9_geometry','test_v9_text_real','test_sprint_v9_replay'):
                        require(test in builds,'Native v9 test was not planned: '+test)
                profiles.append({'variant':name,'plannedCommands':len(calls),'mockPassedNames':result})
    require('test_v9_text_real' in font_runs,'No native v9 real-font invocation planned')
    report['nativePlanningMocks']={'profiles':profiles,'buildCommands':sum(c[0]=='gcc' for c in all_commands),
        'runCommands':sum(c[0]!='gcc' for c in all_commands),'resolvedQuoteDependencyFiles':len(seen),
        'realImageFontSourcesAndArgumentsPresent':True,'realExecution':False,'externalLibraryABIValidated':False,
        'note':'Subprocess calls were replaced with dependency/planning assertions; no native binary or compiler was executed.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,default=WS/'lab3-optimized-ready.tgz')
    parser.add_argument('--report',type=Path,default=WS/'evidence/v9-package-verification.json')
    args=parser.parse_args()
    report={'passed':False,'hardwareValidated':False,'armNativeCompileValidated':False,'performanceMeasured':False}
    try:
        check_archive(args.archive.resolve(),report);mock_runner(report);mock_native(report);report['passed']=True
    except Exception as error:
        report['error']=type(error).__name__+': '+str(error)
        raise
    finally:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS: archive/manifest, preserved original/v6/v7/v8, v8 source bytes, runner forwarding, native dependency mocks')
    print(args.report)

if __name__=='__main__':main()
