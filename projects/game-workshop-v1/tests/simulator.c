/* Windows mouse simulator, not real framebuffer/touch/ARM validation. */
#include <windows.h>
#include <windowsx.h>
#include "fixture.h"
#include "../arcade/app.h"
#include "../lab6_gomoku/app.h"
static arcade_app arcade;
static gm_app gomoku;
static int in_gomoku,held;
static ULONGLONG last;
static int pixels[1024*600];
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
    case WM_DESTROY:KillTimer(w,1);PostQuitMessage(0);return 0;
    }
    return DefWindowProc(w,msg,wp,lp);
}
int WINAPI WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR command,int show) {
    (void)previous;(void)command;
    reset_surfaces(0);arcade_init(&arcade,(unsigned)GetTickCount64());
    WNDCLASS wc={0};wc.lpfnWndProc=procedure;wc.hInstance=instance;
    wc.lpszClassName="OrangePiArcadeSimulator";wc.hCursor=LoadCursor(NULL,IDC_ARROW);
    if(!RegisterClass(&wc))return 1;
    DWORD style=WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX;
    RECT rect={0,0,1024,600};AdjustWindowRect(&rect,style,FALSE);
    HWND w=CreateWindow(wc.lpszClassName,"OrangePi Arcade - HOST SIMULATION - Mouse: touch / ESC: menu / no save",style,
        CW_USEDEFAULT,CW_USEDEFAULT,rect.right-rect.left,rect.bottom-rect.top,NULL,NULL,instance,NULL);
    if(!w)return 1;
    refresh(w);ShowWindow(w,show);last=GetTickCount64();SetTimer(w,1,20,NULL);
    MSG msg;while(GetMessage(&msg,NULL,0,0)>0){TranslateMessage(&msg);DispatchMessage(&msg);}
    free(front_storage);return 0;
}
