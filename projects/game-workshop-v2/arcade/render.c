#include "../common/common.h"
#include "app.h"
#define BG FB_COLOR(18,25,42)
#define PANEL FB_COLOR(32,43,64)
#define TEXT FB_COLOR(235,240,248)
#define ACCENT FB_COLOR(66,211,184)
#define GOLD FB_COLOR(255,205,100)
static void text(int x,int y,char *s,int size) {fb_draw_text(x,y,s,size,TEXT);}
static void button(int x,int y,int w,char *s) {fb_draw_rect(x,y,w,60,PANEL);text(x+18,y+39,s,24);}
static void disk(int x,int y,int r,int color) {
    for(int dy=-r;dy<=r;dy++)for(int dx=-r;dx<=r;dx++)if(dx*dx+dy*dy<=r*r)fb_draw_pixel(x+dx,y+dy,color);
}
static void draw_breaker(const breaker *b) {
    char buf[100];
    snprintf(buf,sizeof(buf),"关卡 %d/3   得分 %d   生命 %d",b->level,b->score,b->lives);text(310,50,buf,24);
    fb_draw_border(40,80,680,490,FB_COLOR(65,82,108));
    for(int i=0;i<50;i++)if(b->brick[i]) {
        int x=48+i%10*66,y=110+i/10*32;
        fb_draw_rect(x,y,60,24,FB_COLOR((80+i/10*30),(180-i/10*20),180));
        if(b->brick[i]>1)fb_draw_border(x+4,y+4,52,16,GOLD);
    }
    for(int i=0;i<b->trail_count;i++) {
        int at=(b->trail_head-b->trail_count+i+BREAK_TRAIL)%BREAK_TRAIL;
        disk((int)b->trail_x[at],(int)b->trail_y[at],2+i*4/BREAK_TRAIL,FB_COLOR((28+i*4),(55+i*8),(74+i*8)));
    }
    int half=(int)breaker_half_width(b);
    fb_draw_rect((int)b->paddle-half,510,half*2,12,b->wide_time>0?GOLD:ACCENT);
    disk((int)b->x,(int)b->y,7,TEXT);
    if(b->shield)fb_draw_rect(42,550,676,3,ACCENT);
    for(int i=0;i<BREAK_PARTICLES;i++) {
        const spark *p=&b->particles[i];
        if(p->life>0&&p->x>=42&&p->x<714&&p->y>=82&&p->y<564)fb_draw_rect((int)p->x,(int)p->y,3,3,GOLD);
    }
    if(b->drop_type) {
        int x=(int)b->drop_x,y=(int)b->drop_y;
        fb_draw_rect(x-15,y-15,30,30,FB_COLOR(68,111,151));
        char *labels[]={"","宽","缓","盾"};text(x-10,y+8,labels[b->drop_type],20);
    }
    snprintf(buf,sizeof(buf),"COMBO %d",b->combo);fb_draw_text(58,300,buf,24,b->combo>=5?GOLD:TEXT);
    if(b->wide_time>0){snprintf(buf,sizeof(buf),"加宽 %.0fs",b->wide_time);text(58,335,buf,20);}
    if(b->slow_time>0){snprintf(buf,sizeof(buf),"减速 %.0fs",b->slow_time);text(210,335,buf,20);}
    button(780,280,220,b->paused?"继续":"暂停");
    if(b->result==1&&b->level<3)button(780,360,220,"进入下一关");
    else {text(780,385,"拖动挡板接道具",20);text(780,417,"松手发球",20);}
    if(b->result)text(780,475,b->result<0?"挑战结束":b->level==3?"三关全通！":"本关已完成",24);
    else if(b->paused)text(780,475,"已暂停",24);
    else if(!b->launched)text(780,475,"点击场地发球",20);
    text(780,525,"宽：挡板加宽",16);text(780,550,"缓：球速减慢",16);text(780,575,"盾：抵挡一次漏球",16);
}
void arcade_render(const arcade_app *a) {
    char buf[120];fb_draw_rect(0,0,1024,600,BG);
    text(40,50,"橙派游戏工坊",30);
    if(!a->mode) {
        text(330,48,"挑战版 v2 · 策略与反应",20);
        button(50,120,924,"01  五子棋     人机对战 / 同屏双人 / 自动存档");
        button(50,220,924,"02  2048        撤销一步 / 局面提示 / 挑战纪录");
        button(50,320,924,"03  打砖块     三关挑战 / 连击道具 / 耐打砖块");
        for(int i=0;i<3;i++)fb_draw_rect(50,120+i*100,5,60,ACCENT);
        fb_draw_rect(50,405,924,95,PANEL);
        snprintf(buf,sizeof(buf),"最高分   2048: %u     打砖块: %u     最佳连击: %u",a->profile.puzzle_best,a->profile.breaker_best,a->profile.best_combo);
        text(70,438,buf,20);
        char *labels[]={"2048达成","五连击","第一关","第二关","全通关"};
        for(int i=0;i<5;i++) {
            int x=70+i*175;fb_draw_rect(x,458,150,27,(a->profile.badges&(1u<<i))?FB_COLOR(43,119,109):BG);
            text(x+9,479,labels[i],16);
        }
        text(50,548,a->records_ok?"纪录自动保存 · 点亮徽章，刷新自己的最好成绩":"纪录保存暂停，请检查存档文件和日志",20);
        button(780,520,220,"退出合集");
    } else {
        button(780,100,220,"返回菜单");button(780,190,220,"重新开始");
        if(a->mode==1) {
            snprintf(buf,sizeof(buf),"2048   得分 %u",a->puzzle.score);text(340,50,buf,24);
            for(int i=0;i<16;i++) {
                int x=110+i%4*120,y=90+i/4*120;unsigned v=a->puzzle.cell[i];
                unsigned power=0;for(unsigned n=v;n>1;n>>=1)power++;if(power>11)power=11;
                int color=v?FB_COLOR((35+power*14),(130-power*5),(155-power*6)):PANEL;
                fb_draw_rect(x,y,110,110,color);
                if(v){snprintf(buf,sizeof(buf),"%u",v);text(x+12,y+65,buf,v>=10000?20:30);}
                if(a->pulse>0&&v&&a->undo.cell[i]!=v) {
                    fb_draw_border(x,y,110,110,GOLD);fb_draw_border(x+1,y+1,108,108,GOLD);
                }
            }
            button(780,280,220,a->can_undo?"撤销一步":"暂无可撤销");button(780,360,220,"局面提示");
            char *hints[]={"建议向左滑","建议向右滑","建议向上滑","建议向下滑"};
            if(a->hint>=0)text(780,465,hints[a->hint],24);
            else if(a->hint==-1)text(780,465,"无可用移动",24);
            else text(780,465,"在棋盘上滑动",20);
            snprintf(buf,sizeof(buf),"纪录 %u",a->profile.puzzle_best);text(780,508,buf,20);
            if(puzzle_over(&a->puzzle))text(780,550,"本局结束",24);
            else if(a->profile.badges&1)text(780,550,"已解锁 2048",20);
            text(780,578,"提示为估算，可自由选择",16);
        } else draw_breaker(&a->breaker);
        if(a->confirm) {
            fb_draw_rect(770,260,240,330,BG);
            button(780,270,220,"确认重新开始");text(780,380,"点其他处取消",20);
        }
    }
    fb_update();
}
