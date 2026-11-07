#include "../arcade/app.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
static unsigned total(const puzzle *p) {unsigned n=0;for(int i=0;i<16;i++)n+=p->cell[i];return n;}
static void tap(arcade_app *a,int x,int y) {arcade_touch(a,1,x,y,0);arcade_touch(a,3,x,y,0);}
int main(void) {
    puzzle p={.cell={2,2,2,2},.rng=1};assert(puzzle_move(&p,0));
    assert(p.cell[0]==4&&p.cell[1]==4&&p.score==8);
    p=(puzzle){.cell={2,2,4,0},.rng=1};puzzle_move(&p,0);assert(p.cell[0]==4&&p.cell[1]==4&&p.score==4);
    p=(puzzle){.cell={2,0,0,0},.rng=1};puzzle copy=p;assert(!puzzle_move(&p,0));assert(!memcmp(&p,&copy,sizeof(p)));
    p=(puzzle){.cell={2,4,2,4,4,2,4,2,2,4,2,4,4,2,4,2},.rng=1};assert(puzzle_over(&p));
    p.cell[0]=4;assert(!puzzle_over(&p));
    for(int d=0;d<4;d++) {
        puzzle_init(&p,123);
        for(int i=0;i<2000;i++) {
            unsigned before=total(&p);int changed=puzzle_move(&p,(i+d)%4);
            unsigned delta=total(&p)-before;assert(changed?(delta==2||delta==4):delta==0);
            for(int j=0;j<16;j++)assert(!p.cell[j]||!(p.cell[j]&(p.cell[j]-1)));
            if(puzzle_over(&p))puzzle_init(&p,(unsigned)i+1);
        }
    }
    breaker b;breaker_init(&b);assert(b.remaining==50&&b.lives==3);
    breaker_paddle(&b,-100);assert(b.paddle==95);breaker_paddle(&b,1000);assert(b.paddle==665);
    breaker_init(&b);breaker_launch(&b);b.paused=1;breaker old=b;breaker_tick(&b,0.1);assert(!memcmp(&b,&old,sizeof(b)));
    b.paused=0;b.x=48;b.y=350;b.vx=-300;b.vy=0;breaker_tick(&b,0.02);assert(b.vx>0&&b.x>=47);
    breaker_init(&b);breaker_launch(&b);b.x=b.paddle;b.y=501;b.vy=300;breaker_tick(&b,0.02);assert(b.vy<0);
    breaker_init(&b);breaker_launch(&b);b.x=75;b.y=100;b.vy=300;b.vx=0;breaker_tick(&b,0.02);assert(b.remaining==49&&b.score==10&&b.vy<0);
    breaker_init(&b);breaker_launch(&b);b.y=569;b.vy=300;breaker_tick(&b,0.02);assert(b.lives==2&&!b.launched);
    b.lives=1;breaker_launch(&b);b.y=569;b.vy=300;breaker_tick(&b,0.02);assert(b.result==-1);
    breaker_init(&b);memset(b.brick,0,sizeof(b.brick));b.brick[0]=1;b.remaining=1;breaker_launch(&b);
    b.x=75;b.y=100;b.vy=300;b.vx=0;breaker_tick(&b,0.02);assert(b.result==1&&b.remaining==0);
    breaker_init(&b);breaker_launch(&b);breaker c=b;
    breaker_tick(&b,0.1);for(int i=0;i<10;i++)breaker_tick(&c,0.01);
    assert(fabs(b.x-c.x)<0.01&&fabs(b.y-c.y)<0.01);
    arcade_app a;arcade_init(&a,1);tap(&a,200,250);assert(a.mode==1);
    copy=a.puzzle;arcade_touch(&a,1,200,200,0);arcade_touch(&a,1,300,300,1);arcade_touch(&a,3,500,300,1);assert(!memcmp(&copy,&a.puzzle,sizeof(copy)));
    arcade_touch(&a,3,200,200,0);assert(a.owner==-1);
    tap(&a,800,210);assert(a.confirm);tap(&a,500,300);assert(!a.confirm);
    tap(&a,800,120);assert(a.mode==0);tap(&a,200,350);assert(a.mode==2);
    tap(&a,400,400);assert(a.breaker.launched);tap(&a,800,300);assert(a.breaker.paused);
    tap(&a,800,210);tap(&a,800,300);assert(!a.confirm&&!a.breaker.launched&&a.breaker.lives==3);
    tap(&a,800,120);tap(&a,200,150);assert(a.launch_gomoku);
    puts("PASS: 8000 generated 2048 moves; merge rules, no-op RNG, conservation, collisions, win/loss, pause, fixed-step timing, multi-touch ownership, menu and restart");
    return 0;
}
