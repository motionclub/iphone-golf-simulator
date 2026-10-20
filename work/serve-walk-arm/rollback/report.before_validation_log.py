from pathlib import Path
import json,csv,hashlib,shutil,zipfile
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
w=root/'work/serve-walk-arm'; out=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/find-2/outputs/serve-walk-arm')
r=json.loads((w/'report/matrix.json').read_text())
assert len(r)==16, f'Need 16 completed paired cases, have {len(r)}'
for name in r:
 for stage in ['before','after']:
  expected=900 if name.startswith('opponent-') else 1200
  assert json.loads((w/stage/name/'completed.json').read_text())['frames']==expected,(stage,name)

def f(x):return f'{x:.3f}'
def passed(b):return 'PASS' if b else 'FAIL'
player=[x for n,x in r.items() if not n.startswith('opponent-')]
control=max(x['control_comparison']['arm_max_delta_deg'] for x in r.values())
steps=max(x['smooth_frames_excluding_fixture_teleports']['step_cm'] for x in r.values())
speed=max(x['smooth_frames_excluding_fixture_teleports']['speed_change'] for x in r.values())
length=max(x['after_walk']['before_after_length_delta_mm'] for x in r.values())
depth=max(x['turn_plant']['depth_mm'] for x in r.values())
inside=max(x['turn_plant']['inside_share_max_pct'] for x in r.values())
lines=['# Serve walk / ball arm — GATE FAIL', '',
'2026-10-05. Requested prompt read in full and executed in the golf simulator project.', '',
f'Project: `{root}`. Work: `{w}`.', '',
'**No production carry fix was installed.** The new editor proof tool is the production change. The rejected runtime candidate is preserved as `report/CANDIDATE_GATES_FAIL.patch` and in the isolated `CandidateClone`; applying it would retain known failures. No commit was made.', '',
'## Reproduction and candidate', '',
'BEFORE male RH deuce walking-left: **105.208 mm** at frame **129**, **23.782%** of ARM vertices inside TRUNK, dominant bone **LeftUpperArm**. Female RH deuce: **78.701 mm** at frame **143**. Exact front/left stills are saved even though those odd frames are between the regular 30 fps image samples.', '',
'The Serve-derived hold target and inherited elbow pole do not fit the Walk pose; the IK pulls the upper arm through the trunk. Match forces serveYaw to zero, so an extra serveYaw rotation is not the cause, and walking right also penetrates. The game asks for the target before the driver updates the visual yaw/root, adding a one-frame mismatch.', '',
'The candidate samples the Walk hand, places the ball outside and in front of the thigh, guards the target with torso/thigh capsules, and chooses an outward elbow pole. It blends back in 0.25 s and changes only the Match carry branch. All eight player walking cases reach 0 mm / 0% penetration, but the complete acceptance gates remain FAIL.', '',
'## Binary gates', '',
'| Gate | Result | Actual result |', '|---|---|---|',
f'| G1 NO_ARM_IN_BODY | FAIL | Player walking: 0 mm / 0% in 8/8. Player planting: up to 30.215 mm; complete player/opponent transitions: {f(depth)} mm, {f(inside)}% max inside share. |',
'| G2 BALL_IN_HAND | FAIL | Player walking maximum 4.208 cm; unchanged free bounce reaches 74.673 cm. Some opponent/reset frames also exceed this, and ball centre can be inside the body/hand mesh. Limit: 3.5 cm, zero inside frames. |',
f'| G3 BALL_VISIBLE | FAIL | Per-run walking percentages below. Player game view can be below 95%; front view is below 100%. |',
f'| G4 FULL_ARM | FAIL | Same-frame BEFORE/AFTER limb lengths differ at most {f(length)} mm. Walking elbow range and belt height fail; lateral and exact mesh clearance are tabulated below. No bone scaling occurs. |',
f'| G5 SMOOTH | FAIL | Worst measured non-fixture hand step {f(steps)} cm and speed change {f(speed)} m/s/frame. Limits: 3 cm and 0.6. Carry-to-hold duration is 0.250 s. |',
f'| G6 NO_REGRESSION | FAIL | Stationary control and subsequent player serve positions: 0.000 cm difference; arm angle numerical roundoff at most {control:.8f} deg. Walking-right continuity/visibility or ball clearance worsens in some cases. |',
'| G7 MATRIX | FAIL | 16 requested player/opponent cases recorded BEFORE and AFTER. No case passes all G1–G6. Current Match driver always solves Left arm; left-handed player visuals are not mirrored. Opponent requested LH remains actual RH in ConfigureMatch. |',
'| G8 GAME_PATH | FAIL | Visible Editor Play capture attempted through the real A/D input path, but native UI control could not activate reliably. Captured keyboard runs contain no walking input, so they cannot establish this gate. |',
'| G9 EYE | FAIL | Eight paired films and eight paired contact sheets delivered. Adnan eye approval has not been supplied. |', '',
'## Per-run G1 and visibility', '',
'G1 covers the input walking/turning/planting sequence, including the planted bounce. Opponent rows cover the real OpponentServe flow before release, excluding its separate stationary control segment and the explicit fixture-placement frames 0 and 300. Walking is |speed| > 0.2 m/s with PrepareAmount <= 0.001. The opponent speed is in the server’s local frame; its two fixture segments move to the legal serve spot from each side.', '',
'| Case | BEFORE left mm @ frame / bone | AFTER walking mm / max inside % | AFTER G1 mm @ frame / max inside % | Game visible % | Front visible % |', '|---|---|---|---|---|---|']
for name,x in r.items():
 b=x['before_left'];a=x['after_walk'];s=x['turn_plant']
 lines.append(f"| {name} | {f(b['depth_mm'])} @ {b['frame']} / {b['bone']} | {f(a['depth_mm'])} / {f(a['inside_share_max_pct'])} | {f(s['depth_mm'])} @ {s['frame']} / {f(s['inside_share_max_pct'])} | {f(a['game_visible_pct'])} | {f(a['front_visible_pct'])} |")
lines += ['', '## Per-run hand, full-arm and smoothness', '',
'G2 maxima below use the complete pre-toss trace, including reset transients. The independently useful player walking/planting bounce maximum is 74.673 cm; the larger complete-trace figures include stale ball positions immediately after Refeed. These transients are visible in the CSV and are not presented as carry-target defects. G5 excludes frames 0/1 after each explicit opponent fixture placement (0, 300, 600), because a fixture teleport and its acceleration derivative are not a hand-motion test.', '',
'| Case | G2 pre-toss max cm / inside frames | Walk elbow min–max deg | Hip lateral min–max cm | Mesh clearance min cm | Wrist above hips max cm | Step cm / speed change m/s |', '|---|---|---|---|---|---|---|']
for name,x in r.items():
 a=x['after_walk'];pre=x['pre_toss'];s=x['smooth_frames_excluding_fixture_teleports']
 lines.append(f"| {name} | {f(pre['ball_palm_max_cm'])} / {pre['ball_inside_frames']} | {f(a['elbow_min_deg'])}–{f(a['elbow_max_deg'])} | {f(a['hip_lateral_min_cm'])}–{f(a['hip_lateral_max_cm'])} | {f(a['palm_trunk_clearance_min_cm'])} | {f(a['wrist_above_hips_max_cm'])} | {f(s['step_cm'])} / {f(s['speed_change'])} |")
lines += ['', '## G6 control evidence', '',
'The player controls contain plain hold, two bounces, wind-up, toss, trophy and contact. The opponent control segment starts at frame 600 at the legal service mark, then lets its real routine complete. Every matching control frame is compared, rather than selecting only six favorable stills. Player post-walk serve segment frames 552–767 is also compared. Phase transitions, release and contact in these identical trajectories occur on the same frames.', '',
'| Case | Control frames | Palm / ball / strings delta cm | Arm delta deg | Subsequent player serve delta cm | Walking right no worse |', '|---|---|---|---|---|---|']
for name,x in r.items():
 c=x['control_comparison'];s=x['serve_comparison']
 lines.append(f"| {name} | {c['control_frames']} | {f(c['palm_max_delta_cm'])} / {f(c['ball_max_delta_cm'])} / {f(c['strings_max_delta_cm'])} | {c['arm_max_delta_deg']:.8f} | {f(max(s[k+'_max_delta_cm'] for k in ['palm','ball','strings']))} | {passed(x['right_no_worse'])} |")
lines += ['', '## Constraint requiring a decision', '',
'G2 literally requires the ball to remain within 3.5 cm on every pre-toss frame, while the prompt also requires preserving the bouncing ritual and the BEFORE palm/ball path within 1 cm. The BEFORE free bounce separates ball and palm by about 74 cm. Keeping both ball and palm within 1 cm of those positions cannot reduce that separation to 3.5 cm. The earlier clarification request about applying G2 only to held/caught frames remains unanswered; the gate has not been silently narrowed. Other candidate failures remain independent of this conflict.', '',
'## Method and scope', '',
'Unity 6000.3.24f1, real Tennis.unity scene, campaign match, actual MatchHeroLook body, real TennisGame.Step/serve routine. Player input uses only ServeNudge. NativeControlled prevents the keyboard auto-toss in scripted runs; AutoPlay and ManualSimulation are false. Both halves and sex/hand settings are recorded in input.json. Opponent uses its production UpdateOpponent path without simulated player nudge.', '',
'Each rendered frame is measured at a 60 Hz capture clock. The actual SkinnedMeshRenderer is baked into world space. ARM uses summed bone weights > 0.5 to Left upper/lower arm, hand and fingers; TRUNK uses hips/spine/chest/upper chest and both thighs. Trunk triangles require three trunk vertices. Coincident bind vertices are welded to 1 micrometre, and partition boundary loops are capped for parity containment. Three oblique rays vote inside; depth is nearest ORIGINAL trunk triangle, excluding caps. The male split closes three loops from 248 boundary edges, with zero unresolved/nonmanifold edges. This is a bone-region mesh measurement, not garment occlusion or a capsule substitute.', '',
'Visibility is a ray against the full baked body plus game-camera frustum test, starting outside the 10 cm ball radius. Ball-centre containment uses the full body mesh; ball mesh overlap volume and cloth/racket occlusion are not measured. Camera views are fixed in the actor frame during turns. Game camera includes HUD. PNG every second frame is encoded at 30 fps; numeric trace remains 60 fps.', '',
'BEFORE and candidate assets are frozen in separate APFS clones so concurrent project work cannot change the comparison. source-audit.json confirms identical Serve FBXs, TennisGame, TennisRules, TennisActor, TennisServeRoutine and QualitySettings between both clones and production. A recursive binary comparison of all clone Assets reports only HeroTennisDriver.cs differing; all ProjectSettings match. Production HeroTennisDriver.cs still matches this task’s initial backup.', '',
'## Exact film and sheet paths', '']
for sex in ['male','female']:
 for view in ['game','front','left','top']:
  for suffix in [f'{sex}-{view}-before-after.mp4',f'{sex}-{view}-comparison-sheet.jpg']:
   lines.append(f'- `{w/"film"/suffix}`')
lines += ['', 'Raw per-run views and 12-frame sheets: `before/<case>/` and `after/<case>/`, with `game.mp4`, `front.mp4`, `left.mp4`, `top.mp4`, and `worst-<view>-sheet.jpg`. Every run also has trace.csv, input.json, completed.json, summary.json and measurement.txt.', '',
'## Changed files and rollback', '',
f'- New `{root/"Unity/Assets/Editor/ServeWalkFilm.cs"}` and its `.meta`. Rollback absence markers: `{w/"rollback/Unity/Assets/Editor/ServeWalkFilm.cs.ABSENT"}` and `.meta.ABSENT`.',
f'- Rejected candidate only: `{w/"CandidateClone/Assets/Scripts/Tennis/HeroTennisDriver.cs"}`. Original backup: `{w/"rollback/Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs"}`. Review patch: `{w/"report/CANDIDATE_GATES_FAIL.patch"}`.',
'- Backups also preserve original TennisActor.cs and TennisServeRoutine.cs; neither was edited. Tool iterations and analysis-script revisions are in rollback/. No FBX, mesh, rig, socket, golf code, timing, URP or quality setting was edited by this task.',
'- Only this task’s editor source/meta, text report, review patch and proof scripts are staged. Existing unrelated dirty/staged work is preserved. No commit.', '',
'## Remaining work', '',
'Correct the carry transition to meet continuity/visibility/full-arm limits, support the real opponent movement path, mirror left-handed Match visuals within the allowed scope, resolve the bounce/G2 contract, and complete a successful keyboard-driven Editor proof. The candidate should remain unapplied until these measurements pass, then Adnan can judge the paired film.']
(w/'report/GATE_RESULTS.md').write_text('\n'.join(lines)+'\n')
repro='''# Failing BEFORE reproduction

Male RH deuce: 105.2082 mm ARM-in-TRUNK at frame 129 (2.150 s), 23.78177% inside at that frame, dominant bone LeftUpperArm. Female RH deuce: 78.70114 mm at frame 143 (2.383 s), 17.39927% inside at that frame, LeftUpperArm. These are actual moving-left frames after the input stops while the game decelerates.

The target mismatch theory is confirmed: a Serve-derived hold target and inherited elbow pole do not fit the Walk body, pulling the upper arm through the trunk. Match sets serveYaw to zero, so the extra serveYaw rotation is not the cause, and the right walk also penetrates. The target is requested before the driver’s visual yaw/root update, adding a frame mismatch.

'''
for sex,frame in [('male',129),('female',143)]:
 for view in ['front','left']:
  repro+=f'- Exact {sex} {view} still: `{w/"before"/(sex+"-rh-deuce")/f"worst-{view}_{frame:05d}.png"}`\n'
repro+='\nAll 16 requested cases have a BEFORE trace and film. The candidate clears player walking penetration but fails the full gate; see report/GATE_RESULTS.md and report/matrix.json. No production carry fix is installed.\n'
(w/'REPRO.md').write_text(repro)
out.mkdir(parents=True,exist_ok=True)
for name in ['GATE_RESULTS.md','matrix.json','CANDIDATE_GATES_FAIL.patch','source-audit.json','keyboard-audit.json','clone-assets-diff.txt']:
 shutil.copy2(w/'report'/name,out/name)
shutil.copy2(w/'REPRO.md',out/'REPRO.md')
shutil.copy2(root/'Unity/Assets/Editor/ServeWalkFilm.cs',out/'ServeWalkFilm.cs')
shutil.copy2(root/'Unity/Assets/Editor/ServeWalkFilm.cs.meta',out/'ServeWalkFilm.cs.meta')
shutil.copytree(w/'film',out/'film',dirs_exist_ok=True)
(out/'before-stills').mkdir(exist_ok=True)
for sex,frame in [('male',129),('female',143)]:
 for view in ['front','left']:
  q=w/'before'/(sex+'-rh-deuce')/f'worst-{view}_{frame:05d}.png'
  shutil.copy2(q,out/'before-stills'/f'{sex}-{view}-frame-{frame}.png')
with zipfile.ZipFile(out/'matrix-traces-and-sheets.zip','w',zipfile.ZIP_DEFLATED) as z:
 for stage in ['before','after']:
  for name in r:
   run=w/stage/name
   for q in run.iterdir():
    if q.name in ['trace.csv','input.json','completed.json','summary.json','measurement.txt','worst.json'] or q.name.startswith('worst-') and q.suffix=='.jpg':z.write(q,str(q.relative_to(w)))
 for q in (w/'scripts').glob('*.py'):z.write(q,'scripts/'+q.name)
 for q in (w/'scripts').glob('*.sh'):z.write(q,'scripts/'+q.name)
manifest=[]
for q in out.rglob('*'):
 if q.is_file() and q.name!='deliverable-manifest.json':manifest.append({'path':str(q.relative_to(out)),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
(out/'deliverable-manifest.json').write_text(json.dumps(manifest,indent=2))
print(f'Report and {len(manifest)} deliverables saved to {out}')
