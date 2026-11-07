"""Independent short-span candidate; never edit or promote v9/v10 packages."""
from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parent
WS=ROOT.parent
SOURCE=WS/'lab3-optimized-v10-prepared'
DEST=ROOT/'candidate'
assert not DEST.exists(), 'Candidate already exists; inspect before rebuilding'
shutil.copytree(SOURCE/'common',DEST/'common')
p=DEST/'common/fast_pixels_v9.h'
s=p.read_text(encoding='utf-8')
needle='static inline void fb_blend4(uint32_t *dst,uint32x4_t s,uint32x4_t a,int partial)'
helper='''/* Each packed half remains <= 65407 after correction: no lane carry.
   Keep the same /255 rounding; this is not premultiplied /256 blending. */
static inline uint32x4_t fb_round4_rb_candidate(uint32x4_t t)
{
    uint32x4_t mask=vdupq_n_u32(0x00ff00ffu);
    t=vaddq_u32(t,vdupq_n_u32(0x00800080u));
    return vandq_u32(vshrq_n_u32(vaddq_u32(t,vandq_u32(vshrq_n_u32(t,8),mask)),8),mask);
}
'''
assert s.count(needle)==1
s=s.replace(needle,helper+needle)
start=s.index('    uint32x4_t b=fb_mix4_channel',s.index(needle))
end=s.index('    if(!partial)',start)
old=s[start:end]
new='''    #ifndef FB_DISABLE_PACKED_FOUR
    uint32x4_t rbmask=vdupq_n_u32(0x00ff00ffu);
    uint32x4_t rb=fb_round4_rb_candidate(vmlaq_u32(vmulq_u32(vandq_u32(s,rbmask),a),
        vandq_u32(d,rbmask),vsubq_u32(vdupq_n_u32(255),a)));
    uint32x4_t g=fb_mix4_channel(vandq_u32(vshrq_n_u32(s,8),mask),vandq_u32(vshrq_n_u32(d,8),mask),a);
    uint32x4_t out=vorrq_u32(vdupq_n_u32(0xff000000u),vorrq_u32(rb,vshlq_n_u32(g,8)));
    #else
'''+old+'    #endif\n'
s=s[:start]+new+s[end:]
p.write_text(s,encoding='utf-8')
p=DEST/'common/prepared_image_v9.h';s=p.read_text(encoding='utf-8')
start=s.index('        uint32x4_t dest[3]=')
end=s.index('x+=4;',start)+len('x+=4;')
old=s[start:end]
new='''        #ifndef FB_DISABLE_PACKED_FOUR
        uint32x4_t rbmask=vdupq_n_u32(0x00ff00ffu);
        uint32x4_t products=vorrq_u32(vmovl_u16(vld1_u16(b+x)),vshlq_n_u32(vmovl_u16(vld1_u16(r+x)),16));
        uint32x4_t rb=fb_round4_rb_candidate(vmlaq_u32(products,vandq_u32(d,rbmask),inv));
        uint32x4_t green=vmlaq_u32(vmovl_u16(vld1_u16(g+x)),vandq_u32(vshrq_n_u32(d,8),mask),inv);
        green=vaddq_u32(green,vdupq_n_u32(128));
        green=vshrq_n_u32(vaddq_u32(green,vshrq_n_u32(green,8)),8);
        vst1q_u32(dst+x,vorrq_u32(vdupq_n_u32(0xff000000u),vorrq_u32(rb,vshlq_n_u32(green,8))));x+=4;
        #else
'''+old+'\n        #endif'
s=s[:start]+new+s[end:];p.write_text(s,encoding='utf-8')
manifest={str(p.relative_to(WS)):hashlib.sha256(p.read_bytes()).hexdigest() for p in WS.glob('*.tgz')}
manifest.update({str(p.relative_to(WS)):hashlib.sha256(p.read_bytes()).hexdigest() for base in (SOURCE,WS/'lab3-optimized-prepared',WS/'hust-embedded-labs-orangepi') for p in base.rglob('*') if p.is_file() and '.git' not in p.parts})
(ROOT/'preserved.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared independent candidate; production packages unchanged')
