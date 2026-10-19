# 实验二：矩形与直线

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
