#include <stdint.h>
#include <stddef.h>
uint64_t observe_surface(const int *p,size_t count)
{
    uint64_t hash=UINT64_C(1469598103934665603);
    for(size_t i=0;i<count;i++){hash^=(uint32_t)p[i];hash*=UINT64_C(1099511628211);}
    return hash;
}
