"""Prepare a separate board comparison package; preserve v9 and public repo."""
from pathlib import Path
import ast,hashlib,importlib.util,json,shutil,tarfile

ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
BASE=WS/'lab3-optimized-prepared';DEST=WS/'lab3-pixel-prepared'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    result=json.loads((ROOT/'correctness-results.json').read_text(encoding='utf-8'))
    assert result['passed'] and result['nineFullFrameStagesEqual']
    assert result['headerSHA256']==sha(ROOT/'pixel_fast_candidate.h')
    assert result['testSHA256']==sha(ROOT/'test_pixel_candidate.c')
    assert result['candidateSHA256']==sha(WS/'lab3-optimization-study/common/graphic-v9-pixel.c')
    if DEST.exists():raise SystemExit('Existing candidate package preserved; use a new output directory')
    baseline_manifest=sha(BASE/'manifest.json')
    shutil.copytree(BASE,DEST,ignore=shutil.ignore_patterns('__pycache__','board-comparison-*'))
    for name in ('graphic-v9-pixel.c','pixel_fast_candidate.h'):
        shutil.copy2(WS/'lab3-optimization-study/common'/name,DEST/'common'/name)
    shutil.copy2(ROOT/'test_pixel_candidate.c',DEST/'tests/test_pixel_candidate.c')
    runner=(DEST/'board_compare.py').read_text(encoding='utf-8')
    runner=runner.replace("'v9-dsu':'graphic-v9-batch.c'", "'v9-dsu':'graphic-v9-batch.c','v9-pixel-unsigned':'graphic-v9-pixel.c','v9-pixel-axis':'graphic-v9-pixel.c','v9-pixel-minmax':'graphic-v9-pixel.c'")
    runner=runner.replace("'v9-sprint','v9-dsu'", "'v9-sprint','v9-dsu','v9-pixel-unsigned','v9-pixel-axis','v9-pixel-minmax'")
    marker="        if variant=='v9-dsu':flags+=['-DFB_GEOMETRY_DSU']"
    assert marker in runner
    runner=runner.replace(marker,marker+"\n        if variant=='v9-pixel-unsigned':flags+=['-DFB_PIXEL_MODE=1']\n        if variant=='v9-pixel-axis':flags+=['-DFB_PIXEL_MODE=2']\n        if variant=='v9-pixel-minmax':flags+=['-DFB_PIXEL_MODE=3']")
    runner=runner.replace("'geometry-coalesce':'FB_DISABLE_GEOMETRY_COALESCE'", "'geometry-coalesce':'FB_DISABLE_GEOMETRY_COALESCE','pixel':'FB_DISABLE_PIXEL_FAST'")
    runner=runner.replace('analytic-lines,geometry-coalesce\'','analytic-lines,geometry-coalesce,pixel\'')
    (DEST/'board_compare.py').write_text(runner,encoding='utf-8')
    native=(DEST/'native_checks.py').read_text(encoding='utf-8')
    marker='    for name in tests:'
    assert marker in native
    native=native.replace(marker,"    if graphic=='graphic-v9-pixel.c':tests+=['test_pixel_candidate']\n"+marker,1)
    (DEST/'native_checks.py').write_text(native,encoding='utf-8')
    compare='''"""Compare unchanged point loops, immediate dirty work, identical flags."""
from pathlib import Path
import argparse,subprocess,sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--project',required=True);p.add_argument('--runs',type=int,default=5)
p.add_argument('--build-only',action='store_true');p.add_argument('--precise-timing',action='store_true')
a=p.parse_args()
command=[sys.executable,str(Path(__file__).with_name('board_compare.py')),'--project',a.project,
 '--variants','v9-sprint,v9-pixel-unsigned,v9-pixel-axis,v9-pixel-minmax','--runs',str(a.runs),
 '--threads','2','--threshold','4096','--lto','--native-cpu','--vector-report','--no-stats',
 '--governor','performance','--bind','fast','--active-wait']
if a.build_only:command+=['--build-only']
if a.precise_timing:command+=['--precise-timing']
sys.exit(subprocess.call(command))
'''
    (DEST/'run-pixel-compare.py').write_text(compare,encoding='utf-8')
    for name in ('correctness-results.json','host-benchmark-results.json'):
        shutil.copy2(ROOT/name,DEST/'evidence'/('pixel-'+name))
    notes='''画点优化独立候选（2026-10-18）

当前状态
原版、v9整包与源码保持不变；公开仓库未更新。
本包只为画点做独立对照，不替换lab3-optimized-ready.tgz。
所有157685次点调用、153600个有效点、原测试循环与计时位置保留；每个点立即写入，并立即保持精确脏区。
未将脏区计算、队列执行或绘制移到计时结束之后。

候选
v9-sprint：保留现有画点代码。
v9-pixel-unsigned：无符号坐标检查与size_t地址计算，保留原脏区更新。
v9-pixel-axis：额外判断每个轴是否已被脏区包含，内部点不再更新该轴min/max。
v9-pixel-minmax：显式min/max赋值，交给编译器选择条件指令；不承诺生成无分支代码。
FB_DISABLE_PIXEL_FAST或--disable pixel可回退原画点路径。
没有给点阵写专用预制图、删掉越界调用或改成一次矩形/网格绘制。单点API复杂度仍O(N)。

已做验证
8配置每组590个检查点、194651次点调用，覆盖即时脏区、像素、整数极限、随机alpha颜色、重复点、与矩形混用、部分刷新、清空脏区及保护区。
每配置另跑404项原基础图形回归，完整9阶段课程画面与v9/保留基线一致。
包含标量、关闭新优化、NEON算术模拟、2线程与LTO；不是ARM指令或真实板测。
主机微基准原循环不变，独立观察函数阻止编译器删除写入，完整检查在计时外；另有x86汇编供检查。
原来的4项C边界表达式已经被主机GCC合成2个无符号范围比较，不能宣称仅改unsigned就必然省一半指令。
主机LTO实验候选有改善，无LTO时axis/unsigned接近原版、minmax甚至更慢。不能把主机百分比套到RK3399。

上板待执行
将lab3-pixel-candidate-ready.tgz解压到独立位置，进入lab3-pixel-prepared：
python3 run-pixel-compare.py --project /path/to/course-project --build-only
检查真实像素/脏区/字体/完整回放和构建通过后，确认桌面与其他画屏程序已停止，再执行：
python3 run-pixel-compare.py --project /path/to/course-project --runs 5 --precise-timing
四版同flags、相同运行配置，轮转原课程测速。独立精细计时在全部原课程轮次后运行，不覆盖原成绩。
重点读取pixel和total中位数、范围及温度/频率；其他工序也要检查没有回归。
运行器记录完整源码manifest、编译命令与flags，原生检查包含test_pixel_candidate；任何错误会中止测速。

收益判断
过去原画点单次已有2ms，也有6ms，6ms不是固定下限。
LTO、绑核/调频已在v9冲刺配置中，属于原155ms与新候选差异的一部分，不能重复算成此次新增收益。
先把画点按1—3ms作为待验证优化预算而非预测/保证；若实测从6到2，总耗时可省4ms。
如果同flags的v9本来就只有1—2ms，新代码可能只能省很少。没有新增板测前，不提高20ms达标概率。
'''
    (DEST/'画点候选说明.txt').write_text(notes,encoding='utf-8')
    for path in DEST.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'),feature_version=(3,8))
    spec=importlib.util.spec_from_file_location('pixel_board_compare',DEST/'board_compare.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for name in ('v9-pixel-unsigned','v9-pixel-axis','v9-pixel-minmax'):assert mod.VARIANTS[name]=='graphic-v9-pixel.c'
    assert sha(BASE/'manifest.json')==baseline_manifest
    files=[p for p in DEST.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='manifest.json']
    hashes={p.relative_to(DEST).as_posix():sha(p) for p in files}
    original=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
    original.update({'version':'20261018-v9-pixel-candidate','sourceHashes':hashes,
                     'pixelCandidateHostValidated':True,'pixelCandidateBoardValidated':False,'pixelCandidatePerformanceMeasuredOnARM':False})
    (DEST/'manifest.json').write_text(json.dumps(original,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    archive=WS/'lab3-pixel-candidate-ready.tgz'
    if archive.exists():raise SystemExit('Existing pixel archive preserved')
    with tarfile.open(archive,'w:gz') as tar:
        for path in sorted(files+[DEST/'manifest.json']):tar.add(path,arcname=DEST.name+'/'+path.relative_to(DEST).as_posix(),recursive=False)
    with tarfile.open(archive) as tar:
        for relative,digest in hashes.items():assert hashlib.sha256(tar.extractfile(DEST.name+'/'+relative).read()).hexdigest()==digest
    archive.with_suffix('.tgz.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
    print('PASS isolated pixel candidate package, Python3.8, variants, manifest/archive hashes; old v9 unchanged')

if __name__=='__main__':main()
