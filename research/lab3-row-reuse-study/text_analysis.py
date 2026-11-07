"""Exact text-row reuse oracle on HOST Pillow masks; not ARM timings."""
from pathlib import Path
import hashlib,json,random,struct
ROOT=Path(__file__).resolve().parent
ASSETS=ROOT.parent/'lab3-optimization-study/build/assets'
W,H=1024,600
rows=[[] for _ in range(H)]
glyph_calls=0
for baseline in range(-5,605,60):
    for text,size,y,color in [('嵌入式系统实验',40,baseline,(0,255,0)),('Embedded System Experiment',20,baseline+40,(0,0,0))]:
        advance=0
        for char in text:
            data=(ASSETS/f'glyph-{ord(char):x}-{size}.bin').read_bytes()
            width,height,left,dy,step=struct.unpack('<5i',data[:20])
            mask=data[20:];assert len(mask)==width*height
            gx,gy=20+advance+left,y+dy
            glyph_calls+=1
            for sy in range(height):
                yy=gy+sy
                if not 0<=yy<H:continue
                for sx in range(width):
                    a=mask[sy*width+sx];xx=gx+sx
                    if a and 0<=xx<W:rows[yy].append((xx,a,color))
            advance+=step
recipes=[tuple(row) for row in rows]
bounds=[(min(p[0] for p in r),max(p[0] for p in r)+1) if r else (0,0) for r in recipes]
def render(initial,recipe):
    out=bytearray(initial)
    for x,a,color in recipe:
        for c in range(3):out[4*x+c]=(color[c]*a+out[4*x+c]*(255-a)+127)//255
        out[4*x+3]=255
    return bytes(out)
rng=random.Random(1037)
report={'warning':'Host Pillow glyph masks, work counts only; recipe tuples expand pixels for the oracle, not proposed production representation.', 'glyphCalls':glyph_calls,'activeRows':sum(bool(r) for r in recipes),'uniqueActiveRecipes':len(set(recipes)-{()}),'cases':{}}
for case in ('white','random-distinct','same-roi-different-outside'):
    if case=='white':initial=[bytes([255,255,255,0])*W]*H
    else:
        initial=[rng.randbytes(W*4) for _ in range(H)]
        if case=='same-roi-different-outside':
            for y,(l,r) in enumerate(bounds):initial[y]=initial[y][:l*4]+bytes([255,255,255,0])*(r-l)+initial[y][r*4:]
    groups={}
    for y,recipe in enumerate(recipes):
        if recipe:
            l,r=bounds[y]
            groups.setdefault((recipe,initial[y][l*4:r*4]),[]).append(y)
    expected=[render(initial[y],recipes[y]) for y in range(H)]
    actual=list(initial);copies=0
    for (recipe,_),members in groups.items():
        leader=members[0];l,r=bounds[leader]
        result=render(initial[leader],recipe)
        actual[leader]=result
        for y in members[1:]:
            actual[y]=initial[y][:l*4]+result[l*4:r*4]+initial[y][r*4:]
            copies+=(r-l)*4
    assert actual==expected
    report['cases'][case]={'allBytesEqual':True,'groups':len(groups),'nonzeroAlphaOperationsBefore':sum(map(len,recipes)),'nonzeroAlphaOperationsAfter':sum(len(k[0]) for k in groups),'followerCopyBytes':copies,'fullRowCopyBytesIfUsed':sum((len(v)-1)*W*4 for v in groups.values()),'finalSHA256':hashlib.sha256(b''.join(actual)).hexdigest()}
(ROOT/'text-analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
