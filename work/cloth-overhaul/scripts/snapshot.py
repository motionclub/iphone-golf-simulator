from pathlib import Path
import hashlib,json,shutil,subprocess
R=Path(__file__).resolve().parents[3]; W=R/'work/cloth-overhaul'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[R/'Unity/Assets/Scripts/Tennis/MatchHeroLook.cs',R/'Unity/Assets/Resources/Tennis/Shaders/TennisCloth.shader',R/'Unity/Assets/Editor/MatchHeroKit.cs',R/'Unity/Assets/Editor/HeroDetailTextures.cs']
paths += list((R/'Unity/Assets/Characters/MatchHeroKit').glob('*'))
paths += list((R/'Unity/Assets/Resources/Tennis/HeroDetail').glob('*'))
paths += [R/'GolfArcade/Unity'/n for n in ['MatchHeroData.swift','MatchHeroSurfaces.swift','CharacterModelPreview.swift']]+[R/'Unity/Assets/Editor/MatchHeroLockerExport.cs']
paths += list((R/'GolfArcade/Unity/CharacterAssets').glob('MatchHero_*'))
manifest={}
for p in paths:
 if not p.is_file(): continue
 rel=p.relative_to(R); dst=W/'rollback'/rel; dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists(): shutil.copy2(p,dst)
 manifest[str(rel)]={'sha256':sha(dst),'rollback':str(dst),'mtime':p.stat().st_mtime}
(W/'baseline_files.json').write_text(json.dumps(manifest,indent=2))
protected={}
for folder,glob in [('Unity/Assets/Characters/MatchHeroes','*.fbx'),('Unity/Assets/Scripts/Tennis','*Serve*.cs'),('Unity/ProjectSettings','*.asset'),('Unity/Assets/Settings','*'),('ArtDir/hero/base_lock/blender','*.blend')]:
 for p in (R/folder).rglob(glob):
  if p.is_file(): protected[str(p.relative_to(R))]=sha(p)
for n in ['HeroTennisDriver.cs','TennisGame.cs']:
 p=R/'Unity/Assets/Scripts/Tennis'/n; protected[str(p.relative_to(R))]=sha(p)
(W/'protected_before.json').write_text(json.dumps(protected,indent=2))
(W/'git_status_before.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=R,text=True))
print(f'Backed up {len(manifest)} files; recorded {len(protected)} protected hashes')
