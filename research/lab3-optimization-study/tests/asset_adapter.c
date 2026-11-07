/* HOST SIMULATION ONLY: decoded assets and glyph masks are produced by Pillow.
 * The deployment package uses the course's actual libjpeg/libpng/FreeType code. */
#include "../common/common.h"
#include "image-memory-under-test.c"

void font_init(char *path) { (void)path; }
static fb_image *load_pixels(const char *name)
{
    char path[256];snprintf(path,sizeof(path),"build/assets/%s.bgra",name);
    FILE *f=fopen(path,"rb");if(!f) return NULL;
    int32_t header[3];if(fread(header,sizeof(header),1,f)!=1) {fclose(f);return NULL;}
    fb_image *img=fb_new_image(header[2],header[0],header[1],0);
    if(img && fread(img->content,(size_t)img->line_byte*img->pixel_h,1,f)!=1) {fb_free_image(img);img=NULL;}
    fclose(f);return img;
}
fb_image *fb_read_jpeg_image(char *path) {(void)path;return load_pixels("test.jpg");}
fb_image *fb_read_png_image(char *path) {(void)path;return load_pixels("test.png");}
fb_image *fb_read_font_image(const char *text,int size,fb_font_info *info)
{
    const unsigned char *p=(const unsigned char *)text;
    unsigned code;int bytes;
    if(p[0]<0x80) {code=p[0];bytes=1;}
    else if(p[0]<0xe0) {code=((p[0]&31)<<6)|(p[1]&63);bytes=2;}
    else if(p[0]<0xf0) {code=((p[0]&15)<<12)|((p[1]&63)<<6)|(p[2]&63);bytes=3;}
    else {code=((p[0]&7)<<18)|((p[1]&63)<<12)|((p[2]&63)<<6)|(p[3]&63);bytes=4;}
    char path[256];snprintf(path,sizeof(path),"build/assets/glyph-%x-%d.bin",code,size);
    FILE *f=fopen(path,"rb");if(!f) {fprintf(stderr,"Missing host glyph: %s\n",path);return NULL;}
    int32_t h[5];if(fread(h,sizeof(h),1,f)!=1) {fclose(f);return NULL;}
    fb_image *img=fb_new_image(FB_COLOR_ALPHA_8,h[0],h[1],h[0]);
    if(img && h[0]*h[1]>0 && fread(img->content,(size_t)h[0]*h[1],1,f)!=1) {fb_free_image(img);img=NULL;}
    fclose(f);
    if(info) *info=(fb_font_info){bytes,h[4],h[2],-h[3]};
    return img;
}
