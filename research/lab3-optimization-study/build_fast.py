"""Generate a separate fast candidate. Run host_tests_fast.py after changes."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=(ROOT/'common/graphic.c').read_text(encoding='utf-8')
begin=source.index('/* Blend one channel')
end=source.index('void fb_draw_image(',begin)
source=source[:begin]+'#include <limits.h>\n#include "fast_pixels.h"\n'+source[end:]
begin=source.index('    for(int row = 0; row < h; ++row) {',source.index('void fb_draw_image('))
end=source.index('\nvoid fb_draw_border(',begin)
source=source[:begin]+'''    #ifndef FB_PARALLEL_MIN_PIXELS
    #define FB_PARALLEL_MIN_PIXELS 65536
    #endif
    #ifdef _OPENMP
    if((size_t)w*h>=FB_PARALLEL_MIN_PIXELS) {
        #pragma omp parallel for schedule(static)
        for(int row=0;row<h;++row) {
            uint32_t *dst=(uint32_t *)(buf+((int)top+row)*SCREEN_WIDTH+(int)left);
            fb_fast_row(dst,source+(size_t)row*image->line_byte,w,image->color_type,foreground);
        }
        return;
    }
    #endif
    for(int row=0;row<h;++row) {
        uint32_t *dst=(uint32_t *)(buf+((int)top+row)*SCREEN_WIDTH+(int)left);
        fb_fast_row(dst,source+(size_t)row*image->line_byte,w,image->color_type,foreground);
    }
}
''' +source[end:]
source=source[:source.index('/** draw a text string **/')]+ '#include "text_layout.h"\n'
(ROOT/'common/graphic-fast.c').write_text(source,encoding='utf-8')
image=(ROOT.parent/'lab3-prepared/common/image.c').read_text(encoding='utf-8')
image+='\n/* Identity for layout-cache keys. Images returned by the existing API stay owned. */\nconst void *fb_font_identity(void) { return face; }\n'
(ROOT/'common/image-fast.c').write_text(image,encoding='utf-8')
print('Generated fast candidate; no deployed source changed.')
