from pathlib import Path
import csv,gzip,hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[3]
W=ROOT/'work/serve-toss-jump'
D=W/'r2'
OUT=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/in-g/outputs/serve-toss-jump-r2')
OUT.mkdir(parents=True,exist_ok=True)
metrics=json.loads((D/'live_metrics.json').read_text())
audit=json.loads((D/'source_audit.json').read_text())
movies=json.loads((D/'proof/movie_decode/movie_audit.json').read_text())
old=json.loads((W/'data/fbx_gates.json').read_text())
assert len(movies)==16 and all(m['decoded_samples']==3 for m in movies)
assert all(abs(m['duration_s']-(269/(15 if 'half_speed' in m['file'] else 30)))<.001 for m in movies)
assert audit['runtime_source_files_changed']==0 and audit['rollback_matches_installed']
M,F=metrics['male'],metrics['female']
gates=[
('G1 TOSS_FEET_DOWN','FAIL',f"Live maximum heel/toe heights M: {M['G1_max_heights_mm']['Lheel']:.3f}/{M['G1_max_heights_mm']['Ltoe']:.3f} mm (left); F: {F['G1_max_heights_mm']['Rheel']:.3f}/{F['G1_max_heights_mm']['Rtoe']:.3f} mm (right), within 0.20–1.55 s; limit 10 mm. Procedural step arc is the cause."),
('G2 LOAD_AT_TROPHY','FAIL',f"M deepest pre-takeoff knee {M['G2_knee_peak_deg']:.2f}° at {M['G2_peak_clipTime']:.6f} s: PASS. F deepest {F['G2_knee_peak_deg']:.2f}° at {F['G2_peak_clipTime']:.6f} s: FAIL (outside 65–80° and 1.25–1.36 s), caused by the procedural step. F trophy-window peak is 76.35°. Lowest pelvis is 1.278853 s for both."),
('G3 TAKEOFF','FAIL',"First clearance >3 mm after clip 0.20 s: M left / F right at 1.418728 s, before 1.57–1.63 s. Both feet clear >3 mm on the drive at 1.572265 s for both; that does not erase the earlier procedural lift. Preparatory sway also produces >3 mm clearance at about 0.151 s."),
('G4 AIR_AT_CONTACT','FAIL',f"At 1.70 s, interpolated front/back lowest-foot clearance M {min(M['G4_contact']['Lheel_mm'],M['G4_contact']['Ltoe_mm']):.2f}/{min(M['G4_contact']['Rheel_mm'],M['G4_contact']['Rtoe_mm']):.2f} mm; F {min(F['G4_contact']['Lheel_mm'],F['G4_contact']['Ltoe_mm']):.2f}/{min(F['G4_contact']['Rheel_mm'],F['G4_contact']['Rtoe_mm']):.2f} mm: air/back-height components PASS. Front knee M/F {M['G4_contact']['Lknee_deg']:.2f}/{F['G4_contact']['Lknee_deg']:.2f}° >35°: FAIL."),
('G5 APEX_AFTER_CONTACT','PASS',"Live pelvis apex 1.778333 s for both, within 1.72–1.82 s."),
('G6 LANDING_IN_GAME','FAIL',"Serve ends at clip 1.978333 s; authored front touch remains 2.033333 s. Live Serve landing rows before 1.90 s: 0/0. At clip 1.90 s the front foot is still about 14 cm up. The eventual front/back touches occur at recording times 7.983333/8.183333 s (12 frames apart), in Run after Serve has exited; those are not an authored Serve landing. Game/side stills show this blend touchdown and are labelled accordingly."),
('G7 NO_POP_IN','FAIL',f"First 0.15 s after the live driver enters Serve: max head/hand step M/F {M['G7_first_0p15_entry_hand_head_max_step']['mm']:.2f}/{F['G7_first_0p15_entry_hand_head_max_step']['mm']:.2f} mm, both >30 mm (left hand, frame 116). Pure Serve at about 0.199 s differs from the live driver's ReadyIdle source at its current phase by up to {M['G7_live_ready_source_max_delta']['mm']:.2f}/{F['G7_live_ready_source_max_delta']['mm']:.2f} mm. Clip frame 0 is not sampled by this live entry; the no-pop alternative fails directly."),
('G8 CONTACT_POSE_KEPT','FAIL',f"A paired installed-vs-candidate live strings measurement was not rerun after the required stop. The unchanged candidate's prior 1.3× FBX strings deltas are M/F 13.15/33.43 mm; female exceeds the new 15 mm limit. Live right-elbow angles interpolated at 1.70 s are {M['G4_contact']['Relbow_deg']:.2f}/{F['G4_contact']['Relbow_deg']:.2f}° against ≥170°; these are bracket estimates, not an exact 1.70 s sample."),
('G9 SMOOTH','FAIL',f"Largest complete hand step strictly before contact M/F {M['G9_hand_step_strictly_before_contact']['mm']:.2f}/{F['G9_hand_step_strictly_before_contact']['mm']:.2f} mm >150 (left hand, 1.530292→1.572265 s). Contact-crossing hand step M/F {M['G9_hand_step_before']['mm']:.2f}/{F['G9_hand_step_before']['mm']:.2f} mm (left hand, 1.662085→1.703333 s); the interval is mostly before contact and exceeds the 150 mm limit. Post-contact maximum is {M['G9_hand_step_after']['mm']:.2f}/{F['G9_hand_step_after']['mm']:.2f} mm, under 220. Longitudinal wrist-twist step M/F {M['G9_longitudinal_wrist_twist_max']['degrees']:.2f}/{F['G9_longitudinal_wrist_twist_max']['degrees']:.2f}° >15. Full local wrist-orientation steps are 45.56/58.20°. Reversal-free follow-through is not accepted after the stop."),
('G10 CLEARANCE','FAIL',"Prior penetrate_dj.py measurements on these identical candidate FBX hashes, at 1.3× and 3 mm: entirely new frame/obstacle pairs M/F 0/2; increased existing pairs 2/5; extra intersecting vertices +35/+315. No collision rebuild was performed after the runtime-owner stop."),
('G11 NO_FOOT_SLIDE','FAIL',"Planted toe drift M/F 30.70/34.95 mm >5 mm (right toe, frames 112/113). Actor root is stationary across these plant episodes; the player actor frame is aligned with the court. Ankle locking still permits toe movement as the foot rotates. Positions, lock positions, weights and step state are recorded, not inferred from film pixels."),
('G12 GAME_TIMES_UNCHANGED','PASS',"Stance/release/trophy/contact remain 0.20/0.70/1.3333334/1.70 s in both PlayerMale/PlayerFemale prefabs; imported lengths 2.500 s (76 authored samples). Prefab/Serve meta hashes unchanged. Both live traces enter Rally; 295 Serve rows each."),
('G13 PROOF_COMPLETE','PASS',"16 live-game films: front, side, back, game × male/female × full/half speed. 269 pictures per view; 8.966667 s at 30 fps, 17.933333 s at 15 fps. All 16 decode at start/middle/end (48 samples). Each 60 Hz trace has 537 contiguous rows, 282 populated fields, and no nonfinite or missing values. Each has 139,620 bone/stage rows for 52 mapped skeleton bones. Tail is 2.5 s after contact and 1.966667 s after actual blend touchdown; the authored Serve landing still fails G6."),
('G14 INSTALLED_EQUALS_TESTED','FAIL',"NOT INSTALLED. Only 2/4 tested FBX/meta hashes match the installed files (the two metas). All 4 installed files equal rollback_r2 byte for byte."),
('G15 EYE','FAIL',"All 16 film paths are listed below. Adnan reviews received: 0. These are diagnostic failed-candidate films; no visual acceptance is claimed.")
]
(D/'gate_results.json').write_text(json.dumps({name:{'status':status,'measurement':text} for name,status,text in gates},indent=2)+'\n')

report=f'''**GATE: SERVE TOSS-JUMP ROUND 2 FAIL — NOT INSTALLED. Mandatory runtime-owner handoff.**

Read `ArtDir/hero/base_lock/parallel_prompts/26b_SERVE_TOSS_JUMP_FINISH.txt` in full, plus prompt 26's report, NOT_INSTALLED, timeline audit, scripts and proof sheet. Continued from its existing candidate and APFS UnityClone. No clip rebuild, runtime edit, installation or commit occurred.

The prompt explicitly requires: “If it's game code owned by another chat … stop and report the exact line and the minimal change, don't edit it.” The live trace confirms that condition. Prompt 28 must handle the runtime change before the remaining clip fixes can proceed.

**Cause of the Unity foot lift**

`Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs:708`, in `LockFeet`, adds `sin(pi * clamp01(stepT)) * 0.065` metres to the animated foot height. Lines 716–720 start that procedural replant when planted-foot drift exceeds 0.20 m. The match Serve is currently eligible for this step, including a step carried over from the walk-in.

At recording frame 377 / clip 1.402685 s, measured drift from the locked foot is 249.350 mm for the male left foot and 299.749 mm for the female right foot, so the 200 mm trigger fires. At frame 381 / clip 1.510118 s:

| Measurement | Male left foot | Female right foot |
|---|---:|---:|
| Base Serve / Ready / Walk / Run weights | 1 / 0 / 0 / 0 | 1 / 0 / 0 / 0 |
| Upper-body layer weight | 0 | 0 |
| Heel height in base / both layers / pure imported Serve | 3.310993 mm | 3.172889 mm |
| Heel height in final live pose | 67.323490 mm | 67.185100 mm |
| Added procedural rise | 64.012497 mm | 64.012211 mm |
| `stepT` | 0.555556 | 0.555556 |
| Predicted rise from line 708 | 64.012488 mm | 64.012488 mm |
| Prediction residual | 0.000009 mm | 0.000277 mm |
| Ground lift / sink | 0 / 0 | 0 / 0 |

The base and upper-layer replay agree exactly at this peak; ReadyIdle/locomotion contributes zero. SmoothRoot has no vertical contribution. The step explains the extra rise numerically. The earlier report's 63.8 mm lowest-right-foot lift need not occur at the same clip time in this capture: the pre-serve stance uses an absolute-time sway and this recorder starts during walk-in. It records preparatory right-foot steps as well as the later grounded-period steps above.

The clone's two Serve `.metas` equal production exactly: Generic rig, compression 0, resampled curves, length 2.5 s, retained original root orientation/position. The imported candidate skeleton also agreed with the independently reimported FBX within 0.009 mm in prompt 26's unchanged-candidate audit. Changing import settings cannot remove this runtime step arc.

The proposed minimal change is in `MINIMAL_RUNTIME_CHANGE.md`: cancel a pending procedural step during match Serve and exclude match Serve from the drift-triggered step creation, while retaining the normal planted-foot lock. It is **not applied or tested**. The source line numbers refer to runtime SHA256 `18c0b0e121003cff345a6498e6fc4bd31e16897eb2c278bd6ec4f284dd6ca790`.

**Gate results on the unchanged candidate**

All new pose measurements come from the live 60 Hz game trace. Contact interpolation uses clip-time bracket 1.662085–1.703333 s; both the bracket and method are recorded. Heights use the driver's calibrated ReadyIdle heel/toe rest offsets, the same joint-clearance convention as its foot logger. Source collision/strings results are explicitly identified as prior FBX evidence and are not presented as new live checks. M/F means male/female; a failed or unverified required component makes a gate FAIL.

| Gate | Result | Measurement |
|---|---|---|
'''
report+=''.join(f'| {name} | **{status}** | {text} |\n' for name,status,text in gates)
report+='''
**Proof tool and films**

Added only `Unity/Assets/Editor/ServeJumpProof.cs` and its meta to the production project. The identical Editor-only tool compiled and completed both live runs in the existing scratch clone (exit 0). It records after the driver's LateUpdate, samples base/both-layer/pure-Serve/Ready source stages without advancing graph time, and restores graph weights, clip times and transforms before rendering. It adds a front camera and preserves game, side and back captures beyond the blend touchdown. Existing ServeTossFilm.cs and MatchHeroFilm.cs were not changed.

The two trace CSVs contain palm, all four heel/toe positions and calibrated clearances, left/right knee flexion, pelvis, both wrist quaternions, actor/hero positions, planted-foot lock positions, step states and layer weights. `bones.csv.gz` contains the skeleton-stage replays; `live_metrics.json` includes measured step-formula residuals and gate numbers.

`proof/live_serve_keys.jpg` is the live-game contact sheet. `proof/male_procedural_step.jpg` and `female_procedural_step.jpg` show the diagnosed step and its measured numbers. `proof/<sex>_actual_blend_touch_game.png` and `_side.png` show the eventual foot touch after switching to Run; they are not labelled as the requested Serve landing.

All film originals are under the project path `work/serve-toss-jump/r2/film/`; review copies are linked here:

| Hero | View | Full speed | Half speed |
|---|---|---|---|
'''
for sex in ['male','female']:
    for view in ['front','side','back','game']:
        full=f'serve_r2_{sex}_{view}.mp4';half=f'serve_r2_{sex}_{view}_half_speed.mp4'
        report+=f'| {sex} | {view} | [{full}]({OUT}/film/{full}) | [{half}]({OUT}/film/{half}) |\n'
report+=f'''
**Installation, scope and remaining work**

NOT INSTALLED. The candidate FBXs and original prompt 26 scripts remain available. No authored landing/compression changes were attempted after confirming the mandatory runtime-owner stop. Remaining clip work: front touch ≤1.90 s; squash 1.90–1.96 s and settle by 1.97 s; ReadyIdle blend-in; front knee ≤35° at contact; female strings shift ≤15 mm; wrist/hand smoothness and collision counts. The revised toss-knee limit also still needs a pass: these live traces reach about 60° by clip 1.083 s, although the prior pre-release-only FBX audit was 38/39°. Rerun all live gates after the runtime owner fixes the procedural step, then install only on complete success and verify installed hashes.

Rollback directory: `{W}/rollback_r2/`. It contains all four original installed files plus SHA256SUMS.txt. All four still match production; restoration is unnecessary. Original round-1 rollback and report are preserved.

| File | Current installed SHA256 | Tested candidate SHA256 |
|---|---|---|
'''
for name,h in audit['installed_sha256'].items():report+=f"| {name} | `{h}` | `{audit['tested_sha256'][name]}` |\n"
report+=f'''
Changed by this task: the new Editor-only proof script/meta; scripts, logs, measurements, PNGs, movies and reports under `work/serve-toss-jump/`; review deliverables under `{OUT}`. No runtime source, hero mesh, socket, shader, other clip, prefab, QualitySettings or golf file was edited. No commit.

Source audit observed an unrelated change to `Unity/Assets/Tests/EditMode/TennisTutorialTests.cs` while this task ran. This task did not edit or revert it. It is recorded in source_audit.json and is not a serve gate failure.
'''
(D/'GATE_REPORT.md').write_text(report)
(W/'GATE_REPORT_R2.md').write_text(report)
(W/'NOT_INSTALLED_R2.md').write_text('NOT INSTALLED: required stop in prompt 26b. HeroTennisDriver.LockFeet adds the measured 65 mm procedural step. Prompt 28 owns the runtime change. See r2/GATE_REPORT.md and r2/MINIMAL_RUNTIME_CHANGE.md. All four production Serve FBXs/metas still equal rollback_r2. No commit.\n')
for folder in ['film','proof']:
    destination=OUT/folder;destination.mkdir(exist_ok=True)
    for p in (D/folder).iterdir():
        if p.is_file(): shutil.copy2(p,destination/p.name)
for name in ['GATE_REPORT.md','MINIMAL_RUNTIME_CHANGE.md','live_metrics.json','source_audit.json','gate_results.json']:
    shutil.copy2(D/name,OUT/name)
shutil.copy2(D/'proof/movie_decode/movie_audit.json',OUT/'movie_audit.json')
shutil.copy2(W/'NOT_INSTALLED_R2.md',OUT/'NOT_INSTALLED.md')
shutil.copy2(W/'scripts/ServeJumpProof.cs',OUT/'ServeJumpProof.cs')
for sex in ['male','female']:
    destination=OUT/'data'/sex;destination.mkdir(parents=True,exist_ok=True)
    shutil.copy2(D/sex/'trace.csv',destination/'trace.csv')
    with (D/sex/'bones.csv').open('rb') as src,gzip.open(destination/'bones.csv.gz','wb') as dst: shutil.copyfileobj(src,dst)
(OUT/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT))+'\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'))
print(f'Wrote report and verified review package: {OUT}')
