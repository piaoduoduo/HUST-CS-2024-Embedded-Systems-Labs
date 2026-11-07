"""Extend the separate candidate after its first four-pixel gates complete."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
common=ROOT/'candidate/common'
p=common/'fast_pixels_v9.h';s=p.read_text(encoding='utf-8')
needle='static inline uint8x8_t fb_mix8(uint8x8_t s, uint8x8_t d, uint8x8_t a)'
helper='''/* For 0<=t<=65025:
   ((t + round(t/256)) + 128)>>8 == (t+128+((t+128)>>8))>>8.
   Rounded shift-accumulate plus rounded narrow preserves exact /255 rounding. */
static inline uint8x8_t fb_round8_candidate(uint16x8_t t)
{
    #ifndef FB_DISABLE_SHORT_ROUND
    return vrshrn_n_u16(vrsraq_n_u16(t,t,8),8);
    #else
    t=vaddq_u16(t,vdupq_n_u16(128));
    t=vaddq_u16(t,vshrq_n_u16(t,8));
    return vshrn_n_u16(t,8);
    #endif
}
'''
assert s.count(needle)==1;s=s.replace(needle,helper+needle)
old='''    t=vaddq_u16(t,vdupq_n_u16(128));
    t=vaddq_u16(t,vshrq_n_u16(t,8));
    return vshrn_n_u16(t,8);'''
pos=s.index(needle);assert s[pos:].count(old)==1
s=s[:pos]+s[pos:].replace(old,'    return fb_round8_candidate(t);',1)
p.write_text(s,encoding='utf-8')
p=common/'prepared_image_v9.h';s=p.read_text(encoding='utf-8')
old='''            t=vaddq_u16(t,vdupq_n_u16(128));t=vaddq_u16(t,vshrq_n_u16(t,8));
            d.val[channel]=vshrn_n_u16(t,8);'''
assert s.count(old)==1;s=s.replace(old,'            d.val[channel]=fb_round8_candidate(t);')
p.write_text(s,encoding='utf-8')
em=ROOT/'candidate/neon-emulation';em.mkdir(exist_ok=True)
shutil.copy2(WS/'lab3-optimization-study/tests/neon-emulation/arm_neon.h',em/'arm_neon.h')
with (em/'arm_neon.h').open('a',encoding='utf-8') as f:
    f.write('''
/* Candidate-only semantic emulation. No ARM instruction speed is simulated. */
static inline uint16x8_t vrsraq_n_u16(uint16x8_t a,uint16x8_t b,int n){for(int i=0;i<8;i++)a.v[i]=(uint16_t)(a.v[i]+(((uint32_t)b.v[i]+(1u<<(n-1)))>>n));return a;}
static inline uint8x8_t vrshrn_n_u16(uint16x8_t a,int n){uint8x8_t r;for(int i=0;i<8;i++)r.v[i]=(uint8_t)(((uint32_t)a.v[i]+(1u<<(n-1)))>>n);return r;}
''')
p=ROOT/'check.py';s=p.read_text(encoding='utf-8')
s=s.replace("'old-four':['-DFB_TEST_NEON','-DFB_DISABLE_PACKED_FOUR']", "'old-four':['-DFB_TEST_NEON','-DFB_DISABLE_PACKED_FOUR'],\n 'old-round':['-DFB_TEST_NEON','-DFB_DISABLE_SHORT_ROUND']")
s=s.replace("'-I'+str(STUDY/'tests/neon-emulation')", "'-I'+str(ROOT/'candidate/neon-emulation')")
s=s.replace("'PASS: 25 gates;", "'PASS: 30 gates;")
p.write_text(s,encoding='utf-8')
# Exhaust the full numerator domain using an independent integer division.
for t in range(65026):
    candidate=(t+((t+128)>>8)+128)>>8
    assert candidate==(t+127)//255,(t,candidate)
print('PASS: all 65026 valid numerators; combined candidate ready for C checks')
