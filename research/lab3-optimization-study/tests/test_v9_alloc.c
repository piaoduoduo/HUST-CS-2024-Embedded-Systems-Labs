/* Fail only graphics-side malloc calls; image ownership remains real. */
#include <stdlib.h>
static int fail_enabled,alloc_before_fail,failures;
static void *checked_malloc(size_t size)
{
    if(fail_enabled && alloc_before_fail--==0){fail_enabled=0;failures++;return NULL;}
    return malloc(size);
}
#define malloc checked_malloc
#include "fixture.h"
#undef malloc
int main(void)
{
    #if defined(FB_DISABLE_PREPARED) || defined(FB_DISABLE_MANY)
    puts("PASS: allocation-fallback path disabled");return 0;
    #else
    static int initial[SCREEN_WIDTH*SCREEN_HEIGHT],expected[SCREEN_WIDTH*SCREEN_HEIGHT];
    fb_image *image=fb_new_image(FB_COLOR_RGBA_8888,71,5,71*4);require(image!=NULL,"allocate source");
    for(int y=0;y<5;y++)for(int x=0;x<71;x++) {
        unsigned char *s=(unsigned char *)image->content+y*image->line_byte+x*4;
        s[0]=(unsigned char)(x*7);s[1]=(unsigned char)(y*47);s[2]=(unsigned char)(x*3+y);
        s[3]=(unsigned char)(x%5==0?255:x%5==1?0:127);
    }
    fb_prepared_image *p=fb_prepare_image(image);require(p!=NULL,"prepare before fault injection");
    fb_prepared_draw draws[8];for(unsigned i=0;i<8;i++)draws[i]=(fb_prepared_draw){(int)i*11-3,7,(int)i*0x123456};
    reset_surfaces(0);
    for(int i=0;i<SCREEN_WIDTH*SCREEN_HEIGHT;i++)initial[i]=DRAW_BUF[i]=(int)(0x12340000u+(unsigned)i*137);
    for(unsigned i=0;i<8;i++)fb_draw_image(draws[i].x,draws[i].y,image,draws[i].color);
    memcpy(expected,DRAW_BUF,sizeof(expected));struct area expected_area=update_area;
    for(int failing=0;failing<2;failing++) {
        memcpy(DRAW_BUF,initial,sizeof(initial));AREA_SET_EMPTY(&update_area);
        #ifdef FB_CULL_TEST_STATS
        memset(fb_v9_cull_stats,0,sizeof(fb_v9_cull_stats));
        #endif
        fail_enabled=1;alloc_before_fail=failing;int prior=failures;
        fb_draw_prepared_many(p,draws,8);fail_enabled=0;
        #if !defined(FB_DISABLE_ROW_INDEX) && FB_ROW_INDEX_LIMIT>1
        require(failures==prior+1,"requested malloc failure occurred");
        #else
        if(!failing)require(failures==prior+1,"command malloc failure occurred");
        #endif
        require(!memcmp(expected,DRAW_BUF,sizeof(expected)),"allocation failure preserves exact pixels");
        require(!memcmp(&expected_area,&update_area,sizeof(expected_area)),"allocation failure dirty region");
        #ifdef FB_CULL_TEST_STATS
        require(fb_v9_cull_stats[0]==0,"failed storage falls back without culling");
        #endif
        check_canaries();
    }
    fb_free_prepared(p);fb_free_image(image);free(front_storage);
    puts("PASS: commands and CSR-index malloc failures preserve ordered draw and dirty bounds");return 0;
    #endif
}
