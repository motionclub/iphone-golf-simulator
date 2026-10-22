from pathlib import Path
import json,shutil,zipfile,hashlib,csv,subprocess
P=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=P/'work/serve-walk-arm';R=W/'report_r2';O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/find-2/outputs/serve-walk-arm-r2');O.mkdir(exist_ok=True)
manifest=json.loads((W/'film_r2/manifest.json').read_text());assert 'v37' in manifest['candidate'];assert len(manifest['films'])==12 and len(manifest['sheets'])==6 and len(manifest['real_input_films'])==4
for f in W.joinpath('film_r2').glob('*'):
 if f.suffix in ['.mp4','.jpg','.json']:shutil.copy2(f,O/'film_r2'/f.name) if (O/'film_r2').exists() else ((O/'film_r2').mkdir(),shutil.copy2(f,O/'film_r2'/f.name))
reports=['GATE_RESULTS.md','gate-summary.json','after_r2_v37-matrix.json','before_r2_final-matrix.json','CANDIDATE_R2_GATES_FAIL.patch','PLAYER_DEPTH_SPEED_SCOPE_REQUEST.patch','REFEED_CONSTRAINT_CONFLICT.json','GAME_TIMES_UNCHANGED.json','real-input-final.json','exclusion-ranges.json','production-runtime-audit.json','source-diff-v37.json','protected-assets-audit.json','staging-manifest.json','git-status-after-r2.txt','git-diff-stat-after-r2.txt','git-cached-stat-after-r2.txt','owned-diff-stat-r2.txt','unity-runs-v37.json','SCOPE_DECISION.md','baseline-film-frame-match.json','OPPONENT_FOLLOWUP.md','OPPONENT_V37_FOLLOWUP.patch','after_r2_v37_smoke-matrix.json','movie-readiness-v37.json','goal-turn-audit.json','completion-audit-v37.json']
for f in reports:shutil.copy2(R/f,O/f)
shutil.copy2(W/'LEFTY_GAP.md',O/'LEFTY_GAP.md');shutil.copy2(P/'ArtDir/hero/base_lock/parallel_prompts/28b_SERVE_WALK_BALL_ARM_FINISH.txt',O/'28b_INSTRUCTIONS.txt')
with zipfile.ZipFile(O/'paired-traces-and-source-records.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for stage in ['before_r2_final','after_r2_v37','input_r2_v37','before_r2_film','after_r2_film_v37','after_r2_v37_smoke']:
  for p in (W/stage).glob('*'):
   for f in ['trace.csv','source.json','completed.json','measurement.md']:
    q=p/f
    if q.exists():z.write(q,str(q.relative_to(W)))
 for f in R.glob('*.json'):z.write(f,str(f.relative_to(W)))
 for pattern in ['*v37*UPM_STARTUP_FAILURE*','*MONO_ASSEMBLY_STALL*','mono-stall-B*.sample.txt']:
  for f in (W/'logs_r2').glob(pattern):z.write(f,str(f.relative_to(W)))
lines=['# Serve-walk arm — v37 review package','', '**Candidate not installed. No commit. See GATE_RESULTS.md for the binary gate table and remaining failures.**','', 'RH films are before|after, at half speed, with actual frame and depth readouts. Every sheet includes the exact plant frame f547 and both player and opponent. LH films are archive 28, explicitly unsupported, and excluded from the matrix.','', '| Hero | Game | Front | Side |','|---|---|---|---|']
for sex in ['male','female']:
 items=[f'[Sheet](film_r2/{sex}-{v}-contact-sheet.jpg)' for v in ['game','front','side']];lines.append(f'| {sex} | '+' | '.join(items)+' |')
lines+=['','| Role / hero | Game | Front | Side |','|---|---|---|---|']
for role in ['player','opponent']:
 for sex in ['male','female']:
  items=[f'[Film](film_r2/{role}-{sex}-{v}-before-after-half-speed.mp4)' for v in ['game','front','side']];lines.append(f'| {role} {sex} | '+' | '.join(items)+' |')
lines+=['','Production input-entry captures (SetLateralInput; normal speed):','']
for p in manifest['real_input_films']:lines.append(f'- [{Path(p).stem}]({p})')
lines+=['','[Unsupported LH film index](film_r2/manifest.json) · [Left-handed gap](LEFTY_GAP.md) · [All traces and source hashes](paired-traces-and-source-records.zip)','']
(O/'FILMS_AND_SHEETS.md').write_text('\n'.join(lines))
files=[p for p in O.rglob('*') if p.is_file() and p.name!='deliverable-manifest.json'];proof=[{'path':str(p.relative_to(O)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)];(O/'deliverable-manifest.json').write_text(json.dumps(proof,indent=2))
with zipfile.ZipFile(O/'paired-traces-and-source-records.zip') as z:assert z.testzip() is None
print('Exported',len(proof),'hashed deliverables;',len(manifest['films']),'RH films;',len(manifest['sheets']),'sheets;',len(manifest['real_input_films']),'input films;',len(manifest['unsupported_LH']),'unsupported LH films')
