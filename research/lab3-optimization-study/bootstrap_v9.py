"""Create v9 glue in new files; preserve v8 and the original test."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parent
archive=ROOT.parent/'resources/lab3-optimized-v8-ready.tgz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='4936a6db6269fd3e054b95050ebd5feda578cf7e141665dbf62ab475d001ddae'
source=(ROOT/'common/graphic-v8-batch.c').read_text(encoding='utf-8')
source=source.replace('fast_pixels_v8.h','fast_pixels_v9.h').replace('prepared_image_v8.h','prepared_image_v9.h')
source+='\n#include "text_batch_v9.h"\n#include "geometry_batch_v9.h"\n'
(ROOT/'common/graphic-v9-batch.c').write_text(source,encoding='utf-8')
main=(ROOT/'sprint-v6-main.c').read_text(encoding='utf-8')
main=main.replace('#include "../common/prepared_api_v6.h"', '#include "../common/prepared_api_v6.h"\n#include "../common/text_batch_api_v9.h"\n#include "../common/geometry_batch_api_v9.h"')
for marker,label,old,new,kind in (
    ('for(row=-15','rect','fb_draw_rect(','fb_geometry_batch_rect(geometry_rect,','geometry'),
    ('for(row=0;row<=400','line','fb_draw_line(','fb_geometry_batch_line(geometry_line,','geometry'),
    ('for(row=-5;row<605;row+=60)','text','fb_draw_text(','fb_text_batch_add(text_batch,','text')):
    where=main.index(marker)
    start=main.rfind('start = task_get_time();',0,where)+len('start = task_get_time();')
    end=main.index('end = task_get_time();',where)
    block=main[start:end]
    assert old in block and 'fb_update' not in block
    block=block.replace(old,new)
    if kind=='geometry':
        declaration='\n\tfb_geometry_batch *geometry_'+label+'=fb_geometry_batch_begin();'
        finish='\tfb_geometry_batch_end(geometry_'+label+');\n\t'
    else:
        declaration='\n\tfb_text_batch *text_batch=fb_text_batch_begin();'
        finish='\tfb_text_batch_end(text_batch);\n\t'
    main=main[:start]+declaration+block+finish+main[end:]
main='/* V9 EXPERIMENT: geometry/text command gathering and execution are timed. */\n'+main
(ROOT/'sprint-v9-main.c').write_text(main,encoding='utf-8')
print('Created new v9 graphic/main glue; original and v8 untouched')
