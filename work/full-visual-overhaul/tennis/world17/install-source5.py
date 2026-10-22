from pathlib import Path
import shutil,hashlib,json
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=Path(__file__).parent;A=R/'ArtDir/tennis/audience';U=R/'Unity/Assets';installed=[]
for n in ['TennisPromenadeHero3','TennisSeatedHero3']:
 p=U/'Resources/Tennis/Premium'/(n+'.fbx');shutil.copy2(A/'staging5'/(n+'.fbx'),p);installed.append(p)
 shutil.copy2(A/'staging5'/(n+'.blend'),A/'source'/(n.replace('Hero3','Hero5')+'.blend'))
for n in ['TennisResortCrowd.cs']:
 p=U/'Scripts/Tennis'/n;shutil.copy2(W/n,p);installed.append(p)
for n in ['TennisAudienceProof.cs','TennisPromenadeFilm.cs','TennisNpcInventory.cs']:
 p=U/'Editor'/n;shutil.copy2(W/n,p);installed.append(p)
manifest=[dict(path=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in installed]
(R/'proof/full-visual-overhaul/tennis/audience5-installed-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
files=[p for p in A.rglob('*') if p.is_file() and p.suffix in ['.py','.blend','.fbx'] and '__pycache__' not in str(p)]
(A/'source-manifest.json').write_text(json.dumps([dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],indent=2)+'\n')
print(json.dumps(manifest,indent=2))
