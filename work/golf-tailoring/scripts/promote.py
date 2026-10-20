from pathlib import Path
import shutil,json,hashlib,sys
W=Path(__file__).resolve().parents[1];R=W.parents[1];U=W/'Unity';B=W/'rollback/production';apply='--apply' in sys.argv
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
changes=[]
def update(path,data):
 old=path.read_bytes() if path.exists() else None
 if old==data:return
 rel=path.relative_to(R);changes.append(dict(path=str(rel),before=hashlib.sha256(old).hexdigest() if old else None,after=hashlib.sha256(data).hexdigest()))
 if apply:
  if old is not None:
   backup=B/rel;backup.parent.mkdir(parents=True,exist_ok=True)
   if not backup.exists():backup.write_bytes(old)
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
for a,b in pairs:
 assert a.is_file(),a
 update(b,a.read_bytes())
# Merge only this pass's code into the current shared checkout.
rel='Assets/Scripts/Tennis/MatchHeroLook.cs';target=R/'Unity'/rel;s=target.read_text();candidate=(U/rel).read_text()
if 'static ClothLook GolfClothFor' not in s:
 start=candidate.index('        // Golf has coarser pique');end=candidate.index('        /// A copy of an authored flat material',start)
 needle='        /// A copy of an authored flat material';assert s.count(needle)==1;s=s.replace(needle,candidate[start:end]+needle)
 s=s.replace('var look = ClothFor(role);','var look = golfKit ? GolfClothFor(role) : ClothFor(role);')
update(target,s.encode())
rel='Assets/Scripts/Game/HeroGolfer.cs';target=R/'Unity'/rel;s=target.read_text();candidate=(U/rel).read_text()
if 'var sourceBody = source.GetComponent<MatchHeroLook>().body;' not in s:
 start=candidate.index('            // The legacy golf body was cut away');end=candidate.index('            var garments = new List<SkinnedMeshRenderer>();',start)
 needle='            var garments = new List<SkinnedMeshRenderer>();';assert s.count(needle)==1;s=s.replace(needle,candidate[start:end]+needle)
update(target,s.encode())
rel='Assets/Editor/MatchHeroLockerExport.cs';target=R/'Unity'/rel;s=target.read_text();old='GetMethod("ClothFor", BindingFlags.Static | BindingFlags.NonPublic)';new='GetMethod(golf ? "GolfClothFor" : "ClothFor", BindingFlags.Static | BindingFlags.NonPublic)';assert old in s or new in s;s=s.replace(old,new);update(target,s.encode())
rel='Assets/Editor/GolfGarmentRepair.cs';target=R/'Unity'/rel;s=target.read_text();candidate=(U/rel).read_text()
if 'static void CoverBody' not in s:
 start=candidate.index('  // Keep the original body');end=candidate.rfind('\n }');pos=s.rfind('\n }');s=s[:pos]+candidate[start:end]+s[pos:]
 s=s.replace('    var root=Resources.Load<GameObject>', '    CoverBody(sex);\n    var root=Resources.Load<GameObject>')
update(target,s.encode())
(W/'data'/('promoted.json' if apply else 'promotion_plan.json')).write_text(json.dumps(changes,indent=2));print(('UPDATED' if apply else 'PLANNED'),len(changes),'files')
