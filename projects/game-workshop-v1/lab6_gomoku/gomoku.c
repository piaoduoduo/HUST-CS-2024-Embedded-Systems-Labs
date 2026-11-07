#include "gomoku.h"
#include <string.h>
static const int directions[4][2] = {{0,1},{1,0},{1,1},{1,-1}};
static int inside(int r, int c) { return r >= 0 && r < GM_SIZE && c >= 0 && c < GM_SIZE; }
static int run(const gm_game *g, int r, int c, int dr, int dc, int side)
{
    int length = 0;
    for(r += dr, c += dc; inside(r,c) && g->cells[r][c] == side; r += dr, c += dc)
        ++length;
    return length;
}
void gm_init(gm_game *g) { memset(g,0,sizeof(*g)); g->next = GM_BLACK; }
int gm_legal(const gm_game *g, int r, int c)
{ return !g->result && inside(r,c) && g->cells[r][c] == GM_EMPTY; }
int gm_would_win(const gm_game *g, int r, int c, int side)
{
    if(!inside(r,c) || g->cells[r][c] || (side != GM_BLACK && side != GM_WHITE)) return 0;
    for(int d=0; d<4; ++d) {
        int dr=directions[d][0], dc=directions[d][1];
        if(1+run(g,r,c,dr,dc,side)+run(g,r,c,-dr,-dc,side) >= 5) return 1;
    }
    return 0;
}
int gm_play(gm_game *g, int r, int c)
{
    if(!gm_legal(g,r,c) || g->count >= GM_CAPACITY) return 0;
    int side=g->next, win=gm_would_win(g,r,c,side);
    g->cells[r][c]=(uint8_t)side;
    g->moves[g->count++]=(gm_move){r,c};
    g->next=3-side;
    if(win) g->result=side;
    else if(g->count == GM_CAPACITY) g->result=GM_DRAW;
    return 1;
}
int gm_undo(gm_game *g, int steps)
{
    int removed=0;
    while(steps-- > 0 && g->count > 0) {
        gm_move m=g->moves[--g->count];
        g->cells[m.row][m.col]=GM_EMPTY;
        ++removed;
    }
    if(removed) { g->next=g->count%2 ? GM_WHITE : GM_BLACK; g->result=GM_EMPTY; }
    return removed;
}
int gm_win_line(const gm_game *g, gm_move *first, gm_move *last)
{
    if(!g->count || !g->result || g->result == GM_DRAW) return 0;
    gm_move m=g->moves[g->count-1];
    for(int d=0; d<4; ++d) {
        int dr=directions[d][0], dc=directions[d][1];
        int before=run(g,m.row,m.col,-dr,-dc,g->result);
        int after=run(g,m.row,m.col,dr,dc,g->result);
        if(1+before+after >= 5) {
            *first=(gm_move){m.row-before*dr,m.col-before*dc};
            *last=(gm_move){m.row+after*dr,m.col+after*dc};
            return 1;
        }
    }
    return 0;
}
