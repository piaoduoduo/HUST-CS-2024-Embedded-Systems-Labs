/* Bounded layout cache; keeps separate owned glyphs and preserves draw order. */
#ifndef FB_TEXT_LAYOUT_H
#define FB_TEXT_LAYOUT_H
const void *fb_font_identity(void);
#define FB_LAYOUT_SLOTS 8
#define FB_LAYOUT_GLYPHS 128
#define FB_LAYOUT_TEXT_BYTES 256
#define FB_LAYOUT_MAX_BYTES (64U*1024U)
struct fb_layout_glyph {fb_image *image;fb_font_info info;int offset;};
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
    for(int i=0;i<entry->count;++i) fb_free_image(entry->glyphs[i].image);
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
        e.glyphs[e.count++]=(struct fb_layout_glyph){image,info,(int)advance};
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
void fb_draw_text(int x,int y,char *text,int font_size,int color)
{
    if(!text) return;
    struct fb_layout_entry *layout=fb_layout_get(text,font_size);
    if(layout) {
        for(int i=0;i<layout->count;++i) {
            const struct fb_layout_glyph *g=&layout->glyphs[i];
            fb_draw_image(x+g->offset+g->info.left,y-g->info.top,g->image,color);
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
