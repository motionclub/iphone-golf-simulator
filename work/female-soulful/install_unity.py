"""Install only the explicit female implementation from the disposable Editor clone."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parent;repo=root.parent.parent
source=Path('/private/tmp/female-soulful-UnityClone/Assets');dest=repo/'Unity/Assets'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()if p.exists()else None
installed=json.loads((root/'IMPLEMENTATION_MANIFEST.json').read_text())
baseline={'files':{k.removeprefix('Unity/Assets/'):{'productionSha256':v['afterSha256']}for k,v in installed['files'].items()}}
paths=json.loads((root/'pending-unity-paths.json').read_text())
extra=root/'revisions/armholes-motion-v2/shared-before.json'
if extra.exists():
 for name,value in json.loads(extra.read_text()).items():
  if 'Unity/Assets/'+name not in installed['files'] and sha(dest/name)!=value:raise RuntimeError('Concurrent added-path edit: '+name)
for name,info in baseline['files'].items():
 if sha(dest/name)!=info['productionSha256']:raise RuntimeError('Concurrent edit: '+name)
rows={}
for name in paths:
 src=source/name;out=dest/name
 if not src.exists():raise RuntimeError('Missing '+name)
 rows['Unity/Assets/'+name]={'beforeSha256':installed['files'].get('Unity/Assets/'+name,{}).get('beforeSha256',sha(out)),'afterSha256':sha(src)}
for name in paths:
 out=dest/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,out)
(root/'IMPLEMENTATION_MANIFEST.json').write_text(json.dumps({'status':'Installed in repository; user visual review owns appearance acceptance','originalFacePreserved':True,'phonePerformance':'Deferred by user','files':rows},indent=2))
print('Installed',len(paths),'explicit Unity paths')
