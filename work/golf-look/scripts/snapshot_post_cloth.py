"""Freeze the released post-cloth source and create an isolated rendering project."""
from pathlib import Path
import hashlib, json, subprocess, datetime
R=Path(__file__).resolve().parents[3]
W=R/'work/golf-look'
B=W/'inputs/post_cloth'
U=W/'isolation/PostClothUnity'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def clone(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['/bin/cp','-cR',str(src),str(dst)],check=True)
if (W/'data/post_cloth_baseline.json').exists():
    raise SystemExit('Baseline already exists; preserve it and inspect before rerunning')
paths=[]
for folder in ['Unity/Assets','Unity/Packages','Unity/ProjectSettings','GolfArcade/Unity','ArtDir/hero/kit']:
    paths.extend(p for p in (R/folder).rglob('*') if p.is_file())
manifest={}
for p in sorted(paths):
    rel=p.relative_to(R)
    dst=B/rel
    clone(p,dst)
    value=sha(p)
    assert value==sha(dst),str(rel)
    manifest[str(rel)]={'sha256':value,'bytes':p.stat().st_size,'snapshot':str(dst)}
U.mkdir(parents=True,exist_ok=True)
for folder in ['Assets','Packages','ProjectSettings','Library']:
    if not (U/folder).exists(): clone(R/'Unity'/folder,U/folder)
for rel,row in manifest.items():
    assert sha(R/rel)==row['sha256'],'Source changed during snapshot: '+rel
    if rel.startswith('Unity/'):
        assert sha(U/rel.removeprefix('Unity/'))==row['sha256'],'Isolated asset mismatch: '+rel
report={'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
        'g0':'PASS: explicit user override supersedes stale postcard phase file; final cloth report/spec available',
        'postcard_status_edited':False,'files':manifest,'isolated_project':str(U)}
(W/'data/post_cloth_baseline.json').write_text(json.dumps(report,indent=2)+'\n')
(W/'data/post_cloth_index.txt').write_text(subprocess.check_output(['git','ls-files','--stage'],cwd=R,text=True))
print('Frozen',len(manifest),'files; isolated project',U,flush=True)
