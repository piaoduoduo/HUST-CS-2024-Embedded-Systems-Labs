"""Host exactness gates, including NEON emulation; no ARM timing claim."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
PKG=WS/'lab3-optimized-v10-prepared';STUDY=WS/'lab3-optimization-study'
BUILD=ROOT/'build';BUILD.mkdir(exist_ok=True)
shutil.copy2(WS/'lab3-v10-study/build/graphics-under-test.c',BUILD/'graphics-under-test.c')
shutil.copy2(STUDY/'build/image-memory-under-test.c',BUILD/'image-memory-under-test.c')
(BUILD/'font-identity.c').write_text('const void *fb_font_identity(void){return "host-font";}\n',encoding='ascii')
cc=sys.argv[1];env=dict(os.environ);env['PATH']=str(Path(cc).parent)+os.pathsep+env.get('PATH','')
env['OMP_NUM_THREADS']=env['OMP_THREAD_LIMIT']='2'
expected=json.loads((STUDY/'v8-replay-results.json').read_text(encoding='utf-8'))['hashes']['original']
configs={'scalar':[], 'packed-four':['-DFB_TEST_NEON'],
 'old-four':['-DFB_TEST_NEON','-DFB_DISABLE_PACKED_FOUR'],
 'old-round':['-DFB_TEST_NEON','-DFB_DISABLE_SHORT_ROUND'],
 'no-products':['-DFB_TEST_NEON','-DFB_DISABLE_PRODUCTS'],
 'lto-omp2':['-DFB_TEST_NEON','-flto','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1']}
logs={}
for name,flags in configs.items():
    for test in ('test_v9_pixels','test_v9_rows','test_v9_cull','test_v9_text_batch','test_sprint_v10_replay'):
        src=PKG/'tests'/(test+'.c');exe=BUILD/(name+'-'+test+'.exe')
        adapter=[] if test=='test_v9_text_batch' else [str(STUDY/'tests/asset_adapter.c'),str(BUILD/'font-identity.c')]
        cmd=[cc,'-std=gnu11','-O3','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-static',
             '-D__USE_MINGW_ANSI_STDIO=1','-DFB_CULL_TEST_STATS',*flags,
             '-I'+str(BUILD),'-I'+str(ROOT/'candidate/common'),'-I'+str(PKG/'tests'),
             '-I'+str(ROOT/'candidate/neon-emulation'),str(src),*adapter,'-o',str(exe),'-lm']
        r=subprocess.run(cmd,cwd=STUDY,env=env,capture_output=True,text=True,timeout=120)
        assert r.returncode==0,r.stdout+r.stderr
        r=subprocess.run([str(exe)],cwd=STUDY,env=env,capture_output=True,text=True,timeout=120)
        assert r.returncode==0,r.stdout+r.stderr
        logs[name+'/'+test]=r.stdout+r.stderr
        if test=='test_sprint_v10_replay':
            assert [list(x) for x in re.findall(r'STAGE_HASH (\d+) ([0-9a-f]+)',r.stdout)]==expected
        print(name,test,'PASS',flush=True)
preserved=json.loads((ROOT/'preserved.json').read_text(encoding='utf-8'))
for p,h in preserved.items():assert hashlib.sha256((WS/p).read_bytes()).hexdigest()==h,p
report={'passed':True,'hostOnly':True,'neonEmulated':True,'armCompiled':False,'boardMeasured':False,
        'nineStagesEqual':True,'productionAndPublicPreserved':True,'logs':logs}
(ROOT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS: 30 gates; all production/public files preserved')
