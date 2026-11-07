from pathlib import Path
import argparse,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'build-v9-png';BUILD.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--cc',required=True);parser.add_argument('--cull-only',action='store_true');args=parser.parse_args()
cc=Path(args.cc);env=dict(os.environ);env['PATH']=str(cc.parent)+os.pathsep+env.get('PATH','')
source=(ROOT/'common/graphic-v8-batch.c').read_text(encoding='utf-8').replace('fast_pixels_v8.h','fast_pixels_v9.h').replace('prepared_image_v8.h','prepared_image_v9.h')
globals_=source[source.index('static int LCD_FB_FD;'):source.index('void fb_init(')]
globals_=globals_.replace('static int LCD_FB_FD;\n','').replace('static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];','static struct {int before[GUARD_WORDS];int pixels[SCREEN_WIDTH*SCREEN_HEIGHT];int after[GUARD_WORDS];} TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
(BUILD/'graphics-under-test.c').write_text('#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n'+globals_+source[source.index('static void _copy_area('):],encoding='utf-8')
(BUILD/'image-memory-under-test.c').write_bytes((ROOT/'build/image-memory-under-test.c').read_bytes())
(BUILD/'font-identity.c').write_text('const void *fb_font_identity(void){return "host-font";}\n',encoding='utf-8')
logs={}
def run(command,label):
    p=subprocess.run(list(map(str,command)),cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    logs[label]=p.stdout+p.stderr
    if p.returncode:raise RuntimeError(label+'\n'+logs[label])
    if p.stdout:print(label,p.stdout.strip(),flush=True)
base=['-std=gnu11','-O3','-Wall','-Wextra','-Werror','-static','-D__USE_MINGW_ANSI_STDIO=1','-DFB_CULL_TEST_STATS','-I',BUILD,'-I',ROOT/'common','-I',ROOT/'tests']
variants=[('scalar',[],1),('neon',['-DFB_TEST_NEON'],1),('omp2',['-DFB_TEST_NEON','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'],2),('omp4',['-DFB_TEST_NEON','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'],4),('no-four',['-DFB_TEST_NEON','-DFB_DISABLE_FOUR_LANE'],1),('no-cull',['-DFB_TEST_NEON','-DFB_DISABLE_OPAQUE_CULL'],1),('cull-spill',['-DFB_TEST_NEON','-DFB_CULL_MAX_COMMANDS=1'],1),('index-spill',['-DFB_TEST_NEON','-DFB_ROW_INDEX_LIMIT=1'],1),('index-disabled',['-DFB_TEST_NEON','-DFB_DISABLE_ROW_INDEX'],1),('no-products',['-DFB_TEST_NEON','-DFB_DISABLE_PRODUCTS'],1),('no-packed',['-DFB_TEST_NEON','-DFB_DISABLE_PACKED'],1)]
for name,flags,threads in variants:
    env['OMP_NUM_THREADS']=str(threads);env['OMP_DYNAMIC']='FALSE'
    if '-DFB_TEST_NEON' in flags:flags=flags+['-I',ROOT/'tests/neon-emulation']
    for test in (['test_v9_cull','test_prepared','test_v9_alloc'] if args.cull_only else ['test_v9_cull','test_v9_pixels','test_prepared','test_v9_alloc']):
        exe=BUILD/(name+'-'+test+'.exe')
        run([cc,*base,*flags,ROOT/'tests'/(test+'.c'),ROOT/'tests/asset_adapter.c',BUILD/'font-identity.c','-o',exe,'-lm'],name+'-'+test+'-compile')
        run([exe],name+'-'+test)
report={'hardwareValidated':False,'armNativeCompileValidated':False,'performanceMeasured':False,'neonArithmeticEmulated':True,'guardPageProtectedReads':True,'hostOMPThreads':[2,4],'sourceHashes':{f:hashlib.sha256((ROOT/'common'/f).read_bytes()).hexdigest() for f in ['fast_pixels_v9.h','prepared_image_v9.h']},'unchangedArithmeticEvidence':'v9-png-before-nonoverlap-results.json' if args.cull_only else None,'logs':logs}
(ROOT/'v9-png-offline-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
