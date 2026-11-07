/* TEST EMULATION ONLY. This validates lane arithmetic, not ARM compilation or speed. */
#include <stdint.h>
#include <string.h>
typedef struct {uint8_t v[8];} uint8x8_t;
typedef struct {uint8_t v[16];} uint8x16_t;
typedef struct {uint16_t v[8];} uint16x8_t;
typedef struct {uint16_t v[4];} uint16x4_t;
typedef struct {uint64_t v[1];} uint64x1_t;
typedef struct {uint32_t v[4];} uint32x4_t;
static inline uint32x4_t vdupq_n_u32(uint32_t n){uint32x4_t r;for(int i=0;i<4;i++)r.v[i]=n;return r;}
static inline void vst1q_u32(uint32_t*p,uint32x4_t r){memcpy(p,r.v,16);}
static inline uint32x4_t vld1q_u32(const uint32_t*p){uint32x4_t r;memcpy(r.v,p,16);return r;}
static inline uint8x16_t vld1q_u8(const uint8_t*p){uint8x16_t r;memcpy(r.v,p,16);return r;}
static inline uint32x4_t vreinterpretq_u32_u8(uint8x16_t a){uint32x4_t r;memcpy(r.v,a.v,16);return r;}
static inline uint32x4_t vaddq_u32(uint32x4_t a,uint32x4_t b){for(int i=0;i<4;i++)a.v[i]+=b.v[i];return a;}
static inline uint32x4_t vsubq_u32(uint32x4_t a,uint32x4_t b){for(int i=0;i<4;i++)a.v[i]-=b.v[i];return a;}
static inline uint32x4_t vmulq_u32(uint32x4_t a,uint32x4_t b){for(int i=0;i<4;i++)a.v[i]*=b.v[i];return a;}
static inline uint32x4_t vmlaq_u32(uint32x4_t t,uint32x4_t a,uint32x4_t b){for(int i=0;i<4;i++)t.v[i]+=a.v[i]*b.v[i];return t;}
static inline uint32x4_t vshrq_n_u32(uint32x4_t a,int n){for(int i=0;i<4;i++)a.v[i]>>=n;return a;}
static inline uint32x4_t vshlq_n_u32(uint32x4_t a,int n){for(int i=0;i<4;i++)a.v[i]<<=n;return a;}
static inline uint32x4_t vandq_u32(uint32x4_t a,uint32x4_t b){for(int i=0;i<4;i++)a.v[i]&=b.v[i];return a;}
static inline uint32x4_t vorrq_u32(uint32x4_t a,uint32x4_t b){for(int i=0;i<4;i++)a.v[i]|=b.v[i];return a;}
static inline uint32x4_t vceqq_u32(uint32x4_t a,uint32x4_t b){for(int i=0;i<4;i++)a.v[i]=a.v[i]==b.v[i]?UINT32_MAX:0;return a;}
static inline uint32x4_t vbslq_u32(uint32x4_t m,uint32x4_t a,uint32x4_t b){for(int i=0;i<4;i++)a.v[i]=(m.v[i]&a.v[i])|(~m.v[i]&b.v[i]);return a;}
static inline uint8x8_t vcreate_u8(uint64_t n){uint8x8_t r;memcpy(r.v,&n,8);return r;}
static inline uint16x8_t vmovl_u8(uint8x8_t a){uint16x8_t r;for(int i=0;i<8;i++)r.v[i]=a.v[i];return r;}
static inline uint16x4_t vget_low_u16(uint16x8_t a){uint16x4_t r;memcpy(r.v,a.v,8);return r;}
static inline uint32x4_t vmovl_u16(uint16x4_t a){uint32x4_t r;for(int i=0;i<4;i++)r.v[i]=a.v[i];return r;}
static inline uint16x4_t vld1_u16(const uint16_t*p){uint16x4_t r;memcpy(r.v,p,8);return r;}
typedef struct {uint8x8_t val[4];} uint8x8x4_t;
static inline uint8x8_t vdup_n_u8(uint8_t n){uint8x8_t r;for(int i=0;i<8;i++)r.v[i]=n;return r;}
static inline uint16x8_t vdupq_n_u16(uint16_t n){uint16x8_t r;for(int i=0;i<8;i++)r.v[i]=n;return r;}
static inline uint16x8_t vld1q_u16(const uint16_t*p){uint16x8_t r;memcpy(r.v,p,16);return r;}
static inline uint8x8_t vld1_u8(const uint8_t*p){uint8x8_t r;memcpy(r.v,p,8);return r;}
static inline void vst1_u8(uint8_t*p,uint8x8_t r){memcpy(p,r.v,8);}
static inline uint8x8x4_t vld4_u8(const uint8_t*p){uint8x8x4_t r;for(int i=0;i<8;i++)for(int k=0;k<4;k++)r.val[k].v[i]=p[4*i+k];return r;}
static inline void vst4_u8(uint8_t*p,uint8x8x4_t r){for(int i=0;i<8;i++)for(int k=0;k<4;k++)p[4*i+k]=r.val[k].v[i];}
static inline uint16x8_t vmull_u8(uint8x8_t a,uint8x8_t b){uint16x8_t r;for(int i=0;i<8;i++)r.v[i]=(uint16_t)a.v[i]*b.v[i];return r;}
static inline uint16x8_t vmlal_u8(uint16x8_t t,uint8x8_t a,uint8x8_t b){for(int i=0;i<8;i++)t.v[i]+=(uint16_t)a.v[i]*b.v[i];return t;}
static inline uint8x8_t vsub_u8(uint8x8_t a,uint8x8_t b){for(int i=0;i<8;i++)a.v[i]-=b.v[i];return a;}
static inline uint16x8_t vaddq_u16(uint16x8_t a,uint16x8_t b){for(int i=0;i<8;i++)a.v[i]+=b.v[i];return a;}
static inline uint16x8_t vshrq_n_u16(uint16x8_t a,int n){for(int i=0;i<8;i++)a.v[i]>>=n;return a;}
static inline uint8x8_t vshrn_n_u16(uint16x8_t a,int n){uint8x8_t r;for(int i=0;i<8;i++)r.v[i]=(uint8_t)(a.v[i]>>n);return r;}
static inline uint8x8_t vceq_u8(uint8x8_t a,uint8x8_t b){for(int i=0;i<8;i++)a.v[i]=a.v[i]==b.v[i]?255:0;return a;}
static inline uint8x8_t vbsl_u8(uint8x8_t m,uint8x8_t a,uint8x8_t b){for(int i=0;i<8;i++)a.v[i]=(m.v[i]&a.v[i])|((uint8_t)~m.v[i]&b.v[i]);return a;}
static inline uint64x1_t vreinterpret_u64_u8(uint8x8_t a){uint64x1_t r;memcpy(r.v,a.v,8);return r;}
static inline uint64_t vget_lane_u64(uint64x1_t a,int n){return a.v[n];}
