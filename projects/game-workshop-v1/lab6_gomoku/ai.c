#include "ai.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#define WIN_SCORE 10000000
static const int dirs[4][2]={{0,1},{1,0},{1,1},{1,-1}};
static int inside(int r,int c) { return r>=0 && r<GM_SIZE && c>=0 && c<GM_SIZE; }
static int shape(int length,int open)
{
    if(length>=5) return 500000;
    if(!open) return 0;
    if(length==4) return open==2 ? 50000 : 5000;
    if(length==3) return open==2 ? 1500 : 120;
    if(length==2) return open==2 ? 70 : 8;
    return open==2 ? 3 : 1;
}
static int near_stone(const gm_game *g,int r,int c)
{
    if(!g->count) return r==GM_SIZE/2 && c==GM_SIZE/2;
    for(int dr=-2;dr<=2;++dr) for(int dc=-2;dc<=2;++dc)
        if(inside(r+dr,c+dc) && g->cells[r+dr][c+dc]) return 1;
    return 0;
}
static int placement(const gm_game *g,int r,int c,int side)
{
    int total=0;
    for(int d=0;d<4;++d) {
        int length=1,open=0;
        for(int sign=-1;sign<=1;sign+=2) {
            int rr=r+dirs[d][0]*sign, cc=c+dirs[d][1]*sign;
            while(inside(rr,cc) && g->cells[rr][cc]==side) {
                ++length; rr+=dirs[d][0]*sign; cc+=dirs[d][1]*sign;
            }
            if(inside(rr,cc) && !g->cells[rr][cc]) ++open;
        }
        total+=shape(length,open);
        /* Five-cell windows recognize broken threats, not just contiguous runs. */
        for(int start=-4;start<=0;++start) {
            int stones=0,valid=1;
            for(int k=0;k<5;++k) {
                int delta=start+k,rr=r+delta*dirs[d][0],cc=c+delta*dirs[d][1];
                if(!inside(rr,cc) || (g->cells[rr][cc] && g->cells[rr][cc]!=side)) { valid=0; break; }
                stones+=delta==0 || g->cells[rr][cc]==side;
            }
            if(valid) total+=stones==5 ? 500000 : stones==4 ? 3000 : stones==3 ? 150 : stones==2 ? 10 : 0;
        }
    }
    return total;
}
static int position_score(const gm_game *g,int side)
{
    int total=0;
    for(int r=0;r<GM_SIZE;++r) for(int c=0;c<GM_SIZE;++c) {
        int stone=g->cells[r][c];
        if(!stone) continue;
        for(int d=0;d<4;++d) {
            int dr=dirs[d][0],dc=dirs[d][1],pr=r-dr,pc=c-dc;
            if(inside(pr,pc) && g->cells[pr][pc]==stone) continue;
            int length=0,rr=r,cc=c;
            while(inside(rr,cc) && g->cells[rr][cc]==stone) { ++length;rr+=dr;cc+=dc; }
            int open=(inside(pr,pc) && !g->cells[pr][pc])+(inside(rr,cc) && !g->cells[rr][cc]);
            total+=(stone==side ? 1 : -1)*shape(length,open);
        }
    }
    return total;
}
static int candidates(const gm_game *g,int side,gm_move *out,int capacity)
{
    int scores[GM_AI_CANDIDATES],count=0;
    for(int r=0;r<GM_SIZE;++r) for(int c=0;c<GM_SIZE;++c) {
        if(!gm_legal(g,r,c) || !near_stone(g,r,c)) continue;
        int score=placement(g,r,c,side)*2+placement(g,r,c,3-side)*2;
        score=score*4-(abs(r-GM_SIZE/2)+abs(c-GM_SIZE/2));
        int index=count;
        if(index==capacity) { if(score<=scores[index-1]) continue; --index; }
        else ++count;
        while(index>0 && score>scores[index-1]) { scores[index]=scores[index-1];out[index]=out[index-1];--index; }
        scores[index]=score;out[index]=(gm_move){r,c};
    }
    return count;
}
void gm_ai_begin(gm_ai *ai,const gm_game *g)
{
    memset(ai,0,sizeof(*ai));ai->snapshot=*g;ai->side=g->next;
    ai->best=(gm_move){-1,-1};ai->best_score=INT_MIN;
    if(g->result || g->count==GM_CAPACITY) return;
    /* Check all legal cells before pruning: never discard a one-move win. */
    for(int side=g->next,pass=0;pass<2;++pass,side=3-side)
        for(int r=0;r<GM_SIZE;++r) for(int c=0;c<GM_SIZE;++c)
            if(gm_legal(g,r,c) && gm_would_win(g,r,c,side)) {
                ai->candidates[0]=(gm_move){r,c};ai->count=1;ai->active=1;return;
            }
    ai->count=candidates(g,g->next,ai->candidates,GM_AI_CANDIDATES);
    ai->active=ai->count>0;
}
int gm_ai_step(gm_ai *ai)
{
    if(!ai->active) return 1;
    gm_move move=ai->candidates[ai->cursor++];
    gm_game after=ai->snapshot;
    gm_play(&after,move.row,move.col);
    int score=after.result==ai->side ? WIN_SCORE : position_score(&after,ai->side);
    if(!after.result) {
        int losing=0;
        for(int r=0;r<GM_SIZE && !losing;++r) for(int c=0;c<GM_SIZE;++c)
            if(gm_legal(&after,r,c) && gm_would_win(&after,r,c,3-ai->side)) { losing=1;break; }
        if(losing) score=-WIN_SCORE;
        else {
            gm_move replies[GM_AI_CANDIDATES];
            int n=candidates(&after,3-ai->side,replies,8),worst=INT_MAX;
            for(int i=0;i<n;++i) {
                gm_game leaf=after;gm_play(&leaf,replies[i].row,replies[i].col);
                int value=leaf.result==3-ai->side ? -WIN_SCORE : position_score(&leaf,ai->side);
                if(value<worst) worst=value;
            }
            if(n) score=worst;
        }
    }
    if(score>ai->best_score) { ai->best_score=score;ai->best=move; }
    ai->active=ai->cursor<ai->count;
    return !ai->active;
}
