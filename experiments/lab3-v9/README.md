# 实验三 v9：待板测候选

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

显式batch/prepared调用须与保留基线调用接口的成绩区分。基线main相对课程模板补了缺素材检查和结果表的有界字符串格式化，测试循环和计时位置保持一致，具体差异可在实验三补丁查看。
所有准备、收集、执行、释放位于相应计时内；精细诊断另行保存，不能替换原课程分数。
