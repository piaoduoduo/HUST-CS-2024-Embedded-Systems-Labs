"""Offline mock of board_compare diagnostics. Does not connect to hardware."""
from pathlib import Path
import ast, importlib.util, json, os, shutil, subprocess, sys, tempfile, types
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
RUNNER=ROOT.parent/'lab3-optimized-prepared/board_compare.py'
BUILD=ROOT/'build-v9-timing-tests';BUILD.mkdir(exist_ok=True)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
module=load('board_precise_test',RUNNER)
generator=load('prepare_precise_timing',ROOT/'audit-20261018/prepare_precise_timing.py')
ast.parse(RUNNER.read_text(encoding='utf-8'),feature_version=(3,8))
course='draw pixel: 9 ms\ndraw rect: 10 ms\ndraw line: 11 ms\n**jpeg: 12\n**png: 13\n**font: 14\ndraw text: 15 ms\nTotal time: 84 ms\n'
diagnostic=''.join('DIAGNOSTIC_STAGE_NS %s 2000000\n'%name for name in ('pixel','rect','line','jpg','png','font','text'))+'DIAGNOSTIC_TOTAL_NS 14000000\nDIAGNOSTIC_ONLY=1 includes_flush=0 includes_decode=0 includes_sleep=0\n'
assert module.parse_metrics(course)['total']==84
assert module.parse_precise_metrics(course+diagnostic)['total']==14000000
invalid=[diagnostic.replace('pixel','unknown'),diagnostic.replace('14000000','14000001'),diagnostic+'DIAGNOSTIC_STAGE_NS text 2000000\n',diagnostic.replace('DIAGNOSTIC_STAGE_NS text 2000000\n',''),diagnostic.replace('DIAGNOSTIC_ONLY=1','DIAGNOSTIC_ONLY=0'),diagnostic+'DIAGNOSTIC_TOTAL_NS 14000000\n']
for text in invalid:
    try:module.parse_precise_metrics(text)
    except ValueError:pass
    else:raise AssertionError('malformed diagnostic accepted')
logs={}
class FakeControls:
    def __init__(self,args,record,environment):self.path=record/'mock-controls.json';self.restored=False;controls.append(self)
    def restore(self):self.restored=True
def scenario(label,precise,build_only):
    fixture=Path(tempfile.mkdtemp(prefix=label+'-',dir=BUILD));package=fixture/'package';package.mkdir()
    project=fixture/'project';(project/'common/external/include').mkdir(parents=True);(project/'common/external/lib').mkdir()
    (package/'common').mkdir();(package/'test').mkdir();(package/'out').mkdir()
    # Real current course/v8/v9 main sources exercise the REAL generator;
    # compilation and Linux system operations alone are mocked.
    sources={name:(ROOT.parent/'lab3-optimized-prepared/test'/name).read_bytes() for name in ('main.c','sprint-v6-main.c')}
    sources['sprint-v9-main.c']=(ROOT/'sprint-v9-main.c').read_bytes()
    for path in (ROOT/'common').glob('*.h'):shutil.copyfile(path,package/'common'/path.name)
    for name,source in sources.items():(package/'test'/name).write_bytes(source)
    for name in ('test.jpg','test.png','font.ttc'):(package/'out'/name).write_bytes(b'mock asset')
    (package/'manifest.json').write_text(json.dumps({'sourceHashes':{}}),encoding='utf-8')
    calls=[];checks=[]
    def run(command,**kwargs):
        command=list(map(str,command));calls.append(command)
        if command==['gcc','--version']:return subprocess.CompletedProcess(command,0,'mock gcc 9.4\n','')
        if command[0]=='gcc':return subprocess.CompletedProcess(command,0,'','')
        if command[0]=='python3':return subprocess.CompletedProcess(command,0,'','')
        if Path(command[0]).name=='test':return subprocess.CompletedProcess(command,0,course,'FLUSH_US=500\n')
        if Path(command[0]).name=='test-diagnostic':return subprocess.CompletedProcess(command,0,course+diagnostic,'FLUSH_US=700\n')
        raise AssertionError('unexpected subprocess '+repr(command))
    def native(*args):checks.append(args[-1]);return ['mock-native-pass']
    def link(self,target,*args,**kwargs):self.write_bytes(Path(target).read_bytes())
    options=['board_compare.py','--project',str(project),'--variants','baseline,v8-sprint,v9-sprint,v9-dsu','--runs','2','--disable','geometry-coalesce','--lto','--no-stats']
    if precise:options.append('--precise-timing')
    if build_only:options.append('--build-only')
    with patch.object(module,'ROOT',package),patch.object(module,'os',types.SimpleNamespace(name='posix',environ=os.environ,pathsep=os.pathsep)),patch.object(module.platform,'machine',return_value='aarch64'),patch.object(module.subprocess,'run',side_effect=run),patch.object(module,'snapshot',return_value={}),patch.object(sys,'argv',options),patch.object(Path,'symlink_to',link),patch.dict(sys.modules,{'prepare_precise_timing':generator,'native_checks':types.SimpleNamespace(native_checks=native,native_batch_checks=native),'runtime_controls':types.SimpleNamespace(RuntimeControls=FakeControls)}):
        module.main()
    records=list(package.glob('board-comparison-*/results.json'));assert len(records)==1
    result=json.loads(records[0].read_text(encoding='utf-8'))
    assert result['preciseTimingEnabled']==precise and controls[-1].restored
    assert len(result['commands'])==4
    assert '-DFB_GEOMETRY_DSU' in result['commands']['v9-dsu']
    assert '-DFB_DISABLE_GEOMETRY_COALESCE' in result['commands']['v9-sprint']
    assert all((package/'test'/name).read_bytes()==source for name,source in sources.items())
    if precise:
        assert len(result['diagnosticCommands'])==4 and result['diagnosticTimingIsCourseScore'] is False
        assert all(metadata['originalSourceUnchanged'] for metadata in result['diagnosticSources'].values())
        for variant,cmd in result['commands'].items():
            diag=result['diagnosticCommands'][variant]
            differences=[(a,b) for a,b in zip(cmd,diag) if a!=b]
            assert len(differences)==2 and len(cmd)==len(diag)
            assert any(Path(b).name=='diagnostic-main.c' for a,b in differences)
            assert any(Path(b).name=='test-diagnostic' for a,b in differences)
    else:assert 'diagnosticCommands' not in result
    executions=[Path(cmd[0]).name for cmd in calls if Path(cmd[0]).name in ('test','test-diagnostic')]
    if build_only:assert not executions and not result['runs']
    else:
        assert len(result['runs'])==8 and all(t['medianTotalMs']==84 and not t['meets40msCourseTiming'] for t in result['targetAssessment'].values())
        assert executions==['test']*8+(['test-diagnostic']*8 if precise else [])
        if precise:
            assert len(result['diagnosticRuns'])==8 and all(not x['isCourseScore'] for x in result['diagnosticRuns'])
            assert all(x['total']==14 for x in result['diagnosticMedianMs'].values())
    logs[label]={'passed':True,'courseRuns':len(result['runs']),'diagnosticRuns':len(result.get('diagnosticRuns',[])),'record':str(records[0]),'nativeChecksMocked':True,'subprocessesMocked':True}
controls=[]
scenario('default',False,False)
scenario('precise-build-only',True,True)
scenario('precise-runs',True,False)
report={'python38Syntax':True,'strictDiagnosticParserCases':8,'scenarios':logs,'hardwareValidated':False,'performanceMeasured':False}
(ROOT/'v9-precise-runner-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: optional diagnostic parser, unchanged score isolation, four variants, flags, build-only, ordered execution, generator provenance and Python 3.8 syntax')
