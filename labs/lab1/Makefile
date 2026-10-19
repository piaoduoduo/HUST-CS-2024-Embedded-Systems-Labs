# Standalone build for experiment 1; output follows the lecture's out directory.
# Native build on Orange Pi: make
# Cross build: make CC=/path/to/aarch64-none-linux-gnu-gcc
CC = gcc
CFLAGS = -O2 -Wall -Wextra -pedantic
TARGET = out/lab1

.PHONY: all run
all: $(TARGET)

$(TARGET): main.c Makefile
	mkdir -p out
	$(CC) $(CPPFLAGS) $(CFLAGS) main.c $(LDFLAGS) -o $(TARGET)

run: $(TARGET)
	$(TARGET)
