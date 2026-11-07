from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from copy import deepcopy
import csv, json

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'reports/最终修订-20261106/嵌入式系统实验报告_20页完成版_20261106.docx'
OUT=ROOT/'reports/定稿-20261107'
DST=OUT/'嵌入式系统实验报告_20页核对版_20261107.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
Q=lambda n:'{'+NS['w']+'}'+n
def add(parent,name,**attrs):
 node=E.SubElement(parent,Q(name))
 for k,v in attrs.items():node.set(Q(k),str(v))
 return node
def text(p):return ''.join(p.xpath('.//w:t/text()',namespaces=NS))
def pp(p):
 ppr=p.find('w:pPr',NS)
 if ppr is None:ppr=E.Element(Q('pPr'));p.insert(0,ppr)
 return ppr
def prop(p,key,value):
 ppr=pp(p);node=ppr.find('w:'+key,NS)
 if node is None:node=E.SubElement(ppr,Q(key))
 node.set(Q('val'),str(value))
def table(rows,widths):
 t=E.Element(Q('tbl'));pr=add(t,'tblPr');add(pr,'tblW',w=sum(widths),type='dxa');add(pr,'jc',val='center')
 borders=add(pr,'tblBorders')
 for name in ['top','left','bottom','right','insideH','insideV']:add(borders,name,val='single',sz=4,color='D9D9D9')
 add(pr,'tblLayout',type='fixed');m=add(pr,'tblCellMar')
 for name,v in [('top',65),('bottom',65),('left',70),('right',70)]:add(m,name,w=v,type='dxa')
 grid=add(t,'tblGrid')
 for w in widths:add(grid,'gridCol',w=w)
 for ri,row in enumerate(rows):
  tr=add(t,'tr');trpr=add(tr,'trPr');add(trpr,'cantSplit')
  if ri==0:add(trpr,'tblHeader')
  for ci,value in enumerate(row):
   tc=add(tr,'tc');tcpr=add(tc,'tcPr');add(tcpr,'tcW',w=widths[ci],type='dxa');add(tcpr,'vAlign',val='center')
   if ri==0:add(tcpr,'shd',val='clear',fill='F2F2F2')
   p=add(tc,'p');ppr=add(p,'pPr');add(ppr,'spacing',before=0,after=0,line=250,lineRule='auto');add(ppr,'jc',val='left' if ci in (0,len(row)-1) and len(row)>2 else 'center')
   add(ppr,'keepNext',val=1 if ri<len(rows)-1 else 0)
   r=add(p,'r');rpr=add(r,'rPr');add(rpr,'rFonts',ascii='Times New Roman',hAnsi='Times New Roman',eastAsia='宋体');add(rpr,'sz',val=21);add(rpr,'szCs',val=21)
   if ri==0:add(rpr,'b')
   add(r,'t').text=str(value)
 return t

OUT.mkdir(exist_ok=True);(OUT/'qa').mkdir(exist_ok=True)
with ZipFile(SRC) as z:entries=[(i,z.read(i.filename)) for i in z.infolist()]
data={i.filename:b for i,b in entries};doc=E.fromstring(data['word/document.xml']);styles=E.fromstring(data['word/styles.xml'])
ps=doc.xpath('//w:p',namespaces=NS)
results=[p for p in ps if text(p)=='实验结果'];assert len(results)==6
for i in [2,4]:prop(results[i],'pageBreakBefore',1)
for p in ps:
 if text(p).startswith('（') and len(text(p))<40:prop(p,'keepNext',1)
 if text(p).startswith('我先在电脑端测试游戏规则和界面逻辑'):prop(p,'keepLines',1)

# Make the one-page TOC layout its actual style, so a later field update stays compact.
for sid in ['7','8']:
 p=doc.xpath('//w:p[w:pPr/w:pStyle[@w:val="'+sid+'"]]',namespaces=NS)[0]
 st=styles.xpath('//w:style[@w:styleId="'+sid+'"]',namespaces=NS)[0]
 old=st.find('w:pPr',NS)
 if old is not None:st.remove(old)
 pr=deepcopy(pp(p))
 for node in list(pr):
  if node.tag in (Q('pStyle'),Q('rPr')):pr.remove(node)
 spacing=pr.find('w:spacing',NS)
 if spacing is None:spacing=add(pr,'spacing')
 for k,v in [('before','0'),('after','0'),('line','240'),('lineRule','auto')]:spacing.set(Q(k),v)
 st.append(pr)

rows=list(csv.reader((ROOT/'reports/manual-materials-20261106/实验三测速表.csv').open(encoding='utf-8-sig')))
conditions=['早期原接口','同批字模缓存','缓存与 -O3','同配置原接口','批量绘制','批量绘制','直接矩形＋批量','同部署版本复测']
table3=[['版本','三轮耗时/ms','中位数/ms','最小值/ms','测试配置']]
for row,condition in zip(rows[1:],conditions):table3.append([row[1],row[2],row[3],row[4],condition])
for label,rows_,widths in [
 ('表2-1',[['测试项目','阶段耗时/ms'],['画点','1'],['矩形','2'],['直线','2']],[3500,3500]),
 ('表3-1',table3,[2100,2100,1200,1200,2100])]:
 cap=next(p for p in ps if text(p).startswith(label));image=cap.getprevious()
 assert image.xpath('.//w:drawing | .//w:pict',namespaces=NS)
 image.getparent().replace(image,table(rows_,widths))

# WPS substitutes this nonstandard face automatically; store the actual equivalent name.
font_fixed=0
for root in [doc,styles]:
 for node in root.xpath('//w:rFonts',namespaces=NS):
  for k,v in list(node.attrib.items()):
   if v.startswith('Times New Roman') and v!='Times New Roman':node.set(k,'Times New Roman');font_fixed+=1
data['word/document.xml']=E.tostring(doc,encoding='UTF-8',xml_declaration=True,standalone=True)
data['word/styles.xml']=E.tostring(styles,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(DST,'w') as z:
 for i,b in entries:z.writestr(i,data[i.filename])
(OUT/'修改记录.json').write_text(json.dumps({'source':str(SRC),'destination':str(DST),'native_tables':2,'toc_style_fixed':True,'font_aliases_fixed':font_fixed,'report_media_preserved':15},ensure_ascii=False,indent=2),encoding='utf8')
print(DST)
