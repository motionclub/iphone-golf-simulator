from pathlib import Path
import shutil,json,hashlib,sys
W=Path(__file__).resolve().parents[1];R=W.parents[1];U=W/'Unity';B=W/'rollback/followthrough-baseline/production';apply='--apply' in sys.argv
pairs=[]
for sex in ['Male','Female']:
 for rel in [f'Assets/Characters/GolfHeroKit/{sex}_Kit.fbx',f'Assets/Resources/Tennis/Customization/Player{sex}GolfKit.prefab',f'Assets/Resources/Golf/Fitted_{sex}_Top.asset',f'Assets/Resources/Golf/Fitted_{sex}_Body.asset']:
  for suffix in ['', '.meta']:pairs.append((U/(rel+suffix),R/'Unity'/(rel+suffix)))
 for ext in ['json','lzfse']:pairs.append((W/'native'/f'GolfKitHero_{sex}.{ext}',R/'GolfArcade/Unity/CharacterAssets'/f'GolfKitHero_{sex}.{ext}'))
 pairs.append((W/'export'/f'Golf_{sex}_Draft.blend',R/'ArtDir/hero/kit/golf/tailoring/source'/f'Golf_{sex}.blend'))
for p in (W/'maps').glob('*.png'):
 for suffix in ['', '.meta']:
  name=p.name+suffix;pairs.append((U/'Assets/Resources/Golf/HeroDetail'/name,R/'Unity/Assets/Resources/Golf/HeroDetail'/name))
for p in (W/'native').glob('*.ktx'):pairs.append((p,R/'GolfArcade/Unity/CharacterAssets'/p.name))
for p in (U/'Assets/Characters/GolfHeroKit/Materials').glob('*.mat'):pairs.append((p,R/'Unity/Assets/Characters/GolfHeroKit/Materials'/p.name))

for rel in ['Assets/Scripts/Game/GolfSwingClearance.cs','Assets/Scripts/Game/GolferView.cs','Assets/Editor/GolfGarmentRepair.cs']:
 pairs.append((U/rel,R/'Unity'/rel))
expected={row['path']:row['after'] for row in json.loads((W/'data/promoted.json').read_text())}
for rel in ['Assets/Scripts/Game/GolfSwingClearance.cs','Assets/Scripts/Game/GolferView.cs','Assets/Editor/GolfGarmentRepair.cs']:
 expected['Unity/'+rel]=hashlib.sha256((W/'rollback/followthrough-baseline/codeInputs'/rel).read_bytes()).hexdigest()
changes=[]
for source,target in pairs:
 assert source.is_file(),source
 data=source.read_bytes();old=target.read_bytes() if target.exists() else None
 if old==data:continue
 rel=str(target.relative_to(R));before=hashlib.sha256(old).hexdigest() if old else None
 if rel in expected:assert before==expected[rel],('Shared checkout changed since baseline',rel)
 changes.append(dict(path=rel,before=before,after=hashlib.sha256(data).hexdigest(),source=str(source)))
# Validate the whole plan before any writes.
if apply:
 for row in changes:
  target=R/row['path'];backup=B/row['path'];backup.parent.mkdir(parents=True,exist_ok=True)
  if target.exists() and not backup.exists():shutil.copy2(target,backup)
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(row['source'],target)
 for row in changes:assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['after']
(W/'data'/('followthrough_promoted.json' if apply else 'followthrough_promotion_plan.json')).write_text(json.dumps(changes,indent=2))
print(('UPDATED AND VERIFIED' if apply else 'PLANNED'),len(changes),'files')
