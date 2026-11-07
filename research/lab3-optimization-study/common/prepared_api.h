#ifndef FB_PREPARED_API_H
#define FB_PREPARED_API_H
#include "common.h"
typedef struct fb_prepared_image fb_prepared_image;
/* Owned immutable snapshot, explicit lifecycle; NULL means use normal drawing. */
fb_prepared_image *fb_prepare_image(const fb_image *source);
void fb_draw_prepared(int x,int y,const fb_prepared_image *,int color);
void fb_free_prepared(fb_prepared_image *);
#endif
