# 历史版本与研究归档

保留每个阶段的源码与笔记，当前推荐入口为实验三 `v10` 和综合实验 `arcade-v2`。历史笔记中的待测状态及估算按写作当时理解，最终测速以真实板测日志为准。

所有快照通过同一个重建命令使用：

```sh
python3 tools/materialize.py --profile 名称 --course /path/to/lab-st-2026 --output .work/新的目录
```

| 名称 | 配置 | 文件数 |
| --- | --- | --- |
| `lab2` | [profile](../labs/lab2/profile.json) | 10 |
| `lab3` | [profile](../labs/lab3/profile.json) | 10 |
| `lab4` | [profile](../labs/lab4/profile.json) | 14 |
| `v9` | [profile](../experiments/lab3-v9/profile.json) | 77 |
| `lab5` | [profile](../labs/lab5/profile.json) | 24 |
| `lab6` | [profile](../labs/lab6/profile.json) | 32 |
| `v10` | [profile](../labs/v10/profile.json) | 87 |
| `lab3-history-v1` | [profile](../archive/profiles/lab3-history-v1/profile.json) | 12 |
| `lab3-history-v2` | [profile](../archive/profiles/lab3-history-v2/profile.json) | 22 |
| `lab3-history-v3` | [profile](../archive/profiles/lab3-history-v3/profile.json) | 29 |
| `lab3-history-v4` | [profile](../archive/profiles/lab3-history-v4/profile.json) | 34 |
| `lab3-history-v5` | [profile](../archive/profiles/lab3-history-v5/profile.json) | 48 |
| `lab3-history-v6` | [profile](../archive/profiles/lab3-history-v6/profile.json) | 53 |
| `lab3-history-v7` | [profile](../archive/profiles/lab3-history-v7/profile.json) | 55 |
| `lab3-history-v8` | [profile](../archive/profiles/lab3-history-v8/profile.json) | 61 |
| `lab3-history-v9` | [profile](../archive/profiles/lab3-history-v9/profile.json) | 79 |
| `gomoku-history-v1` | [profile](../archive/profiles/gomoku-history-v1/profile.json) | 30 |
| `gomoku-history-v2` | [profile](../archive/profiles/gomoku-history-v2/profile.json) | 37 |
| `snapshot-lab2` | [profile](../archive/profiles/snapshot-lab2/profile.json) | 13 |
| `snapshot-lab3-optimized` | [profile](../archive/profiles/snapshot-lab3-optimized/profile.json) | 79 |
| `snapshot-lab3-optimized-v10-boardfix` | [profile](../archive/profiles/snapshot-lab3-optimized-v10-boardfix/profile.json) | 87 |
| `snapshot-lab3-optimized-v10-directrect` | [profile](../archive/profiles/snapshot-lab3-optimized-v10-directrect/profile.json) | 87 |
| `snapshot-lab3-optimized-v10` | [profile](../archive/profiles/snapshot-lab3-optimized-v10/profile.json) | 87 |
| `snapshot-lab3-pixel` | [profile](../archive/profiles/snapshot-lab3-pixel/profile.json) | 83 |
| `snapshot-lab3` | [profile](../archive/profiles/snapshot-lab3/profile.json) | 15 |
| `snapshot-lab4` | [profile](../archive/profiles/snapshot-lab4/profile.json) | 15 |
| `snapshot-lab5-boardfix` | [profile](../archive/profiles/snapshot-lab5-boardfix/profile.json) | 42 |
| `snapshot-lab5` | [profile](../archive/profiles/snapshot-lab5/profile.json) | 42 |
| `arcade-v1` | [profile](../labs/arcade-v1/profile.json) | 42 |
| `arcade-v2` | [profile](../labs/arcade-v2/profile.json) | 48 |
| `snapshot-lab6-gomoku-boardfix` | [profile](../archive/profiles/snapshot-lab6-gomoku-boardfix/profile.json) | 39 |
| `snapshot-lab6-gomoku` | [profile](../archive/profiles/snapshot-lab6-gomoku/profile.json) | 39 |
| `snapshot-labs3-5` | [profile](../archive/profiles/snapshot-labs3-5/profile.json) | 59 |
| `study-lab3-coverage-study` | [profile](../archive/profiles/study-lab3-coverage-study/profile.json) | 46 |
| `study-lab3-shortspan-study` | [profile](../archive/profiles/study-lab3-shortspan-study/profile.json) | 44 |

`workspace-tools/` 是历史调试与文档整理脚本，需要原工作区和相应依赖，仅作过程参考。网络共享及配对辅助脚本可能改变设备状态，先读代码并调整本机设置；公开副本的设备地址已替换为示例。

原版、v6/v7/v8/v9、字模修复版、画点候选、直接矩形版及离线研究候选均保留。源码用补丁表达课程框架修改，不包含课程镜像、字体和二进制库。
