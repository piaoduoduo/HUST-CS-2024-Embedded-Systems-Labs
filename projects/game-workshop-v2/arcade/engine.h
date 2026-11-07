#ifndef ARCADE_ENGINE_H
#define ARCADE_ENGINE_H
#include <stdint.h>
typedef struct { unsigned cell[16], score, rng; } puzzle;
void puzzle_init(puzzle *p, unsigned seed);
int puzzle_move(puzzle *p, int direction); /* left, right, up, down; spawn only on change */
int puzzle_over(const puzzle *p);
int puzzle_hint(const puzzle *p); /* deterministic two-ply expectation, no RNG changes */
#define BREAK_PARTICLES 64
#define BREAK_TRAIL 12
typedef struct { double x,y,vx,vy,life; } spark;
typedef struct {
    double x,y,vx,vy,paddle,accumulator;
    unsigned char brick[50];
    int lives,score,remaining,launched,paused,result;
    int level,combo,best_combo,destroyed,shield,drop_type,drop_serial;
    double wide_time,slow_time,drop_x,drop_y,trail_x[BREAK_TRAIL],trail_y[BREAK_TRAIL];
    int trail_count,trail_head;
    spark particles[BREAK_PARTICLES];
    unsigned effects_rng;
} breaker;
void breaker_init(breaker *b);
void breaker_paddle(breaker *b, double x);
void breaker_launch(breaker *b);
void breaker_tick(breaker *b, double seconds);
int breaker_next_level(breaker *b);
double breaker_half_width(const breaker *b);
#endif
