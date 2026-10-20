from pathlib import Path
import json,hashlib,shutil
W=Path(__file__).resolve().parents[1];D=W/'r3';O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/in-g/outputs/serve-toss-jump-r3');s=json.loads((D/'FINAL_MEASURED_SUMMARY.json').read_text());m,f=s['male'],s['female']
def n(v):return f'{v:.3f}'
rows=[('G1 feet down','PASS',n(m['feet_mm'])+' mm',n(f['feet_mm'])+' mm'),('G2 load/toss knees','PASS',f"{n(m['load_knee_deg'][0])}–{n(m['load_knee_deg'][1])}°; toss {n(m['toss_knee_deg'])}°",f"{n(f['load_knee_deg'][0])}–{n(f['load_knee_deg'][1])}°; toss {n(f['toss_knee_deg'])}°"),('G3 takeoff','PASS','1.594 s both feet','1.594 s both feet'),('G4 air/contact knee','PASS',n(m['front_knee_contact_deg'])+'°; both clear',n(f['front_knee_contact_deg'])+'°; both clear'),('G5 apex','PASS','1.762 s','1.762 s'),('G6 landing','PASS','touch 1.878; settled 1.962 s','touch 1.878; settled 1.962 s'),('G7 entry, five phases','PASS in staged integration',n(m['entry_step_mm'])+' mm',n(f['entry_step_mm'])+' mm'),('G8 contact kept','PASS',n(m['contact_strings_mm'])+' mm; elbow '+n(m['elbow_contact_deg'])+'°',n(f['contact_strings_mm'])+' mm; elbow '+n(f['elbow_contact_deg'])+'°'),('G9 smooth','PASS in staged integration',n(m['left_step_mm'])+' mm left; wrist '+n(m['wrist_deg'])+'°',n(f['left_step_mm'])+' mm left; wrist '+n(f['wrist_deg'])+'°'),('G10 clearance','PASS','0 new/increased pairs; extra −129 vertices','0 new/increased pairs; extra −36 vertices'),('G11 foot drift','PASS',n(m['drift_mm'])+' mm',n(f['drift_mm'])+' mm'),('G12 times/input scope','PASS in tested snapshot','0.20/0.70/1.3333334/1.70; length 2.5','same; prefab unchanged by this task'),('G13 runtime scope','PASS','LockFeet only; replants 4→4','LockFeet only; replants 2→2'),('G14 proofs','PASS','8 decoded live films','8 decoded live films'),('G15 installed/tested','PENDING — not installed','Production rerun required','Production rerun required'),('G16 human EYE','PENDING','Adnan decides','Adnan decides')]
text='''Staged candidate — not installed. No commit.

The passing measurements below use the current production look/prefabs plus a frozen snapshot of the parallel 28b carry runtime. That runtime is not installed in production. With the exact current production runtime and this owned candidate in a private clone, male G7 fails at 51.128 mm (frame 110, clip 0.150439), and G9 wrist twist fails at 37.448° (frame 261, clip 0.325). The staged integration gives 22.028 mm and 12.397°. No production Serve asset or LockFeet hunk has been installed.

'''
legacy=D/'production_runtime_candidate/female/phase0/metrics.json'
if legacy.exists():
 l=json.loads(legacy.read_text());text+=f"Female current-runtime check: entry {n(l['G7_entry_max_step']['mm'])} mm, wrist {n(l['G9_wrist']['degrees'])}°.\n\n"
text+='| Gate | Result | Male | Female |\n|---|---|---|---|\n'+'\n'.join('| '+' | '.join(r)+' |' for r in rows)+'\n\n'
text+='''The load peaks lie in 1.279–1.333 s. Both heroes land and squash inside Serve, which exits at 1.978 s. Right-hand peak steps before/contact/after are 114.237/221.184/118.223 mm (male), 111.970/125.727/116.115 mm (female); no follow-through reversals. Contact differences also pass on the final rendered pose: 10.369/10.051 mm. Entry and hand-speed checks include both actor-relative and world motion. The five ReadyIdle phases are 0.583333, 0.150000, 1.900000, 1.466667 and 1.016667 s. Authored entry head/hand centering errors are at most 0.024 mm.

Runtime change: the replant guard removes the procedural Serve step. The toe anchor and shared hip reach correction keep the authored grounded stance reachable through the walk-in turn; the jump releases the lock. Only LockFeet changes; the Serve crossfade stays 0.08 s. The saved hunk was generated against the current production file. Installation must regenerate/re-read it immediately beforehand.

Before/after on the unchanged original candidate:

| Hero | G1 before → minimal guard | G2 before → guard | G3 before → guard | G11 before → guard |
|---|---|---|---|---|
| Male | 67.323 → 12.248 mm | 76.440 → 74.516° | 1.419/1.572 → 1.572/1.472 s | 30.758 → 474.824 mm |
| Female | 67.066 → 10.884 mm | 76.348 → 73.398° | 1.419/1.572 → 1.572/1.572 s | 35.001 → 539.124 mm |

The minimal guard alone did not solve the unreachable walk-in anchors or toe drift. On the unchanged original clip, authored toe drift is below 0.003 mm, while live toe drift was 31–35 mm; that establishes a runtime cause. The final runtime control preserves non-Serve replants 4→4 and 2→2. The finished clips and final lock together give the G1/G11 values above.

Clip changes: sway-centered Ready entry, separate shallow toss and trophy load, grounded feet through the toss, extended contact, earlier front touch and landing squash, continuous tuck/follow-through, steady female palm during windup, forearm roll corrections preserving hand world orientation, female contact stretch, and measured wrist clearance corrections. Marker times, length, rig and other clips were not authored by this task.

Other chats updated the production prefabs during this work. Those changes were preserved and included in the final input snapshot; the tested prefab hashes match that snapshot, and the serve timing values stayed unchanged. This task did not write those prefabs or the parallel carry/runtime code.

Install remains conditional: the parallel owner must supply its approved production carry runtime; rerun every gate with those actual inputs, obtain Adnan’s EYE decision on the matching films, install only the four Serve files and the LockFeet hunk, then rerun every gate on production. If any gate fails, install nothing. Rollback originals remain in work/serve-toss-jump/rollback_r3/ with SHA256SUMS. A change to the tested runtime inputs requires renewed verification and matching review films.

'''
text+='Candidate file hashes:\n\n```text\n'+(D/'final_candidate/SHA256SUMS').read_text()+'```\n\n'
text+='[Film review](REVIEW.md) · [Labeled live keys](proof/live_serve_keys.jpg) · [Candidate archive](staged_candidate.zip) · [Hunk patch](LOCKFEET.patch) · [Measured gate evidence](gate_results_current.json)\n'
(D/'GATE_REPORT.md').write_text(text);(O/'GATE_REPORT.md').write_text(text)
review='''These films show the staged candidate with the verified parallel carry input snapshot and current production look. Production installation is pending. G16 is a human EYE gate: the prompt says “Do not self-pass the look.”

![Live entry, contact and landing frames](proof/live_serve_keys.jpg)

| Hero | View | Full speed | Half speed |
|---|---|---|---|
'''
for sex in ['male','female']:
 for view in ['front','side','back','game']:
  base=f'serve_r3_{sex}_{view}';review+=f'| {sex.title()} | {view} | [Play](film/{base}.mp4) | [Play](film/{base}_half_speed.mp4) |\n'
review+='\n[Gate report](GATE_REPORT.md) · [Exact prompt](PROMPT_26c.txt) · [Movie decode audit](movie_audit.json)\n'
(O/'REVIEW.md').write_text(review);(D/'REVIEW.md').write_text(review)
import re
for name in ['GATE_REPORT.md','REVIEW.md']:
 p=O/name;v=p.read_text();v=re.sub(r'\]\(([^)]+)\)',lambda match:']('+str((O/match.group(1)).resolve())+')',v);p.write_text(v)
print('saved report and 16-film review index')
