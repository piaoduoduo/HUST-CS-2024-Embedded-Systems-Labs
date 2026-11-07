from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
DEST=ROOT/'candidate';assert not DEST.exists()
shutil.copytree(WS/'lab3-shortspan-study/candidate/common',DEST/'common')
shutil.copy2(ROOT/'opaque_bitset.h',DEST/'common/opaque_bitset_candidate.h')
p=DEST/'common/opaque_batch_v5.h';s=p.read_text(encoding='utf-8')
needle='static void fb_batch_flush(fb_opaque_batch *batch)'
assert s.count(needle)==1
s=s.replace(needle,'#include "opaque_bitset_candidate.h"\n'+needle)
s=s.replace('struct fb_row_stats row=fb_batch_row(batch,y);','''struct fb_row_stats row;
        #ifdef FB_OPAQUE_BITSET
        row=fb_batch_row_bitset(batch,y);
        #else
        row=fb_batch_row(batch,y);
        #endif''')
# Both renderers remain available for the same-process microbenchmark.
s=s.replace('static struct fb_row_stats fb_batch_row(', 'static inline struct fb_row_stats fb_batch_row(')
s=s.replace('static struct fb_row_stats fb_batch_row_bitset(', 'static inline struct fb_row_stats fb_batch_row_bitset(')
p.write_text(s,encoding='utf-8')
# The included candidate is unused in default profile; inline prevents an unused warning.
p=DEST/'common/opaque_bitset_candidate.h';s=p.read_text(encoding='utf-8').replace('static struct fb_row_stats fb_batch_row_bitset(', 'static inline struct fb_row_stats fb_batch_row_bitset(');p.write_text(s,encoding='utf-8')
paths=[p for base in (WS/'lab3-optimized-v10-prepared',WS/'lab3-optimized-prepared',WS/'hust-embedded-labs-orangepi') for p in base.rglob('*') if p.is_file() and '.git' not in p.parts]
paths+=list(WS.glob('*.tgz'));paths+=list((WS/'lab3-shortspan-study').glob('*.tgz'))
(ROOT/'preserved.json').write_text(json.dumps({str(p.relative_to(WS)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},ensure_ascii=False,indent=2),encoding='utf-8')
print('Independent coverage candidate created; default still interval renderer')
