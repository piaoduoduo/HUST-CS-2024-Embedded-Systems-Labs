from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
shutil.copy2(ROOT/'validation.json',ROOT/'bitset-validation.json')
shutil.copy2(ROOT/'host-benchmark.json',ROOT/'bitset-host-benchmark.json')
common=ROOT/'candidate/common';p=common/'opaque_bitset_candidate.h';s=p.read_text(encoding='utf-8')
start=s.index('static inline struct fb_row_stats fb_batch_row_bitset(')
body=s[start:]
body=body.replace('fb_batch_row_bitset(const fb_opaque_batch *batch,int y)','fb_batch_row_bitset_from(const fb_opaque_batch *batch,int y,unsigned start,uint64_t *covered,unsigned full)',1)
old='''    uint64_t covered[FB_OPAQUE_WORDS]={0};
    if(SCREEN_WIDTH%64)covered[FB_OPAQUE_WORDS-1]=UINT64_MAX<<(SCREEN_WIDTH%64);
    unsigned full=0;struct fb_row_stats result={0};'''
assert old in body;body=body.replace(old,'    struct fb_row_stats result={0};',1).replace('command=batch->count','command=start',1)
body+='''
static inline struct fb_row_stats fb_batch_row_bitset(const fb_opaque_batch *batch,int y)
{
    uint64_t covered[FB_OPAQUE_WORDS]={0};
    if(SCREEN_WIDTH%64)covered[FB_OPAQUE_WORDS-1]=UINT64_MAX<<(SCREEN_WIDTH%64);
    return fb_batch_row_bitset_from(batch,y,batch->count,covered,0);
}
'''
p.write_text(s[:start]+body,encoding='utf-8')
p=common/'opaque_batch_v5.h';s=p.read_text(encoding='utf-8')
start=s.index('static inline struct fb_row_stats fb_batch_row(');end=s.index('#include "opaque_bitset_candidate.h"',start)
original=s[start:end]
new=original.replace('fb_batch_row(', 'fb_batch_row_adaptive(',1)
needle='        if(count==1 && left==0 && right==SCREEN_WIDTH)break;'
insert='''        if(count>=FB_OPAQUE_SWITCH_INTERVALS && command>1) {
            uint64_t bits[FB_OPAQUE_WORDS]={0};unsigned full=0;
            if(SCREEN_WIDTH%64)bits[FB_OPAQUE_WORDS-1]=UINT64_MAX<<(SCREEN_WIDTH%64);
            for(int i=0;i<count;i++)for(int w=covered[i].left/64;w<=(covered[i].right-1)/64;w++) {
                int base=w*64,l=covered[i].left>base?covered[i].left-base:0,r=covered[i].right-base;
                if(r>64)r=64;
                uint64_t old=bits[w];bits[w]|=fb_opaque_mask(l,r);
                if(old!=UINT64_MAX && bits[w]==UINT64_MAX)full++;
            }
            struct fb_row_stats tail=fb_batch_row_bitset_from(batch,y,command-1,bits,full);
            result.writes+=tail.writes;result.spans+=tail.spans;
            result.checks+=tail.checks;result.comparisons+=tail.comparisons;
            return result;
        }
'''
assert new.count(needle)==1;new=new.replace(needle,insert+needle)
adaptive='#ifndef FB_OPAQUE_SWITCH_INTERVALS\n#define FB_OPAQUE_SWITCH_INTERVALS 8\n#endif\n'+new
(common/'opaque_adaptive_candidate.h').write_text(adaptive,encoding='utf-8')
s=s.replace('#include "opaque_bitset_candidate.h"\n','')
s=s.replace(original,'#include "opaque_bitset_candidate.h"\n'+original+'#include "opaque_adaptive_candidate.h"\n')
s=s.replace('#ifdef FB_OPAQUE_BITSET\n        row=', '#if defined(FB_OPAQUE_ADAPTIVE)\n        row=fb_batch_row_adaptive(batch,y);\n        #elif defined(FB_OPAQUE_BITSET)\n        row=')
p.write_text(s,encoding='utf-8')
p=ROOT/'check.py';s=p.read_text(encoding='utf-8');s=s.replace("('interval',[]),", "('interval',[]),('adaptive',['-DFB_OPAQUE_ADAPTIVE']),('adaptive-switch1',['-DFB_OPAQUE_ADAPTIVE','-DFB_OPAQUE_SWITCH_INTERVALS=1']),")
s=s.replace("('bitset-lto-omp2',['-DFB_OPAQUE_BITSET'", "('adaptive-lto-omp2',['-DFB_OPAQUE_ADAPTIVE'")
p.write_text(s,encoding='utf-8')
p=ROOT/'bench_rows.c';s=p.read_text(encoding='utf-8').replace('renderer functions[2]={fb_batch_row,fb_batch_row_bitset};unsigned repeats[2];uint64_t hash[2];',
 'renderer functions[3]={fb_batch_row,fb_batch_row_bitset,fb_batch_row_adaptive};unsigned repeats[3];uint64_t hash[3];')
s=s.replace('k<2;k++','k<3;k++').replace('order<2;order++','order<3;order++').replace('k=(trial+order)%2','k=(trial+order)%3')
s=s.replace('k?"bitset":"interval"','k==2?"adaptive":k==1?"bitset":"interval"')
p.write_text(s,encoding='utf-8')
print('Adaptive candidate added; interval/bitset retained as controls')
