#include "fixture.h"
static unsigned checks;
static uint32_t oracle(uint32_t s,uint32_t d,unsigned a)
{
    if(!a)return d;
    uint32_t out=0xff000000u;
    for(int c=0;c<3;c++)out|=((((s>>(8*c))&255)*a+((d>>(8*c))&255)*(255-a)+127)/255)<<(8*c);
    return out;
}
int main(void)
{
    for(unsigned s=0;s<256;s++)for(unsigned d=0;d<256;d++)for(unsigned a=0;a<256;a++) {
        uint32_t source=s|((255-s)<<8)|(((s*73+19)&255)<<16);
        uint32_t old=d|((255-d)<<8)|(((d*137+7)&255)<<16)|((s^d)<<24);
        unsigned char bytes[4]={(unsigned char)source,(unsigned char)(source>>8),(unsigned char)(source>>16),(unsigned char)a};
        uint32_t expected=oracle(source,old,a);
        require(fb_mix_pixel(old,bytes,a,0)==expected,"packed RGBA channel oracle");
        require(fb_mix_pixel(old,NULL,a,source)==expected,"packed alpha/ink oracle");checks+=2;
        if(a) {
            require(fb_product_pixel(old,s*a,((source>>8)&255)*a,((source>>16)&255)*a,255-a)==expected,"unrounded product channel oracle");checks++;
        }
    }
    /* Exercise vector loads, scalar tails, offset alignment and destination canaries. */
    uint16_t products[3*64];unsigned char inverse[64];fb_image image={0};
    image.pixel_w=64;image.pixel_h=1;
    fb_prepared_image prepared={0};prepared.image=&image;prepared.products=products;prepared.inverse=inverse;
    uint32_t dst[68],expected[68];
    for(int offset=0;offset<8;offset++)for(int width=0;width<=40;width++) {
        for(int i=0;i<64;i++) {
            unsigned alpha=1+(unsigned)(i*61+width*17)%254;inverse[i]=(unsigned char)(255-alpha);
            for(int c=0;c<3;c++)products[i+c*64]=(uint16_t)((unsigned)((i*53+c*71)&255)*alpha);
        }
        for(int i=0;i<68;i++)dst[i]=expected[i]=0x17395479u+(unsigned)i*37;
        for(int i=0;i<width;i++) {
            int pos=offset+i;uint32_t source=(unsigned)((pos*53)&255)|((unsigned)((pos*53+71)&255)<<8)|((unsigned)((pos*53+142)&255)<<16);
            expected[i+1]=oracle(source,expected[i+1],255-inverse[pos]);
        }
        fb_prepared_product_row(dst+1,&prepared,(size_t)offset,width);
        require(!memcmp(dst,expected,sizeof(dst)),"product vector/tail row oracle");checks++;
    }
    printf("PASS: %u packed/product oracle comparisons (rounding, channels, alpha, vector offsets/tails)\n",checks);
    return 0;
}
