"""Full course replay for equality only: host assets, no sleeps, fake time. NOT a speed benchmark."""
from pathlib import Path
import argparse,json,os,re,shutil,subprocess
ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'build-batch'
p=argparse.ArgumentParser();p.add_argument('--cc',required=True);p.add_argument('--v4',action='store_true');p.add_argument('--v8',action='store_true');p.add_argument('--disable',default='');args=p.parse_args()
cc=Path(args.cc);env=dict(os.environ);env['PATH']=str(cc.parent)+os.pathsep+env.get('PATH','')
env['OMP_NUM_THREADS']='4';env['OMP_DYNAMIC']='FALSE'
shutil.copytree(ROOT.parent/'labs3-5-prepared/build/assets',ROOT/'build/assets',dirs_exist_ok=True)
logs={};hashes={}
if args.v8:
    source=(ROOT/'common/graphic-v8-batch.c').read_text(encoding='utf-8')
    globals_=source[source.index('static int LCD_FB_FD;'):source.index('void fb_init(')]
    globals_=globals_.replace('static int LCD_FB_FD;\n','').replace('static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];',
      'static struct {int before[GUARD_WORDS];int pixels[SCREEN_WIDTH*SCREEN_HEIGHT];int after[GUARD_WORDS];} TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
    (BUILD/'graphics-under-test.c').write_text('#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n'+globals_+source[source.index('static void _copy_area('):],encoding='utf-8')
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
variants=[('original',ROOT.parent/'lab3-prepared/test/main.c'),('batch',ROOT/'batch-main.c')]
if args.v8:variants+=[('sprint',ROOT/'sprint-v6-main.c')]
for variant,path in variants:
    source=path.read_text(encoding='utf-8')
    source=re.sub(r'(?m)^#include[^\n]*\n?','',source)
    replay=BUILD/(variant+'-replay.c');replay.write_text(prefix+source+suffix,encoding='utf-8')
    exe=BUILD/(variant+'-replay.exe')
    command=[cc,'-std=gnu11','-D__USE_MINGW_ANSI_STDIO=1','-O3','-Wall','-Wextra','-Wno-unused-parameter','-Werror','-static',
      '-fopenmp','-DFB_TEST_NEON','-I',ROOT/'tests/neon-emulation','-I',BUILD,'-I',ROOT/'common','-I',ROOT/'tests',
      replay,ROOT/'tests/asset_adapter.c',BUILD/'font-identity.c','-o',exe,'-lm']
    flags={'line':'FB_DISABLE_LINE_FAST','rect':'FB_DISABLE_RECT_FAST','text-ranges':'FB_DISABLE_TEXT_RANGES','prepared':'FB_DISABLE_PREPARED','neon':'FB_DISABLE_NEON','stats':'FB_DISABLE_STATS','many':'FB_DISABLE_MANY','row-index':'FB_DISABLE_ROW_INDEX','packed':'FB_DISABLE_PACKED','products':'FB_DISABLE_PRODUCTS'}
    if args.disable:command+=['-D'+flags[k] for k in args.disable.split(',')]
    build=subprocess.run(list(map(str,command)),cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
    assert build.returncode==0,build.stdout+build.stderr
    run=subprocess.run([str(exe)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
    logs[variant]=run.stdout+run.stderr
    assert run.returncode==0,logs[variant]
    hashes[variant]=re.findall(r'STAGE_HASH (\d+) ([0-9a-f]+)',run.stdout)
assert len(hashes['original'])==9,hashes
assert hashes['original']==hashes['batch'],hashes
if args.v8:assert hashes['sprint']==hashes['original'],hashes
if args.v4 or args.v8:
    previous=json.loads((ROOT/'batch-replay-results.json').read_text(encoding='utf-8'))
    assert [list(x) for x in hashes['original']]==previous['hashes']['original'],'v4 differs from preserved v3 full replay'
report={'allNineStageHashesEqual':True,'hashes':hashes,'logs':logs,
        'hardwareValidated':False,'performanceMeasured':False,'timeStubAlwaysZero':True,
        'sleepsDisabledOnlyInHostReplay':True,'decodeAndFontSimulation':'Pillow host adapters',
        'neonArithmeticEmulated':True,'hostThreads':4}
name='v8-replay-'+args.disable+'.json' if args.v8 and args.disable else 'v8-replay-results.json' if args.v8 else 'v4-replay-results.json' if args.v4 else 'batch-replay-results.json'
(ROOT/name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: all 9 complete course framebuffer stage hashes equal; no speed measurement.')
