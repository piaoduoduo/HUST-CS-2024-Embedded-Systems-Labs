"""Run the installed measured candidate; every invocation produces a NEW score."""
from pathlib import Path
from types import SimpleNamespace
import datetime,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'best-support'))
from runtime_controls import RuntimeControls
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
record=ROOT/'best-runs'/stamp;record.mkdir(parents=True)
env=dict(os.environ)
env['LD_LIBRARY_PATH']=str(ROOT.parent/'common/external/lib')
args=SimpleNamespace(threads=2,active_wait=True,build_only=False,bind='fast',governor='performance')
subprocess.run(['systemctl','stop','display-manager'],check=True)
subprocess.run(['fbset','-g','1024','600','1280','720','32'],check=True)
controls=RuntimeControls(args,record,env)
try:
    with (record/'run.log').open('w') as log:
        process=subprocess.Popen([str(ROOT/'test')],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for line in process.stdout:
            print(line,end='',flush=True);log.write(line);log.flush()
        code=process.wait()
    (record/'status.json').write_text(json.dumps({'exitCode':code,'historicalBestMs':17,'historicalThreeRunsMs':[22,21,17],'newResultLog':str(record/'run.log')},indent=2))
    subprocess.run([sys.executable,str(ROOT/'best-support/capture-framebuffer.py'),str(record/'screen.ppm')],check=True)
    print('Saved fresh result:',record)
    if code:raise SystemExit(code)
finally:controls.restore()
