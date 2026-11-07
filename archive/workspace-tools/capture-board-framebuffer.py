"""Read the visible 32-bit BGR framebuffer and save a PPM without changing it."""
import array
import fcntl
import os
import struct
import sys

fd = os.open('/dev/fb0', os.O_RDONLY)
try:
    var = array.array('I', [0] * 40)
    fix = bytearray(80)
    fcntl.ioctl(fd, 0x4600, var, True)
    fcntl.ioctl(fd, 0x4602, fix, True)
    width, height, _, _, xoffset, yoffset, bpp = var[:7]
    # fb_fix_screeninfo on this verified Linux aarch64 board: line_length at 48.
    stride = struct.unpack_from('I', fix, 48)[0]
    assert bpp == 32 and var[8:16:3].tolist() == [16, 8, 0]
    assert width <= 4096 and height <= 4096 and stride >= (width + xoffset) * 4
    with open(sys.argv[1], 'wb') as output:
        output.write(f'P6\n{width} {height}\n255\n'.encode())
        for row in range(height):
            bgra = os.pread(fd, width * 4, (row + yoffset) * stride + xoffset * 4)
            assert len(bgra) == width * 4
            rgb = bytearray(width * 3)
            rgb[0::3] = bgra[2::4]
            rgb[1::3] = bgra[1::4]
            rgb[2::3] = bgra[0::4]
            output.write(rgb)
    print(f'Saved actual framebuffer: {width}x{height}, stride={stride}, {sys.argv[1]}')
finally:
    os.close(fd)
