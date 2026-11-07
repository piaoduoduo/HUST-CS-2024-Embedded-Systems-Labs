#include "../common/common.h"
#include "app.h"
#define BG FB_COLOR(246,244,239)
#define INK FB_COLOR(40,50,57)
#define MUTED FB_COLOR(108,116,119)
#define ACCENT FB_COLOR(36,113,97)
#define WOOD FB_COLOR(239,219,181)
#define GRID FB_COLOR(131,107,74)
#define WHITE FB_COLOR(255,255,255)
static void disk(int x,int y,int radius,int color)
{
    for(int dy=-radius;dy<=radius;++dy) for(int dx=-radius;dx<=radius;++dx)
        if(dx*dx+dy*dy<=radius*radius) fb_draw_pixel(x+dx,y+dy,color);
}
static void stone(int x,int y,int side)
{
    disk(x,y,13,FB_COLOR(101,88,67));
    disk(x,y,12,side==GM_BLACK ? INK : WHITE);
    disk(x-4,y-4,3,side==GM_BLACK ? FB_COLOR(75,88,95) : FB_COLOR(239,240,234));
}
static void draw_button(int top,char *label,int enabled,int primary)
{
    int background=primary ? ACCENT : WHITE;
    fb_draw_rect(GM_BUTTON_X,top,GM_BUTTON_W,GM_BUTTON_H,background);
    fb_draw_border(GM_BUTTON_X,top,GM_BUTTON_W,GM_BUTTON_H,FB_COLOR(218,223,216));
    fb_draw_text(GM_BUTTON_X+22,top+35,label,24,primary ? WHITE : enabled ? INK : MUTED);
}
void gm_render(const gm_app *app)
{
    const gm_game *g=&app->game;
    char text[120];
    fb_draw_rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT,BG);
    fb_draw_text(40,43,"触屏五子棋",30,INK);
    fb_draw_text(584,38,"自由规则 / 连续五子或以上获胜",20,MUTED);
    fb_draw_rect(40,74,500,500,WOOD);
    fb_draw_border(40,74,500,500,FB_COLOR(212,188,149));
    for(int i=0;i<GM_SIZE;++i) {
        fb_draw_line(GM_BOARD_X,GM_BOARD_Y+i*GM_CELL,GM_BOARD_X+14*GM_CELL,GM_BOARD_Y+i*GM_CELL,GRID);
        fb_draw_line(GM_BOARD_X+i*GM_CELL,GM_BOARD_Y,GM_BOARD_X+i*GM_CELL,GM_BOARD_Y+14*GM_CELL,GRID);
        snprintf(text,sizeof(text),"%c",'A'+i);
        fb_draw_text(GM_BOARD_X+i*GM_CELL-5,92,text,16,GRID);
        snprintf(text,sizeof(text),"%d",GM_SIZE-i);
        fb_draw_text(GM_BOARD_X-24,GM_BOARD_Y+i*GM_CELL+5,text,16,GRID);
    }
    const int stars[5][2]={{3,3},{3,11},{7,7},{11,3},{11,11}};
    for(int i=0;i<5;++i) disk(GM_BOARD_X+stars[i][1]*GM_CELL,GM_BOARD_Y+stars[i][0]*GM_CELL,3,GRID);
    gm_move first,last;
    if(gm_win_line(g,&first,&last)) {
        int x1=GM_BOARD_X+first.col*GM_CELL,y1=GM_BOARD_Y+first.row*GM_CELL;
        int x2=GM_BOARD_X+last.col*GM_CELL,y2=GM_BOARD_Y+last.row*GM_CELL;
        for(int k=-2;k<=2;++k) fb_draw_line(x1+k,y1,x2+k,y2,ACCENT);
    }
    for(int r=0;r<GM_SIZE;++r) for(int c=0;c<GM_SIZE;++c)
        if(g->cells[r][c]) stone(GM_BOARD_X+c*GM_CELL,GM_BOARD_Y+r*GM_CELL,g->cells[r][c]);
    if(g->count) {
        gm_move m=g->moves[g->count-1];
        fb_draw_rect(GM_BOARD_X+m.col*GM_CELL-2,GM_BOARD_Y+m.row*GM_CELL-2,5,5,FB_COLOR(218,107,65));
    }
    fb_draw_rect(568,74,412,130,WHITE);
    fb_draw_text(584,102,app->human_ai ? "人机对战 / 你执黑棋" : "同屏双人 / 黑棋先行",20,MUTED);
    char *status=app->quit ? "已退出" : g->result==GM_BLACK ? "黑棋获胜" : g->result==GM_WHITE ? "白棋获胜" :
        g->result==GM_DRAW ? "本局和棋" : app->ai.active ? "电脑思考中…" : g->next==GM_BLACK ? "轮到黑棋" : "轮到白棋";
    fb_draw_text(584,148,status,30,g->result ? ACCENT : INK);
    if(g->count) {
        gm_move m=g->moves[g->count-1];
        snprintf(text,sizeof(text),"已落 %d 手 / 最后一手 %c%d",g->count,'A'+m.col,GM_SIZE-m.row);
    } else snprintf(text,sizeof(text),"已落 0 手");
    fb_draw_text(584,184,text,20,MUTED);
    draw_button(GM_NEW_Y,app->pending_action==GM_CONFIRM_NEW ? "再点确认重新开始" : "重新开始",1,1);
    draw_button(GM_UNDO_Y,app->human_ai ? "悔棋 / 回退一轮" : "悔棋 / 回退一步",g->count>0,0);
    draw_button(GM_MODE_Y,app->pending_action==GM_CONFIRM_MODE ? "再点确认切换模式并重开" :
        app->human_ai ? "切换为同屏双人（重开）" : "切换为人机对战（重开）",1,0);
    draw_button(GM_EXIT_Y,app->save_status==GM_SAVE_PAUSED ?
        (app->pending_action==GM_CONFIRM_EXIT ? "再点退出（本局未保存）" : "退出（自动保存已暂停）") :
        app->pending_action==GM_CONFIRM_EXIT ? "再点确认保存并退出" : "保存并退出",1,0);
    const char *messages[]={"点击棋盘交叉点落子","这个位置已有棋子","对局已结束，请重开或悔棋","请等待电脑落子","当前没有可悔的棋步"};
    fb_draw_text(584,512,app->pending_action ? "三秒内再点同一按钮确认" : (char *)messages[app->message],20,
        app->pending_action || app->message ? ACCENT : MUTED);
    fb_draw_text(584,545,"一次按下只落一子，多指不连落",20,MUTED);
    const char *saves[]={"电脑模拟 / 不读写真实存档","对局已自动保存，下次可继续","自动保存失败，请保留日志","旧存档异常，自动保存已暂停"};
    fb_draw_text(584,578,(char *)saves[app->save_status],16,app->save_status>=GM_SAVE_ERROR ? FB_COLOR(170,65,45) : MUTED);
    fb_update();
}
