#include "../arcade/app.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
static void tap(arcade_app *a,int x,int y){arcade_touch(a,1,x,y,0);arcade_touch(a,3,x,y,0);}
static void shot(breaker *b){b->x=75;b->y=100;b->vx=0;b->vy=300;b->launched=1;breaker_tick(b,0.02);}
int main(void) {
    arcade_app a;arcade_init(&a,1);a.mode=1;
    a.puzzle=(puzzle){.cell={2,2,4},.rng=123};puzzle before=a.puzzle;
    arcade_touch(&a,1,450,200,0);arcade_touch(&a,3,250,200,0);
    assert(a.can_undo&&a.puzzle.score==4);puzzle after=a.puzzle;
    tap(&a,800,300);assert(!a.can_undo&&!memcmp(&before,&a.puzzle,sizeof(before)));
    arcade_touch(&a,1,450,200,0);arcade_touch(&a,3,250,200,0);
    assert(!memcmp(&after,&a.puzzle,sizeof(after))); /* exact RNG restoration */
    before=a.puzzle;tap(&a,800,390);assert(a.hint>=0&&a.hint<4&&!memcmp(&before,&a.puzzle,sizeof(before)));
    for(unsigned seed=1;seed<=200;seed++) {
        puzzle p;puzzle_init(&p,seed);
        for(int i=0;i<30;i++)puzzle_move(&p,(int)((seed+i)%4));
        puzzle old=p;int h=puzzle_hint(&p);assert(!memcmp(&p,&old,sizeof(p)));
        if(h>=0)assert(puzzle_move(&p,h));else assert(puzzle_over(&p));
    }
    breaker b;breaker_init(&b);assert(!breaker_next_level(&b));
    b.result=1;b.score=456;assert(breaker_next_level(&b)&&b.level==2&&b.remaining==25&&b.score==456);
    b.result=1;assert(breaker_next_level(&b)&&b.level==3&&b.remaining==50&&b.brick[0]==2);
    shot(&b);assert(b.brick[0]==1&&b.remaining==50&&b.score==458);
    shot(&b);assert(b.brick[0]==0&&b.remaining==49&&b.combo==1&&b.score==468);
    b.result=1;assert(!breaker_next_level(&b));
    breaker_init(&b);b.destroyed=4;shot(&b);assert(b.drop_type==1&&b.destroyed==5);
    b.drop_x=b.paddle;b.drop_y=499;breaker_tick(&b,0.02);assert(!b.drop_type&&b.wide_time>9.9&&breaker_half_width(&b)==85);
    b.wide_time=0.005;b.drop_type=0;breaker_tick(&b,0.02);assert(b.wide_time==0&&breaker_half_width(&b)==55);
    for(int type=2;type<=3;type++) {
        breaker_init(&b);b.launched=1;b.drop_type=type;b.drop_x=b.paddle;b.drop_y=499;
        breaker_tick(&b,0.02);assert(!b.drop_type);
        if(type==2)assert(b.slow_time>7.9);else assert(b.shield==1);
    }
    b.x=50;b.y=542;b.vy=300;b.vx=0;breaker_tick(&b,0.02);assert(!b.shield&&b.vy<0&&b.lives==3);
    breaker_init(&b);b.launched=1;b.y=400;b.vy=-200;b.vx=0;breaker normal=b;
    b.slow_time=8;breaker_tick(&b,0.1);breaker_tick(&normal,0.1);assert(b.y>normal.y);
    breaker_init(&b);b.combo=4;shot(&b);assert(b.combo==5&&b.score==50&&b.best_combo==5);
    int particles=0;for(int i=0;i<BREAK_PARTICLES;i++)particles+=b.particles[i].life>0;assert(particles>0&&b.trail_count>0);
    b.paused=1;breaker snapshot=b;breaker_tick(&b,1);assert(!memcmp(&b,&snapshot,sizeof(b)));
    arcade_init(&a,1);a.puzzle.score=1234;a.puzzle.cell[0]=2048;a.breaker.score=888;a.breaker.best_combo=6;
    a.breaker.level=3;a.breaker.result=1;arcade_collect(&a);
    assert(a.profile.puzzle_best==1234&&a.profile.breaker_best==888&&a.profile.best_combo==6&&a.profile.badges==19);
    a.mode=1;tap(&a,800,210);tap(&a,800,300);assert(a.puzzle.score==0&&a.profile.puzzle_best==1234);
    /* Long synthetic run: particles, counters and finite physics remain bounded. */
    breaker_init(&b);
    for(int i=0;i<100000;i++) {
        if(b.result<0)breaker_init(&b);
        if(b.result>0&&!breaker_next_level(&b))breaker_init(&b);
        breaker_paddle(&b,80+(i*37)%620);breaker_launch(&b);breaker_tick(&b,0.02);
        assert(isfinite(b.x)&&isfinite(b.y)&&isfinite(b.vx)&&isfinite(b.vy));
        assert(b.remaining>=0&&b.remaining<=50&&b.trail_count<=BREAK_TRAIL&&b.lives>=0&&b.lives<=3);
    }
    puts("PASS: undo+RNG restore, 200 hint positions, three levels, armor, drops, timers, shield, slow, combos, bounded effects, badges, 100000 physics frames");return 0;
}
