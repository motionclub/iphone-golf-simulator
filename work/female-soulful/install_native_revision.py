"""Install female-only exports and goldens without replacing any male payload."""
from pathlib import Path
import json,hashlib,shutil,subprocess,datetime
root=Path(__file__).resolve().parent;repo=root.parent.parent
src=root/'native-arm-surfaces';dst=repo/'GolfArcade/Unity/CharacterAssets';gold=repo/'GolfArcadeTests/VisualGolden'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changed=set(json.loads((root/'native-changed-paths.json').read_text()))
rows=json.loads((gold/'provenance.json').read_text())
expected=['MatchHero_Female','MatchHero_Female_Distance','GolfKitHero_Female']
for name in expected:
 for suffix in ['.json','.lzfse','_Rig.lzfse']:
  if not(src/'assets'/(name+suffix)).exists():raise RuntimeError('Incomplete female export '+name+suffix)
 if not(src/'golden'/(name+'_golden.json')).exists():raise RuntimeError('Missing golden '+name)
for p in (src/'assets').iterdir():
 if not p.is_file():continue
 if 'Female' not in p.name:continue
 q=dst/p.name
 if not q.exists()or sha(p)!=sha(q):shutil.copy2(p,q);changed.add(str(q.relative_to(repo)))
paths=[s.strip()for s in (repo/'work/hero-sync/look_sources.txt').read_text().splitlines()if s.strip()and not s.startswith('#')]
look={s:sha(repo/s)for s in paths};heads={s:v for s,v in look.items()if s.startswith('Unity/Assets/Resources/Tennis/OriginalSeamBlinkFinish/')}
for row in rows:
 name=row['name'];row['heroLookSourceFiles']=look
 if name in expected:
  p=src/'golden'/(name+'_golden.json');packed=gold/(name+'_golden.lzfse')
  subprocess.run([str(repo/'work/hero-sync/out/PackGolden'),str(p),str(packed)],check=True)
  row.update(source=str(p.relative_to(repo)),unitySampleCount=len(json.loads(p.read_text())['samples']),unitySourceSha256=sha(p),packedSha256=sha(packed),packedBytes=packed.stat().st_size,manifestSha256=sha(dst/(name+'.json')),frozenFaceSourceFiles=heads,note='Female revision: independent garment armholes/sleeves, repaired arm volume and female-only skin/fabric shaders. Neutral body/face vertices and source rig/clips retained.')
  changed.add(str(packed.relative_to(repo)))
 else:
  if row['manifestSha256']!=sha(dst/(name+'.json')):raise RuntimeError('Unexpected male payload change '+name)
  row['note']='Male payload retained unchanged; arm skinning and material branches are female only.'
(gold/'provenance.json').write_text(json.dumps(rows,indent=2)+'\n');changed.add(str((gold/'provenance.json').relative_to(repo)))
(root/'native-changed-paths.json').write_text(json.dumps(sorted(changed),indent=2))
print('Female-only payloads installed; male payload hashes retained')
