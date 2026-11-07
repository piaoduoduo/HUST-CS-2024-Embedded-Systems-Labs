/* Include after text_layout_v5.h. Each batch owns its glyph snapshots; layout
 * cache eviction and font identity changes cannot invalidate queued commands.
 * CSR construction is O(H + G + K), rendering O(K + P): G visible glyph commands,
 * K clipped glyph-row references, P visited pixels. Alpha order is unchanged. */
#ifndef FB_TEXT_BATCH_V9_H
#define FB_TEXT_BATCH_V9_H
#include "text_batch_api_v9.h"
#ifndef FB_TEXT_BATCH_CAPACITY
#define FB_TEXT_BATCH_CAPACITY 1024
#endif
#ifndef FB_TEXT_BATCH_LAYOUTS
#define FB_TEXT_BATCH_LAYOUTS 64
#endif
#ifndef FB_TEXT_BATCH_MAX_BYTES
#define FB_TEXT_BATCH_MAX_BYTES (4U*1024U*1024U)
#endif
#ifndef FB_TEXT_BATCH_ROW_LIMIT
#define FB_TEXT_BATCH_ROW_LIMIT 262144U
#endif
#ifndef FB_TEXT_BATCH_MALLOC
#define FB_TEXT_BATCH_MALLOC malloc
#endif
#ifndef FB_TEXT_BATCH_CALLOC
#define FB_TEXT_BATCH_CALLOC calloc
#endif
#if FB_TEXT_BATCH_CAPACITY < 1 || FB_TEXT_BATCH_LAYOUTS < 1
#error text batch capacities must be positive
#endif
struct fb_text_command_v9 {
    const struct fb_layout_glyph *glyph;
    int left,right,top,bottom,sx,sy;
    uint32_t color;
};
struct fb_text_batch {
    struct fb_layout_entry layouts[FB_TEXT_BATCH_LAYOUTS];
    struct fb_text_command_v9 commands[FB_TEXT_BATCH_CAPACITY];
    unsigned layout_count,count;
    size_t bytes;
};
#ifndef FB_DISABLE_TEXT_BATCH
static void fb_text_row_v9(const struct fb_text_command_v9 *c,int row)
{
    const fb_image *im=c->glyph->image;
    int sy=c->sy+row-c->top,left=c->sx,right=left+c->right-c->left;
    if(c->glyph->ranges) {
        if(left<c->glyph->ranges[sy].left)left=c->glyph->ranges[sy].left;
        if(right>c->glyph->ranges[sy].right)right=c->glyph->ranges[sy].right;
    }
    if(left<right) {
        uint32_t *dst=(uint32_t *)(DRAW_BUF+(size_t)row*SCREEN_WIDTH+c->left+left-c->sx);
        int stride=im->color_type==FB_COLOR_ALPHA_8?1:4;
        const unsigned char *src=(const unsigned char *)im->content+(size_t)sy*im->line_byte+(size_t)left*stride;
        fb_fast_row(dst,src,right-left,im->color_type,c->color);
    }
}
static void fb_text_batch_flush_v9(fb_text_batch *b)
{
    if(!b || !b->count)return;
    size_t offsets[SCREEN_HEIGHT+1]={0},cursor[SCREEN_HEIGHT],total=0;
    for(unsigned i=0;i<b->count;i++)
        for(int y=b->commands[i].top;y<b->commands[i].bottom;y++)offsets[y+1]++;
    for(int y=0;y<SCREEN_HEIGHT;y++){offsets[y+1]+=offsets[y];cursor[y]=offsets[y];}
    total=offsets[SCREEN_HEIGHT];
    uint32_t *indices=total<=FB_TEXT_BATCH_ROW_LIMIT && total<=SIZE_MAX/sizeof(*indices)
        ?FB_TEXT_BATCH_MALLOC(total*sizeof(*indices)):NULL;
    if(indices) {
        for(unsigned i=0;i<b->count;i++)
            for(int y=b->commands[i].top;y<b->commands[i].bottom;y++)indices[cursor[y]++]=i;
        /* Only disjoint destination rows run concurrently; commands within
         * every row retain their submission order, including overlapping text. */
        #ifdef _OPENMP
        #pragma omp parallel for schedule(static) if(total>=(FB_PARALLEL_MIN_PIXELS+7)/8)
        #endif
        for(int y=0;y<SCREEN_HEIGHT;y++)
            for(size_t j=offsets[y];j<offsets[y+1];j++)fb_text_row_v9(&b->commands[indices[j]],y);
        free(indices);
    } else {
        /* No allocation or index capacity: exact original command order. */
        for(unsigned i=0;i<b->count;i++)
            for(int y=b->commands[i].top;y<b->commands[i].bottom;y++)fb_text_row_v9(&b->commands[i],y);
    }
    b->count=0;
}
static void fb_text_batch_release_v9(fb_text_batch *b)
{
    for(unsigned i=0;i<b->layout_count;i++)fb_layout_release(&b->layouts[i]);
    b->layout_count=0;b->bytes=0;
}
static struct fb_layout_entry *fb_text_snapshot_v9(fb_text_batch *b,const char *text,int size)
{
    const void *font=fb_font_identity();
    for(unsigned i=0;i<b->layout_count;i++) {
        struct fb_layout_entry *e=&b->layouts[i];
        if(e->font==font && e->size==size && !strcmp(e->text,text))return e;
    }
    if(b->layout_count==FB_TEXT_BATCH_LAYOUTS) {
        fb_text_batch_flush_v9(b);fb_text_batch_release_v9(b);
    }
    struct fb_layout_entry *source=fb_layout_get(text,size);
    if(!source)return NULL;
    struct fb_layout_entry e={0};
    size_t bytes=(size_t)source->count*sizeof(*e.glyphs);
    if(bytes>FB_TEXT_BATCH_MAX_BYTES-b->bytes)return NULL;
    e.glyphs=FB_TEXT_BATCH_CALLOC((size_t)source->count,sizeof(*e.glyphs));
    if(!e.glyphs)return NULL;
    e.font=source->font;e.size=source->size;memcpy(e.text,source->text,sizeof(e.text));
    for(int i=0;i<source->count;i++) {
        const struct fb_layout_glyph *g=&source->glyphs[i];
        const fb_image *im=g->image;
        if(!im || im->pixel_w<0 || im->pixel_h<0 || im->line_byte<0
           || (im->pixel_h && (size_t)im->line_byte>SIZE_MAX/(size_t)im->pixel_h))goto fail;
        size_t pixels=(size_t)im->pixel_h*im->line_byte;
        size_t ranges=g->ranges?(size_t)im->pixel_h*sizeof(*g->ranges):0;
        if(pixels>FB_TEXT_BATCH_MAX_BYTES-b->bytes-bytes
           || sizeof(*im)>FB_TEXT_BATCH_MAX_BYTES-b->bytes-bytes-pixels
           || ranges>FB_TEXT_BATCH_MAX_BYTES-b->bytes-bytes-pixels-sizeof(*im))goto fail;
        fb_image *copy=FB_TEXT_BATCH_MALLOC(sizeof(*copy)+pixels);
        if(!copy)goto fail;
        *copy=*im;copy->content=(char *)(copy+1);
        if(pixels)memcpy(copy->content,im->content,pixels);
        struct fb_layout_glyph *out=&e.glyphs[e.count++];
        *out=*g;out->image=copy;out->ranges=NULL;
        if(ranges) {
            out->ranges=FB_TEXT_BATCH_MALLOC(ranges);
            if(!out->ranges)goto fail;
            memcpy(out->ranges,g->ranges,ranges);
        }
        bytes+=sizeof(*copy)+pixels+ranges;
    }
    b->bytes+=bytes;b->layouts[b->layout_count]=e;
    return &b->layouts[b->layout_count++];
fail:
    fb_layout_release(&e);return NULL;
}
#endif
fb_text_batch *fb_text_batch_begin(void)
{
    #ifdef FB_DISABLE_TEXT_BATCH
    return NULL;
    #else
    return FB_TEXT_BATCH_CALLOC(1,sizeof(fb_text_batch));
    #endif
}
int fb_text_batch_add(fb_text_batch *b,int x,int y,const char *text,int size,int color)
{
    if(!text || !*text)return 0;
    #ifdef FB_DISABLE_TEXT_BATCH
    (void)b;fb_draw_text(x,y,(char *)text,size,color);return 1;
    #else
    if(!b){fb_draw_text(x,y,(char *)text,size,color);return 1;}
    struct fb_layout_entry *layout=fb_text_snapshot_v9(b,text,size);
    if(!layout) {
        fb_text_batch_flush_v9(b);fb_draw_text(x,y,(char *)text,size,color);return 1;
    }
    for(int i=0;i<layout->count;i++) {
        const struct fb_layout_glyph *g=&layout->glyphs[i];
        const fb_image *im=g->image;
        int64_t gx=(int64_t)x+g->offset+g->info.left,gy=(int64_t)y-g->info.top;
        int64_t l=gx<0?0:gx,t=gy<0?0:gy,r=gx+im->pixel_w,d=gy+im->pixel_h;
        if(r>SCREEN_WIDTH)r=SCREEN_WIDTH;
        if(d>SCREEN_HEIGHT)d=SCREEN_HEIGHT;
        if(l>=r || t>=d)continue;
        if(b->count==FB_TEXT_BATCH_CAPACITY)fb_text_batch_flush_v9(b);
        b->commands[b->count++]=(struct fb_text_command_v9){g,(int)l,(int)r,(int)t,(int)d,(int)(l-gx),(int)(t-gy),(uint32_t)color};
        _begin_draw((int)l,(int)t,(int)(r-l),(int)(d-t));
    }
    return 1;
    #endif
}
void fb_text_batch_end(fb_text_batch *b)
{
    #ifndef FB_DISABLE_TEXT_BATCH
    if(b){fb_text_batch_flush_v9(b);fb_text_batch_release_v9(b);free(b);}
    #else
    (void)b;
    #endif
}
#endif
