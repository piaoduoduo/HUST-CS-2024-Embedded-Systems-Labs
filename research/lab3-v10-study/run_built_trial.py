"""Run already native-validated board binaries, preserving build evidence."""
import argparse,json,os,statistics,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
p=argparse.ArgumentParser();p.add_argument('record');p.add_argument('--runs',type=int,default=3)
a=p.parse_args();record=Path(a.record).resolve();root=record.parent
sys.path.insert(0,str(root))
from board_compare import parse_metrics,snapshot
from runtime_controls import RuntimeControls
build=json.loads((record/'results.json').read_text())
names=['baseline','v9-sprint','v10-sprint']
assert all(name in build['commands'] for name in names), 'Require completed baseline/v9/v10 builds'
for name in names:
    assert build['exactNativeChecks'].get(name)
    assert (record/name/'out/test').is_file()
resultdir=record/'trial-measurements';resultdir.mkdir(exist_ok=False)
env=dict(os.environ)
env['LD_LIBRARY_PATH']='/root/course-project/lab-st-2026/common/external/lib'
args=SimpleNamespace(threads=2,active_wait=True,build_only=False,bind='fast',governor='performance')
controls=RuntimeControls(args,resultdir,env)
results={'sourceBuildRecord':str(record),'runs':[],'scope':'course timer; explicit batch API for optimized variants; decode/flush/sleep excluded'}
try:
    for iteration in range(a.runs):
        for name in names[iteration%len(names):]+names[:iteration%len(names)]:
            out=record/name/'out';before=snapshot()
            run=subprocess.run([str(out/'test')],cwd=out,env=env,capture_output=True,text=True,timeout=90)
            (resultdir/f'{name}-{iteration+1}.log').write_text(run.stdout+run.stderr)
            assert run.returncode==0,(name,run.returncode)
            metrics=parse_metrics(run.stdout)
            results['runs'].append({'variant':name,'iteration':iteration+1,'timingsMs':metrics,'before':before,'after':snapshot()})
            (resultdir/'results.json').write_text(json.dumps(results,indent=2))
            print(name,metrics,flush=True)
    results['medianMs']={name:{key:statistics.median(r['timingsMs'][key] for r in results['runs'] if r['variant']==name) for key in results['runs'][0]['timingsMs']} for name in names}
    (resultdir/'results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results['medianMs'],indent=2),flush=True)
finally:controls.restore()
