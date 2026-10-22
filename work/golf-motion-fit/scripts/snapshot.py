from pathlib import Path
import hashlib,json,shutil,subprocess
R=Path(__file__).resolve().parents[3];W=R/'work/golf-motion-fit'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=['AGENTS.md','ArtDir/hero/kit/GARMENT_SPEC.md','ArtDir/hero/kit/golf/GOLF_KIT_DESIGN.md','work/golf-look/REPORT.md']
paths += [str(p.relative_to(R)) for folder in ['Unity/Assets/Scripts/Game','GolfArcade/Unity','Unity/Assets/Resources/Tennis/Shaders'] for p in (R/folder).glob('*') if p.is_file() and p.suffix in ['.cs','.swift','.shader','.hlsl']]
rows={}
for rel in paths:
 p=R/rel;dst=W/'rollback'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():shutil.copy2(p,dst);rows[rel]=sha(p)
for sex in ['Male','Female']:
 for label,src in [('Approved',R/f'work/cloth-overhaul/export/Cloth_{sex}.blend'),('Draft',R/f'work/golf-look/export/Golf_{sex}_Draft.blend')]:
  dst=W/f'inputs/{sex}_{label}.blend';shutil.copy2(src,dst);rows[str(src.relative_to(R))]=sha(src)
(W/'data/baseline.json').write_text(json.dumps(rows,indent=2)+'\n')
(W/'data/git_status_start.txt').write_text(subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=R,text=True))
print('Snapshot:',len(rows),'files; approved and golf draft Blender sources copied.')
