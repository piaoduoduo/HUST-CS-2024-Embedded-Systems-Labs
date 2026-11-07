#include "fixture.h"

static uint32_t random_state=0x10372026u;
static int expected[SCREEN_WIDTH*SCREEN_HEIGHT];
static struct area expected_area;
static unsigned calls,valid_calls;
static uint32_t next_random(void){random_state=random_state*1664525u+1013904223u;return random_state;}

static void reset_case(int background)
{
    reset_surfaces(background);
    memset(expected,0,sizeof(expected));expected_area=update_area;
}
static void oracle_pixel(int x,int y,int color)
{
    if((int64_t)x<0 || (int64_t)y<0 || x>=SCREEN_WIDTH || y>=SCREEN_HEIGHT)return;
    expected[y*SCREEN_WIDTH+x]=color;
    if(x<expected_area.x1)expected_area.x1=x;
    if(x+1>expected_area.x2)expected_area.x2=x+1;
    if(y<expected_area.y1)expected_area.y1=y;
    if(y+1>expected_area.y2)expected_area.y2=y+1;
}
static void checked_pixel(int x,int y,int color)
{
    oracle_pixel(x,y,color);fb_draw_pixel(x,y,color);calls++;
    if((unsigned)x<SCREEN_WIDTH && (unsigned)y<SCREEN_HEIGHT) {
        valid_calls++;require(DRAW_BUF[y*SCREEN_WIDTH+x]==color,"immediate pixel visibility");
    }
    require(!memcmp(&update_area,&expected_area,sizeof(expected_area)),"immediate exact dirty box");
}
static void checkpoint(void)
{
    require(!memcmp(DRAW_BUF,expected,sizeof(expected)),"complete framebuffer pixel oracle");
    check_canaries();tested_cases++;
}
static void checked_update(void)
{
    /* Front padding and pixels outside the dirty box must stay untouched. */
    static int prior[SCREEN_WIDTH*SCREEN_HEIGHT];
    for(int y=0;y<SCREEN_HEIGHT;y++)for(int x=0;x<SCREEN_WIDTH;x++)prior[y*SCREEN_WIDTH+x]=LCD_FB_BUF[y*PITCH_WORDS+x];
    struct area dirty=expected_area;fb_update();AREA_SET_EMPTY(&expected_area);
    require(!memcmp(&update_area,&expected_area,sizeof(expected_area)),"update clears dirty box");
    for(int y=0;y<SCREEN_HEIGHT;y++)for(int x=0;x<SCREEN_WIDTH;x++) {
        int inside=x>=dirty.x1 && x<dirty.x2 && y>=dirty.y1 && y<dirty.y2;
        require(LCD_FB_BUF[y*PITCH_WORDS+x]==(inside?expected[y*SCREEN_WIDTH+x]:prior[y*SCREEN_WIDTH+x]),"exact partial refresh");
    }
    check_canaries();tested_cases++;
}
static void checked_rect(int x,int y,int w,int h,int color)
{
    fb_draw_rect(x,y,w,h,color);
    for(int row=0;row<SCREEN_HEIGHT;row++)for(int col=0;col<SCREEN_WIDTH;col++)
        if(w>0 && h>0 && (int64_t)col>=x && col<(int64_t)x+w && (int64_t)row>=y && row<(int64_t)y+h)oracle_pixel(col,row,color);
    require(!memcmp(&update_area,&expected_area,sizeof(expected_area)),"pixel interleaved with other draw dirty");
}
int main(void)
{
    const int coordinates[]={INT_MIN,-1025,-1,0,1,599,600,1023,1024,INT_MAX};
    for(unsigned a=0;a<sizeof(coordinates)/sizeof(*coordinates);a++)for(unsigned b=0;b<sizeof(coordinates)/sizeof(*coordinates);b++) {
        reset_case(CANARY);checked_pixel(coordinates[a],coordinates[b],(int)next_random());checkpoint();checked_update();
    }
    /* Repeat after constructor-style zero state, not just AREA_SET_EMPTY. */
    reset_case(CANARY);update_area=(struct area){0,0,0,0};expected_area=update_area;
    checked_pixel(0,0,0);checked_pixel(1023,599,(int)0xff123456u);checkpoint();checked_update();
    reset_case(CANARY);
    for(int y=-5;y<605;y+=2)for(int x=-5;x<1029;x+=2)checked_pixel(x,y,(int)0xff800001u);
    checkpoint();checked_update();
    for(int test=0;test<64;test++) {
        reset_case(CANARY);
        if(test&1)checked_rect(100,80,500,300,(int)0xaa123456u);
        for(int i=0;i<512;i++) {
            int x=(int)(next_random()%1400)-200,y=(int)(next_random()%900)-150;
            if(i%17==0){x=(int)next_random();y=(int)next_random();}
            checked_pixel(x,y,(int)next_random());
            if(i==128 || i==384) {checkpoint();checked_update();}
            if(i==256)checked_rect(-3,20,70,60,(int)next_random());
        }
        checkpoint();checked_update();
    }
    /* Repeated same point and points inside an existing rectangle. */
    reset_case(CANARY);checked_rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT,0);
    for(int i=0;i<4096;i++)checked_pixel(513,299,(int)next_random());
    checkpoint();checked_update();
    printf("PASS: %u checkpoints, %u point calls (%u visible); immediate pixels/dirty, partial refresh, interleaved rectangles, extremes, canaries\n",tested_cases,calls,valid_calls);
    free(front_storage);return 0;
}
