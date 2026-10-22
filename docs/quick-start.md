# 快速开始

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

重建工具会逐文件检查原始哈希和输出哈希。2026-10-22重新检查七个profile的重建与构建依赖，并核对v10字体/图片复制；这验证迁入完整性，不代表重新做过板上实验。新目录的验证状态仍按各实验说明记录。

公开profile不包含私人工作区打包脚本和安装器测试。实验五的`tests/run_offline.py`用于配有Windows MinGW的主机逻辑检查，`tests/board-serial-test.py`用于Linux伪终端测试。实验六的C规则/存档测试需在具备相应编译环境的独立工程运行；主机模拟结果不能替代实物验收。
