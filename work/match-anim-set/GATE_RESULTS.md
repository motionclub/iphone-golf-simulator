# MATCH_ANIM_BUILD - gate results (2026-10-03 11:47:38)

**GATE: MATCH_ANIM_BUILD FAIL**

Everything below is measured by the scripts in `scripts/` on the files in this folder; the numbers are in `checks.json` and `data/verify_*.json`.
The gate definitions are `GATE_DEFS_preregistered.md` (written before anything was built). Where a measurement needed a choice that file did not make, the choice is
listed under "Choices and deviations" - nothing there was adjusted to make a number pass.

| gate | male | female | failed lines |
|---|---|---|---|
| FROM_WATCH | PASS | PASS | - |
| SHORT_IS_18 | PASS | PASS | - |
| SLICE_IS_17 | PASS | PASS | - |
| ALL_CLIPS | PASS | PASS | - |
| CONTACT_NAMED | PASS | PASS | - |
| IN_PLACE | PASS | PASS | - |
| RACKET_HELD | PASS | PASS | - |
| READS_FROM_BEHIND | PASS | PASS | - |
| READY_LOOP | PASS | PASS | - |
| BODY_UNCHANGED | PASS | PASS | - |
| ON_HERO | PASS | PASS | - |
| NO_FOOTAGE_IN_REPO | FAIL | FAIL | ArtDir differs from the baseline: +1 -0 ~0 (base_lock hash changes: 1) - see data/verify_repo.json; none of the match-anim-set scripts opens an ArtDir path (checked below) |

## Per-clip measurements (every cell with two values is male · female)

| clip | WATCH sec | THIN | length s | contact s | peak shoulder yaw deg, male · female (need) | finish held frames, male · female | reach m, male · female (limit male/female) | racket speed within +-0.12 s of contact / peak, male · female | contact face/shaft error vs authored intent deg, male · female | start/end max bone angle vs READY deg, male · female |
|---|---|---|---|---|---|---|---|---|---|---|
| ReadyIdle | 1 | no | 2.20 | - | 0 · 0 (-) | - · - | - · - (-) | - · - | - · - | 0/0 · 0/0 |
| SplitToForehand | 2 | no | 0.60 | - | 85 · 86 (-) | - · - | - · - (-) | - · - | - · - | 3/1 · 3/2 |
| SplitToBackhand | 3 | no | 0.60 | - | 95 · 95 (-) | - · - | - · - (-) | - · - | - · - | 5/1 · 5/1 |
| RecoverCenter | 4 | no | 0.80 | - | 14 · 14 (-) | - · - | - · - (-) | - · - | - · - | 3/2 · 3/2 |
| Forehand | 5 | no | 1.20 | 0.667 | 111 · 110 (60) | 3 · 4 | 0.69 · 0.73 (0.81/0.77) | 1.00 · 1.00 | 17/15 · 17/19 | 3/0 · 3/2 |
| ForehandOpen | 6 | yes | 1.00 | 0.533 | 108 · 109 (40) | 4 · 4 | 0.59 · 0.60 (0.81/0.77) | 1.00 · 1.00 | 26/25 · 33/31 | 6/4 · 6/4 |
| ForehandWide | 7 | yes | 1.30 | 0.867 | 99 · 100 (60) | 3 · 4 | 0.58 · 0.62 (0.81/0.77) | 1.00 · 1.00 | 15/20 · 4/3 | 9/12 · 9/12 |
| ForehandShort | 18 | yes | 1.00 | 0.467 | 56 · 56 (40) | 3 · 3 | 0.48 · 0.45 (0.81/0.77) | 1.00 · 1.00 | 31/26 · 29/15 | 8/0 · 8/1 |
| Backhand | 9 | no | 1.20 | 0.633 | 82 · 82 (60) | 4 · 4 | 0.71 · 0.68 (0.81/0.77) | 1.00 · 1.00 | 10/56 · 10/51 | 1/8 · 1/7 |
| BackhandWide | 10 | no | 1.30 | 0.767 | 96 · 95 (60) | 6 · 13 | 0.77 · 0.76 (0.81/0.77) | 1.00 · 1.00 | 21/28 · 25/32 | 4/8 · 4/7 |
| SliceApproach | 17 | yes | 1.20 | 0.500 | 69 · 69 (60) | 9 · 9 | 0.77 · 0.74 (0.81/0.77) | 1.00 · 1.00 | 32/44 · 52/26 | 1/8 · 1/7 |
| Serve | 12 | yes | 1.60 | 0.900 | 140 · 140 (70) | 4 · 4 | 0.78 · 0.73 (0.81/0.77) | 1.00 · 1.00 | 5/28 · 6/29 | 5/2 · 5/2 |
| Return | 13 | yes | 0.90 | 0.433 | 72 · 71 (60) | 7 · 4 | 0.70 · 0.65 (0.81/0.77) | 1.00 · 1.00 | 10/51 · 9/53 | 17/11 · 17/11 |
| VolleyForehand | 14 | yes | 0.70 | 0.300 | 79 · 78 (20) | 3 · 3 | 0.77 · 0.73 (0.81/0.77) | 1.00 · 1.00 | 17/18 · 22/21 | 1/3 · 1/3 |
| VolleyBackhand | 15 | yes | 0.70 | 0.300 | 34 · 33 (20) | 3 · 10 | 0.60 · 0.58 (0.81/0.77) | 1.00 · 1.00 | 18/35 · 21/34 | 1/3 · 1/3 |
| Overhead | 16 | yes | 1.20 | 0.733 | 128 · 128 (70) | 3 · 8 | 0.78 · 0.73 (0.81/0.77) | 1.00 · 1.00 | 5/29 · 6/30 | 1/1 · 1/1 |

## What was built

* Neither staged blend had an armature (the brief says "keep their bone lengths"), so a 53-bone Unity-humanoid-named skeleton was **fitted to each hero's own mesh** (cross-section landmarks,
  measured shoulder width / arm / leg lengths in `checks.json`), the body was skinned to it (vertex groups named after the bones + one Armature modifier), face and hair are parented to the head bone,
  the classic racket sits on a `Hand_Racket` socket on the right-hand bone (finger grip from the dressed-look solution, left-hand throat / handle grips fitted by `scripts/leftgrip.py`).
* 16 actions per hero (30 fps, frames from 0), all driving that armature, one FBX per clip and hero (`export/fbx/`, armature + skinned meshes + racket + the clip, baked); every FBX was re-imported:
  one armature, identical bone names, rest heads equal to 0.0004 mm, same frame count, posed bone heads equal to the blend's within 0.004 mm at four sampled frames.
* Clip content comes from `WATCH.md` only (each key in `scripts/clips.py` names its WATCH step in `src`); ForehandShort = section 18, SliceApproach = section 17 (contact face not authored).
* The pose solver (`scripts/pose.py`, `clipkit.py`) places feet, pelvis and chest from the keys, drives the racket arm by IK so the racket stays in the right hand, and holds the sweet spot at the
  authored contact point; a Viterbi search over elbow swivel and wrist angles keeps the arms continuous; contact frames are solved exactly (the 40 cm racket lever couples position and orientation).

## Choices and deviations (read these)

1. **Skeleton added** (see above): the only data added to the copies are the armature, vertex groups named after bones, one Armature modifier, parenting of Face/Hair, the racket socket and the actions.
   Mesh geometry hashes (positions, topology, normals, UVs, attributes) of Body/Face/Hair equal the sources; the original `LOOP_*` vertex groups hash equal; no shape keys; world matrices equal in the bind pose.
2. **Five bone heads moved** (`scripts/fix_bones.py`): the landmark fit had left thumb / little-finger heads outside the hand skin (ON_HERO needs every head inside). They were moved to at most 10 mm under the skin.
   Those bones are never rotated in any clip, so the skinned mesh is unchanged by it (checked: BODY_UNCHANGED still holds and the poses were re-baked).
3. **Foot grounding**: with the heel raised the toe vertices dip because they are partly weighted to the foot bone; `scripts/foot_ground.py` measures the dip per heel angle and the solver lifts the
   foot by that amount (<= 12 mm male / 9.4 mm female) so that no vertex goes below the floor (gate: no vertex lower than -3 mm).
4. **Test definitions that the pre-registration left open** (all in `scripts/verify_*.py`): "ball joint within 5 mm of the floor" is measured as the lowest foot-bone vertex of a planted foot being between -3 mm and +5 mm;
   "local cross-section centroid of the limb" is the centroid of the limb segment's own vertices in a +-20 mm slab 5 cm from the joint (a section nearer than ~4 cm is biased by the hand / foot);
   a foot is "planted" on frames where its lift and heel channels are zero (a foot that travels is lifted by an arc that grows with its ground speed, so no clip skates);
   "one-handed clips: the left hand is not on the grip after the take-back" is tested from the take-back peak (greatest shoulder yaw) to the third frame of the held finish; every clip ends on a
   pose blendable to ReadyIdle, whose left hand is on the throat, so the off hand returns to the racket during the recovery after the finish is held. SliceApproach: from the release to the same point.
   The pre-registered wording "never back on the racket within the clip" for SliceApproach conflicts with "every clip ends blendable to ReadyIdle" (gate 9) and is read the same way.
5. **Reach**: the pre-registered reachable test (shoulder to sweet spot <= arm length + 0.45 x racket length) pulled the pinned contact point of Serve, Overhead, VolleyForehand and SliceApproach (and, after
   solving, VolleyForehand again) a few cm towards the shoulder; this is the "fitted to THIS body" the brief asks for. SliceApproach gets a position-only pin at its contact time (no face is authored).
6. **Racket face / shaft at contact are not exactly the authored intent**: the grip fixes the racket to the hand and the wrist has anatomical limits, so the contact pose is the nearest the arm can hold with
   the sweet spot where authored (errors per clip in the table; they are weighted to keep the face square). SliceApproach's face is not authored at all. Racket-head speed peaks at / next to the contact in every hit clip.
7. **Off-hand reach**: when the left hand is attached and the racket would be out of its reach the racket is moved towards the left shoulder (`racket_shift` in the diagnostics: Serve ready/toss stance ~4 cm,
   SliceApproach low-left stance ~9-10 cm for the male, ~9 cm female); when the hand is letting go or taking hold it follows the racket only as far as it reaches.
8. **Fast phases**: at 30 fps the racket head covers up to ~1.2 m per frame at contact, so a few arm bones turn by more than 100 degrees between two frames around contact and at the off-hand release
   (counts per clip in `checks.json` -> `measured.arm_steps_over_100deg`). The solver keeps the arm path continuous (no elbow flips); these are the swing speeds, not tracking jumps.
9. **Torso penetration listing** (ON_HERO): poses where an arm vertex or the racket passes deeper than 15 mm into the torso triangle set at the contact / finish / take-back frames are listed in `data/verify_blend_<hero>.json`
   -> `fitted_to_the_hero`; the list is printed below.

* Male: 3 pose(s) flagged: ForehandOpen@contact: arm 18 mm, racket 0 mm; Return@peak_turn: arm 17 mm, racket 0 mm; Return@contact: arm 17 mm, racket 0 mm
* Female: 5 pose(s) flagged: ForehandWide@contact: arm 17 mm, racket 0 mm; ForehandShort@contact: arm 16 mm, racket 0 mm; SliceApproach@peak_turn: arm 21 mm, racket 0 mm; Return@finish: arm 19 mm, racket 0 mm; VolleyBackhand@contact: arm 16 mm, racket 0 mm

## Not done / not claimed

* Nothing was tried in Unity; no Animator wiring; no ball physics; no root motion (all clips are in place; step = plant + weight shift). No source-footage file or frame is in the repo.
* The THIN clips carry only what their WATCH sections show (see the THIN table in `GATE_DEFS_preregistered.md`; reasons in `checks.json`).
* The review videos are 540x674 H.264 (Blender's writer) with a clip / time / contact caption; the proof sheets show contact and held finish from behind the court and from the racket side.

## Files

`export/HeroBase_Male_MatchAnims.blend`, `export/HeroBase_Female_MatchAnims.blend`, `export/fbx/<Hero>_<Clip>.fbx` (32), `proof/Sheet_<Hero>_{Behind,Side}.png`, `proof/Review_<Hero>.mp4`,
`checks.json`, `README.md`, `scripts/` (everything that produced these), `data/` (rig / racket / hand fits and every measurement).
