#include "../common/common.h"
#include "app.h"
#define BG FB_COLOR(18,25,42)
#define PANEL FB_COLOR(32,43,64)
#define TEXT FB_COLOR(235,240,248)
#define ACCENT FB_COLOR(66,211,184)
static void text(int x,int y,char *s,int size) {fb_draw_text(x,y,s,size,TEXT);}
static void button(int x,int y,int w,char *s) {fb_draw_rect(x,y,w,60,PANEL);text(x+18,y+39,s,24);}
void arcade_render(const arcade_app *a) {
    char buf[100];fb_draw_rect(0,0,1024,600,BG);
    text(40,50,"橙派游戏工坊",30);
    if(!a->mode) {
        text(330,48,"触摸选择 · 三种玩法",20);
        button(50,140,924,"01  五子棋     人机对战 / 同屏双人 / 自动存档");
        button(50,260,924,"02  2048        滑动合并 / 策略挑战");
        button(50,380,924,"03  打砖块     实时碰撞 / 触摸挡板 / 三次机会");
        text(50,550,"五子棋自动存档；其余游戏仅保留当前进程内进度",20);
        button(780,520,220,"退出合集");
    } else {
        button(780,100,220,"返回菜单");button(780,190,220,"重新开始");
        if(a->mode==1) {
            snprintf(buf,sizeof(buf),"2048   得分 %u",a->puzzle.score);text(340,50,buf,24);
            for(int i=0;i<16;i++) {
                int x=110+i%4*120,y=90+i/4*120;unsigned v=a->puzzle.cell[i];
                unsigned power=0;for(unsigned n=v;n>1;n>>=1)power++;
                if(power>11)power=11;
                int color=v?FB_COLOR((35+power*14),(130-power*5),(155-power*6)):PANEL;
                fb_draw_rect(x,y,110,110,color);
                if(v){snprintf(buf,sizeof(buf),"%u",v);text(x+12,y+65,buf,v>=10000?20:30);}
            }
            text(780,390,"在棋盘上滑动",20);text(780,425,"相同数字合并",20);
            int won=0;for(int i=0;i<16;i++)if(a->puzzle.cell[i]>=2048)won=1;
            if(puzzle_over(&a->puzzle))text(780,490,"无可用移动",24);
            else if(won)text(780,490,"已达 2048！",24);
        } else {
            const breaker *b=&a->breaker;
            snprintf(buf,sizeof(buf),"打砖块   得分 %d   生命 %d",b->score,b->lives);text(310,50,buf,24);
            fb_draw_border(40,80,680,490,FB_COLOR(65,82,108));
            for(int i=0;i<50;i++)if(b->brick[i])fb_draw_rect(48+i%10*66,110+i/10*32,60,24,FB_COLOR((80+i/10*30),(180-i/10*20),180));
            fb_draw_rect((int)b->paddle-55,510,110,12,ACCENT);
            fb_draw_rect((int)b->x-7,(int)b->y-7,14,14,TEXT);
            button(780,280,220,b->paused?"继续":"暂停");
            text(780,390,"拖动控制挡板",20);text(780,425,"松手发球",20);
            if(b->result)text(780,490,b->result>0?"全部击破！":"本局结束",24);
            else if(b->paused)text(780,490,"已暂停",24);
            else if(!b->launched)text(780,490,"点击场地发球",20);
        }
        if(a->confirm) {
            fb_draw_rect(770,260,240,290,BG);
            button(780,270,220,"确认重新开始");text(780,380,"点其他处取消",20);
        }
    }
    fb_update();
}
