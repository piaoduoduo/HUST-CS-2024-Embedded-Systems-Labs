from pathlib import Path
import json,os,re,statistics,subprocess,sys
ROOT=Path(__file__).resolve().parent;WS=ROOT.parent;STUDY=WS/'lab3-optimization-study';BUILD=ROOT/'build';cc=sys.argv[1]
env=dict(os.environ);env['PATH']=str(Path(cc).parent)+os.pathsep+env.get('PATH','')
exe=BUILD/'bench_rows.exe'
cmd=[cc,'-std=gnu11','-O3','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-static','-D__USE_MINGW_ANSI_STDIO=1',
 '-I'+str(BUILD),'-I'+str(ROOT/'candidate/common'),'-I'+str(WS/'lab3-optimized-v10-prepared/tests'),
 str(ROOT/'bench_rows.c'),str(ROOT/'observer.c'),str(STUDY/'tests/asset_adapter.c'),str(BUILD/'font-identity.c'),'-o',str(exe),'-lm']
r=subprocess.run(cmd,env=env,cwd=STUDY,capture_output=True,text=True,timeout=120);assert r.returncode==0,r.stdout+r.stderr
r=subprocess.run([str(exe)],env=env,cwd=STUDY,capture_output=True,text=True,timeout=120);assert r.returncode==0,r.stdout+r.stderr
(ROOT/'host-benchmark.log').write_text(r.stdout,encoding='utf-8')
samples={}
for workload,variant,trial,ms,repeats,hashvalue in re.findall(r'BENCH (\w+) (\w+) (\d+) ([\d.]+) (\d+) ([\da-f]+)',r.stdout):samples.setdefault(workload,{}).setdefault(variant,[]).append(float(ms))
assert all(len(v)==9 for d in samples.values() for v in d.values())
report={'scope':'x86 GCC8.1 O3, no LTO, no NEON emulation, row renderer only; not board or full JPEG timer','samplesMs':samples,'mediansMs':{},'bitsetToIntervalRatio':{}}
for workload,d in samples.items():
    med={k:statistics.median(v) for k,v in d.items()};report['mediansMs'][workload]=med;report['bitsetToIntervalRatio'][workload]=med['bitset']/med['interval']
(ROOT/'host-benchmark.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
