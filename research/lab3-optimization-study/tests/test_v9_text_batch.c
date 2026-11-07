#include <stdlib.h>
static int text_failure=-1,text_allocations;
static void *text_test_malloc(size_t n){return text_allocations++==text_failure?NULL:malloc(n);}
static void *text_test_calloc(size_t n,size_t m){return text_allocations++==text_failure?NULL:calloc(n,m);}
#define FB_TEXT_BATCH_MALLOC text_test_malloc
#define FB_TEXT_BATCH_CALLOC text_test_calloc
#include "fixture.h"
#include "image-memory-under-test.c"
static uintptr_t font_token=1;
const void *fb_font_identity(void){return (const void *)font_token;}
void font_init(char *p){(void)p;}
fb_image *fb_read_jpeg_image(char *p){(void)p;return NULL;}
fb_image *fb_read_png_image(char *p){(void)p;return NULL;}
fb_image *fb_read_font_image(const char *text,int size,fb_font_info *info)
{
    if(size<=0 || !text || !*text)return NULL;
    unsigned code=(unsigned char)text[0];int bytes=code<128?1:code<224?2:code<240?3:4;
    int w=code==' '?0:7+size%13,h=code==' '?0:6+size%11;
    fb_image *im=fb_new_image(FB_COLOR_ALPHA_8,w,h,w+3);
    if(!im)return NULL;
    *info=(fb_font_info){bytes,4,-2,5};memset(im->content,0x71,(size_t)im->line_byte*h);
    for(int y=0;y<h;y++)for(int x=0;x<w;x++)
        im->content[y*im->line_byte+x]=(char)((code=='z' || y==0 || y==h-1 || x<2 || x>=w-2)?0:(x+y+code+size+font_token)%3==0?0:(x+y)%3==0?255:(x*37+y*11+size)%256);
    return im;
}
#define FB_TEST_SET_FONT(v) (font_token=(uintptr_t)(v))
#define FB_TEST_ALLOC_FAIL(v) (text_failure=(v),text_allocations=0)
#include "test_v9_text_cases.h"
int main(void)
{
    /* Suppress unused warnings in compile-time-disabled configuration. */
    (void)text_test_malloc;(void)text_test_calloc;
    for(int i=0;i<10;i++)text_test_v9(i,-1);
    for(int i=0;i<32;i++)text_test_v9(9,i);
    int faults[]={0,1,2,3,4,5,8,16,32,64,128,256,512,1024,2048};
    for(unsigned i=0;i<sizeof(faults)/sizeof(faults[0]);i++)text_test_v9(3,faults[i]);
    text_null_batch_v9();
    printf("PASS: %u ordered text batch cases (full-frame/dirty/canaries, UTF8, overlap, clipping, mutable input, font identity, cache eviction, allocation failures)\n",tested_cases);
    free(front_storage);return 0;
}
