"""Use Git credential manager in memory; never print credentials."""
import subprocess,json,urllib.request
from pathlib import Path
repo=Path(__file__).resolve().parents[1]/'hust-embedded-labs-orangepi'
result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,cwd=repo,check=True)
credential=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
token=credential.get('password')
if not token:raise SystemExit('GitHub credential unavailable')
headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'course-repository-publisher','Content-Type':'application/json'}
url='https://api.github.com/repos/piaoduoduo/--24-'
with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as response: before=json.load(response)
if before['owner']['login'].lower()!='piaoduoduo' or not before.get('permissions',{}).get('admin'):
    raise SystemExit('Repository administration permission unavailable')
payload={'name':'HUST-CS-2024-Embedded-Systems-Labs','description':'华中科技大学计算机学院24届嵌入式系统实验','has_wiki':before['has_wiki']}
with urllib.request.urlopen(urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode(),headers=headers,method='PATCH'),timeout=30) as response: after=json.load(response)
print(json.dumps({k:after[k] for k in ('full_name','html_url','description','private','default_branch')},ensure_ascii=True))
