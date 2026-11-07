from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent;common=ROOT/'candidate/common'
shutil.copy2(ROOT/'host-benchmark.json',ROOT/'adaptive-host-benchmark.json')
p=common/'opaque_adaptive_candidate.h';s=p.read_text(encoding='utf-8')
s=s[s.index('static inline struct fb_row_stats'):].replace('fb_batch_row_adaptive(', 'fb_batch_row_fast(',1)
needle='        for(int i=0;i<count && covered[i].left<c->right;++i) {'
fast='''        /* The single connected-interval case avoids the generic interval
           search/insertion/memmove. No course-specific dimensions or assets. */
        if(count==1 && c->left<=covered[0].right && c->right>=covered[0].left) {
            FB_COUNT(result.comparisons++);
            int old_left=covered[0].left,old_right=covered[0].right;
            if(c->left<old_left) {
                memcpy(DRAW_BUF+(size_t)y*SCREEN_WIDTH+c->left,row,(size_t)(old_left-c->left)*4);
                FB_COUNT(result.writes+=(unsigned)(old_left-c->left));FB_COUNT(result.spans++);
                covered[0].left=c->left;
            }
            if(c->right>old_right) {
                memcpy(DRAW_BUF+(size_t)y*SCREEN_WIDTH+old_right,row+(size_t)(old_right-c->left)*4,(size_t)(c->right-old_right)*4);
                FB_COUNT(result.writes+=(unsigned)(c->right-old_right));FB_COUNT(result.spans++);
                covered[0].right=c->right;
            }
            if(covered[0].left==0 && covered[0].right==SCREEN_WIDTH)break;
            continue;
        }
'''
assert s.count(needle)==1;s=s.replace(needle,fast+needle)
(common/'opaque_fast_candidate.h').write_text(s,encoding='utf-8')
p=common/'opaque_batch_v5.h';s=p.read_text(encoding='utf-8').replace('#include "opaque_adaptive_candidate.h"','#include "opaque_adaptive_candidate.h"\n#include "opaque_fast_candidate.h"')
s=s.replace('#if defined(FB_OPAQUE_ADAPTIVE)','#if defined(FB_OPAQUE_FAST)\n        row=fb_batch_row_fast(batch,y);\n        #elif defined(FB_OPAQUE_ADAPTIVE)')
p.write_text(s,encoding='utf-8')
p=ROOT/'check.py';s=p.read_text(encoding='utf-8').replace("('interval',[]),", "('interval',[]),('fast',['-DFB_OPAQUE_FAST']),('fast-switch1',['-DFB_OPAQUE_FAST','-DFB_OPAQUE_SWITCH_INTERVALS=1']),")
s=s.replace("('adaptive-lto-omp2',['-DFB_OPAQUE_ADAPTIVE'", "('fast-lto-omp2',['-DFB_OPAQUE_FAST'")
p.write_text(s,encoding='utf-8')
p=ROOT/'bench_rows.c';s=p.read_text(encoding='utf-8')
s=s.replace('renderer functions[3]={fb_batch_row,fb_batch_row_bitset,fb_batch_row_adaptive};unsigned repeats[3];uint64_t hash[3];',
 'renderer functions[4]={fb_batch_row,fb_batch_row_bitset,fb_batch_row_adaptive,fb_batch_row_fast};unsigned repeats[4];uint64_t hash[4];')
s=s.replace('k<3;k++','k<4;k++').replace('order<3;order++','order<4;order++').replace('k=(trial+order)%3','k=(trial+order)%4')
s=s.replace('k==2?"adaptive":', 'k==3?"fast":k==2?"adaptive":')
p.write_text(s,encoding='utf-8')
print('Generic connected-interval fast path added as fourth candidate')
