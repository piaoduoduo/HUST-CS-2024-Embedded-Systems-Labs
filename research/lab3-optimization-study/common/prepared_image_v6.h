#include "prepared_api_v6.h"
struct fb_prepared_span {int left,right,opaque;};
struct fb_prepared_image {fb_image *image;unsigned *rows;struct fb_prepared_span *spans;unsigned count;};
void fb_free_prepared(fb_prepared_image *p)
{
    if(!p)return;
    fb_free_image(p->image);free(p->rows);free(p->spans);free(p);
}
fb_prepared_image *fb_prepare_image(const fb_image *source)
{
    #ifdef FB_DISABLE_PREPARED
    (void)source;return NULL;
    #else
    if(!source || !source->content || source->pixel_w<=0 || source->pixel_h<=0 ||
       (source->color_type!=FB_COLOR_RGBA_8888 && source->color_type!=FB_COLOR_ALPHA_8))return NULL;
    int bytes=source->color_type==FB_COLOR_ALPHA_8?1:4;
    if(source->line_byte<=0 || (int64_t)source->pixel_w*bytes>source->line_byte)return NULL;
    uint64_t pixels=(uint64_t)source->pixel_w*source->pixel_h;
    if(pixels>512U*1024U)return NULL;
    uint64_t required=pixels*(bytes+sizeof(struct fb_prepared_span))+
        ((uint64_t)source->pixel_h+1)*sizeof(unsigned)+sizeof(fb_prepared_image);
    if(required>16U*1024U*1024U)return NULL;
    fb_prepared_image *p=calloc(1,sizeof(*p));if(!p)return NULL;
    p->image=fb_new_image(source->color_type,source->pixel_w,source->pixel_h,0);
    p->rows=calloc((size_t)source->pixel_h+1,sizeof(*p->rows));
    p->spans=malloc((size_t)pixels*sizeof(*p->spans));
    if(!p->image || !p->rows || !p->spans){fb_free_prepared(p);return NULL;}
    for(int row=0;row<source->pixel_h;row++) {
        unsigned char *dst=(unsigned char *)p->image->content+(size_t)row*p->image->line_byte;
        memcpy(dst,(const unsigned char *)source->content+(size_t)row*source->line_byte,(size_t)source->pixel_w*bytes);
        p->rows[row]=p->count;
        int x=0;
        while(x<source->pixel_w) {
            unsigned a=dst[x*bytes+bytes-1];
            if(!a){x++;continue;}
            int left=x,opaque=a==255;x++;
            while(x<source->pixel_w) {
                a=dst[x*bytes+bytes-1];if(!a || (a==255)!=opaque)break;x++;
            }
            p->spans[p->count++]=(struct fb_prepared_span){left,x,opaque};
        }
    }
    p->rows[source->pixel_h]=p->count;return p;
    #endif
}
/* A prepared partial span guarantees 1<=alpha<=254, so endpoint tests vanish. */
static void fb_prepared_partial(uint32_t *dst,const unsigned char *src,int w,int bytes,uint32_t ink)
{
    int col=0;
    #if FB_HAVE_NEON
    uint8x8x4_t s;
    if(bytes==1){s.val[0]=vdup_n_u8(ink&255);s.val[1]=vdup_n_u8((ink>>8)&255);s.val[2]=vdup_n_u8((ink>>16)&255);}
    for(;col+8<=w;col+=8) {
        uint8x8_t a;
        if(bytes==4){s=vld4_u8(src+col*4);a=s.val[3];}else a=vld1_u8(src+col);
        uint8x8x4_t d=vld4_u8((unsigned char *)(dst+col));
        for(int c=0;c<3;c++)d.val[c]=fb_mix8(s.val[c],d.val[c],a);
        d.val[3]=vdup_n_u8(255);vst4_u8((unsigned char *)(dst+col),d);
    }
    #endif
    for(;col<w;col++) {
        unsigned a=src[col*bytes+bytes-1];uint32_t old=dst[col];
        unsigned b=bytes==4?src[col*4]:ink&255;
        unsigned g=bytes==4?src[col*4+1]:(ink>>8)&255;
        unsigned r=bytes==4?src[col*4+2]:(ink>>16)&255;
        dst[col]=0xff000000u|fb_mix(b,old&255,a)|(fb_mix(g,(old>>8)&255,a)<<8)|(fb_mix(r,(old>>16)&255,a)<<16);
    }
}
static void fb_prepared_solid(uint32_t *dst,int w,uint32_t ink)
{
    int col=0;ink|=0xff000000u;
    #if FB_HAVE_NEON
    uint32x4_t v=vdupq_n_u32(ink);
    for(;col+4<=w;col+=4)vst1q_u32(dst+col,v);
    #endif
    for(;col<w;col++)dst[col]=ink;
}
static void fb_prepared_row_draw(int x,int y,const fb_prepared_image *p,int row,int64_t left,int64_t right,int color)
{
    const fb_image *image=p->image;
    int bytes=image->color_type==FB_COLOR_ALPHA_8?1:4;
    const unsigned char *src=(const unsigned char *)image->content+(size_t)row*image->line_byte;
    for(unsigned i=p->rows[row];i<p->rows[row+1];i++) {
        int l=p->spans[i].left,r=p->spans[i].right;
        if(l<left-x)l=(int)(left-x);
        if(r>right-x)r=(int)(right-x);
        if(l>=r)continue;
        uint32_t *dst=(uint32_t *)(DRAW_BUF+(int)((int64_t)y+row)*SCREEN_WIDTH+(int)((int64_t)x+l));
        if(bytes==4 && p->spans[i].opaque)memcpy(dst,src+(size_t)l*4,(size_t)(r-l)*4);
        else if(bytes==1 && p->spans[i].opaque)fb_prepared_solid(dst,r-l,(uint32_t)color);
        else fb_prepared_partial(dst,src+(size_t)l*bytes,r-l,bytes,(uint32_t)color);
    }
}
void fb_draw_prepared(int x,int y,const fb_prepared_image *p,int color)
{
    if(!p)return;
    const fb_image *image=p->image;
    int64_t left=x,top=y,right=(int64_t)x+image->pixel_w,bottom=(int64_t)y+image->pixel_h;
    if(left<0)left=0;
    if(top<0)top=0;
    if(right>SCREEN_WIDTH)right=SCREEN_WIDTH;
    if(bottom>SCREEN_HEIGHT)bottom=SCREEN_HEIGHT;
    if(left>=right || top>=bottom)return;
    _begin_draw((int)left,(int)top,(int)(right-left),(int)(bottom-top));
    int first_row=(int)(top-y),last_row=(int)(bottom-y);
    #ifdef _OPENMP
    if((right-left)*(bottom-top)>=FB_PARALLEL_MIN_PIXELS) {
        #pragma omp parallel for schedule(static)
        for(int row=first_row;row<last_row;row++)fb_prepared_row_draw(x,y,p,row,left,right,color);
        return;
    }
    #endif
    for(int row=first_row;row<last_row;row++)fb_prepared_row_draw(x,y,p,row,left,right,color);
}

#ifndef FB_DISABLE_MANY
struct fb_prepared_clip {int x,y,left,right,top,bottom,color;};
static void fb_prepared_many_row(const fb_prepared_image *p,const struct fb_prepared_clip *commands,unsigned count,int y)
{
    for(unsigned i=0;i<count;i++) {
        const struct fb_prepared_clip *c=&commands[i];
        if(y>=c->top && y<c->bottom)
            fb_prepared_row_draw(c->x,c->y,p,y-c->y,c->left,c->right,c->color);
    }
}
#endif
void fb_draw_prepared_many(const fb_prepared_image *p,const fb_prepared_draw *draws,unsigned count)
{
    if(!p || !draws || !count)return;
    #ifdef FB_DISABLE_MANY
    for(unsigned i=0;i<count;i++)fb_draw_prepared(draws[i].x,draws[i].y,p,draws[i].color);
    #else
    /* Bound temporary storage; allocation failures preserve immediate semantics. */
    struct fb_prepared_clip *commands=count<=4096?malloc((size_t)count*sizeof(*commands)):NULL;
    if(!commands) {
        for(unsigned i=0;i<count;i++)fb_draw_prepared(draws[i].x,draws[i].y,p,draws[i].color);
        return;
    }
    unsigned used=0;int top=SCREEN_HEIGHT,bottom=0;
    uint64_t pixels=0;
    for(unsigned i=0;i<count;i++) {
        int64_t l=draws[i].x,t=draws[i].y;
        int64_t r=l+p->image->pixel_w,b=t+p->image->pixel_h;
        if(l<0)l=0;
        if(t<0)t=0;
        if(r>SCREEN_WIDTH)r=SCREEN_WIDTH;
        if(b>SCREEN_HEIGHT)b=SCREEN_HEIGHT;
        if(l>=r || t>=b)continue;
        commands[used++]=(struct fb_prepared_clip){draws[i].x,draws[i].y,(int)l,(int)r,(int)t,(int)b,draws[i].color};
        _begin_draw((int)l,(int)t,(int)(r-l),(int)(b-t));
        if(top>t)top=(int)t;
        if(bottom<b)bottom=(int)b;
        pixels+=(uint64_t)(r-l)*(b-t);
    }
    #ifdef _OPENMP
    if(pixels>=FB_PARALLEL_MIN_PIXELS && bottom-top>1) {
        #pragma omp parallel for schedule(static)
        for(int y=top;y<bottom;y++)fb_prepared_many_row(p,commands,used,y);
    }else
    #else
    (void)pixels;
    #endif
    for(int y=top;y<bottom;y++)fb_prepared_many_row(p,commands,used,y);
    free(commands);
    #endif
}
