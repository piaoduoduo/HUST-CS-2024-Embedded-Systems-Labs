#include "app.h"
#include <string.h>
#include <stdlib.h>
void arcade_init(arcade_app *a,unsigned seed) {
    memset(a,0,sizeof(*a));a->owner=-1;a->rng=seed?seed:1;a->dirty=1;
    puzzle_init(&a->puzzle,a->rng);breaker_init(&a->breaker);
    a->hint=-2;a->records_ok=1;
}
static void restart(arcade_app *a) {
    if(a->mode==1){puzzle_init(&a->puzzle,++a->rng);a->can_undo=0;a->hint=-2;a->pulse=0;}
    if(a->mode==2)breaker_init(&a->breaker);
}
void arcade_touch(arcade_app *a,int type,int x,int y,int finger) {
    arcade_collect(a);
    if(finger<0||finger>=5)return;
    if(type==1) {
        if(a->owner!=-1)return;
        a->owner=finger;a->start_x=x;a->start_y=y;
    } else if(finger!=a->owner)return;
    if(a->mode==2&&!a->confirm&&a->start_x<740&&x<740&&type==2) {
        breaker_paddle(&a->breaker,x);a->dirty=1;
    }
    if(type!=3)return;
    a->owner=-1;a->dirty=1;
    int dx=x-a->start_x,dy=y-a->start_y;
    int tap=abs(dx)<25&&abs(dy)<25;
    if(a->confirm) {
        if(tap&&x>=780&&x<1000&&y>=270&&y<330){restart(a);a->confirm=0;}
        else if(tap)a->confirm=0;
        return;
    }
    if(!a->mode) {
        if(!tap)return;
        if(x>=50&&x<974&&y>=120&&y<180)a->launch_gomoku=1;
        if(x>=50&&x<974&&y>=220&&y<280)a->mode=1;
        if(x>=50&&x<974&&y>=320&&y<380)a->mode=2;
        if(x>=780&&y>=520)a->quit=1;
        return;
    }
    if(tap&&x>=780&&x<1000) {
        if(y>=100&&y<160){a->mode=0;return;}
        if(y>=190&&y<250){a->confirm=1;return;}
        if(a->mode==2&&y>=280&&y<340){a->breaker.paused=!a->breaker.paused;return;}
        if(a->mode==2&&y>=360&&y<420){breaker_next_level(&a->breaker);return;}
        if(a->mode==1&&y>=280&&y<340) {
            if(a->can_undo){a->puzzle=a->undo;a->can_undo=0;a->hint=-2;a->pulse=0;}
            return;
        }
        if(a->mode==1&&y>=360&&y<420){a->hint=puzzle_hint(&a->puzzle);return;}
    }
    if(a->mode==1&&a->start_x>=110&&a->start_x<590&&a->start_y>=90&&a->start_y<570) {
        if(abs(dx)>=35||abs(dy)>=35) {
            puzzle before=a->puzzle;
            if(puzzle_move(&a->puzzle,abs(dx)>abs(dy)?(dx<0?0:1):(dy<0?2:3))) {
                a->undo=before;a->can_undo=1;a->hint=-2;a->pulse=0.22;
            }
        }
    }
    if(a->mode==2&&x<740&&a->start_x<740) {breaker_paddle(&a->breaker,x);breaker_launch(&a->breaker);}
}
void arcade_tick(arcade_app *a,double dt) {
    if(dt>0&&a->pulse>0&&a->mode==1){a->pulse-=dt;if(a->pulse<0)a->pulse=0;a->dirty=1;}
    if(a->mode==2&&!a->confirm) {
        breaker before=a->breaker;
        breaker_tick(&a->breaker,dt);
        if(memcmp(&before,&a->breaker,sizeof(before)))a->dirty=1;
    }
    arcade_collect(a);
}
void arcade_collect(arcade_app *a) {
    arcade_profile before=a->profile;
    if(a->puzzle.score>a->profile.puzzle_best)a->profile.puzzle_best=a->puzzle.score;
    if((unsigned)a->breaker.score>a->profile.breaker_best)a->profile.breaker_best=(unsigned)a->breaker.score;
    if((unsigned)a->breaker.best_combo>a->profile.best_combo)a->profile.best_combo=(unsigned)a->breaker.best_combo;
    for(int i=0;i<16;i++)if(a->puzzle.cell[i]>=2048)a->profile.badges|=1;
    if(a->breaker.best_combo>=5)a->profile.badges|=2;
    if(a->breaker.result==1)a->profile.badges|=1u<<(a->breaker.level+1);
    if(memcmp(&before,&a->profile,sizeof(before)))a->dirty=1;
}
