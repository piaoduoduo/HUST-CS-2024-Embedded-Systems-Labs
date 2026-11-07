#ifndef GM_AI_H
#define GM_AI_H
#include "gomoku.h"
#define GM_AI_CANDIDATES 12
typedef struct {
    gm_game snapshot;
    gm_move candidates[GM_AI_CANDIDATES], best;
    int count, cursor, side, best_score, active;
} gm_ai;
void gm_ai_begin(gm_ai *ai, const gm_game *game);
/* Evaluates one root candidate per call. Returns 1 when best is ready. */
int gm_ai_step(gm_ai *ai);
#endif
