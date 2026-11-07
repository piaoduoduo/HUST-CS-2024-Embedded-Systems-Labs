"""Host clock-injection and source-preservation test; never a benchmark."""
from pathlib import Path
import argparse
import ast
import json
import os
import subprocess
import tempfile
from prepare_precise_timing import generate

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]


def test(cc):
    logs = []
    with tempfile.TemporaryDirectory(prefix='precise-test-', dir=ROOT) as tmp:
        tmp = Path(tmp)
        source = tmp/'main.c'
        durations = [123456, 2500000, 999999, 1000000, 333333, 7654321, 1234567]
        stamps = []
        now = 1000999999
        for duration in durations:
            stamps.extend([now, now+duration])
            now += duration+1000000000  # Delays between stages must be excluded.
        pairs = '\n'.join('a=task_get_time(); b=task_get_time(); sum+=b-a;' for _ in durations)
        source.write_text('#include <stdint.h>\n#include <stdio.h>\nint main(int argc,char **argv){\n'
                          '(void)argc;(void)argv; int32_t a,b,sum=0;\n'+pairs+
                          '\nprintf("QUANTIZED_MS %d\\n",sum); return 0;}\n', encoding='utf-8')
        saved = source.read_bytes()
        header = tmp/'clock.h'
        header.write_text('#include <stdint.h>\n#include <time.h>\n'
                          'static int test_clock(int id,struct timespec *t){ (void)id;\n'
                          'static unsigned i; static const uint64_t ns[14]={'+
                          ','.join(str(n)+'ULL' for n in stamps)+'};\n'
                          'if(i>=14) { return -1; }\n t->tv_sec=(time_t)(ns[i]/1000000000);'
                          't->tv_nsec=(long)(ns[i]%1000000000);i++;return 0;}\n'
                          '#ifndef CLOCK_MONOTONIC\n#define CLOCK_MONOTONIC 1\n#endif\n'
                          '#define LAB3_DIAG_CLOCK_READ test_clock\n', encoding='utf-8')
        generated = tmp/'diagnostic.c'
        generate(source, generated)
        exe = tmp/'diagnostic.exe'
        env = dict(os.environ)
        env['PATH'] = str(Path(cc).parent) + os.pathsep + env.get('PATH', '')
        cmd = [cc, '-std=gnu11', '-O3', '-Wall', '-Wextra', '-Werror',
               '-D__USE_MINGW_ANSI_STDIO=1', '-include', str(header), str(generated), '-o', str(exe)]
        build = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
        assert build.returncode == 0, build.stdout+build.stderr
        run = subprocess.run([str(exe)], capture_output=True, text=True, env=env, timeout=20)
        assert run.returncode == 0, run.stdout+run.stderr
        logs.append(run.stdout)
        stages = dict((s.split()[1], int(s.split()[2])) for s in run.stdout.splitlines()
                      if s.startswith('DIAGNOSTIC_STAGE_NS '))
        assert list(stages.values()) == durations
        assert 'DIAGNOSTIC_TOTAL_NS %d' % sum(durations) in run.stdout
        quantized = sum(stamps[i+1]//1000000-stamps[i]//1000000 for i in range(0,14,2))
        assert 'QUANTIZED_MS %d' % quantized in run.stdout
        assert source.read_bytes() == saved
        for wrong in (source, generated):
            try:
                generate(source, wrong)
                raise AssertionError('overwrite was not rejected')
            except ValueError:
                pass
        for label, path in [('baseline', PROJECT/'lab3-prepared/test/main.c'),
                            ('v8', PROJECT/'lab3-optimized-prepared/test/sprint-v6-main.c')]:
            metadata = generate(path, tmp/(label+'.c'))
            assert metadata['timingSites'] == 14 and metadata['originalSourceUnchanged']
        for path in (ROOT/'prepare_precise_timing.py', ROOT/'test_precise_timing.py'):
            ast.parse(path.read_text(encoding='utf-8'), feature_version=(3,8))
    report = {'passed': True, 'clockInjected': True, 'stageNanoseconds': durations,
              'sumNs': sum(durations), 'quantizedMs': quantized,
              'inputPreserved': True, 'rejectOverwrite': True, 'realCourseSourcesGenerate': True,
              'hardwareValidated': False, 'performanceMeasured': False, 'logs': logs}
    (ROOT/'precise-timing-tests.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('PASS precise timing injection, intervals, course-source generation and preservation')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--cc', required=True)
    test(p.parse_args().cc)
