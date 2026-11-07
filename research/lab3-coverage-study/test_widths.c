#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define FB_COUNT(s) do{s;}while(0)
struct fb_batch_command {int left,right,top,bottom,stride;const unsigned char *source;};
struct fb_row_stats {uint64_t writes,spans,checks,comparisons;};
typedef struct {unsigned count;struct fb_batch_command commands[128];} fb_opaque_batch;
static uint32_t surface[SCREEN_WIDTH+2];
#define DRAW_BUF (surface+1)
#include "opaque_bitset_candidate.h"
struct fb_covered_span {int left,right;};
#define FB_OPAQUE_SWITCH_INTERVALS 1
#include "opaque_adaptive_candidate.h"
#include "opaque_fast_candidate.h"
static unsigned state=0x1037;
static unsigned rnd(void){return state=state*1664525u+1013904223u;}
int main(void)
{
    static uint32_t source[128][SCREEN_WIDTH],expected[SCREEN_WIDTH],initial[SCREEN_WIDTH];
    fb_opaque_batch batch;
    for(int trial=0;trial<1000;trial++) {
        batch.count=1+rnd()%128;
        surface[0]=0x12345678;surface[SCREEN_WIDTH+1]=0x87654321;
        for(int x=0;x<SCREEN_WIDTH;x++)initial[x]=expected[x]=DRAW_BUF[x]=rnd();
        for(unsigned i=0;i<batch.count;i++) {
            int l=rnd()%SCREEN_WIDTH,r=l+1+rnd()%(SCREEN_WIDTH-l),top=rnd()%3==0;
            for(int x=0;x<SCREEN_WIDTH;x++)source[i][x]=rnd();
            batch.commands[i]=(struct fb_batch_command){l,r,top,top+1,SCREEN_WIDTH*4,(const unsigned char *)(source[i]+l)};
            if(!top)for(int x=l;x<r;x++)expected[x]=source[i][x];
        }
        for(int renderer=0;renderer<3;renderer++) {
            memcpy(DRAW_BUF,initial,sizeof(initial));
            if(renderer==0)fb_batch_row_bitset(&batch,0);
            else if(renderer==1)fb_batch_row_adaptive(&batch,0);
            else fb_batch_row_fast(&batch,0);
            if(memcmp(DRAW_BUF,expected,sizeof(expected)) || surface[0]!=0x12345678 || surface[SCREEN_WIDTH+1]!=0x87654321){fprintf(stderr,"FAIL width %d trial %d renderer %d\n",SCREEN_WIDTH,trial,renderer);return 1;}
        }
    }
    printf("PASS width=%d: 3000 independent forward-oracle comparisons and canaries\n",SCREEN_WIDTH);return 0;
}
