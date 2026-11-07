#include "engine.h"
#include <string.h>
#include <math.h>
static const double STEP=1.0/240.0;
double breaker_half_width(const breaker *b) {return b->wide_time>0?85:55;}
static double speed(const breaker *b) {return 300+(b->level-1)*35;}
static void reset_ball(breaker *b) {
    b->x=b->paddle;b->y=495;b->vx=speed(b)*0.5;b->vy=-speed(b)*0.8660254;
    b->launched=0;b->combo=0;b->trail_count=0;
}
static void layout(breaker *b) {
    b->remaining=0;b->result=0;b->paused=0;b->accumulator=0;
    b->drop_type=0;b->wide_time=b->slow_time=0;b->shield=0;
    memset(b->particles,0,sizeof(b->particles));
    for(int i=0;i<50;i++) {
        int row=i/10,col=i%10;
        int on=b->level==1||b->level==3||(row+col)%2==0;
        b->brick[i]=(unsigned char)(on?(b->level==3&&row<3?2:1):0);
        b->remaining+=!!b->brick[i];
    }
    breaker_paddle(b,b->paddle);reset_ball(b);
}
void breaker_init(breaker *b) {
    memset(b,0,sizeof(*b));b->lives=3;b->level=1;b->paddle=380;b->effects_rng=71;layout(b);
}
int breaker_next_level(breaker *b) {
    if(b->result!=1||b->level>=3)return 0;
    b->level++;layout(b);return 1;
}
void breaker_paddle(breaker *b,double x) {
    double half=breaker_half_width(b);
    b->paddle=x<40+half?40+half:x>720-half?720-half:x;
    if(!b->launched)b->x=b->paddle;
}
void breaker_launch(breaker *b) {if(!b->result&&!b->paused)b->launched=1;}
static unsigned random_effect(breaker *b) {
    b->effects_rng=b->effects_rng*1664525u+1013904223u;return b->effects_rng;
}
static void burst(breaker *b,double x,double y) {
    int n=0;
    for(int i=0;i<BREAK_PARTICLES&&n<8;i++)if(b->particles[i].life<=0) {
        b->particles[i]=(spark){x,y,(int)(random_effect(b)%241)-120,(int)(random_effect(b)%181)-120,0.45};n++;
    }
}
static void effects(breaker *b,double dt) {
    for(int i=0;i<BREAK_PARTICLES;i++)if(b->particles[i].life>0) {
        spark *p=&b->particles[i];p->life-=dt;p->x+=p->vx*dt;p->y+=p->vy*dt;p->vy+=150*dt;
    }
}
static void powerups(breaker *b) {
    if(b->wide_time>0)b->wide_time=fmax(0,b->wide_time-STEP);
    if(b->slow_time>0)b->slow_time=fmax(0,b->slow_time-STEP);
    if(!b->drop_type)return;
    double old=b->drop_y;b->drop_y+=130*STEP;
    if(old<=522&&b->drop_y>=500&&fabs(b->drop_x-b->paddle)<=breaker_half_width(b)+10) {
        if(b->drop_type==1)b->wide_time=10;
        if(b->drop_type==2)b->slow_time=8;
        if(b->drop_type==3)b->shield=1;
        b->drop_type=0;breaker_paddle(b,b->paddle);
    } else if(b->drop_y>570)b->drop_type=0;
}
static void step(breaker *b) {
    const double r=7;double ox=b->x,oy=b->y;
    powerups(b);effects(b,STEP);
    double dt=STEP*(b->slow_time>0?0.68:1);
    b->x+=b->vx*dt;b->y+=b->vy*dt;
    if(b->x<47){b->x=47;b->vx=fabs(b->vx);}
    if(b->x>713){b->x=713;b->vx=-fabs(b->vx);}
    if(b->y<87){b->y=87;b->vy=fabs(b->vy);}
    double half=breaker_half_width(b);
    if(b->vy>0&&oy+r<=510&&b->y+r>=510&&fabs(b->x-b->paddle)<=half+7) {
        b->y=503;double offset=(b->x-b->paddle)/(half+7);
        b->vx=offset*speed(b)*0.80;b->vy=-sqrt(speed(b)*speed(b)-b->vx*b->vx);
        b->combo=0;
    }
    for(int i=0;i<50;i++)if(b->brick[i]) {
        double x=48+(i%10)*66,y=110+(i/10)*32;
        if(b->x+r>=x&&b->x-r<=x+60&&b->y+r>=y&&b->y-r<=y+24) {
            b->brick[i]--;burst(b,b->x,b->y);
            if(!b->brick[i]) {
                b->remaining--;b->destroyed++;b->combo++;
                if(b->combo>b->best_combo)b->best_combo=b->combo;
                b->score+=10*(b->combo>8?8:b->combo);
                if(b->destroyed%5==0&&!b->drop_type) {
                    b->drop_type=1+(b->drop_serial++%3);b->drop_x=x+30;b->drop_y=y+12;
                }
            } else b->score+=2;
            if(oy+r<=y){b->y=y-r;b->vy=-fabs(b->vy);}
            else if(oy-r>=y+24){b->y=y+24+r;b->vy=fabs(b->vy);}
            else if(ox<x){b->x=x-r;b->vx=-fabs(b->vx);}
            else {b->x=x+60+r;b->vx=fabs(b->vx);}
            if(!b->remaining)b->result=1;
            break;
        }
    }
    if(b->shield&&b->vy>0&&b->y+r>=550) {
        b->shield=0;b->y=543;b->vy=-fabs(b->vy);burst(b,b->x,550);
    }
    if(b->y>570) {
        b->wide_time=b->slow_time=0;b->drop_type=0;
        if(--b->lives==0)b->result=-1;else reset_ball(b);
    }
}
void breaker_tick(breaker *b,double seconds) {
    if(!isfinite(seconds)||seconds<=0||b->paused)return;
    if(seconds>0.1)seconds=0.1;
    if(!b->launched||b->result){effects(b,seconds);return;}
    b->accumulator+=seconds;
    while(b->accumulator+1e-12>=STEP) {
        b->accumulator=fmax(0,b->accumulator-STEP);step(b);
        if(b->result||!b->launched){b->accumulator=0;break;}
    }
    if(b->launched) {
        b->trail_x[b->trail_head]=b->x;b->trail_y[b->trail_head]=b->y;
        b->trail_head=(b->trail_head+1)%BREAK_TRAIL;
        if(b->trail_count<BREAK_TRAIL)b->trail_count++;
    }
}
