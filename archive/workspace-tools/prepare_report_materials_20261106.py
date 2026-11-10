"""Assemble copy-ready report text and traceable existing evidence, without editing Word."""
from pathlib import Path
import csv
import hashlib
import html
import json
import re
import shutil
import zipfile
from html.parser import HTMLParser
from urllib.parse import quote, unquote
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'manual-materials-20261106'
OUT.mkdir(parents=True, exist_ok=True)
manifest = []

def textfile(name, text):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + '\n', encoding='utf-8-sig')
    return p

def copy(source, destination, role, caption=''):
    src = ROOT / source
    dst = OUT / destination
    assert src.is_file(), src
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    digest = hashlib.sha256(dst.read_bytes()).hexdigest()
    assert digest == hashlib.sha256(src.read_bytes()).hexdigest()
    manifest.append({'file':destination,'source':str(src),'kind':role,'caption':caption,
                     'bytes':dst.stat().st_size,'sha256':digest})

chapters = [
('01-实验一-系统烧录.txt', '''1 实验一 系统烧录

1.1 实验要求

完成 Orange Pi 4 LTS 的 Linux 系统烧录和启动，建立电脑与开发板之间的连接，熟悉课程工程的编译、部署和运行方法，并在开发板上运行第一个应用程序。实验依据课程 PPT 第19—43页。

1.2 实验过程

（1）烧录系统与连接硬件
在 Windows 电脑上解压课程提供的 Orangepi4-lts_3.0.6_ubuntu_desktop_otg.img 镜像，使用 balenaEtcher 选择镜像和约64 GB的存储卡，完成写入及校验。出现“Flash Complete!”后取出存储卡，在开发板断电状态下将其插入卡槽，再连接开发板电源、显示屏电源和 HDMI，等待系统启动。

（2）建立远程连接
本实验主要采用网线连接电脑与开发板，通过 Windows PowerShell 中的 SSH 客户端登录。已用配置中，电脑以太网地址为192.168.137.1，开发板 eth0 地址为192.168.137.115。电脑将 WLAN 网络共享给连接开发板的以太网接口。调试过程中也曾使用手机热点连接，板端地址为192.168.43.160；该地址可能随热点重新分配，不作为固定地址。

在 PowerShell 中执行 ssh root@192.168.137.115，核对主机身份并输入密码。SSH 输入密码时不显示字符或星号，这是终端的正常行为。登录后出现 root@orangepi4-lts 提示符，说明后续命令在开发板上执行。

（3）编译并运行程序
将课程工程放在开发板独立工作目录，使用板端 GCC 原生编译，将 common/rules.mk 的编译器设为 gcc。进入 lab1 目录执行 make，再进入 out 目录运行 ./lab1。随后执行 echo $? 检查返回值。

1.3 实验结果

balenaEtcher 显示烧录完成；开发板成功启动 Orange Pi 3.0.6 Focal 系统，内核版本为 Linux 5.10.43，体系结构为 aarch64。SSH 登录后运行 lab1，终端输出“Hello embedded linux!”，返回值为0。系统烧录、远程连接和首个程序运行均完成，实验一已由助教验收。

【插图位置】图1-1 balenaEtcher 烧录并校验完成。
【插图位置】图1-2 通过 PowerShell 登录开发板并运行 lab1，程序正常退出。
'''),
('02-实验二-图形界面基础.txt', '''2 实验二 图形界面基础

2.1 实验要求

理解 Linux framebuffer 的显示原理与内存映射方式，补全矩形和直线绘制函数，在屏幕上显示点、线和矩形，并理解软件双缓冲及更新区域的作用。实验依据课程 PPT 第44—52页。

2.2 实验过程

（1）初始化 framebuffer
程序打开 /dev/fb0，通过 ioctl 获取可见分辨率、像素格式和行跨度，再利用 mmap 将显存映射到进程地址空间。本次板测的可见分辨率为1024×600，每像素32位，虚拟分辨率为1280×720，line_length 为5120字节。因此，屏幕一行的实际跨度不能直接用1024×4代替。

（2）补全矩形绘制
fb_draw_rect 先检查宽高，使用较宽的整数类型计算矩形边界，再将绘制范围裁剪到屏幕内。对于完全位于屏幕外或裁剪后为空的区域直接返回；其余情况按行连续写入绘图缓冲。该方法避免越界访问，并利用连续内存访问完成颜色填充。

（3）补全直线绘制
fb_draw_line 选择变化较大的坐标轴为主轴，统一端点顺序后，使用整数误差累加确定每一步的像素坐标。对于主轴位于屏幕外的部分，先跳过不可见区间，同时保留对应误差相位；最终由画点函数处理像素边界。相同端点退化为一个点，水平线、竖直线和不同斜率的线段使用同一套流程。

（4）更新屏幕并运行测试
图形先写入内存中的绘图缓冲，记录被修改的区域，再调用 fb_update 按实际显存行跨度复制至 framebuffer。绘制前临时停止开发板图形桌面，避免桌面程序同时修改显存；该操作针对开发板，不影响笔记本的 Windows 桌面和 SSH 使用。

2.3 实验结果

实验二在开发板上编译和运行成功，保留日志中的画点、矩形和直线测试分别为1 ms、2 ms和2 ms，程序返回值为0。上述数字是该次程序测试阶段的整数毫秒计时，不代表每一个图元的单次调用耗时。实验二已由助教验收。

【结果表位置】表2-1 实验二运行记录：画点1 ms，矩形2 ms，直线2 ms，程序退出状态0。
【可补插图】图2-1 实验二基础图形显示结果。现有材料缺少单独的实验二结果截图；可补拍真实屏幕，或仅保留结果表和原始日志，不使用实验三图片冒充。
'''),
('03-实验三-图片文字显示与优化.txt', '''3 实验三 图片文字显示

3.1 实验要求

实现不透明 JPEG 图像、带透明度的 PNG 图像以及矢量字体的显示，正确处理颜色格式、透明度混合和 UTF-8 字符，运行综合图形测试并分析性能。实验依据课程 PPT 第53—64页。

3.2 实验过程

（1）图像和文字绘制
fb_image 保存图像格式、宽高、源图行跨度和像素数据。JPEG 作为不透明图像处理，PNG 按每个颜色通道进行前景色与背景色的 alpha 混合；alpha 为0时可跳过，alpha 为255时可直接写入。混合中采用整数运算，并保持原程序的取整规则，避免因近似算法导致像素差异。

字体由 FreeType 从 font.ttc 中提取。字符串按 UTF-8 字符字节数逐个推进，利用字形的 left、top 和 advance_x 确定绘制位置。字模作为透明度图像与指定颜色组合后叠加到背景。实际板测曾发现小字号单色 MONO 字模不能直接按8位灰度读取，后续板测修正版补充了相应格式转换。

（2）优化重复工作
首先对重复字体建立缓存，减少相同字符和字号的重复解析，并保留容量限制和回退路径。随后针对不同图像格式建立专用绘制路径，处理完全透明和完全不透明的区间；对重复透明图像绘制建立目标行索引，减少无效的逐行筛选，并保持同一目标像素的混合顺序。部分像素处理结合 ARM NEON 和按行并行，几何绘制则保留边界检查与屏内快速路径。

对于不透明图像的批量绘制，还研究了遮挡消除与覆盖检测：只有在能够证明前面的写入最终完全被覆盖时，才消除对最终画面无影响的重复写入。该优化通过显式批量接口实现，必须同时说明测试接口和可观察语义的变化，不能把它说成对任意即时绘图调用都完全等价的加速。

矩形部分在真实板测后保留了较快的直接绘制实现，没有仅凭离线理论判断选择复杂方案。各版本原件和候选版本分开保留，优化正确性通过像素比较、边界检查、真实字体检查和完整画面回放验证。

（3）测试方法与比较范围
课程程序分别统计画点、矩形、直线、JPEG、PNG、独立字模和文本阶段，再将整数毫秒结果相加。该总数不包含图像解码、屏幕刷新、等待和程序启动等全部耗时，不是端到端显示延迟。批量版本须单独标注；CPU调频、绑核、线程数、编译选项也会影响成绩。

2026年10月19日同轮条件下，基线三轮为47、46、47 ms，v9为27、27、25 ms，v10为28、25、28 ms。随后在另一组试验中将矩形恢复为较快的直接绘制路径，保留其余优化与字模修复，测得22、21、17 ms。不能将两组试验当作随机交替的严格消融，也不能将早期155 ms到17 ms的全部差异归因于单一算法。

3.3 实验结果

功能显示方面，开发板正常显示羊驼 JPEG、绿色透明 PNG、红色“嵌”字和紫色《静夜思》。早期在保留课程绘制流程的条件下，缓存及 -O3 版本三轮为160、155、173 ms，中位数为160 ms。

采用后续批量优化与直接矩形组合的实测三轮为22、21、17 ms，中位数为21 ms，最低值为17 ms；17 ms的原始日志及成绩截图均已保存。该轮分项为画点0、矩形4、直线4、JPEG 1、PNG 6、字模1、文本1 ms，总计17 ms。0 ms表示整数毫秒计时未跨越刻度，不表示没有执行工作。

2026年11月5日再次运行已部署版本，三轮分别为58、19、20 ms，中位数为20 ms。第一轮文字阶段为41 ms，后两轮均为1 ms，原因尚未确定，因此完整保留首轮，未将其删除后再计算成绩。当前可以确认已获得17 ms的历史单次结果和20 ms的最新三轮中位数，不能表述为“每次均稳定17 ms”。

【插图位置】图3-1 JPEG、透明 PNG 与中文文字的真实显示结果。
【插图位置】图3-2 批量优化候选的17 ms开发板原始成绩截图。
【插图位置】图3-3 2026年11月5日第三轮20 ms成绩截图。
【表格位置】表3-1 各批次三轮完整耗时与计时范围，见配套“实验三测速表.csv”。
'''),
('04-实验四-多点触摸.txt', '''4 实验四 多点触摸开发

4.1 实验要求

读取 Linux Input Event 和多点触摸协议中的触点信息，在 LCD 上绘制触摸轨迹。本实验选择课程 PPT 第72页的连续轨迹方案：不同手指使用不同颜色，线条连续且具有明显宽度，并提供清屏按钮。相关原理见 PPT 第65—72页。

4.2 实验过程

（1）识别触摸设备
通过 /proc/bus/input/devices 和 /dev/input/eventN 查找触摸屏。实测设备为 wch.cn USB2IIC_CTP_CONTROL。节点编号可能随插拔而改变，不能永久写死为某个 eventN。屏幕通过 HDMI 接收图像，通过独立 USB 数据线向开发板发送触摸事件。

（2）解析多点事件
程序按 Protocol B 维护各 slot 的跟踪编号、坐标和按压状态，并在同步事件到来时形成按下、移动、抬起等应用事件。触摸原始坐标范围为0—4096，映射到1024×600显示坐标。驱动报告6个slot，课程应用处理其中0—4共五个触点。

（3）绘制连续轨迹与清屏
为五个触点分配固定的红、蓝、绿、紫、橙颜色，分别保存上一次坐标。在相邻采样点间插值并绘制9像素笔刷，使快速移动时仍可形成连续粗线。手指抬起后清除旧轨迹起点，防止下次触摸与旧位置错误连接。

右上角设置清屏按钮。触发清屏时清除画布，并要求当时仍按住的手指先抬起后再重新落下，以免立即在空白画布上继续画线。顶部色块用于说明触点配色，不承担单指手动选色功能。

4.3 实验结果

真实开发板测试中，单指快速画线正常，五指同时拖动形成五条不同颜色、连续且较粗的轨迹，清屏按钮有效。用户已逐项确认上述现象；事件统计记录最大同时触点数为5，五个触点均有事件，记录到24次清屏触发。保留了实际画布截图、运行日志和事件统计文件。

【插图位置】图4-1 五指画板的五种颜色连续轨迹。
【插图位置】图4-2 空白画板及清屏按钮界面（程序初始状态截图，不单独证明清屏过程）。
'''),
('05-实验五-蓝牙通讯.txt', '''5 实验五 蓝牙通讯

5.1 实验要求

配置 Linux 蓝牙设备，理解配对、服务发现、RFCOMM 连接与应用数据收发的关系，通过蓝牙串口实现双向通信。按照课程 PPT 第85页给出的方案，本实验使用安卓手机与开发板进行通信。实验整体依据 PPT 第73—87页。

5.2 实验过程

（1）准备蓝牙服务与手机应用
开发板使用 BlueZ 提供经典蓝牙功能，检查适配器状态、可发现/可配对设置和串口服务。手机使用图标带“SPP”的蓝牙串口应用。先在系统蓝牙设置中完成配对，再到串口应用中连接开发板；系统显示“已配对”并不代表应用数据通道已经建立。

（2）建立 RFCOMM 数据通道
在开发板保持 rfcomm -r watch 0 1 监听，手机串口应用连接后创建 /dev/rfcomm0。程序以该设备文件进行读写。设备节点尚不存在时显示等待状态并定时重试，成功打开后切换为 Connected。

（3）收发文字与处理断线
接收端处理 UTF-8 分片和行结束符，将完整文字显示到 framebuffer。发送端通过屏幕 send 按钮发送 hello，维护发送队列并处理部分写入和暂时不可写的情况。每次回调限制读写工作量，使触摸和定时事件仍可得到处理。遇到断线或读写错误时关闭旧描述符并等待重新连接；断线前尚未发送的残留不会自动带入下一次会话。

（4）逐项验证
先进行伪终端自动测试，检查文本处理、设备重建和错误恢复；再使用真实手机完成无线双向收发。实际测试中手机发送“你好，orange pi！”，开发板显示收到的文字；点击开发板 send，手机接收 hello。最后在手机应用内断开并重新连接，再次检查两个方向的收发。

5.3 实验结果

真实蓝牙连接建立后，开发板显示 Connected，并正确显示手机发来的中文文字。日志记录 Bluetooth RX 和发送队列信息，用户同时确认手机实际收到了 hello。因此双向成功的结论由板端接收日志、真实界面和手机端反馈共同支撑，而非只依据“TX queued”。

用户随后确认“重连后双向收发正常”，说明实际无线断开重连后功能恢复。重连结果已有用户实物反馈，但尚未另存该次重连的独立截图或日志。现有双向通信图及原始日志可用于报告，手机侧接收画面可在提交前补拍。

【插图位置】图5-1 开发板蓝牙串口已连接并收到中文消息。
【可补插图】图5-2 安卓蓝牙串口应用收到开发板发送的 hello。
'''),
('06-实验六-最新游戏工坊v2.txt', '''6 实验六 综合实验——橙派游戏工坊 v2

6.1 实验要求

课程 PPT 第88页允许综合运用前面实验的技术，设计多开发板通信程序或功能较复杂的单机程序。本实验选择后者，在 Orange Pi 4 LTS 上实现“橙派游戏工坊 v2”，整合五子棋、2048 和三关打砖块，并提供触摸交互、中文界面、挑战纪录和存档功能。该项目复用 framebuffer 绘图、字体显示、触摸事件和任务调度，不将蓝牙联机或语音识别列为本版已实现功能。

6.2 实验过程

（1）整体设计与模块划分
游戏工坊以统一菜单组织三种游戏。arcade/main.c 负责硬件初始化、触摸回调、定时更新和退出处理；app.c 负责菜单与交互状态；render.c 负责界面绘制；engine.c 实现2048规则与提示；breaker.c 实现打砖块的关卡、碰撞、道具和效果；profile.c 处理挑战纪录。五子棋继续使用独立的 lab6_gomoku 工程，包含棋规、AI、交互、绘制、会话和存储模块。因此，本实验的扩展涉及多个模块，而不是只修改 main 函数。

板端通过配套脚本管理合集与五子棋进程：从菜单选择五子棋时，以约定退出状态交给脚本启动五子棋；五子棋正常退出后回到合集。脚本使用单实例锁，避免多个游戏同时操作显存。原课程语音识别示例、原版五子棋和游戏工坊v1均保留，新版位于独立目录。

（2）统一显示与触摸交互
程序检查可见 framebuffer 为1024×600、32位RGB格式，并使用实际 line_length 更新屏幕。触摸模块读取多点协议，将坐标映射到屏幕；交互层一次只接受一个主触点，避免第二根手指干扰当前滑动或误触按钮。菜单与静态页面在状态变化后重绘，打砖块随定时事件持续更新。中文显示使用课程字体和板测修正后的字模转换。

（3）五子棋模块
棋盘为15×15，采用自由规则，横、竖和两条斜线方向连续五子或以上获胜。程序支持人机对战、同屏双人、悔棋、重新开始、最后落子提示及保存退出。每次触摸按下只落一子，已经占用的位置不能落子。

AI先检查当前一手获胜机会和对手的一手威胁，再对已有棋子附近的候选点进行评分。评分结合连子长度、两端开放情况和五格窗口内的断续威胁，再对受限数量的候选和对手应答进行前瞻。搜索按定时任务分步推进，降低长时间阻塞触摸处理的风险。该AI是启发式搜索，不宣称必胜，也不以一次胜负说明棋力上限。

五子棋保存完整落子序列和模式，并通过回放与校验恢复局面。存档采用临时文件写入、同步和替换机制；异常记录保留并提示，避免直接覆盖。新版使用独立存档文件，与此前演示的五子棋存档区分。

（4）2048模块
将棋盘表示为4×4数组，滑动方向转换为逐行处理次序，每行按“压紧—相邻同值合并—补零”完成移动，单次移动不重复合并刚生成的格子。仅在棋盘发生有效变化后生成新格子，生成2和4的概率分别为90%和10%。

撤销功能恢复上一步的棋盘、分数及随机数状态，因而撤销后重复同一操作不会借助重新抽取随机数改变结果。提示功能枚举四个方向、随机落点及下一步选择，按空格数量、相邻数值差和大数靠角等因素计算建议；提示只提供方向，不自动执行，也不保证最终达到2048。有效移动后的格子边框短暂高亮。

（5）三关打砖块模块
第一关使用普通砖阵，第二关采用交错阵型，第三关引入需击打两次的耐打砖。触摸拖动控制挡板，松手发球；程序处理球与边界、挡板和砖块的碰撞，维护得分、生命、当前关卡和过关状态。过关后通过“进入下一关”继续，保留当前分数与生命。

连续击破砖块提高连击得分，碰到挡板或漏球时重置连击。每累计击破五块砖且没有活动道具时，依次产生“宽”“缓”“盾”三种道具；挡板接住后分别使挡板加宽10秒、球速降至68%并持续8秒，或抵挡一次漏球。道具需要实际接住才生效，漏球与切关按规则清理状态。

物理更新采用1/240秒的固定子步，并限制单次补算时间不超过100毫秒，以减少不稳定的时间步对碰撞的影响。画面采用20毫秒定时器驱动，但这只表示目标调度间隔，不等于已经测得50 FPS。球拖尾最多12点，粒子最多64个；每个物理子步检查砖块和受限粒子集合，工作量随砖块数与粒子数线性变化。

（6）挑战纪录与可靠性
合集保存2048最高分、打砖块最高分、最佳连击和五枚挑战徽章。纪录文件包含版本、数值范围和校验信息，采用临时文件、写入同步、原子替换及目录同步；损坏文件不会被静默覆盖。这里保存的是挑战纪录，2048与打砖块局内进度仅保存在当前进程内；板端切入五子棋后再返回时，这两种小游戏重新开局。五子棋对局使用独立的完整存档。

（7）验证流程
先在电脑端验证规则、输入状态、图形边界和记录文件，再在开发板进行 ARM 原生编译及自动测试。独立打包首次上板时发现缺少课程任务调度文件 common/task.c，构建脚本已补充从课程工程复制该文件；测试代码同时检查 fread 返回值，以适配板端编译器的严格警告检查。修复后两个程序均成功构建，原有版本不覆盖。

6.3 实验结果

2026年11月5日，游戏工坊v2在开发板完成编译，板端自动测试通过，包括8000次生成的2048移动检查、200个提示局面检查、100000帧合成物理压力测试及Linux文件读写测试。合成物理帧用于检查状态和边界，不是实际显示帧率测量。

重新接好屏幕到开发板的USB数据线后，系统识别到 wch.cn USB2IIC_CTP_CONTROL，触摸事件节点为 /dev/input/event2，多点触摸驱动已加载。运行合集后，真实 framebuffer 截图显示打砖块第1/3关、350分、2条生命，以及砖阵、挡板、球和中文菜单。该图来自真实开发板，可证明新版已启动并进入游戏运行状态。

复用的五子棋模块此前已完成真实落子、人机应答和悔棋体验，用户确认上述操作正常，并保留实际对局日志。游戏工坊v2的菜单、2048及道具展示另有电脑模拟图片，这些仅用于说明功能设计，不作为对应板端操作已通过的证据。

截至本次整理，材料中尚缺新版2048滑动、撤销和提示、打砖块暂停与通关、记录重启恢复、合集与五子棋往返等完整逐项实物反馈，因此当前结果写为“板端构建和自动测试通过，已有真实打砖块运行截图”。后续按实际操作补充测试结果和助教验收记录。

【插图位置】图6-1 游戏工坊v2统一菜单（电脑模拟预览，用于界面设计说明）。
【插图位置】图6-2 五子棋模块此前的开发板初始界面（旧模块实测，不代表新版合集切换已验收）。
【插图位置】图6-3 2048的撤销与提示界面（电脑模拟预览）。
【插图位置】图6-4 游戏工坊v2打砖块真实运行画面：第1关、350分、2条生命。
【可选插图】图6-5 打砖块道具与视觉效果设计（电脑模拟测试场景，非实测通关成绩）。
【表格位置】表6-1 功能、验证证据与待补项目，见“实验六验证状态.csv”。
'''),
('07-实验总结与建议.txt', '''7 实验总结与建议

7.1 实验总结

六个实验围绕同一块Orange Pi开发板逐步展开：先完成系统烧录和远程连接，再实现基础图形、图片文字、多点触摸与蓝牙通信，最后将显示、输入、状态管理和文件存储组合为游戏工坊。通过这一过程，实验从单一函数实现扩展到多个模块协作的完整应用。

实际调试表明，硬件连接、操作系统接口和应用逻辑应分层检查。例如，HDMI能够正常显示并不意味着触摸USB已连接；蓝牙配对成功不等于SPP数据通道已建立；SSH连接失败需要区分网线、IP地址和网络共享问题。按设备枚举、接口状态、运行日志和界面现象逐项定位，比反复重启更有针对性。

实验三的优化也说明，性能结论必须与测量口径绑定。缓存、格式专用处理、减少无效遍历以及批量覆盖消除能够减少重复工作，但需要保留像素级正确性检查；编译选项、CPU配置和接口变化会影响可比性。报告同时保留完整三轮、最低值和中位数，避免只展示最好的一次而忽略波动。

综合实验中，菜单、不同游戏、存档和记录之间存在状态切换，仅验证单个算法并不足以证明整套程序可用。因此将电脑自动测试、板端编译、非交互测试、真实触摸运行和现场验收分开记录。原版、候选版本及实测材料分开保存，便于复现与回退。

7.2 实验建议

建议在实验开始前提供更直观的硬件接线说明，将开发板供电、显示屏供电、HDMI 视频线、触摸 USB 数据线和网络连接分别标注，并配上接口照片。本次实验中，显示正常但触摸无响应的问题，最终通过重新连接屏幕与开发板之间的 USB 数据线得到解决。如果指导材料能够明确每根线的用途，并列出正常连接时的现象，可以减少初次使用开发板时的摸索时间。

在开发环境配置方面，建议整理一份从系统烧录到运行首个程序的快速操作单，集中说明镜像版本、编译方式、工程目录、依赖库和常用命令。对于 Windows 网络共享、SSH 登录以及手机热点连接，可以分别给出检查步骤。例如，先检查网卡是否连接，再核对电脑与开发板的 IP 地址，最后检查 SSH 服务。还可以补充密码输入不回显、开发板时钟未校准、触摸设备节点随插拔变化等常见现象，使学生能够判断哪些属于正常行为，哪些需要进一步排查。

对于图形显示和触摸实验，建议在基础示例之外增加边界测试说明。图形绘制可以覆盖部分越界的矩形、不同方向的直线、透明图像以及不同字号的中文；触摸测试可以覆盖快速移动、多指同时操作、抬起后重新落下和清屏等情况。同时，应强调屏幕可见分辨率、虚拟分辨率与显存行跨度之间的区别，帮助学生理解程序在普通测试中能够运行，却可能在边缘位置或实际硬件上出现问题的原因。

性能测试方面，建议统一测试素材、循环次数、编译选项和计时范围，并明确缓存、并行处理及批量绘制等优化方式的比较条件。测试结果可以同时记录各阶段耗时、完整多轮结果、最小值和中位数，保留首次运行与后续运行之间的差异。当某次结果明显偏高时，应结合日志分析原因。这样既能提高不同实现之间的可比性，也能引导学生区分算法改进、编译优化和硬件运行状态带来的影响。

对于蓝牙通信实验，建议将检查流程拆分为设备发现、系统配对、SPP 应用连接、RFCOMM 设备建立和双向收发几个阶段，并为每个阶段列出预期现象与常见错误。验收时除正常收发外，还可以加入断开后重新连接的测试，观察程序是否能够恢复通信。通过这种分阶段的方式，学生更容易理解蓝牙协议与应用程序之间的关系，也能更准确地定位“已经配对但无法通信”等问题。

综合实验建议进一步明确功能完整性、交互体验、算法设计和异常处理等方面的评价要求。不同项目可以有不同的实现方向，但都应说明模块划分、操作流程、核心技术及实际测试结果。报告要求也可以提前列出需要保留的截图、日志和数据，并提供一份简明的提交检查表。这样学生在实验过程中就能及时收集材料，将更多精力用于程序设计、调试和结果分析。

【填写提示】以上总结基于已保存的调试过程。提交前可补充自己印象最深的一次排障或设计取舍；未亲自发生的经历不要补写。
''')]

for name,body in chapters:
    textfile('正文/'+name,body)
textfile('01-报告正文-按模板逐节粘贴.txt','\n\n' + '\n\n'.join(body.strip() for _,body in chapters))

images = [
('evidence/lab1/01-etcher-flash-complete.png','图片/真实记录/图1-1-烧录完成.png','电脑真实截图','图1-1 balenaEtcher 完成镜像写入及校验。'),
('evidence/lab1/04-lab1-ssh-run-success.png','图片/真实记录/图1-2-SSH运行lab1.png','电脑真实截图','图1-2 PowerShell 经SSH连接开发板，lab1输出Hello embedded linux!，返回值0。'),
('evidence/lab3/lab3-cache.png','图片/真实记录/图3-1-图片文字显示.png','真实开发板显存截图','图3-1 JPEG、透明PNG、独立字模和中文文本显示结果。'),
('evidence/board-20261019/17ms重点留存/17ms-开发板原始成绩截图.png','图片/真实记录/图3-2-历史17ms.png','真实开发板显存截图','图3-2 2026-10-19批量优化候选第三轮17 ms成绩；同组三轮22、21、17 ms。'),
('evidence/board-20261105/lab3/20261019-142918-954174/screen.png','图片/真实记录/图3-3-最新20ms.png','真实开发板显存截图','图3-3 2026-11-05第三轮20 ms成绩；同组三轮58、19、20 ms。开发板时钟未校准。'),
('evidence/lab4/drawing.png','图片/真实记录/图4-1-五指五色轨迹.png','真实开发板显存截图','图4-1 五指画板显示五种颜色的连续粗轨迹。同时五指结论另由事件日志及用户确认支持。'),
('evidence/lab4/initial.png','图片/真实记录/图4-2-画板初始界面.png','真实开发板显存截图','图4-2 画板初始空白界面及清屏按钮；此图不是清屏操作过程录像。'),
('evidence/lab5-board-20261019/双向通信实测.png','图片/真实记录/图5-1-蓝牙收到中文.png','真实开发板显存截图','图5-1 蓝牙SPP连接后，开发板显示Connected及手机发送的中文消息。'),
('evidence/lab6-board-20261019/gomoku-first-run.png','图片/真实记录/图6-2-五子棋旧模块实测.png','旧版模块真实开发板显存截图','图6-2 复用五子棋模块的开发板初始界面；实际落子和AI应答另见对局日志。'),
('evidence/board-20261105/lab6-breakout-board.png','图片/真实记录/图6-4-最新游戏工坊板测.png','最新版真实开发板显存截图','图6-4 2026-11-05游戏工坊v2打砖块真实运行：第1/3关、350分、2条生命。'),
('lab6-arcade-v2/preview/menu.png','图片/电脑模拟-仅设计说明/图6-1-菜单-电脑模拟.png','电脑模拟','图6-1 游戏工坊v2统一菜单的电脑模拟预览，不是开发板实测图。'),
('lab6-arcade-v2/preview/2048.png','图片/电脑模拟-仅设计说明/图6-3-2048-电脑模拟.png','电脑模拟','图6-3 2048电脑模拟界面，展示撤销及提示设计；图中局面为测试场景。'),
('lab6-arcade-v2/preview/effects.png','图片/电脑模拟-仅设计说明/图6-5-道具效果-电脑模拟.png','电脑模拟','图6-5 道具与粒子效果的电脑模拟测试场景，不表示实际通过该关卡。'),
('lab6-arcade-v2/preview/records.png','图片/电脑模拟-仅设计说明/图6-6-挑战纪录-电脑模拟.png','电脑模拟','图6-6 挑战纪录及徽章的电脑模拟测试场景；显示分数不是本次实际取得的成绩。')]
for args in images: copy(*args)
textfile('02-配图清单与图注.txt','\n\n'.join(f'{dest}\n{caption}\n证据类型：{role}\n原始来源：{src}' for src,dest,role,caption in images))

logs = [
('evidence/lab1/03-user-ssh-verification.txt','日志/实验一-SSH运行确认.txt'),
('evidence/lab1/environment.json','日志/实验一-环境.json'),
('evidence/lab2/run.log','日志/实验二-运行.log'),
('evidence/lab2/status.json','日志/实验二-验收状态.json'),
('evidence/lab3/results.json','日志/实验三-早期完整三轮.json'),
('evidence/lab3/o3-2.log','日志/实验三-早期155ms.log'),
('evidence/board-20261019/17ms重点留存/17ms-第三轮原始日志.log','日志/实验三-历史17ms.log'),
('evidence/board-20261019/17ms重点留存/三轮完整结果及编译参数.json','日志/实验三-历史完整三轮与编译参数.json'),
('evidence/board-20261019/17ms重点留存/测试说明.txt','日志/实验三-17ms测试说明.txt'),
('evidence/board-20261105/lab3-three-runs.log','日志/实验三-20261105完整三轮.log'),
('evidence/board-20261105/lab3-metrics.json','日志/实验三-20261105结构化数据.json'),
('evidence/lab4/event-summary.json','日志/实验四-五指事件统计.json'),
('evidence/lab4/run-snapshot.log','日志/实验四-原始触摸事件.log'),
('evidence/lab5-board-20261019/实测确认.txt','日志/实验五-双向收发与真实重连确认.txt'),
('evidence/lab5-board-20261019/run.log','日志/实验五-真实收发.log'),
('evidence/lab5-board-20261019/serial-test.log','日志/实验五-伪终端测试.log'),
('evidence/lab6-board-20261019/实际对局日志.log','日志/实验六-五子棋旧模块实际对局.log'),
('evidence/lab6-board-20261019/用户实测确认.txt','日志/实验六-五子棋旧模块操作确认.txt'),
('evidence/board-20261105/build-v2.log','日志/实验六-最新工坊ARM构建与板端自动测试.log'),
('evidence/board-20261105/session.json','日志/实验六-20261105实测状态.json'),
('evidence/board-20261105/board-metadata.json','日志/实验六-20261105设备识别与二进制哈希.json'),
('lab6-arcade-v2/test-results/result.json','日志/实验六-20261030电脑离线测试-历史.json'),
]
for src,dst in logs:copy(src,dst,'原始记录副本')
copy('resources/lab6-arcade-v2-board-source.tgz','代码附件/实验六-游戏工坊v2-开发板源码包.tgz','20261105修正后的源码准备包')
copy('resources/lab6-arcade-v2-offline.zip','代码附件/实验六-游戏工坊v2-电脑试玩包.zip','Windows离线试玩包')
copy('resources/lab6-arcade-v2-packages.json','代码附件/原始包校验值.json','源码包与试玩包的原始校验记录')

selected_sources = [
('lab2-prepared/common/graphic.c','代码附件/选读源码/实验二/graphic.c'),
('lab3-optimized-v10-directrect-prepared/common/graphic.c','代码附件/选读源码/实验三/graphic.c'),
('lab4-prepared/lab4/main.c','代码附件/选读源码/实验四/main.c'),
('lab5-boardfix-prepared/lab5_bt/main.c','代码附件/选读源码/实验五/main.c')]
for src,dst in selected_sources:
    if (ROOT/src).is_file():copy(src,dst,'源码选读副本-具体板测版本以日志哈希为准')
for folder in ['arcade','lab6_gomoku']:
    for p in sorted((ROOT/'lab6-arcade-v2'/folder).glob('*')):
        if p.suffix in ['.c','.h'] or p.name=='Makefile':
            copy(p.relative_to(ROOT).as_posix(),f'代码附件/选读源码/实验六/{folder}/{p.name}','游戏工坊v2当前源码副本')

textfile('03-使用方法与排版.txt', '''使用本材料包填写自己的报告

一、怎么用
1. 打开原来的“嵌入式系统实验报告模板.docx”，保留封面、页眉、页脚、目录和标题样式。
2. 打开“01-报告正文-按模板逐节粘贴.txt”，也可按“正文”目录中的单章文件复制。每章均对应模板的x.1实验要求、x.2实验过程、x.3实验结果；第七章为总结与建议。
3. 将正文粘贴到相应标题下，选择“只保留文本”，继承模板正文样式，不要把材料中的章节标题重复粘贴到已有标题下。
4. 按“02-配图清单与图注.txt”插入图片。完成插图后删除正文中所有【插图位置】【可补插图】【表格位置】【填写提示】等编辑标记。
5. 补齐姓名、学号、专业、班级、联系方式、实际实验日期与已获确认的验收信息。现有材料只明确记录实验一、二助教验收通过，其余若已验收，由你补充真实结论。
6. 最后更新目录和图号，检查分页后再导出PDF。本材料包是文本与证据，不是替你填好的Word报告。

二、模板现有格式（依据先前读取的用户模板样式，不是新编的课程规定）
正文：中文宋体，西文Times New Roman，12磅（小四），两端对齐；正文样段为1.5倍行距、首行缩进21磅。直接沿用模板的正文段落格式最稳妥。
一级标题：中文黑体，西文Arial，16磅（三号），居中，段前/后24磅，模板设章前分页。
二级标题：中文黑体，西文Arial，14磅（四号），左对齐，段前/后12磅。
图题：优先沿用模板已有图题样式；没有时可统一宋体、居中，字号与正文协调。这一条是排版建议，未从课程PPT找到强制字号要求。
目录：使用Word自动目录更新，不把参考报告页码手工照搬。截图保持原始比例，不拉伸，不修改成绩。

三、本次报告口径
实验六以“橙派游戏工坊v2”为主线：五子棋、2048、三关打砖块、道具、挑战纪录。旧五子棋作为复用模块介绍，不把实验六仍写成只有main函数或只有五子棋。
真实截图位于“图片/真实记录”；电脑模拟图位于“图片/电脑模拟-仅设计说明”。模拟图可用于6.2的设计说明，图注必须保留“电脑模拟”；不要移到6.3冒充板测。
17 ms是历史最好一次，2026-11-05三轮为58/19/20 ms。第一轮不得隐藏。155 ms只有该次原始日志，既有173 ms截图不能改称155 ms。
板上日期未校准，2026-11-05原始文件可能含20261019，实验一日志还出现2022年时间；报告以电脑记录的真实操作日期为准，不改写原始日志。

四、参考
章节结构参考用户指定的nivag8899/HUST-Embedded-System往届报告；具体内容依据当期PPT、本项目源码及实际记录重新组织。没有沿用参考作者姓名、学号、测试结果或蓝牙联机经历。
''')

textfile('04-实验六操作与答辩要点.txt', '''橙派游戏工坊 v2：操作与说明材料

【接板后的入口】
以下地址和目录是2026-11-05最后验证值，本次材料整理没有重新连接开发板。
电脑PowerShell：ssh root@192.168.137.115
登录后先检查：ip -4 -br addr；lsusb；cat /proc/bus/input/devices；fbset -i。
应确认触摸屏USB接在开发板上、屏幕可见1024×600且32位。event2是上次节点，不保证每次相同。
检查已有游戏进程：pgrep -af 'lab6_arcade|lab6_gomoku'。如果已经在运行，直接操作屏幕，不重复启动。
当前部署目录：/root/acceptance-20261105-9d5DtL/lab6-arcade-v2
进入该目录后：bash run-on-board.sh
自动识别失败时，再按实际触摸节点执行：bash run-on-board.sh --touch /dev/input/eventN
该脚本不负责把任意显示模式改为1024×600，显示不符时先恢复已验证的屏幕配置。
从源码包重建：解压到独立目录，运行 bash build-on-board.sh /root/course-project/lab-st-2026，再运行上述启动脚本。
退出合集后，脚本只恢复启动前正在运行的开发板桌面。上次桌面在启动前已停，退出不会自动重启；需要桌面时可执行 systemctl start display-manager。

【电脑离线试玩】
解压“代码附件/实验六-游戏工坊v2-电脑试玩包.zip”，在解压目录双击“电脑试玩.cmd”。保持整个目录完整，不能只拷贝EXE。鼠标模拟触摸，Esc返回菜单。它用于熟悉操作和展示界面，不替代开发板验收。

【推荐演示顺序：约3—5分钟】
1. 主菜单：指出三个游戏入口、最高分、最佳连击和徽章。
2. 2048：在棋盘上明显滑动一次，观察合并和得分；点撤销恢复，再点提示查看建议方向。
3. 打砖块：在左侧游戏区域按住拖动挡板，松开发球；点暂停/继续；有道具时让挡板接住观察变化。通关必须实际完成，没打通时不要展示模拟通关分数当成绩。
4. 五子棋：回菜单选择五子棋，轻点交叉点落黑子，观察电脑白子，试悔棋；保存退出返回合集。
5. 纪录：正常退出后重开，检查已产生的挑战纪录是否保留，并补存截图。

【可以讲清楚的实现要点】
模块分工：main负责调度；app负责交互状态；engine负责2048；breaker负责关卡物理；render负责显示；profile负责挑战纪录；五子棋有独立棋规、AI、会话与存储模块。
屏幕：显存行跨度5120字节，可见一行只显示1024像素；软件绘图缓冲与物理显存不能混用跨度。
触摸：Protocol B按slot维护状态，区分按下、移动、抬起；合集一次选择一个主触点处理手势。
2048：单行压紧合并，四个方向复用同一处理逻辑。撤销还原随机数状态；提示是受限前瞻加启发式评分，非必胜算法。
打砖块：固定物理子步1/240秒，最多补算100毫秒；碰撞、连击、关卡、道具是显式状态。20毫秒定时器不等于实测50 FPS。
记录：挑战纪录和五子棋完整存档分开。校验、临时文件、同步和原子替换用于降低写坏风险；突然断电恢复尚未实测。
五子棋：自由规则连续五子以上获胜；优先检查获胜/防守，再在受限候选上前瞻；不是神经网络模型，也没有实现本版蓝牙联机。
复杂度：2048移动对n×n棋盘遍历为O(n²)；当前n=4。打砖块每物理子步为O(B+P)，B是砖块数，P是有限粒子数。固定小棋盘和有限对象使开销有明确上限，但不能把整套软件笼统说成O(1)。

【准备好的代码入口】
代码附件/选读源码/实验六/arcade：main.c、app.c、engine.c、breaker.c、profile.c、render.c。
代码附件/选读源码/实验六/lab6_gomoku：main.c、gomoku.c、ai.c、app.c、render.c、session.c、storage.c。
完整源码准备包依赖课程工程提供common/task.c、common/external和out/font.ttc，不能当成任何Linux电脑上无依赖的独立安装包。
''')

textfile('05-提交前还需补什么.txt', '''提交前清单（截至2026-11-06，依据保存材料）

必填个人信息：姓名、学号、专业、班级、联系方式、实际实验日期。
验收信息：实验一、二已有用户明确确认助教验收；实验三至六未在本材料中新增助教已通过结论。若已现场验收，按真实结果补写。

优先补图：
1. 实验六v2开发板菜单和2048操作结果；目前对应图片只有电脑模拟预览。
2. 实验五手机实际收到hello的截图；板端收到中文已有图，双向和重连已有用户确认。
3. 实验二基础点线矩形屏幕图；现有运行日志和验收状态可直接引用。
4. 实验六从合集进入五子棋后的实际对局、正常退出重开后纪录恢复图。

按需要补测（先看实际是否已经做过，做过则补真实记录）：
2048滑动/撤销/提示；打砖块拖动、暂停/继续、道具效果、切关；合集与五子棋来回；正常退出后记录重读；退出时桌面恢复。
目前已保存：v2 ARM编译通过、板端规则/物理/文件测试通过、触摸设备识别、真实打砖块运行截图。尚未测真实FPS和突然断电恢复，不需要为写报告凭空补一个性能值。

截图不可替换的边界：
17ms图配历史三轮22/21/17；20ms图配2026-11-05三轮58/19/20。
模拟菜单、2048、道具和纪录只能标“电脑模拟”。旧五子棋图只表示复用模块已有实机基础。
原始日志中的TX queued只表示排队，手机收到的结论来自用户实际反馈。

文字最后检查：
删除所有【插图位置】等编辑提示；保留必要的测量条件和未完成项。
不要写每次稳定17ms、实测50FPS、已实现蓝牙联机、已验证断电不丢档、已全部通关等缺少证据的结论。
更新目录、图号、表号，检查页眉页脚和分页后自行导出PDF。
''')

textfile('06-连接排障简表.txt', '''连接与排障速查（历史已用配置；接板时重新核对）

硬件连接：开发板独立供电；屏幕独立供电；HDMI负责显示；屏幕触摸数据口→开发板USB-A负责触摸；笔记本与开发板之间网线负责SSH。
触摸USB不要误接到笔记本；开发板Type-C到笔记本的USB网络路线与屏幕触摸是两回事。

电脑端：检查以太网有连接，ipconfig中以太网通常为192.168.137.1；WLAN共享目标必须是连接开发板的以太网。
开发板：ip -4 -br addr确认eth0为UP且IP为192.168.137.115/24，注意192.168不能误写成192.16。
连接：Windows PowerShell输入ssh root@192.168.137.115，输入密码不显示字符。
有VPN导致路由干扰时，此前成功用法是ssh -b 192.168.137.1 root@192.168.137.115；先核对IP，不盲目关闭全部网络设置。
无网线时曾使用手机热点，板端192.168.43.160只是当次地址。先在板端或热点设备列表查新IP，再SSH。

能显示但不能触摸：lsusb中应有1a86:e5e3 USB2IIC_CTP_CONTROL；/proc/bus/input/devices中应有wch.cn触摸设备；event节点可能变化。2026-11-05重接屏幕到板子的USB数据线后恢复识别。
黑屏：分别检查屏幕电源、HDMI、开发板启动状态及桌面/应用是否运行。仅停止开发板桌面不等于开发板关机，也不影响笔记本Windows桌面。
实验五：手机配对后还需在SPP串口应用连接，rfcomm监听继续运行，出现/dev/rfcomm0后才有数据通道。
收工：退出应用，保存记录；在开发板SSH执行sync，再正常poweroff，等待停机后断电。不要在存储卡写入时直接拔电源。
''')

lab2=json.loads((ROOT/'evidence/lab2/status.json').read_text(encoding='utf-8'))
with (OUT/'实验二结果表.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['测试项目','该阶段耗时（ms）'])
    for key,label in [('pixel','画点'),('rect','矩形'),('line','直线')]:
        w.writerow([label,lab2['measurementsMs'][key]])

rows=[
['2026-10-15','早期基线','228 / 236 / 263',236,228,'原接口；早期CPU/编译条件'],
['2026-10-15','字模缓存','170 / 172 / 175',172,170,'与同批早期基线对比'],
['2026-10-15','缓存及-O3','160 / 155 / 173',160,155,'155ms仅有原始日志；既有成绩截图为173ms'],
['2026-10-19','同轮基线','47 / 46 / 47',47,46,'O3/LTO/native、performance、CPU4/5、2线程；原接口'],
['2026-10-19','v9-sprint','27 / 27 / 25',27,25,'与同轮基线交替；显式批量接口'],
['2026-10-19','v10-sprint','28 / 25 / 28',28,25,'与同轮基线交替；显式批量接口'],
['2026-10-19','直接矩形组合','22 / 21 / 17',21,17,'后续独立三轮；显式批量接口；17ms原图已保存'],
['2026-11-05','已部署最优组合复测','58 / 19 / 20',20,19,'三轮全部保留；首轮文字41ms，后二轮1ms，原因未定'],
]
with (OUT/'实验三测速表.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['日期','版本','三轮总耗时ms','中位数ms','最小值ms','条件与限制']);w.writerows(rows)
checks=[
['v2 ARM构建','已通过','build-v2.log','两个程序链接成功；非助教验收'],
['2048规则与提示自动测试','已通过','8000生成移动、200提示局面','真实触摸滑动/撤销/提示待补反馈'],
['打砖块状态与物理自动测试','已通过','100000合成物理帧','不代表实测FPS或三关人工通关'],
['Linux纪录文件测试','已通过','板端test_profile结果','实际合集重开与突然断电是不同测试'],
['触摸USB识别','已确认','20261105设备记录','当次event2，重新连接后可能变化'],
['v2打砖块真实运行','已留图','第1/3关、350分、生命2','完整操作清单仍待用户反馈'],
['五子棋旧模块落子/AI/悔棋','用户已确认','20261019用户确认与实际对局日志','不能替代v2菜单进出流程验证'],
['v2菜单/2048/道具预览','电脑模拟图','preview目录','只能用于设计说明'],
['真实FPS、断电安全、v2正式验收','未记录完成','待补','不写具体性能或验收通过结论'],
]
with (OUT/'实验六验证状态.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['项目','当前证据状态','依据','边界或待补']);w.writerows(checks)

table_page=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>实验报告表格合集</title>',
    '<style>body{max-width:1120px;margin:32px auto;padding:0 20px;color:#111;background:white;font:12pt/1.65 "Times New Roman","SimSun",serif}h1{font:18pt "SimHei",sans-serif}h2{font:14pt "SimHei",sans-serif;margin-top:36px}table{border-collapse:collapse;width:100%;margin:12px 0;table-layout:auto}th,td{border:1px solid #333;padding:7px 9px;vertical-align:top}th{font-weight:bold;background:#f1f3f5}p{margin:12px 0}.note{font-size:10.5pt}a{color:#165a91}@media print{body{margin:0}h2{break-after:avoid}tr{break-inside:avoid}}</style>',
    '<h1>实验报告表格合集</h1><p>对应正文中的表2-1、表3-1和表6-1。可选中表格复制到Word，粘贴时保留表格，再按模板统一字体；也可打开对应CSV。</p>']
for title,filename,note in [
    ('表2-1 实验二运行结果','实验二结果表.csv','数据来自2026-10-15开发板原始运行日志，程序退出状态为0。耗时是各测试阶段的整数毫秒计时，不是单个图元的一次调用耗时。'),
    ('表3-1 实验三各版本三轮完整测速结果','实验三测速表.csv','时间单位均为ms。总耗时为课程绘制阶段整数计时之和，不包含解码、刷新、等待及启动等全部成本。批量版本采用显式批量接口；跨批次CPU和编译条件不同，不能把全部差异归因于单一算法。2026-11-05第一轮58ms完整保留，文字阶段41ms的原因未定。'),
    ('表6-1 最新游戏工坊v2功能验证状态','实验六验证状态.csv','依据截至2026-11-06已保存材料。电脑模拟、板端自动测试、实际操作及助教验收分别记录；若之后完成操作或验收，请按真实结果更新。')]:
    with (OUT/filename).open(encoding='utf-8-sig',newline='') as f:table=list(csv.reader(f))
    table_page.append('<h2>'+html.escape(title)+'</h2><p><a href="'+quote(filename)+'">打开CSV</a></p><table><thead><tr>')
    table_page.extend('<th>'+html.escape(v)+'</th>' for v in table[0]);table_page.append('</tr></thead><tbody>')
    for row in table[1:]:table_page.append('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in row)+'</tr>')
    table_page.append('</tbody></table><p class="note">注：'+html.escape(note)+'</p>')
table_page.append('</html>')
(OUT/'表格合集.html').write_text('\n'.join(table_page),encoding='utf-8')

reference_url='https://github.com/nivag8899/HUST-Embedded-System/blob/main/U202115285_%E9%AB%98%E5%83%96.pdf'
textfile('07-依据与来源.txt',f'''当期课程依据
用户提供：4.实验-Orangepi-20250815-V25.pptx。
已读文本保存在：{ROOT / '.ppt-reading/4.实验-Orangepi-20250815-V25.txt'}。
第17页：六次实验分别检查，提交实验报告；实验80%，报告20%。
实验一19—43页；实验二44—52页；实验三53—64页；实验四65—72页；实验五73—87页；实验六选题依据88页。
课程PPT没有在以上材料中提供本报告所有字体的强制规范，字体安排沿用用户提供模板。

结构参考：用户选定的往届报告
{reference_url}
仓库：https://github.com/nivag8899/HUST-Embedded-System
本地已读取报告正文与目录：references/report-templates-20261022/nivag-2021-report.pdf.txt。
采用每章“实验要求、实验过程、实验结果”及“实验总结与建议”的结构。没有复制其个人信息、他人测试结果或联机游戏经历。

1037检索范围
2026-11-06访问 https://1037.wiki/ ，工具只取得导航与搜索入口，未取得新的嵌入式报告正文；未把导航页当作读过课程报告。

模板格式依据
用户原文件：/example/user/Desktop/嵌入式系统实验报告模板.docx。
已保存样式分析：reports/template-filled-20261023/template-analysis.json。

实测与实现依据
本包“日志”均由已有原文件复制，来源与SHA256见材料清单.csv。正文中的实现细节已对照本地代码。
实验六以lab6-arcade-v2与2026-11-05板测材料为准；该目录README中较早的“显示与触摸全部待板测”字样不覆盖本次已获得的真实截图和设备识别证据。
原始代码、旧报告、历史优化版本和公开仓库均保留。本次只增加材料包，没有联网改动开发板或推送GitHub。
''')

template=Path('/example/user/Desktop/嵌入式系统实验报告模板.docx')
if template.is_file():
    copy(str(template),'模板/用户原始模板-未填充.docx','用户原始模板副本-未修改')

textfile('00-先看这里.txt','''实验报告自填材料包｜2026-11-06

直接打开“材料总览.html”浏览文字和配图，或从“01-报告正文-按模板逐节粘贴.txt”复制。

已备好：实验一至六和总结的完整文字、按章拆分文本、真实截图、明确标注的电脑模拟图、图注、原始日志、三张CSV表与可复制的表格合集、游戏工坊v2源码包及电脑试玩包、操作与答辩说明。

实验六按最新“橙派游戏工坊v2”写：五子棋＋2048＋三关打砖块＋道具＋挑战纪录。正文6.3区分当前实测和待补项目。

你需要做：粘贴到自己的Word模板；填个人资料和真实验收信息；插图并删除编辑提示；补目前欠缺的真实截图；更新目录，检查排版后导出PDF。

先看“03-使用方法与排版.txt”；要补什么看“05-提交前还需补什么.txt”。
“图片/真实记录”可以作为对应实测证据；“图片/电脑模拟-仅设计说明”必须保留模拟图注。
实验一、二已有明确验收记录；其余实验若已验收，自行按实际补充，当前材料不代写未知结论。
历史17ms和最新58/19/20ms均保留。游戏工坊v2真实打砖块截图已备好，不用拿旧五子棋充当整个实验六。
''')

# Plain local browsing index; text stays selectable and images are unchanged copies.
def anchor(path,label=None):return f'<a href="{quote(path,safe="/")}">{html.escape(label or path)}</a>'
page=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>实验报告自填材料</title>',
      '<style>body{max-width:1050px;margin:40px auto;padding:0 24px;color:#20262e;font:17px/1.8 system-ui,"Microsoft YaHei",sans-serif;background:#fafbfc}h1,h2{line-height:1.4}a{color:#175ca0}nav{display:flex;gap:14px;flex-wrap:wrap}pre{white-space:pre-wrap;font:16px/1.9 "SimSun",serif;background:white;border:1px solid #dfe4e8;padding:24px}figure{background:white;border:1px solid #dfe4e8;margin:20px 0;padding:16px}img{display:block;width:100%;height:auto}figcaption{font-size:15px;margin-top:12px}small{color:#646d76}.tag{color:#8a4200;font-weight:600}details{margin:16px 0}summary{cursor:pointer;font-weight:600}</style>',
      '<h1>实验报告自填材料</h1><p>2026-11-06 · 实验六使用最新「橙派游戏工坊 v2」</p>',
      '<p>按照自己的模板逐节复制，配图保持原始内容。真实板测、旧模块记录与电脑模拟分别标注。</p><nav>']
for f in ['00-先看这里.txt','01-报告正文-按模板逐节粘贴.txt','03-使用方法与排版.txt','04-实验六操作与答辩要点.txt','05-提交前还需补什么.txt','表格合集.html','实验二结果表.csv','实验三测速表.csv','实验六验证状态.csv','07-依据与来源.txt']:
    page.append(anchor(f))
page.append('</nav><h2>正文</h2>')
for name,body in chapters:
    page.append(f'<details><summary>{html.escape(body.splitlines()[0])}</summary><p>{anchor("正文/"+name,"打开本章TXT")}</p><pre>{html.escape(body.strip())}</pre></details>')
page.append('<h2>配图及图注</h2>')
for _,dest,role,caption in images:
    page.append(f'<figure><p class="tag">{html.escape(role)}</p><img loading="lazy" src="{quote(dest,safe="/")}" alt="{html.escape(caption)}"><figcaption>{html.escape(caption)}<br>{anchor(dest,"打开原图")}</figcaption></figure>')
page.append('<h2>代码与日志</h2><ul>')
for item in manifest:
    if item['file'].startswith(('代码附件/','日志/')):page.append('<li>'+anchor(item['file'])+'</li>')
page.append('</ul><p>结构参考：<a href="'+reference_url+'">用户指定的往届报告</a>；当期要求以课程PPT为准。</p></html>')
(OUT/'材料总览.html').write_text('\n'.join(page),encoding='utf-8')
with (OUT/'材料清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['file','source','kind','caption','bytes','sha256']);w.writeheader();w.writerows(manifest)

# Verify copied evidence, chapter completeness, readable images, and all local HTML links.
for entry in manifest:
    p=OUT/entry['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
    if p.suffix.lower()=='.png':
        with Image.open(p) as im:im.verify()
body=(OUT/'01-报告正文-按模板逐节粘贴.txt').read_text(encoding='utf-8-sig')
assert all(f'{n}.{k} ' in body for n in range(1,7) for k in range(1,4))
assert all(x in body for x in ['7.1 实验总结','7.2 实验建议','橙派游戏工坊 v2','58、19、20','17 ms'])
assert not re.search(r'\b[UMD]20\d{7,10}\b|\b1[3-9]\d{9}\b', body)
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('src','href') and value and not value.startswith(('http:','https:','#')):
                assert (OUT/unquote(value)).is_file(),value
Links().feed((OUT/'材料总览.html').read_text(encoding='utf-8'))
Links().feed((OUT/'表格合集.html').read_text(encoding='utf-8'))
assert (OUT/'表格合集.html').read_text(encoding='utf-8').count('<table>')==3
report={'preparedDate':'2026-11-06','copiedFiles':len(manifest),'copiedImageFiles':len(images),'chapters':7,
        'originalHashesMatched':True,'localHtmlLinksExist':True,'imageDecodeVerified':True,
        'reportTextCharacters':len(body),'gameWorkshop':'v2','noNewBoardRun':True,
        'newTAacceptanceNotClaimed':True,'wordTemplateNotEdited':True}
textfile('材料检查.json',json.dumps(report,ensure_ascii=False,indent=2))
archive=OUT.parent/'实验报告自填材料_20261106_游戏工坊v2.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(OUT.parent))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({**report,'folder':str(OUT),'archive':str(archive),'archiveBytes':archive.stat().st_size},ensure_ascii=False,indent=2))

