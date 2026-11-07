"""Integration gates for v10; host rendering and mocked board plans only."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,tempfile,types
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
PKG=WS/'lab3-optimized-v10-prepared';STUDY=WS/'lab3-optimization-study'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def c_tests(cc):
    build=ROOT/'build';build.mkdir(exist_ok=True)
    text=(PKG/'common/graphic-v10-batch.c').read_text(encoding='utf-8')
    glob=text[text.index('static int LCD_FB_FD;'):text.index('void fb_init(')]
    glob=glob.replace('static int LCD_FB_FD;\n','').replace('static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];',
        'static struct {int before[GUARD_WORDS];int pixels[SCREEN_WIDTH*SCREEN_HEIGHT];int after[GUARD_WORDS];} TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
    (build/'graphics-under-test.c').write_text('#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n'+glob+text[text.index('static void _copy_area('):],encoding='utf-8')
    shutil.copy2(STUDY/'build/image-memory-under-test.c',build/'image-memory-under-test.c')
    (build/'font-identity.c').write_text('const void *fb_font_identity(void){return "host-font";}\n',encoding='ascii')
    env=dict(os.environ);env['PATH']=str(Path(cc).parent)+os.pathsep+env.get('PATH','')
    env['OMP_NUM_THREADS']=env['OMP_THREAD_LIMIT']='2'
    expected=json.loads((STUDY/'v8-replay-results.json').read_text(encoding='utf-8'))['hashes']['original']
    logs={};stagehashes={}
    configs=[('v10-default',[]),('v10-unsigned',['FB_PIXEL_MODE=1']),('v10-minmax',['FB_PIXEL_MODE=3']),
             ('v10-disabled',['FB_DISABLE_PIXEL_FAST']),('v10-lto-neon-omp2',['FB_TEST_NEON','OMP','LTO'])]
    for name,defines in configs:
        flags=['-D'+x for x in defines if x not in ('OMP','LTO')]
        if 'OMP' in defines:flags+=['-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1']
        if 'LTO' in defines:flags+=['-flto']
        for test in ('test_pixel_candidate','test_lab2_regression','test_sprint_v10_replay'):
            src=PKG/'tests'/(test+'.c');exe=build/(name+'-'+test+'.exe')
            command=[cc,'-std=gnu11','-O3','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-static','-D__USE_MINGW_ANSI_STDIO=1',*flags,
                     '-I'+str(build),'-I'+str(PKG/'common'),'-I'+str(PKG/'tests'),'-I'+str(STUDY/'tests/neon-emulation'),
                     str(src),str(STUDY/'tests/asset_adapter.c'),str(build/'font-identity.c'),'-o',str(exe),'-lm']
            compiled=subprocess.run(command,cwd=STUDY,env=env,capture_output=True,text=True,timeout=120)
            logs[name+'-'+test+'-compile']=compiled.stdout+compiled.stderr
            assert compiled.returncode==0,compiled.stdout+compiled.stderr
            run=subprocess.run([str(exe)],cwd=STUDY,env=env,capture_output=True,text=True,timeout=120)
            logs[name+'-'+test]=run.stdout+run.stderr;assert run.returncode==0,run.stdout+run.stderr
            if test=='test_sprint_v10_replay':
                found=[list(x) for x in re.findall(r'STAGE_HASH (\d+) ([0-9a-f]+)',run.stdout)]
                assert found==expected,(name,found);stagehashes[name]=found
            print(name,test,'PASS',flush=True)
    return {'configurations':[x[0] for x in configs],'logs':logs,'stageHashes':stagehashes,'allNineStageHashesEqual':True}

def runner_tests():
    source=(STUDY/'test_v9_precise_runner.py').read_text(encoding='utf-8')
    source=source.replace('ROOT=Path(__file__).resolve().parent','ROOT=Path('+repr(str(STUDY))+')')
    source=source.replace("RUNNER=ROOT.parent/'lab3-optimized-prepared/board_compare.py'", "RUNNER=ROOT.parent/'lab3-optimized-v10-prepared/board_compare.py'")
    source=source.replace("BUILD=ROOT/'build-v9-timing-tests'", "BUILD=ROOT.parent/'lab3-v10-study/build-runner'")
    source=source.replace('baseline,v8-sprint,v9-sprint,v9-dsu','v9-sprint,v10-sprint,v10-unsigned,v10-minmax')
    source=source.replace("'--disable','geometry-coalesce'", "'--disable','pixel','--native-cpu'")
    marker="    for path in (ROOT/'common').glob('*.h')"
    source=source.replace(marker,"    sources['sprint-v10-main.c']=(ROOT.parent/'lab3-optimized-v10-prepared/test/sprint-v10-main.c').read_bytes()\n"+marker)
    source=source.replace("    assert '-DFB_GEOMETRY_DSU' in result['commands']['v9-dsu']", "    for mode,name in ((2,'sprint'),(1,'unsigned'),(3,'minmax')):\n        cmd=result['commands']['v10-'+name]\n        assert '-DFB_PIXEL_MODE='+str(mode) in cmd\n        assert '-fopenmp' in cmd and '-flto' in cmd and '-mcpu=native' in cmd\n        assert any(Path(x).name=='image-fast.c' for x in cmd)\n        assert any(Path(x).name=='sprint-v10-main.c' for x in cmd)\n        assert '-DFB_DISABLE_PIXEL_FAST' in cmd")
    source=source.replace("    assert '-DFB_DISABLE_GEOMETRY_COALESCE' in result['commands']['v9-sprint']", "    assert '-DFB_DISABLE_PIXEL_FAST' in result['commands']['v9-sprint']")
    source=source.replace("(ROOT/'v9-precise-runner-results.json')", "(ROOT.parent/'lab3-v10-study/runner-results.json')")
    namespace={'__name__':'__main__','__file__':str(ROOT/'adapted-runner.py')}
    exec(compile(source,str(ROOT/'adapted-runner.py'),'exec'),namespace)
    for wrapper,expected in [('run-sprint.py','baseline,v9-sprint,v10-sprint,v10-unsigned,v10-minmax'),
                             ('run-pixel-compare.py','v9-sprint,v10-sprint,v10-unsigned,v10-minmax')]:
        import runpy
        for options in ([],['--build-only','--precise-timing','--runs','3']):
            calls=[]
            with patch.object(sys,'argv',[wrapper,'--project','COURSE']+options),patch.object(subprocess,'call',side_effect=lambda cmd:calls.append(cmd) or 0):
                try:runpy.run_path(str(PKG/wrapper),run_name='__main__')
                except SystemExit as result:assert result.code==0
            assert len(calls)==1;cmd=calls[0]
            assert cmd[cmd.index('--variants')+1]==expected
            assert ('--build-only' in cmd)==('--build-only' in options)
            assert ('--precise-timing' in cmd)==('--precise-timing' in options)
    return {'mockScenariosPassed':True,'wrapperDefaultsAndForwardingPassed':True,'realBoardExecution':False}

def native_plan_tests():
    module=load('v10_native_plan',PKG/'native_checks.py')
    build=ROOT/'build-native';build.mkdir(exist_ok=True)
    calls=[]
    def fake(command,**kwargs):
        args=list(map(str,command));calls.append(args)
        if args[0]=='gcc':
            for x in args:
                if x.endswith('.c'):assert Path(x).is_file(),x
            output=''
        else:output=''.join('STAGE_HASH %d %016x\n'%(i,i) for i in range(9))
        return subprocess.CompletedProcess(args,0,output,'')
    with tempfile.TemporaryDirectory(dir=build) as folder:
        record=Path(folder);project=WS/'course-source/lab-st-2026'
        flags=['-O3','-flto','-fopenmp','-DFB_PIXEL_MODE=2']
        with patch.object(module.subprocess,'run',side_effect=fake):
            first=module.native_checks(project,record,dict(os.environ),'graphic-v10-batch.c',flags)
            second=module.native_batch_checks(project,record,dict(os.environ),'graphic-v10-batch.c',flags)
        assert 'test_pixel_candidate-1' in first
        assert any('test_v9_text_real' in x for x in first)
        assert any('test_sprint_v10_replay' in x for x in second)
        assert any(any(x.endswith('/image-fast.c') or x.endswith('\\image-fast.c') for x in cmd) for cmd in calls if cmd[0]=='gcc')
    return {'nativePointGateSelected':True,'realFontAndV10FullReplaySelected':True,'allReferencedSourcesExist':True,'realARMCompileRun':False}

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cc',required=True);args=p.parse_args()
    integration=json.loads((ROOT/'integration.json').read_text(encoding='utf-8'))
    assert integration['graphicSHA256']==sha(PKG/'common/graphic-v10-batch.c')
    assert integration['headerSHA256']==sha(PKG/'common/pixel_fast_v10.h')
    report={'passed':False,'hardwareValidated':False,'armNativeCompileValidated':False,'boardPerformanceMeasured':False}
    report['rendering']=c_tests(args.cc)
    report['runner']=runner_tests();report['nativePlan']=native_plan_tests()
    for path in PKG.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'),feature_version=(3,8))
    report.update({'passed':True,'python38Syntax':True,'graphicSHA256':integration['graphicSHA256'],'headerSHA256':integration['headerSHA256']})
    (ROOT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS v10 integration gates; host drawing and mocked board planning only')

if __name__=='__main__':main()
