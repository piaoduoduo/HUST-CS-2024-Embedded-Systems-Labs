"""Counts only: exact course coordinates and image alpha. No timing predictions."""
from pathlib import Path
from collections import Counter
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
W, H = 1024, 600

def line_points(x1, y1, x2, y2):
    steep = abs(y2-y1) > abs(x2-x1)
    m1, m2 = (y1, y2) if steep else (x1, x2)
    n1, n2 = (x1, x2) if steep else (y1, y2)
    if m1 > m2: m1, m2, n1, n2 = m2, m1, n2, n1
    length, dist = m2-m1, abs(n2-n1)
    sign = -1 if n2 < n1 else 1
    for k in range(length+1):
        minor = n1 + sign * ((dist*k+length//2)//length if length else 0)
        yield (minor, m1+k) if steep else (m1+k, minor)

rects=[]
for row in range(-15,300,5):
    for column in range(-15,1029,5):rects.append((column,row,10,10))
for row in range(300,605,5):rects.append((0,row,500,10))
for column in range(500,1029,5):rects.append((column,300,10,300))
visits=np.zeros((H,W),np.uint32)
visible_commands=0
for x,y,w,h in rects:
    l,t,r,b=max(x,0),max(y,0),min(x+w,W),min(y+h,H)
    if l<r and t<b:visits[t:b,l:r]+=1;visible_commands+=1
rect_info=dict(commands=len(rects),visible_commands=visible_commands,
               writes=int(visits.sum()),unique_pixels=int((visits>0).sum()),
               max_overdraw=int(visits.max()))

lines=[(200,100+row,800,500-row) for row in range(401)]
lines += [(300+col,100,700-col,500) for col in range(401)]
visits.fill(0);horizontal=vertical=0;stride_hist=Counter()
for x1,y1,x2,y2 in lines:
    horizontal += y1==y2;vertical += x1==x2
    prev=None
    for x,y in line_points(x1,y1,x2,y2):
        visits[y,x]+=1
        if prev is not None:stride_hist[y*W+x-prev]+=1
        prev=y*W+x
line_info=dict(commands=len(lines),writes=int(visits.sum()),
               unique_pixels=int((visits>0).sum()),max_overdraw=int(visits.max()),
               horizontal=horizontal,vertical=vertical,strides=dict(stride_hist))

rgba=np.array(Image.open(ROOT/'lab3-prepared/out/test.png').convert('RGBA'))
alpha=rgba[:,:,3];ph,pw=alpha.shape
draws=[(x,y) for y in range(-5,605,128) for x in range(-5,1029,50)]
blocked=np.zeros((H,W),bool)
before=Counter();after=Counter();blends_by_row=np.zeros(H,np.int64)
span_len=Counter();partial_visits=scalar_tails=neon_blocks=0
for x,y in reversed(draws):
    l,t,r,b=max(x,0),max(y,0),min(x+pw,W),min(y+ph,H)
    if l>=r or t>=b:continue
    a=alpha[t-y:b-y,l-x:r-x];mask=blocked[t:b,l:r]
    for name,p in [('zero',a==0),('opaque',a==255),('partial',(a>0)&(a<255))]:
        before[name]+=int(p.sum());after[name]+=int((p&~mask).sum())
    blocked[t:b,l:r] |= (a==255)
    # v8 scans original source spans then clips, equivalent to clipped runs.
    for yy,arow in enumerate(a):
        xs=np.where((arow>0)&(arow<255))[0]
        starts=np.r_[0,np.flatnonzero(np.diff(xs)>1)+1] if len(xs) else []
        ends=np.r_[starts[1:],len(xs)] if len(xs) else []
        for start,end in zip(starts,ends):
            n=int(end-start);span_len[n]+=1;partial_visits+=n
            scalar_tails+=n%8;neon_blocks+=n//8
        blends_by_row[t+yy]+=len(xs)
png_info=dict(image_width=pw,image_height=ph,commands=len(draws),
              before_opaque_cull=dict(before),after_opaque_cull=dict(after),
              opaque_cull_partial_saved=before['partial']-after['partial'],
              clipped_partial_spans=sum(span_len.values()),
              clipped_short_spans=sum(v for k,v in span_len.items() if k<8),
              clipped_partial_pixels=partial_visits,clipped_scalar_tail_pixels=scalar_tails,
              clipped_neon_blocks=neon_blocks,
              hypothetical_four_lane_scalar_tail_pixels=sum((n%4)*v for n,v in span_len.items()),
              static_two_thread_partial_load=[int(x.sum()) for x in np.array_split(blends_by_row,2)],
              span_length_histogram=dict(sorted(span_len.items())))

# Verify culling only earlier contributions covered by a later alpha=255.
# Keep per-command masks: each pixel is still blended in original draw order.
def draw(dst,x,y,keep=None):
    l,t,r,b=max(x,0),max(y,0),min(x+pw,W),min(y+ph,H)
    if l>=r or t>=b:return
    src=rgba[t-y:b-y,l-x:r-x,:3].astype(np.uint32)
    a=alpha[t-y:b-y,l-x:r-x].astype(np.uint32)
    old=dst[t:b,l:r]
    mixed_rgb=(src*a[:,:,None]+old[:,:,:3]*(255-a[:,:,None])+127)//255
    # Match the actual framebuffer alpha contract, not just visible RGB:
    # transparent source preserves the old whole pixel, every nonzero alpha
    # sets output alpha to 255, including partial-alpha blending.
    mixed_alpha=np.where(a>0,255,old[:,:,3]).astype(np.uint32)
    mixed=np.concatenate((mixed_rgb,mixed_alpha[:,:,None]),axis=2)
    if keep is not None:mixed=np.where(keep[:,:,None],mixed,old)
    dst[t:b,l:r]=mixed
blocked=np.zeros((H,W),bool);keeps=[]
for x,y in reversed(draws):
    l,t,r,b=max(x,0),max(y,0),min(x+pw,W),min(y+ph,H)
    a=alpha[t-y:b-y,l-x:r-x]
    keeps.append(~blocked[t:b,l:r].copy())
    blocked[t:b,l:r] |= a==255
keeps.reverse()
rng=np.random.default_rng(20261018)
image_oracle=[]
black=np.zeros((H,W,4),np.uint32);black[:,:,3]=255
for label,background in [('opaque_black',black),
                         ('random_rgba',rng.integers(0,256,(H,W,4),dtype=np.uint32))]:
    direct=background.copy();culled=background.copy()
    for (x,y),keep in zip(draws,keeps):draw(direct,x,y);draw(culled,x,y,keep)
    assert np.array_equal(direct,culled)
    image_oracle.append(dict(initial_background=label,equal=True,channels=int(direct.size),
                             complete_32bit_pixels=H*W,
                             alpha_contract='a=0 preserves old alpha; a>0 sets alpha to 255'))
png_info['opaque_culling_python_oracle']=image_oracle

baseline=dict(pixel=6,rect=14,line=23,jpeg=62,png=30,font=9,text=11)
def worst_sparse_intervals(n):
    # Reproduce the list comparison count in fb_batch_row for x=0,2,4,...
    # when visited in reverse command order. No row ever becomes fully covered.
    covered=[]; comparisons=0
    for x in range(0,2*n,2):
        for left,right in covered:
            if left>=x+1:break
            comparisons+=1
        first=0
        while first<len(covered) and covered[first][1]<x:
            first+=1;comparisons+=1
        covered.insert(first,(x,x+1))
    assert comparisons==n*(n-1)
    return dict(commands=n,unique_written_pixels=n,interval_comparisons=comparisons)
out=dict(measurement_type='offline operation counts, no performance measurement',
         dimensions=[W,H],pixel=dict(calls=305*517,visible_pixels=300*512),
         rect=rect_info,line=line_info,png=png_info,baseline_ms=baseline,
         jpeg_sparse_adversarial_rows=[worst_sparse_intervals(n) for n in (16,32,64,128,256)],
         required_total_speedup_20ms=sum(baseline.values())/20,
         eliminate_jpeg_png_residual_ms=sum(baseline.values())-62-30,
         eliminate_all_images_residual_ms=6+14+23+11,
         equal_ratio_budget_20ms={k:v*20/155 for k,v in baseline.items()},
         sequential_rounding_counterexample=dict(source=100,destination=0,alpha1=1,alpha2=1,
               sequential=0,fused_exact_alpha_then_round=1))
(HERE/'workload-counts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
