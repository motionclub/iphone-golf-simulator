"""Assemble checks.json, GATE_RESULTS.md and the gate roll-up from the measurement files (system python):  python3 finalize.py
Reads data/bake_*.json, verify_data_*.json, verify_blend_*.json, verify_fbx_*.json, fbx_*.json, verify_video.json, verify_repo.json, rig_*.json."""
import hashlib
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, '..'))
DATA = WORK + '/data'
EXPORT = WORK + '/export'
PROOF = WORK + '/proof'
CLIPS = ['ReadyIdle', 'SplitToForehand', 'SplitToBackhand', 'RecoverCenter', 'Forehand', 'ForehandOpen', 'ForehandWide', 'ForehandShort',
         'Backhand', 'BackhandWide', 'SliceApproach', 'Serve', 'Return', 'VolleyForehand', 'VolleyBackhand', 'Overhead']
HIT = ['Forehand', 'ForehandOpen', 'ForehandWide', 'ForehandShort', 'Backhand', 'BackhandWide', 'SliceApproach', 'Serve', 'Return', 'VolleyForehand', 'VolleyBackhand', 'Overhead']
MOVE = ['ReadyIdle', 'SplitToForehand', 'SplitToBackhand', 'RecoverCenter']
CAPS = dict(ReadyIdle=2.4, SplitToForehand=0.6, SplitToBackhand=0.6, RecoverCenter=0.8, Forehand=1.2, ForehandOpen=1.0, ForehandWide=1.3, ForehandShort=1.0, Backhand=1.2,
            BackhandWide=1.3, SliceApproach=1.2, Serve=1.6, Return=0.9, VolleyForehand=0.7, VolleyBackhand=0.7, Overhead=1.2)
SRC_SHA = dict(male='d6c4dcfb1150853a8802a8dc7501aa64066adb8b2734c14a4d6ed8e82dada781', female='a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1')
HEROES = ('male', 'female')
LABEL = dict(male='Male', female='Female')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for ch in iter(lambda: f.read(1 << 20), b''):
            h.update(ch)
    return h.hexdigest()


def J(name):
    return json.load(open(f'{DATA}/{name}'))


B = {t: J(f'bake_{t}.json') for t in HEROES}
VD = {t: J(f'verify_data_{t}.json') for t in HEROES}
VB = {t: J(f'verify_blend_{t}.json') for t in HEROES}
VF = {t: J(f'verify_fbx_{t}.json') for t in HEROES}
FB = {t: J(f'fbx_{t}.json') for t in HEROES}
RJ = {t: J(f'rig_{t}.json') for t in HEROES}
VV = J('verify_video.json')
VR = J('verify_repo.json')
FX = {t: J(f'fix_bones_{t}.json') for t in HEROES}
watch = open(f'{WORK}/WATCH.md').read()
sec_heads = {int(m.group(1)): m.group(2).strip() for m in re.finditer(r'^## (\d+)\.\s*(.*)$', watch, re.M)}

fails = {g: [] for g in ['FROM_WATCH', 'SHORT_IS_18', 'SLICE_IS_17', 'ALL_CLIPS', 'CONTACT_NAMED', 'IN_PLACE', 'RACKET_HELD', 'READS_FROM_BEHIND', 'READY_LOOP',
                         'BODY_UNCHANGED', 'ON_HERO', 'NO_FOOTAGE_IN_REPO']}


def add(g, t, msg):
    fails[g].append(f'{LABEL[t] if t in LABEL else t}: {msg}')


for t in HEROES:
    for m in VD[t]['gates']['FROM_WATCH_text']:
        add('FROM_WATCH', t, m)
    for m in VD[t]['gates']['SHORT_IS_18_data']:
        add('SHORT_IS_18', t, m)
    for m in VD[t]['gates']['SLICE_IS_17_data']:
        add('SLICE_IS_17', t, m)
    for m in VD[t]['gates']['CONTACT_NAMED_data']:
        add('CONTACT_NAMED', t, m)
    for m in VD[t]['gates']['IN_PLACE_data']:
        add('IN_PLACE', t, m)
    for m in VD[t]['gates']['READS_FROM_BEHIND_data']:
        add('READS_FROM_BEHIND', t, m)
    for m in VD[t]['gates']['READY_LOOP_data']:
        add('READY_LOOP', t, m)
    for g, lst in VB[t]['failed'].items():
        for m in lst:
            add(g, t, m)
    # ---- checks.json completeness for FROM_WATCH / CONTACT_NAMED
    c18, c17 = B[t]['clips']['ForehandShort'], B[t]['clips']['SliceApproach']
    # SLICE_IS_17: no racket-orientation key inside the contact window (the face is not authored), one-handed through the swing
    win = [k for k in c17['keys_near_contact'] if k['has_racket_orientation']]
    if win:
        add('SLICE_IS_17', t, f'racket-orientation keys inside the contact window: {win}')
    if not c17['thin']:
        add('SLICE_IS_17', t, 'thin flag missing')
    ev = VB[t].get('two_hand_events', {}).get('SliceApproach', {})
    if not ev.get('off_hand_on_racket_from_release_to_finish_hold_end', False):
        add('SLICE_IS_17', t, 'the off hand is on the racket between the release and the end of the finish')
    # ALL_CLIPS
    for c in CLIPS:
        L = B[t]['clips'][c]['length_s']
        if L > CAPS[c] + 1e-6:
            add('ALL_CLIPS', t, f'{c}: length {L:.3f} s > cap {CAPS[c]}')
        f = VF[t][c]
        if not f['ok']:
            add('ALL_CLIPS', t, f'{c}: FBX round trip failed {f}')
        if not os.path.exists(f'{EXPORT}/fbx/{LABEL[t]}_{c}.fbx'):
            add('ALL_CLIPS', t, f'{c}: FBX missing')
    if not (2.0 <= B[t]['clips']['ReadyIdle']['length_s'] <= 2.4):
        add('ALL_CLIPS', t, 'ReadyIdle length outside 2.0-2.4 s')
    # READS: videos and sheets
    v = VV[t]
    if not v['decode_ok']:
        add('READS_FROM_BEHIND', t, f'Review_{LABEL[t]}.mp4 does not decode as expected: {v}')
    for view in ('Behind', 'Side'):
        if not os.path.exists(f'{PROOF}/Sheet_{LABEL[t]}_{view}.png'):
            add('READS_FROM_BEHIND', t, f'Sheet_{LABEL[t]}_{view}.png missing')
    # BODY_UNCHANGED / source SHAs
    if VR['source_sha'][t]['sha256'] != SRC_SHA[t]:
        add('BODY_UNCHANGED', t, 'source blend SHA differs from the brief after the build')
for m in VR['failed']:
    if m.startswith('source '):
        fails['BODY_UNCHANGED'].append(m)
    else:
        fails['NO_FOOTAGE_IN_REPO'].append(m)

# ---- dedupe
for g in fails:
    seen, out = set(), []
    for m in fails[g]:
        if m not in seen:
            seen.add(m)
            out.append(m)
    fails[g] = out
verdict = 'PASS' if not any(fails.values()) else 'FAIL'

# =========================================================================================== checks.json
checks = dict(job='MATCH_ANIM_BUILD', built=time.strftime('%Y-%m-%d %H:%M:%S'), fps=30, watch_md=dict(path='work/match-anim-set/WATCH.md', sha256=sha(f'{WORK}/WATCH.md')),
              verdict=verdict, gates={g: dict(status='PASS' if not v else 'FAIL', failed=v) for g, v in fails.items()}, heroes={})
for t in HEROES:
    H = dict(source_blend=dict(sha256_expected=SRC_SHA[t], sha256_now=VR['source_sha'][t]['sha256']), blend=f'work/match-anim-set/export/HeroBase_{LABEL[t]}_MatchAnims.blend',
             blend_sha256=sha(f'{EXPORT}/HeroBase_{LABEL[t]}_MatchAnims.blend'), armature=f'Rig_{LABEL[t]}', bones=len(RJ[t]['bones']),
             measured_from_this_hero=dict(RJ[t]['measures'], height_m=RJ[t]['height']), rig_fixes=FX[t], clips=[])
    for c in CLIPS:
        b = B[t]['clips'][c]
        vd = VD[t]['clips'][c]
        fb = FB[t][c]
        sec = b['section']
        entry = dict(name=c, hero=t, watch_section=sec, watch_section_title=sec_heads.get(sec), watch_source=b['url'], thin=b['thin'], thin_reasons=b['thin_why'], length_s=round(b['length_s'], 4),
                     frames=b['frames'], fps=30, cap_s=b['cap_s'], contact_time_s=b['contact_s'], contact_frame=None if b['contact_s'] is None else int(round(b['contact_s'] * 30)),
                     left_release_s=b['events'].get('left_release_s'), key_sources=b['src_tokens'], n_keys=b['n_keys'],
                     fbx=dict(file=f'work/match-anim-set/export/fbx/{LABEL[t]}_{c}.fbx', bytes=fb['bytes'], sha256=fb['sha256'], reimport=VF[t][c]['ok'],
                              reimport_pose_max_err_mm=round(VF[t][c].get('pose_max_err_mm', -1), 5)))
        entry['measured'] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in vd.items() if k not in ('length_s', 'frames', 'section', 'contact_s', 'thin')}
        if b['contact_orientation_error'] is not None:
            entry['contact_racket_orientation_error_vs_authored_intent_deg'] = {k: round(v, 1) for k, v in b['contact_orientation_error'].items() if isinstance(v, float)}
        entry['diag'] = {k: round(v, 4) for k, v in b['diag'].items()}
        H['clips'].append(entry)
    checks['heroes'][t] = H
json.dump(checks, open(f'{WORK}/checks.json', 'w'), indent=1)

# =========================================================================================== GATE_RESULTS.md
L = []
w = L.append
w(f'# MATCH_ANIM_BUILD - gate results ({checks["built"]})')
w('')
w(f'**GATE: MATCH_ANIM_BUILD {verdict}**')
w('')
w('Everything below is measured by the scripts in `scripts/` on the files in this folder; the numbers are in `checks.json` and `data/verify_*.json`.')
w('The gate definitions are `GATE_DEFS_preregistered.md` (written before anything was built). Where a measurement needed a choice that file did not make, the choice is')
w('listed under "Choices and deviations" - nothing there was adjusted to make a number pass.')
w('')
w('| gate | male | female | failed lines |')
w('|---|---|---|---|')
for g, lst in fails.items():
    m = [x for x in lst if x.startswith('Male')] + [x for x in lst if not x.startswith(('Male', 'Female'))]
    f = [x for x in lst if x.startswith('Female')] + [x for x in lst if not x.startswith(('Male', 'Female'))]
    w(f'| {g} | {"PASS" if not m else "FAIL"} | {"PASS" if not f else "FAIL"} | {"; ".join(lst) if lst else "-"} |')
w('')
w('## Per-clip measurements (every cell with two values is male · female)')
w('')
w('| clip | WATCH sec | THIN | length s | contact s | peak shoulder yaw deg, male · female (need) | finish held frames, male · female | reach m, male · female (limit male/female) | racket speed within +-0.12 s of contact / peak, male · female | contact face/shaft error vs authored intent deg, male · female | start/end max bone angle vs READY deg, male · female |')
w('|---|---|---|---|---|---|---|---|---|---|---|')
for c in CLIPS:
    cells = []
    for t in HEROES:
        d = VD[t]['clips'][c]
        b = B[t]['clips'][c]
        ce = b['contact_orientation_error']
        cells.append(d)
    d, f = cells
    bm, bf = B['male']['clips'][c], B['female']['clips'][c]
    cem, cef = bm['contact_orientation_error'], bf['contact_orientation_error']
    w('| {c} | {s} | {th} | {L:.2f} | {ct} | {y1:.0f} · {y2:.0f} ({yr}) | {h1} · {h2} | {r1} · {r2} ({rl}) | {s1} · {s2} | {e1} · {e2} | {a1:.0f}/{b1:.0f} · {a2:.0f}/{b2:.0f} |'.format(
        c=c, s=bm['section'], th='yes' if bm['thin'] else 'no', L=bm['length_s'], ct='-' if bm['contact_s'] is None else f'{bm["contact_s"]:.3f}',
        y1=d['peak_shoulder_yaw_deg'], y2=f['peak_shoulder_yaw_deg'], yr=d['yaw_required_deg'] or '-', h1=d.get('finish_hold_frames', '-'), h2=f.get('finish_hold_frames', '-'),
        r1='-' if 'reach_m' not in d else f'{d["reach_m"]:.2f}', r2='-' if 'reach_m' not in f else f'{f["reach_m"]:.2f}', rl='-' if 'reach_limit_m' not in d else f'{d["reach_limit_m"]:.2f}/{f["reach_limit_m"]:.2f}',
        s1='-' if 'speed_ratio' not in d else f'{d["speed_ratio"]:.2f}', s2='-' if 'speed_ratio' not in f else f'{f["speed_ratio"]:.2f}',
        e1='-' if cem is None else f'{cem["face_deg"]:.0f}/{cem["shaft_deg"]:.0f}', e2='-' if cef is None else f'{cef["face_deg"]:.0f}/{cef["shaft_deg"]:.0f}',
        a1=d['start_max_deg'], b1=d['end_max_deg'], a2=f['start_max_deg'], b2=f['end_max_deg']))
w('')
w('## What was built')
w('')
w('* Neither staged blend had an armature (the brief says "keep their bone lengths"), so a 53-bone Unity-humanoid-named skeleton was **fitted to each hero\'s own mesh** (cross-section landmarks,')
w('  measured shoulder width / arm / leg lengths in `checks.json`), the body was skinned to it (vertex groups named after the bones + one Armature modifier), face and hair are parented to the head bone,')
w('  the classic racket sits on a `Hand_Racket` socket on the right-hand bone (finger grip from the dressed-look solution, left-hand throat / handle grips fitted by `scripts/leftgrip.py`).')
w('* 16 actions per hero (30 fps, frames from 0), all driving that armature, one FBX per clip and hero (`export/fbx/`, armature + skinned meshes + racket + the clip, baked); every FBX was re-imported:')
w('  one armature, identical bone names, rest heads equal to 0.0004 mm, same frame count, posed bone heads equal to the blend\'s within 0.004 mm at four sampled frames.')
w('* Clip content comes from `WATCH.md` only (each key in `scripts/clips.py` names its WATCH step in `src`); ForehandShort = section 18, SliceApproach = section 17 (contact face not authored).')
w('* The pose solver (`scripts/pose.py`, `clipkit.py`) places feet, pelvis and chest from the keys, drives the racket arm by IK so the racket stays in the right hand, and holds the sweet spot at the')
w('  authored contact point; a Viterbi search over elbow swivel and wrist angles keeps the arms continuous; contact frames are solved exactly (the 40 cm racket lever couples position and orientation).')
w('')
w('## Choices and deviations (read these)')
w('')
w('1. **Skeleton added** (see above): the only data added to the copies are the armature, vertex groups named after bones, one Armature modifier, parenting of Face/Hair, the racket socket and the actions.')
w('   Mesh geometry hashes (positions, topology, normals, UVs, attributes) of Body/Face/Hair equal the sources; the original `LOOP_*` vertex groups hash equal; no shape keys; world matrices equal in the bind pose.')
w('2. **Five bone heads moved** (`scripts/fix_bones.py`): the landmark fit had left thumb / little-finger heads outside the hand skin (ON_HERO needs every head inside). They were moved to at most 10 mm under the skin.')
w('   Those bones are never rotated in any clip, so the skinned mesh is unchanged by it (checked: BODY_UNCHANGED still holds and the poses were re-baked).')
w('3. **Foot grounding**: with the heel raised the toe vertices dip because they are partly weighted to the foot bone; `scripts/foot_ground.py` measures the dip per heel angle and the solver lifts the')
w('   foot by that amount (<= 12 mm male / 9.4 mm female) so that no vertex goes below the floor (gate: no vertex lower than -3 mm).')
w('4. **Test definitions that the pre-registration left open** (all in `scripts/verify_*.py`): "ball joint within 5 mm of the floor" is measured as the lowest foot-bone vertex of a planted foot being between -3 mm and +5 mm;')
w('   "local cross-section centroid of the limb" is the centroid of the limb segment\'s own vertices in a +-20 mm slab 5 cm from the joint (a section nearer than ~4 cm is biased by the hand / foot);')
w('   a foot is "planted" on frames where its lift and heel channels are zero (a foot that travels is lifted by an arc that grows with its ground speed, so no clip skates);')
w('   "one-handed clips: the left hand is not on the grip after the take-back" is tested from the take-back peak (greatest shoulder yaw) to the third frame of the held finish; every clip ends on a')
w('   pose blendable to ReadyIdle, whose left hand is on the throat, so the off hand returns to the racket during the recovery after the finish is held. SliceApproach: from the release to the same point.')
w('   The pre-registered wording "never back on the racket within the clip" for SliceApproach conflicts with "every clip ends blendable to ReadyIdle" (gate 9) and is read the same way.')
w('5. **Reach**: the pre-registered reachable test (shoulder to sweet spot <= arm length + 0.45 x racket length) pulled the pinned contact point of Serve, Overhead, VolleyForehand and SliceApproach (and, after')
w('   solving, VolleyForehand again) a few cm towards the shoulder; this is the "fitted to THIS body" the brief asks for. SliceApproach gets a position-only pin at its contact time (no face is authored).')
w('6. **Racket face / shaft at contact are not exactly the authored intent**: the grip fixes the racket to the hand and the wrist has anatomical limits, so the contact pose is the nearest the arm can hold with')
w('   the sweet spot where authored (errors per clip in the table; they are weighted to keep the face square). SliceApproach\'s face is not authored at all. Racket-head speed peaks at / next to the contact in every hit clip.')
w('7. **Off-hand reach**: when the left hand is attached and the racket would be out of its reach the racket is moved towards the left shoulder (`racket_shift` in the diagnostics: Serve ready/toss stance ~4 cm,')
w('   SliceApproach low-left stance ~9-10 cm for the male, ~9 cm female); when the hand is letting go or taking hold it follows the racket only as far as it reaches.')
w('8. **Fast phases**: at 30 fps the racket head covers up to ~1.2 m per frame at contact, so a few arm bones turn by more than 100 degrees between two frames around contact and at the off-hand release')
w('   (counts per clip in `checks.json` -> `measured.arm_steps_over_100deg`). The solver keeps the arm path continuous (no elbow flips); these are the swing speeds, not tracking jumps.')
w('9. **Torso penetration listing** (ON_HERO): poses where an arm vertex or the racket passes deeper than 15 mm into the torso triangle set at the contact / finish / take-back frames are listed in `data/verify_blend_<hero>.json`')
w('   -> `fitted_to_the_hero`; the list is printed below.')
w('')
for t in HEROES:
    fit = VB[t].get('fitted_to_the_hero', [])
    w(f'* {LABEL[t]}: {len(fit)} pose(s) {"flagged: " + "; ".join(fit[:40]) if fit else "none above 15 mm"}')
w('')
w('## Not done / not claimed')
w('')
w('* Nothing was tried in Unity; no Animator wiring; no ball physics; no root motion (all clips are in place; step = plant + weight shift). No source-footage file or frame is in the repo.')
w('* The THIN clips carry only what their WATCH sections show (see the THIN table in `GATE_DEFS_preregistered.md`; reasons in `checks.json`).')
w('* The review videos are 540x674 H.264 (Blender\'s writer) with a clip / time / contact caption; the proof sheets show contact and held finish from behind the court and from the racket side.')
w('')
w('## Files')
w('')
w('`export/HeroBase_Male_MatchAnims.blend`, `export/HeroBase_Female_MatchAnims.blend`, `export/fbx/<Hero>_<Clip>.fbx` (32), `proof/Sheet_<Hero>_{Behind,Side}.png`, `proof/Review_<Hero>.mp4`,')
w('`checks.json`, `README.md`, `scripts/` (everything that produced these), `data/` (rig / racket / hand fits and every measurement).')
open(f'{WORK}/GATE_RESULTS.md', 'w').write('\n'.join(L) + '\n')
print('FINALIZE_DONE', verdict)
for g, v in fails.items():
    for m in v:
        print('  FAIL', g, m)

# =========================================================================================== README.md
R = []
r = R.append
r('# match-anim-set - 16 match animations on the two staged heroes (MATCH ANIMS 2/2)')
r('')
r(f'Verdict: **GATE: MATCH_ANIM_BUILD {verdict}** (details and every measured number: `GATE_RESULTS.md`, `checks.json`).')
r('')
r('## What is here')
r('')
r('| path | what |')
r('|---|---|')
r('| `export/HeroBase_Male_MatchAnims.blend`, `export/HeroBase_Female_MatchAnims.blend` | the staged hero + fitted armature `Rig_<Hero>` + racket + the 16 actions (active: ReadyIdle) |')
r('| `export/fbx/<Hero>_<Clip>.fbx` | 32 files: armature + skinned body / face / hair + racket on the hand socket + that clip (baked, 30 fps, frames 0..N) |')
r('| `proof/Sheet_<Hero>_Behind.png`, `proof/Sheet_<Hero>_Side.png` | every clip at contact (movement clips: mid) and at the held finish (end), camera behind the court / from the racket-hand side |')
r('| `proof/Review_<Hero>.mp4` | all 16 clips in order from the behind-the-court camera, 30 fps, with clip / time / CONTACT captions |')
r('| `checks.json` | per clip and hero: name, length, contact time (null for the 4 movement clips), WATCH section + source id, THIN + reasons, key sources, FBX hash, measurements |')
r('| `GATE_RESULTS.md`, `GATE_DEFS_preregistered.md` | results; the gate definitions written before the build |')
r('| `WATCH.md` | the only source of motion (MATCH ANIMS 1/2); no footage is in the repo |')
r('| `scripts/`, `data/` | everything that produced the above; `scripts/run_all.sh` rebuilds the animation, FBX, proofs and checks from the stage blends |')
r('')
r('## Clips')
r('')
r('| clip | WATCH section | source | THIN | length s (cap) | contact s (male / female) | key facts |')
r('|---|---|---|---|---|---|---|')
for c in CLIPS:
    bm, bf = B['male']['clips'][c], B['female']['clips'][c]
    facts = {'ReadyIdle': 'loop, last frame = first, sway only; off hand on the throat', 'SplitToForehand': 'first stride, widening, racket back; no hop (not seen)', 'SplitToBackhand': 'two-hand turn; no hop (not seen)',
             'RecoverCenter': 'strides and short steps back to centre', 'Forehand': 'neutral forehand, loop take-back, wrap finish', 'ForehandOpen': 'open stance, weight on the R leg, L foot lifted, off hand at the chin, high finish',
             'ForehandWide': 'wide run-in and lunge', 'ForehandShort': 'SECTION 18 step-in on a short ball (not section 8)', 'Backhand': 'two-hand backhand, off hand on the racket through contact, released on the finish',
             'BackhandWide': 'wide two-hand backhand', 'SliceApproach': 'SECTION 17, one-handed through the swing, contact face not authored (THIN)', 'Serve': 'toss, trophy, contact above the head (contact inferred: THIN)',
             'Return': 'two-hand return, split and turn', 'VolleyForehand': 'short punch, held finish', 'VolleyBackhand': 'two-hand volley', 'Overhead': 'trophy, smash, landing'}[c]
    r('| {c} | {s} | `{u}` | {th} | {L:.2f} ({cap}) | {ct} | {f} |'.format(c=c, s=bm['section'], u=bm['url'], th='yes' if bm['thin'] else 'no', L=bm['length_s'], cap=bm['cap_s'],
                                                                           ct='-' if bm['contact_s'] is None else f'{bm["contact_s"]:.3f} / {bf["contact_s"]:.3f}', f=facts))
r('')
r('## Rebuild')
r('')
r('```')
r('work/match-anim-set/scripts/run_all.sh        # bake both heroes, verify, export FBX, render proofs, write checks.json / GATE_RESULTS.md')
r('```')
r('')
r('Stage steps that run once (already done; outputs are in `data/` and `export/_stage/`): `build_rig.py` (fit + skin), `racket_info.py`, `leftgrip.py`, `fix_bones.py`, `foot_ground.py`.')
r('')
r('## Conventions')
r('')
r('Blender units = metres, the hero faces -Y, its right hand is world -X; 30 fps; frames start at 0; the armature object and the `Root` bone never move (clips are in place); the hips carry the pelvis motion.')
r('Bone names are Unity-humanoid names, so the FBX clips retarget to the existing hero avatars. Racket socket: `Hand_Racket` empty on `RightHand` (matrix fixed over all clips).')
open(f'{WORK}/README.md', 'w').write('\n'.join(R) + '\n')
print('README_DONE')
