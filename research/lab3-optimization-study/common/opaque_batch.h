/* Private implementation: reverse opaque coverage, independent target rows. */
#include "batch_api.h"
#ifndef FB_BATCH_CAPACITY
#define FB_BATCH_CAPACITY 256
#endif
struct fb_batch_command {
    int left,right,top,bottom,stride;
    const unsigned char *source;
};
struct fb_opaque_batch {
    unsigned count;
    struct fb_batch_command commands[FB_BATCH_CAPACITY];
    fb_batch_stats stats;
};
struct fb_covered_span {int left,right;};
struct fb_row_stats {uint64_t writes,spans,checks,comparisons;};
static struct fb_row_stats fb_batch_row(const fb_opaque_batch *batch,int y)
{
    /* At most ceil(width/2) non-adjacent nonempty integer intervals exist. */
    struct fb_covered_span covered[(SCREEN_WIDTH+1)/2+1];
    int count=0;
    struct fb_row_stats result={0};
    for(unsigned command=batch->count;command>0;--command) {
        const struct fb_batch_command *c=&batch->commands[command-1];
        result.checks++;
        if(y<c->top || y>=c->bottom)continue;
        int cursor=c->left;
        const unsigned char *row=c->source+(size_t)(y-c->top)*c->stride;
        for(int i=0;i<count && covered[i].left<c->right;++i) {
            result.comparisons++;
            if(covered[i].right<=cursor)continue;
            if(covered[i].left>cursor) {
                int end=covered[i].left<c->right?covered[i].left:c->right;
                memcpy(DRAW_BUF+y*SCREEN_WIDTH+cursor,row+(size_t)(cursor-c->left)*4,(size_t)(end-cursor)*4);
                result.writes+=(unsigned)(end-cursor);result.spans++;
            }
            if(cursor<covered[i].right)cursor=covered[i].right;
            if(cursor>=c->right)break;
        }
        if(cursor<c->right) {
            memcpy(DRAW_BUF+y*SCREEN_WIDTH+cursor,row+(size_t)(cursor-c->left)*4,(size_t)(c->right-cursor)*4);
            result.writes+=(unsigned)(c->right-cursor);result.spans++;
        }
        /* Union this rectangle's row with existing sorted, disjoint coverage. */
        int first=0,left=c->left,right=c->right;
        while(first<count && covered[first].right<left){first++;result.comparisons++;}
        int last=first;
        while(last<count && covered[last].left<=right) {
            if(left>covered[last].left)left=covered[last].left;
            if(right<covered[last].right)right=covered[last].right;
            last++;result.comparisons++;
        }
        memmove(covered+first+1,covered+last,(size_t)(count-last)*sizeof(*covered));
        count=count-(last-first)+1;covered[first]=(struct fb_covered_span){left,right};
        if(count==1 && left==0 && right==SCREEN_WIDTH)break;
    }
    return result;
}
static void fb_batch_flush(fb_opaque_batch *batch)
{
    if(!batch->count)return;
    int left=SCREEN_WIDTH,right=0,top=SCREEN_HEIGHT,bottom=0;
    for(unsigned i=0;i<batch->count;i++) {
        const struct fb_batch_command *c=&batch->commands[i];
        if(left>c->left)left=c->left;
        if(right<c->right)right=c->right;
        if(top>c->top)top=c->top;
        if(bottom<c->bottom)bottom=c->bottom;
    }
    _begin_draw(left,top,right-left,bottom-top);
    uint64_t writes=0,spans=0,checks=0,comparisons=0;
    #ifdef _OPENMP
    #pragma omp parallel for schedule(static) reduction(+:writes,spans,checks,comparisons) if(batch->count>8 && bottom-top>64)
    #endif
    for(int y=top;y<bottom;y++) {
        struct fb_row_stats row=fb_batch_row(batch,y);
        writes+=row.writes;spans+=row.spans;checks+=row.checks;comparisons+=row.comparisons;
    }
    batch->stats.copied_pixels+=writes;batch->stats.copied_spans+=spans;
    batch->stats.row_command_checks+=checks;batch->stats.interval_comparisons+=comparisons;
    batch->stats.flushes++;batch->count=0;
}
fb_opaque_batch *fb_opaque_batch_begin(void){return calloc(1,sizeof(fb_opaque_batch));}
int fb_opaque_batch_add(fb_opaque_batch *batch,int x,int y,const fb_image *image)
{
    if(!batch || !image || !image->content || image->color_type!=FB_COLOR_RGB_8880 ||
       image->pixel_w<=0 || image->pixel_h<=0 || image->line_byte<=0 ||
       (int64_t)image->pixel_w*4>image->line_byte)return 0;
    batch->stats.accepted_commands++;
    int64_t left=x,top=y,right=(int64_t)x+image->pixel_w,bottom=(int64_t)y+image->pixel_h;
    if(left<0)left=0;
    if(top<0)top=0;
    if(right>SCREEN_WIDTH)right=SCREEN_WIDTH;
    if(bottom>SCREEN_HEIGHT)bottom=SCREEN_HEIGHT;
    if(left>=right || top>=bottom)return 1;
    if(batch->count==FB_BATCH_CAPACITY)fb_batch_flush(batch);
    batch->commands[batch->count++]=(struct fb_batch_command){(int)left,(int)right,(int)top,(int)bottom,image->line_byte,
        (const unsigned char *)image->content+(size_t)(top-y)*image->line_byte+(size_t)(left-x)*4};
    batch->stats.submitted_pixels+=(uint64_t)(right-left)*(bottom-top);
    return 1;
}
void fb_opaque_batch_end(fb_opaque_batch *batch,fb_batch_stats *stats)
{
    if(!batch){if(stats)memset(stats,0,sizeof(*stats));return;}
    fb_batch_flush(batch);if(stats)*stats=batch->stats;free(batch);
}
