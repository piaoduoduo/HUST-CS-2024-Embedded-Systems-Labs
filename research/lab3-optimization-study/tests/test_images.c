#include "fixture.h"

static unsigned rng = 0x1037;
static unsigned random_byte(void) { rng = rng*1664525u+1013904223u; return rng>>24; }
static uint32_t oracle(uint32_t foreground, uint32_t background, unsigned alpha)
{
    if(!alpha) return background;
    uint32_t result = UINT32_C(0xff000000);
    for(unsigned channel = 0; channel < 3; ++channel) {
        unsigned shift = channel*8;
        double mixed = ((foreground>>shift)&255)*(alpha/255.0) +
                       ((background>>shift)&255)*(1-alpha/255.0);
        result |= (uint32_t)floor(mixed+0.5) << shift;
    }
    return result;
}

static void image_case(int type, int x, int y, int padding)
{
    snprintf(case_label, sizeof(case_label), "image type=%d at %d,%d padding=%d", type,x,y,padding);
    const int width=9, height=7, bytes=type==FB_COLOR_ALPHA_8 ? 1 : 4;
    fb_image *image = fb_new_image(type,width,height,width*bytes+padding);
    require(image != NULL, "image allocation");
    memset(image->content,0xa5,(size_t)image->line_byte*height);
    uint32_t background=UINT32_C(0xff316a9d), ink=UINT32_C(0xffe51891);
    reset_surfaces(0);
    fb_draw_rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT,(int)background);
    fb_update();
    for(int row=0;row<height;++row) for(int col=0;col<width;++col) {
        unsigned char *p=(unsigned char *)image->content+row*image->line_byte+col*bytes;
        if(bytes==1) p[0]=(unsigned char)(col==0 ? 0 : col==1 ? 255 : random_byte());
        else {
            p[0]=random_byte();p[1]=random_byte();p[2]=random_byte();
            p[3]=type==FB_COLOR_RGB_8880 ? 255 : col==0 ? 0 : col==1 ? 255 : random_byte();
        }
    }
    uint64_t front_before=front_hash();
    fb_draw_image(x,y,image,(int)ink);
    require(front_hash()==front_before, "image drawing must wait for fb_update");
    for(int row=0;row<SCREEN_HEIGHT;++row) for(int col=0;col<SCREEN_WIDTH;++col) {
        uint32_t expected=background;
        int64_t ix=(int64_t)col-x, iy=(int64_t)row-y;
        if(ix>=0 && ix<width && iy>=0 && iy<height) {
            unsigned char *p=(unsigned char *)image->content+iy*image->line_byte+ix*bytes;
            uint32_t foreground=bytes==1 ? ink : (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16;
            expected=oracle(foreground,background,type==FB_COLOR_RGB_8880 ? 255 : bytes==1 ? p[0] : p[3]);
        }
        require((uint32_t)DRAW_BUF[row*SCREEN_WIDTH+col]==expected,"image clipping/blending oracle");
    }
    check_canaries();fb_update();check_front_matches_back();
    fb_free_image(image);++tested_cases;
}

int main(void)
{
    const int positions[][2]={{0,0},{-4,-3},{1020,596},{-9,0},{1024,600},{INT_MIN,INT_MIN},{INT_MAX,INT_MAX}};
    for(int type=1;type<=3;++type) for(unsigned p=0;p<sizeof(positions)/sizeof(*positions);++p)
        for(int pad=0;pad<=5;pad+=5) image_case(type,positions[p][0],positions[p][1],pad);
    for(int type=1;type<=3;++type) for(int i=0;i<20;++i) image_case(type,10+i,20+i,i%4);
    snprintf(case_label,sizeof(case_label),"invalid images and allocation bounds");
    reset_surfaces(0);
    fb_draw_image(0,0,NULL,0);
    fb_image invalid={99,1,1,4,"abcd"};fb_draw_image(0,0,&invalid,0);
    invalid=(fb_image){FB_COLOR_RGBA_8888,9,2,1,"abcd"};fb_draw_image(0,0,&invalid,0);
    require(update_area.x2==0,"invalid image changed dirty region");
    require(fb_new_image(FB_COLOR_RGBA_8888,INT_MAX,1,0)==NULL,"overflowing image width");
    fb_image *tall=fb_new_image(FB_COLOR_ALPHA_8,2,20,3);
    fb_image *sub=fb_get_sub_image(tall,0,15,2,5);
    require(sub!=NULL && sub->content==tall->content+45,"subimage must use image height");
    fb_free_image(sub);
    require(fb_get_sub_image(tall,0,19,2,2)==NULL,"subimage exceeds height");
    fb_free_image(tall);
    fb_image *wide=fb_new_image(FB_COLOR_ALPHA_8,20,2,20);
    require(fb_get_sub_image(wide,0,2,1,1)==NULL,"wide image height check");fb_free_image(wide);
    check_canaries();++tested_cases;
    printf("PASS: %u image cases (three formats, alpha endpoints, clipping, padding, subimages)\n",tested_cases);
    free(front_storage);return 0;
}
