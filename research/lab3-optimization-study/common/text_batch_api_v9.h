/* Explicit ordered text batch. begin/add/end (including allocation, rasterization,
 * index construction and destruction) belong INSIDE the measured text stage.
 * add snapshots glyph pixels and the string; its input can be freed immediately.
 * Do not interleave other framebuffer drawing between add calls and end.
 * A NULL batch or resource limit falls back internally to ordered immediate
 * drawing. The caller must NOT retry an add based on its return value.
 * Returns 1 for accepted/drawn nonempty text; 0 for NULL/empty text. */
#ifndef FB_TEXT_BATCH_API_V9_H
#define FB_TEXT_BATCH_API_V9_H
typedef struct fb_text_batch fb_text_batch;
fb_text_batch *fb_text_batch_begin(void);
int fb_text_batch_add(fb_text_batch *,int,int,const char *,int,int);
void fb_text_batch_end(fb_text_batch *);
#endif
