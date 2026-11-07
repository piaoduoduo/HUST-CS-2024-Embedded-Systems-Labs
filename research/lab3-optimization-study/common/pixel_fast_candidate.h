/* Exact, immediate single-pixel API. No batching or delayed dirty work. */
#ifndef FB_PIXEL_FAST_CANDIDATE_H
#define FB_PIXEL_FAST_CANDIDATE_H
#ifndef FB_PIXEL_MODE
#define FB_PIXEL_MODE 2
#endif
#if FB_PIXEL_MODE < 0 || FB_PIXEL_MODE > 3
#error FB_PIXEL_MODE must be 0..3
#endif
void fb_draw_pixel(int x,int y,int color)
{
#if defined(FB_DISABLE_PIXEL_FAST) || FB_PIXEL_MODE == 0
    if(x<0 || y<0 || x>=SCREEN_WIDTH || y>=SCREEN_HEIGHT)return;
    int *buf=_begin_draw(x,y,1,1);
    buf[(size_t)y*SCREEN_WIDTH+x]=color;
#else
    /* Converting negative coordinates to unsigned also rejects them. */
    if((unsigned)x>=SCREEN_WIDTH || (unsigned)y>=SCREEN_HEIGHT)return;
#if FB_PIXEL_MODE == 1
    int *buf=_begin_draw(x,y,1,1);
    buf[(size_t)y*SCREEN_WIDTH+x]=color;
#elif FB_PIXEL_MODE == 2
    /* The private dirty box is inside the screen, or the standard reversed
     * empty box (W,0,H,0). Unsigned subtraction is defined in every case.
     * Already-covered axes need no min/max writes. An empty axis always
     * fails this containment test for every on-screen coordinate. */
    unsigned left=(unsigned)update_area.x1,top=(unsigned)update_area.y1;
    if((unsigned)x-left >= (unsigned)update_area.x2-left) {
        if(x<update_area.x1)update_area.x1=x;
        if(x>=update_area.x2)update_area.x2=x+1;
    }
    if((unsigned)y-top >= (unsigned)update_area.y2-top) {
        if(y<update_area.y1)update_area.y1=y;
        if(y>=update_area.y2)update_area.y2=y+1;
    }
    DRAW_BUF[(size_t)y*SCREEN_WIDTH+x]=color;
#else
    /* A competitor for targets where conditional min/max instructions beat
     * predictable branches. Compiler output determines whether branchless. */
    update_area.x1=x<update_area.x1?x:update_area.x1;
    update_area.x2=x+1>update_area.x2?x+1:update_area.x2;
    update_area.y1=y<update_area.y1?y:update_area.y1;
    update_area.y2=y+1>update_area.y2?y+1:update_area.y2;
    DRAW_BUF[(size_t)y*SCREEN_WIDTH+x]=color;
#endif
#endif
}
#endif
