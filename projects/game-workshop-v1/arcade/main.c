#define _POSIX_C_SOURCE 200809L
#include "../common/common.h"
#include "app.h"
#include <signal.h>
#include <time.h>
#include <sys/ioctl.h>
#include <linux/fb.h>
static arcade_app app;
static volatile sig_atomic_t stopped;
static struct timespec previous;
static void stop(int signal_number) {(void)signal_number;stopped=1;}
static int screen_ready(void) {
    struct fb_fix_screeninfo fix;struct fb_var_screeninfo var;
    int fd=open("/dev/fb0",O_RDWR);if(fd<0){perror("/dev/fb0");return 0;}
    int ok=ioctl(fd,FBIOGET_FSCREENINFO,&fix)==0&&ioctl(fd,FBIOGET_VSCREENINFO,&var)==0;close(fd);
    return ok&&var.xres==1024&&var.yres==600&&var.bits_per_pixel==32&&
        var.red.offset==16&&var.red.length==8&&var.green.offset==8&&var.green.length==8&&
        var.blue.offset==0&&var.blue.length==8&&fix.line_length>=4096&&
        (uint64_t)fix.smem_len>=(uint64_t)fix.line_length*600;
}
static void touch_callback(int fd) {
    int type,x,y,finger;
    while((type=touch_read(fd,&x,&y,&finger))!=TOUCH_NO_EVENT) {
        if(type==TOUCH_ERROR){fprintf(stderr,"Touch disconnected\n");exit(1);}
        arcade_touch(&app,type,x,y,finger);
    }
}
static void timer_callback(int unused) {
    (void)unused;struct timespec now;
    if(clock_gettime(CLOCK_MONOTONIC,&now)){perror("clock_gettime");exit(1);}
    double dt=(double)(now.tv_sec-previous.tv_sec)+(now.tv_nsec-previous.tv_nsec)/1e9;previous=now;
    if(stopped||app.quit)exit(0);
    if(app.launch_gomoku)exit(42); /* launcher hands framebuffer exclusively to gomoku */
    arcade_tick(&app,dt);
    if(app.dirty){arcade_render(&app);app.dirty=0;}
}
int main(int argc,char **argv) {
    char *device=NULL;
    if(argc==3&&!strcmp(argv[1],"--touch"))device=argv[2];
    else if(argc!=1){fprintf(stderr,"Usage: %s [--touch /dev/input/eventN]\n",argv[0]);return 2;}
    if(!screen_ready()){fprintf(stderr,"Expected 1024x600 32-bit RGB framebuffer\n");return 1;}
    int fd=touch_init(device);if(fd<0)return 1;
    font_init("./font.ttc");fb_image *probe=fb_read_font_image("游",24,NULL);
    if(!probe){fprintf(stderr,"font.ttc missing or unreadable\n");close(fd);return 1;}fb_free_image(probe);
    fb_init("/dev/fb0");
    if(clock_gettime(CLOCK_MONOTONIC,&previous)){perror("clock_gettime");close(fd);return 1;}
    arcade_init(&app,(unsigned)(previous.tv_nsec^previous.tv_sec));
    signal(SIGINT,stop);signal(SIGTERM,stop);
    setvbuf(stdout,NULL,_IOLBF,0);puts("Arcade ready: gomoku / 2048 / breakout; 240Hz physics, 50Hz timer");
    task_add_file(fd,touch_callback);task_add_timer(20,timer_callback);task_loop();return 0;
}
