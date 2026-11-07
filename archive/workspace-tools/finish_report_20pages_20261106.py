from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/最终修订-20261106'
SRC=OUT/'嵌入式系统实验报告_第一人称修订版_20261106.docx'
DST=OUT/'嵌入式系统实验报告_20页完成版_20261106.docx'
BASE=ROOT/'reports/文字修订版-20261106/嵌入式系统实验报告_文字排版修订版_20261106.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
Q=lambda n:'{'+NS['w']+'}'+n
with ZipFile(SRC) as z:
 entries=[(i,z.read(i.filename)) for i in z.infolist()]
doc=E.fromstring(dict((i.filename,b) for i,b in entries)['word/document.xml'])
with ZipFile(BASE) as z: base=E.fromstring(z.read('word/document.xml'))
xp='//w:p[w:pPr/w:pStyle[@w:val="7" or @w:val="8"]]'
toc=doc.xpath(xp,namespaces=NS)
old=base.xpath(xp,namespaces=NS)
assert len(toc)==len(old)==27
for p,op in zip(toc,old):
 p.replace(p.find('w:pPr',NS),deepcopy(op.find('w:pPr',NS)))
 rt=p.xpath('.//w:r[w:t]',namespaces=NS)
 ot=op.xpath('.//w:r[w:t]',namespaces=NS)
 # All text and page references retain their current values.
 for j,r in enumerate(rt):
  rpr=r.find('w:rPr',NS)
  if rpr is not None:r.remove(rpr)
  source=ot[min(j,len(ot)-1)].find('w:rPr',NS)
  if source is not None:r.insert(0,deepcopy(source))

anchor=next(p for p in doc.xpath('//w:p',namespaces=NS) if ''.join(p.xpath('.//w:t/text()',namespaces=NS)).startswith('我对矩形的不同画法'))
additions=[
 '从工作量看，我把优化分为减少单次计算和减少重复绘制两部分。若重复绘制 N 次，每次图像包含 P 个像素，逐次完整遍历需要处理约 N×P 个像素。NEON 和按行并行主要加快这部分计算，仍然需要处理相同数量的像素；字形缓存则把重复的字符解析与栅格化结果保存起来，后续直接复用。这样既减少了函数调用，也把更多时间留给实际的像素写入。',
 '批量覆盖消除进一步改变了需要执行的工作。以多次在同一位置绘制同样大小的不透明图像为例，如果两次绘制之间没有刷新屏幕，最终画面只保留最后一次图像。我的实现先整理绘制请求，确定最后可见的区域，再执行这些区域的写入。这个例子中的像素写入量可以从 N×P 降到接近 P，另外仍有请求整理与区域分析的开销。实际收益与图像位置、覆盖关系和可见区域数量有关，这也解释了为什么这种方法在重复覆盖较多时效果明显。',
 '透明 PNG 的处理方式有所不同：半透明像素会读取背景并参与混合，连续绘制的结果与先后顺序有关。因此，我仍保留透明混合的顺序，主要从跳过透明像素、复用行索引和加快颜色运算入手。文字部分则复用字形与布局计算。对照最快一轮的数据，PNG 为 6 ms，矩形和直线各为 4 ms，已经占到总成绩的大部分；后续继续优化时，我会优先分析这些阶段。画点显示 0 ms 是整数毫秒计时的结果，说明该阶段很短。',
]
for text in additions:
 p=E.Element(Q('p'))
 ppr=anchor.find('w:pPr',NS)
 if ppr is not None:p.append(deepcopy(ppr))
 r=E.SubElement(p,Q('r'))
 rpr=anchor.find('w:r/w:rPr',NS)
 if rpr is not None:r.append(deepcopy(rpr))
 E.SubElement(r,Q('t')).text=text
 anchor.addnext(p);anchor=p

# Keep each figure or table image with its following caption.
for p in doc.xpath('//w:p[.//w:drawing or .//w:pict]',namespaces=NS):
 nxt=p.getnext()
 if nxt is None or nxt.tag!=Q('p'):continue
 caption=''.join(nxt.xpath('.//w:t/text()',namespaces=NS)).strip()
 if not caption.startswith(('图','表')):continue
 ppr=p.find('w:pPr',NS)
 if ppr is None:ppr=E.Element(Q('pPr'));p.insert(0,ppr)
 k=ppr.find('w:keepNext',NS)
 if k is None:k=E.SubElement(ppr,Q('keepNext'))
 k.set(Q('val'),'1')

xml=E.tostring(doc,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(DST,'w') as z:
 for i,b in entries:z.writestr(i,xml if i.filename=='word/document.xml' else b)
(OUT/'优化分析补充.json').write_text(json.dumps(additions,ensure_ascii=False,indent=2),encoding='utf8')
print(DST)
