/* Windows mouse simulator, not real framebuffer/touch/ARM validation. */
#include <windows.h>
#include <windowsx.h>
#include <shellapi.h>
#include "fixture.h"
#include "../arcade/app.h"
#include "../lab6_gomoku/app.h"
static arcade_app arcade;
static gm_app gomoku;
static int in_gomoku,held;
static ULONGLONG last;
static int pixels[1024*600];
static profile_io records;
static HANDLE instance_lock;
static int self_test;
static void refresh(HWND window) {
    if(in_gomoku) {gm_render(&gomoku);gomoku.dirty=0;}
    else {arcade_render(&arcade);arcade.dirty=0;}
    check_front_matches_back();
    for(int y=0;y<600;y++)memcpy(pixels+y*1024,LCD_FB_BUF+y*PITCH_WORDS,4096);
    InvalidateRect(window,NULL,FALSE);
}
static void touch(HWND window,int type,int x,int y) {
    if(in_gomoku){gm_app_set_time(&gomoku,GetTickCount64());gm_app_touch(&gomoku,type,x,y,0);}
    else arcade_touch(&arcade,type,x,y,0);
    refresh(window);
}
static LRESULT CALLBACK procedure(HWND w,UINT msg,WPARAM wp,LPARAM lp) {
    switch(msg) {
    case WM_LBUTTONDOWN:held=1;SetCapture(w);touch(w,1,GET_X_LPARAM(lp),GET_Y_LPARAM(lp));return 0;
    case WM_MOUSEMOVE:if(held)touch(w,2,GET_X_LPARAM(lp),GET_Y_LPARAM(lp));return 0;
    case WM_LBUTTONUP:if(held){held=0;ReleaseCapture();touch(w,3,GET_X_LPARAM(lp),GET_Y_LPARAM(lp));}return 0;
    case WM_CAPTURECHANGED:
        if(held){held=0;if(in_gomoku)gm_app_touch(&gomoku,3,-1,-1,0);else {arcade.owner=-1;arcade.breaker.paused=1;}}
        return 0;
    case WM_KEYDOWN:
        if(wp==VK_ESCAPE){in_gomoku=0;arcade.mode=0;arcade.owner=-1;held=0;ReleaseCapture();refresh(w);}
        return 0;
    case WM_ACTIVATEAPP:
        if(!wp&&!self_test&&!in_gomoku&&arcade.mode==2){arcade.breaker.paused=1;arcade.dirty=1;}
        return 0;
    case WM_TIMER: {
        ULONGLONG now=GetTickCount64();double dt=(now-last)/1000.0;last=now;
        if(arcade.quit){DestroyWindow(w);return 0;}
        if(arcade.launch_gomoku){
            arcade.launch_gomoku=0;in_gomoku=1;gm_app_init(&gomoku,1);
            gomoku.save_status=GM_SAVE_PAUSED;gm_app_set_time(&gomoku,now);refresh(w);
        }
        if(in_gomoku){
            gm_app_set_time(&gomoku,now);gm_app_tick(&gomoku);
            if(gomoku.quit){in_gomoku=0;arcade.dirty=1;}
            if(gomoku.dirty||arcade.dirty)refresh(w);
        } else {arcade_tick(&arcade,dt);if(arcade.dirty)refresh(w);}
        if(!profile_sync(&records,&arcade.profile,dt,0)&&arcade.records_ok){arcade.records_ok=0;refresh(w);}
        return 0;
    }
    case WM_PAINT: {
        PAINTSTRUCT ps;HDC dc=BeginPaint(w,&ps);BITMAPINFO info={0};
        info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);info.bmiHeader.biWidth=1024;
        info.bmiHeader.biHeight=-600;info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=32;
        info.bmiHeader.biCompression=BI_RGB;
        SetDIBitsToDevice(dc,0,0,1024,600,0,0,0,600,pixels,&info,DIB_RGB_COLORS);
        EndPaint(w,&ps);return 0;
    }
    case WM_ERASEBKGND:return 1;
    case WM_DESTROY:
        arcade_collect(&arcade);profile_sync(&records,&arcade.profile,0,1);
        KillTimer(w,1);PostQuitMessage(0);return 0;
    }
    return DefWindowProc(w,msg,wp,lp);
}
static void click(HWND w,int x,int y) {
    SendMessage(w,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(x,y));
    SendMessage(w,WM_LBUTTONUP,0,MAKELPARAM(x,y));
}
static void window_test(HWND w) {
    fprintf(stderr,"window-test: start\n");fflush(stderr);
    click(w,200,250);require(arcade.mode==1,"2048 menu click");
    arcade.puzzle=(puzzle){.cell={2,2,4},.rng=1};puzzle before=arcade.puzzle;
    SendMessage(w,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(450,200));
    SendMessage(w,WM_MOUSEMOVE,MK_LBUTTON,MAKELPARAM(250,200));
    SendMessage(w,WM_LBUTTONUP,0,MAKELPARAM(250,200));
    require(arcade.can_undo,"window swipe");click(w,800,300);
    require(!memcmp(&before,&arcade.puzzle,sizeof(before)),"window undo");
    click(w,800,390);require(arcade.hint>=0,"window hint");
    fprintf(stderr,"window-test: 2048 complete\n");fflush(stderr);
    click(w,800,120);click(w,200,350);require(arcade.mode==2,"breakout menu click");
    click(w,400,400);require(arcade.breaker.launched,"window launch");
    click(w,800,300);require(arcade.breaker.paused,"window pause");
    SendMessage(w,WM_KEYDOWN,VK_ESCAPE,0);require(!arcade.mode,"escape menu");
    fprintf(stderr,"window-test: breakout complete\n");fflush(stderr);
    click(w,200,150);SendMessage(w,WM_TIMER,1,0);require(in_gomoku,"gomoku handoff in simulator");
    click(w,GM_BOARD_X+7*GM_CELL,GM_BOARD_Y+7*GM_CELL);
    require(gomoku.game.count==1,"gomoku placement via window");
    for(int i=0;i<100&&gomoku.game.count==1;i++)SendMessage(w,WM_TIMER,1,0);
    require(gomoku.game.count==2,"gomoku AI response via window");
    fprintf(stderr,"window-test: gomoku complete\n");fflush(stderr);
    SendMessage(w,WM_KEYDOWN,VK_ESCAPE,0);require(!in_gomoku&&!arcade.mode,"gomoku exit");
    puts("PASS: hidden Win32 window events: menus, swipe, undo, hint, launch, pause, escape, gomoku AI handoff");
    DestroyWindow(w);
    fprintf(stderr,"window-test: destroyed\n");fflush(stderr);
}
int WINAPI WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR command,int show) {
    (void)previous;(void)command;
    int argc=0;LPWSTR *argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    self_test=argv&&argc==2&&!wcscmp(argv[1],L"--self-test");
    if(argv)LocalFree(argv);
    if(self_test){fprintf(stderr,"simulator: scripted window test\n");fflush(stderr);}
    SetProcessDPIAware();
    instance_lock=CreateMutexA(NULL,TRUE,"Local\\OrangePiArcadeV2");
    if(!instance_lock||GetLastError()==ERROR_ALREADY_EXISTS)return 1;
    reset_surfaces(0);arcade_init(&arcade,(unsigned)GetTickCount64());
    if(profile_open(&records,self_test?"./test-results/window-test-records.txt":"./arcade-records-v2-simulator.txt",&arcade.profile)<0)arcade.records_ok=0;
    WNDCLASS wc={0};wc.lpfnWndProc=procedure;wc.hInstance=instance;
    wc.lpszClassName="OrangePiArcadeSimulator";wc.hCursor=LoadCursor(NULL,IDC_ARROW);
    if(!RegisterClass(&wc))return 1;
    DWORD style=WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX;
    RECT rect={0,0,1024,600};AdjustWindowRect(&rect,style,FALSE);
    HWND w=CreateWindow(wc.lpszClassName,"OrangePi Arcade v2 - HOST SIMULATION - Mouse: touch / ESC: menu / records saved",style,
        CW_USEDEFAULT,CW_USEDEFAULT,rect.right-rect.left,rect.bottom-rect.top,NULL,NULL,instance,NULL);
    if(!w)return 1;
    refresh(w);if(!self_test)ShowWindow(w,show);last=GetTickCount64();SetTimer(w,1,20,NULL);
    if(self_test)window_test(w);
    MSG msg;while(GetMessage(&msg,NULL,0,0)>0){TranslateMessage(&msg);DispatchMessage(&msg);}
    CloseHandle(instance_lock);free(front_storage);return 0;
}
