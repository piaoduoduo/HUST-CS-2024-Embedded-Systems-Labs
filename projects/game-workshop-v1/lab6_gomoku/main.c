#include "../common/common.h"
#include "app.h"
#include "storage.h"
#include <signal.h>
#include <sys/ioctl.h>
#include <linux/fb.h>
#include <time.h>
static gm_app app;
static volatile sig_atomic_t stopped;
static const char *save_path="./gomoku-save.txt";
static unsigned saved_revision;
static void stop(int sig) { (void)sig;stopped=1; }
static void update_time(void)
{
    struct timespec now;
    if(clock_gettime(CLOCK_MONOTONIC,&now)!=0) { perror("CLOCK_MONOTONIC");exit(EXIT_FAILURE); }
    gm_app_set_time(&app,(uint64_t)now.tv_sec*1000+(uint64_t)now.tv_nsec/1000000);
}
static int screen_ready(void)
{
    struct fb_fix_screeninfo fix;
    struct fb_var_screeninfo var;
    int fd=open("/dev/fb0",O_RDWR);
    if(fd<0) { perror("/dev/fb0");return 0; }
    int ok=ioctl(fd,FBIOGET_FSCREENINFO,&fix)==0 && ioctl(fd,FBIOGET_VSCREENINFO,&var)==0;
    close(fd);
    if(!ok || var.xres!=1024 || var.yres!=600 || var.bits_per_pixel!=32 ||
       var.red.offset!=16 || var.red.length!=8 || var.green.offset!=8 || var.green.length!=8 ||
       var.blue.offset!=0 || var.blue.length!=8 || fix.line_length<4096 ||
       (uint64_t)fix.smem_len<(uint64_t)fix.line_length*600) {
        fprintf(stderr,"Unsupported framebuffer; expected 1024x600, 32-bit RGB. Run preflight.py first.\n");
        return 0;
    }
    return 1;
}
static void save_if_changed(void)
{
    if(app.save_status==GM_SAVE_PAUSED || saved_revision==app.revision) return;
    int ok=gm_storage_save(save_path,&app.game,app.human_ai);
    saved_revision=app.revision;
    app.save_status=ok ? GM_SAVE_OK : GM_SAVE_ERROR;app.dirty=1;
    if(!ok) perror("Autosave failed");
}
static void flush_view(void)
{
    save_if_changed();
    if(app.dirty) { gm_render(&app);app.dirty=0; }
}
static void touch_callback(int fd)
{
    int type,x,y,finger;
    while((type=touch_read(fd,&x,&y,&finger))!=TOUCH_NO_EVENT) {
        if(type==TOUCH_ERROR) { fprintf(stderr,"Touch input stopped; restart after checking USB cable.\n");exit(EXIT_FAILURE); }
        update_time();
        int previous=app.game.count,previous_result=app.game.result;
        gm_app_touch(&app,type,x,y,finger);
        if(previous!=app.game.count || previous_result!=app.game.result)
            printf("game: moves=%d next=%d result=%d mode=%s\n",app.game.count,app.game.next,app.game.result,app.human_ai?"human-ai":"two-player");
    }
    flush_view();
}
static void timer_callback(int period)
{
    (void)period;
    update_time();
    if(stopped || app.quit) {
        if(app.save_status==GM_SAVE_ERROR) { saved_revision=app.revision-1;save_if_changed(); }
        printf("Gomoku stopped; autosave status=%d\n",app.save_status);
        exit(app.save_status==GM_SAVE_OK ? EXIT_SUCCESS : EXIT_FAILURE);
    }
    int previous=app.game.count;
    gm_app_tick(&app);
    if(app.game.count!=previous) {
        gm_move m=app.game.moves[app.game.count-1];
        printf("AI move: row=%d col=%d moves=%d result=%d\n",m.row,m.col,app.game.count,app.game.result);
    }
    flush_view();
}
int main(int argc,char **argv)
{
    char *device=NULL;int human_ai=1,fresh=0;
    for(int i=1;i<argc;++i) {
        if(!strcmp(argv[i],"--touch") && i+1<argc) device=argv[++i];
        else if(!strcmp(argv[i],"--two-player")) { human_ai=0;fresh=1; }
        else if(!strcmp(argv[i],"--fresh")) fresh=1;
        else if(!strcmp(argv[i],"--save") && i+1<argc) save_path=argv[++i];
        else { fprintf(stderr,"Usage: %s [--touch event-path] [--two-player] [--fresh] [--save path]\n",argv[0]);return EXIT_FAILURE; }
    }
    setvbuf(stdout,NULL,_IOLBF,0);
    if(!screen_ready()) return EXIT_FAILURE;
    int save_lock=gm_storage_lock(save_path);
    if(save_lock<0) { perror("Game save lock; check directory permissions or another instance");return EXIT_FAILURE; }
    int fd=touch_init(device);
    if(fd<0) return EXIT_FAILURE;
    font_init("./font.ttc");
    fb_image *probe=fb_read_font_image("棋",24,NULL);
    if(!probe) { fprintf(stderr,"Load font.ttc failed; run from the course out directory.\n");close(fd);return EXIT_FAILURE; }
    fb_free_image(probe);
    fb_init("/dev/fb0");
    gm_app_init(&app,human_ai);
    gm_game restored;int mode;
    int loaded=fresh ? 0 : gm_storage_load(save_path,&restored,&mode);
    if(loaded>0) {
        gm_app_restore(&app,&restored,mode);saved_revision=app.revision;app.save_status=GM_SAVE_OK;
        printf("Resumed saved game: %d moves\n",app.game.count);
    }
    else if(loaded<0) {
        app.save_status=GM_SAVE_PAUSED;
        fprintf(stderr,"Saved game invalid/unreadable; preserved original and paused autosave. Use --fresh to deliberately replace it.\n");
    }
    flush_view();
    signal(SIGINT,stop);signal(SIGTERM,stop);
    task_add_file(fd,touch_callback);task_add_timer(20,timer_callback);
    printf("Gomoku ready: %s, freestyle >=5 wins, board=15x15, max AI roots=%d\n",app.human_ai?"human-ai":"two-player",GM_AI_CANDIDATES);
    task_loop();return 0;
}
