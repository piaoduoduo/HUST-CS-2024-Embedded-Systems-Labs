#include "fixture.h"
#include "batch_api.h"
static unsigned seed=0x1037;
static unsigned random_u(void){seed=seed*1664525u+1013904223u;return seed;}
struct command {int x,y;fb_image *image;};
static uint64_t clipped_area(const struct command *c)
{
    int64_t l=c->x,t=c->y,r=l+c->image->pixel_w,b=t+c->image->pixel_h;
    if(l<0)l=0;
    if(t<0)t=0;
    if(r>SCREEN_WIDTH)r=SCREEN_WIDTH;
    if(b>SCREEN_HEIGHT)b=SCREEN_HEIGHT;
    return r>l && b>t?(uint64_t)(r-l)*(b-t):0;
}
static fb_batch_stats compare(struct command *commands,int count)
{
    static int initial[SCREEN_WIDTH*SCREEN_HEIGHT],expected[SCREEN_WIDTH*SCREEN_HEIGHT];
    reset_surfaces(0);
    for(int i=0;i<SCREEN_WIDTH*SCREEN_HEIGHT;i++)initial[i]=DRAW_BUF[i]=(int)random_u();
    _begin_draw(0,0,SCREEN_WIDTH,SCREEN_HEIGHT);fb_update();
    uint64_t submitted=0;
    for(int i=0;i<count;i++){
        fb_draw_image(commands[i].x,commands[i].y,commands[i].image,0);
        submitted+=clipped_area(&commands[i]);
    }
    memcpy(expected,DRAW_BUF,sizeof(expected));
    struct area expected_area=update_area;
    memcpy(DRAW_BUF,initial,sizeof(initial));AREA_SET_EMPTY(&update_area);
    uint64_t front_before=front_hash();
    fb_opaque_batch *batch=fb_opaque_batch_begin();require(batch!=NULL,"batch allocation");
    require(!fb_opaque_batch_add(NULL,0,0,commands[0].image),"null batch rejection");
    require(!fb_opaque_batch_add(batch,0,0,NULL),"null image rejection");
    fb_image invalid={FB_COLOR_RGBA_8888,1,1,4,"xxxx"};
    require(!fb_opaque_batch_add(batch,0,0,&invalid),"transparent image rejected");
    invalid=(fb_image){FB_COLOR_RGB_8880,2,1,4,"xxxx"};
    require(!fb_opaque_batch_add(batch,0,0,&invalid),"invalid stride rejected");
    for(int i=0;i<count;i++)require(fb_opaque_batch_add(batch,commands[i].x,commands[i].y,commands[i].image),"valid command accepted");
    fb_batch_stats stats;fb_opaque_batch_end(batch,&stats);
    require(stats.accepted_commands==(unsigned)count,"command counter");
    require(stats.submitted_pixels==submitted,"submitted area counter");
    require(stats.copied_pixels<=submitted,"copy count never exceeds submitted area");
    require(!memcmp(expected,DRAW_BUF,sizeof(expected)),"batch final pixels differ from immediate drawing");
    require(!memcmp(&expected_area,&update_area,sizeof(expected_area)),"dirty bounding box differs");
    require(front_hash()==front_before,"batch must not write front buffer");
    check_canaries();fb_update();check_front_matches_back();tested_cases++;
    return stats;
}
int main(int argc,char **argv)
{
    fb_image *images[4];
    const int widths[]={600,37,1,1024},heights[]={400,19,600,600};
    for(int k=0;k<4;k++){
        images[k]=fb_new_image(FB_COLOR_RGB_8880,widths[k],heights[k],widths[k]*4+5);
        require(images[k]!=NULL,"image allocation");
        for(size_t i=0;i<(size_t)images[k]->line_byte*heights[k];i++)images[k]->content[i]=(char)(random_u()>>24);
    }
    if(argc>1) {
        fb_free_image(images[0]);images[0]=fb_read_jpeg_image(argv[1]);
        require(images[0] && images[0]->pixel_w==600 && images[0]->pixel_h==400,"course JPEG decode and dimensions");
    }
    struct command commands[600];int count=0;
    for(int y=-5;y<605;y+=100)for(int x=-5;x<1029;x+=50)commands[count++]=(struct command){x,y,images[0]};
    fb_batch_stats course=compare(commands,count);
    require(course.submitted_pixels==UINT64_C(16413045),"course workload count");
    #if FB_BATCH_CAPACITY >= 147 && !defined(FB_DISABLE_STATS)
    require(course.copied_pixels==UINT64_C(614400),"course batch writes each visible pixel once");
    #endif
    printf("COURSE submitted_pixels=%llu copied_pixels=%llu row_checks=%llu interval_comparisons=%llu spans=%llu flushes=%llu\n",
        (unsigned long long)course.submitted_pixels,(unsigned long long)course.copied_pixels,
        (unsigned long long)course.row_command_checks,(unsigned long long)course.interval_comparisons,
        (unsigned long long)course.copied_spans,(unsigned long long)course.flushes);
    for(int trial=0;trial<65;trial++){
        count=1+(int)(random_u()%420);
        for(int i=0;i<count;i++)commands[i]=(struct command){(int)(random_u()%1400)-200,(int)(random_u()%900)-150,images[random_u()%4]};
        snprintf(case_label,sizeof(case_label),"random batch %d with %d commands",trial,count);compare(commands,count);
    }
    for(int i=0;i<512;i++)commands[i]=(struct command){i*2,0,images[2]};
    compare(commands,512); /* Many disjoint covered intervals and queue spill. */
    commands[512]=(struct command){0,0,images[3]};compare(commands,513);
    commands[0]=(struct command){INT_MIN,INT_MIN,images[0]};
    commands[1]=(struct command){INT_MAX,INT_MAX,images[0]};compare(commands,2);
    fb_opaque_batch *empty=fb_opaque_batch_begin();fb_batch_stats stats;
    fb_opaque_batch_end(empty,&stats);require(!stats.copied_pixels && !stats.flushes,"empty batch");
    fb_opaque_batch_end(NULL,&stats);require(!stats.accepted_commands,"null batch end");
    for(int i=0;i<4;i++)fb_free_image(images[i]);
    printf("PASS: %u opaque-batch full-frame comparisons (random ordering, clipping, padding, disjoint spans, queue spill)\n",tested_cases);
    free(front_storage);return 0;
}
