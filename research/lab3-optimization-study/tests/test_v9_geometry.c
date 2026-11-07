#include <stdlib.h>
#include <stdint.h>
#include <limits.h>
/* Inject failures only into the new geometry allocator, never the oracle. */
static int geometry_fail_after=-1;
static int geometry_allocation_ok(void){if(geometry_fail_after==0)return 0;if(geometry_fail_after>0)--geometry_fail_after;return 1;}
static inline void *geometry_test_malloc(size_t n){return geometry_allocation_ok()?malloc(n):NULL;}
static inline void *geometry_test_calloc(size_t n,size_t s){return geometry_allocation_ok()?calloc(n,s):NULL;}
static inline void *geometry_test_realloc(void *p,size_t n){return geometry_allocation_ok()?realloc(p,n):NULL;}
#define FB_GEOMETRY_MALLOC geometry_test_malloc
#define FB_GEOMETRY_CALLOC geometry_test_calloc
#define FB_GEOMETRY_REALLOC geometry_test_realloc
#define FB_GEOMETRY_FREE free
#include "fixture.h"
#include "geometry_batch_api_v9.h"
static uint32_t rng=0x19261018u;
static uint32_t next_random(void){rng=rng*1664525u+1013904223u;return rng;}
static int expected[SCREEN_WIDTH*SCREEN_HEIGHT];
static struct area oracle_area;
static unsigned commands;
static void oracle_dirty(int x,int y,int w,int h)
{
    if(oracle_area.x1>x)oracle_area.x1=x;
    if(oracle_area.x2<x+w)oracle_area.x2=x+w;
    if(oracle_area.y1>y)oracle_area.y1=y;
    if(oracle_area.y2<y+h)oracle_area.y2=y+h;
}
static void oracle_pixel(int64_t x,int64_t y,int color)
{
    if(x<0 || y<0 || x>=SCREEN_WIDTH || y>=SCREEN_HEIGHT)return;
    expected[(size_t)y*SCREEN_WIDTH+(size_t)x]=color;oracle_dirty((int)x,(int)y,1,1);
}
static void oracle_line(int x1,int y1,int x2,int y2,int color)
{
    int64_t dx=(int64_t)x2-x1,dy=(int64_t)y2-y1;
    int steep=llabs(dy)>llabs(dx);
    int64_t a=steep?y1:x1,b=steep?y2:x2,c=steep?x1:y1,d=steep?x2:y2;
    if(a>b){int64_t t=a;a=b;b=t;t=c;c=d;d=t;}
    int64_t len=b-a,dist=llabs(d-c),sign=d<c?-1:1;
    int64_t first=a<0?0:a,last=b,limit=steep?SCREEN_HEIGHT:SCREEN_WIDTH;
    if(last>=limit)last=limit-1;
    for(int64_t major=first;major<=last;++major){
        int64_t minor=c+(len?sign*(int64_t)(((__int128)dist*(major-a)+len/2)/len):0);
        oracle_pixel(steep?minor:major,steep?major:minor,color);
    }
}
static void oracle_rect(int x,int y,int w,int h,int color)
{
    if(w<=0 || h<=0)return;
    int64_t l=x,r=(int64_t)x+w,t=y,b=(int64_t)y+h;
    if(l<0)l=0;
    if(r>SCREEN_WIDTH)r=SCREEN_WIDTH;
    if(t<0)t=0;
    if(b>SCREEN_HEIGHT)b=SCREEN_HEIGHT;
    if(l>=r || t>=b)return;
    for(int64_t row=t;row<b;++row)for(int64_t col=l;col<r;++col)expected[row*SCREEN_WIDTH+col]=color;
    oracle_dirty((int)l,(int)t,(int)(r-l),(int)(b-t));
}
static void begin_case(const char *label)
{
    snprintf(case_label,sizeof(case_label),"%s",label);reset_surfaces(0);AREA_SET_EMPTY(&oracle_area);
    for(int y=0;y<SCREEN_HEIGHT;++y)for(int x=0;x<SCREEN_WIDTH;++x){
        int color=(int)next_random();expected[y*SCREEN_WIDTH+x]=DRAW_BUF[y*SCREEN_WIDTH+x]=color;
        LCD_FB_BUF[y*PITCH_WORDS+x]=color;
    }
}
static void rect(fb_geometry_batch *p,int x,int y,int w,int h,int color)
{
    oracle_rect(x,y,w,h,color);require(fb_geometry_batch_rect(p,x,y,w,h,color)==1,"rect consumption");++commands;
}
static void line(fb_geometry_batch *p,int x1,int y1,int x2,int y2,int color)
{
    oracle_line(x1,y1,x2,y2,color);require(fb_geometry_batch_line(p,x1,y1,x2,y2,color)==1,"line consumption");++commands;
}
static void finish_case(fb_geometry_batch *p)
{
    fb_geometry_batch_end(p);geometry_fail_after=-1;
    require(!memcmp(expected,DRAW_BUF,sizeof(expected)),"ordered geometry differs from independent exact quotient oracle");
    require(!memcmp(&oracle_area,&update_area,sizeof(oracle_area)),"geometry dirty region mismatch");
    check_canaries();fb_update();check_front_matches_back();++tested_cases;
}
int main(void)
{
    const int offsets[]={-61,-17,-8,-3,-1,0,1,3,8,17,61};
    for(unsigned ix=0;ix<sizeof(offsets)/sizeof(*offsets);++ix)
    for(unsigned iy=0;iy<sizeof(offsets)/sizeof(*offsets);++iy)
    for(int reverse=0;reverse<2;++reverse){
        begin_case("all octants, phases and endpoint reversals");fb_geometry_batch *p=fb_geometry_batch_begin();
        int x=31,y=23,xx=x+offsets[ix],yy=y+offsets[iy];
        if(reverse)line(p,xx,yy,x,y,(int)next_random());else line(p,x,y,xx,yy,(int)next_random());
        finish_case(p);
    }
    for(int trial=0;trial<144;++trial){
        begin_case("mixed ordered rectangles and clipped lines");fb_geometry_batch *p=fb_geometry_batch_begin();
        for(unsigned n=0;n<97;++n){
            int x=(int)(next_random()%(SCREEN_WIDTH+400))-200,y=(int)(next_random()%(SCREEN_HEIGHT+200))-100;
            int a=(int)(next_random()%(SCREEN_WIDTH+400))-200,b=(int)(next_random()%(SCREEN_HEIGHT+200))-100;
            if(n%3)line(p,x,y,a,b,(int)next_random());else rect(p,x,y,a/3,b/3,(int)next_random());
        }
        finish_case(p);
    }
    const int extremes[][4]={{INT_MIN,INT_MIN,INT_MAX,INT_MAX},{INT_MIN,INT_MAX,INT_MAX,INT_MIN},
        {INT_MIN,17,INT_MAX,18},{17,INT_MIN,18,INT_MAX},{INT_MAX,22,INT_MAX,22},{INT_MIN,-1,INT_MAX,-1},
        {INT_MIN,0,INT_MAX,0},{0,INT_MIN,0,INT_MAX},{0,0,0,0},{INT_MIN,INT_MAX,INT_MIN,INT_MAX},
        {INT_MAX,INT_MIN,INT_MIN,INT_MAX-1}};
    for(unsigned n=0;n<sizeof(extremes)/sizeof(*extremes);++n)for(int rev=0;rev<2;++rev){
        begin_case("extreme int32 endpoint phase");fb_geometry_batch *p=fb_geometry_batch_begin();
        const int *v=extremes[n];if(rev)line(p,v[2],v[3],v[0],v[1],(int)next_random());else line(p,v[0],v[1],v[2],v[3],(int)next_random());
        finish_case(p);
    }
    for(unsigned trial=0;trial<96;++trial){
        begin_case("random int32 and rectangle sum overflow");fb_geometry_batch *p=fb_geometry_batch_begin();
        for(int n=0;n<5;++n)line(p,(int)next_random(),(int)next_random(),(int)next_random(),(int)next_random(),(int)next_random());
        rect(p,INT_MIN,INT_MIN,INT_MAX,INT_MAX,11);rect(p,4,7,INT_MAX,INT_MAX,0x12121314);
        rect(p,INT_MAX,INT_MAX,INT_MAX,INT_MAX,23);rect(p,-5,-5,9,9,0x00123456);
        finish_case(p);
    }
    for(int fail=0;fail<12;++fail){
        begin_case("allocation failures and partial ordered flush");geometry_fail_after=fail;fb_geometry_batch *p=fb_geometry_batch_begin();
        for(int n=0;n<151;++n){rect(p,n-20,n-30,40,23,(int)next_random());line(p,n-40,0,SCREEN_WIDTH-n,SCREEN_HEIGHT-1,(int)next_random());}
        finish_case(p);
    }
    begin_case("NULL fallback");rect(NULL,3,4,67,25,0x12345678);line(NULL,INT_MIN,17,INT_MAX,18,0x00efefef);finish_case(NULL);
    begin_case("same-row same-color coalescing and intervening-color barriers");fb_geometry_batch *coalesce=fb_geometry_batch_begin();
    for(int i=0;i<120;++i){
        rect(coalesce,20+i,30,20,40,0x12123456);rect(coalesce,700-i,30,5,40,0x12123456);
        rect(coalesce,200+i,30,4,40,(i%3)?0x12123456:0x00123456);
        line(coalesce,300,100+i,800,500-i,0x12123456);
    }
    finish_case(coalesce);
    static const unsigned colors[]={0xffff0000u,0xffffa500u,0xffffff00u,0xff00ff00u,0xff007fffu,0xff0000ffu,0xff8b00ffu,0xffffffffu,0xff000000u};
    begin_case("complete course rectangles 13334");fb_geometry_batch *p=fb_geometry_batch_begin();unsigned count=0,c=0;
    for(int y=-15;y<300;y+=5)for(int x=-15;x<1029;x+=5){rect(p,x,y,10,10,(int)colors[c++%9]);++count;}
    c=0;for(int y=300;y<605;y+=5){rect(p,0,y,500,10,(int)colors[c++%9]);++count;}
    c=0;for(int x=500;x<1029;x+=5){rect(p,x,300,10,300,(int)colors[c++%9]);++count;}
    require(count==13334,"course rectangle count");
    if(p){fb_geometry_flush(p);printf("COURSE rect submitted=%llu written=%llu flushes=%llu generated_spans=%llu retained_spans=%llu\n",(unsigned long long)p->submitted_pixels,(unsigned long long)p->written_pixels,(unsigned long long)p->flushes,(unsigned long long)p->generated_spans,(unsigned long long)p->retained_spans);}
    finish_case(p);
    begin_case("complete course lines 802");p=fb_geometry_batch_begin();
    for(int i=0;i<=400;++i)line(p,200,100+i,800,500-i,(int)colors[1]);
    for(int i=0;i<=400;++i)line(p,300+i,100,700-i,500,(int)colors[2]);
    if(p){fb_geometry_flush(p);printf("COURSE line submitted=%llu written=%llu flushes=%llu generated_spans=%llu retained_spans=%llu\n",(unsigned long long)p->submitted_pixels,(unsigned long long)p->written_pixels,(unsigned long long)p->flushes,(unsigned long long)p->generated_spans,(unsigned long long)p->retained_spans);}
    finish_case(p);
    printf("PASS: %u geometry cases, %u commands; full pixel + dirty + framebuffer padding/canary checks\n",tested_cases,commands);
    free(front_storage);return 0;
}
