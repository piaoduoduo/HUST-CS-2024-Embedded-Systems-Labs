"""V9 integrated host checks. Emulated NEON is never ARM or speed evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'build-v9-integrated'


def fixture():
    BUILD.mkdir(exist_ok=True)
    source=(ROOT/'common/graphic-v9-batch.c').read_text(encoding='utf-8')
    glob=source[source.index('static int LCD_FB_FD;'):source.index('void fb_init(')]
    glob=glob.replace('static int LCD_FB_FD;\n','').replace('static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];',
        'static struct {int before[GUARD_WORDS];int pixels[SCREEN_WIDTH*SCREEN_HEIGHT];int after[GUARD_WORDS];} TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
    (BUILD/'graphics-under-test.c').write_text('#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n'+glob+source[source.index('static void _copy_area('):],encoding='utf-8')
    shutil.copy2(ROOT/'build/image-memory-under-test.c',BUILD/'image-memory-under-test.c')
    (BUILD/'font-identity.c').write_text('const void *fb_font_identity(void){return "host-font";}\n',encoding='ascii')


def replay_source():
    main=(ROOT/'sprint-v9-main.c').read_text(encoding='utf-8')
    main=re.sub(r'(?m)^#include[^\n]*\n?','',main)
    prefix='''#include "fixture.h"
void fb_init(char *p){(void)p;reset_surfaces(0);}
myTime task_get_time(void){return 0;}
static unsigned stage;
static void test_update(void){fb_update();check_front_matches_back();printf("STAGE_HASH %u %016llx\\n",stage++,(unsigned long long)front_hash());}
#define fb_update test_update
#define sleep(n) ((void)0)
#define main course_main
'''
    suffix='''
#undef main
#undef fb_update
int main(void){int result=course_main(0,NULL);require(result==0,"course replay return");check_canaries();free(front_storage);return result;}
'''
    path=BUILD/'sprint-v9-replay.c';path.write_text(prefix+main+suffix,encoding='utf-8')
    return path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc',required=True)
    parser.add_argument('--only',default='',help='Comma-separated configurations, empty means all')
    parser.add_argument('--replay-only',action='store_true')
    args=parser.parse_args()
    fixture();replay=replay_source()
    configurations=[
        ('scalar',[],1),
        ('neon',['FB_TEST_NEON'],1),
        ('omp2',['FB_TEST_NEON','OPENMP'],2),
        ('omp4',['FB_TEST_NEON','OPENMP'],4),
        ('four-disabled',['FB_TEST_NEON','FB_DISABLE_FOUR_LANE'],1),
        ('cull-disabled',['FB_TEST_NEON','FB_DISABLE_OPAQUE_CULL'],1),
        ('text-disabled',['FB_TEST_NEON','FB_DISABLE_TEXT_BATCH'],1),
        ('geometry-disabled',['FB_TEST_NEON','FB_DISABLE_GEOMETRY_BATCH'],1),
        ('analytic-disabled',['FB_TEST_NEON','FB_DISABLE_ANALYTIC_LINES'],1),
        ('geometry-dsu',['FB_TEST_NEON','FB_GEOMETRY_DSU','OPENMP'],2),
        ('products-disabled',['FB_TEST_NEON','FB_DISABLE_PRODUCTS','OPENMP'],2),
        ('small-capacity',['FB_TEST_NEON','FB_GEOMETRY_BATCH_CAPACITY=7','FB_TEXT_BATCH_CAPACITY=3','FB_CULL_MAX_COMMANDS=1','OPENMP'],4),
        ('row-index-disabled',['FB_TEST_NEON','FB_DISABLE_ROW_INDEX','OPENMP'],2),
        ('new-disabled',['FB_TEST_NEON','FB_DISABLE_FOUR_LANE','FB_DISABLE_OPAQUE_CULL','FB_DISABLE_TEXT_BATCH','FB_DISABLE_GEOMETRY_BATCH'],1),
        ('lto-no-stats',['FB_TEST_NEON','FB_DISABLE_STATS','OPENMP','LTO'],2),
        ('coalesce-disabled',['FB_TEST_NEON','FB_DISABLE_GEOMETRY_COALESCE','OPENMP'],2),
    ]
    if args.only:
        selected=args.only.split(',');configurations=[x for x in configurations if x[0] in selected]
        assert len(configurations)==len(set(selected)), 'Unknown configuration'
    env=dict(os.environ);env['PATH']=str(Path(args.cc).parent)+os.pathsep+env.get('PATH','')
    env['OMP_DYNAMIC']='FALSE'
    base=[args.cc,'-std=gnu11','-O3','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-D__USE_MINGW_ANSI_STDIO=1','-static',
          '-I',str(BUILD),'-I',str(ROOT/'common'),'-I',str(ROOT/'tests'),'-I',str(ROOT/'tests/neon-emulation')]
    logs={};hashes={};source_hashes={}
    expected=json.loads((ROOT/'v8-replay-results.json').read_text(encoding='utf-8'))['hashes']['original']
    for config,defines,threads in configurations:
        env['OMP_NUM_THREADS']=env['OMP_THREAD_LIMIT']=str(threads)
        flags=['-D'+x for x in defines if x not in ('OPENMP','LTO')]
        if 'OPENMP' in defines:flags+=['-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1']
        if 'LTO' in defines:flags+=['-flto']
        tests=[] if args.replay_only else ['test_images','test_prepared','test_v8_arithmetic','test_v8_product_storage',
                                         'test_v9_pixels','test_v9_cull','test_v9_alloc','test_v9_text_batch','test_v9_geometry']
        if config in ('scalar','neon','omp2','omp4') and not args.replay_only:
            tests+=['test_v9_rows','test_lab2_regression','test_line_exact','test_text_layout_v4','test_opaque_batch']
        for name in tests+['sprint-v9-replay']:
            src=replay if name=='sprint-v9-replay' else ROOT/'tests'/(name+'.c')
            assert src.exists(), src
            sources=[str(src)]
            # Synthetic text tests own their image allocation and font provider.
            if name not in ('test_v9_text_batch','test_text_layout_v4','test_v9_rows'):
                sources += [str(ROOT/'tests/asset_adapter.c'),str(BUILD/'font-identity.c')]
            exe=BUILD/(config+'-'+name+'.exe')
            testflags=(['-DFB_USE_REAL_IMAGE'] if name=='test_line_exact' else [])+(['-DFB_CULL_TEST_STATS'] if name=='test_v9_cull' else [])
            command=base+flags+testflags+sources+['-o',str(exe),'-lm']
            compiled=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
            logs[config+'-'+name+'-compile']=compiled.stdout+compiled.stderr
            if compiled.returncode:raise RuntimeError(logs[config+'-'+name+'-compile'])
            run=subprocess.run([str(exe)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
            logs[config+'-'+name]=run.stdout+run.stderr
            if run.returncode:raise RuntimeError(config+' '+name+'\n'+logs[config+'-'+name])
            if name=='sprint-v9-replay':
                found=[list(x) for x in re.findall(r'STAGE_HASH (\d+) ([0-9a-f]+)',run.stdout)]
                assert found==expected,(config,found,expected)
                hashes[config]=found
            print(config,name,'PASS',flush=True)
            source_hashes[str(src.relative_to(ROOT))]=hashlib.sha256(src.read_bytes()).hexdigest()
    for path in (ROOT/'common').glob('*v9*'):
        source_hashes[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    report={'passed':True,'configurations':[x[0] for x in configurations], 'logs':logs,'replayHashes':hashes,
            'nineStagesMatchPreservedV8Baseline':True,'sourceHashes':source_hashes,
            'hardwareValidated':False,'armNativeCompileValidated':False,'performanceMeasured':False,
            'neonEmulated':True,'fontSimulation':'Pillow or synthetic mocks; no native FreeType',
            'replayClockAlwaysZero':True,'replaySleepsDisabled':True}
    suffix=('-'+args.only.replace(',','_')) if args.only else ''
    if args.replay_only:suffix+='-replay'
    reportpath=ROOT/('v9-integrated-results'+suffix+'.json')
    reportpath.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS integrated v9; no hardware speed claim:',reportpath)


if __name__=='__main__':main()
