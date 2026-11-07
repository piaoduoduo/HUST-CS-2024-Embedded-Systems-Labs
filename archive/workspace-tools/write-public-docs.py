from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]/'hust-embedded-labs-orangepi'
docs={
'README.md':'''# HUST Embedded Labs · Orange Pi 4 LTS

华中科技大学嵌入式系统实验的实现、复现步骤与排障记录。硬件为 Orange Pi 4 LTS，内容包括 Linux 图形、图片与文字、多点触摸、蓝牙串口和触屏五子棋候选。

**状态快照：2026-10-18。** 本地整理版，尚未推送远端。先分享实验一至四和已有证据；实验三 v9、实验五、六明确标为待板测。下一轮成果更新等待实验三、五、六的实际验收反馈。

## 先看这些

- [快速开始与依赖](docs/quick-start.md)
- [电脑连接开发板、SSH 与排障](docs/connection-troubleshooting.md)
- [实验三优化过程与测量口径](docs/lab3-optimization.md)
- [各实验状态与验收后更新步骤](docs/status-and-updates.md)
- [来源、引用和公开范围](THIRD_PARTY_NOTICES.md)

## 实验导航

| 实验 | 实现与说明 | 实际状态 |
| --- | --- | --- |
| 一 | [烧录、启动和 Hello](labs/lab1/README.md) | 用户反馈已验收 |
| 二 | [矩形和直线](labs/lab2/README.md) | 用户反馈已验收 |
| 三 | [图片、字模、文字与测试](labs/lab3/README.md) | 基线已板测，验收待反馈 |
| 四 | [五指画板](labs/lab4/README.md) | 功能已板测，验收待反馈 |
| 三 v9 | [PNG、文字与几何优化候选](experiments/lab3-v9/README.md) | **待板测** |
| 五 | [经典蓝牙 SPP](labs/lab5/README.md) | **待板测** |
| 六 | [触屏五子棋](labs/lab6/README.md) | **待板测** |

已实现、离线测试、真实板测、助教验收分别记录。完整状态见 [STATUS.json](STATUS.json)。

## 代码组织

实验一提供独立源码；实验二至四与 v9 以可读的 `changes.patch` 和带哈希校验的 `profile.json` 记录修改。你需要从课程渠道取得匹配的原始工程，工具会重建到新的独立目录，不修改原工程或已有输出目录。

```sh
python3 tools/materialize.py --profile lab3 --course /path/to/original-course --output .work/lab3 --include-assets
make -B -C .work/lab3/lab3 CC=gcc CFLAGS='-Wall -O3'
make -B -C .work/lab3/test CC=gcc CFLAGS='-Wall -O3'
```

这些构建命令在开发板执行；显示程序运行前按快速开始检查屏幕和桌面状态。需要匹配的课程工程与随课外部库，不能只复制 `.c` 文件就假定可运行。

## 实测结果

实验三字模缓存配合 `-O3` 的三次真实板测为 **160 / 155 / 173 ms，中位数 160 ms**。155 ms 有完整日志，没有该轮独立截图；下图对应 173 ms。

![真实开发板 framebuffer 中的 173ms 结果表](results/board/lab3-173ms.png)

v9 的 PNG 混合次数、几何写入量与离线画面比对见优化记录；**目前没有 v9 板上耗时，20 ms 是目标**。公开成绩不采用工程估计或同学口述的数字。

## 验证本仓库

```sh
python3 -m unittest discover -s tests -v
python3 tools/check-repository.py
make -C labs/lab1
./labs/lab1/out/lab1
```

这里的自动检查只验证仓库结构、重建工具和普通主机可执行的 Hello，不等于 ARM、触摸或蓝牙验收。历史绘图测试摘要单独存放于 [results/host](results/host/README.md)。GitHub Actions 配置已准备，尚未在远端执行。

## 使用与贡献

请先理解实现，再对照当期任务书完成实验。不同年份镜像和硬件可能不同；报告性能时附版本、flags、计时范围及多轮分项数据。参考他人资料时保留来源，不把他人的测试与验收当成本项目结果。

本地原始材料、历史版本和归档另外完整保留。PPT、系统镜像、字体文件、SDK、模型和他人报告未打包进仓库；公开范围与许可证状态见来源说明。开发中使用过 AI 辅助，可靠性以明确列出的测试为依据。
''',
'docs/quick-start.md':'''# 快速开始

## 环境与外部输入

已使用的环境：Orange Pi 4 LTS（RK3399、约4GB内存），课程 Orange Pi 3.0.6 Focal 镜像、Linux 5.10.43、AArch64 GCC；屏幕可见1024×600、32bpp。具体编译器和内核以你的板子为准。

通过课程渠道取得2026版原始工程，至少保留 `common`、对应实验、`test`、`out` 与 `common/external`。字体、测试图片、JPEG/PNG/FreeType等外部库由课程工程提供，本仓库不下载或分发它们。

重建工具使用 Python 3.8+ 标准库；示例中的 `python3` 在 Windows 上可替换为已有的 Python 命令。输入工程必须为匹配的原始模板；已改动工程可能哈希不匹配，应另取干净副本。不要用忽略哈希的方式强行覆盖。

## 获得独立源码副本

在仓库根目录执行，输出目录必须不存在且位于原课程工程之外：

```sh
python3 tools/materialize.py --profile lab2 --course /path/to/original-course --output .work/lab2 --include-assets
python3 tools/materialize.py --profile lab3 --course /path/to/original-course --output .work/lab3 --include-assets
python3 tools/materialize.py --profile lab4 --course /path/to/original-course --output .work/lab4 --include-assets
```

不加 `--include-assets` 只重建源文件；加上后从你指定的课程目录复制字体、图片和稳定实验需要的外部库到输出。工具不编译、不运行程序，也不操作网卡或服务。

## 在板上构建

```sh
make -B -C .work/lab2/lab2 CC=gcc
make -B -C .work/lab3/lab3 CC=gcc CFLAGS='-Wall -O3'
make -B -C .work/lab3/test CC=gcc CFLAGS='-Wall -O3'
make -B -C .work/lab4/lab4 CC=gcc CFLAGS='-Wall -O3'
```

`-B` 避免旧公共对象文件或不同优化参数留下的产物混入。镜像和库必须与AArch64程序匹配；不要用电脑x86编译器生成的程序充当ARM结果。

## 显示程序启动前

1. 确认 SSH 已连上开发板，检查 `uname -m`、`gcc --version`。
2. 查看 `systemctl is-active display-manager`、`fbset -i`、`cat /proc/bus/input/devices`。
3. 确认没有其他实验程序同时绘屏；核对进程身份后再停止对应进程。
4. 如果板上桌面仍运行，临时执行 `sudo systemctl stop display-manager`。
5. 根据实际framebuffer检查可见尺寸、32位色和行跨度。触摸节点按实际设备选择。

随后进入输出目录的 `out` 运行对应程序。课程图片和字体相对路径以运行工作目录为基准。

```sh
cd .work/lab3/out
./lab3
# 再单独运行性能测试
./test
```

停止的是开发板桌面，不影响笔记本桌面或SSH聊天。需要恢复时可在实验退出后执行 `sudo systemctl start display-manager`。不要默认永久修改开机默认target。

## 当前重建验证的边界

重建工具会逐文件检查原始哈希和输出哈希。迁入时已在本地重建四个profile并与现存已准备源码逐字节对照；这验证迁入完整性，不代表重新做过板上实验。新目录的验证状态仍按各实验说明记录。
''',
'docs/connection-troubleshooting.md':'''# 连接开发板与排障

## 已跑通的路线

本项目两次上课实际采用：**笔记本有线网口 → 网线 → 开发板，以 SSH 操作**。触控屏的USB负责触摸输入；HDMI负责画面。板上的USB网络接口是另一条路线，不能把它的地址当作网线接口地址。

先接好开发板电源、SD卡、屏幕电源、HDMI、触摸USB与网线。确认供电规格与实际接口，首次启动留出时间。

## Windows 电脑端

用 `ipconfig` 查看与开发板连接的有线网卡。已有可用地址时直接连接，不需要先重做共享。

```powershell
ipconfig
Test-NetConnection <BOARD_IP> -Port 22
ssh <USER>@<BOARD_IP>
```

尖括号是待替换参数，实际输入时删除。SSH密码没有字符或星号回显是正常现象，输入后回车。首次连接前核对设备，确认主机指纹；已知设备出现密钥变化提示时先确认换镜像或换板等原因。

如果需要使用Windows的网络共享：Win+R → `ncpa.cpl` → 当前有网络的WLAN属性 → 共享 → 家庭网络连接选择真正连开发板的有线网卡。保存后重新查看地址；多网卡环境不要凭网卡显示名称猜测目标。

## 固定地址示例

以下仅为网线点对点示例，不是每台电脑的通用配置：电脑 `192.168.137.1/24`，板子 `192.168.137.2/24`。以本机实际共享网段和未占用地址为准。USB网络接口的地址单独处理。

板端检查：

```sh
ip -4 -br addr
ip route
```

网线接口应有正确地址且链路正常。接口不一定叫eth0；下面假设实际接口为eth0：

```sh
sudo ip addr replace 192.168.137.2/24 dev eth0
```

这只是当前启动期的地址设置，并不保证自动持久保存。设置时不要覆盖承担其他连接的接口；需要长期使用时在对应NetworkManager有线连接内保存。点对点直连不应随意抢占已有默认路由。

## 连接失败按层检查

| 现象 | 优先检查 |
| --- | --- |
| 有线网卡未连接 | 网线两端、接口、板子供电和链路灯 |
| 有线网卡地址不对 | 共享目标和实际网段，保存后重新读地址 |
| 板端无地址 | 实际接口状态、DHCP或手动地址配置 |
| 端口22不可达 | 两端是否同网段、路由、板上SSH服务 |
| 端口通但无法认证 | 用户名、镜像认证方式、输入法、账户状态 |
| SSH已进入但屏幕黑 | 屏幕供电/视频输入、桌面、framebuffer和占屏程序 |

曾遇到把 `192.168` 输入为 `192.16`；修正地址后SSH恢复。反复扫描地址或重烧系统并没有解决这类输入错误。
`arp -a` 没有条目不能单独证明硬件损坏。

## 只有笔记本键盘时

笔记本键盘通常控制笔记本上的窗口，不会自动向开发板小屏输入。优先从电脑恢复SSH；如必须板端输入，可临时借USB键盘。触屏是否有可用软键盘取决于镜像，不默认它一定安装。

## 屏幕与framebuffer

先确认屏幕能开菜单、有电、视频输入正确，检查HDMI两端。屏幕恢复供电后可能还需要等待输入重新同步。
开发板能显示Applications菜单说明桌面已起来，但不代表课程framebuffer程序已运行。

```sh
systemctl is-active display-manager
fbset -i
cat /proc/bus/input/devices
```

本项目遇到可见尺寸和虚拟缓冲不同：可见1024×600，虚拟1280×720，行跨度5120字节。停止桌面后，针对这一特定模式曾使用：

```sh
sudo fbset -g 1024 600 1280 720 32
```

先读本机配置再决定是否使用，不把该命令套到所有屏幕。虚拟尺寸和可见尺寸可以不同，绘制/刷新必须尊重实际行跨度。

## 触摸与收工

通过设备描述识别触摸节点；本项目设备曾为 `wch.cn USB2IIC_CTP_CONTROL`，节点编号会变化。HDMI有画面不代表触摸USB已接入。
需要断电时在板端执行 `sudo shutdown -h now`，等待关机后再断电或取卡。只有屏幕断电、板子仍供电时，不需要因此重烧SD卡。
''',
'labs/lab1/README.md':'''# 实验一：烧录、启动与 Hello

状态：用户反馈已完成助教验收。

## 操作顺序

1. 按当期教案核对开发板型号、课程镜像和SD卡。
2. 用烧录工具选择镜像和目标卡，确认目标卡内容可覆盖。
3. 等待写入及校验完成，安全移除卡；板子断电时插卡。
4. 接好供电与显示，等待首次启动。恢复SSH后在板上构建、运行本目录程序。

仓库不附课程镜像、烧录软件或原始SD卡备份。

```sh
make -C labs/lab1
./labs/lab1/out/lab1
echo $?
```

预期输出 `Hello embedded linux!`，退出码0。若在普通电脑运行，只验证Hello程序；实验一验收还需要实际板子烧录、启动和运行过程。

烧录成功提示、系统能启动、板上程序正常输出分别提供证据。SSH密码输入没有回显的情况见[连接指南](../../docs/connection-troubleshooting.md)。
''',
'labs/lab2/README.md':'''# 实验二：矩形与直线

状态：用户反馈已完成并通过助教验收。

读取 [changes.patch](changes.patch) 查看相对课程模板的实现变化；[profile.json](profile.json) 用于精确重建。矩形用64位中间坐标裁剪后逐行填色；直线沿较长轴按整数误差推进，覆盖端点反转、八方向、单点和越界。

```sh
python3 tools/materialize.py --profile lab2 --course /path/to/original-course --output .work/lab2 --include-assets
make -B -C .work/lab2/lab2 CC=gcc
cd .work/lab2/out
./lab2
```

运行前按[快速开始](../../docs/quick-start.md)处理桌面和屏幕。验收要看点阵、彩色矩形、中央交叉线及边界显示；退出码0不能替代画面检查。

后续实验修改了公共图形/图片代码。每个profile重建到独立目录，避免用实验二旧代码覆盖实验三的缓存或实验四的触摸处理。
''',
'labs/lab3/README.md':'''# 实验三：图片、字模与文字

状态：图片和文字已在板上显示正常；基础版本有真实性能日志。尚未收到助教验收通过反馈。

实现：JPG逐行复制；PNG与alpha字模透明混合；文字使用通用字模缓存，键包含字体、字符与字号，并保持返回图片的独立所有权。

```sh
python3 tools/materialize.py --profile lab3 --course /path/to/original-course --output .work/lab3 --include-assets
make -B -C .work/lab3/lab3 CC=gcc CFLAGS='-Wall -O3'
make -B -C .work/lab3/test CC=gcc CFLAGS='-Wall -O3'
cd .work/lab3/out
./lab3
./test
```

运行前查看[快速开始](../../docs/quick-start.md)。预期基础画面包含羊驼图片、绿色透明图、红色“嵌”和紫色两行诗；综合测试约有数秒等待，成绩表不包含这些sleep。

真实结果为160/155/173ms，中位数160ms。完整分项与优化前对照见[真实板测数据](../../results/board/lab3-20261015.json)，155ms日志见[原始测试输出](../../results/board/lab3-155ms.log)。
字模缓存有960项真实FreeType对照记录，已有基础版本画面像素对照通过；这不能推导v9已经通过同样的板上验证。

验收时展示基础合成画面、完整测试表，保存编译参数、完整日志和反馈。性能优化过程见[优化记录](../../docs/lab3-optimization.md)；[v9候选](../../experiments/lab3-v9/README.md)仍待板测。
''',
'labs/lab4/README.md':'''# 实验四：五指画板

状态：真实单指绘制、五指五色连续粗轨迹、清屏均已由用户确认；助教验收待反馈。

```sh
python3 tools/materialize.py --profile lab4 --course /path/to/original-course --output .work/lab4 --include-assets
make -B -C .work/lab4/lab4 CC=gcc CFLAGS='-Wall -O3'
cd .work/lab4/out
./lab4 --touch /dev/input/eventX
```

`eventX`须替换为实际触摸节点，参见[连接与设备排查](../../docs/connection-troubleshooting.md)。不要重复启动多个画屏程序。

本版保留已验证的实验三字模缓存，新增触点协议和绘制模块。顶部色块表示触点颜色，**不提供单指选色**；每个触点按编号分配颜色。

验收：单指快速画线、五指同时拖动后抬起，确认五条不同颜色、连续且较粗的轨迹；点击右上角清屏。

![读取真实开发板 framebuffer 的五色轨迹](../../results/board/lab4-five-fingers.png)

该图是从真实开发板framebuffer读取的图像，不是屏幕实物照片。运行状态记录见[板测结果](../../results/board/lab4-20261015.json)。
''',
'labs/lab5/README.md':'''# 实验五：经典蓝牙 SPP（待板测）

离线应用和修复版本已在本地准备，手机选择安卓“蓝牙串口”类SPP应用。当前只提供状态和后续验收入口，尚未把待验收应用作为已完成成果迁入本仓库。

尚未确认手机配对成功，未完成真实双向收发、断连重连、Linux PTY集成或助教验收。
配对、SPP连接、`/dev/rfcomm0`出现、应用层收发分别检查；BLE调试器不能直接代替经典SPP应用。

验收需记录：设备与服务配置、英文/中文两个方向的数据、断连重连和真实屏幕/手机表现。确认完成后按[更新流程](../../docs/status-and-updates.md)迁入最终代码和证据。
''',
'labs/lab6/README.md':'''# 实验六：触屏五子棋（待板测）

本地候选为15×15自由五子棋，支持人机与同屏双人、悔棋、重开、胜负提示、存档恢复和受限AI搜索。没有蓝牙对战或语音控制。

规则、状态、AI和模拟界面已有离线测试；尚未确认ARM编译、真实触摸、实际存储与响应速度，也未助教验收。模拟截图不得标为真实板图。

当前仓库保留待办入口，待验收后再迁入最终应用。验收需检查触点映射、每次只落一子、胜负/和棋、AI响应、悔棋/重开、退出与存档恢复。
更新方式见[验收后更新](../../docs/status-and-updates.md)。
''',
'experiments/lab3-v9/README.md':'''# 实验三 v9：待板测候选

**状态：仅离线验证；无ARM原生编译、真实FreeType验证和板上耗时。**

候选保留原版及v8对照，加入精确四像素SIMD、PNG不透明后缀遮挡剔除、有序文字批处理、精确几何批次、同行同色合并及可选DSU。
[changes.patch](changes.patch)可以查看源码，[profile.json](profile.json)记录重建数据。算法、复杂度和历史测试范围见[优化过程](../../docs/lab3-optimization.md)。

## 在独立目录准备

```sh
python3 tools/materialize.py --profile v9 --course /path/to/original-course --output .work/v9 --include-assets
cd .work/v9
python3 run-sprint.py --project /path/to/original-course --build-only
```

这是**待上板执行**的原生正确性验证和构建入口，不是已经执行的记录。v9运行器通过`--project`读取原课程外部库，不修改那个工程。
`--include-assets`为此profile复制本地课程字体和图片，运行器所需manifest在重建时生成；不随仓库分发原素材。

确认画面环境后再测：

```sh
python3 run-sprint.py --project /path/to/original-course --runs 5
# 如需更细时间诊断，另一次比较可加：
python3 run-sprint.py --project /path/to/original-course --runs 5 --precise-timing
```

依次比较baseline、v8-packed、v8-sprint、v9-core、v9-sprint。全开不一定更快，按分项中位数和正确性选版本；DSU等可单独对照。
临时CPU设置的恢复功能沿用已准备运行器，断电或强制终止后核对记录，用`restore-controls.py`恢复。

显式batch/prepared调用须与未改课程main的成绩区分。所有准备、收集、执行、释放位于相应计时内；精细诊断另行保存，不能替换原课程分数。
''',
'docs/lab3-optimization.md':'''# 实验三优化过程

## 真实板测基线

2026-10-15使用完整课程循环、素材与原计时范围，进程逐次独立启动。已记录：

| 版本 | 三次总时间/ms | 中位数/ms |
| --- | --- | --- |
| 基础版本 | 228 / 236 / 263 | 236 |
| 字模缓存、O2 | 170 / 172 / 175 | 172 |
| 字模缓存、O3 | 160 / 155 / 173 | 160 |

当时CPU governor为ondemand，未调频或绑核。中位数236→160降低约32.2%；单次最快155ms不代表稳定性能。
来源：[逐项数据](../results/board/lab3-20261015.json)、[155ms输出](../results/board/lab3-155ms.log)、[173ms framebuffer截图](../results/board/lab3-173ms.png)。

155ms这一轮：pixel6、rect14、line23、jpeg62、png30、font9、text11，总和155。图片共101ms。

## 优化顺序与状态

1. 基础图形裁剪、整数线算法、图片透明混合和字模缓存：已有基础版本板测。
2. SIMD行内核、几何专用路径、文字布局缓存与JPG反向覆盖：离线候选发展阶段。
3. PNG/alpha字模prepare与目标行整批绘制：减少透明扫描及重复启动并行区，仍逐层保持顺序。
4. v7行CSR：筛选从逐行扫全部命令O(HN)变为O(H+N+K)，K为实际行交集；构建索引也计时。
5. v8短区间打包通道、未舍入source×alpha乘积缓存：减少常数工作，增加内存读取，保留开关。
6. v9补精确4像素尾部、PNG遮挡剔除、跨字符串有序文字批次和几何覆盖：完整离线整合通过，**仍待板测**。

v2以后候选的主机测试不构成ARM实测。原版、v6/v7/v8完整归档另外本地保留；候选重建产物还保留v8对照源码。

## PNG与文字确实做了什么

PNG只删除被后续alpha=255完全覆盖的早期贡献。反向分析覆盖，正向混合剩余像素；没有把半透明层任意合成一次。
课程PNG半透明混合555909→427251（少23.14%），不透明写445265→344107。新四像素核避免把4—7像素尾部全部交给标量，且不越界多读8像素。
确定不重叠的行走快路，字体网格不承担无收益的位图分析。

文字批次拥有独立字形快照，避免缓存淘汰后队列引用失效。按目标行CSR保留原字形顺序，一批共享并行区；容量或分配失败有精确回退。
透明混合仍逐层整数舍入。两个半透明层通常不能直接合成一层：逐层舍入和最后一次舍入并不等价。

## 几何与复杂度

课程矩形写1849440→614400，直线写401802→201797；直线生成241602个行片段，同行相邻同色相交合并后保留1202个CSR记录。
生成片段依然有成本；“每像素最终只写一次”不等于整个算法O(最终像素)。

设N命令、H屏幕行、W宽、Kg生成片段、Kr合并片段、U实际写像素。生成O(N+Kg)，CSR O(H+Kr)，位图还需扫描片段覆盖的64位字和写U像素。
DSU候选约O(N+Kg+HW+(Kr+U)α(W))，逐像素find/union有常数开销，不保证比连续填充快。
文字每批约O(H+G+K+P)加字形快照成本；G字形、K字形行引用、P访问像素，必要透明工作没有消失。

PNG后缀位图也有复制、扫描、切段开销；source乘积缓存增加带宽。任何工作量减少都需要真实A/B计时确认收益。

## 已有离线验证

- PNG最终11配置，每配置32全帧oracle、104 prepared所有权/裁剪/脏区回归和真实malloc失败回退；四像素核另有穷举与保护页检查。
- 文字10配置，每配置58全帧/脏区/哨兵案例，包含UTF-8、重叠、缓存淘汰、输入修改、字体身份与故障注入。
- 几何15配置，每配置520案例、33338命令，含整数极值、容量/分配失败、位图/DSU和多线程。
- 最终整合16配置，九阶段画面哈希一致；主机NEON为算术模拟，字体为Pillow/测试字模，时钟置0的回放不产生性能成绩。

摘要见[主机证据目录](../results/host/README.md)。这些是迁入前已完成的历史验证，本次仓库整理只重新验证源码重建和文件一致性。

## 下次怎样测

先执行与测速flags相同的ARM/真实字体/完整画面检查，再轮换顺序跑至少3—5轮。保存每阶段、总时间、编译器、flags、线程/绑核、频率/温度和日志。
逐个关闭four-lane、opaque-cull、text-batch、geometry-batch、analytic-lines、geometry-coalesce或products，找到真正收益和回退成本。

课程表内不含解码、fb_update或sleep；刷新另记。20ms不等于程序20ms结束或稳定50FPS。
七段整毫秒差分存在量化误差；可另跑CLOCK_MONOTONIC纳秒诊断，保留原课程口径并分别记录。

目前没有足够数据给v9的可靠毫秒预测或达标概率；公开记录只保留实际测量。
''',
'docs/status-and-updates.md':'''# 状态与验收后更新

当前冻结快照：2026-10-18。状态以 [STATUS.json](../STATUS.json) 为机器可读记录，首页提供摘要。

- 实验一、二：用户反馈验收通过。
- 实验三基线、实验四功能：真实板测通过，助教验收尚未收到确认。
- v9、实验五、实验六：待板测；v9不是另一个已验收实验。

按本轮约定，下一轮成果更新等实验三、五、六的验收反馈。实验四验收如果另有反馈也如实补记，不根据推测改状态。
不定时扫描、不自动提升状态，也不在离线测试通过后自动发布。

## 三个实验验收完成后

1. 由实际操作人确认实验编号、验收日期、助教结果及最终使用的版本。
2. 保存最终源码哈希、构建命令、日志、照片/原始framebuffer和设备环境；分清照片与读取屏幕内存的图片。
3. 实验三同时保存原接口/显式批处理区别、逐项耗时、多轮数据和正确性检查。
4. 实验五保存手机→板和板→手机的真实收发、断连重连；只配对不算收发完成。
5. 实验六补ARM编译、触摸、AI实际响应、存档恢复与错误处理；模拟测试不替代板测。
6. 核对身份信息、素材来源与允许公开范围，迁入最终实验五/六代码，更新状态与首页，写CHANGELOG。
7. 执行仓库检查与相应测试，再向已确定的GitHub目标发布。

本地原代码、历史包及原始证据均另行保留。更新时从最终验证版本导出，不覆盖历史归档；需要撤回候选时可重建旧profile。
''',
'results/board/README.md':'''# 真实板上记录

- [实验三逐项结果](lab3-20261015.json)：三种版本、各三次；字模缓存+O3中位数160ms。
- [155ms完整输出](lab3-155ms.log)：没有该轮独立截图。
- [173ms结果表](lab3-173ms.png)：读取真实framebuffer，不能当成155ms图片。
- [实验四状态](lab4-20261015.json)与[五指轨迹](lab4-five-fingers.png)：用户确认功能正常；图片为真实framebuffer读取。

本目录没有v9板测数据。保留`TAaccepted: false`表示未收到明确验收确认，不表示助教判定失败。
原始记录另外本地完整保存，公开副本不附认证信息或私人终端截图。
''',
'results/host/README.md':'''# 历史离线验证摘要

记录对应2026-10-18前的离线测试，本次整理没有重新运行全部渲染穷举。

- [v9整合](v9-integrated-results.json)：16配置、9阶段画面对照。
- [PNG](v9-png-offline-results.json)：透明混合、遮挡、容量及分配失败回退。
- [文字](v9-text-offline-results.json)：有序批次、缓存寿命与输入所有权。
- [几何](v9-geometry-results.json)：精确行跨度、覆盖、边界和故障回退。

摘要删除编译器输出中的私人工作路径等原始日志，保留原记录SHA256、状态和适用字段。完整日志在本地原材料中保存。
NEON模拟与Pillow/测试字模不等于ARM和真实FreeType，回放伪时钟的0值不代表耗时。
仓库重建测试见 [tests](../../tests/)，不要求分发课程字体或SDK。
''',
'THIRD_PARTY_NOTICES.md':'''# 来源与公开范围

## 当前范围

本仓库是本地公开整理候选。包含课程模板的修改补丁、新增实现、复现工具与文档；完整课件、镜像、原工程、SDK、外部二进制库、字体、模型和他人报告未附。
补丁也包含课程接口及修改上下文，公开前仍需逐项确认课程要求和相应来源的公开范围。尚未给整个混合项目套用统一MIT等许可证。
已有许可声明应随对应文件保留；课程与第三方部分不因放入本仓库而被重新授权。许可证方案最终确认前，仓库不宣称所有内容均已获得统一开源授权。
参考[GitHub许可说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)。

## 基础输入

2026课程原工程与当期实验PPT是实现和验收依据，由课程渠道取得。`profile.json`以原文件SHA256锁定输入，新增/修改代码可从`changes.patch`审阅。
[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)记录本地迁入来源标签和哈希，路径为材料内相对标签，不是读者必须具备的绝对路径。

## 已实际参考的材料

- [Oliver-242/HUST-Embedded-System](https://github.com/Oliver-242/HUST-Embedded-System)：此前已读取lab3/lab4/lab5、graphic/touch等源码；源码定位记录保存在本地references中。
- [nivag8899/HUST-Embedded-System](https://github.com/nivag8899/HUST-Embedded-System)：已读取README及仓库结构，参考其课程与运行组织；其蓝牙五子棋不是本项目已实现功能。
- [uniqueFranky/Embedded-System](https://github.com/uniqueFranky/Embedded-System)：此前已读取图形源码作接口与方法对照。
- [1037.wiki](https://1037.wiki/)：已尝试直接访问与检索，但本次只取得动态入口，没有对应课程正文。
- [Qt像素运算](https://github.com/qt/qtbase/blob/dev/src/gui/painting/qdrawhelper_p.h)：借鉴通道打包思路，课程整数舍入不能直接替换成Qt其他混合公式。
- [Arm NEON intrinsic参考](https://arm-software.github.io/acle/neon_intrinsics/advsimd.html)：四像素核接口核对。
- [Linux多点触摸协议](https://www.kernel.org/doc/html/latest/input/multi-touch-protocol.html)：触点协议理解。

往届材料用于理解要求与方法，不把他人姓名学号、报告、测试成绩、验收和贡献写成本项目实际记录。

## 自动化配置

GitHub Actions依赖官方[checkout](https://github.com/actions/checkout)与[setup-python](https://github.com/actions/setup-python)。这里只运行仓库工具检查和Hello，远端工作流尚未执行。

## AI辅助

设计、编码、整理与审查曾使用AI辅助；人工操作、用户确认、主机测试和板测分别标注。没有把模型估计的毫秒或未执行的测试当作事实。
''',
'CONTRIBUTING.md':'''# 如何补充

请注明适用年份、开发板、镜像和测试范围；修改代码时给出最小复现、实际构建命令与验证结果。
性能数据附版本、编译器、flags、线程、计时口径、逐项多轮结果和正确性对照。
文档、代码、截图和素材保留来源。不要提交凭据、私人路径、未经整理的整段聊天记录、他人报告或许可不明的大文件。
离线、ARM编译、板测和助教验收分别表述；提交“待板测”实现是允许的，但不能改成已验收状态。
''',
'CHANGELOG.md':'''# 变更记录

## 2026-10-18 · 本地整理快照

- 整理实验一至四的复现、连接排障、实验三优化过程和真实板测数据。
- 课程基础工程外置，以精确哈希和差量profile重建到新目录，保留可读补丁。
- v9、实验五和六标为待板测；约定实验三、五、六验收后更新成果。
- 保留原始材料；未创建远端、未推送、未执行GitHub Actions。
'''
}
for name,text in docs.items():
    path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
print('Wrote',len(docs),'public repository documents')
