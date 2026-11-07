/* Syntax-check shim only; constants/fields used by the real Linux wrapper. */
#ifndef HOST_INPUT_H
#define HOST_INPUT_H
#include <stdint.h>
struct input_event { int64_t time[2]; uint16_t type,code; int32_t value; };
struct input_absinfo { int32_t value,minimum,maximum,fuzz,flat,resolution; };
#define EV_SYN 0
#define EV_ABS 3
#define SYN_REPORT 0
#define SYN_DROPPED 3
#define ABS_MT_SLOT 0x2f
#define ABS_MT_POSITION_X 0x35
#define ABS_MT_POSITION_Y 0x36
#define ABS_MT_TRACKING_ID 0x39
#define EVIOCGABS(x) (x)
#define EVIOCGMTSLOTS(size) (0x10000u+(size))
#endif
