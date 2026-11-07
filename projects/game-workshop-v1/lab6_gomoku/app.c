#include "app.h"
#include <stdlib.h>
#include <string.h>
static void reset_game(gm_app *app)
{
    gm_init(&app->game);memset(&app->ai,0,sizeof(app->ai));
    app->message=GM_MSG_NORMAL;app->dirty=1;
    app->pending_action=GM_CONFIRM_NONE;app->confirm_deadline_ms=0;++app->revision;
}
void gm_app_restore(gm_app *app,const gm_game *game,int human_ai)
{
    gm_app_init(app,human_ai);app->game=*game;
    if(app->human_ai && !game->result && game->next==GM_WHITE) gm_ai_begin(&app->ai,game);
}
void gm_app_init(gm_app *app,int human_ai)
{
    memset(app,0,sizeof(*app));app->human_ai=!!human_ai;reset_game(app);
}
int gm_screen_cell(int x,int y,gm_move *move)
{
    if(x<GM_BOARD_X-14 || y<GM_BOARD_Y-14 ||
       x>GM_BOARD_X+(GM_SIZE-1)*GM_CELL+14 || y>GM_BOARD_Y+(GM_SIZE-1)*GM_CELL+14) return 0;
    int col=(x-GM_BOARD_X+GM_CELL/2)/GM_CELL;
    int row=(y-GM_BOARD_Y+GM_CELL/2)/GM_CELL;
    if(abs(x-(GM_BOARD_X+col*GM_CELL))>14 || abs(y-(GM_BOARD_Y+row*GM_CELL))>14) return 0;
    *move=(gm_move){row,col};return 1;
}
static int button(int x,int y,int top)
{ return x>=GM_BUTTON_X && x<GM_BUTTON_X+GM_BUTTON_W && y>=top && y<top+GM_BUTTON_H; }
void gm_app_set_time(gm_app *app,uint64_t now_ms)
{
    if(now_ms<app->now_ms) return;
    app->now_ms=now_ms;
    if(app->pending_action && now_ms>=app->confirm_deadline_ms) {
        app->pending_action=GM_CONFIRM_NONE;app->confirm_deadline_ms=0;app->dirty=1;
    }
}
void gm_app_touch(gm_app *app,int type,int x,int y,int finger)
{
    if(finger<0 || finger>=5) return;
    if(type==3) { app->held[finger]=0;return; }
    if(type!=1 || app->quit || app->held[finger]) return;
    int other_down=0;
    for(int i=0;i<5;++i) other_down|=app->held[i];
    app->held[finger]=1;
    if(other_down || x<0 || y<0 || x>=1024 || y>=600) return;
    int action=button(x,y,GM_NEW_Y) ? GM_CONFIRM_NEW : button(x,y,GM_MODE_Y) ? GM_CONFIRM_MODE :
        button(x,y,GM_EXIT_Y) ? GM_CONFIRM_EXIT : GM_CONFIRM_NONE;
    if(action && app->game.count && app->pending_action!=action) {
        app->pending_action=action;app->confirm_deadline_ms=app->now_ms+3000;app->dirty=1;return;
    }
    if(app->pending_action) { app->pending_action=GM_CONFIRM_NONE;app->confirm_deadline_ms=0;app->dirty=1; }
    if(action==GM_CONFIRM_NEW) { reset_game(app);return; }
    if(action==GM_CONFIRM_MODE) { app->human_ai=!app->human_ai;reset_game(app);return; }
    if(action==GM_CONFIRM_EXIT) { app->quit=1;app->dirty=1;return; }
    if(button(x,y,GM_UNDO_Y)) {
        int steps=app->human_ai ? (app->game.count%2 ? 1 : 2) : 1;
        app->ai.active=0;
        int removed=gm_undo(&app->game,steps);
        app->message=removed ? GM_MSG_NORMAL : GM_MSG_NO_UNDO;
        if(removed) ++app->revision;
        app->dirty=1;return;
    }
    gm_move move;
    if(!gm_screen_cell(x,y,&move)) return;
    if(app->game.result) app->message=GM_MSG_FINISHED;
    else if(app->human_ai && (app->game.next==GM_WHITE || app->ai.active)) app->message=GM_MSG_WAIT;
    else if(!gm_play(&app->game,move.row,move.col)) app->message=GM_MSG_OCCUPIED;
    else {
        app->message=GM_MSG_NORMAL;++app->revision;
        if(app->human_ai && !app->game.result) gm_ai_begin(&app->ai,&app->game);
    }
    app->dirty=1;
}
void gm_app_tick(gm_app *app)
{
    if(app->quit) return;
    if(!app->ai.active) return;
    if(gm_ai_step(&app->ai)) {
        gm_move m=app->ai.best;
        if(!app->game.result && app->game.next==GM_WHITE && gm_legal(&app->game,m.row,m.col)) {
            gm_play(&app->game,m.row,m.col);
            ++app->revision;
        }
        app->message=GM_MSG_NORMAL;app->dirty=1;
    }
}
