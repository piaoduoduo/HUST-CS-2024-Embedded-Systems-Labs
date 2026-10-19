# 历史离线验证摘要

记录对应2026-10-18前的离线测试，本次整理没有重新运行全部渲染穷举。

- [v9整合](v9-integrated-results.json)：16配置、9阶段画面对照。
- [PNG](v9-png-offline-results.json)：透明混合、遮挡、容量及分配失败回退。
- [文字](v9-text-offline-results.json)：有序批次、缓存寿命与输入所有权。
- [几何](v9-geometry-results.json)：精确行跨度、覆盖、边界和故障回退。

摘要删除编译器输出中的私人工作路径等原始日志，保留原记录SHA256、状态和适用字段。完整日志在本地原材料中保存。
NEON模拟与Pillow/测试字模不等于ARM和真实FreeType，回放伪时钟的0值不代表耗时。
仓库重建测试见 [tests](../../tests/)，不要求分发课程字体或SDK。
