from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=(ROOT/'common/graphic-fast.c').read_text(encoding='utf-8')
source=source.replace('void fb_draw_rect(int x, int y, int w, int h, int color)\n{',
 '''#include "fast_pixels.h"
#include "geometry_v4.h"
void fb_draw_rect(int x, int y, int w, int h, int color)
{
    if(w>0 && h>0 && (unsigned)x<SCREEN_WIDTH && (unsigned)y<SCREEN_HEIGHT
       && w<=SCREEN_WIDTH-x && h<=SCREEN_HEIGHT-y) {
        fb_fill_rect_inside(x,y,w,h,color);return;
    }''')
old='''    for(int row = y; row < y + h; ++row) {
        int *pixel = buf + row * SCREEN_WIDTH + x;
        for(int column = 0; column < w; ++column) {
            pixel[column] = color;
        }
    }'''
assert source.count(old)==1
source=source.replace('    int *buf = _begin_draw(x, y, w, h);\n\n'+old,'    fb_fill_rect_inside(x,y,w,h,color);')
source=source.replace('void fb_draw_line(int x1, int y1, int x2, int y2, int color)\n{',
 '''void fb_draw_line(int x1, int y1, int x2, int y2, int color)
{
    if((unsigned)x1<SCREEN_WIDTH && (unsigned)x2<SCREEN_WIDTH
       && (unsigned)y1<SCREEN_HEIGHT && (unsigned)y2<SCREEN_HEIGHT) {
        fb_line_inside(x1,y1,x2,y2,color);return;
    }''')
source=source.replace('#include "text_layout.h"','#include "text_layout_v4.h"')
(ROOT/'common/graphic-v4.c').write_text(source,encoding='utf-8')
(ROOT/'common/graphic-v4-batch.c').write_text(source+'\n#include "opaque_batch.h"\n',encoding='utf-8')
layout=(ROOT/'common/text_layout.h').read_text(encoding='utf-8')
layout=layout.replace('struct fb_layout_glyph {fb_image *image;fb_font_info info;int offset;};',
 '''struct fb_glyph_row_range {uint16_t left,right;};
struct fb_layout_glyph {fb_image *image;fb_font_info info;int offset;struct fb_glyph_row_range *ranges;};''')
layout=layout.replace('for(int i=0;i<entry->count;++i) fb_free_image(entry->glyphs[i].image);',
 '''for(int i=0;i<entry->count;++i) {
        fb_free_image(entry->glyphs[i].image);free(entry->glyphs[i].ranges);
    }''')
layout=layout.replace('e.glyphs[e.count++]=(struct fb_layout_glyph){image,info,(int)advance};',
 '''struct fb_glyph_row_range *ranges=NULL;
        size_t range_bytes=(size_t)image->pixel_h*sizeof(*ranges);
        if(image->color_type==FB_COLOR_ALPHA_8 && image->content && image->pixel_w>0 && image->pixel_h>0 && image->pixel_w<=UINT16_MAX
           && range_bytes<=FB_LAYOUT_MAX_BYTES-total_bytes-bytes) {
            ranges=calloc((size_t)image->pixel_h,sizeof(*ranges));
            if(ranges) {
                for(int row=0;row<image->pixel_h;row++) {
                    const unsigned char *p=(const unsigned char *)image->content+(size_t)row*image->line_byte;
                    int left=0,right=image->pixel_w;
                    while(left<right && !p[left])left++;
                    while(right>left && !p[right-1])right--;
                    ranges[row]=(struct fb_glyph_row_range){(uint16_t)left,(uint16_t)right};
                }
                total_bytes+=range_bytes;
            }
        }
        e.glyphs[e.count++]=(struct fb_layout_glyph){image,info,(int)advance,ranges};''')
marker='void fb_draw_text(int x,int y,char *text,int font_size,int color)'
helper='''static void fb_layout_draw_glyph(int x,int y,const struct fb_layout_glyph *g,int color)
{
    fb_image *image=g->image;
    if(!g->ranges){fb_draw_image(x,y,image,color);return;}
    if(!image->content || image->pixel_w<=0 || image->pixel_h<=0)return;
    int64_t left=x,top=y,right=(int64_t)x+image->pixel_w,bottom=(int64_t)y+image->pixel_h;
    if(left<0)left=0;
    if(top<0)top=0;
    if(right>SCREEN_WIDTH)right=SCREEN_WIDTH;
    if(bottom>SCREEN_HEIGHT)bottom=SCREEN_HEIGHT;
    if(left>=right || top>=bottom)return;
    _begin_draw((int)left,(int)top,(int)(right-left),(int)(bottom-top));
    int clip_left=(int)(left-x),clip_right=(int)(right-x);
    for(int row=(int)top;row<(int)bottom;row++) {
        int source_y=(int)((int64_t)row-y);
        int l=g->ranges[source_y].left,r=g->ranges[source_y].right;
        if(l<clip_left)l=clip_left;
        if(r>clip_right)r=clip_right;
        if(l<r)fb_alpha_row((uint32_t *)(DRAW_BUF+row*SCREEN_WIDTH+(int)((int64_t)x+l)),
            (const unsigned char *)image->content+(size_t)source_y*image->line_byte+l,r-l,(uint32_t)color);
    }
}
'''
layout=layout.replace(marker,helper+marker)
layout=layout.replace('fb_draw_image(x+g->offset+g->info.left,y-g->info.top,g->image,color);',
                      'fb_layout_draw_glyph(x+g->offset+g->info.left,y-g->info.top,g,color);')
(ROOT/'common/text_layout_v4.h').write_text(layout,encoding='utf-8')
print('Generated isolated v4 geometry and immutable cached-glyph row ranges.')
