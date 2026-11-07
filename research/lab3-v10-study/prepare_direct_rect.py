"""Preserve v10 board-fix; use measured baseline rectangle renderer only."""
from pathlib import Path
import hashlib,json,shutil,sys
src=Path(sys.argv[1]).resolve();dst=Path(sys.argv[2]).resolve();assert src!=dst
shutil.copytree(src,dst,ignore=shutil.ignore_patterns('board-comparison-*','__pycache__'))
changed=[]
baseline=(src/'common/graphic-baseline.c').read_text(encoding='utf-8')
start=baseline.index('void fb_draw_rect(');end=baseline.index('\nvoid ',start+1)
rect=baseline[start:end]
p=dst/'common/graphic-v10-batch.c';s=p.read_text(encoding='utf-8');start=s.index('void fb_draw_rect(');end=s.index('\nvoid ',start+1)
with p.open('w',encoding='utf-8',newline='\n') as f:f.write(s[:start]+rect+s[end:])
changed.append(p)
for name in ('test/sprint-v10-main.c','tests/test_sprint_v10_replay.c'):
 p=dst/name;s=p.read_text(encoding='utf-8')
 assert s.count('fb_geometry_batch *geometry_rect=fb_geometry_batch_begin();')==1
 s=s.replace('fb_geometry_batch *geometry_rect=fb_geometry_batch_begin();','/* Measured direct rectangle path; all rectangle calls remain timed. */')
 s=s.replace('fb_geometry_batch_rect(geometry_rect,','fb_draw_rect(')
 s=s.replace('fb_geometry_batch_end(geometry_rect);','/* Direct rectangle writes already completed. */')
 with p.open('w',encoding='utf-8',newline='\n') as f:f.write(s)
 changed.append(p)
m=dst/'manifest.json';manifest=json.loads(m.read_text(encoding='utf-8'));manifest['version']+='-direct-rect'
for p in changed:manifest['sourceHashes'][p.relative_to(dst).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(dst)
