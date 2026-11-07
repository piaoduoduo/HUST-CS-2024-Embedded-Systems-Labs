from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=(ROOT/'common/graphic-fast.c').read_text(encoding='utf-8')
(ROOT/'common/graphic-batch.c').write_text(source+'\n#include "opaque_batch.h"\n',encoding='utf-8')
test=(ROOT.parent/'lab3-prepared/test/main.c').read_text(encoding='utf-8')
test='/* EXPERIMENTAL explicit opaque batch API; execution remains INSIDE jpeg timer. */\n'+test
test=test.replace('#include "../common/common.h"','#include "../common/common.h"\n#include "../common/batch_api.h"')
start=test.index('\tstart = task_get_time();\n\tfor(row=-5; row<605; row+=100)')
end=test.index('\n\tend = task_get_time();',start)
part=test[start:end]
part=part.replace('\tstart = task_get_time();','\tstart = task_get_time();\n\tfb_opaque_batch *batch = fb_opaque_batch_begin();\n\tif(!batch) return EXIT_FAILURE;\n\tfb_batch_stats batch_stats;')
part=part.replace('fb_draw_image(column,row,img1,0);','if(!fb_opaque_batch_add(batch,column,row,img1)) { fb_opaque_batch_end(batch,NULL); return EXIT_FAILURE; }')
part+='\n\tfb_opaque_batch_end(batch,&batch_stats);'
test=test[:start]+part+test[end:]
marker='\tprintf("    **jpeg:\\t%d\\n", end-start);'
assert marker in test
test=test.replace(marker,marker+'\n\tprintf("BATCH_API_EXPERIMENT=1 submitted_pixels=%llu copied_pixels=%llu row_checks=%llu interval_comparisons=%llu flushes=%llu\\n",\n\t    (unsigned long long)batch_stats.submitted_pixels,(unsigned long long)batch_stats.copied_pixels,\n\t    (unsigned long long)batch_stats.row_command_checks,(unsigned long long)batch_stats.interval_comparisons,\n\t    (unsigned long long)batch_stats.flushes);')
(ROOT/'batch-main.c').write_text(test,encoding='utf-8')
print('Generated separate batch variant. Original test untouched.')
