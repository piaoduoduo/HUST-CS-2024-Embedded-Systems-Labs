from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import re
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/定稿-20261107'
SRC=OUT/'嵌入式系统实验报告_正文20页_20261107.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
Q=lambda n:'{'+NS['w']+'}'+n
with ZipFile(SRC) as z:entries=[(i,z.read(i.filename)) for i in z.infolist()]
data={i.filename:b for i,b in entries};doc=E.fromstring(data['word/document.xml']);styles=E.fromstring(data['word/styles.xml'])
ps=doc.xpath('//w:p',namespaces=NS)
tocps=[p for p in ps if p.xpath('w:pPr/w:pStyle[@w:val="7" or @w:val="8"]',namespaces=NS)]
for p in tocps:
 pr=p.find('w:pPr',NS);sp=pr.find('w:spacing',NS)
 if sp is None:sp=E.SubElement(pr,Q('spacing'))
 for k,v in [('before','0'),('after','0'),('line','220'),('lineRule','auto')]:sp.set(Q(k),v)
 snap=pr.find('w:snapToGrid',NS)
 if snap is not None:snap.set(Q('val'),'0')
 t=''.join(p.xpath('.//w:t/text()',namespaces=NS))
 if t.startswith('7.4 '):
  for n in p.xpath('.//w:instrText',namespaces=NS):n.text=n.text.replace('_TocBody20Add0','_TocBody20Add1')
  p.xpath('.//w:t',namespaces=NS)[-1].text='20'
for st in styles.xpath('//w:style[@w:styleId="7" or @w:styleId="8"]',namespaces=NS):
 sp=st.find('w:pPr/w:spacing',NS);sp.set(Q('line'),'220')
 sn=st.find('w:pPr/w:snapToGrid',NS)
 if sn is not None:sn.set(Q('val'),'0')
data['word/styles.xml']=E.tostring(styles,encoding='UTF-8',xml_declaration=True,standalone=True)
def save(name):
 data['word/document.xml']=E.tostring(doc,encoding='UTF-8',xml_declaration=True,standalone=True)
 with ZipFile(OUT/name,'w') as z:
  for info,b in entries:z.writestr(info,data[info.filename])
save('嵌入式系统实验报告_提交版_20261107.docx')
# Blank only the personal-value cells on the cover. Keep the original row geometry.
cover=doc.find('.//w:tbl',NS)
personal=[]
for row in cover.findall('w:tr',NS):
 cells=row.findall('w:tc',NS)
 if len(cells)<2:continue
 label=re.sub(r'\s','', ''.join(cells[0].xpath('.//w:t/text()',namespaces=NS)))
 if any(k in label for k in ['姓名','学号','电话','邮件','班级']):
  for cell in cells[1:]:
   ts=cell.xpath('.//w:t',namespaces=NS);personal.extend(t.text for t in ts if t.text)
   for t in ts:t.text=''
   if ts:ts[0].text='________'
# Clear author metadata and personal values in remaining XML parts as well.
for name,b in list(data.items()):
 if name=='word/document.xml' or not name.endswith('.xml'):continue
 try:r=E.fromstring(b)
 except E.XMLSyntaxError:continue
 for el in r.iter():
  if E.QName(el).localname in ['creator','lastModifiedBy','Company','Manager']:el.text=''
  for value in personal:
   if el.text and value in el.text:el.text=el.text.replace(value,'')
 data[name]=E.tostring(r,encoding='UTF-8',xml_declaration=True,standalone=True)
save('嵌入式系统实验报告_公开版_20261107.docx')
print('Created private and anonymized public copies; TOC entries:',len(tocps))
