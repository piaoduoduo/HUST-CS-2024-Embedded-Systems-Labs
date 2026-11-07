"""Host-only microbenchmark/assembly diagnostic, never a board prediction."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,statistics

ROOT=Path(__file__).resolve().parent;BUILD=ROOT/'build-bench'
STUDY=ROOT.parent/'lab3-optimization-study'
PREFIX='''#include <stdint.h>
#include <stddef.h>
#define SCREEN_WIDTH 1024
#define SCREEN_HEIGHT 600
static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];
static struct area {int x1,x2,y1,y2;} update_area;
static inline void *_begin_draw(int x,int y,int w,int h){
 int x2=x+w,y2=y+h;
 if(update_area.x1>x)update_area.x1=x;
 if(update_area.y1>y)update_area.y1=y;
 if(update_area.x2<x2)update_area.x2=x2;
 if(update_area.y2<y2)update_area.y2=y2;
 return DRAW_BUF;
}
'''
SUFFIX='''
extern int bench_verify(const int *,const int *,int);
void bench_reset(void){update_area=(struct area){SCREEN_WIDTH,0,SCREEN_HEIGHT,0};}
int bench_finish(int color){int box[4]={update_area.x1,update_area.x2,update_area.y1,update_area.y2};return bench_verify(DRAW_BUF,box,color);}
'''
MAIN=r'''
#include <stdint.h>
#include <stdio.h>
#ifdef _WIN32
#include <windows.h>
static uint64_t now_ns(void){static LARGE_INTEGER freq;LARGE_INTEGER t;if(!freq.QuadPart)QueryPerformanceFrequency(&freq);QueryPerformanceCounter(&t);return (uint64_t)((t.QuadPart/freq.QuadPart)*1000000000ULL+(t.QuadPart%freq.QuadPart)*1000000000ULL/freq.QuadPart);}
#else
#include <time.h>
static uint64_t now_ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;}
#endif
extern void fb_draw_pixel(int,int,int);
extern void bench_reset(void);
extern int bench_finish(int);
static volatile unsigned colors=0xff123456u;
static void draw(int color){for(int row=-5;row<605;row+=2)for(int col=-5;col<1029;col+=2)fb_draw_pixel(col,row,color);}
int main(void){
 for(int warm=0;warm<16;warm++){int color=(int)(colors+=0x10101u);bench_reset();draw(color);if(!bench_finish(color))return 2;}
 for(int trial=0;trial<9;trial++){
   uint64_t total=0;
   for(int frame=0;frame<16;frame++){
     int color=(int)(colors+=0x10101u);bench_reset();
     uint64_t start=now_ns();draw(color);uint64_t end=now_ns();total+=end-start;
     if(!bench_finish(color))return 3;
   }
   printf("HOST_POINT_NS %llu\n",(unsigned long long)(total/16));
 }
 return 0;
}
'''
VERIFY='''#include <stdint.h>
static volatile uint64_t checksum;
int bench_verify(const int *pixels,const int *box,int color){
 if(box[0]!=1 || box[1]!=1024 || box[2]!=1 || box[3]!=600)return 0;
 uint64_t h=0;
 for(int y=0;y<600;y++)for(int x=0;x<1024;x++){
   int expected=((x&1)&&(y&1))?color:0;
   if(pixels[y*1024+x]!=expected)return 0;
   h=h*33u+(uint32_t)pixels[y*1024+x];
 }
 checksum^=h;return 1;
}
'''

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cc',required=True);args=p.parse_args()
    BUILD.mkdir(exist_ok=True)
    source=(STUDY/'common/graphic-v9-batch.c').read_text(encoding='utf-8')
    a=source.index('void fb_draw_pixel(');b=source.index('#include "fast_pixels_v9.h"',a)
    baseline=source[a:b]
    (BUILD/'baseline.c').write_text(PREFIX+baseline+SUFFIX,encoding='utf-8')
    (BUILD/'candidate.c').write_text(PREFIX+'#include "pixel_fast_candidate.h"\n'+SUFFIX,encoding='utf-8')
    (BUILD/'main.c').write_text(MAIN,encoding='utf-8');(BUILD/'verify.c').write_text(VERIFY,encoding='utf-8')
    env=dict(os.environ);env['PATH']=str(Path(args.cc).parent)+os.pathsep+env.get('PATH','')
    base=[args.cc,'-std=gnu11','-O3','-Wall','-Wextra','-Werror','-Wno-unused-function','-D__USE_MINGW_ANSI_STDIO=1','-I'+str(ROOT)]
    def run(command):
        result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=180)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        return result.stdout+result.stderr
    run(base+['-fno-lto','-c',str(BUILD/'verify.c'),'-o',str(BUILD/'verify.o')])
    report={'hostOnly':True,'hardwareValidated':False,'armPerformanceMeasured':False,
      'compiler':run([args.cc,'--version']).splitlines()[0],
      'scope':'157685 original calls / 153600 visible writes; only draw loop timed; dirty updates immediate; full buffer verification outside interval prevents dead-store elimination',
      'allLoopsRetained':True,'results':{},'assemblyFiles':{},'headerSHA256':hashlib.sha256((ROOT/'pixel_fast_candidate.h').read_bytes()).hexdigest()}
    for lto in (False,True):
        for mode,name in ((0,'v9'),(1,'unsigned'),(2,'axis'),(3,'minmax')):
            stem=name+('-lto' if lto else '-calls')
            core=BUILD/('baseline.c' if mode==0 else 'candidate.c')
            flags=(['-flto'] if lto else [])+['-DFB_PIXEL_MODE='+str(mode)]
            exe=BUILD/(stem+'.exe')
            run(base+flags+['-static',str(core),str(BUILD/'main.c'),str(BUILD/'verify.o'),'-o',str(exe)])
            output=run([str(exe)]);values=[int(x) for x in re.findall(r'HOST_POINT_NS (\d+)',output)]
            assert len(values)==9
            report['results'][stem]={'samplesNs':values,'medianNs':statistics.median(values),'minimumNs':min(values),'maximumNs':max(values),'fullPixelAndDirtyCheckPassed':True}
            print(stem,'host median us',round(statistics.median(values)/1000,2),flush=True)
            if not lto:
                asm=BUILD/(stem+'.s');run(base+flags+['-S',str(core),'-o',str(asm)])
                report['assemblyFiles'][stem]=asm.relative_to(ROOT).as_posix()
    (ROOT/'host-benchmark-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Host diagnostic complete; these numbers are not RK3399 milliseconds.',flush=True)

if __name__=='__main__':main()
