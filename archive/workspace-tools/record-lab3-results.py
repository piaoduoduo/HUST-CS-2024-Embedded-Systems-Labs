from pathlib import Path
import hashlib
import json
import re
import statistics
from PIL import Image

root = Path(__file__).resolve().parents[1]
evidence = root / 'evidence/lab3'
results = {}
for variant in ('baseline', 'cache', 'o3'):
    rows = []
    for run in (1, 2, 3):
        text = (evidence / f'{variant}-{run}.log').read_text(encoding='utf-8')
        row = {name: int(re.search(rf'draw {name}: (\d+) ms', text)[1])
               for name in ('pixel', 'rect', 'line', 'image', 'text')}
        row['total'] = int(re.search(r'Total time: (\d+) ms', text)[1])
        row['exitStatus'] = int(re.search(r'Program exit status: (\d+)', text)[1])
        assert row['exitStatus'] == 0
        assert row['total'] == sum(row[name] for name in ('pixel', 'rect', 'line', 'image', 'text'))
        rows.append(row)
    totals = [row['total'] for row in rows]
    results[variant] = {'runs': rows, 'medianMs': statistics.median(totals), 'minimumMs': min(totals), 'maximumMs': max(totals)}

for name in ('lab3-baseline', 'lab3-cache', 'lab3-o3', 'performance-final'):
    Image.open(evidence / f'{name}.ppm').save(evidence / f'{name}.png')
baseline = (evidence / 'lab3-baseline.ppm').read_bytes()
assert baseline == (evidence / 'lab3-cache.ppm').read_bytes() == (evidence / 'lab3-o3.ppm').read_bytes()
for name in ('glyph-cache-check.log', 'glyph-cache-o3-check.log'):
    assert 'PASS: 960 real FreeType glyph comparisons' in (evidence / name).read_text(encoding='utf-8')

report = {
    'date': '2026-10-15',
    'target': 'Orange Pi 4 LTS, Linux aarch64',
    'method': 'Same course test loops, assets and CLOCK_MONOTONIC millisecond timer; separate process for each run',
    'variants': results,
    'selectedVariant': 'o3',
    'compilerFlags': '-Wall -O3',
    'glyphCacheComparisonsPerBuild': 960,
    'renderedFramebuffersBitIdentical': True,
    'framebufferSHA256': hashlib.sha256(baseline).hexdigest(),
    'physicalLab3Display': 'User confirmed all expected image/text elements display normally',
    'TAaccepted': False,
    'TAstatus': 'Awaiting user/TA confirmation',
    'cpuGovernor': 'ondemand, unchanged',
    'cpuAffinityChanged': False,
    'evidenceImages': 'Read directly from the actual board framebuffer; not physical photographs',
}
(evidence / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: {'medianMs': v['medianMs'], 'runsMs': [r['total'] for r in v['runs']]} for k, v in results.items()}, ensure_ascii=False))
