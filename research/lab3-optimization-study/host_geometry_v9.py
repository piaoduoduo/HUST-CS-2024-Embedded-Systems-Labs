from pathlib import Path
import argparse,json,os,subprocess
ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'build-v9-geometry';BUILD.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--cc',required=True);args=p.parse_args()
cc=Path(args.cc);env=dict(os.environ);env['PATH']=str(cc.parent)+os.pathsep+env.get('PATH','')
source=(ROOT/'common/graphic-v8-batch.c').read_text(encoding='utf-8')
globals_=source[source.index('static int LCD_FB_FD;'):source.index('void fb_init(')]
globals_=globals_.replace('static int LCD_FB_FD;\n','').replace('static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];',
 'static struct {int before[GUARD_WORDS];int pixels[SCREEN_WIDTH*SCREEN_HEIGHT];int after[GUARD_WORDS];} TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
(BUILD/'graphics-under-test.c').write_text('#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n'+globals_+source[source.index('static void _copy_area('):]+'\n#include "geometry_batch_v9.h"\n',encoding='utf-8')
(BUILD/'font-identity.c').write_text('const void *fb_font_identity(void){return "host-font";}\n',encoding='utf-8')
image=(ROOT/'common/image-fast.c').read_text(encoding='utf-8')
memory=image[image.index('/*w, h maybe == 0*/'):image.index('/*================== read a jpeg image')]
(BUILD/'image-memory-under-test.c').write_text('#include <limits.h>\n'+memory,encoding='utf-8')
logs={}
base=['-std=gnu11','-O3','-Wall','-Wextra','-Werror','-D__USE_MINGW_ANSI_STDIO=1','-static','-I',BUILD,'-I',ROOT/'common','-I',ROOT/'tests']
variants=[('bitset-scalar',[],1),('bitset-neon',['-DFB_TEST_NEON'],1),('bitset-omp2',['-DFB_TEST_NEON','-fopenmp'],2),('bitset-omp4',['-DFB_TEST_NEON','-fopenmp'],4),
('dsu-scalar',['-DFB_GEOMETRY_DSU'],1),('dsu-omp2',['-DFB_GEOMETRY_DSU','-fopenmp'],2),('dsu-omp4',['-DFB_GEOMETRY_DSU','-fopenmp'],4),
('small-command-capacity',['-DFB_GEOMETRY_BATCH_CAPACITY=3'],1),('small-span-capacity',['-DFB_GEOMETRY_SPAN_LIMIT=7'],1),
('index-allocation-fallback',['-DFB_GEOMETRY_FAIL_INDEX'],1),('bounded-raster-fallback',['-DFB_DISABLE_ANALYTIC_LINES'],1),('coalesce-disabled',['-DFB_DISABLE_GEOMETRY_COALESCE'],1),
('disabled',['-DFB_DISABLE_GEOMETRY_BATCH'],1),('production-no-stats',['-DFB_DISABLE_STATS','-DFB_TEST_NEON','-fopenmp'],2),('host-lto',['-flto','-DFB_TEST_NEON','-fopenmp'],2)]
for name,extra,threads in variants:
    env['OMP_NUM_THREADS']=str(threads);env['OMP_DYNAMIC']='FALSE'
    if '-DFB_TEST_NEON' in extra:extra+=['-I',ROOT/'tests/neon-emulation']
    exe=BUILD/(name+'.exe')
    for label,command in [('compile',[cc,*base,*extra,ROOT/'tests/test_v9_geometry.c',ROOT/'tests/asset_adapter.c',BUILD/'font-identity.c','-o',exe,'-lm']),('test',[exe])]:
        r=subprocess.run(list(map(str,command)),cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        logs[name+'-'+label]=r.stdout+r.stderr
        if r.returncode:raise RuntimeError(name+'-'+label+'\n'+logs[name+'-'+label])
        if r.stdout:print(name,r.stdout.strip(),flush=True)
report={'hardwareValidated':False,'performanceMeasured':False,'armNativeCompileValidated':False,'neonInstructionExecutionValidated':False,
        'scope':'exact geometry, all octants, int32 extremes, full-color/alpha replacement, ordered mixed shapes, allocation failure, capacity, course workload, dirty bounds/canaries',
        'logs':logs,'ompThreads':[1,2,4],'bitsetAndDSU':True}
(ROOT/'v9-geometry-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
