# 橙派游戏工坊 v2

实验六已通过助教正式验收（2026-11-10 确认），报告与最终演示使用游戏工坊 v2。

统一菜单组织五子棋、2048 和打砖块。v2 增加三关挑战、连击、道具、成绩与徽章记录，保留五子棋独立对局存档；没有蓝牙联机或语音功能。

```sh
python3 tools/materialize.py --profile arcade-v2 --course /path/to/lab-st-2026 --output .work/arcade-v2 --include-assets
bash .work/arcade-v2/build-on-board.sh /path/to/lab-st-2026
bash .work/arcade-v2/run-on-board.sh --touch /dev/input/event2
```

后两条在 Orange Pi 开发板执行。触摸节点按 `/proc/bus/input/devices` 确认；HDMI 负责显示，触摸 USB 接到开发板。构建脚本使用课程 `common/task.c`、字体和外部库。

- 五子棋：点击交叉点落子，支持人机、双人、悔棋、保存退出。
- 2048：滑动合并，支持撤销和提示。
- 打砖块：拖动挡板，松手发球，支持暂停与重新开始；v2 支持过关后进入下一关。

v2 在 2026-11-05 完成 ARM 编译与规则/文件测试并在开发板运行；[运行截图和记录](../../results/board/board-20261105/本次板测说明.txt)保留现场情况。电脑模拟图与实际 framebuffer 截图分开存放。v1 是历史版本；v2 是报告使用的版本。

[新增源码](../../projects/game-workshop-v2/README.md) · [可读补丁](changes.patch) · [重建配置](profile.json)
