#include "fixture.h"
#ifndef FB_DISABLE_PREPARED
static unsigned rng=0x1037;
static unsigned next(void){rng=rng*1664525u+1013904223u;return rng;}
static uint32_t oracle(uint32_t s,uint32_t d,unsigned a)
{
    if(!a)return d;
    uint32_t out=0xff000000u;
    for(int c=0;c<3;c++)out|=((((s>>(8*c))&255)*a+((d>>(8*c))&255)*(255-a)+127)/255)<<(8*c);
    return out;
}
static void compare(fb_image *image,const fb_prepared_draw *draws,unsigned count,int expect_skips)
{
    static uint32_t initial[SCREEN_WIDTH*SCREEN_HEIGHT],expected[SCREEN_WIDTH*SCREEN_HEIGHT];
    reset_surfaces(0);int bytes=image->color_type==FB_COLOR_ALPHA_8?1:4;
    for(int i=0;i<SCREEN_WIDTH*SCREEN_HEIGHT;i++)initial[i]=expected[i]=(uint32_t)(DRAW_BUF[i]=(int)next());
    for(unsigned i=0;i<count;i++) {
        int64_t left=draws[i].x,top=draws[i].y,right=left+image->pixel_w,bottom=top+image->pixel_h;
        if(left<0)left=0;
        if(top<0)top=0;
        if(right>SCREEN_WIDTH)right=SCREEN_WIDTH;
        if(bottom>SCREEN_HEIGHT)bottom=SCREEN_HEIGHT;
        if(left>=right || top>=bottom)continue;
        _begin_draw((int)left,(int)top,(int)(right-left),(int)(bottom-top));
        for(int y=(int)top;y<(int)bottom;y++)for(int x=(int)left;x<(int)right;x++) {
            const unsigned char *src=(const unsigned char *)image->content+(size_t)((int64_t)y-draws[i].y)*image->line_byte+(size_t)((int64_t)x-draws[i].x)*bytes;
            uint32_t color=(uint32_t)draws[i].color;
            if(bytes==4)color=(uint32_t)src[0]|((uint32_t)src[1]<<8)|((uint32_t)src[2]<<16);
            expected[y*SCREEN_WIDTH+x]=oracle(color,expected[y*SCREEN_WIDTH+x],src[bytes-1]);
        }
    }
    struct area expected_area=update_area;AREA_SET_EMPTY(&update_area);memcpy(DRAW_BUF,initial,sizeof(initial));
    fb_prepared_image *p=fb_prepare_image(image);require(p!=NULL,"prepared cull snapshot");
    #if defined(FB_CULL_TEST_STATS) && !defined(FB_DISABLE_MANY)
    memset(fb_v9_cull_stats,0,sizeof(fb_v9_cull_stats));
    #endif
    fb_draw_prepared_many(p,draws,count);
    require(!memcmp(DRAW_BUF,expected,sizeof(expected)),"cull independent ordered alpha oracle");
    require(!memcmp(&expected_area,&update_area,sizeof(expected_area)),"cull dirty union");check_canaries();tested_cases++;
    #if defined(FB_CULL_TEST_STATS) && !defined(FB_DISABLE_MANY)
    #if !defined(FB_DISABLE_OPAQUE_CULL) && !defined(FB_DISABLE_ROW_INDEX) && FB_ROW_INDEX_LIMIT > 1 && FB_CULL_MAX_COMMANDS > 1
    if(expect_skips) {
        require(fb_v9_cull_stats[0]>0,"cull enabled path actually ran");
        require(fb_v9_cull_stats[1]+fb_v9_cull_stats[2]>0,"cull skipped hidden writes");
    }
    if(count==129 && FB_CULL_MAX_COMMANDS<129)require(fb_v9_cull_stats[3]>0,"cull capacity fallback actually ran");
    #else
    (void)expect_skips;require(fb_v9_cull_stats[0]==0,"disabled or capacity fallback never culls");
    #endif
    #else
    (void)expect_skips;
    #endif
    fb_free_prepared(p);
}
#endif
int main(void)
{
    #ifdef FB_DISABLE_PREPARED
    puts("PASS: cull skipped with prepared disabled");return 0;
    #else
    fb_prepared_draw draws[4097];
    for(int type=2;type<=3;type++)for(int mode=0;mode<5;mode++) {
        int bytes=type==3?1:4;fb_image *image=fb_new_image(type,73,9,73*bytes+3);require(image!=NULL,"image");
        for(int y=0;y<9;y++)for(int x=0;x<73;x++) {
            unsigned char *p=(unsigned char *)image->content+y*image->line_byte+x*bytes;
            for(int c=0;c<bytes;c++)p[c]=(unsigned char)(next()>>24);
            p[bytes-1]=(unsigned char)(mode==0?0:mode==1?255:mode==2?127:mode==3?(x%5==0?255:1+next()%254):next()>>24);
        }
        for(unsigned i=0;i<48;i++)draws[i]=(fb_prepared_draw){(int)(i%7)*23-41,(int)(i%3)-2,(int)next()};
        draws[40]=(fb_prepared_draw){INT_MIN,INT_MIN,0};draws[41]=(fb_prepared_draw){INT_MAX,INT_MAX,0};
        draws[42]=(fb_prepared_draw){1007,596,0xabcdef};draws[43]=(fb_prepared_draw){1013,593,0x5678ab};
        compare(image,draws,48,mode==1 || mode==3);
        for(unsigned i=0;i<4097;i++)draws[i]=(fb_prepared_draw){3,4,(int)next()};
        compare(image,draws,129,0);compare(image,draws,4097,0);fb_free_image(image);
    }
    fb_image *png=fb_read_png_image("./test.png");require(png!=NULL,"course PNG loaded");unsigned count=0;
    for(int y=-5;y<605;y+=128)for(int x=-5;x<1029;x+=50)draws[count++]=(fb_prepared_draw){x,y,0};
    compare(png,draws,count,1);
    #if defined(FB_CULL_TEST_STATS) && !defined(FB_DISABLE_MANY)
    #if !defined(FB_DISABLE_OPAQUE_CULL) && !defined(FB_DISABLE_ROW_INDEX) && FB_ROW_INDEX_LIMIT > 1 && FB_CULL_MAX_COMMANDS >= 21
    require(fb_v9_cull_stats[1]==128658,"course hidden partial count exactly matches audit");
    printf("course PNG: skipped partial=%llu opaque=%llu; partial executed=427251 (baseline555909)\n",fb_v9_cull_stats[1],fb_v9_cull_stats[2]);
    #endif
    #endif
    /* A disjoint row is proved by command bounds, without suffix bitmaps. */
    draws[0]=(fb_prepared_draw){0,0,0};draws[1]=(fb_prepared_draw){200,0,0};
    compare(png,draws,2,0);
    #if defined(FB_CULL_TEST_STATS) && !defined(FB_DISABLE_MANY)
    require(fb_v9_cull_stats[0]==0,"ordered disjoint rows bypass culling");
    require(fb_v9_cull_stats[3]>0,"ordered disjoint rows use original draw");
    #endif
    fb_free_image(png);free(front_storage);printf("PASS: %u v9 cull full-frame oracle cases\n",tested_cases);return 0;
    #endif
}
