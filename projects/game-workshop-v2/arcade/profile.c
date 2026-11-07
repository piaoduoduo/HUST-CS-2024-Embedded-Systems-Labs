#define _POSIX_C_SOURCE 200809L
#include "profile.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <math.h>
#ifdef _WIN32
#include <windows.h>
#include <io.h>
#else
#include <unistd.h>
#include <fcntl.h>
#endif
static uint32_t checksum(const arcade_profile *p) {
    uint32_t h=2166136261u,v[4]={p->puzzle_best,p->breaker_best,p->best_combo,p->badges};
    for(int i=0;i<4;i++)for(int shift=0;shift<32;shift+=8){h^=(v[i]>>shift)&255;h*=16777619u;}
    return h;
}
static int read_profile(FILE *f,arcade_profile *p) {
    char buf[160];size_t n=fread(buf,1,sizeof(buf)-1,f);
    if(ferror(f)||!feof(f)||n<8)return 0;
    buf[n]=0;if(memchr(buf,0,n)||strncmp(buf,"ARCADE2\n",8))return 0;
    uint32_t v[5];char *s=buf+8;
    for(int i=0;i<5;i++) {
        while(*s==' '||*s=='\n'||*s=='\r')s++;
        if(*s<'0'||*s>'9')return 0;
        char *end;errno=0;unsigned long long x=strtoull(s,&end,10);
        if(errno||x>UINT32_MAX||end==s)return 0;
        v[i]=(uint32_t)x;s=end;
    }
    while(*s==' '||*s=='\n'||*s=='\r')s++;
    if(*s||v[3]>31||v[2]>100000)return 0;
    arcade_profile candidate={v[0],v[1],v[2],v[3]};
    if(checksum(&candidate)!=v[4])return 0;
    *p=candidate;return 1;
}
int profile_open(profile_io *io,const char *path,arcade_profile *p) {
    memset(io,0,sizeof(*io));memset(p,0,sizeof(*p));
    if(strlen(path)>=sizeof(io->path)){io->blocked=1;return -1;}
    strcpy(io->path,path);FILE *f=fopen(path,"rb");
    if(!f){if(errno==ENOENT)return 0;io->blocked=1;return -1;}
    int ok=read_profile(f,p);if(fclose(f))ok=0;
    if(!ok){memset(p,0,sizeof(*p));io->blocked=1;return -1;}
    io->saved=*p;return 1;
}
static int write_profile(const char *path,const arcade_profile *p) {
    char temp[600];
    if(snprintf(temp,sizeof(temp),"%s.tmp",path)>=(int)sizeof(temp))return 0;
    FILE *f=fopen(temp,"wb");if(!f)return 0;
    int ok=fprintf(f,"ARCADE2\n%u %u %u %u %u\n",p->puzzle_best,p->breaker_best,p->best_combo,p->badges,checksum(p))>0;
    if(fflush(f))ok=0;
#ifdef _WIN32
    if(_commit(_fileno(f)))ok=0;
#else
    if(fsync(fileno(f)))ok=0;
#endif
    if(fclose(f))ok=0;
    if(!ok){remove(temp);return 0;}
#ifdef _WIN32
    ok=MoveFileExA(temp,path,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;
#else
    ok=rename(temp,path)==0;
    if(ok) {
        char dir[512];strcpy(dir,path);char *slash=strrchr(dir,'/');
        if(!slash)strcpy(dir,".");else if(slash==dir)slash[1]=0;else *slash=0;
        int fd=open(dir,O_RDONLY|O_DIRECTORY);if(fd<0)ok=0;else {if(fsync(fd))ok=0;close(fd);}
    }
#endif
    if(!ok)remove(temp);
    return ok;
}
int profile_sync(profile_io *io,const arcade_profile *p,double dt,int force) {
    if(io->blocked)return 0;
    if(!memcmp(p,&io->saved,sizeof(*p))){io->pending_seconds=0;return 1;}
    if(isfinite(dt)&&dt>0)io->pending_seconds+=dt;
    if(!force&&io->pending_seconds<1)return 1;
    if(!write_profile(io->path,p)){io->blocked=1;return 0;}
    io->saved=*p;io->pending_seconds=0;return 1;
}
