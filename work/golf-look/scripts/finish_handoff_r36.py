"""Promote the current candidate after the user's final-validation waiver.

No builds, tests, phone operations, commits or branch changes. Existing native
motion resources and foreign index entries are preserved.
"""
from pathlib import Path
import hashlib,json,shutil,re,subprocess,difflib
R=Path(__file__).resolve().parents[3];W=R/'work/golf-look';C=W/'candidate';U=W/'isolation/PostClothUnity';B=W/'inputs/post_cloth';BK=W/'rollback/handoff_r36';BK.mkdir(exist_ok=True)
O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/read-artdir-environments-30b-golf-shaders/outputs')
owned=[];stage=[];patches=[];beforeIndex=subprocess.check_output(['git','ls-files','-s','-z'],cwd=R)
def put(rel,data,stageFile=True):
 p=R/rel;q=BK/rel
 if p.exists():
  q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
  old=p.read_bytes()
 else:old=None
 if old==data:return
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);owned.append(str(rel))
 if stageFile:stage.append(str(rel))
 if old is not None and p.suffix in ['.swift','.pbxproj']:
  patches.extend(difflib.unified_diff(old.decode().splitlines(True),data.decode().splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
def copyUnity(rel,src):
 live=R/rel;base=B/rel
 assert not live.exists() or live.read_bytes()==src.read_bytes() or (base.exists() and live.read_bytes()==base.read_bytes()),'Concurrent edit: '+str(rel)
 put(rel,src.read_bytes())
 meta=Path(str(src)+'.meta');target=Path(str(rel)+'.meta')
 if meta.exists() and not (R/target).exists():put(target,meta.read_bytes())
 # Preserve directory GUIDs used by the imported prefab/material references.
 for parent in Path(rel).parents:
  if str(parent) in ['Unity/Assets','Unity','.']:break
  sm=U/(str(parent).removeprefix('Unity/')+'.meta')
  if sm.exists() and not (R/(str(parent)+'.meta')).exists():put(Path(str(parent)+'.meta'),sm.read_bytes())
for src in sorted((C/'Unity').rglob('*')):
 if not src.is_file():continue
 rel=Path('Unity')/src.relative_to(C/'Unity');copyUnity(rel,src)
 # Candidate source scripts do not own import metadata; the verified clone does.
 um=U/(str(rel).removeprefix('Unity/')+'.meta');tm=R/(str(rel)+'.meta')
 if um.exists() and not tm.exists():put(Path(str(rel)+'.meta'),um.read_bytes())
for src in sorted((U/'Assets/Characters/GolfHeroKit').rglob('*')):
 if src.is_file():copyUnity(Path('Unity')/src.relative_to(U),src)
for sex in ['Male','Female']:
 for ext in ['.prefab','.prefab.meta']:
  rel=Path(f'Unity/Assets/Resources/Tennis/Customization/Player{sex}GolfKit{ext}');copyUnity(rel,U/str(rel).removeprefix('Unity/'))
# Keep static kit exports distinct from previously generated GolfHero motion data.
assets=Path('GolfArcade/Unity/CharacterAssets');newNative=[]
for sex in ['Male','Female']:
 p=W/f'locker/assets/GolfHero_{sex}.json';manifest=json.loads(p.read_text());assert not manifest['swingFrames'] and not manifest['rig']['bones']
 s=p.read_text();s=re.sub(r'Golf_(Male|Female|Fabric)',r'GolfKit_\1',s)
 for suffix,data in [('.json',s.encode()),('.lzfse',(W/f'locker/assets/GolfHero_{sex}.lzfse').read_bytes())]:
  rel=assets/f'GolfKitHero_{sex}{suffix}';assert not (R/rel).exists();put(rel,data);newNative.append(rel.name)
for src in sorted((W/'locker/assets').glob('MatchHero_Golf_*.ktx')):
 rel=assets/src.name.replace('MatchHero_Golf_','MatchHero_GolfKit_');assert not (R/rel).exists();put(rel,src.read_bytes());newNative.append(rel.name)
rel=Path('GolfArcade/Unity/MatchHeroData.swift');s=(R/rel).read_text();needle='(golf ? "GolfHero_" : "MatchHero_")';assert s.count(needle)==1;s=s.replace(needle,'(golf ? "GolfKitHero_" : "MatchHero_")');put(rel,s.encode(),False)
rel=Path('GolfArcade/Unity/LockerCatalog.swift');s=(R/rel).read_text();needle='LockerItem(id: golfKitID, slot: .skin, name: "Classic Golf", sports: [.golf], tintable: false)';assert s.count(needle)==1;s=s.replace(needle,'LockerItem(id: golfKitID, slot: .skin, name: "Golf Polo", sports: [.golf], tintable: true)');put(rel,s.encode(),False)
rel=Path('GolfArcade/Unity/CharacterModelPreview.swift');s=(R/rel).read_text();needle='case "Kit_Shirt", "Kit_GolfGlove": return pick("shirt").map(kitTint)';assert s.count(needle)==1;s=s.replace(needle,'case "Kit_Shirt", "Kit_GolfGlove", "Kit_GolfHead": return pick("shirt").map(kitTint)');put(rel,s.encode(),False)
# Add resource entries without replacing project changes from other chats.
rel=Path('GolfArcade.xcodeproj/project.pbxproj');s=(R/rel).read_text();bf=[];fr=[];gr=[];rs=[]
for name in newNative:
 rid=hashlib.sha256(('30b-ref-'+name).encode()).hexdigest()[:24].upper();bid=hashlib.sha256(('30b-build-'+name).encode()).hexdigest()[:24].upper();assert rid not in s and bid not in s
 bf.append(f'\t\t{bid} /* {name} in Resources */ = {{isa = PBXBuildFile; fileRef = {rid} /* {name} */; }};\n')
 typ='text.json' if name.endswith('.json') else 'file'
 fr.append(f'\t\t{rid} /* {name} */ = {{isa = PBXFileReference; lastKnownFileType = {typ}; path = {name}; sourceTree = "<group>"; }};\n')
 gr.append(f'\t\t\t\t{rid} /* {name} */,\n');rs.append(f'\t\t\t\t{bid} /* {name} in Resources */,\n')
s=s.replace('/* Begin PBXBuildFile section */\n','/* Begin PBXBuildFile section */\n'+''.join(bf),1).replace('/* Begin PBXFileReference section */\n','/* Begin PBXFileReference section */\n'+''.join(fr),1)
s=re.sub(r'(CFBEB2E659D13EC358060998 /\* CharacterAssets \*/ = \{\s*isa = PBXGroup;\s*children = \(\n)',lambda m:m[0]+''.join(gr),s,count=1)
s=re.sub(r'(368A99EA91977F617064F797 /\* Resources \*/ = \{\s*isa = PBXResourcesBuildPhase;\s*buildActionMask = 2147483647;\s*files = \(\n)',lambda m:m[0]+''.join(rs),s,count=1)
assert all(s.count(name)>=4 for name in newNative);put(rel,s.encode(),False)
# Subsequent static golf exports use the same separate namespace.
rel=Path('Unity/Assets/Editor/MatchHeroLockerExport.cs');s=(R/rel).read_text();needle='(golf ? "GolfHero_" : "MatchHero_")';assert s.count(needle)==1;put(rel,s.replace(needle,'(golf ? "GolfKitHero_" : "MatchHero_")').encode())
for rel in [Path('ArtDir/hero/kit/GARMENT_SPEC.md')]:
 src=C/rel;assert (R/rel).read_bytes()==(B/rel).read_bytes();put(rel,src.read_bytes())
rel=Path('ArtDir/hero/kit/golf/GOLF_KIT_DESIGN.md');s=(W/'design/GOLF_KIT_DESIGN.md').read_text().replace('golf_polo','golf-classic-kit').replace('golf_spikeless','golf-spikeless');put(rel,s.encode(),False)
# Stage only clean-owned paths. Shared native edits stay in the working tree;
# their exact small patch is provided so no foreign unstaged work is staged.
subprocess.run(['git','add','--']+stage,cwd=R,check=True)
afterIndex=subprocess.check_output(['git','ls-files','-s','-z'],cwd=R)
def other(data):return sorted(r for r in data.split(b'\0') if r and r.split(b'\t',1)[1].decode() not in set(stage))
assert other(beforeIndex)==other(afterIndex),'Foreign index entries changed'
(W/'data/handoff_owned_paths_r36.json').write_text(json.dumps({'changed':owned,'stagedOwned':stage,'sharedNativePatch':'outputs/golf_shared_native_r36.patch','foreignIndexPreserved':True,'validationWaivedByUser':True,'commit':None,'branchChanged':False},indent=2))
O.mkdir(exist_ok=True);(O/'golf_shared_native_r36.patch').write_text(''.join(patches))
print('CURRENT CANDIDATE INSTALLED',len(owned),'files; staged owned',len(stage),'; foreign index preserved; no commit',flush=True)
