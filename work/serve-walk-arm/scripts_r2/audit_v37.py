from pathlib import Path
import json,csv,hashlib,subprocess
P=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=P/'work/serve-walk-arm';R=W/'report_r2'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
audit={};candidate=W/'CandidateR2Clone/Assets';before=W/'BeforeR2Clone/Assets'
for stage,count,base in [('before_r2_final',16,before),('after_r2_v37',16,candidate),('input_r2_v37',4,candidate),('after_r2_film_v37',4,candidate)]:
 cases=list((W/stage).glob('*/completed.json'));assert len(cases)==count,(stage,len(cases))
 for p in cases:
  c=p.parent;done=json.loads(p.read_text());src=json.loads((c/'source.json').read_text());rows=list(csv.DictReader((c/'trace.csv').open()));expect=540 if stage.startswith('input') else 480 if c.name.endswith('control') else 900 if c.name.startswith('opponent') else 1200
  assert done['exit_code']==0 and done['frames']==len(rows)==expect,(c,len(rows),expect)
  assert len(src['sources'])==len(src['sha256'])==5 and set(src['sources'])=={'Scripts/Tennis/HeroTennisDriver.cs','Scripts/Tennis/TennisActor.cs','Scripts/Tennis/TennisServeRoutine.cs','Scripts/Tennis/TennisGame.cs','Editor/ServeWalkFilm.cs'}
  matches=all(h(base/n)==v for n,v in zip(src['sources'],src['sha256']));assert matches,(c,'hash mismatch')
  assert [int(x['frame']) for x in rows]==list(range(expect)),(c,'frame gaps')
  audit[str(c.relative_to(W))]={'completed':True,'frames':len(rows),'source_hashes_match':matches,'input_path':src['inputPath']}
fail_logs=[str(p.relative_to(W)) for p in (W/'logs_r2').glob('*v37*UPM_STARTUP_FAILURE*')]
(R/'unity-runs-v37.json').write_text(json.dumps({'successful_captures':audit,'successful_capture_count':len(audit),'retried_local_package_manager_startup_logs':fail_logs,'terminated_assembly_load_stall_logs':[str(p.relative_to(W)) for p in (W/'logs_r2').glob('*MONO_ASSEMBLY_STALL*')]+[str(p.relative_to(W)) for p in (W/'logs_r2').glob('mono-stall-B*.sample.txt')],'note':'Successful capture completion records, continuous raw frames and source hashes audited. Startup failures, if listed, were retried and their logs retained.'},indent=2))
# Compare all ordinary assets and settings, ignoring the isolated external Editor scratch symlink.
diffs=[]
for folder in ['Assets','ProjectSettings']:
 a=W/'BeforeR2Clone'/folder;b=W/'CandidateR2Clone'/folder
 aa={str(p.relative_to(a)):p for p in a.rglob('*') if p.is_file()};bb={str(p.relative_to(b)):p for p in b.rglob('*') if p.is_file()}
 for rel in sorted(set(aa)|set(bb)):
  if rel not in aa or rel not in bb or h(aa[rel])!=h(bb[rel]):diffs.append(folder+'/'+rel)
allowed=['Assets/Scripts/Tennis/HeroTennisDriver.cs','Assets/Scripts/Tennis/TennisGame.cs','Assets/Scripts/Tennis/TennisServeRoutine.cs'];assert diffs==allowed,diffs
(R/'source-diff-v37.json').write_text(json.dumps({p:'different' for p in diffs},indent=2));print('Audited 40 successful captures and exactly three owned runtime differences.')
