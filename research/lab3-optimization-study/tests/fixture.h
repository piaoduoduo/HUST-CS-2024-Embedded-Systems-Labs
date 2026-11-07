#include "graphics-under-test.c"

#define PAD_WORDS 4
#define PITCH_WORDS (SCREEN_WIDTH + PAD_WORDS)
#define FRONT_WORDS (PITCH_WORDS * SCREEN_HEIGHT)
#define CANARY 0x13579bdf
#define TEST_COLOR 0x1234ab

int *front_storage;
unsigned tested_cases;
char case_label[128] = "initialization";

void require(int condition, const char *message)
{
    if(!condition) {
        fprintf(stderr, "FAIL [%s]: %s\n", case_label, message);
        exit(1);
    }
}

void reset_surfaces(int visible_color)
{
    require(sizeof(int) == 4, "framebuffer requires 32-bit int pixels");
    if(front_storage == NULL) {
        front_storage = malloc((FRONT_WORDS + 2 * GUARD_WORDS) * sizeof(int));
        require(front_storage != NULL, "front-buffer allocation");
    }
    for(int i = 0; i < FRONT_WORDS + 2 * GUARD_WORDS; ++i)
        front_storage[i] = CANARY;
    LCD_FB_BUF = front_storage + GUARD_WORDS;
    LCD_FB_LINELEN = PITCH_WORDS * sizeof(int);
    for(int y = 0; y < SCREEN_HEIGHT; ++y)
        for(int x = 0; x < SCREEN_WIDTH; ++x)
            LCD_FB_BUF[y * PITCH_WORDS + x] = visible_color;
    for(int i = 0; i < GUARD_WORDS; ++i) {
        TEST_BACK.before[i] = CANARY;
        TEST_BACK.after[i] = CANARY;
    }
    memset(DRAW_BUF, 0, sizeof(DRAW_BUF));
    AREA_SET_EMPTY(&update_area);
}

void check_canaries(void)
{
    for(int i = 0; i < GUARD_WORDS; ++i) {
        require(TEST_BACK.before[i] == CANARY, "write before back buffer");
        require(TEST_BACK.after[i] == CANARY, "write after back buffer");
        require(front_storage[i] == CANARY, "write before front buffer");
        require(front_storage[GUARD_WORDS + FRONT_WORDS + i] == CANARY,
                "write after front buffer");
    }
    for(int y = 0; y < SCREEN_HEIGHT; ++y)
        for(int x = SCREEN_WIDTH; x < PITCH_WORDS; ++x)
            require(LCD_FB_BUF[y * PITCH_WORDS + x] == CANARY,
                    "framebuffer row-padding was overwritten");
}

void check_front_matches_back(void)
{
    for(int y = 0; y < SCREEN_HEIGHT; ++y)
        for(int x = 0; x < SCREEN_WIDTH; ++x)
            require(LCD_FB_BUF[y * PITCH_WORDS + x] ==
                    DRAW_BUF[y * SCREEN_WIDTH + x], "refresh pixel mismatch");
    check_canaries();
}

uint64_t front_hash(void)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for(int i = 0; i < FRONT_WORDS; ++i) {
        hash ^= (uint32_t)LCD_FB_BUF[i];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

void write_preview_ppm(const char *path)
{
    FILE *file = fopen(path, "wb");
    require(file != NULL, "open preview file");
    fprintf(file, "P6\n%d %d\n255\n", SCREEN_WIDTH, SCREEN_HEIGHT);
    for(int y = 0; y < SCREEN_HEIGHT; ++y) {
        for(int x = 0; x < SCREEN_WIDTH; ++x) {
            uint32_t color = (uint32_t)LCD_FB_BUF[y * PITCH_WORDS + x];
            unsigned char rgb[3] = {
                (unsigned char)(color >> 16),
                (unsigned char)(color >> 8),
                (unsigned char)color
            };
            require(fwrite(rgb, 1, 3, file) == 3, "write preview pixels");
        }
    }
    require(fclose(file) == 0, "close preview file");
}
