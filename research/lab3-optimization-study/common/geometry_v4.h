/* Valid on-screen coordinates only; callers keep the original clipped fallback. */
static void fb_fill_rect_inside(int x,int y,int w,int h,int color)
{
    _begin_draw(x,y,w,h);
    #if FB_HAVE_NEON
    uint32x4_t value=vdupq_n_u32((uint32_t)color);
    #endif
    for(int row=0;row<h;row++) {
        uint32_t *dst=(uint32_t *)(DRAW_BUF+(y+row)*SCREEN_WIDTH+x);
        int col=0;
        #if FB_HAVE_NEON
        for(;col+16<=w;col+=16) {
            vst1q_u32(dst+col,value);vst1q_u32(dst+col+4,value);
            vst1q_u32(dst+col+8,value);vst1q_u32(dst+col+12,value);
        }
        for(;col+4<=w;col+=4)vst1q_u32(dst+col,value);
        #endif
        for(;col<w;col++)dst[col]=(uint32_t)color;
    }
}
static void fb_line_inside(int x1,int y1,int x2,int y2,int color)
{
    int dx=x2-x1,dy=y2-y1,steep=abs(dy)>abs(dx);
    int major1=steep?y1:x1,major2=steep?y2:x2;
    int minor1=steep?x1:y1,minor2=steep?x2:y2;
    if(major1>major2) {
        int temp=major1;major1=major2;major2=temp;
        temp=minor1;minor1=minor2;minor2=temp;
    }
    int left=x1<x2?x1:x2,top=y1<y2?y1:y2;
    _begin_draw(left,top,abs(dx)+1,abs(dy)+1);
    int length=major2-major1,distance=abs(minor2-minor1);
    int *pixel=DRAW_BUF+(steep?major1:minor1)*SCREEN_WIDTH+(steep?minor1:major1);
    if(!length){*pixel=color;return;}
    int error=length/2,major_step=steep?SCREEN_WIDTH:1;
    int minor_step=(minor2<minor1?-1:1)*(steep?1:SCREEN_WIDTH);
    for(int i=0;i<length;i++) {
        *pixel=color;error+=distance;pixel+=major_step;
        if(error>=length){error-=length;pixel+=minor_step;}
    }
    *pixel=color;
}
