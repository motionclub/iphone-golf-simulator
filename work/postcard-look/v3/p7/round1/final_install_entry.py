"""Root-owned current-stage provenance, then required pre/install/guards."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');V=R/'work/postcard-look/v3';P=V/'p7/round1';B=P/'rebuild'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (R/'work/postcard-look/heavy.lock/owner').is_file()
inputs=json.loads((B/'inputs_at_start.json').read_text());assert all(sha(R/p)==s for p,s in inputs.items())
scoring=json.loads((B/'scoring_exact_after_foam_vapour_rethink.json').read_text());assert scoring['pass'] and len(scoring['results'])==12
assert all(x['threshold_m']==0 and x['max_vertex_delta_m']==0 and x['max_marker_delta_m']==0 for x in scoring['results'])
fresh=B/'hole08/stage';current=V/'hole08/stage';archive=P/'before/stage_promoted_failed_h8'
assert not archive.exists();current.rename(archive);shutil.copytree(fresh,current)
for n in ('08','09','10'):
 folder=V/f'hole{n}';stage=folder/'stage'
 lp=[line.split(None,1)[1] for line in (folder/'lib_sha_final.txt').read_text().splitlines() if re.match(r'^[a-f0-9]{64}\s',line)]
 (folder/'lib_sha_final.txt').write_text(''.join(f'{sha(R/p)}  {p}\n' for p in lp))
 pngs=sorted((R/'Unity/Assets/Resources/Course/Look').glob('*.png'));assert len(pngs)==31
 (folder/'look_png_sha_final.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(R)}\n' for p in pngs))
 (folder/'stage_sha256.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(R)}\n' for p in sorted(stage.rglob('*')) if p.is_file()))
assert all(sha(R/p)==s for p,s in inputs.items())
for script in (P/'write_current_install_docs.py',V/'proof/runtime/prepare_install_route.py'):
 argv=[sys.executable,str(script)]+(['--apply'] if script.name=='prepare_install_route.py' else [])
 if subprocess.call(argv,cwd=R):raise SystemExit(1)
env=os.environ.copy();env['PROOF_TAG']='p7_pre_install_round1_retry1'
raise SystemExit(subprocess.call(['bash',str(V/'proof/runtime/run_proof.sh'),'pre','install','protected'],cwd=R,env=env))
