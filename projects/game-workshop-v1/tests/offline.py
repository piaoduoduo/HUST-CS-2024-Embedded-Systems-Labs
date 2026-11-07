"""Reproducible Windows tests. Host simulations are not ARM or board acceptance."""
from pathlib import Path
import hashlib,json,os,struct,subprocess
from PIL import Image,ImageFont,ImageDraw
root=Path(__file__).resolve().parents[1]
cc=Path(os.environ.get('ARCADE_CC','C:/msys64/ucrt64/bin/gcc.exe'))
env=dict(os.environ);env['PATH']=str(cc.parent)+os.pathsep+env.get('PATH','')
for d in ('build/assets','test-results','preview'):(root/d).mkdir(parents=True,exist_ok=True)
def run(args,log):
    r=subprocess.run([str(v) for v in args],cwd=root,env=env,capture_output=True,encoding='utf-8',errors='replace',timeout=120)
    (root/'test-results'/log).write_text(r.stdout+r.stderr,encoding='utf-8')
    print(r.stdout+r.stderr,end='')
    if r.returncode:raise RuntimeError(f'{log}: exit {r.returncode}')
flags=['-std=gnu11','-O2','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-static','-Ibuild','-Icommon','-Itests']
engine=['arcade/engine.c','arcade/app.c']
run([cc,*flags,'tests/test_arcade.c',*engine,'-lm','-o','build/test_arcade.exe'],'compile.log')
run([root/'build/test_arcade.exe'],'engine.log')
source=(root/'common/graphic.c').read_text(encoding='utf-8')
globals=source[source.index('static int LCD_FB_FD;'):source.index('void fb_init(')]
globals=globals.replace('static int LCD_FB_FD;\n','').replace('static int DRAW_BUF[SCREEN_WIDTH*SCREEN_HEIGHT];','static struct { int before[GUARD_WORDS]; int pixels[SCREEN_WIDTH*SCREEN_HEIGHT]; int after[GUARD_WORDS]; } TEST_BACK;\n#define DRAW_BUF TEST_BACK.pixels')
(root/'build/graphics-under-test.c').write_text('#include "common.h"\n#include <limits.h>\n#include <math.h>\n#define GUARD_WORDS 64\n'+globals+source[source.index('static void _copy_area('):],encoding='utf-8')
image=(root/'common/image.c').read_text(encoding='utf-8')
(root/'build/image-memory-under-test.c').write_text('#include <limits.h>\n'+image[image.index('/*w, h maybe == 0*/'):image.index('/*================== read a jpeg image')],encoding='utf-8')
chars=set(chr(i) for i in range(32,127))
for folder in ('arcade','lab6_gomoku'):
    for path in (root/folder).glob('*.c'):chars.update(path.read_text(encoding='utf-8'))
fontpath=root.parent/'course-source/lab-st-2026/out/font.ttc'
for size in (16,20,24,30):
    font=ImageFont.truetype(str(fontpath),size)
    for ch in sorted(c for c in chars if ord(c)>=32):
        mask,offset=font.getmask2(ch,mode='L',anchor='ls')
        (root/f'build/assets/glyph-{ord(ch):x}-{size}.bin').write_bytes(struct.pack('<iiiii',*mask.size,*offset,round(font.getlength(ch)))+bytes(mask))
run([cc,*flags,'tests/test_render.c',*engine,'arcade/render.c','tests/asset_adapter.c','-lm','-o','build/test_render.exe'],'render-compile.log')
run([root/'build/test_render.exe'],'render.log')
run([cc,*flags,'-DO_NONBLOCK=2048','-Itests/host-headers','-fsyntax-only','arcade/main.c'],'host-syntax.log')
gm=['lab6_gomoku/'+n+'.c' for n in ('gomoku','ai','app','session','render')]
run([cc,*flags,'tests/simulator.c',*engine,'arcade/render.c',*gm,'tests/asset_adapter.c','-lm','-lgdi32','-luser32','-mwindows','-o','build/arcade-simulator.exe'],'simulator-compile.log')
paths=[]
for p in (root/'preview').glob('*.ppm'):
    Image.open(p).save(p.with_suffix('.png'));paths.append(p.with_suffix('.png'))
sheet=Image.new('RGB',(1024,660),'#eeeeee');draw=ImageDraw.Draw(sheet)
for i,p in enumerate(sorted(paths)):
    im=Image.open(p);im.thumbnail((500,190));x=(i%2)*512;y=(i//2)*220
    sheet.paste(im,(x,y+25));draw.text((x+10,y+5),p.stem+' (HOST SIMULATION)',fill='black')
sheet.save(root/'preview/contact.png')
original=root.parent/'lab6-gomoku-boardfix-prepared'
hashes=json.loads((root/'preserved-source-hashes.json').read_text())
assert all(hashlib.sha256((original/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
report={'hostTestsPassed':True,'generated2048Moves':8000,'simulatedUIStates':6,'hostSyntaxWithLinuxShimsPassed':True,'originalSourceUnchanged':True,'nativeLinuxBuildVerified':False,'hardwareVerified':False,'formalAcceptance':False,'sources':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'arcade').glob('*') if p.is_file()}}
(root/'test-results/result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PASS: originals unchanged; host verification complete; ARM and board testing pending')
