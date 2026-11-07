from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
correct=json.loads((ROOT/'correctness-results.json').read_text(encoding='utf-8'))
bench=json.loads((ROOT/'host-benchmark-results.json').read_text(encoding='utf-8'))
runner=json.loads((ROOT/'runner-results.json').read_text(encoding='utf-8'))
assert correct['passed'] and correct['headerSHA256']==sha(ROOT/'pixel_fast_candidate.h')
assert bench['headerSHA256']==correct['headerSHA256']
assert all(x['passed'] for x in runner['scenarios'].values())
v9=json.loads((WS/'lab3-optimization-study/v9-integrated-results.json').read_text(encoding='utf-8'))
for name,digest in v9['sourceHashes'].items():assert sha(WS/'lab3-optimization-study'/name)==digest
assert sha(WS/'lab3-optimized-ready.tgz')=='a6bfb3e6336bcee2c7197164fc1c3fce0dc455d52243463e241a78136a9b9877'
assert sha(WS/'resources/lab3-optimized-v9-ready.tgz')==sha(WS/'lab3-optimized-ready.tgz')
public_archive=WS/'GitHub发布筹备/hust-embedded-labs-orangepi-local-snapshot.zip'
with zipfile.ZipFile(public_archive) as z:
    for name in z.namelist():assert z.read(name)==(WS/name).read_bytes(),('public snapshot changed',name)
package=WS/'lab3-pixel-prepared';manifest=json.loads((package/'manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['sourceHashes'].items():assert sha(package/name)==digest
report={'passed':True,'oldV9AndOriginalSourcesUnchanged':True,'publicRepositoryMatchesFrozenSnapshot':True,
        'pixelCandidateArchiveSHA256':sha(WS/'lab3-pixel-candidate-ready.tgz'),
        'hostCorrectnessConfigurations':correct['configurations'],'allNineStageHashesEqual':True,
        'runnerPlanMocksPassed':True,'hostMicrobenchmarkRun':True,'ARMCompiled':False,'boardPerformanceMeasured':False}
(ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
rows=[]
for name in ('v9-calls','unsigned-calls','axis-calls','minmax-calls','v9-lto','unsigned-lto','axis-lto','minmax-lto'):
    rows.append('%-16s %.2f us (host-only)'%(name,bench['results'][name]['medianNs']/1000))
note=(package/'画点候选说明.txt').read_text(encoding='utf-8')
note+='\n本机微基准中位数（仅x86电脑，不能换算成板上ms）\n'+'\n'.join(rows)+'\n'
note+='\n对照入口已验证编译flags、原循环main选择、可关闭pixel和精细计时分离；模拟日志中的84ms/14ms是注入数据，不是性能结果。\n'
note+='公开仓库逐文件与冻结zip一致，未触发验收后更新。详细总检查：verification.json。\n'
(ROOT/'研究结论.txt').write_text(note,encoding='utf-8')
print('PASS pixel candidate, v9 preservation, frozen public repository, package hashes and independent runner checks')
