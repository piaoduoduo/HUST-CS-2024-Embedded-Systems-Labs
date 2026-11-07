from pathlib import Path
import os,subprocess,json
ROOT=Path(__file__).resolve().parent;BUILD=ROOT/'build';CC=Path('E:/x86_64-8.1.0-release-win32-seh-rt_v6-rev0/mingw64/bin/gcc.exe')
env=dict(os.environ);env['PATH']=str(CC.parent)+os.pathsep+env.get('PATH','')
logs={}
for name,flags in [('enabled',[]),('products-disabled',['-DFB_DISABLE_PRODUCTS']),('products-spill',['-DFB_PRODUCT_MAX_PIXELS=1']),('prepare-disabled',['-DFB_DISABLE_PREPARED']),('lto-neon',['-flto','-DFB_TEST_NEON'])]:
    exe=BUILD/('v8-storage-'+name+'.exe')
    command=[CC,'-std=gnu11','-O3','-Wall','-Wextra','-Werror','-static','-D__USE_MINGW_ANSI_STDIO=1',*flags,'-I',BUILD,'-I',ROOT/'common','-I',ROOT/'tests','-I',ROOT/'tests/neon-emulation',ROOT/'tests/test_v8_product_storage.c',ROOT/'tests/asset_adapter.c',BUILD/'font-identity.c','-o',exe,'-lm']
    r=subprocess.run(list(map(str,command)),env=env,capture_output=True,text=True,timeout=120);logs[name+'-build']=r.stdout+r.stderr;assert r.returncode==0,logs
    r=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=60);logs[name]=r.stdout+r.stderr;assert r.returncode==0,logs;print(r.stdout,flush=True)
(ROOT/'v8-storage-results.json').write_text(json.dumps({'logs':logs,'hardwareValidated':False,'performanceMeasured':False},indent=2),encoding='utf-8')
