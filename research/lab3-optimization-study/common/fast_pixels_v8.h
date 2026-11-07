/* Exact BGRA row kernels. ARM SIMD is optional; scalar output is the oracle. */
#ifndef FB_FAST_PIXELS_H
#define FB_FAST_PIXELS_H
#include <stdint.h>
#include <string.h>
#if (defined(FB_TEST_NEON) || defined(__aarch64__)) && !defined(FB_DISABLE_NEON)
#include <arm_neon.h>
#define FB_HAVE_NEON 1
#else
#define FB_HAVE_NEON 0
#endif
static inline unsigned fb_mix(unsigned s, unsigned d, unsigned a)
{
    unsigned t=s*a+d*(255-a)+128;
    return (t+(t>>8))>>8;
}
static inline uint32_t fb_mix_partial_pixel(uint32_t old, const unsigned char *src, unsigned a, uint32_t ink)
{
#ifndef FB_DISABLE_PACKED
    uint32_t source=ink;
    if(src)source=(uint32_t)src[0]|((uint32_t)src[1]<<8)|((uint32_t)src[2]<<16);
    /* Two independent 16-bit lanes. Bias MUST precede high-byte correction. */
    uint32_t rb=(source&0x00ff00ffu)*a+(old&0x00ff00ffu)*(255-a)+0x00800080u;
    rb=((rb+((rb>>8)&0x00ff00ffu))>>8)&0x00ff00ffu;
    unsigned g=fb_mix((source>>8)&255,(old>>8)&255,a);
    return 0xff000000u|rb|(g<<8);
#else
    unsigned b=src?src[0]:ink&255;
    unsigned g=src?src[1]:(ink>>8)&255;
    unsigned r=src?src[2]:(ink>>16)&255;
    b=fb_mix(b,old&255,a);g=fb_mix(g,(old>>8)&255,a);r=fb_mix(r,(old>>16)&255,a);
    return UINT32_C(0xff000000)|(r<<16)|(g<<8)|b;
#endif
}
static inline uint32_t fb_mix_pixel(uint32_t old,const unsigned char *src,unsigned a,uint32_t ink)
{
    if(!a)return old;
    if(a==255) {
        uint32_t color=src?(uint32_t)src[0]|((uint32_t)src[1]<<8)|((uint32_t)src[2]<<16):ink;
        return 0xff000000u|(color&0x00ffffffu);
    }
    return fb_mix_partial_pixel(old,src,a,ink);
}

#if FB_HAVE_NEON
static inline uint8x8_t fb_mix8(uint8x8_t s, uint8x8_t d, uint8x8_t a)
{
    uint16x8_t t=vmull_u8(s,a);
    t=vmlal_u8(t,d,vsub_u8(vdup_n_u8(255),a));
    t=vaddq_u16(t,vdupq_n_u16(128));
    t=vaddq_u16(t,vshrq_n_u16(t,8));
    return vshrn_n_u16(t,8);
}
static inline void fb_blend8(unsigned char *dst, uint8x8x4_t s, uint8x8_t a)
{
    uint8x8x4_t d=vld4_u8(dst),out;
    uint8x8_t zero=vceq_u8(a,vdup_n_u8(0));
    for(int k=0;k<3;++k) out.val[k]=vbsl_u8(zero,d.val[k],fb_mix8(s.val[k],d.val[k],a));
    out.val[3]=vbsl_u8(zero,d.val[3],vdup_n_u8(255));
    vst4_u8(dst,out);
}
#endif
static inline void fb_rgba_row(uint32_t *dst,const unsigned char *src,int w)
{
    int x=0;
#if FB_HAVE_NEON
    for(;x+8<=w;x+=8) {
        uint8x8x4_t s=vld4_u8(src+x*4);
        uint64_t bits=vget_lane_u64(vreinterpret_u64_u8(s.val[3]),0);
        if(!bits) continue;
        if(bits==UINT64_MAX) {memcpy(dst+x,src+x*4,32);continue;}
        fb_blend8((unsigned char *)(dst+x),s,s.val[3]);
    }
#endif
    for(;x<w;++x) {
        unsigned a=src[x*4+3];
        if(a) dst[x]=fb_mix_pixel(dst[x],src+x*4,a,0);
    }
}
static inline void fb_alpha_row(uint32_t *dst,const unsigned char *src,int w,uint32_t ink)
{
    int x=0;
#if FB_HAVE_NEON
    uint8x8x4_t s;
    s.val[0]=vdup_n_u8(ink&255);s.val[1]=vdup_n_u8((ink>>8)&255);
    s.val[2]=vdup_n_u8((ink>>16)&255);s.val[3]=vdup_n_u8(255);
    for(;x+8<=w;x+=8) {
        uint8x8_t a=vld1_u8(src+x);
        uint64_t bits=vget_lane_u64(vreinterpret_u64_u8(a),0);
        if(!bits) continue;
        if(bits==UINT64_MAX) {vst4_u8((unsigned char *)(dst+x),s);continue;}
        fb_blend8((unsigned char *)(dst+x),s,a);
    }
#endif
    for(;x<w;++x) if(src[x]) dst[x]=fb_mix_pixel(dst[x],NULL,src[x],ink);
}
static inline void fb_fast_row(uint32_t *dst,const unsigned char *src,int w,int type,uint32_t ink)
{
    if(type==1) memcpy(dst,src,(size_t)w*4);
    else if(type==2) fb_rgba_row(dst,src,w);
    else fb_alpha_row(dst,src,w,ink);
}
#endif
