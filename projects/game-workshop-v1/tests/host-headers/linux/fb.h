/* Host syntax-check shim only; native Linux builds use the real kernel header. */
#ifndef HOST_FB_H
#define HOST_FB_H
#define FBIOGET_FSCREENINFO 0x4602
#define FBIOGET_VSCREENINFO 0x4600
struct fb_bitfield { unsigned offset,length,msb_right; };
struct fb_fix_screeninfo { unsigned line_length,smem_len; };
struct fb_var_screeninfo { unsigned xres,yres,bits_per_pixel;struct fb_bitfield red,green,blue; };
#endif
