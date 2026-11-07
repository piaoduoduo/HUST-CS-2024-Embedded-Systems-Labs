"""Save reviewable candidate patch and evidence without changing any package."""
from pathlib import Path
import difflib,hashlib,json,tarfile
ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
result=json.loads((ROOT/'validation.json').read_text(encoding='utf-8'))
assert result['passed'] and len(result['logs'])==30
preserved=json.loads((ROOT/'preserved.json').read_text(encoding='utf-8'))
for p,h in preserved.items():assert hashlib.sha256((WS/p).read_bytes()).hexdigest()==h,p
changes=[]
for name in ('fast_pixels_v9.h','prepared_image_v9.h'):
    old=(WS/'lab3-optimized-v10-prepared/common'/name).read_text(encoding='utf-8')
    new=(ROOT/'candidate/common'/name).read_text(encoding='utf-8')
    changes.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/common/'+name,tofile='b/common/'+name))
(ROOT/'shortspan-candidate.patch').write_text(''.join(changes),encoding='utf-8')
sources=[
 {'url':'https://1037.wiki/','read':'首页搜索入口；本次未读到嵌入式课程正文，不作为实现或成绩证据'},
 {'url':'https://github.com/nivag8899/HUST-Embedded-System','read':'README实际正文；performance/O3建议已有，未发现可直接证明20ms的新实现'},
 {'url':'https://chromium.googlesource.com/libyuv/libyuv/+/refs/heads/main/source/row_neon64.cc','read':'ARGBBlendRow_NEON实际源码；采用预乘源色与/256语义，不直接替换本课程/255逐层精确混合'},
 {'url':'https://arm-software.github.io/acle/neon_intrinsics/advsimd.html','read':'vrsraq_n_u16 -> URSRA；vrshrn_n_u16 -> RSHRN。仅证明指令映射，未作ARM实测'}]
(ROOT/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
note='''2026-10-19 实验三继续离线研究：PNG与文字短区间候选

状态：独立候选，未替换v10、未发布、未上板。原版、v9、v10及公开仓库均逐文件校验未变。
源码：candidate/common/fast_pixels_v9.h、prepared_image_v9.h。
可审阅补丁：shortspan-candidate.patch，基于当前v10的两个同名头文件。

一、四像素混合打包红蓝通道
普通四像素混合由三组独立通道乘加减为两组；预计算源色乘积的四像素路径也由三组乘加减为两组。
只描述乘加组数，不代表整个内核或总程序快33%。装载、掩码与重新组合仍有成本。
16位子通道的加偏置与校正最大65407，不产生跨半字进位。
维持alpha=0保留旧32位、非零alpha输出255及/255原始舍入；没有合并透明图层。
控制开关：FB_DISABLE_PACKED_FOUR，关闭后使用v10的四像素算式。

二、八像素舍入压缩
对t=s*a+d*(255-a)，0<=t<=65025：
原式：(t+128+((t+128)>>8))>>8
新式：vrshrn_n_u16(vrsraq_n_u16(t,t,8),8)
等价整数式：(t+((t+128)>>8)+128)>>8
旧源码显式舍入序列4个向量操作，新式为URSRA、RSHRN两个映射操作。
编译器可能已将旧式的移位加法合为USRA，因此机器码净节省可能只有一条；需要实际编译检查，不能认定耗时减半。
八像素普通RGBA、字形alpha及prepared源色乘积路径均使用新舍入。
全部65026个有效分子已与(t+127)/255整数除法独立核对。
控制开关：FB_DISABLE_SHORT_ROUND，关闭后使用v10舍入。

验证：
第一项单独25项回归通过，four-only-validation.json保存当时结果。
组合候选6种配置×5项=30项通过：标量、两项开启、只关闭四像素打包、只关闭新舍入、无源色乘积缓存、LTO+2线程。
每组检查四像素穷举和保护页、行/通道独立除法oracle、PNG遮挡、文字快照生命周期、完整九阶段回放。
全部九阶段画面哈希与既有原版一致；PNG和文字都实际执行过主机测试。
NEON在主机上是语义模拟，不是ARM指令执行；模拟头仅供测试，不能带到板端代替系统arm_neon.h。
无ARM原生编译、真实FreeType新增验证或板上耗时结果。

收益判断：
复杂度仍为O(P)，属于降低常数。四像素方案不会改善不足4像素的小尾部；八像素方案只改善进入相应向量循环的部分。
不能根据局部指令组数把25—45ms的总估计直接改为20ms，也不能报可靠的20ms达标概率。
现阶段继续保留25—45ms规划范围；新增收益应由同板、同频率、同线程、同编译选项的逐工序对照决定。
未引入改材质、减少绘制次数、计时外预渲染或近似透明度。

复现：先检查check.py中的GCC路径/主机条件，运行check.py <gcc绝对路径>。
下次板测前应在v10副本应用补丁，并为两个关闭开关加入板端对照；当前默认包仍为已保留的v10。
本目录是研究候选，不是新增已验收实验版本。来源范围和链接见sources.json。
'''
(ROOT/'优化发现与验证.txt').write_text(note,encoding='utf-8')
result['candidateFiles']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'candidate/common').glob('*.h')}
result['roundingNumeratorsExhausted']=65026
(ROOT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive=ROOT/'shortspan-offline-candidate.tgz'
with tarfile.open(archive,'w:gz') as tf:
    for name in ('shortspan-candidate.patch','优化发现与验证.txt','sources.json','validation.json','four-only-validation.json','check.py'):
        tf.add(ROOT/name,arcname=name)
    for folder in ('candidate/common','candidate/neon-emulation'):
        tf.add(ROOT/folder,arcname=folder)
checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.tgz.sha256').write_text(checksum+'  '+archive.name+'\n',encoding='ascii')
progress=WS/'当前进度.txt';old=progress.read_text(encoding='utf-8')
prefix='''离线研究补充（2026-10-19，未替换v10）
实验三：新增四像素红蓝打包、八像素精确舍入两项独立候选；30项组合回归通过，九阶段画面一致。
  记录lab3-shortspan-study/优化发现与验证.txt；补丁、测试和来源均在同目录。
  无ARM原生编译或新板测；默认包仍v10，原版/v9/v10及公开仓库逐文件未变。
  总估计仍25—45ms，仅作规划；20ms尚无可靠达标判断。

'''
assert not old.startswith('离线研究补充（2026-10-19')
progress.write_text(prefix+old,encoding='utf-8')
print('Saved candidate, exactness evidence and research notes; production/public preserved')
