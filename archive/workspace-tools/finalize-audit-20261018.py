"""Verify this review's artifacts and record progress without board claims."""
from pathlib import Path
import hashlib
import json
import tarfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'evidence/audit-20261018'
EVIDENCE.mkdir(parents=True, exist_ok=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


preserved = {
    'lab3-ready.tgz': '349c9483f99cab1ac9d4edc7512928fe1f3004b16ed2325609a47ebfb3861984',
    'lab3-optimized-ready.tgz': '4936a6db6269fd3e054b95050ebd5feda578cf7e141665dbf62ab475d001ddae',
    'resources/lab3-optimized-v6-ready.tgz': '04c9413f1b57c2e12a1ca105caf15ed8dacd527d8731a5e0c37e13486ac58f30',
    'resources/lab3-optimized-v7-ready.tgz': '144d594f9f8a844ae1dfb616da073b1d212b17383e1b65ad5d5e59629fcc4ddd',
    'resources/lab6-gomoku-v2-ready.tgz': 'f46d0213eb140713bb17f38cd105e9e2248da92a20ce195f8216df4634692214',
}
for name, digest in preserved.items():
    assert sha(ROOT/name) == digest, name

packages = {}
for directory, filename in [('lab5-prepared', 'lab5-ready.tgz'),
                            ('lab6-gomoku-prepared', 'lab6-gomoku-ready.tgz')]:
    folder = ROOT/directory
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        assert sha(folder/entry['path']) == entry['sha256'], entry['path']
    total = 0
    with tarfile.open(ROOT/filename, 'r:gz') as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            local = (ROOT/member.name).resolve()
            local.relative_to(folder.resolve())
            assert archive.extractfile(member).read() == local.read_bytes(), member.name
            total += 1
    digest = sha(ROOT/filename)
    assert (ROOT/(filename+'.sha256')).read_text(encoding='ascii').split()[0] == digest
    packages[filename] = {'sha256': digest, 'filesVerified': total, 'version': manifest['version']}

for name in ('touch.c', 'touch_protocol.c', 'touch_protocol.h', 'graphic.c', 'image.c'):
    assert (ROOT/'lab5-prepared/common'/name).read_bytes() == (ROOT/'lab6-gomoku-prepared/common'/name).read_bytes(), name

audit = ROOT/'lab3-optimization-study/audit-20261018'
report = {
    'date': '2026-10-18', 'hardwareValidatedThisReview': False,
    'performanceMeasuredThisReview': False, 'preservedArchives': preserved,
    'newPackages': packages, 'lab5Lab6SharedCodeConsistent': True,
    'lab3ProductionPackageUnchanged': True,
    'lab3AnalysisHashes': {p.name: sha(p) for p in sorted(audit.iterdir()) if p.is_file()},
    'reports': ['实验3-5-6复审-20261018.txt', 'lab5-prepared/20261018审计记录.txt',
                'lab6-gomoku-prepared/代码审计-20261018.txt'],
}
(EVIDENCE/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

status = '''最新复审（2026-10-18，以本段为准；后文保留历史记录）
实验三：原155ms实测仍有效；v8包和原版/v6/v7完整保留，本次未上板。
  新验证PNG后续不透明遮挡剔除，可少23.14%半透明混合；矩形/直线覆盖消除PoC及精确光栅验证通过。
  这些为独立算法研究，尚未合入v8；20ms不是已达到或可靠预计的成绩。
  新增独立精细计时生成工具，通过主机注入时钟检查，待板上诊断。
实验五：新增lab5-ready.tgz与lab5-prepared，修断连重试、收发限额、会话残留及首触点初始化。
  主机状态/交互/安装测试通过；配对、Linux PTY、无线双向收发、真实屏幕和验收仍待完成。
实验六：lab6-gomoku-ready.tgz升级v3，修首触点、实际3秒确认、未保存提示、恢复日志与历史升级。
  旧v2完整保存在resources/lab6-gomoku-v2-ready.tgz；规则/状态/模拟界面及安装验证通过。
  ARM编译、触摸、Linux存储/锁和实际AI/存档响应仍待上板。
实验五与六公共代码已对齐，并验证交替安装不降级；旧lab4和旧labs3-5总包保持不变。
总复审：实验3-5-6复审-20261018.txt；最终包校验：evidence/audit-20261018/verification.json。

'''
progress = ROOT/'当前进度.txt'
old = progress.read_text(encoding='utf-8')
if not old.startswith(status.splitlines()[0]):
    progress.write_text(status+old, encoding='utf-8')

index_text = '''

2026-10-18 实验三、五、六复审材料
  实验3-5-6复审-20261018.txt：总审计、修复、复杂度和接板检查顺序。
  lab5-ready.tgz / lab5-prepared：新的实验五独立审计修复包，优先使用，保留已用字模缓存。
  lab6-gomoku-ready.tgz / lab6-gomoku-prepared：五子棋v3审计修复包。
  resources/lab6-gomoku-v2-ready.tgz：上版完整回退包。
  lab3-optimization-study/audit-20261018：PNG遮挡验证、矩形/直线覆盖消除PoC、精细计时工具。
  evidence/audit-20261018/verification.json：原包保留、新包逐文件校验和材料哈希。
  本轮没有ARM/无线/触摸实测，没有20ms或40ms新成绩；实验三v8正式候选包未修改。
'''
index = ROOT/'实验材料索引.txt'
old_index = index.read_text(encoding='utf-8')
if '2026-10-18 实验三、五、六复审材料' not in old_index:
    index.write_text(old_index+index_text, encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
