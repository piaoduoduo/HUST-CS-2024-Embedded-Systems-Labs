/* Prepared PNG/alpha snapshot creation and destruction are timed. */
/* EXPERIMENTAL explicit opaque batch API; execution remains INSIDE jpeg timer. */
/* Lab1 ~ Lab3测试程序 */

#include <stdio.h>
#include <time.h>
#include <string.h>

#include "../common/common.h"
#include "../common/batch_api.h"
#include "../common/prepared_api.h"

#define RED	FB_COLOR(255,0,0)
#define ORANGE	FB_COLOR(255,165,0)
#define YELLOW	FB_COLOR(255,255,0)
#define GREEN	FB_COLOR(0,255,0)
#define CYAN	FB_COLOR(0,127,255)
#define BLUE	FB_COLOR(0,0,255)
#define PURPLE	FB_COLOR(139,0,255)
#define WHITE   FB_COLOR(255,255,255)
#define BLACK   FB_COLOR(0,0,0)

int main(int argc, char *argv[])
{
	int row,column,i;
	fb_image *img1,*img2,*img3;

	fb_init("/dev/fb0");
	font_init("./font.ttc");

	int32_t start ,end, time_total = 0;
	int32_t time_pixel=0,time_rect=0,time_image=0,time_text=0,time_line=0;
	int32_t time[5] = {0,0,0,0,0};
	int color[9] = {RED,ORANGE,YELLOW,GREEN,CYAN,BLUE,PURPLE,WHITE,BLACK};

	fb_draw_rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT,BLACK);
	fb_update();
	printf("\n========== Start Test ===========\n");

//Lab2 test
	sleep(1);
	printf("\nLab2 test:\n");
	start = task_get_time();
	for(row=-5; row<605; row+=2) {
		for(column=-5; column<1029; column+=2) {
			fb_draw_pixel(column,row,color[0]);
		}
	}
	end = task_get_time();
	fb_update();
	time_pixel = end - start;
	time[0] = time_pixel;
	printf("draw pixel: %d ms\n",time_pixel);
	time_total += time_pixel;

	sleep(1);
	start = task_get_time();
	for(row=-15,i=0; row<300; row+=5){
		for(column=-15; column<1029; column+=5){
			fb_draw_rect(column,row,10,10,color[i]);
			i = (i+1) % 9;
		}
	}
	for(row=300,i=0; row<605; row+=5){
		fb_draw_rect(0,row,500,10,color[i]);
		i = (i+1) % 9;
	}
	for(column=500,i=0; column<1029; column+=5){
		fb_draw_rect(column,300,10,300,color[i]);
		i = (i+1) % 9;
	}
	end = task_get_time();
	fb_update();
	time_rect = end - start;
	time[1] = time_rect;
	printf("draw rect: %d ms\n",time_rect);
	time_total += time_rect;

	sleep(1);
	start = task_get_time();
	for(row=0;row<=400;row++){
		fb_draw_line(500-300,300-200+row,500+300,300+200-row,color[1]);
	}
	for(column=0;column<=400;column++){
		fb_draw_line(500-200+column,300-200,500+200-column,300+200,color[2]);
	}
	end = task_get_time();
	fb_update();
	time_line = end - start;
	time[2] = time_line;
	printf("draw line: %d ms\n", time_line);
	time_total += time_line;

//Lab3 test
	sleep(1);
	printf("\nLab3 test:\n");
	img1 = fb_read_jpeg_image("./test.jpg");
	img2 = fb_read_png_image("./test.png");
	img3 = fb_read_font_image("嵌",30,NULL);
	if(!img1 || !img2 || !img3) { fprintf(stderr,"Missing test image/font assets\n"); return EXIT_FAILURE; }
	start = task_get_time();
	fb_opaque_batch *batch = fb_opaque_batch_begin();
	if(!batch) return EXIT_FAILURE;
	fb_batch_stats batch_stats;
	for(row=-5; row<605; row+=100){
		for(column=-5; column<1029; column+=50){
			if(!fb_opaque_batch_add(batch,column,row,img1)) { fb_opaque_batch_end(batch,NULL); return EXIT_FAILURE; }
		}
	}
	fb_opaque_batch_end(batch,&batch_stats);
	end = task_get_time();
	fb_update();
	printf("    **jpeg:\t%d\n", end-start);
	printf("BATCH_API_EXPERIMENT=1 submitted_pixels=%llu copied_pixels=%llu row_checks=%llu interval_comparisons=%llu flushes=%llu\n",
	    (unsigned long long)batch_stats.submitted_pixels,(unsigned long long)batch_stats.copied_pixels,
	    (unsigned long long)batch_stats.row_command_checks,(unsigned long long)batch_stats.interval_comparisons,
	    (unsigned long long)batch_stats.flushes);
	time_image += (end - start);
	
	sleep(1);
	fb_draw_rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT,BLACK);
	start = task_get_time();
	fb_prepared_image *prepared_png=fb_prepare_image(img2);
	for(row=-5; row<605; row+=128){
		for(column=-5; column<1029; column+=50){
			if(prepared_png) fb_draw_prepared(column,row,prepared_png,0); else fb_draw_image(column,row,img2,0);
		}
	}
	fb_free_prepared(prepared_png);
	end = task_get_time();
	fb_update();
	printf("    **png:\t%d\n", end-start);
	time_image += (end - start);
	
	sleep(1);
	start = task_get_time();
	fb_prepared_image *prepared_font=fb_prepare_image(img3);
	for(row=-5,i=0; row<605; row+=40){
		for(column=-5; column<1029; column+=40){
			if(prepared_font) fb_draw_prepared(column,row,prepared_font,color[i]); else fb_draw_image(column,row,img3,color[i]);
			i = (i+1) % 9;
		}
	}
	fb_free_prepared(prepared_font);
	end = task_get_time();
	fb_update();
	printf("    **font:\t%d\n", end-start);
	time_image += (end - start);

	time[3] = time_image;
	printf("draw image: %d ms\n", time_image);
	time_total += time_image;
	fb_free_image(img1);
	fb_free_image(img2);
	fb_free_image(img3);

	sleep(1);
	fb_draw_rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT,WHITE);
	start = task_get_time();
	for(row=-5;row<605;row+=60){
		fb_draw_text(20,row,"嵌入式系统实验",40,color[3]);
		fb_draw_text(20,row+40,"Embedded System Experiment",20,color[8]);
	}
	end = task_get_time();
	fb_update();
	time_text = end - start;
	time[4] = time_text;
	printf("draw text: %d ms\n",time_text);
	time_total += time_text;

	printf("\nTotal time: %d ms\n\n", time_total);
	printf("=================================\n");

//print result
	sleep(1);
	fb_draw_rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT,WHITE);
	fb_draw_text(55,35,"嵌入式系统实验--测试",40,BLACK);
	for(row=50,i=0; i<8; i++){
		fb_draw_rect(50,row,524,5,BLACK);
		row += 52;
	}
	for(column=50,i=0; i<3; i++){
		fb_draw_rect(column,50,5,364,BLACK);
		column += 260;
	}
	fb_draw_text(155,90,"操作",30,RED);
	fb_draw_text(370,90,"时间（ms）",30,CYAN);
	fb_draw_text(135,142,"点pixel",30,RED);
	fb_draw_text(135,194,"矩形rect",30,RED);
	fb_draw_text(135,246,"线line",30,RED);
	fb_draw_text(135,298,"图像image",30,RED);
	fb_draw_text(135,350,"文本text",30,RED);
	fb_draw_text(135,402,"合计total",30,ORANGE);
	fb_draw_text(260,454,"华中科技大学",30,PURPLE);
	
	char str[32];
	for(i=0; i<5; i++){
		memset(str,0,sizeof(str));
		snprintf(str,sizeof(str),"%d",time[i]);
		fb_draw_text(370,90+52*(i+1),str,30,CYAN);
	}
	memset(str,0,sizeof(str));
	snprintf(str,sizeof(str),"%d",time_total);
	fb_draw_text(370,402,str,30,ORANGE);

	fb_update();
	return 0;
}

