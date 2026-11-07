#ifndef ARCADE_ENGINE_H
#define ARCADE_ENGINE_H
#include <stdint.h>
typedef struct { unsigned cell[16], score, rng; } puzzle;
void puzzle_init(puzzle *p, unsigned seed);
int puzzle_move(puzzle *p, int direction); /* left, right, up, down; spawn only on change */
int puzzle_over(const puzzle *p);
typedef struct {
    double x,y,vx,vy,paddle,accumulator;
    unsigned char brick[50];
    int lives,score,remaining,launched,paused,result;
} breaker;
void breaker_init(breaker *b);
void breaker_paddle(breaker *b, double x);
void breaker_launch(breaker *b);
void breaker_tick(breaker *b, double seconds);
#endif
