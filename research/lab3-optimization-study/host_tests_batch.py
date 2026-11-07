from pathlib import Path
import argparse,json,os,re,struct,subprocess
from PIL import Image
ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'build-batch';BUILD.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--cc',required=True);p.add_argument('--v4',action='store_true');args=p.parse_args()
cc=Path(args.cc);env=dict(os.environ);env['PATH']=str(cc.parent)+os.pathsep+env.get('PATH','')
source=(ROOT/'common'/('graphic-v4-batch.c' if args.v4 else 'graphic-batch.c')).read_text(encoding='utf-8')
globals_=source[source.index('static int LCD_FB_FD;'):source.index('void fb_init(')]
globals_=globals_.replace('static int LCD_FB_FD;\n','').replace('static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];',
 'static struct {int before[GUARD_WORDS];int pixels[SCREEN_WIDTH*SCREEN_HEIGHT];int after[GUARD_WORDS];} TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
(BUILD/'graphics-under-test.c').write_text('#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n'+globals_+source[source.index('static void _copy_area('):],encoding='utf-8')
image=(ROOT/'common/image-fast.c').read_text(encoding='utf-8')
memory=image[image.index('/*w, h maybe == 0*/'):image.index('/*================== read a jpeg image')]
(BUILD/'image-memory-under-test.c').write_text('#include <limits.h>\n'+memory,encoding='utf-8')
(BUILD/'font-identity.c').write_text('const void *fb_font_identity(void){return "host-font";}\n')
assets=ROOT/'build/assets';assets.mkdir(parents=True,exist_ok=True)
with Image.open(ROOT.parent/'lab3-prepared/out/test.jpg') as decoded:
    rgba=decoded.convert('RGBA')
    (assets/'test.jpg.bgra').write_bytes(struct.pack('<iii',*rgba.size,1)+rgba.tobytes('raw','BGRA'))
logs={};metrics={}
def run(command,label):
    r=subprocess.run(list(map(str,command)),cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    logs[label]=r.stdout+r.stderr
    if r.returncode:raise RuntimeError(label+'\n'+logs[label])
    if r.stdout:print(label,r.stdout.strip(),flush=True)
    return r.stdout
base=['-std=gnu11','-D__USE_MINGW_ANSI_STDIO=1','-O3','-Wall','-Wextra','-Werror','-static','-I',BUILD,'-I',ROOT/'common','-I',ROOT/'tests']
variants=[('serial',[],1),('parallel-2',['-fopenmp'],2),('parallel-4',['-fopenmp'],4),('capacity-3',['-DFB_BATCH_CAPACITY=3'],1)]
for name,flags,threads in variants:
    env['OMP_NUM_THREADS']=str(threads);env['OMP_DYNAMIC']='FALSE'
    exe=BUILD/(name+'.exe')
    run([cc,*base,*flags,ROOT/'tests/test_opaque_batch.c',ROOT/'tests/asset_adapter.c',BUILD/'font-identity.c','-o',exe,'-lm'],name+'-compile')
    out=run([exe],name)
    metrics[name]={k:int(v) for k,v in re.findall(r'(submitted_pixels|copied_pixels|row_checks|interval_comparisons|spans|flushes)=(\d+)',out)}
    run([exe,'course-jpeg'],name+'-course-jpeg')
report={'logs':logs,'courseWorkload':metrics,'hardwareValidated':False,'armNativeCompileValidated':False,
        'performanceMeasured':False,'sourcePixelsCompared':'synthetic padded RGB and actual course JPEG decoded by host Pillow, not ARM libjpeg',
        'batchInterfaceChangesSemantics':'explicit final-frame API; original immediate API preserved'}
(ROOT/('v4-batch-offline-results.json' if args.v4 else 'batch-offline-results.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
