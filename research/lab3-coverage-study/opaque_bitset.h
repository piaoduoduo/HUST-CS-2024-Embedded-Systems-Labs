/* Private experimental row renderer. Valid clipped opaque commands only.
 * Reverse order keeps the final writer, copying each exposed pixel once.
 * Per row: O(B*ceil(W/64) + R + U), R copy runs, U copied pixels.
 * Scratch: O(ceil(W/64)); no sorted interval insertion or memmove. */
#define FB_OPAQUE_WORDS ((SCREEN_WIDTH+63)/64)
static uint64_t fb_opaque_mask(int l,int r)
{
    return (UINT64_MAX<<l)&(r==64?UINT64_MAX:((UINT64_C(1)<<r)-1));
}
static void fb_opaque_copy_run(const struct fb_batch_command *c,int y,int l,int r,struct fb_row_stats *stats)
{
    const unsigned char *source=c->source+(size_t)(y-c->top)*c->stride;
    memcpy(DRAW_BUF+(size_t)y*SCREEN_WIDTH+l,source+(size_t)(l-c->left)*4,(size_t)(r-l)*4);
    FB_COUNT(stats->writes+=(unsigned)(r-l));FB_COUNT(stats->spans++);
    (void)stats;
}
static struct fb_row_stats fb_batch_row_bitset(const fb_opaque_batch *batch,int y)
{
    uint64_t covered[FB_OPAQUE_WORDS]={0};
    if(SCREEN_WIDTH%64)covered[FB_OPAQUE_WORDS-1]=UINT64_MAX<<(SCREEN_WIDTH%64);
    unsigned full=0;struct fb_row_stats result={0};
    for(unsigned command=batch->count;command>0;--command) {
        const struct fb_batch_command *c=&batch->commands[command-1];
        FB_COUNT(result.checks++);
        if(y<c->top || y>=c->bottom)continue;
        int run_l=-1,run_r=0;
        for(int word=c->left/64;word<=(c->right-1)/64;word++) {
            int base=word*64,l=c->left>base?c->left-base:0,r=c->right-base;
            if(r>64)r=64;
            uint64_t mask=fb_opaque_mask(l,r),old=covered[word],todo=mask&~old;
            covered[word]=old|mask;
            if(old!=UINT64_MAX && covered[word]==UINT64_MAX)full++;
            /* Existing comparison counter now records coverage-word visits. */
            FB_COUNT(result.comparisons++);
            while(todo) {
                int a=__builtin_ctzll(todo);uint64_t shifted=todo>>a;
                int length=~shifted?__builtin_ctzll(~shifted):64-a;
                int end=a+length;
                if(run_l>=0 && run_r==base+a)run_r=base+end;
                else {
                    if(run_l>=0)fb_opaque_copy_run(c,y,run_l,run_r,&result);
                    run_l=base+a;run_r=base+end;
                }
                todo&=~fb_opaque_mask(a,end);
            }
        }
        if(run_l>=0)fb_opaque_copy_run(c,y,run_l,run_r,&result);
        if(full==FB_OPAQUE_WORDS)break;
    }
    return result;
}
