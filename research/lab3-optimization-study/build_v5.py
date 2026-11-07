from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent
source=(ROOT/'common/graphic-v4.c').read_text(encoding='utf-8')
source=source.replace('#include "geometry_v4.h"','#include "geometry_v5.h"')
source=source.replace('    if(w>0 && h>0 && (unsigned)x<SCREEN_WIDTH','    #ifndef FB_DISABLE_RECT_FAST\n    if(w>0 && h>0 && (unsigned)x<SCREEN_WIDTH',1)
source=source.replace('fb_fill_rect_inside(x,y,w,h,color);return;\n    }','fb_fill_rect_inside(x,y,w,h,color);return;\n    }\n    #endif',1)
source=source.replace('    fb_fill_rect_inside(x,y,w,h,color);\n    return;', '''    #ifndef FB_DISABLE_RECT_FAST
    fb_fill_rect_inside(x,y,w,h,color);
    #else
    int *buf=_begin_draw(x,y,w,h);
    for(int row=0;row<h;row++)for(int col=0;col<w;col++)buf[(y+row)*SCREEN_WIDTH+x+col]=color;
    #endif
    return;''',1)
source=source.replace('    if((unsigned)x1<SCREEN_WIDTH','    #ifndef FB_DISABLE_LINE_FAST\n    if((unsigned)x1<SCREEN_WIDTH',1)
source=source.replace('fb_line_inside(x1,y1,x2,y2,color);return;\n    }','fb_line_inside(x1,y1,x2,y2,color);return;\n    }\n    #endif',1)
source=source.replace('#include "text_layout_v4.h"','#include "text_layout_v5.h"')
geometry=(ROOT/'common/geometry_v4.h').read_text(encoding='utf-8').replace('static void','static inline void')
(ROOT/'common/geometry_v5.h').write_text(geometry,encoding='utf-8')
layout=(ROOT/'common/text_layout_v4.h').read_text(encoding='utf-8')
layout=layout.replace('        if(image->color_type==FB_COLOR_ALPHA_8','        #ifndef FB_DISABLE_TEXT_RANGES\n        if(image->color_type==FB_COLOR_ALPHA_8',1)
layout=layout.replace('        e.glyphs[e.count++]=','        #endif\n        e.glyphs[e.count++]=',1)
layout=layout.replace('        size_t range_bytes=', '        #ifndef FB_DISABLE_TEXT_RANGES\n        size_t range_bytes=',1).replace('        #ifndef FB_DISABLE_TEXT_RANGES\n        if(image->color_type','        if(image->color_type',1)
(ROOT/'common/text_layout_v5.h').write_text(layout,encoding='utf-8')
batch=(ROOT/'common/opaque_batch.h').read_text(encoding='utf-8')
batch='#ifdef FB_DISABLE_STATS\n#define FB_COUNT(s) ((void)0)\n#else\n#define FB_COUNT(s) do {s;} while(0)\n#endif\n'+batch
batch=re.sub(r'result\.(?:writes|spans|checks|comparisons)(?:\+\+|\+=\(unsigned\)\([^;]+\));',lambda m:'FB_COUNT('+m[0][:-1]+');',batch)
(ROOT/'common/opaque_batch_v5.h').write_text(batch,encoding='utf-8')
(ROOT/'common/graphic-v5.c').write_text(source+'\n#include "prepared_image.h"\n',encoding='utf-8')
(ROOT/'common/graphic-v5-batch.c').write_text(source+'\n#include "prepared_image.h"\n#include "opaque_batch_v5.h"\n',encoding='utf-8')
test=(ROOT/'batch-main.c').read_text(encoding='utf-8').replace('#include "../common/batch_api.h"','#include "../common/batch_api.h"\n#include "../common/prepared_api.h"')
for image,label in [('img2','png'),('img3','font')]:
    call='fb_draw_image(column,row,%s,'%image
    begin=test.index('\tstart = task_get_time();',test.index('printf("    **jpeg:')) if label=='png' else test.index('\tstart = task_get_time();',test.index('printf("    **png:'))
    end=test.index('\n\tend = task_get_time();',begin)
    block=test[begin:end].replace('\tstart = task_get_time();','\tstart = task_get_time();\n\tfb_prepared_image *prepared_%s=fb_prepare_image(%s);'%(label,image))
    color='0' if label=='png' else 'color[i]'
    block=block.replace('fb_draw_image(column,row,%s,%s);'%(image,color),
      'if(prepared_%s) fb_draw_prepared(column,row,prepared_%s,%s); else fb_draw_image(column,row,%s,%s);'%(label,label,color,image,color))
    block+='\n\tfb_free_prepared(prepared_%s);'%label
    test=test[:begin]+block+test[end:]
(ROOT/'sprint-main.c').write_text('/* Prepared PNG/alpha snapshot creation and destruction are timed. */\n'+test,encoding='utf-8')
print('Generated v5 switches, explicit prepared snapshots, and timed sprint test.')
