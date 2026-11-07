from pathlib import Path
import json,struct
ROOT=Path(__file__).resolve().parent
assets=ROOT.parent/'labs3-5-prepared/build/assets'
visits=trimmed=nonzero=rows=empty_rows=glyphs=0
for baseline_y in range(-5,605,60):
    for text,size,y in [('嵌入式系统实验',40,baseline_y),('Embedded System Experiment',20,baseline_y+40)]:
        pen=20
        for char in text:
            data=(assets/('glyph-%x-%d.bin'%(ord(char),size))).read_bytes()
            width,height,left,top,advance=struct.unpack('<iiiii',data[:20]);mask=data[20:]
            x=pen+left;gy=y+top;glyphs+=1;pen+=advance
            l=max(0,-x);r=min(width,1024-x);t=max(0,-gy);b=min(height,600-gy)
            if l>=r or t>=b:continue
            for row in range(t,b):
                values=mask[row*width:(row+1)*width];rows+=1;visits+=r-l
                nz=[i for i,v in enumerate(values) if v]
                nonzero+=sum(1 for v in values[l:r] if v)
                if not nz:empty_rows+=1;continue
                first=max(l,nz[0]);last=min(r,nz[-1]+1)
                trimmed+=max(0,last-first)
result={'mode':'Pillow host glyph-mask workload projection, not ARM FreeType or time measurement',
        'glyphDrawCalls':glyphs,'visibleMaskPixelsBefore':visits,'visibleMaskPixelsAfterRowTrim':trimmed,
        'visibleNonzeroPixels':nonzero,'visibleRows':rows,'completelyEmptyVisibleRows':empty_rows,
        'reductionFraction':1-trimmed/visits,'performanceMeasured':False}
(ROOT/'v4-text-workload.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
