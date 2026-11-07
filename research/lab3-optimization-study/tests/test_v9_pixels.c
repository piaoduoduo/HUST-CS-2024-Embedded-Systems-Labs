/* Independent division oracle, including four-pixel boundary accesses. */
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#else
#include <sys/mman.h>
#include <unistd.h>
#endif
#include "fixture.h"
static unsigned long long checks;
static uint32_t oracle(uint32_t s,uint32_t d,unsigned a)
{
    if(!a)return d;
    uint32_t out=0xff000000u;
    for(int c=0;c<3;c++)out|=((((s>>(8*c))&255)*a+((d>>(8*c))&255)*(255-a)+127)/255)<<(8*c);
    return out;
}
static unsigned rng=0x1037;
static unsigned next(void){rng=rng*1664525u+1013904223u;return rng;}
static unsigned char *guarded(size_t *length)
{
    #ifdef _WIN32
    SYSTEM_INFO info;GetSystemInfo(&info);*length=info.dwPageSize;
    unsigned char *p=VirtualAlloc(NULL,*length*2,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    DWORD old;require(p && VirtualProtect(p+*length,*length,PAGE_NOACCESS,&old),"guard page setup");return p;
    #else
    *length=(size_t)sysconf(_SC_PAGESIZE);
    unsigned char *p=mmap(NULL,*length*2,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    require(p!=MAP_FAILED && mprotect(p+*length,*length,PROT_NONE)==0,"guard page setup");return p;
    #endif
}
static void release_guard(unsigned char *p,size_t length)
{
    #ifdef _WIN32
    (void)length;VirtualFree(p,0,MEM_RELEASE);
    #else
    munmap(p,length*2);
    #endif
}
int main(void)
{
    #if FB_HAVE_NEON && !defined(FB_DISABLE_FOUR_LANE)
    for(unsigned s=0;s<256;s++)for(unsigned d=0;d<256;d++)for(unsigned a=0;a<256;a+=4) {
        uint32_t source[4],alpha[4],old[4],out[4];
        for(unsigned i=0;i<4;i++) {
            source[i]=s|((255-s)<<8)|(((s*73+19)&255)<<16);
            out[i]=old[i]=d|((255-d)<<8)|(((d*137+7)&255)<<16)|((s^d^i)<<24);alpha[i]=a+i;
        }
        fb_blend4(out,vld1q_u32(source),vld1q_u32(alpha),0);
        for(unsigned i=0;i<4;i++){require(out[i]==oracle(source[i],old[i],a+i),"four lane exhaustive rounding and alpha");checks++;}
    }
    #endif
    size_t size;unsigned char *guard=guarded(&size);
    uint32_t dst[70],expected[70];
    for(int width=0;width<=63;width++)for(int type=2;type<=3;type++)for(unsigned mode=0;mode<4;mode++) {
        int bytes=type==2?4:1;unsigned char *src=guard+size-width*bytes;uint32_t ink=next();
        for(int i=0;i<70;i++)dst[i]=expected[i]=next();
        for(int x=0;x<width;x++) {
            unsigned a=mode==0?0:mode==1?255:mode==2?(unsigned)(x%3==0?0:x%3==1?255:127):next()>>24;
            uint32_t s=type==2?next():ink;
            if(bytes==4){memcpy(src+x*4,&s,4);src[x*4+3]=(unsigned char)a;}else src[x]=(unsigned char)a;
            expected[x+1]=oracle(s,expected[x+1],a);
        }
        fb_fast_row(dst+1,src,width,type,ink);
        require(!memcmp(dst,expected,sizeof(dst)),"exact-length source guard and destination canaries");checks++;
    }
    /* Partial-only prepared RGBA/alpha kernels at every four/eight tail. */
    for(int width=0;width<=63;width++)for(int bytes=1;bytes<=4;bytes+=3) {
        unsigned char *src=guard+size-width*bytes;uint32_t ink=next();
        for(int i=0;i<70;i++)dst[i]=expected[i]=next();
        for(int x=0;x<width;x++) {
            unsigned a=1+(next()%254);uint32_t s=bytes==4?next():ink;
            if(bytes==4){memcpy(src+x*4,&s,4);src[x*4+3]=(unsigned char)a;}else src[x]=(unsigned char)a;
            expected[x+1]=oracle(s,expected[x+1],a);
        }
        fb_prepared_partial(dst+1,src,width,bytes,ink);
        require(!memcmp(dst,expected,sizeof(dst)),"partial prepared row guard and rounding");checks++;
    }
    /* Product loads stop at the final four 16-bit values/inverse bytes. */
    size_t inv_size,product_size;unsigned char *inv_guard=guarded(&inv_size),*product_guard=guarded(&product_size);
    for(int width=0;width<=63;width++) {
        uint16_t *products=(uint16_t *)(void *)(product_guard+product_size-width*3*sizeof(uint16_t));
        unsigned char *inverse=inv_guard+inv_size-width;
        fb_image image={0};image.pixel_w=width;image.pixel_h=1;
        fb_prepared_image p={0};p.image=&image;p.products=products;p.inverse=inverse;
        for(int i=0;i<70;i++)dst[i]=expected[i]=next();
        for(int x=0;x<width;x++) {
            unsigned a=1+next()%254;uint32_t s=next();inverse[x]=(unsigned char)(255-a);
            for(int c=0;c<3;c++)products[x+c*width]=(uint16_t)(((s>>(8*c))&255)*a);
            expected[x+1]=oracle(s,expected[x+1],a);
        }
        fb_prepared_product_row(dst+1,&p,0,width);
        require(!memcmp(dst,expected,sizeof(dst)),"prepared product exact loads and four-lane tails");checks++;
    }
    release_guard(guard,size);release_guard(inv_guard,inv_size);release_guard(product_guard,product_size);
    printf("PASS: %llu v9 four-lane/guard-page oracle checks\n",checks);return 0;
}
