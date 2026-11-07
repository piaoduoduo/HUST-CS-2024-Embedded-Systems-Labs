#include "fixture.h"

static int saved_pixels[SCREEN_WIDTH * SCREEN_HEIGHT];
static uint32_t random_state = UINT32_C(0x20261008);

static int random_between(int low, int high)
{
    random_state = random_state * UINT32_C(1664525) + UINT32_C(1013904223);
    return low + (int)(random_state % (uint32_t)(high - low + 1));
}

static void test_rectangle(int x, int y, int width, int height)
{
    snprintf(case_label, sizeof(case_label), "rectangle %u (%d,%d,%d,%d)",
             tested_cases, x, y, width, height);
    reset_surfaces(0);
    fb_draw_rect(x, y, width, height, TEST_COLOR);
    int64_t right = (int64_t)x + width;
    int64_t bottom = (int64_t)y + height;
    for(int row = 0; row < SCREEN_HEIGHT; ++row) {
        for(int column = 0; column < SCREEN_WIDTH; ++column) {
            int inside = width > 0 && height > 0 &&
                         (int64_t)column >= x && (int64_t)column < right &&
                         (int64_t)row >= y && (int64_t)row < bottom;
            require(DRAW_BUF[row * SCREEN_WIDTH + column] ==
                    (inside ? TEST_COLOR : 0), "rectangle point-containment oracle");
        }
    }
    check_canaries();
    fb_update();
    check_front_matches_back();
    ++tested_cases;
}

static void test_line(int x1, int y1, int x2, int y2)
{
    snprintf(case_label, sizeof(case_label), "line %u (%d,%d)-(%d,%d)",
             tested_cases, x1, y1, x2, y2);
    reset_surfaces(0);
    fb_draw_line(x1, y1, x2, y2, TEST_COLOR);
    int64_t dx = (int64_t)x2 - x1;
    int64_t dy = (int64_t)y2 - y1;
    int steep = llabs(dy) > llabs(dx);
    int64_t major1 = steep ? y1 : x1, major2 = steep ? y2 : x2;
    int64_t minor1 = steep ? x1 : y1, minor2 = steep ? x2 : y2;
    int major_limit = steep ? SCREEN_HEIGHT : SCREEN_WIDTH;
    int minor_limit = steep ? SCREEN_WIDTH : SCREEN_HEIGHT;
    int counts[SCREEN_WIDTH] = {0};
    int count = 0;

    for(int row = 0; row < SCREEN_HEIGHT; ++row) {
        for(int column = 0; column < SCREEN_WIDTH; ++column) {
            int pixel = DRAW_BUF[row * SCREEN_WIDTH + column];
            if(pixel == 0) continue;
            require(pixel == TEST_COLOR, "line color");
            ++count;
            int major = steep ? row : column;
            int minor = steep ? column : row;
            ++counts[major];
            if(major1 == major2) {
                require(column == x1 && row == y1, "degenerate line is one pixel");
            } else {
                int64_t low = major1 < major2 ? major1 : major2;
                int64_t high = major1 > major2 ? major1 : major2;
                require(major >= low && major <= high, "pixel beyond endpoints");
                double parameter = ((double)major - major1) /
                                   ((double)major2 - major1);
                double ideal = minor1 + ((double)minor2 - minor1) * parameter;
                require(fabs(minor - ideal) <= 0.50001,
                        "line exceeds half-pixel geometric error");
            }
        }
    }
    if(major1 == major2) {
        int visible = x1 >= 0 && x1 < SCREEN_WIDTH &&
                      y1 >= 0 && y1 < SCREEN_HEIGHT;
        require(count == visible, "single-point count");
    } else {
        int64_t low = major1 < major2 ? major1 : major2;
        int64_t high = major1 > major2 ? major1 : major2;
        for(int major = 0; major < major_limit; ++major) {
            require(counts[major] <= 1, "more than one pixel per major coordinate");
            if(major < low || major > high) {
                require(counts[major] == 0, "major coordinate outside segment");
                continue;
            }
            double parameter = ((double)major - major1) /
                               ((double)major2 - major1);
            double ideal = minor1 + ((double)minor2 - minor1) * parameter;
            if(ideal >= 0 && ideal <= minor_limit - 1)
                require(counts[major] == 1, "gap on a visible line");
            if(ideal < -0.50001 || ideal > minor_limit - 0.49999)
                require(counts[major] == 0, "pixel outside clipping tolerance");
        }
    }
    check_canaries();
    memcpy(saved_pixels, DRAW_BUF, sizeof(saved_pixels));
    reset_surfaces(0);
    fb_draw_line(x2, y2, x1, y1, TEST_COLOR);
    require(memcmp(saved_pixels, DRAW_BUF, sizeof(saved_pixels)) == 0,
            "endpoint reversal changed rasterization");
    check_canaries();
    fb_update();
    check_front_matches_back();
    ++tested_cases;
}

static void test_golden_octants(void)
{
    const int points[6][2] = {{0,0},{1,0},{2,1},{3,1},{4,2},{5,2}};
    for(int transpose = 0; transpose < 2; ++transpose) {
        for(int sx = -1; sx <= 1; sx += 2) {
            for(int sy = -1; sy <= 1; sy += 2) {
                snprintf(case_label, sizeof(case_label), "golden octant %d %d %d",
                         transpose, sx, sy);
                reset_surfaces(0);
                memset(saved_pixels, 0, sizeof(saved_pixels));
                for(int i = 0; i < 6; ++i) {
                    int x = 20 + sx * points[i][transpose ? 1 : 0];
                    int y = 20 + sy * points[i][transpose ? 0 : 1];
                    saved_pixels[y * SCREEN_WIDTH + x] = TEST_COLOR;
                }
                int end_x = 20 + sx * (transpose ? 2 : 5);
                int end_y = 20 + sy * (transpose ? 5 : 2);
                fb_draw_line(20, 20, end_x, end_y, TEST_COLOR);
                require(memcmp(saved_pixels, DRAW_BUF, sizeof(saved_pixels)) == 0,
                        "golden pixel coordinates");
                fb_update();
                check_front_matches_back();
                ++tested_cases;
            }
        }
    }
}

static void test_pixel_and_double_buffer(void)
{
    snprintf(case_label, sizeof(case_label), "pixel clipping");
    reset_surfaces(0);
    fb_draw_pixel(-1, 0, TEST_COLOR);
    fb_draw_pixel(0, -1, TEST_COLOR);
    fb_draw_pixel(SCREEN_WIDTH, 0, TEST_COLOR);
    fb_draw_pixel(0, SCREEN_HEIGHT, TEST_COLOR);
    fb_draw_pixel(INT_MIN, INT_MAX, TEST_COLOR);
    fb_draw_pixel(0, 0, TEST_COLOR);
    fb_draw_pixel(SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1, TEST_COLOR);
    int count = 0;
    for(int i = 0; i < SCREEN_WIDTH * SCREEN_HEIGHT; ++i) {
        if(DRAW_BUF[i] == TEST_COLOR) ++count;
        else require(DRAW_BUF[i] == 0, "unexpected pixel color");
    }
    require(count == 2, "pixel clipping count");
    check_canaries();
    fb_update();
    check_front_matches_back();
    ++tested_cases;

    snprintf(case_label, sizeof(case_label), "deferred dirty-region refresh");
    reset_surfaces(CANARY);
    uint64_t before = front_hash();
    fb_draw_rect(10, 20, 3, 4, TEST_COLOR);
    require(front_hash() == before, "drawing changed front buffer before update");
    require(update_area.x1 == 10 && update_area.x2 == 13 &&
            update_area.y1 == 20 && update_area.y2 == 24, "dirty-region bounds");
    fb_update();
    for(int y = 0; y < SCREEN_HEIGHT; ++y)
        for(int x = 0; x < SCREEN_WIDTH; ++x) {
            int inside = x >= 10 && x < 13 && y >= 20 && y < 24;
            require(LCD_FB_BUF[y * PITCH_WORDS + x] ==
                    (inside ? TEST_COLOR : CANARY), "update copied unrelated region");
        }
    require(update_area.x2 == 0, "dirty region not reset");
    before = front_hash();
    fb_update();
    require(front_hash() == before, "empty update changed front buffer");
    check_canaries();
    ++tested_cases;

    snprintf(case_label, sizeof(case_label), "merged dirty regions");
    reset_surfaces(0);
    fb_draw_pixel(3, 4, TEST_COLOR);
    fb_draw_rect(20, 30, 2, 2, TEST_COLOR);
    require(update_area.x1 == 3 && update_area.x2 == 22 &&
            update_area.y1 == 4 && update_area.y2 == 32, "dirty-region union");
    fb_update();
    check_front_matches_back();
    ++tested_cases;
}

int main(void)
{
    test_pixel_and_double_buffer();
    printf("PASS: pixel clipping, deferred refresh, dirty-region union and padded stride\n");
    const int rectangles[][4] = {
        {0,0,SCREEN_WIDTH,SCREEN_HEIGHT},{0,0,1,1},{-5,-5,20,20},
        {SCREEN_WIDTH-5,SCREEN_HEIGHT-5,20,20},{-30,5,20,20},
        {SCREEN_WIDTH,5,20,20},{5,-30,20,20},{5,SCREEN_HEIGHT,20,20},
        {5,5,0,20},{5,5,20,0},{5,5,-1,20},{5,5,20,-1},
        {INT_MIN,INT_MIN,INT_MAX,INT_MAX},
        {-100,-100,INT_MAX,INT_MAX},{INT_MAX,INT_MAX,INT_MAX,INT_MAX},
        {INT_MIN,0,INT_MAX,100}
    };
    for(unsigned i = 0; i < sizeof(rectangles)/sizeof(rectangles[0]); ++i)
        test_rectangle(rectangles[i][0], rectangles[i][1],
                       rectangles[i][2], rectangles[i][3]);
    for(int i = 0; i < 120; ++i)
        test_rectangle(random_between(-50,SCREEN_WIDTH+50),
                       random_between(-50,SCREEN_HEIGHT+50),
                       random_between(-30,SCREEN_WIDTH+80),
                       random_between(-30,SCREEN_HEIGHT+80));
    printf("PASS: rectangle geometry, clipping, invalid sizes and integer extremes\n");

    test_golden_octants();
    const int lines[][4] = {
        {0,0,0,0},{-1,-1,-1,-1},{17,20,900,20},{20,17,20,500},
        {0,0,SCREEN_WIDTH-1,SCREEN_HEIGHT-1},
        {-5,-5,20,20},{-20,100,1100,100},{100,-20,100,700},
        {-20,-20,-1,-1},{1024,100,1100,500},
        {0,-1,1023,-1},{0,600,1023,600},
        {INT_MIN,123,INT_MAX,123},{456,INT_MIN,456,INT_MAX},
        {INT_MIN,INT_MIN,INT_MAX,INT_MAX},
        {INT_MIN,INT_MAX,INT_MAX,INT_MIN},
        {INT_MAX,INT_MAX,INT_MAX,INT_MAX}
    };
    for(unsigned i = 0; i < sizeof(lines)/sizeof(lines[0]); ++i)
        test_line(lines[i][0], lines[i][1], lines[i][2], lines[i][3]);
    for(int i = 0; i < 240; ++i)
        test_line(random_between(-80,SCREEN_WIDTH+80),
                  random_between(-80,SCREEN_HEIGHT+80),
                  random_between(-80,SCREEN_WIDTH+80),
                  random_between(-80,SCREEN_HEIGHT+80));
    printf("PASS: eight octants, geometric error, reversed endpoints and extreme clipping\n");
    printf("PASS: %u offline cases\n", tested_cases);
    free(front_storage);
    return 0;
}
