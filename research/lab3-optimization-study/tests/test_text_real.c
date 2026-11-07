/* Board-only: compare cached layout with sequential real FreeType glyph drawing. */
#include "fixture.h"
static void reference(int x,int y,char *text,int size,int color)
{
    for(size_t i=0;i<strlen(text);){
        fb_font_info f;fb_image *im=fb_read_font_image(text+i,size,&f);
        require(im!=NULL,"real FreeType glyph load");
        fb_draw_image(x+f.left,y-f.top,im,color);fb_free_image(im);x+=f.advance_x;i+=f.bytes;
    }
}
int main(int argc,char **argv)
{
    require(argc==2,"font path");font_init(argv[1]);
    static int initial[SCREEN_WIDTH*SCREEN_HEIGHT],expected[SCREEN_WIDTH*SCREEN_HEIGHT];
    char *texts[]={"嵌入式系统实验","Embedded System Experiment","床前明月光，疑是地上霜。","A g é 😀"};
    for(int pass=0;pass<3;pass++)for(int t=0;t<4;t++)for(int clipping=0;clipping<3;clipping++){
        int x=clipping==0?20:clipping==1?-12:1000;
        int y=clipping==0?100:clipping==1?3:598;
        int color=pass*0x331177+0x123456,size=t==0?40:t==1?20:64;
        reset_surfaces(0);
        for(int i=0;i<SCREEN_WIDTH*SCREEN_HEIGHT;i++)initial[i]=DRAW_BUF[i]=(int)(0x10371234u+i*1664525u);
        reference(x,y,texts[t],size,color);memcpy(expected,DRAW_BUF,sizeof(expected));
        memcpy(DRAW_BUF,initial,sizeof(initial));AREA_SET_EMPTY(&update_area);
        fb_draw_text(x,y,texts[t],size,color);
        require(!memcmp(expected,DRAW_BUF,sizeof(expected)),"real cached text differs from ordered glyph reference");
        check_canaries();tested_cases++;
    }
    fb_layout_cleanup();free(front_storage);
    printf("PASS: %u real FreeType text comparisons\n",tested_cases);return 0;
}
