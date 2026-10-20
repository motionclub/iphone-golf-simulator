from pathlib import Path
import shutil
w=Path(__file__).resolve().parents[1];bk=w/'rollback/maps_import_r36';bk.mkdir(exist_ok=True)
for name,d in [('candidate',w/'candidate/Unity/Assets/Resources/Golf/HeroDetail'),('isolated',w/'isolation/PostClothUnity/Assets/Resources/Golf/HeroDetail')]:
 if not (bk/name).exists():shutil.copytree(d,bk/name)
 for p in (w/'maps').glob('Golf*.png'):shutil.copy2(p,d/p.name)
u=w/'isolation/PostClothUnity/Assets'
for name in ['GolfGroundFrameAudit.cs','GolfGroundAudit.shader']:
 dest=u/'Editor'/name
 if dest.exists():shutil.copy2(dest,bk/name)
 shutil.copy2(w/'proof-tools'/name,dest)
p=u/'Editor/GolfLookProofRig.cs';shutil.copy2(p,bk/p.name);shutil.copy2(w/'proof-tools/GolfLookProofRig_r36.cs',p)
