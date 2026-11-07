/* Board-native test: link image-fast.c + real FreeType/jpeg/png libraries.
 * The test accepts the actual course .ttc/.ttf font path as argv[1]. */
#include "fixture.h"
#include "test_v9_text_cases.h"
int main(int argc,char **argv)
{
    require(argc==2,"usage: test_v9_text_real path/to/course-font.ttc");
    font_init(argv[1]);require(fb_font_identity()!=NULL,"real FreeType font failed to load");
    for(int i=0;i<10;i++)text_test_v9(i,-1);
    text_null_batch_v9();
    printf("PASS: %u real FreeType ordered text batch cases (whole framebuffer, dirty, clipping, eviction, UTF8, source mutation)\n",tested_cases);
    free(front_storage);return 0;
}
