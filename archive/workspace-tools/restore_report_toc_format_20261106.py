from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
import json

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / 'reports' / '排版修正版-20261106'
SOURCE = Path(r'/example/user\Desktop\嵌入式系统实验报告_当前完成稿（1）_20261106.docx')
DEST = OUTDIR / '嵌入式系统实验报告_间距页码修正版_20261106.docx'
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
Q = lambda n: '{' + NS['w'] + '}' + n
with ZipFile(SOURCE) as z:
    old = E.fromstring(z.read('word/document.xml'))
with ZipFile(DEST) as z:
    entries = [(i, z.read(i.filename)) for i in z.infolist()]
data = {i.filename:b for i,b in entries}
doc = E.fromstring(data['word/document.xml'])
xp = '//w:p[w:pPr/w:pStyle[@w:val="7" or @w:val="8"]]'
old_toc = old.xpath(xp, namespaces=NS)
new_toc = doc.xpath(xp, namespaces=NS)
assert len(old_toc) == len(new_toc) == 27
qa = OUTDIR / 'qa'
qa.mkdir(exist_ok=True)
(qa / '目录重新生成后-修复间距前.docx').write_bytes(DEST.read_bytes())
for p_old, p_new in zip(old_toc, new_toc):
    old_text_runs = p_old.xpath('.//w:r[w:t]', namespaces=NS)
    new_text_runs = p_new.xpath('.//w:r[w:t]', namespaces=NS)
    assert len(old_text_runs) == len(new_text_runs)
    assert [r.find('w:t', NS).text for r in old_text_runs[:-1]] == [r.find('w:t', NS).text for r in new_text_runs[:-1]]
    ppr = p_new.find('w:pPr', NS)
    p_new.replace(ppr, deepcopy(p_old.find('w:pPr', NS)))
    # Keep the original direct run formatting; retain new native field codes.
    default_rpr = old_text_runs[0].find('w:rPr', NS)
    for r in p_new.findall('w:r', NS):
        rpr = r.find('w:rPr', NS)
        if rpr is not None:
            r.remove(rpr)
        r.insert(0, deepcopy(default_rpr))
    for r_old, r_new in zip(old_text_runs, new_text_runs):
        r_new.replace(r_new.find('w:rPr', NS), deepcopy(r_old.find('w:rPr', NS)))

data['word/document.xml'] = E.tostring(doc, encoding='UTF-8', xml_declaration=True, standalone=True)
with ZipFile(DEST, 'w') as z:
    for entry, original in entries:
        z.writestr(entry, data[entry.filename])
record = json.loads((OUTDIR/'修改记录.json').read_text(encoding='utf-8'))
record['toc_regenerated_in_wps'] = True
record['toc_original_format_restored'] = True
record['toc_entries'] = [''.join(p.xpath('.//w:t/text()',namespaces=NS)) for p in new_toc]
(OUTDIR/'修改记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'toc_entries':len(new_toc),'output':str(DEST)},ensure_ascii=False))
