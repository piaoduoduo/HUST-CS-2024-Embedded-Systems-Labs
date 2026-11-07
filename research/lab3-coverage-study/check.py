from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent;WS=ROOT.parent;PKG=WS/'lab3-optimized-v10-prepared';STUDY=WS/'lab3-optimization-study'
BUILD=ROOT/'build';BUILD.mkdir(exist_ok=True);cc=sys.argv[1]
for name,source in [('graphics-under-test.c',WS/'lab3-v10-study/build/graphics-under-test.c'),('image-memory-under-test.c',STUDY/'build/image-memory-under-test.c')]:shutil.copy2(source,BUILD/name)
(BUILD/'font-identity.c').write_text('const void *fb_font_identity(void){return "host-font";}\n',encoding='ascii')
env=dict(os.environ);env['PATH']=str(Path(cc).parent)+os.pathsep+env.get('PATH','');env['OMP_NUM_THREADS']=env['OMP_THREAD_LIMIT']='2'
base=[cc,'-std=gnu11','-O3','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-static','-D__USE_MINGW_ANSI_STDIO=1',
 '-I'+str(BUILD),'-I'+str(ROOT/'candidate/common'),'-I'+str(PKG/'tests'),'-I'+str(WS/'lab3-shortspan-study/candidate/neon-emulation')]
adapter=[str(STUDY/'tests/asset_adapter.c'),str(BUILD/'font-identity.c')]
def run(src,name,flags=(),extra=(),args=()):
    exe=BUILD/(name+'.exe');cmd=[*base,*flags,str(src),*extra,'-o',str(exe),'-lm']
    r=subprocess.run(cmd,env=env,cwd=STUDY,capture_output=True,text=True,timeout=120);assert r.returncode==0,r.stdout+r.stderr
    r=subprocess.run([str(exe),*args],env=env,cwd=STUDY,capture_output=True,text=True,timeout=120);assert r.returncode==0,r.stdout+r.stderr
    print(name,'PASS',flush=True);return r.stdout+r.stderr
expected=json.loads((STUDY/'v8-replay-results.json').read_text(encoding='utf-8'))['hashes']['original'];logs={}
configs=[('interval',[]),('fast',['-DFB_OPAQUE_FAST']),('fast-switch1',['-DFB_OPAQUE_FAST','-DFB_OPAQUE_SWITCH_INTERVALS=1']),('adaptive',['-DFB_OPAQUE_ADAPTIVE']),('adaptive-switch1',['-DFB_OPAQUE_ADAPTIVE','-DFB_OPAQUE_SWITCH_INTERVALS=1']),('bitset',['-DFB_OPAQUE_BITSET']),('bitset-small',['-DFB_OPAQUE_BITSET','-DFB_BATCH_CAPACITY=7']),
         ('fast-lto-omp2',['-DFB_OPAQUE_FAST','-DFB_TEST_NEON','-flto','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'])]
if '--widths-only' in sys.argv:
    logs=json.loads((ROOT/'validation.json').read_text(encoding='utf-8'))['logs'];configs=[]
for name,flags in configs:
    for test in ('test_opaque_batch','test_sprint_v10_replay'):
        src=STUDY/'tests/test_opaque_batch.c' if test=='test_opaque_batch' else PKG/'tests'/f'{test}.c'
        out=run(src,name+'-'+test,flags,adapter);logs[name+'/'+test]=out
        if test=='test_sprint_v10_replay':assert [list(x) for x in re.findall(r'STAGE_HASH (\d+) ([0-9a-f]+)',out)]==expected
for width in (1,63,64,65,127,1024,1031):
    logs['width-'+str(width)]=run(ROOT/'test_widths.c','width-'+str(width),['-DSCREEN_WIDTH='+str(width)])
for p,h in json.loads((ROOT/'preserved.json').read_text(encoding='utf-8')).items():assert hashlib.sha256((WS/p).read_bytes()).hexdigest()==h,p
(ROOT/'validation.json').write_text(json.dumps({'passed':True,'boardMeasured':False,'armCompiled':False,'allStageHashesEqual':True,'productionPublicPreserved':True,'logs':logs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS: full rendering and width-boundary gates')
