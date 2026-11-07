/* Host simulation: production renderer, guarded framebuffer, Pillow glyph masks. */
#include "fixture.h"
#include "../arcade/app.h"
static void save(arcade_app *a,char *name) {
    char path[256];snprintf(path,sizeof(path),"preview/%s.ppm",name);
    arcade_render(a);check_front_matches_back();write_preview_ppm(path);
}
int main(void) {
    reset_surfaces(0);arcade_app a;arcade_init(&a,1);
    save(&a,"menu");a.profile=(arcade_profile){4096,1740,7,15};save(&a,"records");a.mode=1;
    unsigned cells[16]={2,4,8,16,32,64,128,256,512,1024,2048,0,0,2,4,8};
    memcpy(a.puzzle.cell,cells,sizeof(cells));a.puzzle.score=4096;a.can_undo=1;a.hint=puzzle_hint(&a.puzzle);a.pulse=0.2;save(&a,"2048");
    a.mode=2;breaker_launch(&a.breaker);a.breaker.x=300;a.breaker.y=330;save(&a,"breakout");
    a.breaker.paused=1;save(&a,"paused");a.confirm=1;save(&a,"confirm");
    a.confirm=0;a.breaker.result=1;a.breaker.remaining=0;memset(a.breaker.brick,0,sizeof(a.breaker.brick));save(&a,"win");
    breaker_next_level(&a.breaker);save(&a,"level2");
    a.breaker.result=1;breaker_next_level(&a.breaker);breaker_launch(&a.breaker);
    a.breaker.x=75;a.breaker.y=100;a.breaker.vx=0;a.breaker.vy=300;
    breaker_tick(&a.breaker,0.02);a.breaker.combo=5;a.breaker.wide_time=8;a.breaker.slow_time=6;a.breaker.shield=1;
    a.breaker.drop_type=2;a.breaker.drop_x=410;a.breaker.drop_y=350;
    a.breaker.trail_count=12;a.breaker.trail_head=0;
    for(int i=0;i<12;i++){a.breaker.trail_x[i]=300+i*5;a.breaker.trail_y[i]=420-i*5;}
    a.breaker.x=360;a.breaker.y=360;save(&a,"effects");
    a.breaker.result=1;memset(a.breaker.brick,0,50);save(&a,"campaign-win");
    a.mode=0;a.records_ok=0;save(&a,"record-error");
    free(front_storage);puts("PASS: eleven UI states; framebuffer guard and row-padding checks");return 0;
}
