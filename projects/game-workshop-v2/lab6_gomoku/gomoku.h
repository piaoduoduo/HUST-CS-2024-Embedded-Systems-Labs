#ifndef GOMOKU_H
#define GOMOKU_H
#include <stdint.h>
#define GM_SIZE 15
#define GM_CAPACITY (GM_SIZE * GM_SIZE)
enum { GM_EMPTY, GM_BLACK, GM_WHITE, GM_DRAW };
typedef struct { int row, col; } gm_move;
typedef struct {
    uint8_t cells[GM_SIZE][GM_SIZE];
    gm_move moves[GM_CAPACITY];
    int count, next, result;
} gm_game;
void gm_init(gm_game *game);
int gm_legal(const gm_game *game, int row, int col);
int gm_would_win(const gm_game *game, int row, int col, int side);
int gm_play(gm_game *game, int row, int col);
int gm_undo(gm_game *game, int steps);
int gm_win_line(const gm_game *game, gm_move *first, gm_move *last);
#endif
