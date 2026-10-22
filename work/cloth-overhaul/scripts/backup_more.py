from pathlib import Path
import shutil,json,hashlib
R=Path(__file__).resolve().parents[3];W=R/'work/cloth-overhaul';manifest=json.loads((W/'baseline_files.json').read_text())
paths=list((R/'Unity/Assets/Resources/Tennis/Customization').glob('Player*.prefab*'))+list((R/'Unity/Assets/Characters/MatchHeroes/Materials/Kit').glob('*'))
for p in paths:
 if not p.is_file():continue
 rel=p.relative_to(R);dst=W/'rollback'/rel
 if not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
 manifest[str(rel)]={'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'rollback':str(dst),'mtime':p.stat().st_mtime}
(W/'baseline_files.json').write_text(json.dumps(manifest,indent=2));print('Added cloth prefab/material rollback copies')
