#include "fixture.h"
#include "prepared_api.h"
#ifndef FB_DISABLE_PREPARED
static unsigned rng=0x1037;
static unsigned next(void){rng=rng*1664525u+1013904223u;return rng;}
#endif
int main(void)
{
    require(!fb_prepare_image(NULL),"invalid input rejection");
    #ifdef FB_DISABLE_PREPARED
    puts("PASS: prepared path disabled; caller fallback remains available");return 0;
    #else
    const int positions[][2]={{0,0},{-7,-4},{1010,596},{INT_MIN,INT_MIN},{INT_MAX,INT_MAX},{100,100}};
    static int initial[SCREEN_WIDTH*SCREEN_HEIGHT],expected[SCREEN_WIDTH*SCREEN_HEIGHT];
    for(int type=2;type<=3;type++)for(int mode=0;mode<4;mode++) {
        int bytes=type==3?1:4;
        fb_image *src=fb_new_image(type,37,11,37*bytes+7),*reference=fb_new_image(type,37,11,37*bytes+7);
        require(src && reference,"allocation");
        for(int y=0;y<11;y++)for(int x=0;x<37;x++) {
            unsigned char *p=(unsigned char*)src->content+y*src->line_byte+x*bytes;
            for(int c=0;c<bytes;c++)p[c]=(unsigned char)(next()>>24);
            p[bytes-1]=(unsigned char)(mode==0?0:mode==1?255:mode==2?127:next()>>24);
        }
        memcpy(reference->content,src->content,(size_t)src->line_byte*src->pixel_h);
        fb_prepared_image *prepared=fb_prepare_image(src);require(prepared!=NULL,"snapshot prepare");
        memset(src->content,0,(size_t)src->line_byte*src->pixel_h);fb_free_image(src);
        for(unsigned pos=0;pos<sizeof(positions)/sizeof(*positions);pos++)for(int c=0;c<2;c++) {
            int ink=c?0xabcdef:0x123456;reset_surfaces(0);
            for(int i=0;i<SCREEN_WIDTH*SCREEN_HEIGHT;i++)initial[i]=DRAW_BUF[i]=(int)next();
            fb_draw_image(positions[pos][0],positions[pos][1],reference,ink);memcpy(expected,DRAW_BUF,sizeof(expected));
            struct area area=update_area;
            memcpy(DRAW_BUF,initial,sizeof(initial));AREA_SET_EMPTY(&update_area);
            fb_draw_prepared(positions[pos][0],positions[pos][1],prepared,ink);
            require(!memcmp(expected,DRAW_BUF,sizeof(expected)),"prepared pixels differ from immediate reference");
            require(!memcmp(&area,&update_area,sizeof(area)),"prepared dirty region");check_canaries();tested_cases++;
        }
        #ifdef FB_PREPARED_MANY_API
        fb_prepared_draw draws[48];
        for(unsigned n=0;n<48;n++) {
            unsigned pos=n%6;
            draws[n]=(fb_prepared_draw){positions[pos][0]+(pos<3?(int)(n%4):0),positions[pos][1],(int)next()};
        }
        reset_surfaces(0);
        for(int i=0;i<SCREEN_WIDTH*SCREEN_HEIGHT;i++)initial[i]=DRAW_BUF[i]=(int)next();
        for(unsigned n=0;n<48;n++)fb_draw_image(draws[n].x,draws[n].y,reference,draws[n].color);
        memcpy(expected,DRAW_BUF,sizeof(expected));struct area many_area=update_area;
        memcpy(DRAW_BUF,initial,sizeof(initial));AREA_SET_EMPTY(&update_area);
        fb_draw_prepared_many(prepared,draws,48);
        require(!memcmp(expected,DRAW_BUF,sizeof(expected)),"ordered many-image pixels");
        require(!memcmp(&many_area,&update_area,sizeof(many_area)),"ordered many-image dirty region");
        check_canaries();tested_cases++;
        fb_draw_prepared_many(NULL,draws,48);fb_draw_prepared_many(prepared,NULL,48);fb_draw_prepared_many(prepared,draws,0);
        #endif
        fb_free_prepared(prepared);fb_free_image(reference);
    }
    fb_free_prepared(NULL);printf("PASS: %u prepared snapshot comparisons (lifetime, mutation, clipping, alpha, padding)\n",tested_cases);
    free(front_storage);return 0;
    #endif
}
