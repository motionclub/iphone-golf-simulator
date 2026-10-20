# match-anim-set - 16 match animations on the two staged heroes (MATCH ANIMS 2/2)

Verdict: **GATE: MATCH_ANIM_BUILD FAIL** (details and every measured number: `GATE_RESULTS.md`, `checks.json`).

## What is here

| path | what |
|---|---|
| `export/HeroBase_Male_MatchAnims.blend`, `export/HeroBase_Female_MatchAnims.blend` | the staged hero + fitted armature `Rig_<Hero>` + racket + the 16 actions (active: ReadyIdle) |
| `export/fbx/<Hero>_<Clip>.fbx` | 32 files: armature + skinned body / face / hair + racket on the hand socket + that clip (baked, 30 fps, frames 0..N) |
| `proof/Sheet_<Hero>_Behind.png`, `proof/Sheet_<Hero>_Side.png` | every clip at contact (movement clips: mid) and at the held finish (end), camera behind the court / from the racket-hand side |
| `proof/Review_<Hero>.mp4` | all 16 clips in order from the behind-the-court camera, 30 fps, with clip / time / CONTACT captions |
| `checks.json` | per clip and hero: name, length, contact time (null for the 4 movement clips), WATCH section + source id, THIN + reasons, key sources, FBX hash, measurements |
| `GATE_RESULTS.md`, `GATE_DEFS_preregistered.md` | results; the gate definitions written before the build |
| `WATCH.md` | the only source of motion (MATCH ANIMS 1/2); no footage is in the repo |
| `scripts/`, `data/` | everything that produced the above; `scripts/run_all.sh` rebuilds the animation, FBX, proofs and checks from the stage blends |

## Clips

| clip | WATCH section | source | THIN | length s (cap) | contact s (male / female) | key facts |
|---|---|---|---|---|---|---|
| ReadyIdle | 1 | `HI0bvG0pw4w t=21.5-22.9` | no | 2.20 (2.4) | - | loop, last frame = first, sway only; off hand on the throat |
| SplitToForehand | 2 | `DGIkkdxMrWc t=1015.90-1016.40` | no | 0.60 (0.6) | - | first stride, widening, racket back; no hop (not seen) |
| SplitToBackhand | 3 | `DGIkkdxMrWc t=10.19-12.16` | no | 0.60 (0.6) | - | two-hand turn; no hop (not seen) |
| RecoverCenter | 4 | `HI0bvG0pw4w t=150.0-156.5` | no | 0.80 (0.8) | - | strides and short steps back to centre |
| Forehand | 5 | `DGIkkdxMrWc t=7.60-9.90` | no | 1.20 (1.2) | 0.667 / 0.667 | neutral forehand, loop take-back, wrap finish |
| ForehandOpen | 6 | `yAM1j_B6yQs t=0.00-1.37` | yes | 1.00 (1.0) | 0.533 / 0.533 | open stance, weight on the R leg, L foot lifted, off hand at the chin, high finish |
| ForehandWide | 7 | `HI0bvG0pw4w t=145.5-150.0` | yes | 1.30 (1.3) | 0.867 / 0.867 | wide run-in and lunge |
| ForehandShort | 18 | `WBfw9nFojHc t=64.50-68.00` | yes | 1.00 (1.0) | 0.467 / 0.467 | SECTION 18 step-in on a short ball (not section 8) |
| Backhand | 9 | `-Eu80hGbgVA t=164.0-176.0` | no | 1.20 (1.2) | 0.633 / 0.633 | two-hand backhand, off hand on the racket through contact, released on the finish |
| BackhandWide | 10 | `0a_DL1I4q38 t=17.40-22.10` | no | 1.30 (1.3) | 0.767 / 0.767 | wide two-hand backhand |
| SliceApproach | 17 | `ebS3Lf25hZ0 t=3.40-18.70` | yes | 1.20 (1.2) | 0.500 / 0.500 | SECTION 17, one-handed through the swing, contact face not authored (THIN) |
| Serve | 12 | `rxo1uEdLouY t=178.0-181.2` | yes | 1.60 (1.6) | 0.900 / 0.900 | toss, trophy, contact above the head (contact inferred: THIN) |
| Return | 13 | `DGIkkdxMrWc t=635.48-637.98` | yes | 0.90 (0.9) | 0.433 / 0.433 | two-hand return, split and turn |
| VolleyForehand | 14 | `DGIkkdxMrWc t=835.28-839.09` | yes | 0.70 (0.7) | 0.300 / 0.300 | short punch, held finish |
| VolleyBackhand | 15 | `DGIkkdxMrWc t=865.30-866.60` | yes | 0.70 (0.7) | 0.300 / 0.300 | two-hand volley |
| Overhead | 16 | `bvVXmtHt0DM t=447.60-449.90` | yes | 1.20 (1.2) | 0.733 / 0.733 | trophy, smash, landing |

## Rebuild

```
work/match-anim-set/scripts/run_all.sh        # bake both heroes, verify, export FBX, render proofs, write checks.json / GATE_RESULTS.md
```

Stage steps that run once (already done; outputs are in `data/` and `export/_stage/`): `build_rig.py` (fit + skin), `racket_info.py`, `leftgrip.py`, `fix_bones.py`, `foot_ground.py`.

## Conventions

Blender units = metres, the hero faces -Y, its right hand is world -X; 30 fps; frames start at 0; the armature object and the `Root` bone never move (clips are in place); the hips carry the pelvis motion.
Bone names are Unity-humanoid names, so the FBX clips retarget to the existing hero avatars. Racket socket: `Hand_Racket` empty on `RightHand` (matrix fixed over all clips).
