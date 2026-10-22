from pathlib import Path
import shutil,uuid,json,hashlib
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=Path(__file__).parent;A=R/'Unity/Assets'
installed=[]
for name in ['TennisStandsCrowd.cs','TennisResortCrowd.cs']:
 d=A/'Scripts/Tennis'/name;shutil.copy2(W/name,d);installed.append(d)
for name in ['TennisNpcInventory.cs','TennisAudienceProof.cs','TennisPromenadeFilm.cs']:
 d=A/'Editor'/name;shutil.copy2(W/name,d);installed.append(d)
 if not Path(str(d)+'.meta').exists():Path(str(d)+'.meta').write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n')
meta=(A/'Resources/Tennis/Premium/TennisSpectators.fbx.meta').read_text()
for name in ['TennisSeatedHero3','TennisPromenadeHero3']:
 d=A/'Resources/Tennis/Premium'/(name+'.fbx');shutil.copy2(R/'work/full-visual-overhaul/tennis/audience2'/(name+'.fbx'),d);installed.append(d)
 if not Path(str(d)+'.meta').exists():
  lines=meta.splitlines();lines[1]='guid: '+uuid.uuid4().hex;Path(str(d)+'.meta').write_text('\n'.join(lines)+'\n')
manifest=[dict(path=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in installed]
(R/'proof/full-visual-overhaul/tennis/audience4-installed-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for p in installed:print(p.relative_to(R))
