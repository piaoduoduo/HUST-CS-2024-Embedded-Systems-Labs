#include "../arcade/profile.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
    const char *path="test-results/profile-test.txt";remove(path);profile_io io;
    arcade_profile p;assert(profile_open(&io,path,&p)==0);
    p=(arcade_profile){1234,5678,9,31};assert(profile_sync(&io,&p,0,1));
    arcade_profile read;assert(profile_open(&io,path,&read)==1&&!memcmp(&p,&read,sizeof(p)));
    p.puzzle_best=4321;assert(profile_sync(&io,&p,0.5,0));
    profile_io other;assert(profile_open(&other,path,&read)==1&&read.puzzle_best==1234);
    assert(profile_sync(&io,&p,0.6,0));assert(profile_open(&other,path,&read)==1&&read.puzzle_best==4321);
    const char *bad[]={"ARCADE2\n1 2 3 4 5\n","ARCADE2\n-1 2 3 0 0\n","ARCADE2\n4294967296 2 3 0 0\n","broken","ARCADE2\n1 2 3"};
    for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);i++) {
        FILE *f=fopen(path,"wb");assert(f);fputs(bad[i],f);fclose(f);
        assert(profile_open(&io,path,&read)==-1&&io.blocked);assert(!profile_sync(&io,&p,10,1));
        char buf[128]={0};f=fopen(path,"rb");assert(f);
        size_t count=fread(buf,1,sizeof(buf)-1,f);assert(!ferror(f)&&count==strlen(bad[i]));
        assert(fclose(f)==0);assert(!strcmp(buf,bad[i]));
    }
    assert(profile_open(&io,"test-results/no-such-directory/records.txt",&read)==0);
    assert(!profile_sync(&io,&p,0,1)&&io.blocked);
    remove(path);puts("PASS: actual host file round-trip, atomic replacement, delayed writes, malformed/overflow/truncated checksum rejection, corrupt file preserved, I/O failure");return 0;
}
