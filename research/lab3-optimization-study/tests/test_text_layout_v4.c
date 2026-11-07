#include "fixture.h"
#include "image-memory-under-test.c"
static unsigned requests;
static uintptr_t font_token=1;
const void *fb_font_identity(void){return (const void *)font_token;}
void font_init(char *p){(void)p;}
fb_image *fb_read_jpeg_image(char *p){(void)p;return NULL;}
fb_image *fb_read_png_image(char *p){(void)p;return NULL;}
fb_image *fb_read_font_image(const char *text,int size,fb_font_info *info)
{
    requests++;
    unsigned code=(unsigned char)text[0];
    int bytes=code<128?1:code<224?2:code<240?3:4;
    int w=code==' '?0:9,h=code==' '?0:7;
    fb_image *im=fb_new_image(FB_COLOR_ALPHA_8,w,h,0);
    if(!im)return NULL;
    *info=(fb_font_info){bytes,6,-1,5};
    for(int y=0;y<h;y++)for(int x=0;x<w;x++)
        im->content[y*im->line_byte+x]=(char)((code=='z' || y==0 || y==6 || x<2 || x>=7)?0:(x+y+code+size+font_token)%3==0?0:(x+y)%3==0?255:(x*37+y*11+size)%256);
    return im;
}
static void reference(int x,int y,char *text,int size,int color)
{
    for(size_t i=0;i<strlen(text);){
        fb_font_info f;fb_image *im=fb_read_font_image(text+i,size,&f);
        fb_draw_image(x+f.left,y-f.top,im,color);fb_free_image(im);x+=f.advance_x;i+=f.bytes;
    }
}
static void compare(char *text,int size,int x,int y,int color,int must_hit)
{
    static int initial[SCREEN_WIDTH*SCREEN_HEIGHT],expected[SCREEN_WIDTH*SCREEN_HEIGHT];
    reset_surfaces(0);
    for(int i=0;i<SCREEN_WIDTH*SCREEN_HEIGHT;i++)initial[i]=DRAW_BUF[i]=(int)(0x10371234u+i*1664525u);
    reference(x,y,text,size,color);memcpy(expected,DRAW_BUF,sizeof(expected));
    memcpy(DRAW_BUF,initial,sizeof(initial));AREA_SET_EMPTY(&update_area);
    unsigned before=requests;
    fb_draw_text(x,y,text,size,color);
    require(!memcmp(expected,DRAW_BUF,sizeof(expected)),"cached text pixels/order/background differ");
    if(must_hit)require(requests==before,"cache hit rendered/copied glyphs again");
    check_canaries();fb_update();check_canaries();tested_cases++;
}
int main(void)
{
    for(int i=0;i<30;i++)compare("A g嵌入式",40,i%3?-4:100,i%2?3:300,i*1234567,i>0);
    font_token=2;compare("A g嵌入式",40,1020,598,0xabcdef,0);
    compare("A g嵌入式",40,10,20,0x123456,1);
    for(int i=0;i<12;i++){char s[30];snprintf(s,sizeof(s),"eviction %d",i);compare(s,20,30,50,0xaa5500,0);}
    compare("A g嵌入式",40,10,20,0xabcdef,0);
    compare("A g嵌入式",40,10,20,0xff0022,1);
    char longtext[300];memset(longtext,'a',299);longtext[299]=0;
    compare(longtext,40,0,100,0x772200,0);compare("oversize",512,0,100,0x772200,0);
    compare("zzzz",40,100,100,0x123456,0);compare("zzzz",40,-3,2,0xabcdef,1);fb_layout_cleanup();
    printf("PASS: %u text-layout cases (overlap, clipping, backgrounds, colors, font identity, eviction, fallback)\n",tested_cases);
    free(front_storage);return 0;
}

