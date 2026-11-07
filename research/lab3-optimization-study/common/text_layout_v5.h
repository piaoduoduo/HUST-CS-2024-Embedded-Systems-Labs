/* Bounded layout cache; keeps separate owned glyphs and preserves draw order. */
#ifndef FB_TEXT_LAYOUT_H
#define FB_TEXT_LAYOUT_H
const void *fb_font_identity(void);
#define FB_LAYOUT_SLOTS 8
#define FB_LAYOUT_GLYPHS 128
#define FB_LAYOUT_TEXT_BYTES 256
#define FB_LAYOUT_MAX_BYTES (64U*1024U)
struct fb_glyph_row_range {uint16_t left,right;};
struct fb_layout_glyph {fb_image *image;fb_font_info info;int offset;struct fb_glyph_row_range *ranges;};
struct fb_layout_entry {
    const void *font;
    int size,count;
    char text[FB_LAYOUT_TEXT_BYTES+1];
    struct fb_layout_glyph *glyphs;
};
static struct fb_layout_entry fb_layouts[FB_LAYOUT_SLOTS];
static unsigned fb_layout_next;
static int fb_layout_cleanup_registered;
static void fb_layout_release(struct fb_layout_entry *entry)
{
    for(int i=0;i<entry->count;++i) {
        fb_free_image(entry->glyphs[i].image);free(entry->glyphs[i].ranges);
    }
    free(entry->glyphs);
    memset(entry,0,sizeof(*entry));
}
static void fb_layout_cleanup(void)
{
    for(int i=0;i<FB_LAYOUT_SLOTS;++i) fb_layout_release(&fb_layouts[i]);
}
static struct fb_layout_entry *fb_layout_get(const char *text,int size)
{
    const void *font=fb_font_identity();
    if(!font || size<=0 || size>128) return NULL;
    size_t length=strlen(text);
    if(!length || length>FB_LAYOUT_TEXT_BYTES) return NULL;
    for(int i=0;i<FB_LAYOUT_SLOTS;++i) {
        struct fb_layout_entry *e=&fb_layouts[i];
        if(e->glyphs && e->font==font && e->size==size && !strcmp(e->text,text)) return e;
    }
    struct fb_layout_entry e={0};
    e.glyphs=calloc(FB_LAYOUT_GLYPHS,sizeof(*e.glyphs));
    if(!e.glyphs) return NULL;
    e.font=font;e.size=size;memcpy(e.text,text,length+1);
    size_t index=0,total_bytes=0;
    int64_t advance=0;
    while(index<length && e.count<FB_LAYOUT_GLYPHS) {
        fb_font_info info={0};
        fb_image *image=fb_read_font_image(text+index,size,&info);
        if(!image || info.bytes<=0 || (size_t)info.bytes>length-index) {
            fb_free_image(image);fb_layout_release(&e);return NULL;
        }
        size_t bytes=(size_t)image->line_byte*image->pixel_h;
        if(bytes>FB_LAYOUT_MAX_BYTES-total_bytes || advance<INT_MIN || advance>INT_MAX) {
            fb_free_image(image);fb_layout_release(&e);return NULL;
        }
        struct fb_glyph_row_range *ranges=NULL;
        #ifndef FB_DISABLE_TEXT_RANGES
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
        #endif
        e.glyphs[e.count++]=(struct fb_layout_glyph){image,info,(int)advance,ranges};
        total_bytes+=bytes;index+=(size_t)info.bytes;advance+=info.advance_x;
    }
    if(index!=length) {fb_layout_release(&e);return NULL;}
    if(!fb_layout_cleanup_registered) {
        if(atexit(fb_layout_cleanup)) {fb_layout_release(&e);return NULL;}
        fb_layout_cleanup_registered=1;
    }
    struct fb_layout_entry *slot=&fb_layouts[fb_layout_next];
    fb_layout_release(slot);*slot=e;
    fb_layout_next=(fb_layout_next+1)%FB_LAYOUT_SLOTS;
    return slot;
}
static void fb_layout_draw_glyph(int x,int y,const struct fb_layout_glyph *g,int color)
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
void fb_draw_text(int x,int y,char *text,int font_size,int color)
{
    if(!text) return;
    struct fb_layout_entry *layout=fb_layout_get(text,font_size);
    if(layout) {
        for(int i=0;i<layout->count;++i) {
            const struct fb_layout_glyph *g=&layout->glyphs[i];
            fb_layout_draw_glyph(x+g->offset+g->info.left,y-g->info.top,g,color);
        }
        return;
    }
    size_t i=0,length=strlen(text);
    while(i<length) {
        fb_font_info info={0};
        fb_image *image=fb_read_font_image(text+i,font_size,&info);
        if(!image) break;
        if(info.bytes<=0 || (size_t)info.bytes>length-i) {fb_free_image(image);break;}
        fb_draw_image(x+info.left,y-info.top,image,color);
        fb_free_image(image);x+=info.advance_x;i+=(size_t)info.bytes;
    }
}
#endif
