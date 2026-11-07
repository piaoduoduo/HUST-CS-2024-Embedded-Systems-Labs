"""Export source-only, board-tested additions without changing private originals."""
from pathlib import Path
import importlib.util, json, shutil, hashlib
W=Path(__file__).resolve().parents[1]; R=W/'hust-embedded-labs-orangepi'
spec=importlib.util.spec_from_file_location('prepare',W/'tools/prepare-public-repository.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def read(p):return (R/p).read_text(encoding='utf-8')
def write(p,s):m.write(p,s)
def data(p,x):m.write_json(p,x)
catalog=json.loads(read('profiles.json'))
for name,folder in [('lab5','lab5-prepared'),('lab6','lab6-gomoku-boardfix-prepared'),('v10','lab3-optimized-v10-directrect-prepared')]:
    root=W/folder; targets={}
    if name!='v10':
        manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        for entry in manifest['files']:
            if not entry['path'].startswith('out/'):targets[entry['path']]=root/entry['path']
        for p in (root/'tests').rglob('*'):
            if p.name in ('package.py','test_installer.py','build_offline.py','audit_regressions.py'):continue
            if p.is_file() and p.suffix in ('.c','.h','.py','.sh'):targets[p.relative_to(root).as_posix()]=p
        if name=='lab5':targets['common/image.c']=W/'lab6-gomoku-boardfix-prepared/common/image.c'
        # Overlay installers inherit this unmodified file from the course tree;
        # standalone public profiles must explicitly carry the dependency.
        if 'common/task.c' not in targets:targets['common/task.c']=W/'course-source/lab-st-2026/common/task.c'
    else:
        for p in root.rglob('*'):
            rel=p.relative_to(root)
            if p.is_file() and not any(x in ('out','evidence','__pycache__') for x in rel.parts) and (p.suffix in ('.c','.h','.py','.mk') or p.name=='Makefile'):
                targets[rel.as_posix()]=p
    catalog[name]=m.collect_profile(name,targets)
data('profiles.json',catalog)
s=read('tools/materialize.py').replace("profile!='v9'","profile not in ('v9','v10')").replace("profile=='v9'","profile in ('v9','v10')").replace("'lab4','v9'))","'lab4','v9','v10','lab5','lab6'))")
s=s.replace("'public-v9-20261018-pending-board'","'public-'+profile+'-20261019'")
write('tools/materialize.py',s)
status=json.loads(read('STATUS.json'));status['updatedOn']='2026-10-19'
status['publicationAuthorized']=True;status['reportStatus']='Not yet written; will be added later'
for name in ('lab5','lab6','v10'):
    status[name]={'boardTested':True,'armCompiled':True,'taAccepted':False,'state':'实测通过，待助教验收','evidence':'results/board/trial-20261019.json'}
status['lab3']['bestMeasuredMs']=17;status['lab3']['medianMeasuredMs']=21
status['v9']['state']='原始快照保留；字模修正版已板测27/27/25ms，未将修正版覆盖原始profile'
data('STATUS.json',status)
data('results/board/trial-20261019.json',{
 'date':'2026-10-19','hardware':'Orange Pi 4 LTS','taAccepted':False,
 'lab3':{'variant':'v10-directrect + FreeType packed glyph fix','runsMs':[22,21,17],'medianMs':21,'bestMs':17,
 'stages':['pixel','rect','line','jpg','png','font','text'], 'stageRunsMs':[[1,5,5,2,7,1,1],[1,5,5,1,6,1,2],[0,4,4,1,6,1,1]],
 'environment':'gcc 9.4; O3/LTO/mcpu=native; performance; CPU4/5; OpenMP2; framebuffer1024x600 stride5120',
 'timing':'Seven integer-ms course stages; excludes decoding, display refresh and sleep; explicit batch APIs; setup of optimized batches inside timers',
 'correctness':'Actual ARM/FreeType checks and full-frame replay comparisons passed',
 'baselineSameConfigurationMs':[47,46,47], 'v9GlyphFixedMs':[27,27,25], 'v10GlyphFixedMs':[28,25,28]},
 'lab5':{'boardLog':'lab5-run.log','userConfirmed':['Chinese phone-to-board display','send button sends hello to phone','Disconnect/reconnect and both directions work'],'reconnectEvidence':'User confirmation; no separate reconnect capture'},
 'lab6':{'userConfirmed':['Chinese UI','Touch placement','AI reply','Undo'],'logConfirmed':['Clean exit','Resume saved game: 6 moves'],'remaining':'TA acceptance and exhaustive manual UI checks'}})
for src,dst in [('evidence/board-20261019/17ms重点留存/17ms-开发板原始成绩截图.png','lab3-17ms.png'),('evidence/board-20261019/17ms重点留存/17ms-第三轮原始日志.log','lab3-17ms.log'),('evidence/lab5-board-20261019/双向通信实测.png','lab5-bidirectional.png'),('evidence/lab5-board-20261019/run.log','lab5-run.log'),('evidence/lab5-board-20261019/serial-test.log','lab5-pty-test.log'),('evidence/lab6-board-20261019/gomoku-first-run.png','lab6-gomoku.png')]:
    shutil.copy2(W/src,R/'results/board'/dst)
for name,title,sub,exe in [('lab5','经典蓝牙 SPP','lab5_bt','lab5_bt'),('lab6','触屏五子棋','lab6_gomoku','lab6_gomoku')]:
    write('labs/'+name+'/README.md',f'''# {title}

2026-10-19 已完成真实开发板试运行，尚待助教验收。代码含实际板测采用的 FreeType MONO 字模转换修复。

```sh
python3 tools/materialize.py --profile {name} --course /path/to/original-course --output .work/{name} --include-assets
make -B -C .work/{name}/{sub} CC=gcc
cd .work/{name}/out
sudo ./{exe} --touch /dev/input/eventN
```

请先按[快速开始](../../docs/quick-start.md)检查依赖、桌面与 framebuffer。eventN 必须用当前实际触屏设备替换，不能固定为某次实验的编号。

实测范围见[本次记录](../../results/board/trial-20261019.json)。完整课程素材需自行取得，仓库不附字体或外部库。
''')
write('labs/lab5/README.md',read('labs/lab5/README.md')+'''
手机使用经典 SPP 蓝牙串口应用。板端需要 BlueZ 的 SPP 服务记录（RFCOMM channel 1）和 `sudo rfcomm -r watch 0 1` 监听，应用等待 `/dev/rfcomm0`。
配对时保持 `bluetoothctl` 的 agent 活跃，核对手机与板端验证码后确认；关闭会话会移除临时 agent。不要公开手机地址、配对码或自动信任任意设备。
实测：手机中文正常显示，触屏 send 后手机收到 hello，应用内断开重连后双向收发正常。Linux PTY 测试另有日志，它不替代无线实测。

![真实板端接收画面](../../results/board/lab5-bidirectional.png)
''')
write('labs/lab6/README.md',read('labs/lab6/README.md')+'''
已实测落点、电脑应答、悔棋、正常退出及恢复6手存档。AI 对局与存档不等同于所有 UI 边界都已人工遍历；正式验收后再补记录。

![真实开发板五子棋](../../results/board/lab6-gomoku.png)
''')
write('labs/v10/README.md','''# 实验三：v10 直接矩形板测版

三轮22/21/17ms，中位数21ms，最佳17ms；不能声称稳定17ms。原版与v9另行保留。

```sh
python3 tools/materialize.py --profile v10 --course /path/to/original-course --output .work/v10 --include-assets
python3 .work/v10/board_compare.py --project /path/to/original-course --variants baseline,v9-sprint,v10-sprint --runs 3 --threads 2 --threshold 4096 --lto --native-cpu --vector-report --no-stats --governor performance --bind fast --active-wait
```

在板上安装所需开发库后执行；先检查 framebuffer 和桌面冲突。对照工具运行原生正确性检查。性能设置为临时设置，结束时恢复；不要断电中断。
本版矩形恢复直接填充，其余沿用v10；真实FreeType小字模需展开MONO/GRAY2/GRAY4，避免把压缩位图当8位alpha。
使用显式批量接口，计算仍在计时内；课程七段计时不含解码、刷新和sleep。是否接受该接口由当期助教决定。
详细分项和环境见[实测数据](../../results/board/trial-20261019.json)。0ms为整数计时分辨率，不代表零工作。

![真实17ms成绩表](../../results/board/lab3-17ms.png)
''')
s=read('README.md'); start=s.index('**状态快照');end=s.index('\n## 先看这些',start)
s=s[:start]+'**状态快照：2026-10-19。** 实验一、二已获用户确认验收；实验三、四、五、六已有实测，尚未记录正式验收。实验报告待写完后补充。\n'+s[end:]
s=s.replace('| **待板测** |','| 原始候选保留，详见状态记录 |',1).replace('| **待板测** |','| 实测双向收发与重连通过，待验收 |',1).replace('| **待板测** |','| 实测对局、悔棋与存档恢复通过，待验收 |',1)
s=s.replace('实验二至四与 v9','实验二至六、v9 与 [v10板测版](labs/v10/README.md)')
start=s.index('v9 的 PNG');end=s.index('\n## 验证本仓库',start)
s=s[:start]+'''最新[v10直接矩形版](labs/v10/README.md)三轮 **22 / 21 / 17 ms，中位数21ms**。同配置原接口基线47 / 46 / 47ms。旧155ms的CPU和编译配置不同，不能把全部提升归因于算法。优化版使用显式批量接口；公开原始口径和真实分项，不采用估计值。

![17ms真实成绩](results/board/lab3-17ms.png)
'''+s[end:];write('README.md',s)
write('docs/status-and-updates.md','''# 状态与后续更新

2026-10-19 用户授权先公开代码与实测材料，报告稍后补充。
实验一、二已确认验收；三、四、五、六实测不等于助教验收。[STATUS.json](../STATUS.json)记录精确状态。
原v9快照不覆盖；真实板测修正版与最佳v10区别见[优化过程](lab3-optimization.md)。
后续取得正式验收反馈后补日期、版本和证据；报告写完再添加，不提前伪造报告或验收。
本地原材料和历史归档完整保留，公开版本排除私人连接标识、字体、镜像及第三方二进制。
''')
for path in ('docs/lab3-optimization.md','results/board/README.md'):
    write(path,read(path)+'\n\n## 2026-10-19 实测更新（取代以上旧待板测状态）\n\n见[实测记录]('+('../board/' if path.startswith('results') else '../results/board/')+'trial-20261019.json)。v9字模修正版27/27/25ms，v10字模修正版28/25/28ms；直接矩形版22/21/17ms。原v9代码快照仍保留。三、五、六均待正式验收，报告稍后补充。\n')
write('CHANGELOG.md','## 2026-10-19\n\n新增v10板测版、实验五/六代码profile和真实画面；记录17ms最佳/21ms中位数、SPP重连以及五子棋恢复；尚未正式验收，报告后补。\n\n'+read('CHANGELOG.md'))
s=read('tools/check-repository.py');a=s.index("    assert status['remotePublished']");b=s.index("    results=json.loads",a)
s=s[:a]+"    trial=json.loads((ROOT/'results/board/trial-20261019.json').read_text(encoding='utf-8'))\n    assert trial['lab3']['runsMs']==[22,21,17] and trial['lab3']['medianMs']==21\n    for name in ('v10','lab5','lab6'):\n        assert status[name]['boardTested'] and not status[name]['taAccepted']\n"+s[b:];write('tools/check-repository.py',s)
print('Updated source profiles and actual evidence; original packages unchanged.')
