from pathlib import Path
import sys,hashlib,json
target=Path(sys.argv[1]);fixed=Path(sys.argv[2]).read_text(encoding='utf-8')
new=fixed[fixed.index('\t/* FreeType embedded strikes'):fixed.index('\n\tsinfo.advance_x',fixed.index('\t/* FreeType embedded strikes'))]
old='\tif(slot->bitmap.rows && slot->bitmap.pitch > 0)\n\t\tmemcpy(image->content, slot->bitmap.buffer, (size_t)slot->bitmap.rows * slot->bitmap.pitch);\n'
s=target.read_text(encoding='utf-8');assert old in s
with target.open('w',encoding='utf-8',newline='\n') as f:f.write(s.replace(old,new))
print(hashlib.sha256(target.read_bytes()).hexdigest())
