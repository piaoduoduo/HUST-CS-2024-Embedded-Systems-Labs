from pathlib import Path
import argparse,json,os,re,subprocess
ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'build';BUILD.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--cc',required=True);p.add_argument('--v4',action='store_true');p.add_argument('--v7',action='store_true');args=p.parse_args()
cc=Path(args.cc);env=dict(os.environ);env['PATH']=str(cc.parent)+os.pathsep+env.get('PATH','')
source=(ROOT/'common'/('graphic-v7-batch.c' if args.v7 else 'graphic-v4.c' if args.v4 else 'graphic-fast.c')).read_text(encoding='utf-8')
globals_=source[source.index('static int LCD_FB_FD;'):source.index('void fb_init(')]
globals_=globals_.replace('static int LCD_FB_FD;\n','').replace('static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];',
 'static struct {int before[GUARD_WORDS];int pixels[SCREEN_WIDTH*SCREEN_HEIGHT];int after[GUARD_WORDS];} TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
(BUILD/'graphics-under-test.c').write_text('#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n'+globals_+source[source.index('static void _copy_area('):],encoding='utf-8')
(BUILD/'font-identity.c').write_text('const void *fb_font_identity(void){return "host-font";}\n')
logs={}
def run(command,label):
    r=subprocess.run(list(map(str,command)),cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    logs[label]=r.stdout+r.stderr
    if r.returncode:raise RuntimeError(label+'\n'+logs[label])
    if r.stdout:print(label,r.stdout.strip())
    return r.stdout
base=['-std=gnu11','-O3','-Wall','-Wextra','-Werror','-static','-I',BUILD,'-I',ROOT/'common','-I',ROOT/'tests']
variants=[('scalar',[],1),('neon-emulated',['-DFB_TEST_NEON'],1),
                           ('parallel-neon-2',['-DFB_TEST_NEON','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'],2),
                           ('parallel-neon-4',['-DFB_TEST_NEON','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'],4)]
variants+=[('many-disabled',['-DFB_TEST_NEON','-DFB_DISABLE_MANY','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'],2)]
variants+=[('row-index-disabled',['-DFB_TEST_NEON','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1','-DFB_DISABLE_ROW_INDEX'],2),('row-index-spill',['-DFB_TEST_NEON','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1','-DFB_ROW_INDEX_LIMIT=1'],4)]
if args.v7:variants+=[('ablated',['-DFB_DISABLE_NEON','-DFB_DISABLE_LINE_FAST','-DFB_DISABLE_RECT_FAST','-DFB_DISABLE_TEXT_RANGES','-DFB_DISABLE_PREPARED','-DFB_DISABLE_STATS'],1)]
for name,extra,threads in variants:
    env['OMP_NUM_THREADS']=str(threads);env['OMP_DYNAMIC']='FALSE'
    if '-DFB_TEST_NEON' in extra:extra=extra+['-I',ROOT/'tests/neon-emulation']
    # Only the private prepared scheduling header changed; v6 retains the
    # independent geometry/layout/SIMD exhaustive regression evidence.
    tests=['test_images','test_prepared','test_opaque_batch']
    for test in tests:
        exe=BUILD/(name+'-'+test+'.exe')
        sources=[ROOT/'tests'/(test+'.c')]
        flags=[]
        if test in ('test_lab2_regression','test_images','test_prepared','test_opaque_batch') or (args.v7 and test=='test_line_exact'):
            sources += [ROOT/'tests/asset_adapter.c',BUILD/'font-identity.c']
        if args.v7 and test=='test_line_exact':flags+=['-DFB_USE_REAL_IMAGE']
        if args.v7:flags+=['-D__USE_MINGW_ANSI_STDIO=1']
        run([cc,*base,*extra,*flags,*sources,'-o',exe,'-lm'],name+'-'+test+'-compile')
        run([exe],name+'-'+test)
report={'regressionScope':['images','prepared-ordered-many','opaque-batch'], 'unchangedKernelExhaustiveEvidence':'v6-offline-results.json','logs':logs,'hardwareValidated':False,'armNativeCompileValidated':False,
        'neonInstructionExecutionValidated':False,'neonLaneArithmeticEmulated':True,
        'hostOpenMPThreadsValidated':[2,4],'realFreeTypeTextCacheValidated':False,
        'performanceMeasured':False}
(ROOT/('v7-offline-results.json' if args.v7 else 'v4-offline-results.json' if args.v4 else 'fast-offline-results.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
