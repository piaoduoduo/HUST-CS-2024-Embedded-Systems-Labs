from pathlib import Path
import json,hashlib,tarfile
root=Path(__file__).resolve().parent.parent
e=root/'evidence/board-20261019'
first=json.loads((e/'lab3-optimized-v10-boardfix-prepared/board-comparison-qf48wngw/trial-measurements/results.json').read_text(encoding='utf-8'))
lines=['2026-10-19 开发板真实试运行记录','', '连接：安卓手机热点＋SSH，板端192.168.43.160（后续可能变化）。',
'环境：Orange Pi 4 LTS，gcc 9.4，O3/LTO/native，performance，CPU 4/5，2线程；1024x600，32bpp，stride5120。',
'计时：课程七阶段整数毫秒相加，不包含解码、刷新和sleep；优化方案使用显式批量接口。',
'旧155ms与本次配置不同，不能将全部差异归因于算法。',
'首次原v10验证发现真实TTC小字号MONO字模误作8位alpha的问题；独立板测修正版已补格式转换。',
'原版、v9/v10包、公开仓库保持不变。', '', '第一组：每版本三轮，交替顺序']
for name in ('baseline','v9-sprint','v10-sprint'):
 vals=[r['timingsMs']['total'] for r in first['runs'] if r['variant']==name]
 lines.append(f'{name}: {vals} ms；总耗时中位数 {first["medianMs"][name]["total"]} ms')
paths=list(e.glob('lab3-optimized-v10-directrect-prepared/board-comparison-*/results.json'))
if paths:
 data=json.loads(paths[0].read_text(encoding='utf-8'))
 assert json.loads(paths[0].with_name('runtime-controls.json').read_text(encoding='utf-8'))['restored']
 lines+=['','第二组：仅将矩形替换为实测较快的基线直接绘制，保留v10其余优化与字模修复。']
 for r in data['runs']:lines.append(f'第{r["iteration"]}轮：{r["timingsMs"]}')
 lines.append('分项中位数：'+str(data['medianMs']))
 lines.append('注意：分项中位数之和不一定等于总耗时中位数。0ms表示整数计时未跨毫秒刻度，不表示无工作。')
 lines+=['真实ARM及FreeType验证、完整画面回放一致性已通过；临时CPU设置已恢复，板上暂保留成绩表。',
'最新重复PNG/文字行复用研究未整合进此版本。',
'直线、PNG等后续优化以此次实际分项为依据。']
(e/'试运行结果.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
candidate=root/'lab3-optimized-v10-directrect-prepared'
package=root/'lab3-optimized-v10-directrect-ready.tgz'
with tarfile.open(package,'w:gz') as t:t.add(candidate,arcname=candidate.name,filter=lambda m:None if '__pycache__' in m.name else m)
Path(str(package)+'.sha256').write_text(hashlib.sha256(package.read_bytes()).hexdigest()+'  '+package.name+'\n',encoding='utf-8')
