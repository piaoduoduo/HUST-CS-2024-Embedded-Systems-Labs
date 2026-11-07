"""Reuse the checked runner mock with the new four pixel comparison modes."""
from pathlib import Path

ROOT=Path(__file__).resolve().parent
STUDY=ROOT.parent/'lab3-optimization-study'
source=(STUDY/'test_v9_precise_runner.py').read_text(encoding='utf-8')
source=source.replace("ROOT=Path(__file__).resolve().parent", "ROOT=Path("+repr(str(STUDY))+")")
source=source.replace("RUNNER=ROOT.parent/'lab3-optimized-prepared/board_compare.py'", "RUNNER=ROOT.parent/'lab3-pixel-prepared/board_compare.py'")
source=source.replace("BUILD=ROOT/'build-v9-timing-tests'", "BUILD=ROOT.parent/'lab3-pixel-study/build-runner-tests'")
source=source.replace('baseline,v8-sprint,v9-sprint,v9-dsu','v9-sprint,v9-pixel-unsigned,v9-pixel-axis,v9-pixel-minmax')
source=source.replace("'--disable','geometry-coalesce'", "'--disable','pixel'")
source=source.replace("    assert '-DFB_GEOMETRY_DSU' in result['commands']['v9-dsu']", "    for pixel_mode,pixel_name in ((1,'unsigned'),(2,'axis'),(3,'minmax')):\n        cmd=result['commands']['v9-pixel-'+pixel_name]\n        assert '-DFB_PIXEL_MODE='+str(pixel_mode) in cmd\n        assert '-fopenmp' in cmd and '-flto' in cmd\n        assert any(Path(arg).name=='sprint-v9-main.c' for arg in cmd)\n        assert '-DFB_DISABLE_PIXEL_FAST' in cmd")
source=source.replace("    assert '-DFB_DISABLE_GEOMETRY_COALESCE' in result['commands']['v9-sprint']", "    assert '-DFB_DISABLE_PIXEL_FAST' in result['commands']['v9-sprint']")
source=source.replace("(ROOT/'v9-precise-runner-results.json')", "(ROOT.parent/'lab3-pixel-study/runner-results.json')")
exec(compile(source,str(ROOT/'adapted-runner-mock.py'),'exec'),{'__name__':'__main__','__file__':str(ROOT/'adapted-runner-mock.py')})
