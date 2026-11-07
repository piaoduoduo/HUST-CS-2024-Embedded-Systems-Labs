#include "session.h"
#include <ctype.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
static int same_game(const gm_game *a,const gm_game *b)
{
    return a->count==b->count && a->next==b->next && a->result==b->result &&
           !memcmp(a->cells,b->cells,sizeof(a->cells));
}
static unsigned checksum(const gm_game *g,int mode)
{
    uint32_t hash=UINT32_C(2166136261);
    hash=(hash^(unsigned)mode)*UINT32_C(16777619);
    for(int i=0;i<g->count;++i) {
        hash=(hash^(unsigned)g->moves[i].row)*UINT32_C(16777619);
        hash=(hash^(unsigned)g->moves[i].col)*UINT32_C(16777619);
    }
    return (unsigned)hash;
}
int gm_write_session(FILE *file,const gm_game *g,int human_ai)
{
    if(!file || g->count<0 || g->count>GM_CAPACITY || human_ai<0 || human_ai>1) return 0;
    gm_game replay;gm_init(&replay);
    for(int i=0;i<g->count;++i) if(!gm_play(&replay,g->moves[i].row,g->moves[i].col)) return 0;
    if(!same_game(g,&replay)) return 0;
    if(fprintf(file,"HUST-GOMOKU 1\n%d %d\n",human_ai,g->count)<0) return 0;
    for(int i=0;i<g->count;++i) if(fprintf(file,"%d %d\n",g->moves[i].row,g->moves[i].col)<0) return 0;
    return fprintf(file,"END %08x\n",checksum(g,human_ai))>0 && !ferror(file);
}
static int line(FILE *file,char *buf,size_t length)
{
    if(!fgets(buf,(int)length,file)) return 0;
    size_t n=strlen(buf);
    if(!n || buf[n-1]!='\n') return 0;
    buf[--n]=0;if(n && buf[n-1]=='\r')buf[n-1]=0;
    return 1;
}
static int pair(const char *text,int *a,int *b)
{
    char *end;errno=0;long x=strtol(text,&end,10);
    if(errno || end==text || !isspace((unsigned char)*end)) return 0;
    text=end;long y=strtol(text,&end,10);
    if(errno || end==text) return 0;
    while(isspace((unsigned char)*end))++end;
    if(*end || x<0 || x>GM_CAPACITY || y<0 || y>GM_CAPACITY) return 0;
    *a=(int)x;*b=(int)y;return 1;
}
int gm_read_session(FILE *file,gm_game *g,int *human_ai)
{
    char buf[96];int mode,count;
    if(!file || !line(file,buf,sizeof(buf)) || strcmp(buf,"HUST-GOMOKU 1") ||
       !line(file,buf,sizeof(buf)) || !pair(buf,&mode,&count) || mode>1 || count>GM_CAPACITY) return 0;
    gm_game replay;gm_init(&replay);
    for(int i=0;i<count;++i) {
        int r,c;
        if(!line(file,buf,sizeof(buf)) || !pair(buf,&r,&c) || !gm_play(&replay,r,c)) return 0;
    }
    char end_line[40];snprintf(end_line,sizeof(end_line),"END %08x",checksum(&replay,mode));
    if(!line(file,buf,sizeof(buf)) || strcmp(buf,end_line) || fgetc(file)!=EOF || ferror(file)) return 0;
    *g=replay;*human_ai=mode;return 1;
}
