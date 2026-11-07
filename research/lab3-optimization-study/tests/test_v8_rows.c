#include <stdio.h>
#include <stdlib.h>
#include "fast_pixels_v8.h"
static unsigned checks,seed=0x1037;
static unsigned next(void){seed=seed*1664525u+1013904223u;return seed;}
static void check(int ok){checks++;if(!ok){fputs("row oracle failed\n",stderr);exit(1);}}
static uint32_t oracle(uint32_t s,uint32_t d,unsigned a)
{
    if(!a)return d;
    uint32_t out=0xff000000u;
    for(int c=0;c<3;c++)out|=((((s>>(8*c))&255)*a+((d>>(8*c))&255)*(255-a)+127)/255)<<(8*c);
    return out;
}
int main(void)
{
    unsigned char storage[258*4+8];uint32_t dst[260],expected[260];
    for(int w=0;w<=257;w++)for(int type=1;type<=3;type++)for(int mode=0;mode<4;mode++)for(int offset=0;offset<4;offset++){
        unsigned char *src=storage+offset;
        uint32_t ink=next();
        for(int i=0;i<260;i++)dst[i]=expected[i]=next();
        for(int i=0;i<w;i++){
            unsigned a=mode==0?0:mode==1?255:mode==2?(unsigned)(i%3==0?0:i%3==1?255:127):next()>>24;
            uint32_t s=next();
            if(type==3){src[i]=(unsigned char)a;s=ink;}
            else{memcpy(src+4*i,&s,4);if(type==2)src[4*i+3]=(unsigned char)a;}
            expected[i+1]=type==1?s:oracle(s,expected[i+1],a);
        }
        fb_fast_row(dst+1,src,w,type,ink);
        for(int i=0;i<260;i++)check(dst[i]==expected[i]);
    }
#if FB_HAVE_NEON
    for(unsigned s=0;s<256;s++)for(unsigned d=0;d<256;d++)for(unsigned a=0;a<256;a+=8){
        unsigned char aa[8];for(int k=0;k<8;k++)aa[k]=(unsigned char)(a+k);
        uint8x8_t v=fb_mix8(vdup_n_u8((uint8_t)s),vdup_n_u8((uint8_t)d),vld1_u8(aa));
        unsigned char actual[8];vst1_u8(actual,v);
        for(int k=0;k<8;k++)check(actual[k]==(s*(a+k)+d*(255-a-k)+127)/255);
    }
#endif
    printf("PASS: %u row/channel oracle checks (unaligned source, tails, zero/full/mixed alpha)\n",checks);
    return 0;
}
