#ifndef FB_GEOMETRY_BATCH_V9_H
#define FB_GEOMETRY_BATCH_V9_H
#include "geometry_batch_api_v9.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#ifdef FB_DISABLE_STATS
#define FB_GEOMETRY_COUNT(expression) ((void)0)
#else
#define FB_GEOMETRY_COUNT(expression) do {expression;} while(0)
#endif
#ifndef FB_GEOMETRY_BATCH_CAPACITY
#define FB_GEOMETRY_BATCH_CAPACITY 16384u
#endif
#ifndef FB_GEOMETRY_SPAN_LIMIT
#define FB_GEOMETRY_SPAN_LIMIT 1048576u
#endif
#ifndef FB_GEOMETRY_MALLOC
#define FB_GEOMETRY_MALLOC malloc
#define FB_GEOMETRY_CALLOC calloc
#define FB_GEOMETRY_REALLOC realloc
#define FB_GEOMETRY_FREE free
#endif
struct fb_geometry_span {int y,left,right;uint32_t color;};
struct fb_geometry_batch {
    struct fb_geometry_span *spans;
    unsigned count,capacity,commands,row_counts[SCREEN_HEIGHT],row_last[SCREEN_HEIGHT];
    uint64_t submitted_pixels,written_pixels,flushes,fallbacks,generated_spans,retained_spans;
};
static inline void fb_geometry_fill(int y,int left,int right,uint32_t color)
{
    uint32_t *p=(uint32_t *)DRAW_BUF+(size_t)y*SCREEN_WIDTH+left;
    int n=right-left,i=0;
#if FB_HAVE_NEON
    uint32x4_t v=vdupq_n_u32(color);
    for(;i+16<=n;i+=16){vst1q_u32(p+i,v);vst1q_u32(p+i+4,v);vst1q_u32(p+i+8,v);vst1q_u32(p+i+12,v);}
    for(;i+4<=n;i+=4)vst1q_u32(p+i,v);
#endif
    for(;i<n;++i)p[i]=color;
}
#ifdef FB_GEOMETRY_DSU
static unsigned fb_geometry_find(unsigned *parent,unsigned x)
{
    unsigned root=x;
    while(parent[root]!=root)root=parent[root];
    while(parent[x]!=x){unsigned next=parent[x];parent[x]=root;x=next;}
    return root;
}
static unsigned fb_geometry_join(unsigned *parent,unsigned *size,unsigned *end,unsigned x,unsigned y)
{
    unsigned a=fb_geometry_find(parent,x),b=fb_geometry_find(parent,y);
    if(a!=b){if(size[a]<size[b]){unsigned t=a;a=b;b=t;}parent[b]=a;size[a]+=size[b];if(end[a]<end[b])end[a]=end[b];}
    return end[a];
}
#endif
static uint64_t fb_geometry_render_row(const fb_geometry_batch *batch,const unsigned *index,unsigned first,unsigned last,int y)
{
    uint64_t written=0;
#ifdef FB_GEOMETRY_DSU
    unsigned parent[SCREEN_WIDTH+1],size[SCREEN_WIDTH+1],end[SCREEN_WIDTH+1];
    for(unsigned i=0;i<=SCREEN_WIDTH;++i){parent[i]=end[i]=i;size[i]=1;}
    for(unsigned j=last;j>first;--j){
        const struct fb_geometry_span *s=&batch->spans[index[j-1]];
        unsigned x=end[fb_geometry_find(parent,(unsigned)s->left)];
        while(x<(unsigned)s->right){
            DRAW_BUF[(size_t)y*SCREEN_WIDTH+x]=(int)s->color;FB_GEOMETRY_COUNT(++written);
            x=fb_geometry_join(parent,size,end,x,x+1);
        }
        if(end[fb_geometry_find(parent,0)]==SCREEN_WIDTH)break;
    }
#else
    uint64_t covered[(SCREEN_WIDTH+63)/64]={0};
    unsigned remaining=SCREEN_WIDTH;
    for(unsigned j=last;j>first;--j){
        const struct fb_geometry_span *s=&batch->spans[index[j-1]];
        unsigned lo=(unsigned)s->left>>6,hi=((unsigned)s->right-1)>>6;
        int run_left=-1,run_right=0;
        for(unsigned word=lo;word<=hi;++word){
            unsigned left=word==lo?((unsigned)s->left&63u):0u;
            unsigned right=word==hi?(((unsigned)s->right-1)&63u)+1u:64u;
            uint64_t mask=(UINT64_MAX<<left)&(right==64u?UINT64_MAX:((UINT64_C(1)<<right)-1));
            uint64_t todo=mask&~covered[word];covered[word]|=mask;
            while(todo){
                unsigned start=(unsigned)__builtin_ctzll(todo);
                uint64_t suffix=todo>>start;
                unsigned length=~suffix?(unsigned)__builtin_ctzll(~suffix):64u;
                int l=(int)(word*64u+start),r=l+(int)length;
                if(l==run_right && run_left>=0)run_right=r;
                else {if(run_left>=0)fb_geometry_fill(y,run_left,run_right,s->color);run_left=l;run_right=r;}
                FB_GEOMETRY_COUNT(written+=length);remaining-=length;
                if(length==64u)todo=0;else todo&=~(((UINT64_C(1)<<length)-1)<<start);
            }
        }
        if(run_left>=0)fb_geometry_fill(y,run_left,run_right,s->color);
        if(!remaining)break;
    }
#endif
    return written;
}
static void fb_geometry_flush(fb_geometry_batch *batch)
{
    if(!batch || !batch->count)return;
    unsigned offset[SCREEN_HEIGHT+1],cursor[SCREEN_HEIGHT];
    int left=SCREEN_WIDTH,right=0,top=SCREEN_HEIGHT,bottom=0;
    offset[0]=0;
    for(int y=0;y<SCREEN_HEIGHT;++y){offset[y+1]=offset[y]+batch->row_counts[y];cursor[y]=offset[y];}
    for(unsigned i=0;i<batch->count;++i){const struct fb_geometry_span *s=&batch->spans[i];
        if(left>s->left)left=s->left;
        if(right<s->right)right=s->right;
        if(top>s->y)top=s->y;
        if(bottom<s->y+1)bottom=s->y+1;}
    _begin_draw(left,top,right-left,bottom-top);
#ifdef FB_GEOMETRY_FAIL_INDEX
    unsigned *index=NULL;
#else
    unsigned *index=(unsigned *)FB_GEOMETRY_MALLOC((size_t)batch->count*sizeof(*index));
#endif
    uint64_t written=0;
    if(!index){
        FB_GEOMETRY_COUNT(++batch->fallbacks);
        for(unsigned i=0;i<batch->count;++i){const struct fb_geometry_span *s=&batch->spans[i];fb_geometry_fill(s->y,s->left,s->right,s->color);FB_GEOMETRY_COUNT(written+=(unsigned)(s->right-s->left));}
    }else{
        for(unsigned i=0;i<batch->count;++i)index[cursor[batch->spans[i].y]++]=i;
#ifdef _OPENMP
#ifdef FB_DISABLE_STATS
#pragma omp parallel for schedule(static) if(batch->count>64 && bottom-top>32)
#else
#pragma omp parallel for schedule(static) reduction(+:written) if(batch->count>64 && bottom-top>32)
#endif
#endif
        for(int y=top;y<bottom;++y){
            uint64_t row_written=fb_geometry_render_row(batch,index,offset[y],offset[y+1],y);
            FB_GEOMETRY_COUNT(written+=row_written);(void)row_written;
        }
        FB_GEOMETRY_FREE(index);
    }
    FB_GEOMETRY_COUNT(batch->written_pixels+=written;++batch->flushes);(void)written;batch->count=0;batch->commands=0;
    memset(batch->row_counts,0,sizeof(batch->row_counts));
}
static void fb_geometry_emit(fb_geometry_batch *batch,int y,int left,int right,uint32_t color)
{
    if(left>=right)return;
    FB_GEOMETRY_COUNT(++batch->generated_spans;batch->submitted_pixels+=(unsigned)(right-left));
#ifndef FB_DISABLE_GEOMETRY_COALESCE
    /* Only the immediately preceding command on THIS row may be merged.
     * Same color plus intersecting/adjacent spans has exactly the same union;
     * any intervening different color or separated span prevents merging. */
    if(batch->row_counts[y]){
        struct fb_geometry_span *last=&batch->spans[batch->row_last[y]];
        if(last->color==color && last->left<=right && left<=last->right){
            if(last->left>left)last->left=left;
            if(last->right<right)last->right=right;
            return;
        }
    }
#endif
    if(batch->count>=FB_GEOMETRY_SPAN_LIMIT)fb_geometry_flush(batch);
    if(batch->count==batch->capacity){
        unsigned cap=batch->capacity?batch->capacity*2u:1024u;
        if(cap>FB_GEOMETRY_SPAN_LIMIT)cap=FB_GEOMETRY_SPAN_LIMIT;
        struct fb_geometry_span *p=cap?(struct fb_geometry_span *)FB_GEOMETRY_REALLOC(batch->spans,(size_t)cap*sizeof(*p)):NULL;
        if(!p){
            fb_geometry_flush(batch);_begin_draw(left,y,right-left,1);fb_geometry_fill(y,left,right,color);
            FB_GEOMETRY_COUNT(++batch->fallbacks;batch->written_pixels+=(unsigned)(right-left));return;
        }
        batch->spans=p;batch->capacity=cap;
    }
    batch->row_last[y]=batch->count;
    batch->spans[batch->count++]=(struct fb_geometry_span){y,left,right,color};++batch->row_counts[y];FB_GEOMETRY_COUNT(++batch->retained_spans);
}
/* int32 endpoint products are formed wide.  The nonnegative numerators below
 * are at most (2^32-1)^2+(2^31-1), so the actual quotient uses native uint64.
 * Signed ceil handles the negative half-phase at the first row exactly. */
static inline int64_t fb_geometry_ceil(__int128 n,uint64_t d)
{
    if(n<0)return -(int64_t)((uint64_t)(-n)/d);
    uint64_t u=(uint64_t)n;
    return (int64_t)(u/d+(u%d!=0));
}
static inline int64_t fb_geometry_minor(int64_t n,int sign,uint64_t delta,uint64_t q,uint64_t length)
{
    if(!length)return n;
    __int128 product=(__int128)delta*q+length/2;
    return n+sign*(int64_t)((uint64_t)product/length);
}
fb_geometry_batch *fb_geometry_batch_begin(void)
{
#ifdef FB_DISABLE_GEOMETRY_BATCH
    return NULL;
#else
    return (fb_geometry_batch *)FB_GEOMETRY_CALLOC(1,sizeof(fb_geometry_batch));
#endif
}
int fb_geometry_batch_rect(fb_geometry_batch *batch,int x,int y,int w,int h,int color)
{
    if(!batch){fb_draw_rect(x,y,w,h,color);return 1;}
    if(batch->commands>=FB_GEOMETRY_BATCH_CAPACITY)fb_geometry_flush(batch);
    ++batch->commands;if(w<=0 || h<=0)return 1;
    int64_t l=x,r=(int64_t)x+w,t=y,b=(int64_t)y+h;
    if(l<0)l=0;
    if(r>SCREEN_WIDTH)r=SCREEN_WIDTH;
    if(t<0)t=0;
    if(b>SCREEN_HEIGHT)b=SCREEN_HEIGHT;
    if(l>=r || t>=b)return 1;
    for(int row=(int)t;row<(int)b;++row)fb_geometry_emit(batch,row,(int)l,(int)r,(uint32_t)color);
    return 1;
}
int fb_geometry_batch_line(fb_geometry_batch *batch,int x1,int y1,int x2,int y2,int color)
{
    if(!batch){fb_draw_line(x1,y1,x2,y2,color);return 1;}
    if(batch->commands>=FB_GEOMETRY_BATCH_CAPACITY)fb_geometry_flush(batch);
    ++batch->commands;
    int64_t dx=(int64_t)x2-x1,dy=(int64_t)y2-y1;
    int steep=llabs(dy)>llabs(dx),sign;
    int64_t m1=steep?y1:x1,m2=steep?y2:x2,n1=steep?x1:y1,n2=steep?x2:y2;
    if(m1>m2){int64_t t=m1;m1=m2;m2=t;t=n1;n1=n2;n2=t;}
    uint64_t length=(uint64_t)(m2-m1),delta=(uint64_t)llabs(n2-n1);
    sign=n2<n1?-1:1;
#ifdef FB_DISABLE_ANALYTIC_LINES
    int64_t first=m1<0?0:m1,last=m2,limit=steep?SCREEN_HEIGHT:SCREEN_WIDTH;
    if(last>=limit)last=limit-1;
    if(first>last)return 1;
    uint64_t q=(uint64_t)(first-m1),numerator=delta*q+length/2;
    int64_t minor=length?n1+sign*(int64_t)(numerator/length):n1;
    uint64_t error=length?numerator%length:0;
    int run_y=-1,run_l=0,run_r=0;
    for(int64_t major=first;major<=last;++major){
        int64_t x=steep?minor:major,y=steep?major:minor;
        if(x>=0 && x<SCREEN_WIDTH && y>=0 && y<SCREEN_HEIGHT){
            if((int)y==run_y && (int)x==run_r)++run_r;
            else{if(run_y>=0)fb_geometry_emit(batch,run_y,run_l,run_r,(uint32_t)color);run_y=(int)y;run_l=(int)x;run_r=(int)x+1;}
        }
        error+=delta;if(length && error>=length){error-=length;minor+=sign;}
    }
    if(run_y>=0)fb_geometry_emit(batch,run_y,run_l,run_r,(uint32_t)color);
#else
    int64_t qmin=m1<0?-m1:0,qmax=(int64_t)length;
    int64_t major_limit=steep?SCREEN_HEIGHT:SCREEN_WIDTH;
    if(qmax>major_limit-1-m1)qmax=major_limit-1-m1;
    if(qmin>qmax)return 1;
    if(steep){
        if(!delta){if(n1<0 || n1>=SCREEN_WIDTH)return 1;}
        else{
            int64_t kmin=sign>0?-n1:n1-(SCREEN_WIDTH-1),kmax=sign>0?SCREEN_WIDTH-1-n1:n1;
            if(kmin<0)kmin=0;
            if(kmax>(int64_t)delta)kmax=(int64_t)delta;
            if(kmin>kmax)return 1;
            if(kmin>0){int64_t q=fb_geometry_ceil((__int128)kmin*length-length/2,delta);if(qmin<q)qmin=q;}
            if(kmax<(int64_t)delta){int64_t q=fb_geometry_ceil((__int128)(kmax+1)*length-length/2,delta)-1;if(qmax>q)qmax=q;}
        }
        if(qmin>qmax)return 1;
        /* One initial quotient then the original exact Bresenham remainder
         * recurrence.  No divide is executed for subsequent target rows. */
        uint64_t numerator=(uint64_t)((__int128)delta*qmin+length/2);
        int64_t minor=n1+sign*(int64_t)(numerator/length);
        uint64_t remainder=numerator%length;
        for(int64_t q=qmin;q<=qmax;++q){
            fb_geometry_emit(batch,(int)(m1+q),(int)minor,(int)minor+1,(uint32_t)color);
            remainder+=delta;if(remainder>=length){remainder-=length;minor+=sign;}
        }
    }else if(!delta){
        if(n1>=0 && n1<SCREEN_HEIGHT)fb_geometry_emit(batch,(int)n1,(int)(m1+qmin),(int)(m1+qmax+1),(uint32_t)color);
    }else{
        int64_t a=fb_geometry_minor(n1,sign,delta,(uint64_t)qmin,length),b=fb_geometry_minor(n1,sign,delta,(uint64_t)qmax,length);
        int64_t first=a<b?a:b,last=a>b?a:b;if(first<0)first=0;if(last>=SCREEN_HEIGHT)last=SCREEN_HEIGHT-1;
        if(first>last)return 1;
        /* Traverse k in increasing order even for descending lines.  Given
         * c=ceil(n/d), deficit=c*d-n in [0,d), adding L changes c by floor(L/d)
         * plus one carry iff (L%d)>deficit.  This exactly reproduces both ceil
         * bounds with O(1) setup divides rather than two divides per span. */
        int64_t y=sign>0?first:last,k=(y-n1)*sign;
        __int128 numerator=(__int128)k*length-length/2;
        int64_t boundary=fb_geometry_ceil(numerator,delta);
        uint64_t deficit=(uint64_t)((__int128)boundary*delta-numerator);
        uint64_t step=length/delta,carry_step=length%delta;
        for(int64_t row=first;row<=last;++row,y+=sign){
            int carry=carry_step>deficit;
            int64_t next=boundary+(int64_t)step+carry;
            int64_t lo=boundary,hi=next-1;
            deficit=carry?deficit+delta-carry_step:deficit-carry_step;boundary=next;
            if(lo<qmin)lo=qmin;
            if(hi>qmax)hi=qmax;
            if(lo<=hi)fb_geometry_emit(batch,(int)y,(int)(m1+lo),(int)(m1+hi+1),(uint32_t)color);
        }
    }
#endif
    return 1;
}
void fb_geometry_batch_end(fb_geometry_batch *batch)
{
    if(!batch)return;
    fb_geometry_flush(batch);FB_GEOMETRY_FREE(batch->spans);FB_GEOMETRY_FREE(batch);
}
#endif
