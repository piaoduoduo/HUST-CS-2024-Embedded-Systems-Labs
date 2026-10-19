# 实验三：图片、字模与文字

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
