"""Text batch correctness only; host elapsed times are not board benchmarks."""
from pathlib import Path
import argparse, json, os, subprocess
ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'build-v9-text';BUILD.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--cc',required=True);p.add_argument('--pixels-v9',action='store_true');args=p.parse_args()
cc=Path(args.cc);env=dict(os.environ);env['PATH']=str(cc.parent)+os.pathsep+env.get('PATH','')
source=(ROOT/'common/graphic-v8-batch.c').read_text(encoding='utf-8')
source=source.replace('#include "text_layout_v5.h"','#include "text_layout_v5.h"\n#include "text_batch_v9.h"')
if args.pixels_v9:source=source.replace('fast_pixels_v8.h','fast_pixels_v9.h')
globals_=source[source.index('static int LCD_FB_FD;'):source.index('void fb_init(')]
globals_=globals_.replace('static int LCD_FB_FD;\n','').replace('static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];',
 'static struct {int before[GUARD_WORDS];int pixels[SCREEN_WIDTH*SCREEN_HEIGHT];int after[GUARD_WORDS];} TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
(BUILD/'graphics-under-test.c').write_text('#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n'+globals_+source[source.index('static void _copy_area('):],encoding='utf-8')
im=(ROOT/'common/image-fast.c').read_text(encoding='utf-8')
(BUILD/'image-memory-under-test.c').write_text('#include <limits.h>\n'+im[im.index('/*w, h maybe == 0*/'):im.index('/*================== read a jpeg image')],encoding='utf-8')
base=['-std=gnu11','-O3','-Wall','-Wextra','-Werror','-static','-D__USE_MINGW_ANSI_STDIO=1','-I',BUILD,'-I',ROOT/'common','-I',ROOT/'tests']
variants=[('scalar',[],1),('neon-emulated',['-DFB_TEST_NEON'],1),('openmp-2',['-DFB_TEST_NEON','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'],2),('openmp-4',['-DFB_TEST_NEON','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'],4),
 ('batch-disabled',['-DFB_DISABLE_TEXT_BATCH'],1),('capacity-3',['-DFB_TEXT_BATCH_CAPACITY=3','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'],2),('layout-capacity-2',['-DFB_TEXT_BATCH_LAYOUTS=2'],1),('row-limit-1',['-DFB_TEXT_BATCH_ROW_LIMIT=1'],1),('bytes-limit-1',['-DFB_TEXT_BATCH_MAX_BYTES=1'],1),('ranges-disabled',['-DFB_DISABLE_TEXT_RANGES'],1)]
logs={}
for name,extra,threads in variants:
    env['OMP_NUM_THREADS']=str(threads);env['OMP_DYNAMIC']='FALSE'
    if '-DFB_TEST_NEON' in extra:extra=extra+['-I',ROOT/'tests/neon-emulation']
    exe=BUILD/(name+'-text.exe')
    for label,cmd in [(name+'-compile',[cc,*base,*extra,ROOT/'tests/test_v9_text_batch.c','-o',exe,'-lm']),(name,[exe])]:
        r=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
        logs[label]=r.stdout+r.stderr
        if r.returncode:raise RuntimeError(label+'\n'+logs[label])
        if r.stdout:print(label,r.stdout.strip())
report={'scope':'ordered multi-string multi-glyph CSR text batching','pixelsKernel':'v9' if args.pixels_v9 else 'v8','logs':logs,'syntheticGlyphs':True,'wholeFrameDirtyAndCanariesValidated':True,'allocationFailureFallbackValidated':True,'ownedGlyphCacheEvictionAndInputMutationValidated':True,'hostOpenMPThreadsValidated':[2,4],'realFreeTypeValidated':False,'armNativeCompileValidated':False,'neonInstructionsExecuted':False,'performanceMeasured':False}
(ROOT/'v9-text-offline-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
