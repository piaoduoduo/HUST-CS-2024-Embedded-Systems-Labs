from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
import json
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'/example/user\Desktop\嵌入式系统实验报告_当前完成稿（1）_20261106.docx')
DESTDIR = ROOT / 'reports' / '排版修正版-20261106'
DEST = DESTDIR / '嵌入式系统实验报告_间距页码修正版_20261106.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
def q(n): return '{' + W + '}' + n

DESTDIR.mkdir(parents=True, exist_ok=True)
if DEST.exists():
    raise SystemExit('Refusing to overwrite an existing corrected report')
with ZipFile(SOURCE) as z:
    entries = [(e, z.read(e.filename)) for e in z.infolist()]
data = dict((e.filename, b) for e, b in entries)
doc = E.fromstring(data['word/document.xml'])
original_text = doc.xpath('//w:t/text()', namespaces=NS)
targets = [p for p in doc.xpath('//w:p', namespaces=NS)
           if 'Orangepi4-lts_3.0.6_ubuntu_desktop_otg.img' in ''.join(p.xpath('.//w:t/text()', namespaces=NS))]
assert len(targets) == 1
wrap = targets[0].find('w:pPr/w:wordWrap', NS)
assert wrap is not None
# OOXML's wordWrap=off allows character-level breaks, including long filenames.
wrap.set(q('val'), '0')
sections = doc.xpath('//w:sectPr', namespaces=NS)
assert len(sections) == 3
body_section = sections[-1]
page_number = body_section.find('w:pgNumType', NS)
if page_number is None:
    page_number = E.Element(q('pgNumType'))
    cols = body_section.find('w:cols', NS)
    body_section.insert(body_section.index(cols), page_number)
page_number.set(q('fmt'), 'decimal')
page_number.set(q('start'), '1')
# Keep the original cover and Roman-numbered contents section.
assert sections[1].find('w:pgNumType', NS).get(q('fmt')) == 'upperRoman'
assert original_text == doc.xpath('//w:t/text()', namespaces=NS)
data['word/document.xml'] = E.tostring(doc, encoding='UTF-8', xml_declaration=True, standalone=True)
settings = E.fromstring(data['word/settings.xml'])
update = settings.find('w:updateFields', NS)
if update is None:
    update = E.SubElement(settings, q('updateFields'))
update.set(q('val'), 'true')
data['word/settings.xml'] = E.tostring(settings, encoding='UTF-8', xml_declaration=True, standalone=True)
with ZipFile(DEST, 'w') as z:
    for entry, original in entries:
        z.writestr(entry, data.get(entry.filename, original))
media = {e.filename: sha256(b).hexdigest() for e, b in entries if e.filename.startswith('word/media/')}
with ZipFile(DEST) as z:
    assert all(sha256(z.read(n)).hexdigest() == h for n, h in media.items())
record = {'source': str(SOURCE), 'source_sha256': sha256(SOURCE.read_bytes()).hexdigest(),
          'output': str(DEST), 'text_unchanged_before_field_update': True,
          'image_count': len(media), 'media_hashes': media,
          'changes': ['Allow long filename to wrap within the affected paragraph',
                      'Body section uses decimal page numbers starting at 1',
                      'Request native field and table-of-contents recalculation'],
          'reference': 'https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.wordwrap?view=openxml-3.0.1'}
(DESTDIR / '修改记录.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'output':str(DEST),'paragraphs':len(doc.xpath('//w:p',namespaces=NS)),
                  'image_count':len(media),'text_unchanged':True},ensure_ascii=False))
