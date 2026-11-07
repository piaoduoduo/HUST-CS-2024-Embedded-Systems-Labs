#include "storage.h"
#include "session.h"
#include <errno.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <unistd.h>
static int sync_directory(const char *path)
{
    char directory[4096];
    if(strlen(path)>=sizeof(directory)) { errno=ENAMETOOLONG;return 0; }
    strcpy(directory,path);char *slash=strrchr(directory,'/');
    if(!slash) strcpy(directory,".");
    else if(slash==directory) slash[1]=0;
    else *slash=0;
    int fd=open(directory,O_RDONLY|O_DIRECTORY);
    if(fd<0) return 0;
    int ok=fsync(fd)==0,error=errno;close(fd);errno=error;return ok;
}
int gm_storage_lock(const char *path)
{
    char lock_path[4096];
    if(snprintf(lock_path,sizeof(lock_path),"%s.lock",path)>=(int)sizeof(lock_path)) { errno=ENAMETOOLONG;return -1; }
    int fd=open(lock_path,O_CREAT|O_RDWR,0600);
    if(fd<0) return -1;
    if(flock(fd,LOCK_EX|LOCK_NB)<0) { int error=errno;close(fd);errno=error;return -1; }
    return fd;
}
int gm_storage_load(const char *path,gm_game *game,int *human_ai)
{
    FILE *file=fopen(path,"rb");
    if(!file) return errno==ENOENT ? 0 : -1;
    int ok=gm_read_session(file,game,human_ai);
    int closed=fclose(file)==0;
    if(!ok || !closed) { errno=EINVAL;return -1; }
    return 1;
}
int gm_storage_save(const char *path,const gm_game *game,int human_ai)
{
    char temp[4096];
    if(snprintf(temp,sizeof(temp),"%s.tmp-XXXXXX",path)>=(int)sizeof(temp)) { errno=ENAMETOOLONG;return 0; }
    int fd=mkstemp(temp);
    if(fd<0) return 0;
    FILE *file=fdopen(fd,"wb");
    if(!file) { int error=errno;close(fd);unlink(temp);errno=error;return 0; }
    int ok=gm_write_session(file,game,human_ai) && fflush(file)==0 && fsync(fd)==0;
    int error=errno;
    if(fclose(file)!=0) { ok=0;error=errno; }
    if(ok && rename(temp,path)==0) return sync_directory(path);
    if(ok) error=errno;
    unlink(temp);errno=error ? error : EIO;return 0;
}
