#ifndef GM_SESSION_H
#define GM_SESSION_H
#include "gomoku.h"
#include <stdio.h>
int gm_write_session(FILE *file,const gm_game *game,int human_ai);
/* Parse/replay into temporary state; failure leaves both output arguments intact. */
int gm_read_session(FILE *file,gm_game *game,int *human_ai);
#endif
