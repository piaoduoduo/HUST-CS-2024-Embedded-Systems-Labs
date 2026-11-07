#ifndef GM_STORAGE_H
#define GM_STORAGE_H
#include "gomoku.h"
int gm_storage_lock(const char *path);
int gm_storage_load(const char *path,gm_game *game,int *human_ai);
int gm_storage_save(const char *path,const gm_game *game,int human_ai);
#endif
