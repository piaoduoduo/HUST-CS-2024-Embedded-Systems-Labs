#ifndef FB_BATCH_API_H
#define FB_BATCH_API_H
#include "common.h"
typedef struct fb_opaque_batch fb_opaque_batch;
typedef struct fb_batch_stats {
    uint64_t accepted_commands,submitted_pixels,copied_pixels,copied_spans;
    uint64_t row_command_checks,interval_comparisons,flushes;
} fb_batch_stats;
/* Explicit final-frame batching. Until end: source pixels must stay unchanged
 * and alive, and no other drawing/read/update may observe or modify DRAW_BUF.
 * Only RGB_8880 accepted. Returns 0 for invalid input without queueing it.
 * Queues are bounded and can flush early; intermediate results are unspecified.
 */
fb_opaque_batch *fb_opaque_batch_begin(void);
int fb_opaque_batch_add(fb_opaque_batch *,int x,int y,const fb_image *image);
void fb_opaque_batch_end(fb_opaque_batch *,fb_batch_stats *stats);
#endif
