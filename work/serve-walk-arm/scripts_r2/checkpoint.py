from pathlib import Path
import difflib,json,csv,hashlib
P=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=P/'work/serve-walk-arm'
patch=''
for name in ['HeroTennisDriver.cs','TennisServeRoutine.cs','TennisGame.cs']:
 a=(W/'rollback/r2/Unity/Assets/Scripts/Tennis'/name).read_text().splitlines(True);b=(W/'CandidateR2Clone/Assets/Scripts/Tennis'/name).read_text().splitlines(True)
 patch+=''.join(difflib.unified_diff(a,b,fromfile='a/Unity/Assets/Scripts/Tennis/'+name,tofile='b/Unity/Assets/Scripts/Tennis/'+name))
(W/'report_r2/CANDIDATE_R2_GATES_FAIL.patch').write_text(patch)
audit={}
for tree in ['Assets','ProjectSettings']:
 for f in (W/'BeforeR2Clone'/tree).rglob('*'):
  if not f.is_file():continue
  relative=f.relative_to(W/'BeforeR2Clone');other=W/'CandidateR2Clone'/relative
  if other.is_file() and f.read_bytes()!=other.read_bytes():audit[str(relative)]='different'
(W/'report_r2/source-diff.json').write_text(json.dumps(audit,indent=2))
results={}
for p in (W/'smoke_r2').glob('*/trace.csv'):
 r=list(csv.DictReader(p.open()));scope=[x for x in r if x['phase']=='PlayerServeHold']
 if not scope:continue
 carry=[x for x in scope if abs(float(x['speed']))>.2 and float(x['prepare'])<=.001]
 held=[x for x in scope if x['in_hand']=='1'];smooth=[x for x in scope if not x['reset_reason']]
 if not carry or not held or not smooth:continue
 def peak(rows,k):
  x=max(rows,key=lambda x:float(x[k]));return {'value':float(x[k]),'frame':int(x['frame'])}
 results[p.parent.name]={'sampled_frames':len(r),'complete':(p.parent/'completed.json').exists(),'G1':peak(scope,'deepest_mm'),'G2':peak(held,'ball_palm_m'),'G4_elbow':[min(float(x['elbow_flexion']) for x in carry),max(float(x['elbow_flexion']) for x in carry)],'G4_wrist':peak(carry,'wrist_above_hips_m'),'G5_step':peak(smooth,'hand_step_m'),'G5_speed_delta':peak(smooth,'hand_speed_change'),'G3':{k:100*sum(int(x[k]) for x in carry)/len(carry) for k in ['game_visible','front_visible','side_visible']},'G7':sum(x['root_frame']==x['target_frame']==x['unity_frame'] for x in scope)/len(scope)*100}
(W/'report_r2/iterations.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2));print('source differences:',audit)
