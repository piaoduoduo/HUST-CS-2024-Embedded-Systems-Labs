#ifndef ARCADE_APP_H
#define ARCADE_APP_H
#include "engine.h"
typedef struct {
    puzzle puzzle; breaker breaker;
    int mode,owner,start_x,start_y,dirty,quit,launch_gomoku,confirm;
    unsigned rng;
} arcade_app;
void arcade_init(arcade_app *a,unsigned seed);
void arcade_touch(arcade_app *a,int type,int x,int y,int finger);
void arcade_tick(arcade_app *a,double dt);
void arcade_render(const arcade_app *a);
#endif
