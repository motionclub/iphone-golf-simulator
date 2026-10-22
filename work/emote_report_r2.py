from pathlib import Path
import json,hashlib
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');j=r/'work/emote-overhaul'
d=json.loads((j/'data/checks2.json').read_text());lines=[]
for sex in ['male','female']:
 for clip in ['Emote_Spike','Emote_Scuba','Emote_Thrust']:
  for gid,val in sorted(d[sex][clip].items(),key=lambda z:(z[0][0],int(z[0][1:]))):
   v={k:q for k,q in val.items() if k!='ok'}
   if gid=='G7':
    dur={'Emote_Spike':3.2,'Emote_Scuba':4.7,'Emote_Thrust':3.5}[clip]
    rows=json.loads((j/f'proof/collide/{clip}_{sex}_c3.json').read_text())['rows']
    v['midclip_max_mm']=round(1000*max(max(x['L']['pen_skin'],x['R']['pen_skin'],x['racket']['pen_skin']) for x in rows if .25<=x['t']<=dur-.25),4)
    v['midclip_limit_mm']=12;v['ready_edge_limit_mm']=20
   lines.append(f'GATE {gid} {sex} {clip}: {"PASS" if val["ok"] else "FAIL"} '+json.dumps(v,separators=(',',':')))
total=sum(len(b) for a in d.values() for b in a.values());npass=sum(v['ok'] for a in d.values() for b in a.values() for v in b.values())
extra=[]
for sex in ['male','female']:
 fd=j/'film_r2'/sex
 summary=(fd/'summary.txt').read_text();trig=json.loads((fd/'triggers.json').read_text())
 playok=all(f'{c} started=True' in summary and 'seen=True' in next(x for x in summary.splitlines() if x.startswith(c+' ')) for c in ['Emote_Scuba','Emote_Thrust'])
 extra.append(f'GATE UNITY_FILM {sex}: {"PASS" if playok else "FAIL"} clips_played={2 if playok else 0}/2; '+summary.replace('\n','; '))
 triggerok=trig['plain_point_emotes']==0 and trig['won_game_emotes']==1 and trig['point_after_game_emotes']==0 and trig['play_taunt_spike']['ok'] and trig['play_taunt_spike']['count']==1 and trig['intro_hook']['count']==1
 extra.append(f'GATE UNITY_TRIGGERS {sex}: {"PASS" if triggerok else "FAIL"} '+json.dumps(trig,separators=(',',':')))
cl=Path('/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/eea79e4e-5588-4d3e-bf82-e62668519187/scratchpad/UnityClone')
installed=[]
for sex in ['Male','Female']:
 for name in ['Scuba','Thrust']:
  rel=f'Unity/Assets/Characters/MatchHeroes/{sex}/{sex}_Emote_{name}.fbx';p=r/rel
  a=hashlib.sha256(p.read_bytes()).hexdigest();b=hashlib.sha256((cl/rel.removeprefix('Unity/')).read_bytes()).hexdigest()
  installed.append((rel,a,a==b))
extra.append(f'GATE INSTALLED_EQUALS_TESTED: {"PASS" if all(q[2] for q in installed) else "FAIL"} matching_FBX={sum(q[2] for q in installed)}/4')
extra.append('GATE ADNAN_EYE: FAIL approvals=0/1 required; films await Adnan\'s review, and his eye overrides numeric PASS.')
report=[f'# Scuba hand + Thrust arm pull — R2', '', f'Exported FBX gates: {npass}/{total} PASS. No numeric threshold relaxed. Visual acceptance: FAIL (0/1 approvals).', '', *lines, '', *extra, '', 'Original project files changed:', '- work/emote-overhaul/scripts/emo_clips2.py (Scuba2 and Thrust2 only)', '- work/emote-overhaul/scripts/check_gates2.py (new Scuba pose checks; T3 replaced by T7–T10)', '- work/emote-overhaul/GATE_DEFS_preregistered.md (disclosed R2 amendment before build)', '- The four Scuba/Thrust FBX under Unity/Assets/Characters/MatchHeroes/{Male,Female}/', '- work/emote-overhaul/GATE_RESULTS.md and GATE_RESULTS_r2.md (this report)', '', 'Generated working files: work/emotes/data/gen_*, export/blend, export/fbx; work/emote-overhaul/data/trace_*, clearance tracks, checks2.json, logs; R2 proof/film/rollback; verification and film wrappers in work/.', '', f'Rollback: {j}/rollback_r2/ (4 original FBX, 4 untouched meta files, source/gate snapshots, SHA256SUMS.txt).', f'Installed hashes: {j}/INSTALLED_SHA256SUMS_r2.txt', 'No commit.', '', 'Films (front | side plus separate game camera):']
for sex in ['male','female']:
 for clip in ['Scuba','Thrust']:
  report += [f'- {j}/film_r2/Emote_{clip}_{sex}.mp4',f'- {j}/film_r2/Emote_{clip}_{sex}_gamecam.mp4',f'- {j}/proof_r2/Emote_{clip}_{sex}_requested_sheet.png']
text='\n'.join(report)+'\n'
(j/'GATE_RESULTS_r2.md').write_text(text);(j/'GATE_RESULTS.md').write_text(text)
(j/'proof_r2/GATE_LINES_r2.txt').write_text('\n'.join(lines+extra)+'\n')
print(f'Report: {npass}/{total} numeric gates; {len(extra)} Unity/install/eye lines')
