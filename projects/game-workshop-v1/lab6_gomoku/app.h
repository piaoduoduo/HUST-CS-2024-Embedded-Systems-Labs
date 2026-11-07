#ifndef GM_APP_H
#define GM_APP_H
#include "ai.h"
#define GM_BOARD_X 66
#define GM_BOARD_Y 100
#define GM_CELL 32
#define GM_BUTTON_X 584
#define GM_BUTTON_W 380
#define GM_BUTTON_H 52
#define GM_NEW_Y 230
#define GM_UNDO_Y 294
#define GM_MODE_Y 358
#define GM_EXIT_Y 422
enum { GM_MSG_NORMAL, GM_MSG_OCCUPIED, GM_MSG_FINISHED, GM_MSG_WAIT, GM_MSG_NO_UNDO };
enum { GM_CONFIRM_NONE, GM_CONFIRM_NEW, GM_CONFIRM_MODE, GM_CONFIRM_EXIT };
enum { GM_SAVE_OFF, GM_SAVE_OK, GM_SAVE_ERROR, GM_SAVE_PAUSED };
typedef struct {
    gm_game game;
    gm_ai ai;
    int human_ai, held[5], message, dirty, quit;
    int pending_action, save_status;
    uint64_t now_ms, confirm_deadline_ms;
    unsigned revision;
} gm_app;
void gm_app_init(gm_app *app,int human_ai);
void gm_app_restore(gm_app *app,const gm_game *game,int human_ai);
int gm_screen_cell(int x,int y,gm_move *move);
void gm_app_touch(gm_app *app,int type,int x,int y,int finger);
/* Caller supplies CLOCK_MONOTONIC milliseconds before input and timer work. */
void gm_app_set_time(gm_app *app,uint64_t now_ms);
void gm_app_tick(gm_app *app);
void gm_render(const gm_app *app);
#endif
