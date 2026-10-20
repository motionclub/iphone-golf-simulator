from pathlib import Path
import subprocess,json,hashlib
P=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=P/'work/serve-walk-arm';R=W/'report_r2'
def git(*a):return subprocess.check_output(['git',*a],cwd=P)
def index():
 return {p:meta for record in git('ls-files','--stage','-z').split(b'\0') if record for meta,p in [record.split(b'\t',1)]}
files=[P/'Unity/Assets/Editor/ServeWalkFilm.cs',P/'Unity/Assets/Editor/ServeWalkFilm.cs.meta',W/'LEFTY_GAP.md']
reports=['GATE_RESULTS.md','gate-summary.json','after_r2_v37-matrix.json','before_r2_final-matrix.json','CANDIDATE_R2_GATES_FAIL.patch','PLAYER_DEPTH_SPEED_SCOPE_REQUEST.patch','REFEED_CONSTRAINT_CONFLICT.json','GAME_TIMES_UNCHANGED.json','real-input-final.json','exclusion-ranges.json','production-runtime-audit.json','source-diff-v37.json','protected-assets-audit.json','unity-runs-v37.json','SCOPE_DECISION.md','baseline-film-frame-match.json','OPPONENT_FOLLOWUP.md','OPPONENT_V37_FOLLOWUP.patch','after_r2_v37_smoke-matrix.json','movie-readiness-v37.json','goal-turn-audit.json','completion-audit-v37.json']
files += [R/f for f in reports if (R/f).exists()]
files += [q for q in (R/'v33_checkpoint').glob('*') if q.is_file()]
files += [s for pattern in ['*v37*UPM_STARTUP_FAILURE*','*MONO_ASSEMBLY_STALL*','mono-stall-B*.sample.txt'] for s in (W/'logs_r2').glob(pattern) if s.is_file()]
files += list((W/'rollback/r2').rglob('*.cs'))+list((W/'rollback/r2').rglob('*.meta'))
files += [W/'scripts_r2'/f for f in ['build_candidate.py','build_candidate-v37.py','build_candidate-v37-trial.py','audit_v37.py','write_report_v37.py','review_package_v37.py','gates.py','proof_runner.py','write_report.py','review_package_v37.py','export_deliverables.py','stage_v37.py','export_v37.py','verify_movies_v37.py']]
for stage in ['before_r2_final','after_r2_v37','input_r2_v37','before_r2_film','after_r2_film_v37','before_r2_plant547','after_r2_v37_smoke']:
 for case in (W/stage).glob('*'):
  for n in ['trace.csv','source.json','completed.json','measurement.md']:
   q=case/n
   if q.exists():files.append(q)
files += [q for q in (W/'film_r2').glob('*') if q.suffix in ['.mp4','.jpg','.json','.ass']]
files=sorted(set(files));paths=[str(q.relative_to(P)) for q in files];before=index();(R/'git-status-before-final-stage.txt').write_bytes(git('status','--short'));(R/'git-cached-stat-before-final-stage.txt').write_bytes(git('diff','--cached','--stat'))
subprocess.run(['git','add','--',*paths],cwd=P,check=True)
after=index();allowed={x.encode() for x in paths};unchanged=all(before.get(p)==after.get(p) for p in set(before)|set(after) if p not in allowed);assert unchanged,'Unrelated index entries changed'
summary={'owned_paths_staged':paths,'unrelated_index_entries_unchanged':unchanged,'no_commit':True,'candidate_runtime_installed':False,'hashes':{str(q.relative_to(P)):hashlib.sha256(q.read_bytes()).hexdigest() for q in files}}
(R/'staging-manifest.json').write_text(json.dumps(summary,indent=2))
for name,args in [('git-status-after-r2.txt',['status','--short']),('git-diff-stat-after-r2.txt',['diff','--stat']),('git-cached-stat-after-r2.txt',['diff','--cached','--stat']),('owned-diff-stat-r2.txt',['diff','--cached','--stat','--',*paths])]:
 (R/name).write_bytes(git(*args))
audit=['staging-manifest.json','git-status-before-final-stage.txt','git-cached-stat-before-final-stage.txt','git-status-after-r2.txt','git-diff-stat-after-r2.txt','git-cached-stat-after-r2.txt','owned-diff-stat-r2.txt']
subprocess.run(['git','add','--',*[str((R/f).relative_to(P)) for f in audit]],cwd=P,check=True)
print('Staged',len(paths),'owned files plus audit records; unrelated index entries unchanged. No runtime install or commit.')
print((R/'owned-diff-stat-r2.txt').read_text()[-700:])
print('Full git status and global diff stats saved under report_r2.')
