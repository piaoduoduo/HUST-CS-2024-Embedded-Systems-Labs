"""Offline proof of repeated-row reuse on actual decoded course PNG.
This is a Python algorithm oracle, not a production implementation or timing.
"""
from pathlib import Path
import collections,hashlib,json,random,struct
ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
data=(WS/'lab3-optimization-study/build/assets/test.png.bgra').read_bytes()
iw,ih,kind=struct.unpack('<iii',data[:12]);assert (iw,ih,kind)==(128,128,2)
source=data[12:];assert len(source)==iw*ih*4
W,H=1024,600
draws=[(x,y) for y in range(-5,605,128) for x in range(-5,1029,50)]
recipes=[]
for y in range(H):
    recipes.append(tuple((x,y-dy,max(x,0),min(x+iw,W)) for x,dy in draws if dy<=y<dy+ih and x<W and x+iw>0))
def render(row,recipe):
    out=bytearray(row)
    for x,sy,l,r in recipe:
        for px in range(l,r):
            si=(sy*iw+px-x)*4;di=px*4;a=source[si+3]
            if a==255:out[di:di+4]=source[si:si+4]
            elif a:
                for c in range(3):out[di+c]=(source[si+c]*a+out[di+c]*(255-a)+127)//255
                out[di+3]=255
    return bytes(out)
def surviving(recipe):
    covered=bytearray(W);partial=opaque=0
    for x,sy,l,r in reversed(recipe):
        for px in range(l,r):
            a=source[(sy*iw+px-x)*4+3]
            if a and not covered[px]:
                if a==255:opaque+=1
                else:partial+=1
            if a==255:covered[px]=1
    return partial,opaque
per_recipe={r:surviving(r) for r in set(recipes)}
report={'type':'offline work counts and byte-equality oracle; no board timing','sourcePNGDecodedSHA256':hashlib.sha256(data).hexdigest(),
 'screen':[W,H],'drawCalls':len(draws),'distinctRecipes':len(set(recipes)),'cases':{}}
rng=random.Random(1037)
for name in ('black','random-distinct','nonuniform-repeated'):
    if name=='black':initial=[bytes(W*4)]*H
    elif name=='random-distinct':initial=[rng.randbytes(W*4) for _ in range(H)]
    else:
        rows=[rng.randbytes(W*4) for _ in range(128)]
        initial=[rows[(y+5)%128] for y in range(H)]
    # Full recipe and initial bytes are compared before ANY row is modified.
    # A C implementation can retain leader row pointers, avoiding snapshots.
    groups={}
    for y in range(H):groups.setdefault((recipes[y],initial[y]),[]).append(y)
    expected=[render(initial[y],recipes[y]) for y in range(H)]
    actual=[None]*H
    for (recipe,initial_row),members in groups.items():
        out=render(initial_row,recipe)
        for y in members:actual[y]=out
    assert actual==expected
    old_partial=sum(per_recipe[r][0] for r in recipes)
    new_partial=sum(per_recipe[r][0] for r,_ in groups)
    old_opaque=sum(per_recipe[r][1] for r in recipes)
    new_opaque=sum(per_recipe[r][1] for r,_ in groups)
    report['cases'][name]={'equalAllBytes':True,'bytesChecked':W*H*4,'groups':len(groups),'rowsReused':H-len(groups),
     'partialBlendsBefore':old_partial,'partialBlendsAfter':new_partial,'opaqueWritesBefore':old_opaque,'opaqueWritesAfter':new_opaque,
     'additionalFollowerCopyBytes':(H-len(groups))*W*4,'finalSHA256':hashlib.sha256(b''.join(actual)).hexdigest()}
    print(name,report['cases'][name],flush=True)
(ROOT/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
