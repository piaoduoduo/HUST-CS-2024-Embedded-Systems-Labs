#include "engine.h"
#include <string.h>
#include <math.h>
#include <stdlib.h>
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
static int slide(puzzle *p,int d) {
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
    return 1;
}
int puzzle_move(puzzle *p,int d) {if(!slide(p,d))return 0;spawn(p);return 1;}
int puzzle_over(const puzzle *p) {
    for(int i=0;i<16;i++) {
        if(!p->cell[i])return 0;
        if(i%4<3&&p->cell[i]==p->cell[i+1])return 0;
        if(i<12&&p->cell[i]==p->cell[i+4])return 0;
    }
    return 1;
}
static int exponent(unsigned v) {int n=0;while(v>1){v>>=1;n++;}return n;}
static double evaluate(const puzzle *p) {
    double score=0;unsigned largest=0;
    for(int i=0;i<16;i++) {
        if(!p->cell[i])score+=250;
        if(p->cell[i]>largest)largest=p->cell[i];
        if(i%4<3)score-=4*abs(exponent(p->cell[i])-exponent(p->cell[i+1]));
        if(i<12)score-=4*abs(exponent(p->cell[i])-exponent(p->cell[i+4]));
    }
    if(largest&&(p->cell[0]==largest||p->cell[3]==largest||p->cell[12]==largest||p->cell[15]==largest))score+=120;
    return score;
}
int puzzle_hint(const puzzle *p) {
    int best=-1;double best_value=-1e30;
    for(int d=0;d<4;d++) {
        puzzle moved=*p;if(!slide(&moved,d))continue;
        double sum=0;int empty=0;
        for(int i=0;i<16;i++)if(!moved.cell[i]) {
            empty++;
            for(int v=2;v<=4;v+=2) {
                puzzle chance=moved;chance.cell[i]=(unsigned)v;
                double future=-1e20;
                for(int next=0;next<4;next++) {
                    puzzle c=chance;if(!slide(&c,next))continue;
                    double s=evaluate(&c)+0.1*(c.score-chance.score);
                    if(s>future)future=s;
                }
                if(future==-1e20)future=evaluate(&chance)-1000;
                sum+=(v==2?0.9:0.1)*future;
            }
        }
        double value=(empty?sum/empty:evaluate(&moved))+0.1*(moved.score-p->score);
        if(value>best_value){best_value=value;best=d;}
    }
    return best;
}
