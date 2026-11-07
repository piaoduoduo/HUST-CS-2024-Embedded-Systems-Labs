#include "fixture.h"
int main(void)
{
#ifdef FB_DISABLE_PREPARED
    require(!fb_prepare_image(NULL),"disabled prepare");puts("PASS: product storage caller fallback");return 0;
#else
    unsigned cases=0;
    for(int type=2;type<=3;type++)for(int mode=0;mode<4;mode++) {
        int bytes=type==2?4:1;fb_image *image=fb_new_image(type,37,11,37*bytes+7);
        require(image!=NULL,"source allocation");
        for(int y=0;y<11;y++)for(int x=0;x<37;x++) {
            unsigned char *pixel=(unsigned char *)image->content+y*image->line_byte+x*bytes;
            for(int c=0;c<bytes;c++)pixel[c]=(unsigned char)(x*71+y*11+c*53);
            pixel[bytes-1]=(unsigned char)(mode==0?0:mode==1?255:mode==2?127:1+(x*11+y*37)%254);
        }
        fb_prepared_image *p=fb_prepare_image(image);require(p!=NULL,"prepared allocation");
        int enabled=type==2 && mode>=2;
#ifdef FB_DISABLE_PRODUCTS
        enabled=0;
#elif defined(FB_PRODUCT_MAX_PIXELS)
        if(407>FB_PRODUCT_MAX_PIXELS)enabled=0;
#endif
        require((p->products!=NULL)==enabled,"source products allocation/skip/fallback");
        require((p->inverse!=NULL)==enabled,"inverse allocation/skip/fallback");
        if(enabled)for(int y=0;y<11;y++)for(int x=0;x<37;x++) {
            const unsigned char *pixel=(unsigned char *)image->content+y*image->line_byte+x*4;
            size_t pos=(size_t)y*37+x;
            require(p->inverse[pos]==255-pixel[3],"inverse cache value");
            for(int c=0;c<3;c++)require(p->products[pos+(size_t)c*407]==pixel[c]*pixel[3],"unrounded product cache value");
        }
        fb_free_prepared(p);fb_free_image(image);cases++;
    }
    printf("PASS: %u product storage cases (presence, exact values, skip, capacity fallback)\n",cases);return 0;
#endif
}
