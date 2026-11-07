#include "fixture.h"
static unsigned seed=0x1037;
static unsigned next(void){seed=seed*1664525u+1013904223u;return seed;}
static int expected[SCREEN_WIDTH*SCREEN_HEIGHT];
#ifndef FB_USE_REAL_IMAGE
void font_init(char *p){(void)p;}
const void *fb_font_identity(void){return NULL;}
fb_image *fb_read_font_image(const char*t,int s,fb_font_info*f){(void)t;(void)s;(void)f;return NULL;}
void fb_free_image(fb_image *i){(void)i;}
#endif
int main(void)
{
    for(int trial=0;trial<1024;trial++) {
        int x1=(int)(next()%SCREEN_WIDTH),x2=(int)(next()%SCREEN_WIDTH);
        int y1=(int)(next()%SCREEN_HEIGHT),y2=(int)(next()%SCREEN_HEIGHT);
        if(trial%8==0)x2=x1;
        if(trial%8==1)y2=y1;
        if(trial%8==2){x2=x1;y2=y1;}
        reset_surfaces(0);memset(expected,0,sizeof(expected));
        int64_t dx=(int64_t)x2-x1,dy=(int64_t)y2-y1;
        int steep=llabs(dy)>llabs(dx);
        int64_t a=steep?y1:x1,b=steep?y2:x2,c=steep?x1:y1,d=steep?x2:y2;
        if(a>b){int64_t t=a;a=b;b=t;t=c;c=d;d=t;}
        int64_t len=b-a,dist=llabs(d-c),sign=d<c?-1:1;
        for(int64_t i=0;i<=len;i++) {
            int64_t minor=c+(len?sign*((dist*i+len/2)/len):0);
            int x=(int)(steep?minor:a+i),y=(int)(steep?a+i:minor);
            expected[y*SCREEN_WIDTH+x]=0x12345678;
        }
        fb_draw_line(x1,y1,x2,y2,0x12345678);
        require(!memcmp(expected,DRAW_BUF,sizeof(expected)),"inside pointer line differs from exact rounded raster oracle");
        check_canaries();tested_cases++;
    }
    printf("PASS: %u exact inside-line full-buffer comparisons\n",tested_cases);
    free(front_storage);return 0;
}
