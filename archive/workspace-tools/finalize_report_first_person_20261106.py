from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from hashlib import sha256
import json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'reports/文字修订版-20261106/嵌入式系统实验报告_文字排版修订版_20261106.docx'
OUT = ROOT / 'reports/最终修订-20261106'
DST = OUT / '嵌入式系统实验报告_第一人称修订版_20261106.docx'
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
Q = lambda n: '{'+NS['w']+'}'+n

replacements = {
72: '我在 Windows 电脑上解压课程提供的 Orangepi4-lts_3.0.6_ubuntu_desktop_otg.img 镜像，使用 balenaEtcher 选择镜像和约 64 GB 的存储卡，完成写入及校验。出现“Flash Complete!”后取出存储卡，在开发板断电状态下将其插入卡槽，再连接开发板电源、显示屏电源和 HDMI，等待系统启动。',
77: '我在 PowerShell 中执行 ssh root@192.168.137.115，首次连接时确认主机信息，再输入密码。开始时我误以为键盘没有响应，后来发现 SSH 输入密码时本来就不显示字符，输入完成后按回车即可。登录成功后，终端出现 root@orangepi4-lts 提示符，我便可以直接在电脑上编译和运行开发板程序。',
79: '我将课程工程复制到开发板，把 common/rules.mk 中的编译器设为 gcc，使用板端 GCC 进行编译。进入 lab1 目录执行 make，再进入 out 目录运行 ./lab1，最后执行 echo $? 查看程序返回值。',
89: '我先打开 /dev/fb0，通过 ioctl 获取分辨率、像素格式和行跨度，再使用 mmap 将显存映射到进程地址空间。开发板的可见分辨率为 1024×600，每像素 32 位，虚拟分辨率为 1280×720，line_length 为 5120 字节。计算像素地址时，我使用实际行跨度定位每一行，再加上横坐标对应的字节偏移，解决了可见宽度与显存布局不一致的问题。',
91: '我在 fb_draw_rect 中根据起点、宽度和高度确定矩形范围，将超出屏幕的部分裁去，再逐行填充颜色。矩形每一行对应一段连续内存，因此只需计算一次行首地址，再顺序写入各像素。与反复调用画点函数相比，按行填充减少了重复的地址计算与函数调用，绘制宽度为 w、高度为 h 的矩形仍需完成 O(w×h) 次像素写入。',
93: '我在 fb_draw_line 中采用整数误差累加的方法绘制直线。程序选择坐标变化较大的方向作为主轴，每沿主轴前进一步，就根据累计误差判断另一方向是否移动，从而生成连续的像素轨迹。整个过程使用整数加减与比较，不必逐点计算浮点斜率，能够统一处理水平线、竖直线和不同斜率的线段；两个端点重合时绘制一个点。',
95: '我将绘制与显示更新分开：先把图形写入内存缓冲并记录更新区域，再由 fb_update 按显存的实际行跨度复制到 framebuffer。运行程序前，我临时停止开发板桌面，使实验程序直接控制屏幕。',
105: '我用 fb_image 统一保存图像格式、宽高、行跨度和像素数据，并分别实现 JPEG 和 PNG 的绘制。JPEG 按不透明图像直接写入，PNG 则根据 alpha 值混合前景色与背景色。完全透明的像素直接跳过，完全不透明的像素直接写入，其余像素采用整数运算完成颜色混合。',
106: '我使用 FreeType 从 font.ttc 中读取字形，按 UTF-8 编码逐个解析字符，再根据 left、top 和 advance_x 确定字形位置与下一个字符的起点。字模中的灰度值作为透明度，与指定颜色组合后绘制到背景上。调试小字号文字时，我发现单色 MONO 字模与 8 位灰度字模的存储方式不同，补充格式转换后解决了显示问题。',
112: '我对矩形的不同画法进行上板对比，最终保留耗时较低的直接绘制方案。同时比较优化前后的像素结果，并检查图片、透明效果和中文显示，确认优化后的画面正常。这个过程让我认识到，减少绘制次数和加快一次绘制是两类优化，需要结合实际数据选择。',
115: '我让每组测试连续运行三轮，记录各分项和总耗时，再计算中位数，用于观察优化效果及运行波动。比较版本时，除总成绩外，我还逐项检查七个阶段的变化，以判断新的优化究竟节省了哪部分工作。',
129: '我通过 /proc/bus/input/devices 和 /dev/input/eventN 查找触摸设备，识别到的屏幕型号为 wch.cn USB2IIC_CTP_CONTROL。屏幕通过 HDMI 接收图像，通过 USB 数据线向开发板传送触摸事件。调试时，我根据设备信息确定对应的 event 节点。',
131: '我按 Protocol B 为各 slot 保存跟踪编号、坐标和按压状态，并在同步事件到来时生成按下、移动和抬起等应用事件。触摸原始坐标范围为 0—4096，我将其映射到 1024×600 的显示坐标。驱动报告 6 个 slot，课程应用使用其中 0—4 共五个触点，各触点分别维护自己的状态。',
133: '我为五个触点分别分配红、蓝、绿、紫、橙五种颜色，并记录各触点的上一次坐标。在相邻采样点之间插值绘制 9 像素笔刷，使手指快速移动时也能形成连续粗线。手指抬起时结束当前笔画，再次按下时开始新笔画。',
146: '我在开发板上配置 BlueZ，开启经典蓝牙的可发现和可配对状态，并配置串口服务。手机使用带有“SPP”标识的蓝牙串口应用。我先在手机系统设置中与开发板配对，再进入串口应用建立数据连接。',
148: '我在开发板运行 rfcomm -r watch 0 1 监听连接。手机串口应用连接后生成 /dev/rfcomm0，我让程序打开该设备文件进行读写，界面状态由等待连接切换为 Connected。',
150: '我在接收端拼接分段到达的 UTF-8 数据，处理换行后将文字显示到屏幕上，并为 send 按钮添加发送 hello 的回调。收发过程结合事件回调与发送队列进行，保持界面能够继续响应触摸。连接断开后，程序返回等待状态，重新连接后恢复收发。',
162: '我将游戏工坊划分为硬件接入、交互状态、界面绘制和游戏规则等模块。arcade/main.c 负责硬件初始化、触摸回调和定时更新；app.c 管理菜单与交互状态；render.c 绘制界面；engine.c 实现 2048 规则与提示；breaker.c 实现打砖块的关卡和碰撞；profile.c 保存成绩记录。五子棋使用独立的 lab6_gomoku 工程，我分别实现棋规、AI、交互、绘制和存档，再通过统一菜单组织三种游戏。',
163: '我编写配套脚本负责游戏之间的切换。从菜单选择五子棋后，脚本启动五子棋程序；退出对局后，再返回游戏工坊菜单。这样的组织方式便于复用原有五子棋模块，也使各游戏的逻辑相对独立。',
167: '我复用前面实验的显示与触摸接口，让游戏统一使用 1024×600、32 位 RGB framebuffer，并按实际 line_length 更新显存。触摸坐标经映射后传递给交互层，由当前主触点控制按钮和滑动。菜单、2048 等页面在状态变化时重绘，打砖块通过定时事件持续更新，中文显示则复用实验三的字体绘制功能。',
169: '我将五子棋棋盘设为 15×15，采用自由规则，横、竖和两条斜线方向连续五子或以上获胜。程序支持人机对战、同屏双人、悔棋、重新开始、最后落子提示及保存退出。每次触摸按下只落一子，已经占用的位置不能落子。',
170: '我为五子棋 AI 设计了先处理直接胜负、再搜索候选点的决策流程。程序先检查自己是否能够一步获胜，以及对手是否存在需要立即阻挡的威胁，再对已有棋子附近的候选点评分。评分考虑连子长度、两端开放情况和五格窗口中的断续棋形，并对得分较高的候选点进一步搜索对手的应答。我把搜索拆成定时任务分步完成，使电脑思考时界面仍能响应操作。',
171: '我用对局模式和完整落子序列保存五子棋进度，重新打开时按顺序回放落子，恢复棋盘与当前回合。这样可以在退出程序后继续之前的对局。',
173: '我用 4×4 数组表示 2048 棋盘，将四个滑动方向转换为逐行处理次序，再按“压紧—相邻同值合并—补零”完成移动。每个格子在一次移动中只参与一次合并，例如 [2,2,2,2] 向左移动后得到 [4,4,0,0]，两次合并共增加 8 分。仅在棋盘发生有效变化后生成新格子，生成 2 和 4 的概率分别为 90% 和 10%。',
174: '我为 2048 添加撤销和提示功能。撤销时恢复上一步的棋盘、分数和随机数状态；提示时比较四个移动方向，结合随机落点及下一步选择，按照空格数量、相邻数值差和大数靠角等因素评分，给出建议方向。有效移动后的格子边框短暂高亮，便于观察棋盘变化。',
178: '我设计了三个逐步变化的关卡：第一关使用普通砖阵，第二关采用交错阵型，第三关引入需击打两次的耐打砖。触摸拖动控制挡板，松手发球；程序处理球与边界、挡板和砖块的碰撞，维护得分、生命、当前关卡和过关状态。过关后通过“进入下一关”继续，保留当前分数与生命。',
180: '我将打砖块的物理计算设为 1/240 秒固定时间步，画面由 20 毫秒定时器驱动。每一步检测球与边界、挡板和砖块的碰撞，并更新球拖尾和粒子效果。将物理计算与画面更新分开，有助于保持运动与碰撞效果稳定。',
182: '我为游戏工坊加入 2048 最高分、打砖块最高分、最佳连击和五枚挑战徽章的记录功能，重新启动后可继续查看。2048 与打砖块记录历史成绩，五子棋则单独保存完整对局，便于续玩。',
200: '结合自己的接线经历，我建议在实验开始前提供更直观的硬件接线说明，将开发板供电、显示屏供电、HDMI 视频线、触摸 USB 数据线和网络连接分别标注，并配上接口照片。本次实验中，显示正常但触摸无响应的问题，最终通过重新连接屏幕与开发板之间的 USB 数据线得到解决。如果指导材料能够明确每根线的用途，并列出正常连接时的现象，可以减少初次使用开发板时的摸索时间。',
}

OUT.mkdir(exist_ok=True)
(OUT/'qa').mkdir(exist_ok=True)
if DST.exists():
    raise SystemExit('destination already exists')
with ZipFile(SRC) as z:
    entries = [(i,z.read(i.filename)) for i in z.infolist()]
doc=E.fromstring(dict((i.filename,b) for i,b in entries)['word/document.xml'])
ps=doc.xpath('//w:p',namespaces=NS)
assert len(ps)==206
changes=[]
for index,new in replacements.items():
    p=ps[index]
    nodes=p.xpath('.//w:t',namespaces=NS)
    old=''.join(n.text or '' for n in nodes)
    assert nodes and old
    nodes[0].text=new
    nodes[0].set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    for node in nodes[1:]:
        node.getparent().remove(node)
    changes.append({'paragraph_index':index,'before':old,'after':new})
xml=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(DST,'w') as z:
    for info,data in entries:
        z.writestr(info,xml if info.filename=='word/document.xml' else data)
with ZipFile(SRC) as a,ZipFile(DST) as b:
    media=[n for n in a.namelist() if n.startswith('word/media/')]
    assert all(a.read(n)==b.read(n) for n in media)
(OUT/'第一人称修改对照.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'正文.txt').write_text('\n\n'.join(''.join(p.xpath('.//w:t/text()',namespaces=NS)) for p in ps[67:]),encoding='utf-8')
print(json.dumps({'destination':str(DST),'changed_paragraphs':len(changes),'media_preserved':len(media),'sha256':sha256(DST.read_bytes()).hexdigest()},ensure_ascii=False))
