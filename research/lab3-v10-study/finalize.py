"""Promote validated v10 locally while keeping v9 and public files frozen."""
from pathlib import Path
import ast,hashlib,importlib.util,json,shutil,subprocess,sys

ROOT=Path(__file__).resolve().parent;WS=ROOT.parent;PKG=WS/'lab3-optimized-v10-prepared'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    spec=importlib.util.spec_from_file_location('v10_integration_helpers',ROOT/'integrate.py')
    integration=importlib.util.module_from_spec(spec);spec.loader.exec_module(integration);integration.verify_frozen()
    result=json.loads((ROOT/'validation.json').read_text(encoding='utf-8'))
    assert result['passed'] and result['rendering']['allNineStageHashesEqual']
    assert result['graphicSHA256']==sha(PKG/'common/graphic-v10-batch.c')
    assert result['headerSHA256']==sha(PKG/'common/pixel_fast_v10.h')
    assert (PKG/'test/sprint-v10-main.c').read_bytes()==(WS/'lab3-optimized-prepared/test/sprint-v9-main.c').read_bytes()
    checked=['board_compare.py','native_checks.py','run-sprint.py','run-pixel-compare.py',
             'common/graphic-v10-batch.c','common/pixel_fast_v10.h','test/sprint-v10-main.c',
             'tests/test_pixel_candidate.c','tests/test_sprint_v10_replay.c']
    result['validatedRuntimeSourceHashes']={name:sha(PKG/name) for name in checked}
    (ROOT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    shutil.copy2(ROOT/'repack.py',PKG/'package.py')
    shutil.copy2(ROOT/'validation.json',PKG/'evidence/v10-validation.json')
    shutil.copy2(ROOT/'integration.json',PKG/'evidence/v10-integration.json')
    shutil.copy2(ROOT/'runner-results.json',PKG/'evidence/v10-runner-mocks.json')
    notes=(PKG/'v10说明.txt').read_text(encoding='utf-8')
    readme=PKG/'开始前看这里.txt';old=readme.read_text(encoding='utf-8')
    if not old.startswith('实验三 v10：'):
        readme.write_text(notes+'\n\n以下为v9及更早版本历史说明，当前入口以上文v10为准。\n\n'+old,encoding='utf-8')
    for path in PKG.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'),feature_version=(3,8))
    manifest=json.loads((PKG/'manifest.json').read_text(encoding='utf-8'))
    manifest.update({'version':'20261018-integrated-candidate-10','v10DefaultPixelMode':2,
        'v10AlternatePixelModes':[1,3],'v10HostValidated':True,'v10PixelWritesAndDirtyImmediate':True,
        'v10AllNineStagesEqual':True,'v10ArmNativeValidated':False,'v10PerformanceMeasured':False,
        'courseTestUnmodified':False,'baselineMainByteIdenticalToV9':True,
        'courseLoopsAndTimingSitesRetained':True,
        'baselineMainChangesFromCourse':'Asset-failure guard and bounded result-table formatting; original loops and timing positions retained',
        'preservedV9ArchiveSHA256':sha(WS/'resources/lab3-optimized-v9-ready.tgz')})
    files=[p for p in PKG.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='manifest.json' and not any(part.startswith('board-comparison-') for part in p.parts)]
    manifest['sourceHashes']={p.relative_to(PKG).as_posix():sha(p) for p in sorted(files)}
    (PKG/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    subprocess.run([sys.executable,str(PKG/'package.py'),'--promote-latest'],check=True)
    assert sha(WS/'lab3-optimized-ready.tgz')==sha(WS/'lab3-optimized-v10-ready.tgz')
    integration.verify_frozen()
    preserved={'lab3-ready.tgz':'349c9483f99cab1ac9d4edc7512928fe1f3004b16ed2325609a47ebfb3861984',
        'resources/lab3-optimized-v6-ready.tgz':'04c9413f1b57c2e12a1ca105caf15ed8dacd527d8731a5e0c37e13486ac58f30',
        'resources/lab3-optimized-v7-ready.tgz':'144d594f9f8a844ae1dfb616da073b1d212b17383e1b65ad5d5e59629fcc4ddd',
        'resources/lab3-optimized-v8-ready.tgz':'4936a6db6269fd3e054b95050ebd5feda578cf7e141665dbf62ab475d001ddae',
        'resources/lab3-optimized-v9-ready.tgz':'a6bfb3e6336bcee2c7197164fc1c3fce0dc455d52243463e241a78136a9b9877'}
    for name,value in preserved.items():assert sha(WS/name)==value,name
    output={'passed':True,'version':manifest['version'],'defaultPixelMode':2,
        'validationConfigurations':result['rendering']['configurations'],'allNineStagesEqual':True,
        'archiveSHA256':sha(WS/'lab3-optimized-v10-ready.tgz'),'latestPackageMatchesV10':True,
        'preservedArchives':preserved,'oldV9SourceUnchanged':True,'publicRepositoryUnchanged':True,
        'ARMCompiled':False,'boardPerformanceMeasured':False,'sourceFiles':len(files)}
    (ROOT/'verification.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (WS/'evidence/v10-package-verification.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    history=WS/'evidence/v10-20261018';history.mkdir(exist_ok=True)
    progress='''最新整合（2026-10-18 v10，以本段为准）
实验三：画点按轴脏区快路已整合，默认v10-sprint，保留unsigned/minmax及关闭pixel对照。
  v10五组整合回归、590检查点/404基础图形/9阶段画面检查通过；尚未ARM编译或板测。
  当前入口lab3-optimized-v10-prepared/开始前看这里.txt；run-sprint.py默认比较v9与v10。
  lab3-optimized-ready.tgz已指向v10，另有lab3-optimized-v10-ready.tgz。
  v9完整包resources/lab3-optimized-v9-ready.tgz和原lab3-optimized-prepared源码均未改；原版/v6/v7/v8保留。
  总耗时约25—45ms、中心约30ms仅工程规划；20ms仍属乐观目标，无可靠达标百分比。
  公开仓库逐文件与冻结zip相同，未更新；等待实验三、五、六验收反馈。
  包检查证据evidence/v10-package-verification.json。

'''
    index='''最新补充：实验三 v10（2026-10-18）
  lab3-optimized-v10-prepared/开始前看这里.txt、v10说明.txt：画点整合、版本对照与上板命令。
  lab3-optimized-v10-ready.tgz：v10版本包；lab3-optimized-ready.tgz：同步的最新包。
  resources/lab3-optimized-v9-ready.tgz、lab3-optimized-prepared：完整v9归档与原源码，均保留。
  lab3-v10-study/validation.json、verification.json：整合回归和包检查。
  公开仓库hust-embedded-labs-orangepi保持原快照，未纳入v10。

'''
    for name,prefix in [('当前进度.txt',progress),('实验材料索引.txt',index)]:
        path=WS/name;backup=history/name
        if not backup.exists():shutil.copy2(path,backup)
        current=path.read_text(encoding='utf-8')
        if not current.startswith(prefix.splitlines()[0]):path.write_text(prefix+current,encoding='utf-8')
    print('PASS final v10 default entry, archive promotion, originals/v9 preservation, frozen public snapshot')

if __name__=='__main__':main()
