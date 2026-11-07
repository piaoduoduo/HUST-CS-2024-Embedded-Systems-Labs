/* Host simulation: production renderer, guarded framebuffer, Pillow glyph masks. */
#include "fixture.h"
#include "../arcade/app.h"
static void save(arcade_app *a,char *name) {
    char path[256];snprintf(path,sizeof(path),"preview/%s.ppm",name);
    arcade_render(a);check_front_matches_back();write_preview_ppm(path);
}
int main(void) {
    reset_surfaces(0);arcade_app a;arcade_init(&a,1);
    save(&a,"menu");a.mode=1;
    unsigned cells[16]={2,4,8,16,32,64,128,256,512,1024,2048,0,0,2,4,8};
    memcpy(a.puzzle.cell,cells,sizeof(cells));a.puzzle.score=4096;save(&a,"2048");
    a.mode=2;breaker_launch(&a.breaker);a.breaker.x=300;a.breaker.y=330;save(&a,"breakout");
    a.breaker.paused=1;save(&a,"paused");a.confirm=1;save(&a,"confirm");
    a.confirm=0;a.breaker.result=1;a.breaker.remaining=0;memset(a.breaker.brick,0,sizeof(a.breaker.brick));save(&a,"win");
    free(front_storage);puts("PASS: six UI states; framebuffer guard and row-padding checks");return 0;
}
