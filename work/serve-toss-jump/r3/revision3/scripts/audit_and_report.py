"""Final binary prompt-26 audit. Missing required runtime measurements are FAIL.
This script never installs assets or modifies production Unity files.
"""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];REPO=W.parents[1]
sys.path.insert(0,str(W/'scripts'))
from read_trace import load
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fb=json.load(open(W/'data/fbx_gates.json'));imports=json.load(open(W/'data/unity_import_audit.json'))
scale=json.load(open(W/'data/contact_racket_scale_audit.json'))
feet=list(csv.DictReader(open(W/'proof/unity_feet/trace.csv')))
shots=json.load(open(W/'proof/unity_feet/shots.json'))
candidate_hashes={f'{H}_Serve.fbx':sha(W/'export/fbx'/f'{H}_Serve.fbx') for H in ['Male','Female']}
runtime={};by_sex={}
for sex,H,sc,letter in [('male','Male','vs_Nadia','M'),('female','Female','vs_Viktor','F')]:
    rows=load(str(W/f'film_{sex}/trace.csv'));serving=[r for r in rows if r['state'].startswith('Serve')]
    r=[x for x in feet if x['role']=='PLAYER' and x['sex']==letter and x['scenario']==sc and 300<=int(x['frame'])<1140]
    sr=[x for x in r if x['clip'].endswith('_Serve') and x['footL_mm'] and x['footR_mm']]
    air=lambda x:min(float(x['footL_mm']),float(x['footR_mm']))>0
    early=[x for x in sr if float(x['clipTime'])<1.55 and air(x)]
    early3=[x for x in sr if float(x['clipTime'])<1.55 and min(float(x['footL_mm']),float(x['footR_mm']))>3]
    first=next(x for x in sr if air(x));toss=[x for x in sr if .2<=float(x['clipTime'])<=.75]
    oi=next(i for i,x in enumerate(r) if x['clip'].endswith('_Serve') and float(x['clipTime'])>=1.55 and air(x))
    left=next((i for i in range(oi+1,len(r)) if float(r[i]['footL_mm'])<=0),None)
    right=next((i for i in range(oi+1,len(r)) if float(r[i]['footR_mm'])<=0),None)
    lead=int(r[right]['fc'])-int(r[left]['fc']) if left is not None and right is not None else None
    airborne=float(r[left]['t'])-float(r[oi]['t']) if left is not None else None
    sw=[x for x in serving if x['sw']=='True']
    a=max((x for x in sw if x['clip']<=1.7),key=lambda x:x['clip']);b=min((x for x in sw if x['clip']>=1.7),key=lambda x:x['clip']);u=(1.7-a['clip'])/(b['clip']-a['clip'])
    p={k:(1-u)*np.array(a[k])+u*np.array(b[k]) for k in ['Rs','Rh','Rel']};v=p['Rs']-p['Rel'];z=p['Rh']-p['Rel'];elbow=float(np.degrees(np.arccos(np.clip(v@z/np.linalg.norm(v)/np.linalg.norm(z),-1,1))))
    contacts=[x.split(',') for x in shots['serves'] if x.split(',')[1]==letter and x.split(',')[0]=='PLAYER']
    time_delta=max(abs(float(x[4])) for x in contacts)
    prefab=Path('Assets/Resources/Tennis/Customization')/f'Player{H}.prefab'
    same_prefab=sha(REPO/'Unity'/prefab)==sha(W/'UnityClone'/prefab)
    same_meta=(REPO/'Unity/Assets/Characters/MatchHeroes'/H/f'{H}_Serve.fbx.meta').read_bytes()==(W/'rollback'/f'{H}_Serve.fbx.meta').read_bytes()==(W/'UnityClone/Assets/Characters/MatchHeroes'/H/f'{H}_Serve.fbx.meta').read_bytes()
    runtime[sex]={
        'film_trace_rows':len(rows),'Serve_rows':len(serving),'Serve_clip_max_s':max(x['clip'] for x in serving),
        'runtime_foot_rows':len(sr),'air_clearance_threshold_mm':0,'foot_trace_rounding_mm':.1,
        'before_1p55_both_positive_foot_frames':len(early),'before_1p55_both_over_3mm_frames':len(early3),
        'first_both_positive_foot_clip_time':float(first['clipTime']),
        'first_both_positive_foot_heights_mm':[float(first['footL_mm']),float(first['footR_mm'])],
        'toss_lowest_foot_max_LR_mm':[max(float(x[k]) for x in toss) for k in ['footL_mm','footR_mm']],
        'first_positive_segment_after_1p55_clip_s':float(r[oi]['clipTime']),'first_positive_segment_after_1p55_airtime_real_s':airborne,
        'landing_lead_frames_at_60fps':lead,'left_touch_clip':r[left]['clip'] if left is not None else None,
        'right_touch_clip':r[right]['clip'] if right is not None else None,
        'runtime_palm_fields':0,'runtime_toe_fields':0,'runtime_heel_fields':0,'runtime_pelvis_fields':0,
        'runtime_knee_fields':0,'runtime_wrist_rotation_fields':0,'runtime_planted_foot_position_fields':0,
        'elbow_at_1p70_interpolated_deg':elbow,'elbow_interpolation_bracket_s':[a['clip'],b['clip']],
        'contact_log_rows':len(contacts),'contact_log_max_abs_clip_delta_s':time_delta,
        'contact_log_closest_strings_ball_min_mm':min(float(x[10]) for x in contacts)*1000,
        'contact_log_closest_strings_ball_max_mm':max(float(x[10]) for x in contacts)*1000,
        'prefab_bytes_identical':same_prefab,'FBX_meta_bytes_identical':same_meta,
        'Rally_trace_rows':sum(x['flow']=='Rally' for x in rows),'Unity_front_films':0,
        'Serve_rows_at_or_after_authored_left_touch':sum(x['clip']>=61/30 for x in serving),
    }
    rr=runtime[sex]
    # Runtime geometric fields required for the following gates are absent; do not substitute an edit-mode trace.
    g={k:False for k in fb[sex]}
    g['NO_AIR_BEFORE_DRIVE']=fb[sex]['NO_AIR_BEFORE_DRIVE']['pass'] and len(early)==0
    g['TAKEOFF']=fb[sex]['TAKEOFF']['pass'] and 1.57<=float(first['clipTime'])<=1.63
    g['CONTACT_POSE_KEPT']=fb[sex]['CONTACT_POSE_KEPT']['pass'] and elbow>=160
    g['WRIST_SMOOTH']=False # FBX hand-pop breach plus zero runtime rotation measurements.
    g['CLEARANCE']=fb[sex]['CLEARANCE']['pass']
    # Existing contact logger records the contact window; both films enter Rally and the full game capture shows the bounce/return.
    movie_checks=json.load(open(W/'proof/movie_decode/movie_audit.json')) if (W/'proof/movie_decode/movie_audit.json').exists() else [];movie_ok=any(Path(x['file']).name==f'serve_toss_jump_{sex}_game_full.mp4' and x['decoded_samples']==3 and x['duration_s']>5 for x in movie_checks)
    length_ok=scale[sex]['baseline']['imported_length_s']==scale[sex]['candidate']['imported_length_s']==2.5
    g['GAME_TIMES_UNCHANGED']=length_ok and movie_ok and same_prefab and same_meta and fb[sex]['GAME_TIMES_UNCHANGED']['numbers']['clip_length_s']==2.5 and imports[sex]['Unity_frames']==76 and len(contacts)>0 and time_delta<=.16 and rr['Rally_trace_rows']>0 and (W/'film'/f'serve_toss_jump_{sex}_game_full.mp4').exists()
    by_sex[sex]=g
runtime['candidate_hashes']=candidate_hashes
runtime['game_times_pass']=all(by_sex[s]['GAME_TIMES_UNCHANGED'] for s in ['male','female'])
(W/'data/unity_runtime_audit.json').write_text(json.dumps(runtime,indent=2))
results={k:{'pass':all(by_sex[s][k] for s in ['male','female']),'male':by_sex['male'][k],'female':by_sex['female'][k]} for k in fb['male']}
(W/'data/final_gate_results.json').write_text(json.dumps(results,indent=2))
M=fb['male'];F=fb['female'];um=runtime['male'];uf=runtime['female']
num=lambda g,k:[M[g]['numbers'][k],F[g]['numbers'][k]]
lines=[
 ('TOSS_FEET_DOWN',f"FBX toe maxima M/F {num('TOSS_FEET_DOWN','toe_max_mm')[0]:.3f}/{num('TOSS_FEET_DOWN','toe_max_mm')[1]:.3f} mm; Unity male lowest-right-foot maximum {um['toss_lowest_foot_max_LR_mm'][1]:.1f} mm > 10 mm; runtime heel/pelvis fields 0/0."),
 ('NO_AIR_BEFORE_DRIVE',f"FBX early-air frames 0/0; Unity M/F {um['before_1p55_both_positive_foot_frames']}/{uf['before_1p55_both_positive_foot_frames']} positive-clearance frames before 1.55 s (air threshold 0 mm; over 3 mm: {um['before_1p55_both_over_3mm_frames']}/{uf['before_1p55_both_over_3mm_frames']})."),
 ('RELEASE_ON_PATH',f"FBX anchor maxima M/F {max(M['RELEASE_ON_PATH']['numbers']['authoring_ritual_error_mm']):.4f}/{max(F['RELEASE_ON_PATH']['numbers']['authoring_ritual_error_mm']):.4f} mm; Unity-import maxima {max(imports['male']['Unity_imported_palm_anchor_error_mm']):.4f}/{max(imports['female']['Unity_imported_palm_anchor_error_mm']):.4f} mm; live-palm trace fields 0."),
 ('LOAD_AT_TROPHY',f"FBX knee maxima M/F {num('LOAD_AT_TROPHY','max_knee_deg')[0]:.2f}/{num('LOAD_AT_TROPHY','max_knee_deg')[1]:.2f} deg at 1.2667 s; lowest pelvis 1.2667 s both; runtime knee/pelvis fields 0/0."),
 ('TAKEOFF',f"FBX 1.6000 s both; first positive Unity foot clearances M/F {um['first_both_positive_foot_clip_time']:.4f}/{uf['first_both_positive_foot_clip_time']:.4f} s, outside 1.57–1.63 s."),
 ('AIR_AT_CONTACT',f"FBX front/back clearances M {M['AIR_AT_CONTACT']['numbers']['front_low_mm']:.1f}/{M['AIR_AT_CONTACT']['numbers']['back_low_mm']:.1f} mm, F {F['AIR_AT_CONTACT']['numbers']['front_low_mm']:.1f}/{F['AIR_AT_CONTACT']['numbers']['back_low_mm']:.1f} mm; hips +150.0 mm both; runtime pelvis fields 0."),
 ('APEX_AFTER_CONTACT',f"FBX apex 1.7667 s and airtime 0.4333 s both; Unity first positive-clearance segment after 1.55 s, airtime M/F {um['first_positive_segment_after_1p55_airtime_real_s']:.3f}/{uf['first_positive_segment_after_1p55_airtime_real_s']:.3f} s; runtime pelvis fields 0."),
 ('FRONT_FOOT_LANDS_FIRST',f"FBX left lead 5 frames both, knees {num('FRONT_FOOT_LANDS_FIRST','front_knee_peak_deg')[0]:.2f}/{num('FRONT_FOOT_LANDS_FIRST','front_knee_peak_deg')[1]:.2f} deg, dip 40.0 mm both; runtime knee/pelvis fields 0/0; Serve exits 1.9783 s before authored touch 2.0333 s, captured Serve landing rows 0/0."),
 ('CONTACT_POSE_KEPT',f"Strings shifts at 1.3x M/F {scale['male']['strings_delta_13_mm']:.2f}/{scale['female']['strings_delta_13_mm']:.2f} mm (limit 30 mm); FBX elbows {num('CONTACT_POSE_KEPT','hitting_elbow_deg')[0]:.2f}/{num('CONTACT_POSE_KEPT','hitting_elbow_deg')[1]:.2f} deg; live interpolated elbows {um['elbow_at_1p70_interpolated_deg']:.2f}/{uf['elbow_at_1p70_interpolated_deg']:.2f} deg."),
 ('NO_FOOT_SLIDE',f"FBX planted motion M/F {num('NO_FOOT_SLIDE','planted_motion_mm')[0]:.3f}/{num('NO_FOOT_SLIDE','planted_motion_mm')[1]:.3f} mm; landing spot maxima {max(M['NO_FOOT_SLIDE']['numbers']['landing_spot_delta_mm']):.3f}/{max(F['NO_FOOT_SLIDE']['numbers']['landing_spot_delta_mm']):.3f} mm; runtime planted-foot position fields 0."),
 ('WRIST_SMOOTH',f"FBX hand steps outside trophy→contact M/F {max(M['WRIST_SMOOTH']['numbers']['hand_step_outside_trophy_contact_LR_mm']):.2f}/{max(F['WRIST_SMOOTH']['numbers']['hand_step_outside_trophy_contact_LR_mm']):.2f} mm > 150 mm; twist steps {max(M['WRIST_SMOOTH']['numbers']['wrist_twist_step_LR_deg']):.2f}/{max(F['WRIST_SMOOTH']['numbers']['wrist_twist_step_LR_deg']):.2f} deg; runtime rotation fields 0."),
 ('CLEARANCE',f"M/F increased collision frame/obstacle pairs {num('CLEARANCE','increased_collision_frame_obstacles')[0]}/{num('CLEARANCE','increased_collision_frame_obstacles')[1]}, extra intersecting vertices +{num('CLEARANCE','extra_intersecting_vertices')[0]}/+{num('CLEARANCE','extra_intersecting_vertices')[1]}; entirely new pairs 0/2; racket 1.3x, original penetrate_dj.py threshold 3 mm."),
 ('GAME_TIMES_UNCHANGED',f"Clip lengths 2.5000 s / 76 frames both; stance/release/trophy/contact 0.20/0.70/1.3333334/1.70 unchanged; prefab/meta byte changes 0; films in Rally 2/2; contact-window logs {um['contact_log_rows']+uf['contact_log_rows']}/30 within ±0.16 s, largest clip delta {max(um['contact_log_max_abs_clip_delta_s'],uf['contact_log_max_abs_clip_delta_s'])*1000:.1f} ms."),
]
header=f"""# Prompt 26 — FAIL, not installed

Project: `{REPO}`. Prompt read in full: `ArtDir/hero/base_lock/parallel_prompts/26_SERVE_TOSS_THEN_JUMP.txt`.

Two candidates were rebuilt, exported, independently re-imported, collision checked and tested in the APFS clone `{W/'UnityClone'}`. The original male/female installed Serve FBXs and their metas still equal the four rollback backups byte for byte. No commit. No INSTALLED_SHA256SUMS.txt was written because installation did not occur.

The gate verdict includes the requested runtime proof. Missing runtime fields count as FAIL; edit-mode Unity import data does not replace a live film trace. M/F means male/female. Air uses positive emitted lowest-foot clearance with no added air allowance; the existing runtime foot logger rounds to 0.1 mm. Both the zero-mm result and the over-3-mm count are provided. Wrist hand-pop rows outside the stated trophy-to-contact interval retain the 150 mm limit. Collision counts increasing on an already-listed obstacle also fail.

"""
report=header+'\n'.join(f"- **{g}: {'PASS' if results[g]['pass'] else 'FAIL'}** — {s}" for g,s in lines)+'\n\n'
report+="""## Proof completeness — FAIL

Unity front films: **0/2**. `ServeTossFilm.Run` has fixed game/back/side captures and no front capture; no C# was edited. Side, back, game and half-speed side films exist for both heroes. Full game films from the existing `MatchHeroFilm.Run` supplement the supplied recorder, which stops saving Serve pictures before the ball bounces. Adnan eye acceptance: **0 reviews, FAIL**. Six representative movies decoded successfully at three times each; side/back pair films are 3.0 s, half-speed films 6.0 s, and full game films 10.70/10.667 s. These films are failed candidates, not an installed build.

Runtime measured fields missing from the supplied film/proof tools: palm, heel, toe, knee, pelvis, wrist rotation and planted-foot position: **0 each**. The imported Unity probe has all 52 mapped skeleton bones (Root is omitted by that probe), 76 samples, maximum disagreement with the re-imported FBX below 0.009 mm. Root translation is 0.000 mm; maximum FBX bone-length variation M/F is 0.00049/0.00123 mm (numerical evaluation).

Timeline audits also fail: maximum toss-knee flexion M/F is 38.28/38.90 degrees against the requested 25-degree maximum; stance bone positions over 0.00–0.20 s differ from actual READY by as much as 366.05/345.18 mm; front-knee flexion at contact is 78.12/73.71 degrees. See `data/timeline_audit.json` for exact values. Authoring rekeys and quaternion smoothing did not solve all constraints.

## Deliverables

- `proof/serve_keys.jpg`: both heroes, side view, every requested event including exact 0.45 s mid-toss. Authored Blender poses are explicitly labelled; landing/end are not passed off as Unity captures.
- `proof/serve_reference_comparison.jpg`: release, trophy, contact and landing next to watched reference frames. Reference time uncertainty is recorded in `WATCH_SERVE.md`.
- `film/serve_toss_jump_<sex>.mp4`: supplied recorder's game view.
- `film/serve_toss_jump_<sex>_views.mp4`: supplied recorder's back | side view.
- `film/serve_toss_jump_<sex>_side.mp4`, `_back.mp4`, `_side_half_speed.mp4`: individual supplied views.
- `film/serve_toss_jump_<sex>_game_full.mp4`: complete game-camera serve, ball landing and rally.
- `data/`: independent FBX traces, original/candidate collision lists, Unity import and runtime audits, final binary results.
- `logs/`: rebuild, export, re-import, collision and clone-only Unity logs.

## Files changed by this task

All working changes are under `work/serve-toss-jump/`: copied/rekeyed serve authoring and proof scripts; new generated NPZs and copied/baked blend files; two candidate FBXs under `export/fbx/`; these same two FBXs staged in `UnityClone/Assets/Characters/MatchHeroes/<Sex>/`; reference captures, films, sheets, logs, audits and rollback backups. No original Unity FBX, .meta, prefab, .cs, shader, kit or other animation was edited by this task. A deliverable copy also lives in the invoking chat's `outputs/serve-toss-jump/`.

Four unrelated original Unity files changed during the source-wide hash audit: `Assets/Editor/MatchHeroLockerExport.cs`, `Assets/Editor/HeroDetailTextures.cs`, `Assets/Scripts/Tennis/MatchHeroLook.cs`, `Assets/Resources/Tennis/Shaders/TennisCloth.shader`. This task did not edit or revert them. The frozen clone keeps the source it was cloned from; production Serve FBX/meta hashes remain unchanged.

## Rollback

Original backup path: `work/serve-toss-jump/rollback/` under the project above. It contains the two installed FBXs, both metas and `SHA256SUMS.txt`. Rollback is unnecessary because this candidate was not installed. `rollback/README.md` in the deliverable explains restoration of only these four files.

"""
(W/'GATE_REPORT.md').write_text(report)
(W/'NOT_INSTALLED.md').write_text('FAIL: no installation and no commit. The original Serve FBXs/metas still match rollback.\n\nCandidate SHA256:\n\n'+'\n'.join(f'{h}  {n}' for n,h in candidate_hashes.items())+'\n')
(W/'CANDIDATE_SHA256SUMS.txt').write_text('\n'.join(f'{h}  {n}' for n,h in candidate_hashes.items())+'\n')
print('\n'.join(f"{g} {'PASS' if results[g]['pass'] else 'FAIL'} {s}" for g,s in lines))
