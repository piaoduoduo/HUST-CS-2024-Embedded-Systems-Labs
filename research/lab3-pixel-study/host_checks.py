"""Exact pixel candidate validation. Host/emulated results are not ARM timing."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess

ROOT=Path(__file__).resolve().parent
STUDY=ROOT.parent/'lab3-optimization-study'
BUILD=ROOT/'build'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def prepare():
    BUILD.mkdir(exist_ok=True)
    baseline=STUDY/'common/graphic-v9-batch.c'
    source=baseline.read_text(encoding='utf-8')
    start=source.index('void fb_draw_pixel(');end=source.index('#include "fast_pixels_v9.h"',start)
    candidate=source[:start]+'#include "pixel_fast_candidate.h"\n\n'+source[end:]
    (STUDY/'common/graphic-v9-pixel.c').write_text(candidate,encoding='utf-8')
    shutil.copy2(ROOT/'pixel_fast_candidate.h',STUDY/'common/pixel_fast_candidate.h')
    for name,text in [('baseline',source),('candidate',candidate)]:
        folder=BUILD/name;folder.mkdir(exist_ok=True)
        glob=text[text.index('static int LCD_FB_FD;'):text.index('void fb_init(')]
        glob=glob.replace('static int LCD_FB_FD;\n','').replace('static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];',
          'static struct {int before[GUARD_WORDS];int pixels[SCREEN_WIDTH*SCREEN_HEIGHT];int after[GUARD_WORDS];} TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
        (folder/'graphics-under-test.c').write_text('#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n'+glob+text[text.index('static void _copy_area('):],encoding='utf-8')
        shutil.copy2(STUDY/'build/image-memory-under-test.c',folder/'image-memory-under-test.c')
        (folder/'font-identity.c').write_text('const void *fb_font_identity(void){return "host-font";}\n',encoding='ascii')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cc',required=True);args=p.parse_args()
    previous=json.loads((STUDY/'v9-integrated-results.json').read_text(encoding='utf-8'))
    protected={str(STUDY/name):digest for name,digest in previous['sourceHashes'].items()}
    archive=ROOT.parent/'lab3-optimized-ready.tgz'
    protected[str(archive)]=sha(archive)
    for path,digest in protected.items():assert sha(Path(path))==digest,('old source changed',path)
    backup=ROOT.parent/'resources/lab3-optimized-v9-ready.tgz'
    if not backup.exists():shutil.copy2(archive,backup)
    assert sha(backup)==protected[str(archive)]
    backup.with_suffix('.tgz.sha256').write_text(sha(backup)+'  '+backup.name+'\n',encoding='ascii')
    prepare()
    env=dict(os.environ);env['PATH']=str(Path(args.cc).parent)+os.pathsep+env.get('PATH','')
    configs=[('v9','baseline',[]),('unsigned','candidate',['FB_PIXEL_MODE=1']),('axis','candidate',['FB_PIXEL_MODE=2']),
             ('minmax','candidate',['FB_PIXEL_MODE=3']),('disabled','candidate',['FB_PIXEL_MODE=2','FB_DISABLE_PIXEL_FAST']),
             ('axis-neon-omp2','candidate',['FB_PIXEL_MODE=2','FB_TEST_NEON','OMP']),
             ('axis-lto-omp2','candidate',['FB_PIXEL_MODE=2','FB_TEST_NEON','OMP','LTO']),
             ('minmax-neon-omp2','candidate',['FB_PIXEL_MODE=3','FB_TEST_NEON','OMP'])]
    expected=json.loads((STUDY/'v8-replay-results.json').read_text(encoding='utf-8'))['hashes']['original']
    report={'passed':False,'performanceMeasured':False,'armNativeCompileValidated':False,'neonEmulated':True,'logs':{},'configurations':[],'stageHashes':{}}
    import re
    for name,kind,defines in configs:
        folder=BUILD/kind
        flags=['-D'+x for x in defines if x not in ('OMP','LTO')]
        if 'OMP' in defines:flags+=['-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1']
        if 'LTO' in defines:flags+=['-flto']
        env['OMP_NUM_THREADS']=env['OMP_THREAD_LIMIT']='2'
        for test in ('test_pixel_candidate','test_lab2_regression','full-replay'):
            src=ROOT/'test_pixel_candidate.c' if test=='test_pixel_candidate' else STUDY/'tests/test_lab2_regression.c' if test=='test_lab2_regression' else STUDY/'build-v9-integrated/sprint-v9-replay.c'
            output=BUILD/(name+'-'+test+'.exe')
            command=[args.cc,'-std=gnu11','-O3','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-D__USE_MINGW_ANSI_STDIO=1','-static',*flags,
                     '-I'+str(folder),'-I'+str(STUDY/'common'),'-I'+str(STUDY/'tests'),'-I'+str(STUDY/'tests/neon-emulation'),
                     str(src),str(STUDY/'tests/asset_adapter.c'),str(folder/'font-identity.c'),'-o',str(output),'-lm']
            built=subprocess.run(command,cwd=STUDY,env=env,capture_output=True,text=True,timeout=120)
            report['logs'][name+'-'+test+'-build']=built.stdout+built.stderr
            if built.returncode:raise RuntimeError(built.stdout+built.stderr)
            run=subprocess.run([str(output)],cwd=STUDY,env=env,capture_output=True,text=True,timeout=120)
            report['logs'][name+'-'+test]=run.stdout+run.stderr
            if run.returncode:raise RuntimeError(name+' '+test+'\n'+run.stdout+run.stderr)
            if test=='full-replay':
                hashes=[list(x) for x in re.findall(r'STAGE_HASH (\d+) ([0-9a-f]+)',run.stdout)]
                assert hashes==expected,(name,hashes)
                report['stageHashes'][name]=hashes
            print(name,test,'PASS',flush=True)
        report['configurations'].append(name)
    for path,digest in protected.items():assert sha(Path(path))==digest,('old source changed',path)
    report.update({'passed':True,'nineFullFrameStagesEqual':True,'v9SourcesAndArchiveUnchanged':True,
                   'v9BackupSHA256':sha(backup),'candidateSHA256':sha(STUDY/'common/graphic-v9-pixel.c'),
                   'headerSHA256':sha(ROOT/'pixel_fast_candidate.h'),'testSHA256':sha(ROOT/'test_pixel_candidate.c')})
    (ROOT/'correctness-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS pixel candidate; no ARM or performance claim',flush=True)

if __name__=='__main__':main()
