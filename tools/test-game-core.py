"""Run the existing game rule/storage tests without a framebuffer or course font."""
from pathlib import Path
import argparse,json,os,subprocess

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc',default=os.environ.get('CC','gcc'))
    parser.add_argument('--version',choices=('1','2'),default='2')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    source=root/('projects/game-workshop-v'+args.version)
    output=root/'.work'/('game-core-v'+args.version)
    output.mkdir(parents=True,exist_ok=True)
    (output/'test-results').mkdir(exist_ok=True)
    rule_sources=['tests/test_arcade.c','arcade/engine.c','arcade/app.c']
    if args.version=='2':rule_sources.insert(2,'arcade/breaker.c')
    groups=[('rules',rule_sources)]
    if args.version=='2':
        groups += [('v2',['tests/test_v2.c','arcade/engine.c','arcade/breaker.c','arcade/app.c']),
                   ('storage',['tests/test_profile.c','arcade/profile.c'])]
    env=dict(os.environ)
    cc=Path(args.cc)
    if cc.is_absolute():env['PATH']=str(cc.parent)+os.pathsep+env.get('PATH','')
    results=[]
    for label,files in groups:
        executable=output/(label+('.exe' if os.name=='nt' else ''))
        command=[args.cc,'-std=gnu11','-O2','-Wall','-Wextra','-Werror',*[os.path.relpath(source/p,output) for p in files],'-lm','-o',executable.name]
        subprocess.run(command,check=True,cwd=output,env=env)
        result=subprocess.run([str(executable)],check=True,cwd=output,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        print(result.stdout,end='')
        results.append({'test':label,'exitCode':result.returncode,'output':result.stdout})
    (output/'result.json').write_text(json.dumps({'version':args.version,'hostTests':results,'boardTest':False},indent=2)+'\n',encoding='utf8')
    print('PASS: host game rules/storage; no touchscreen or board claim')

if __name__=='__main__':main()
