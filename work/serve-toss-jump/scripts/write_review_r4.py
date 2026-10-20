from pathlib import Path
import csv,json,hashlib,difflib,shutil,gzip
W=Path(__file__).resolve().parents[1];P=W.parents[1];R=W/'r4';C=W/'UnityClone'
O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/in-g/outputs/serve-toss-jump-r4');O.mkdir(parents=True,exist_ok=True)
g=json.loads((R/'matrix14/gate_results.json').read_text());movies=json.loads((R/'proof/movie_decode/movie_audit.json').read_text())
assert len(movies)==16 and all(v['decoded_samples']==3 for v in movies)
for h in g.values():assert h['fiveDistinctEntryPhases'] and h['allMeasuredPhasesPass'] and h['G10'] and h['G13_control']['PASS']
identity=None;summary={}
for sex,h in g.items():
 ms=[p['metrics'] for p in h['phases']]
 for phase in range(5):
  T=R/f'matrix14/{sex}/phase{phase}'; lines=(T/'TESTED_SHA256SUMS').read_text()
  assert identity is None or identity==lines,'Different tested sources';identity=lines
  for line in lines.splitlines():
   sha,path=line.split('  ',1);assert hashlib.sha256((C/path).read_bytes()).hexdigest()==sha,path
  rows=list(csv.DictReader((T/'trace.csv').open()));assert all(None not in v and all(x is not None and x!='' for x in v.values()) for v in rows)
  target=O/'trace'/sex/f'phase{phase}';target.mkdir(parents=True,exist_ok=True)
  for name in ['trace.csv','contact.csv','bones.csv']:
   with gzip.open(target/(name+'.gz'),'wb') as out:out.write((T/name).read_bytes())
  for name in ['TESTED_SHA256SUMS','metrics.json','key_frames.csv','slots.txt']:(target/name).write_bytes((T/name).read_bytes())
 summary[sex]={'feet_mm':max(max(m['G1_heights_mm'].values()) for m in ms),'load_deg':[min(m['G2_knee_deg'] for m in ms),max(m['G2_knee_deg'] for m in ms)],'load_time':[min(m['G2_time'] for m in ms),max(m['G2_time'] for m in ms)],'takeoff':[min(min(m['G3_first_clearance'].values()) for m in ms),max(max(m['G3_first_clearance'].values()) for m in ms)],'entry_mm':max(m['G7_entry_world_max_step']['mm'] for m in ms),'contact_mm':max(p['contact_mm'] for p in h['phases']),'elbow_deg':min(m['G4_G8_contact']['Relbow_deg'] for m in ms),'wrist_deg':max(m['G9_wrist']['degrees'] for m in ms),'left_hand_step_mm':max(m['G9_hands']['L_all']['mm'] for m in ms),'foot_drift_mm':max(m['G11_drift']['live']['mm'] for m in ms),'landing_s':max(m['G6_touch']['clipTime'] for m in ms),'settled_s':max(m['G6_settled']['clipTime'] for m in ms),'apex_s':[min(m['G5_apex'] for m in ms),max(m['G5_apex'] for m in ms)],'nonserve_steps':h['G13_control']}
patch=[];guard={};scope=json.loads((R/'SCOPE_AUDIT.json').read_text())
for name in ['HeroTennisDriver.cs','TennisGame.cs','TennisServeRoutine.cs']:
 old=P/'Unity/Assets/Scripts/Tennis'/name;new=R/'rebased_source/Unity/Assets/Scripts/Tennis'/name
 guard[str(old.relative_to(P))]=hashlib.sha256(old.read_bytes()).hexdigest()
 patch.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='a/'+str(old.relative_to(P)),tofile='b/'+str(old.relative_to(P))))
prod=(P/'Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs').read_text();clone=(C/'Assets/Scripts/Tennis/HeroTennisDriver.cs').read_text()
def region(s):a=s.index('        void LockFeet(');b=s.index('        static void TwoBone(',a);return a,b
a,b=region(prod);c,d=region(clone);only=prod[:a]+clone[c:d]+prod[b:]
lf=''.join(difflib.unified_diff(prod.splitlines(True),only.splitlines(True),fromfile='a/Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs',tofile='b/Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs'))
(R/'LOCKFEET.patch').write_text(lf);(W/'r3/LOCKFEET.patch').write_text(lf)
(R/'PREVIEW.patch').write_text(''.join(patch));(R/'PRODUCTION_INPUT_FINAL.json').write_text(json.dumps(guard,indent=2))
for rel,sha in json.loads((R/'PRODUCTION_GUARD.json').read_text()).items():
 if rel.startswith('Unity/Assets/Scripts/Tennis/'):continue
 assert hashlib.sha256((P/rel).read_bytes()).hexdigest()==sha,'Production changed: '+rel
assert json.loads((R/'FOREIGN_PRODUCTION_EDITS.json').read_text())['foreign_edits_preserved']
for rel,sha in scope['prefab_hashes_unchanged'].items():assert hashlib.sha256((C/rel).read_bytes()).hexdigest()==sha and (C/rel).read_bytes()==(P/'Unity'/rel).read_bytes()
for sex in ['Male','Female']:
 p=C/f'Assets/Resources/Tennis/Customization/Player{sex}.prefab';s=p.read_text()
 for k,v in [('serveStanceTime','0.2'),('serveReleaseTime','0.7'),('serveTrophyTime','1.3333334')]:assert f'{k}: {v}' in s
 assert 'Serve=' in (R/f'matrix14/{sex.lower()}/phase0/slots.txt').read_text() and 'len=2.500 contact=1.7000' in (R/f'matrix14/{sex.lower()}/phase0/slots.txt').read_text()
(O/'film').mkdir(exist_ok=True)
for f in (R/'film').glob('*.mp4'):shutil.copy2(f,O/'film'/f.name)
(O/'proof').mkdir(exist_ok=True);shutil.copy2(R/'proof/live_serve_keys.jpg',O/'proof/live_serve_keys.jpg')
for sex in ['male','female']:
 for key in ['entry','bounce','contact','landing','settled']:
  for view in ['game','side','back']:
   f=R/f'matrix14/{sex}/phase0/key_{key}_{view}.png';shutil.copy2(f,O/'proof'/f'{sex}_{key}_{view}.png')
for name in ['SCOPE_AUDIT.json','EYE_APPROVED_WALK_DRIBBLE.json','LOCKFEET.patch','PREVIEW.patch','PRODUCTION_INPUT_FINAL.json','CLEARANCE_male.json','CLEARANCE_female.json','FOREIGN_PRODUCTION_EDITS.json']:(O/name).write_bytes((R/name).read_bytes())
(O/'TESTED_SHA256SUMS').write_text(identity)
(O/'gate_results.json').write_text(json.dumps(g,indent=2));(O/'MEASURED_SUMMARY.json').write_text(json.dumps(summary,indent=2));(R/'MEASURED_SUMMARY.json').write_text(json.dumps(summary,indent=2))
(O/'movie_audit.json').write_text(json.dumps(movies,indent=2))
lines=['GATE: staged measured serve checks PASS. NOT INSTALLED. Full-sequence human review and post-install validation remain pending.','','Five distinct live ReadyIdle entry phases were tested for each hero in fresh scenes. The user approved the walk and dribble in trial7. Subsequent fixes eased the entry turn/body lowering, bounded wrist twist while preserving the palm-down hold, blended the toss arm back to authored motion, and corrected release clearance for the rendered ball radius. This work modified no production files and made no commit. Current celebration changes from another chat are preserved in the fresh install patch.','','| Gate | Status | Measured result |','|---|---|---|']
M,F=summary['male'],summary['female']
rows=[('G1 Feet down','PASS',f'M/F max {M["feet_mm"]:.3f}/{F["feet_mm"]:.3f} mm (limit 10)'),('G2 Trophy load','PASS',f'M/F {M["load_deg"]}/{F["load_deg"]} degrees; times {M["load_time"]}/{F["load_time"]} s'),('G3 Takeoff','PASS',f'M/F {M["takeoff"]}/{F["takeoff"]} s'),('G4 Air/contact','PASS','Both feet clear; front knees below 35 degrees; back foot higher'),('G5 Apex','PASS',f'M/F {M["apex_s"]}/{F["apex_s"]} s'),('G6 Landing','PASS',f'Front touch {M["landing_s"]:.6f}/{F["landing_s"]:.6f} s; settled {M["settled_s"]:.6f}/{F["settled_s"]:.6f} s'),('G7 Entry','PASS',f'Worst M/F {M["entry_mm"]:.3f}/{F["entry_mm"]:.3f} mm across five distinct phases; limit 30'),('G8 Contact','PASS',f'Strings delta {M["contact_mm"]:.3f}/{F["contact_mm"]:.3f} mm; elbow {M["elbow_deg"]:.3f}/{F["elbow_deg"]:.3f} degrees'),('G9 Smoothness','PASS',f'Left hand max {M["left_hand_step_mm"]:.3f}/{F["left_hand_step_mm"]:.3f} mm; wrist max {M["wrist_deg"]:.4f}/{F["wrist_deg"]:.4f} degrees; racket steps and follow-through pass'),('G10 Clearance','PASS','0 new or increased pairs; M/F -129/-36 intersecting vertices'),('G11 Foot drift','PASS',f'M/F {M["foot_drift_mm"]:.3f}/{F["foot_drift_mm"]:.3f} mm; limit 5'),('G12 Times/prefabs','PASS','0.20/0.70/1.3333334/1.70 s; length 2.5 s; prefab hashes unchanged'),('G13 Scope/control','PASS','User expanded ownership to arm/dribble; only owned runtime paths changed. Replant steps before/after M 4/4, F 3/3. Current LockFeet hunk saved.'),('G14 Proof','PASS','16 films; all decode start/middle/end; contact sheet and populated live traces included'),('G15 Installed equals tested','PENDING','Not installed. Back up and apply a fresh hunk patch only after full visual approval; then rerun on production.'),('G16 Eye','PENDING','Walk/dribble approved by user (perfect). Full serve changed after that approval and needs review. 26c: Adnan’s eye overrides any agent GATE PASS.')]
lines += ['| '+ ' | '.join(v)+' |' for v in rows]
lines+=['','The measured foot lift was the procedural 65 mm replant arc. Its guard and independent plants reduced the previous approximately 64 mm lift to under 0.63 mm. The new entry smoothing keeps the final stagger and jump/landing targets. Original rollback remains in work/serve-toss-jump/rollback_r3; a fresh rollback will be saved before any installation.','','Film paths:']
for f in sorted((O/'film').glob('*.mp4')):lines.append(f'- [{f.name}](film/{f.name})')
(O/'GATE_REPORT.md').write_text('\n'.join(lines)+'\n');(R/'GATE_REPORT.md').write_text('\n'.join(lines)+'\n')
(O/'REVIEW.md').write_text('The walk/dribble approval is recorded. Please review the full male and female serve after the entry and toss-handoff smoothness fixes. Prompt 26c requires full human EYE review before installing; production is untouched. All staged measured motion checks pass. See GATE_REPORT.md for all 16 films and measurements.\n')
(O/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(O))+'\n' for f in sorted(O.rglob('*')) if f.is_file() and f.name!='SHA256SUMS.txt'))
print(json.dumps(summary,indent=2));print(O)
