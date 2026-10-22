"""Promote root-reviewed fresh scratch stages; installed course untouched."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');V=R/'work/postcard-look/v3';P=V/'p7/round1';B=P/'rebuild'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (R/'work/postcard-look/heavy.lock/owner').is_file(), 'required heavy lock'
pid=os.getppid();anc=[]
while pid>1:
 row=subprocess.check_output(['ps','-p',str(pid),'-o','ppid=','-o','command='],text=True).strip().split(None,1)
 if len(row)<2:break
 anc.append(row[1]);pid=int(row[0])
assert any(str(R/'work/postcard-look/heavy.sh') in x for x in anc), 'actual heavy ancestor required'
inputs=json.loads((B/'inputs_at_start.json').read_text())
assert all(sha(R/p)==s for p,s in inputs.items()), 'build input changed concurrently'
scoring=json.loads((B/'scoring_exact.json').read_text());assert scoring['pass'] and len(scoring['results'])==12
for rec in scoring['results']:assert rec['pass'] and rec['threshold_m']==0 and rec['max_vertex_delta_m']==0 and rec['max_marker_delta_m']==0
records=[]
for n in ('08','09','10'):
 fresh=B/f'hole{n}/stage';current=V/f'hole{n}/stage';archive=P/f'before/stage_original/hole{n}'
 assert not archive.exists()
 for ext in ('blend','fbx'):assert (fresh/f'hole_{n}.{ext}').is_file()
 libpaths=[line.split(None,1)[1] for line in (V/f'hole{n}/lib_sha_final.txt').read_text().splitlines() if re.match(r'^[a-f0-9]{64}\s',line)]
 archive.parent.mkdir(parents=True,exist_ok=True);current.rename(archive);shutil.copytree(fresh,current)
 (V/f'hole{n}/lib_sha_final.txt').write_text(''.join(f'{sha(R/p)}  {p}\n' for p in libpaths))
 pngs=sorted((R/'Unity/Assets/Resources/Course/Look').glob('*.png'));assert len(pngs)==31
 (V/f'hole{n}/look_png_sha_final.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(R)}\n' for p in pngs))
 (V/f'hole{n}/stage_sha256.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(R)}\n' for p in sorted(current.rglob('*')) if p.is_file()))
 records.append(dict(hole=n,archive=str(archive),fresh_source=str(fresh),promoted=str(current),blend_sha=sha(current/f'hole_{n}.blend'),fbx_sha=sha(current/f'hole_{n}.fbx')))
assert all(sha(R/p)==s for p,s in inputs.items()), 'input changed during promotion'
(P/'stage_promotion.json').write_text(json.dumps(dict(status='PASS',scoring_exact=0,records=records),indent=2)+'\n')
print(json.dumps(records,indent=2))
