"""Create a separately named board-fix candidate; preserve original v10."""
from pathlib import Path
import hashlib,json,shutil,sys
src=Path(sys.argv[1]).resolve();dst=Path(sys.argv[2]).resolve()
assert src!=dst
shutil.copytree(src,dst,dirs_exist_ok=True,ignore=shutil.ignore_patterns('board-comparison-*','__pycache__'))
p=dst/'common/image-fast.c';s=p.read_text(encoding='utf-8')
old='''	if(slot->bitmap.rows && slot->bitmap.pitch > 0)
		memcpy(image->content, slot->bitmap.buffer, (size_t)slot->bitmap.rows * slot->bitmap.pitch);'''
new='''	/* FreeType embedded strikes may be packed MONO/GRAY2/GRAY4.
	 * Always normalize coverage to one byte per pixel, including row padding. */
	if(slot->bitmap.rows && slot->bitmap.width) {
		unsigned mode=slot->bitmap.pixel_mode;
		unsigned bits=mode==FT_PIXEL_MODE_MONO?1:mode==FT_PIXEL_MODE_GRAY2?2:mode==FT_PIXEL_MODE_GRAY4?4:mode==FT_PIXEL_MODE_GRAY?8:0;
		if(!bits || !slot->bitmap.buffer) {fb_free_image(image);return NULL;}
		unsigned long stride=slot->bitmap.pitch<0?-(long)slot->bitmap.pitch:slot->bitmap.pitch;
		if(stride<((size_t)slot->bitmap.width*bits+7)/8) {fb_free_image(image);return NULL;}
		memset(image->content,0,(size_t)image->line_byte*image->pixel_h);
		for(unsigned row=0;row<slot->bitmap.rows;row++) {
			const unsigned char *source=slot->bitmap.buffer+(long)row*slot->bitmap.pitch;
			unsigned char *target=(unsigned char *)image->content+(size_t)row*image->line_byte;
			for(unsigned col=0;col<slot->bitmap.width;col++) {
				if(bits==8)target[col]=slot->bitmap.num_grays==256?source[col]:slot->bitmap.num_grays>1?(unsigned)source[col]*255/(slot->bitmap.num_grays-1):0;
				else {unsigned mask=(1u<<bits)-1;unsigned shift=8-bits-(col*bits)%8;target[col]=((source[col*bits/8]>>shift)&mask)*255/mask;}
			}
		}
	}'''
assert old in s;s=s.replace(old,new)
with p.open('w',encoding='utf-8',newline='\n') as stream:stream.write(s)
m=dst/'manifest.json';manifest=json.loads(m.read_text(encoding='utf-8'));manifest['version']+='-board-fontfix-20261019'
manifest['sourceHashes']['common/image-fast.c']=hashlib.sha256(p.read_bytes()).hexdigest()
m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(dst)
