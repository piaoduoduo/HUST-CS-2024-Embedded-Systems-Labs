"""Isolated candidates; never modifies the accepted deployment packages."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess

ROOT = Path(__file__).resolve().parent
WS = ROOT.parent
BUILD = ROOT / 'build'
BUILD.mkdir(exist_ok=True)
COMMON = ROOT / 'common'
COMMON.mkdir(exist_ok=True)
TESTS = ROOT / 'tests'
TESTS.mkdir(exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--cc', required=True)
args = parser.parse_args()
cc = Path(args.cc)
env = dict(os.environ)
env['PATH'] = str(cc.parent) + os.pathsep + env.get('PATH', '')
original = (WS / 'lab3-prepared/common/graphic.c').read_text(encoding='utf-8')
candidate = original
old = '''    for(int64_t major = first; major <= last; ++major) {
        if(steep) {
            fb_draw_pixel((int)minor, (int)major, color);
        } else {
            fb_draw_pixel((int)major, (int)minor, color);
        }'''
new = '''    /* Candidate: same raster points, one dirty box for fully visible lines. */
    int inside = x1 >= 0 && x1 < SCREEN_WIDTH && x2 >= 0 && x2 < SCREEN_WIDTH
              && y1 >= 0 && y1 < SCREEN_HEIGHT && y2 >= 0 && y2 < SCREEN_HEIGHT;
    if(inside) {
        int left = x1 < x2 ? x1 : x2;
        int top = y1 < y2 ? y1 : y2;
        _begin_draw(left, top, abs(x2-x1)+1, abs(y2-y1)+1);
    }
    for(int64_t major = first; major <= last; ++major) {
        if(inside) {
            int x = (int)(steep ? minor : major);
            int y = (int)(steep ? major : minor);
            DRAW_BUF[y * SCREEN_WIDTH + x] = color;
        } else if(steep) {
            fb_draw_pixel((int)minor, (int)major, color);
        } else {
            fb_draw_pixel((int)major, (int)minor, color);
        }'''
assert candidate.count(old) == 1
candidate = candidate.replace(old, new)
oldblend = '    return (src * alpha + dst * (255-alpha) + 127) / 255;'
assert candidate.count(oldblend) == 1
candidate = candidate.replace(oldblend, '''    unsigned t = src * alpha + dst * (255-alpha) + 128;
    return (t + (t >> 8)) >> 8; /* Exact rounded /255 for this bounded domain. */''')
(COMMON / 'graphic.c').write_text(candidate, encoding='utf-8')
parallel = candidate.replace('    for(int row = 0; row < h; ++row) {', '''    /* Workers own disjoint destination rows; dirty box set before launch.
     * Implicit end barrier preserves immediate drawing and timing semantics. */
    #ifndef FB_PARALLEL_MIN_PIXELS
    #define FB_PARALLEL_MIN_PIXELS 65536
    #endif
    #ifdef _OPENMP
    #pragma omp parallel for schedule(static) if((size_t)w * h >= FB_PARALLEL_MIN_PIXELS)
    #endif
    for(int row = 0; row < h; ++row) {''')
assert parallel != candidate
(COMMON / 'graphic-openmp.c').write_text(parallel, encoding='utf-8')
shutil.copy2(WS / 'lab3-prepared/common/common.h', COMMON / 'common.h')
for name in ('fixture.h', 'test_lab2_regression.c', 'test_images.c', 'asset_adapter.c'):
    shutil.copy2(WS / 'labs3-5-prepared/tests' / name, TESTS / name)
image = (WS / 'lab3-prepared/common/image.c').read_text(encoding='utf-8')
memory = image[image.index('/*w, h maybe == 0*/'):image.index('/*================== read a jpeg image')]
(BUILD / 'image-memory-under-test.c').write_text('#include <limits.h>\n' + memory, encoding='utf-8')
logs = {}
variants = [('baseline', original), ('candidate', candidate)]
variants += [('openmp-'+str(threads), parallel) for threads in (1,2,4)]
for variant, source in variants:
    is_parallel = variant.startswith('openmp-')
    env['OMP_NUM_THREADS'] = variant.split('-')[-1] if is_parallel else '1'
    env['OMP_DYNAMIC'] = 'FALSE'
    globals_ = source[source.index('static int LCD_FB_FD;'):source.index('void fb_init(')]
    globals_ = globals_.replace('static int LCD_FB_FD;\n', '').replace(
        'static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];',
        'static struct { int before[GUARD_WORDS]; int pixels[SCREEN_WIDTH*SCREEN_HEIGHT]; int after[GUARD_WORDS]; } TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
    core = '#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n' + globals_ + source[source.index('static void _copy_area('):]
    (BUILD / 'graphics-under-test.c').write_text(core, encoding='utf-8')
    for test in ('test_lab2_regression', 'test_images'):
        exe = BUILD / (variant + '-' + test + '.exe')
        command = [str(cc), '-std=gnu11', '-O3', '-Wall', '-Wextra', '-Werror', '-static',
                   '-I', str(BUILD), '-I', str(COMMON), '-I', str(TESTS),
                   str(TESTS / (test + '.c')), str(TESTS / 'asset_adapter.c'), '-o', str(exe), '-lm']
        if is_parallel:
            command += ['-fopenmp', '-DFB_PARALLEL_MIN_PIXELS=1']
        compiled = subprocess.run(command, env=env, cwd=ROOT, capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError(compiled.stdout + compiled.stderr)
        result = subprocess.run([str(exe)], env=env, cwd=ROOT, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stdout + result.stderr
        logs[variant + '-' + test] = result.stdout + result.stderr
        print(variant, result.stdout.strip())
for n in range(65026):
    t = n + 128
    assert (n + 127) // 255 == (t + (t >> 8)) >> 8
report = {'baselineSha256': hashlib.sha256(original.encode()).hexdigest(),
          'candidateSha256': hashlib.sha256(candidate.encode()).hexdigest(),
          'roundedDivisionNumeratorsChecked': 65026,
          'logs': logs, 'hardwareValidated': False, 'armNativeBuildValidated': False,
          'openmpThreadsTested': [1,2,4], 'openmpTestPixelThreshold': 1,
          'openmpDeploymentPixelThreshold': 65536,
          'performanceMeasured': False, 'deploymentPackagesModified': False}
(ROOT / 'offline-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('PASS: 65026 exact rounded division cases; no board speed claim.')
