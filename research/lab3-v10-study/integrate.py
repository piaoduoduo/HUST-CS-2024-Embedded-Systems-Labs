"""Integrate validated pixel candidates into an independent v10 tree."""
from pathlib import Path
import ast,hashlib,importlib.util,json,shutil,zipfile

ROOT=Path(__file__).resolve().parent;WS=ROOT.parent
BASE=WS/'lab3-pixel-prepared';DEST=WS/'lab3-optimized-v10-prepared'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def verify_frozen():
    expected='a6bfb3e6336bcee2c7197164fc1c3fce0dc455d52243463e241a78136a9b9877'
    assert sha(WS/'resources/lab3-optimized-v9-ready.tgz')==expected
    old=json.loads((WS/'lab3-optimized-prepared/manifest.json').read_text(encoding='utf-8'))
    for name,digest in old['sourceHashes'].items():assert sha(WS/'lab3-optimized-prepared'/name)==digest
    with zipfile.ZipFile(WS/'GitHub发布筹备/hust-embedded-labs-orangepi-local-snapshot.zip') as z:
        for name in z.namelist():assert z.read(name)==(WS/name).read_bytes(),name

def main():
    verify_frozen()
    previous=json.loads((WS/'lab3-pixel-study/verification.json').read_text(encoding='utf-8'))
    assert previous['passed']
    if DEST.exists():raise SystemExit('Existing v10 tree preserved')
    shutil.copytree(BASE,DEST,ignore=shutil.ignore_patterns('__pycache__','board-comparison-*'))
    shutil.copy2(BASE/'common/pixel_fast_candidate.h',DEST/'common/pixel_fast_v10.h')
    graphic=(BASE/'common/graphic-v9-pixel.c').read_text(encoding='utf-8').replace('"pixel_fast_candidate.h"','"pixel_fast_v10.h"')
    (DEST/'common/graphic-v10-batch.c').write_text(graphic,encoding='utf-8')
    shutil.copy2(BASE/'test/sprint-v9-main.c',DEST/'test/sprint-v10-main.c')
    shutil.copy2(BASE/'tests/test_sprint_v9_replay.c',DEST/'tests/test_sprint_v10_replay.c')
    assert (DEST/'test/sprint-v10-main.c').read_bytes()==(BASE/'test/sprint-v9-main.c').read_bytes()
    assert graphic.replace('"pixel_fast_v10.h"','"pixel_fast_candidate.h"')==(BASE/'common/graphic-v9-pixel.c').read_text(encoding='utf-8')
    runner=(DEST/'board_compare.py').read_text(encoding='utf-8')
    spec=importlib.util.spec_from_file_location('previous_pixel_runner',BASE/'board_compare.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    variants=dict(module.VARIANTS)
    variants.update({name:'graphic-v10-batch.c' for name in ('v10-sprint','v10-unsigned','v10-minmax')})
    start=runner.index('VARIANTS = ');end=runner.index('\n\ndef parse_metrics',start)
    runner=runner[:start]+'VARIANTS = '+repr(variants)+runner[end:]
    runner=runner.replace("'v9-pixel-minmax')","'v9-pixel-minmax','v10-sprint','v10-unsigned','v10-minmax')")
    runner=runner.replace("'v8','v9')","'v8','v9','v10')")
    runner=runner.replace("('sprint-v9-main.c' if variant.startswith('v9')", "('sprint-v10-main.c' if variant.startswith('v10') else 'sprint-v9-main.c' if variant.startswith('v9')")
    runner=runner.replace("variant.startswith('v9')","variant.startswith(('v9','v10'))")
    marker="        if variant=='v9-pixel-minmax':flags+=['-DFB_PIXEL_MODE=3']"
    assert marker in runner
    runner=runner.replace(marker,marker+"\n        if variant=='v10-sprint':flags+=['-DFB_PIXEL_MODE=2']\n        if variant=='v10-unsigned':flags+=['-DFB_PIXEL_MODE=1']\n        if variant=='v10-minmax':flags+=['-DFB_PIXEL_MODE=3']")
    runner=runner.replace("default='baseline,v4-neon,v4-parallel'","default='baseline,v9-sprint,v10-sprint'")
    marker="'v9GeometryDSURequested':variant=='v9-dsu',"
    assert marker in runner
    runner=runner.replace(marker,marker+"\n                    'pixelOptimizationModeRequested':{'v10-sprint':2,'v10-unsigned':1,'v10-minmax':3}.get(variant),\n                    'pixelOptimizationDisabled':'pixel' in disabled,")
    (DEST/'board_compare.py').write_text(runner,encoding='utf-8')
    native=(DEST/'native_checks.py').read_text(encoding='utf-8')
    native=native.replace("'v9' in graphic","('v9' in graphic or 'v10' in graphic)")
    native=native.replace("if graphic=='graphic-v9-pixel.c'", "if graphic in ('graphic-v9-pixel.c','graphic-v10-batch.c')")
    native=native.replace("for name in ('test_original_replay','test_sprint_v9_replay' if", "for name in ('test_original_replay','test_sprint_v10_replay' if 'v10' in graphic else 'test_sprint_v9_replay' if")
    (DEST/'native_checks.py').write_text(native,encoding='utf-8')
    for name in ('run-sprint.py','run-pixel-compare.py'):
        source=(DEST/name).read_text(encoding='utf-8')
        if name=='run-sprint.py':
            source=source.replace('baseline,v8-packed,v8-sprint,v9-core,v9-sprint','baseline,v9-sprint,v10-sprint,v10-unsigned,v10-minmax')
        else:
            source=source.replace('v9-sprint,v9-pixel-unsigned,v9-pixel-axis,v9-pixel-minmax','v9-sprint,v10-sprint,v10-unsigned,v10-minmax')
        (DEST/name).write_text(source,encoding='utf-8')
    for path in DEST.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'),feature_version=(3,8))
    spec=importlib.util.spec_from_file_location('v10_compare',DEST/'board_compare.py')
    current=importlib.util.module_from_spec(spec);spec.loader.exec_module(current)
    for name in ('v10-sprint','v10-unsigned','v10-minmax'):assert current.VARIANTS[name]=='graphic-v10-batch.c'
    report={'v10Created':True,'defaultPixelMode':2,'alternatePixelModes':[1,3],
            'testMainByteIdenticalToV9':True,'onlyPixelImplementationChanged':True,
            'oldV9SHA256':sha(WS/'resources/lab3-optimized-v9-ready.tgz'),
            'headerSHA256':sha(DEST/'common/pixel_fast_v10.h'),
            'graphicSHA256':sha(DEST/'common/graphic-v10-batch.c'),
            'publicRepositoryFrozen':True,'armNativeCompileValidated':False,'performanceMeasuredOnBoard':False}
    (ROOT/'integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    verify_frozen()
    print('PASS v10 integration; original test main preserved; v9 and public snapshot unchanged')

if __name__=='__main__':main()
