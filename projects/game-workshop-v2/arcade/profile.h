#ifndef ARCADE_PROFILE_H
#define ARCADE_PROFILE_H
#include <stdint.h>
typedef struct {uint32_t puzzle_best,breaker_best,best_combo,badges;} arcade_profile;
typedef struct {
    arcade_profile saved;
    char path[512];
    double pending_seconds;
    int blocked;
} profile_io;
/* Missing file = 0, valid = 1, invalid/unreadable = -1 (preserve and block writes). */
int profile_open(profile_io *io,const char *path,arcade_profile *profile);
int profile_sync(profile_io *io,const arcade_profile *profile,double dt,int force);
#endif
