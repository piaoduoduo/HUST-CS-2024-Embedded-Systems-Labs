# 来源与公开范围

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
