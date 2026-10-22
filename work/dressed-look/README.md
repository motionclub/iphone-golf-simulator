# DRESSED LOOK - standard tennis kit + classic racket on the full male and female bodies

Look only: nothing resculpted, nothing refit, no shrinkwrap. Clip / float is measured and captioned, never fixed.
Verdict and evidence: `GATE_RESULTS.md` (written from `checks.json`); gate definitions written before the work: `GATE_DEFS_preregistered.md`.

## Deliverables
| path | what |
|---|---|
| `export/HeroBase_Male_Dressed.blend` | male body (`work/male-pelvis-form3/export/merged_fd04bc28.blend`, SHA d6c4dcfb...) + kit (white + black) + racket + right-hand rig |
| `export/HeroBase_Female_Dressed.blend` | female body (`work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend`, SHA a1d73a33...) + the same |
| `proof/Sheet_{Male,Female}_{White,Black}.png` | four sheets: front, 3/4, side, back, waist front/back, racket hand x2, CLIP / FLOAT captions |
| `proof/Turntable_{Male,Female}_White.mp4` | 10 s, 240 frames, 1080x1350, white kit, camera behind the court, racket reads |
| `proof/raw/` | the 32 sheet cells + decoded video frames |
| `data/` | SHA / ArtDir snapshots, per-hero build / verify / fit JSON, labels |

## Structure of a dressed blend
* `Rig_Hand_R` (armature, identity transform, root): palm bone `Hand_R` + `<Digit>_1..3` for Index / Middle / Ring / Pinky / Thumb. Body and Face (and Hair_F) are children; the Body carries the Armature modifier and the 16 finger vertex groups.
* sockets (empties, children of the body): `Chest_Top`, `Hip_Bottom`, `Foot_L_Shoe`, `Foot_R_Shoe` at the kit's own transforms.
* collections `Kit_White` (visible) and `Kit_Black` (hidden): `Kit_Top_Polo_*`, `Kit_Bottom_Shorts_M` / `Kit_Bottom_Skort_F`, `Kit_Sock_L/R`, `Kit_Shoe_L/R` (suffix `_White` / `_Black`), each parented to its socket, authored world transform untouched.
* `Hand_Racket` (empty, parented to bone `Hand_R`) > `Racket_Classic` > `StringBed`, `Grip`, `ButtCap`, `Collider_Racket` (hidden in renders).
* actions `Pose_GripClosed` (active) and `Pose_Rest`. To see the bind hand: pick `Pose_Rest` on the rig.

## Rebuild
`scripts/run_all.sh` (headless Blender 5.2; numpy only inside Blender's python, Pillow in the system python). Single steps: `build_dressed.py -- male|female`, `verify_dressed.py`, `measure_fit.py`, `render_dressed.py`, `render_turntable.py`, `compose_sheets.py`, `check_video.py`, `final_report.py`.
Code map: `dl_common.py` paths / hashes - `handlib.py`, `handmodel.py` hand segmentation, digit centre lines, skin weights from the mesh - `handpose_np.py` numpy twin of the armature + racket model - `handrig.py` rig, grip search, actions - `studio.py` kit studio look.
