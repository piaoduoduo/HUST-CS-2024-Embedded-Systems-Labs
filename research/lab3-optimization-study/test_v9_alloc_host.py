from pathlib import Path
import hashlib,json,os,subprocess
root=Path(__file__).resolve().parent;build=root/'build-v9-png'
cc=Path('E:/x86_64-8.1.0-release-win32-seh-rt_v6-rev0/mingw64/bin/gcc.exe')
env=dict(os.environ);env['PATH']=str(cc.parent)+os.pathsep+env.get('PATH','')
logs={}
for name,flags,threads in [('scalar',[],1),('neon',['-DFB_TEST_NEON'],1),('omp2',['-DFB_TEST_NEON','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'],2),('omp4',['-DFB_TEST_NEON','-fopenmp','-DFB_PARALLEL_MIN_PIXELS=1'],4)]:
    exe=build/(name+'-allocation.exe')
    env['OMP_NUM_THREADS']=str(threads);env['OMP_DYNAMIC']='FALSE'
    cmd=[str(cc),'-std=gnu11','-O3','-Wall','-Wextra','-Werror','-static','-D__USE_MINGW_ANSI_STDIO=1','-DFB_CULL_TEST_STATS',*flags,'-I',str(build),'-I',str(root/'common'),'-I',str(root/'tests'),'-I',str(root/'tests/neon-emulation'),str(root/'tests/test_v9_alloc.c'),str(root/'tests/asset_adapter.c'),str(build/'font-identity.c'),'-o',str(exe),'-lm']
    p=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=60)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    p=subprocess.run([str(exe)],cwd=root,capture_output=True,text=True,env=env,timeout=60)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    logs[name]=p.stdout+p.stderr;print(name,p.stdout.strip(),flush=True)
(root/'v9-allocation-results.json').write_text(json.dumps({'hardwareValidated':False,'performanceMeasured':False,'sourceHashes':{f:hashlib.sha256((root/'common'/f).read_bytes()).hexdigest() for f in ['fast_pixels_v9.h','prepared_image_v9.h']},'actualMallocFailuresInjected':['command array','CSR row index'],'logs':logs},indent=2),encoding='utf-8')
