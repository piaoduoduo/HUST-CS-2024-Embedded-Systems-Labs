#include "common.h"
#include <sys/ioctl.h>
#include <linux/fb.h>
#include <linux/kd.h>
#include <linux/vt.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/mman.h>
#include <string.h>

static int LCD_FB_FD;
static int *LCD_FB_BUF;
static int LCD_FB_LINELEN;
static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];

static struct area {
	int x1, x2, y1, y2;
} update_area = {0,0,0,0};

#define AREA_SET_EMPTY(pa) do {\
	(pa)->x1 = SCREEN_WIDTH;\
	(pa)->x2 = 0;\
	(pa)->y1 = SCREEN_HEIGHT;\
	(pa)->y2 = 0;\
} while(0)

void fb_init(char *dev)
{
	int fd;
	struct fb_fix_screeninfo fb_fix;
	struct fb_var_screeninfo fb_var;

	if(LCD_FB_BUF != NULL) return; /*already done*/

	//进入终端图形模式
	fd = open("/dev/tty0",O_RDWR,0);
	ioctl(fd, KDSETMODE, KD_GRAPHICS);
	close(fd);

	//First: Open the device
	if((fd = open(dev, O_RDWR)) < 0){
		printf("Unable to open framebuffer %s, errno = %d\n", dev, errno);
		return;
	}
	if(ioctl(fd, FBIOGET_FSCREENINFO, &fb_fix) < 0){
		printf("Unable to FBIOGET_FSCREENINFO %s\n", dev);
		return;
	}
	if(ioctl(fd, FBIOGET_VSCREENINFO, &fb_var) < 0){
		printf("Unable to FBIOGET_VSCREENINFO %s\n", dev);
		return;
	}

	printf("framebuffer info: bits_per_pixel=%u,size=(%d,%d),virtual_pos_size=(%d,%d)(%d,%d),line_length=%u,smem_len=%u\n",
		fb_var.bits_per_pixel, fb_var.xres, fb_var.yres, fb_var.xoffset, fb_var.yoffset,
		fb_var.xres_virtual, fb_var.yres_virtual, fb_fix.line_length, fb_fix.smem_len);

	//Second: mmap
	void *addr = mmap(NULL, fb_fix.smem_len, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
	if(addr == (void *)-1){
		printf("failed to mmap memory for framebuffer.\n");
		return;
	}

	if((fb_var.xoffset != 0)||(fb_var.yoffset != 0))
	{
		fb_var.xoffset = 0;
		fb_var.yoffset = 0;
		if(ioctl(fd, FBIOPAN_DISPLAY, &fb_var) < 0) {
			printf("FBIOPAN_DISPLAY framebuffer failed\n");
		}
	}

	LCD_FB_FD = fd;
	LCD_FB_BUF = addr;
	LCD_FB_LINELEN = fb_fix.line_length;

	//set empty
	AREA_SET_EMPTY(&update_area);
	return;
}

static void _copy_area(int *dst, int *src, struct area *pa)
{
	int x, y, w, h;
	x = pa->x1; w = pa->x2-x;
	y = pa->y1; h = pa->y2-y;
	char *psrc = (char *)src + y*(SCREEN_WIDTH*4) + x*4;
	char *pdst = (char *)dst + y*LCD_FB_LINELEN + x*4;
	while(h-- > 0){
		memcpy(pdst, psrc, w*4);
		psrc += SCREEN_WIDTH*4;
		pdst += LCD_FB_LINELEN;
	}
}

static int _check_area(struct area *pa)
{
	if(pa->x2 == 0) return 0; //is empty

	if(pa->x1 < 0) pa->x1 = 0;
	if(pa->x2 > SCREEN_WIDTH) pa->x2 = SCREEN_WIDTH;
	if(pa->y1 < 0) pa->y1 = 0;
	if(pa->y2 > SCREEN_HEIGHT) pa->y2 = SCREEN_HEIGHT;

	if((pa->x2 > pa->x1) && (pa->y2 > pa->y1))
		return 1; //no empty

	//set empty
	AREA_SET_EMPTY(pa);
	return 0;
}

void fb_update(void)
{
	if(_check_area(&update_area) == 0) return; //is empty
	_copy_area(LCD_FB_BUF, DRAW_BUF, &update_area);
	AREA_SET_EMPTY(&update_area); //set empty
	return;
}

/*======================================================================*/

static void * _begin_draw(int x, int y, int w, int h)
{
	int x2 = x+w;
	int y2 = y+h;
	if(update_area.x1 > x) update_area.x1 = x;
	if(update_area.y1 > y) update_area.y1 = y;
	if(update_area.x2 < x2) update_area.x2 = x2;
	if(update_area.y2 < y2) update_area.y2 = y2;
	return DRAW_BUF;
}

void fb_draw_pixel(int x, int y, int color)
{
	if(x<0 || y<0 || x>=SCREEN_WIDTH || y>=SCREEN_HEIGHT) return;
	int *buf = _begin_draw(x,y,1,1);
/*---------------------------------------------------*/
	*(buf + y*SCREEN_WIDTH + x) = color;
/*---------------------------------------------------*/
	return;
}

#include "fast_pixels.h"
#include "geometry_v5.h"
void fb_draw_rect(int x, int y, int w, int h, int color)
{
    #ifndef FB_DISABLE_RECT_FAST
    if(w>0 && h>0 && (unsigned)x<SCREEN_WIDTH && (unsigned)y<SCREEN_HEIGHT
       && w<=SCREEN_WIDTH-x && h<=SCREEN_HEIGHT-y) {
        fb_fill_rect_inside(x,y,w,h,color);return;
    }
    #endif
    if(w <= 0 || h <= 0) return;

    /* Clip before indexing. Widen the sums to avoid signed-int overflow. */
    int64_t left = x;
    int64_t top = y;
    int64_t right = (int64_t)x + w;
    int64_t bottom = (int64_t)y + h;

    if(left < 0) left = 0;
    if(top < 0) top = 0;
    if(right > SCREEN_WIDTH) right = SCREEN_WIDTH;
    if(bottom > SCREEN_HEIGHT) bottom = SCREEN_HEIGHT;
    if(left >= right || top >= bottom) return;

    x = (int)left;
    y = (int)top;
    w = (int)(right - left);
    h = (int)(bottom - top);
    #ifndef FB_DISABLE_RECT_FAST
    fb_fill_rect_inside(x,y,w,h,color);
    #else
    int *buf=_begin_draw(x,y,w,h);
    for(int row=0;row<h;row++)for(int col=0;col<w;col++)buf[(y+row)*SCREEN_WIDTH+x+col]=color;
    #endif
    return;
}

void fb_draw_line(int x1, int y1, int x2, int y2, int color)
{
    #ifndef FB_DISABLE_LINE_FAST
    if((unsigned)x1<SCREEN_WIDTH && (unsigned)x2<SCREEN_WIDTH
       && (unsigned)y1<SCREEN_HEIGHT && (unsigned)y2<SCREEN_HEIGHT) {
        fb_line_inside(x1,y1,x2,y2,color);return;
    }
    #endif
    int64_t dx = (int64_t)x2 - x1;
    int64_t dy = (int64_t)y2 - y1;
    int steep = llabs(dy) > llabs(dx);

    /* Use the longer axis, ordered consistently for reversed endpoints. */
    int64_t major1 = steep ? y1 : x1;
    int64_t major2 = steep ? y2 : x2;
    int64_t minor1 = steep ? x1 : y1;
    int64_t minor2 = steep ? x2 : y2;
    if(major1 > major2) {
        int64_t temporary = major1;
        major1 = major2;
        major2 = temporary;
        temporary = minor1;
        minor1 = minor2;
        minor2 = temporary;
    }

    uint64_t length = (uint64_t)(major2 - major1);
    if(length == 0) {
        fb_draw_pixel(x1, y1, color);
        return;
    }

    int direction = minor2 < minor1 ? -1 : 1;
    uint64_t minor_distance = (uint64_t)llabs(minor2 - minor1);
    int64_t limit = steep ? SCREEN_HEIGHT : SCREEN_WIDTH;
    int64_t first = major1 < 0 ? 0 : major1;
    int64_t last = major2 >= limit ? limit - 1 : major2;
    if(first > last) return;

    /*
     * Integer error accumulation, rounded to the nearest pixel.
     * Preserve the error phase when skipping off-screen major coordinates.
     * For 32-bit int endpoints, this product and sum fit in uint64_t.
     * The loop visits at most SCREEN_WIDTH or SCREEN_HEIGHT coordinates.
     */
    uint64_t numerator = minor_distance * (uint64_t)(first - major1)
                       + length / 2;
    int64_t minor = minor1 + direction * (int64_t)(numerator / length);
    uint64_t remainder = numerator % length;

    /* Candidate: same raster points, one dirty box for fully visible lines. */
    int inside = x1 >= 0 && x1 < SCREEN_WIDTH && x2 >= 0 && x2 < SCREEN_WIDTH
              && y1 >= 0 && y1 < SCREEN_HEIGHT && y2 >= 0 && y2 < SCREEN_HEIGHT;
    if(inside) {
        int left = x1 < x2 ? x1 : x2;
        int top = y1 < y2 ? y1 : y2;
        _begin_draw(left, top, abs(x2-x1)+1, abs(y2-y1)+1);
    }
    for(int64_t major = first; major <= last; ++major) {
        if(inside) {
            int x = (int)(steep ? minor : major);
            int y = (int)(steep ? major : minor);
            DRAW_BUF[y * SCREEN_WIDTH + x] = color;
        } else if(steep) {
            fb_draw_pixel((int)minor, (int)major, color);
        } else {
            fb_draw_pixel((int)major, (int)minor, color);
        }
        remainder += minor_distance;
        if(remainder >= length) {
            remainder -= length;
            minor += direction;
        }
    }
    return;
}

#include <limits.h>
#include "fast_pixels.h"
void fb_draw_image(int x, int y, fb_image *image, int color)
{
    if(!image || !image->content || image->pixel_w <= 0 || image->pixel_h <= 0) return;
    int bytes = image->color_type == FB_COLOR_ALPHA_8 ? 1 : 4;
    if(image->color_type != FB_COLOR_RGB_8880 &&
       image->color_type != FB_COLOR_RGBA_8888 &&
       image->color_type != FB_COLOR_ALPHA_8) return;
    if(image->line_byte <= 0 || (int64_t)image->pixel_w * bytes > image->line_byte) return;

    int64_t left = x, top = y;
    int64_t right = (int64_t)x + image->pixel_w;
    int64_t bottom = (int64_t)y + image->pixel_h;
    if(left < 0) left = 0;
    if(top < 0) top = 0;
    if(right > SCREEN_WIDTH) right = SCREEN_WIDTH;
    if(bottom > SCREEN_HEIGHT) bottom = SCREEN_HEIGHT;
    if(left >= right || top >= bottom) return;
    int ix = (int)(left-x), iy = (int)(top-y);
    int w = (int)(right-left), h = (int)(bottom-top);
    int *buf = _begin_draw((int)left, (int)top, w, h);
    const unsigned char *source = (const unsigned char *)image->content
        + (size_t)iy * image->line_byte + (size_t)ix * bytes;
    uint32_t foreground = (uint32_t)color;

    #ifndef FB_PARALLEL_MIN_PIXELS
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

void fb_draw_border(int x, int y, int w, int h, int color)
{
	if(w<=0 || h<=0) return;
	fb_draw_rect(x, y, w, 1, color);
	if(h > 1) {
		fb_draw_rect(x, y+h-1, w, 1, color);
		fb_draw_rect(x, y+1, 1, h-2, color);
		if(w > 1) fb_draw_rect(x+w-1, y+1, 1, h-2, color);
	}
}

#include "text_layout_v5.h"

#include "prepared_image.h"
#include "opaque_batch_v5.h"
