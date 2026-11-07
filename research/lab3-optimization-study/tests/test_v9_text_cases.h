/* Whole-frame/dirty-region oracle shared by synthetic and real FreeType tests. */
#ifndef FB_TEST_SET_FONT
#define FB_TEST_SET_FONT(v) ((void)(v))
#endif
#ifndef FB_TEST_ALLOC_FAIL
#define FB_TEST_ALLOC_FAIL(v) ((void)(v))
#endif
struct text_test_command_v9 {int x,y,size,color,font;char text[320];};
static void text_test_v9(int kind,int fault)
{
    struct text_test_command_v9 commands[48];
    int count=kind==9?2:48;
    for(int i=0;i<count;i++) {
        struct text_test_command_v9 *c=&commands[i];
        c->x=100+(i%6)*9;c->y=120+(i%5)*3;c->size=30+(i%3)*10;
        c->color=(int)(0x01543210u+i*71717u);c->font=kind==3?1+i%3:1;
        snprintf(c->text,sizeof(c->text),"%c 嵌入式系统 %02d",'A'+i%26,i%16);
        if(kind==0) {c->size=40;strcpy(c->text,"床前明月光ABC g");}
        if(kind==1) {c->x=i%3?-20:SCREEN_WIDTH-12;c->y=i%2?3:SCREEN_HEIGHT+2;}
        if(kind==2) {c->size=(i%4==0)?0:(i%4==1)?-1:(i%4==2)?512:1;}
        if(kind==4) {memset(c->text,'a',sizeof(c->text)-1);c->text[sizeof(c->text)-1]=0;c->x=-200;}
        if(kind==5) {c->x=i%2?-2000:2000;c->y=i%3?-1000:1000;}
        if(kind==6)strcpy(c->text,i%2?"zzzz  ":"");
        if(kind==7) {c->size=2+i%120;c->x=SCREEN_WIDTH-20;c->y=SCREEN_HEIGHT-20;}
        if(kind==8) {strcpy(c->text,"abcdefghijklmnopqrstuvwxyz");c->x=i*35-200;c->y=i*17;}
        if(kind==9) {strcpy(c->text,"A嵌B");c->size=30;}
    }
    static int initial[SCREEN_WIDTH*SCREEN_HEIGHT],expected[SCREEN_WIDTH*SCREEN_HEIGHT];
    snprintf(case_label,sizeof(case_label),"text batch kind=%d allocation failure=%d",kind,fault);
    reset_surfaces(0);FB_TEST_ALLOC_FAIL(-1);fb_layout_cleanup();
    for(int i=0;i<SCREEN_WIDTH*SCREEN_HEIGHT;i++)initial[i]=DRAW_BUF[i]=(int)(0x13371234u+i*1664525u);
    for(int i=0;i<count;i++) {
        struct text_test_command_v9 *c=&commands[i];FB_TEST_SET_FONT(c->font);
        fb_draw_text(c->x,c->y,c->text,c->size,c->color);
    }
    memcpy(expected,DRAW_BUF,sizeof(expected));struct area dirty=update_area;
    memcpy(DRAW_BUF,initial,sizeof(initial));AREA_SET_EMPTY(&update_area);fb_layout_cleanup();
    FB_TEST_ALLOC_FAIL(fault);fb_text_batch *batch=fb_text_batch_begin();
    require(fb_text_batch_add(batch,0,0,NULL,30,0)==0,"NULL text should be no-op");
    require(fb_text_batch_add(batch,0,0,"",30,0)==0,"empty text should be no-op");
    for(int i=0;i<count;i++) {
        struct text_test_command_v9 *c=&commands[i];FB_TEST_SET_FONT(c->font);
        char *owned=malloc(strlen(c->text)+1);require(owned!=NULL,"test string allocation");strcpy(owned,c->text);
        fb_text_batch_add(batch,c->x,c->y,owned,c->size,c->color);
        memset(owned,'?',strlen(owned));free(owned); /* must not retain caller bytes */
        if(kind==3 || kind==8)fb_layout_cleanup(); /* strongest cache-eviction/UAF stress */
    }
    fb_text_batch_end(batch);FB_TEST_ALLOC_FAIL(-1);
    require(!memcmp(expected,DRAW_BUF,sizeof(expected)),"batch changed full-frame alpha/order/pixels");
    require(!memcmp(&dirty,&update_area,sizeof(dirty)),"batch changed dirty region");
    check_canaries();fb_update();check_canaries();fb_layout_cleanup();tested_cases++;
}
static void text_null_batch_v9(void)
{
    reset_surfaces(0);fb_text_batch_add(NULL,5,20,"A嵌",30,0x123456);fb_text_batch_end(NULL);
    check_canaries();tested_cases++;
}
