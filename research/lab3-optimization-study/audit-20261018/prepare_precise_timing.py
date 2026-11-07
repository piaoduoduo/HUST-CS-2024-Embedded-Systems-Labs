"""Generate a separate, synchronous high-resolution course diagnostic.

The original source is never edited. Compile the generated main instead of the
original main with exactly the same remaining sources/flags/assets. Diagnostic
numbers must not be silently substituted for the unchanged course score.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

PRELUDE = r'''
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#ifndef LAB3_DIAG_CLOCK_READ
#define LAB3_DIAG_CLOCK_READ clock_gettime
#endif
static uint64_t lab3_diag_times[14];
static unsigned lab3_diag_count;
static int32_t lab3_diag_clock(void)
{
    struct timespec ts;
    if (LAB3_DIAG_CLOCK_READ(CLOCK_MONOTONIC, &ts) != 0) {
        perror("diagnostic clock_gettime"); exit(EXIT_FAILURE);
    }
    uint64_t ns = (uint64_t)ts.tv_sec * UINT64_C(1000000000) + (uint64_t)ts.tv_nsec;
    if (lab3_diag_count >= 14) {
        fprintf(stderr,"Unexpected diagnostic timestamp count\n"); exit(EXIT_FAILURE);
    }
    lab3_diag_times[lab3_diag_count++] = ns;
    return (int32_t)(uint32_t)(ns / UINT64_C(1000000));
}
'''

SUFFIX = r'''
int main(int argc, char **argv)
{
    int rc = lab3_diag_course_main(argc, argv);
    if (rc != 0) return rc;
    if (lab3_diag_count != 14) {
        fprintf(stderr,"Incomplete diagnostic timestamps: %u\n", lab3_diag_count);
        return EXIT_FAILURE;
    }
    const char *names[7] = {"pixel","rect","line","jpg","png","font","text"};
    uint64_t total = 0;
    for (unsigned i = 0; i < 7; ++i) {
        uint64_t a = lab3_diag_times[i*2], b = lab3_diag_times[i*2+1];
        if (b < a) return EXIT_FAILURE;
        uint64_t elapsed = b-a;
        total += elapsed;
        printf("DIAGNOSTIC_STAGE_NS %s %" PRIu64 "\n", names[i], elapsed);
    }
    printf("DIAGNOSTIC_TOTAL_NS %" PRIu64 "\n", total);
    printf("DIAGNOSTIC_ONLY=1 includes_flush=0 includes_decode=0 includes_sleep=0\n");
    return rc;
}
'''


def generate(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or destination.exists():
        raise ValueError('Choose a new diagnostic output path; existing files are preserved')
    original = source.read_bytes()
    body = original.decode('utf-8-sig')
    body, count = re.subn(r'\btask_get_time\s*\(\s*\)', 'lab3_diag_clock()', body)
    if count != 14:
        raise ValueError('Expected exactly fourteen course timing calls, got %d' % count)
    body, count = re.subn(r'\bint\s+main\s*\(', 'static int lab3_diag_course_main(', body)
    if count != 1:
        raise ValueError('Expected exactly one int main definition')
    # The generated source can live outside test/. Resolve only observed quoted
    # local includes; no remote downloads or inferred project source files.
    def include(match):
        path = (source.parent / match.group(1)).resolve(strict=True)
        if '"' in str(path):
            raise ValueError('Unsupported quote in include path')
        return '#include "' + path.as_posix() + '"'
    body = re.sub(r'^\s*#include\s+"([^"\n]+)"\s*$', include, body, flags=re.M)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(PRELUDE + '\n' + body + '\n' + SUFFIX, encoding='utf-8')
    assert source.read_bytes() == original
    metadata = {
        'source': str(source), 'sourceSHA256': hashlib.sha256(original).hexdigest(),
        'generated': str(destination), 'generatedSHA256': hashlib.sha256(destination.read_bytes()).hexdigest(),
        'originalSourceUnchanged': True, 'timingSites': 14,
        'clock': 'CLOCK_MONOTONIC', 'resolutionUnit': 'nanoseconds, not a guarantee of clock precision',
        'stageWorkUnchanged': True, 'timingInstrumentationChanged': True,
        'hardwareValidated': False, 'performanceMeasured': False,
        'scope': 'Seven original synchronous stage intervals; excludes original flush/decode/sleep',
    }
    destination.with_suffix(destination.suffix + '.json').write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return metadata


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    print(json.dumps(generate(args.source, args.output), ensure_ascii=False, indent=2))
