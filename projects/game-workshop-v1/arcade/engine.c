#include "engine.h"
#include <string.h>
#include <math.h>
static unsigned random_next(puzzle *p) {
    unsigned x=p->rng; x^=x<<13; x^=x>>17; x^=x<<5; return p->rng=x;
}
static void spawn(puzzle *p) {
    int empty[16],n=0;
    for(int i=0;i<16;i++) if(!p->cell[i]) empty[n++]=i;
    if(n) { int at=empty[random_next(p)%(unsigned)n]; p->cell[at]=random_next(p)%10 ? 2:4; }
}
void puzzle_init(puzzle *p,unsigned seed) { memset(p,0,sizeof(*p));p->rng=seed?seed:1;spawn(p);spawn(p); }
static int index_at(int d,int line,int i) {
    if(d==0)return line*4+i;
    if(d==1)return line*4+3-i;
    if(d==2)return i*4+line;
    return (3-i)*4+line;
}
int puzzle_move(puzzle *p,int d) {
    if(d<0||d>3)return 0;
    unsigned old[16];memcpy(old,p->cell,sizeof(old));
    for(int l=0;l<4;l++) {
        unsigned a[4]={0},out[4]={0};int n=0,k=0;
        for(int i=0;i<4;i++){unsigned v=p->cell[index_at(d,l,i)];if(v)a[n++]=v;}
        for(int i=0;i<n;i++) {
            unsigned v=a[i];
            if(i+1<n&&a[i+1]==v&&v<0x40000000u){v*=2;p->score+=v;i++;}
            out[k++]=v;
        }
        for(int i=0;i<4;i++)p->cell[index_at(d,l,i)]=out[i];
    }
    if(!memcmp(old,p->cell,sizeof(old)))return 0;
    spawn(p);return 1;
}
int puzzle_over(const puzzle *p) {
    for(int i=0;i<16;i++) {
        if(!p->cell[i])return 0;
        if(i%4<3&&p->cell[i]==p->cell[i+1])return 0;
        if(i<12&&p->cell[i]==p->cell[i+4])return 0;
    }
    return 1;
}
static void reset_ball(breaker *b) { b->x=b->paddle;b->y=495;b->vx=150;b->vy=-260;b->launched=0; }
void breaker_init(breaker *b) {
    memset(b,0,sizeof(*b));memset(b->brick,1,sizeof(b->brick));
    b->lives=3;b->remaining=50;b->paddle=380;reset_ball(b);
}
void breaker_paddle(breaker *b,double x) {
    b->paddle=x<95?95:x>665?665:x;
    if(!b->launched)b->x=b->paddle;
}
void breaker_launch(breaker *b) { if(!b->result&&!b->paused)b->launched=1; }
static void step(breaker *b) {
    const double dt=1.0/240.0,r=7;
    double ox=b->x,oy=b->y;
    b->x+=b->vx*dt;b->y+=b->vy*dt;
    if(b->x<47){b->x=47;b->vx=fabs(b->vx);}
    if(b->x>713){b->x=713;b->vx=-fabs(b->vx);}
    if(b->y<87){b->y=87;b->vy=fabs(b->vy);}
    if(b->vy>0&&oy+r<=510&&b->y+r>=510&&fabs(b->x-b->paddle)<=62) {
        b->y=503;double offset=(b->x-b->paddle)/62;
        b->vx=offset*250;b->vy=-sqrt(320*320-b->vx*b->vx);
    }
    for(int i=0;i<50;i++)if(b->brick[i]) {
        double x=48+(i%10)*66,y=110+(i/10)*32;
        if(b->x+r>=x&&b->x-r<=x+60&&b->y+r>=y&&b->y-r<=y+24) {
            b->brick[i]=0;b->remaining--;b->score+=10;
            if(oy+r<=y){b->y=y-r;b->vy=-fabs(b->vy);}
            else if(oy-r>=y+24){b->y=y+24+r;b->vy=fabs(b->vy);}
            else if(ox<x){b->x=x-r;b->vx=-fabs(b->vx);}
            else {b->x=x+60+r;b->vx=fabs(b->vx);}
            if(!b->remaining)b->result=1;
            break;
        }
    }
    if(b->y>570) { if(--b->lives==0)b->result=-1;else reset_ball(b); }
}
void breaker_tick(breaker *b,double seconds) {
    if(!isfinite(seconds)||seconds<=0||b->paused||!b->launched||b->result)return;
    /* Bound catch-up after OS stalls; fixed substeps prevent tunnelling. */
    if(seconds>0.1)seconds=0.1;
    b->accumulator+=seconds;
    while(b->accumulator>=1.0/240.0) {
        b->accumulator-=1.0/240.0;step(b);
        if(b->result||!b->launched){b->accumulator=0;break;}
    }
}
