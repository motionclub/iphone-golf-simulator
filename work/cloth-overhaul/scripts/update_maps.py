from pathlib import Path
import hashlib,json,shutil
W=Path(__file__).resolve().parents[1];R=W.parents[1];rows=json.loads((W/'installed_files.json').read_text())
for row in rows:
 p=R/row['path']
 if p.name.endswith('.png') and ('_N.' in p.name or '_M.' in p.name or p.name=='Cloth_FabricAtlas.png'):
  assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],('Concurrent map edit',p)
  src=W/'maps'/p.name
  for dst in [p,W/'isolation/Unity/Assets/Resources/Tennis/HeroDetail'/p.name,W/'locker/assets'/('MatchHero_'+p.name)]:shutil.copy2(src,dst)
 row['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
(W/'installed_files.json').write_text(json.dumps(rows,indent=2))
