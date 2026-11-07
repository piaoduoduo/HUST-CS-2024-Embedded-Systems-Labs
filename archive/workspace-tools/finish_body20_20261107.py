from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from copy import deepcopy

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/定稿-20261107'
SRC=OUT/'嵌入式系统实验报告_20页核对版_20261107.docx'
DST=OUT/'嵌入式系统实验报告_正文20页_20261107.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
Q=lambda n:'{'+NS['w']+'}'+n
def txt(p):return ''.join(p.xpath('.//w:t/text()',namespaces=NS))
def prop(p,name,value):
 pr=p.find('w:pPr',NS)
 n=pr.find('w:'+name,NS)
 if n is None:n=E.SubElement(pr,Q(name))
 n.set(Q('val'),str(value))
def replace_text(p,value):
 for c in list(p):
  if c.tag!=Q('pPr'):p.remove(c)
 r=E.SubElement(p,Q('r'));rp=E.SubElement(r,Q('rPr'));f=E.SubElement(rp,Q('rFonts'))
 for k,v in [('ascii','Times New Roman'),('hAnsi','Times New Roman'),('eastAsia','宋体')]:f.set(Q(k),v)
 E.SubElement(r,Q('t')).text=value
 for k in list(p.attrib):del p.attrib[k]

sections=[('实验复现与连接检查',[
'我把两次实验课和后续试运行中用到的连接方法整理成固定流程。开始时先确认开发板和显示屏分别供电，再连接 HDMI 与触摸 USB 数据线。HDMI 负责把图像送到屏幕，触摸数据则通过 USB 返回开发板；因此，看到桌面只能说明显示链路已经工作，还需要检查触摸设备是否被系统识别。',
'使用网线连接笔记本与开发板时，我先在 Windows 中查看以太网是否已连接，再把无线网络共享给对应的以太网接口。开发板端用 ip -br addr 检查 eth0 的状态和地址，确认两端处于同一网段后再登录 SSH。排查时我曾把地址中的 168 写成 16，导致线路看似正常却无法连通；逐段核对地址后恢复了连接。',
'没有网线时，我采用手机热点连接电脑与开发板。热点分配的地址可能变化，因此每次开机后都重新查看开发板地址，再在电脑 PowerShell 中执行 ssh root@开发板地址。SSH 终端中输入密码时不会显示字符或星号，输入完成后直接回车即可。登录后看到开发板的命令提示符，才能继续在板上编译或启动实验程序。',
'开始显示或触摸实验前，我检查当前运行的程序，避免桌面和实验程序同时改写 framebuffer。需要停止的是开发板上的图形桌面，笔记本仍可正常使用。触摸节点通过 /proc/bus/input/devices 与 /dev/input/event* 对照查找，不把上一次的 event 编号直接当作本次编号。出现画面正常、触摸无响应时，我先检查屏幕到开发板的 USB 数据线。',
'实验五按设备发现、系统配对、串口应用连接和双向收发的顺序操作。手机显示已配对后，还要在 SPP 应用中连接串口服务；开发板出现 /dev/rfcomm0 后再检查应用收发。演示结束前，我会主动断开并重连一次，分别发送中文和 hello，确认重连后的通信正常。',
'结束实验时，我先退出前台程序，保存测速日志与运行截图，再通过终端让开发板正常关机，最后收起电源和数据线。按这套顺序准备，可以把课堂时间集中用于程序演示和问题分析，也便于下一次恢复相同的运行环境。'
]),('源码管理与性能记录',[
'在持续优化过程中，我保留原始版本、每次阶段性修改及对应测试材料。稳定版本用于上课演示，候选版本单独编译和测试；只有结果和显示效果都检查完成后，才更新演示程序。这种组织方式使我在实验三修改绘图路径时，仍能随时回到原接口版本进行对照。',
'实验三的记录同时保存三轮总耗时和分项耗时。直接矩形组合的三轮结果为 22、21、17 ms，中位数为 21 ms；后续同一部署版本复测得到 58、19、20 ms，中位数为 20 ms。两组结果说明较快成绩可以再次出现，但首次运行仍会带来明显波动。对外展示时，我把完整三轮数据与最低成绩放在一起，便于看清稳定程度。',
'比较不同版本时，我先确认编译选项、CPU 设置、测试循环和计时位置，再分析算法变化。早期缓存版本的 160、155、173 ms，与后来的同配置基线 47、46、47 ms，不能直接视为单一代码修改造成的差异。我在记录中分别列出历史基线、同轮基线和优化版本，避免把环境变化混入算法收益。',
'从工作量看，逐次绘制需要处理每次请求覆盖的像素，而批量路径可以先确定最终可见区域，再集中写入显存。若多次绘制覆盖同一位置，后画内容会替代前画内容，消除这些最终不可见的写入就能减少实际像素操作。图片与文字的处理仍受像素量和字形大小影响，优化重点是减少重复解析、分支判断、数据搬运和无效覆盖。',
'我还把 PNG、中文文字和基础几何图形的测试与速度测试分开保存。速度下降并不自动说明功能正确，因此仍需要检查透明区域、半透明混合、字形边缘、坐标裁剪以及不同方向的直线。综合实验则增加游戏规则、撤销、存档和连续碰撞等检查，避免只依据一张正常画面判断全部功能。',
'最终整理时，我把代码、构建说明、连接排障、测速表和实验报告放在同一仓库，并在 README 中给出入口。公开材料保留实现方法与实测结果，课程镜像、字体和外部库仍从课程渠道取得。这样既保留了本次实验的完整过程，也便于以后按明确的依赖和操作步骤重新运行。'
])]
with ZipFile(SRC) as z:entries=[(i,z.read(i.filename)) for i in z.infolist()]
data={i.filename:b for i,b in entries};doc=E.fromstring(data['word/document.xml']);body=doc.find('w:body',NS)
ps=doc.xpath('//w:p',namespaces=NS)
head=next(p for p in ps if txt(p)=='实验建议')
para=next(p for p in ps if txt(p).startswith('综合实验建议进一步'))
toc=next(p for p in ps if txt(p).startswith('7.2 '))
for i,(title,paragraphs) in enumerate(sections):
 h=deepcopy(head);replace_text(h,title);prop(h,'pageBreakBefore',1);prop(h,'keepNext',1)
 bm='_TocBody20Add'+str(i);sid=str(1000+i)
 start=E.Element(Q('bookmarkStart'));start.set(Q('id'),sid);start.set(Q('name'),bm);h.insert(1,start)
 end=E.SubElement(h,Q('bookmarkEnd'));end.set(Q('id'),sid)
 body.insert(len(body)-1,h)
 for value in paragraphs:
  p=deepcopy(para);replace_text(p,value);body.insert(len(body)-1,p)
 t=deepcopy(toc)
 for n in t.xpath('.//w:instrText',namespaces=NS):n.text=n.text.replace('_Toc16614',bm)
 ts=t.xpath('.//w:t',namespaces=NS)
 ts[0].text='7.'+str(3+i)+' ';ts[1].text=title
 for node in ts[2:-1]:node.text=''
 ts[-1].text=str(19+i)
 toc.addnext(t);toc=t
data['word/document.xml']=E.tostring(doc,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(DST,'w') as z:
 for info,b in entries:z.writestr(info,data[info.filename])
print(DST)
