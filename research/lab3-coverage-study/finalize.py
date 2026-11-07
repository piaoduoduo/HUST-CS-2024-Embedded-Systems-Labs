from pathlib import Path
import difflib,hashlib,json,tarfile
ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
validation=json.loads((ROOT/'validation.json').read_text(encoding='utf-8'))
assert validation['passed'] and len(validation['logs'])==23
for p,h in json.loads((ROOT/'preserved.json').read_text(encoding='utf-8')).items():assert hashlib.sha256((WS/p).read_bytes()).hexdigest()==h,p
bench=json.loads((ROOT/'host-benchmark.json').read_text(encoding='utf-8'))
bench['allCandidateRatios']={workload:{variant:value/d['interval'] for variant,value in d.items()} for workload,d in bench['mediansMs'].items()}
bench['recommendation']='Keep existing default. Course workload benefit not established; bitset family helps fragmented synthetic workload only in these host runs.'
(ROOT/'host-benchmark.json').write_text(json.dumps(bench,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
patch=[];changed={}
for p in sorted((ROOT/'candidate/common').iterdir()):
    if not p.is_file():continue
    old=WS/'lab3-optimized-v10-prepared/common'/p.name
    before=old.read_text(encoding='utf-8') if old.exists() else ''
    after=p.read_text(encoding='utf-8')
    if before!=after:
        patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/common/'+p.name if old.exists() else '/dev/null',tofile='b/common/'+p.name))
        changed[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT/'combined-candidate.patch').write_text(''.join(patch),encoding='utf-8')
rows=[]
for workload,d in bench['mediansMs'].items():
    rows.append(workload+': '+', '.join(f'{k}={v:.6f} ms' for k,v in d.items()))
note='''2026-10-19 实验三覆盖算法离线研究

结论：不替换默认v10。新增候选通过正确性验证，但未在课程原负载上证明稳定速度收益。
原版、v9、v10、上一轮短区间研究包和公开仓库均逐文件校验未变。

本轮实现三种候选：
1. FB_OPAQUE_BITSET：逆序按64位覆盖图取尚未覆盖的连续段，直接拷贝最终可见像素。
2. FB_OPAQUE_ADAPTIVE：少量有序区间沿用原算法，区间数量到8后转覆盖图。
3. FB_OPAQUE_FAST：在混合方案上增加单个连续区间的直接左右扩展/完全覆盖快路。
三者保留原提交顺序对应的最终写入者，保持脏区、RGB全部32位字节、裁剪及队列分批语义。
默认不定义上述宏，继续选择原有区间算法。

算法复杂度（每目标行）：
原有有序区间表最坏O(B*min(B,W)+U)，反复插入/合并时会出现二次比较与搬移。
纯覆盖图为O(B*ceil(W/64)+R+U)，R为连续拷贝段数，U为拷贝像素数；空间O(ceil(W/64))。
混合方案将区间表规模限制在常数阈值附近，越过阈值时保留已覆盖状态并只处理剩余命令。
这是一般零散输入的最坏情况改进，不意味着课程原负载更快；课程已有区间通常接近一个连续区间。
覆盖图的stats.interval_comparisons字段记录覆盖字访问，不能和旧算法的区间比较数等同解读。

验证：
8组配置各有69个全帧对照及完整9阶段回放；包含强制第一区间切换、小队列、多线程/LTO及前轮PNG/文字候选共同运行。
所有九阶段哈希与原版相同。随机交叠、裁剪、源图padding、越界哨兵、队列溢出和脏区检查通过。
宽度1/63/64/65/127/1024/1031下，三种候选各1000例，合计21000个独立正序oracle对照通过。
没有ARM原生编译或板测；多线程测试中的NEON为语义模拟。

主机微基准：
x86 GCC8.1，O3，无LTO，无NEON模拟；每负载/算法9轮交错测试，计时内只执行600行的渲染。
输出校验使用独立编译单元的observer在计时后读取全部像素，防止无用写入被消除。
最后一轮在本任务的正确性编译结束后单独执行；系统频率与其它应用仍不可控。
以下为最后一轮中位数，不是整项JPEG成绩，更不是ARM预测：
'''+ '\n'.join(rows)+'''
纯覆盖图在课程负载约为旧版2.27倍耗时；零散负载约0.50倍。
连续区间快路此前一轮略快、最后一轮约慢6%，尚不能认定稳定收益，因此未晋级。
课程JPEG素材解码和fb_update本来就在计时区间外，本轮未改变；本微基准进一步排除了批次建立/提交/释放。
不能把零散负载的约50%收益套用到课程JPEG或实验总耗时。

成果和后续：
candidate/common保留全部研究源码；combined-candidate.patch以v10为基线，包含前轮PNG/文字短区间候选和本轮三种覆盖候选。
不应将组合补丁当成已验证更快的新正式版本；默认包、入口和公开资料均未替换。
现有25—45ms总规划范围没有新的板测依据可调整，20ms仍需真实逐项数据支撑。
下一次接板优先测试前轮PNG/文字短区间候选，覆盖图仅作为可选消融项，不应默认开启。

参考检索范围：本轮再次读取GitHub往届仓库README与1037.wiki首页，未读到新的20ms实现或1037课程正文。
https://github.com/nivag8899/HUST-Embedded-System
https://1037.wiki/
本轮覆盖算法来自对当前源码的推导与独立oracle核验，没有把学长项目成绩当作本项目成绩。
'''
(ROOT/'优化研究结论.txt').write_text(note,encoding='utf-8')
validation.update({'changedCandidateSHA256':changed,'widthOracleComparisons':21000,'defaultPromoted':False})
(ROOT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive=ROOT/'coverage-offline-study.tgz'
with tarfile.open(archive,'w:gz') as tf:
    for folder in ('candidate/common',):tf.add(ROOT/folder,arcname=folder)
    for p in ROOT.iterdir():
        if p.is_file() and p.suffix in ('.py','.c','.h','.json','.txt','.patch','.log'):tf.add(p,arcname=p.name)
archive.with_suffix('.tgz.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n',encoding='ascii')
progress=WS/'当前进度.txt';s=progress.read_text(encoding='utf-8')
prefix='''覆盖算法研究补充（2026-10-19，未晋级默认版本）
实验三：实现JPEG覆盖图、区间混合和连续区间快路；8组完整回放及21000个宽度边界对照通过。
  课程原负载未见稳定主机收益，候选仅保留在lab3-coverage-study，未替换v10或上一轮短区间研究包。
  结论lab3-coverage-study/优化研究结论.txt；原版/v9/v10及公开仓库逐文件未变。
  总耗时估计和20ms达标判断没有新的板测依据可调整。

'''
assert not s.startswith('覆盖算法研究补充（2026-10-19')
progress.write_text(prefix+s,encoding='utf-8')
print('Saved rejected/default-off candidates, exactness evidence and honest performance findings')
