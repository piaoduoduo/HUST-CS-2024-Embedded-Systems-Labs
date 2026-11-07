/* Host syntax shim only: native Linux uses real flock. */
#define LOCK_EX 2
#define LOCK_NB 4
int flock(int fd,int operation);
