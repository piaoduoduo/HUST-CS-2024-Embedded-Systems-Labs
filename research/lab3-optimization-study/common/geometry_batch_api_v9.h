#ifndef FB_GEOMETRY_BATCH_API_V9_H
#define FB_GEOMETRY_BATCH_API_V9_H
/* One ordered group of opaque replacement draws.  End the group before any
 * other draw or fb_update.  Ownership is local to begin/end, NULL is valid.
 * Every accepted operation returns 1, including clipped-away operations. */
typedef struct fb_geometry_batch fb_geometry_batch;
fb_geometry_batch *fb_geometry_batch_begin(void);
int fb_geometry_batch_rect(fb_geometry_batch *,int,int,int,int,int);
int fb_geometry_batch_line(fb_geometry_batch *,int,int,int,int,int);
void fb_geometry_batch_end(fb_geometry_batch *);
#endif
