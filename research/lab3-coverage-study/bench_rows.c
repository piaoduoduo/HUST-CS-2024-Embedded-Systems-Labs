#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "fixture.h"
extern uint64_t observe_surface(const int *p,size_t count);
static volatile uint64_t observed;
static double now(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return (double)t.QuadPart/(double)f.QuadPart;}
typedef struct fb_row_stats (*renderer)(const fb_opaque_batch *,int);
static double sample(const fb_opaque_batch *b,renderer draw,unsigned repeats,uint64_t *hash)
{
    uint64_t writes=0,work=0;double start=now();
    for(unsigned i=0;i<repeats;i++)for(int y=0;y<SCREEN_HEIGHT;y++) {
        struct fb_row_stats row=draw(b,y);writes+=row.writes;work+=row.comparisons;
    }
    double elapsed=(now()-start)*1000.0/repeats;
    observed=writes+work;*hash=observe_surface(DRAW_BUF,SCREEN_WIDTH*SCREEN_HEIGHT);
    return elapsed;
}
int main(void)
{
    reset_surfaces(0);
    for(int workload=0;workload<2;workload++) {
        fb_image *im=fb_new_image(FB_COLOR_RGB_8880,workload?1:600,workload?600:400,0);
        require(im!=NULL,"benchmark image");
        for(size_t i=0;i<(size_t)im->line_byte*im->pixel_h;i++)im->content[i]=(char)(i*73+17);
        fb_opaque_batch *batch=fb_opaque_batch_begin();require(batch!=NULL,"benchmark batch");
        if(!workload)for(int y=-5;y<605;y+=100)for(int x=-5;x<1029;x+=50)require(fb_opaque_batch_add(batch,x,y,im),"course add");
        else for(int x=0;x<512;x+=2)require(fb_opaque_batch_add(batch,x,0,im),"fragmented add");
        renderer functions[4]={fb_batch_row,fb_batch_row_bitset,fb_batch_row_adaptive,fb_batch_row_fast};unsigned repeats[4];uint64_t hash[4];
        for(int k=0;k<4;k++) {
            double pilot=sample(batch,functions[k],1,&hash[k]);
            repeats[k]=(unsigned)(50.0/(pilot>0?pilot:0.001));if(repeats[k]<1)repeats[k]=1;if(repeats[k]>512)repeats[k]=512;
        }
        require(hash[0]==hash[1],"benchmark surfaces differ");
        for(int trial=0;trial<9;trial++)for(int order=0;order<4;order++) {
            int k=(trial+order)%4;
            double ms=sample(batch,functions[k],repeats[k],&hash[k]);require(hash[k]==hash[0],"benchmark output unstable");
            printf("BENCH %s %s %d %.9f %u %016llx\n",workload?"fragmented":"course",k==3?"fast":k==2?"adaptive":k==1?"bitset":"interval",trial,ms,repeats[k],(unsigned long long)hash[k]);
        }
        /* No flush is timed here. This is row-rendering research, not the
           full lab3 JPEG timer (decode, refresh and setup remain excluded). */
        free(batch);fb_free_image(im);
    }
    free(front_storage);return observed==UINT64_MAX;
}
