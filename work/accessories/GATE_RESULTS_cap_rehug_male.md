# GATE RESULTS: male cap re-hug to the 10-17 head (2026-10-18)

Male `tennis_cap` and `golf_cap` re-hugged to the male head chat 11 installed on 10-17 (`work/male-face-body`, `HeroFaceReferenceFit` male constants).
On that head the skull is narrower at the temples, so the cap band stood 5–11 mm off the temples and sides.
The socket fit is unchanged: same scale, pitch, anchor, socket pose and bill height. Only the hug and relieve passes were re-run on the new head.

**Result: PASS on all 10 lines.** Gate 10 was re-run on 2026-10-18, once the male prefab patch was in and the garments draw.

## How it was made
1. **Head dump** from my clone `~/cap-rehug-UnityClone` (APFS copy of the working tree, 10-17 23:00).
   - Command: `ClothingV2Dump` with `CV2_HEROES=MatchHero_Male`, `CV2_FPS=1`.
   - Output: `work/accessories/dump_1017/MatchHero_Male`. The body has 44,168 vertices, the new head, with `HeroOriginalSeam installed Male` in the log.
2. **Re-hug:** `ACC_DUMP=work/accessories/dump_1017 blender -b --factory-startup --python py/cap_export.py -- <tennis|golf> Male --keep-fit`.
   - `--keep-fit` is new. It reuses `fit_report.params` from the piece.json already in `out/`, then runs hug ×3 and relieve on the new head.
   - `acc_common.py` gained the `ACC_DUMP` override.
3. **Install:** `prep_install.py`, then `unity_iter.sh install` in the clone (`ACC_CLONE=~/cap-rehug-UnityClone`).
   - Only the 4 male cap files differ from the repo (2 × `Kit_Cap.asset`, 2 × `_M.png`; AO re-baked). These were copied back and staged.
   - Female, glove and bag files are byte-identical and were not copied. `item.json` is unchanged because the socket is the same.
4. **Measurements:** `py/rehug_measure.py` (Blender, signed clearance to the dumped head).
   - `scratch/measure_before_newhead.json` (old caps on the new head)
   - `scratch/measure_after.json`
   - Scripts: `scratch/rehug_before.sh`, `rehug_blender.sh`, `rehug_unity.sh`, `rehug_unity2.sh` (all launched through heavy.sh, `GOLF_MUTE=1`).

## Gates
| # | Gate | Threshold | Before (old cap, new head) | After | Result |
|---|---|---|---|---|---|
| 1 | HEAD_UNTOUCHED | No head/body/face/rig file changed. Only `Resources/Accessories/Male/{tennis,golf}_cap` | – | git: 4 cap files staged, nothing else | **PASS** |
| 2 | MIN_CLEARANCE (lining to skin, rest) | ≥ 1.6 mm | −1.74 mm (40 lining verts inside the forehead) | 1.62 mm, 0 inside (both caps) | **PASS** |
| 3 | LINING_GAP | mean ≈ 2–3 mm | mean 5.27, p95 10.88 mm | mean 3.06, p95 5.31 mm. Band mean front 2.12 / temple 1.87 / side 2.09 / back 1.95 mm | **PASS** |
| 4 | TEMPLE_STANDOFF (band, 35–75° from the front) | mean ≤ 3 mm | mean 5.53, max 7.92 mm (side 9.92 / back 7.58 mean) | mean 1.87, max 2.10 mm | **PASS** |
| 5 | BILL_ON_BROW (sheet 08 relation kept) | front rim z and brim front edge (z, y) Δ ≤ 1 mm | front rim z 1.6361 m, brim front lowest z 1.6223, tip y −0.2255 | identical (Δ 0.0 mm). Brim moves only at its root (mean 0.94 mm, front ±3 cm max 3.6 mm, side root max 6.4 mm, following the band in) | **PASS** |
| 6 | BAND_WIDTH (reads narrower at the temples) | narrower | 187.0 mm | 169.3 mm (−17.7 mm, ≈ 8.9 mm/side) | **PASS** |
| 7 | CLIP: cap inside body (AccessoriesClipCheck, Unity skinning, 10 Hz, both male heroes, 57 clips) | ≤ 0.5 mm, except the known hands-on-head clips | 87–3304 verts, 1.3–2.2 mm in every clip; 15–16 mm in Shock/MissWhiff | 0 in 51 clips. 124 verts / 0.2 mm in Defeat/Slump/SadPointLost/MatchLose. Hands-on-head exceptions: Emote_Shock/MissWhiff 10.9 mm (tennis), 6.7 mm (golf), down from 15.3/16.0 (10-13: 10.3 mm) | **PASS** |
| 8 | CLIP: skin inside cap (no regression) | after ≤ before in every clip | 1,934–12,709 verts per clip | Lower in all 57 clips (e.g. Idle 11,362 → 2, Thrust 10,004 → 1,458) | **PASS** (see note) |
| 9 | PROOF renders, rest pose + 4 posed golf frames, Unity game shaders | present | `proof/rehug_male_1017/before/` | `after/`, `after_poses/`, sheets | **PASS** |
| 10 | CLIP: garment inside cap (Kit_Top/Kit_Bottom vs Acc_Cap, both male heroes, 57 clips) | 0 | (10-17 clone: garments did not draw, counts noisy) | **0 in all 57 clips** (re-run 10-18 on the re-synced clone with the male prefab patch: `clipcheck/rehug_male_1018_garments/`). Acc-in-body and skin-in-cap match the 10-17 after run exactly. Posed golf renders with garments: `proof/rehug_male_1018/` | **PASS** |

**Note on gate 8.** `CapRegionProbe`, a clone-only tool, sorts the remaining "skin in cap" vertices by their dominant bone.
- They are all head/neck vertices, except the hands in Shock/MissWhiff/Scuba (golf).
- Each sits about 20 mm from the cap surface, which is the search radius, so they are not real poke-through. Real poke-through would read a few mm.
- They appear only in clips where the head tips far forward or back (Thrust, Victory, swings, Shock). There, the checker's world-up ray parity test misreads the open cap shell.
- The posed renders (`after_poses/`: Putt 0.3, FistPump 0.4, Spike 3.1, Thrust 1.0) show no skin through the cap.
- Idle has 2 vertices at 3–5 mm (brow under the bill).

## Proof
- `proof/rehug_male_1017/sheet_MatchHero_Male_before_after.png`, `sheet_GolfKitHero_Male_before_after.png`: sheet 08 on top, then before and after rows at 0 / 45 / 90 / 180 / 315 / 270.
- `proof/rehug_male_1017/temple_front_closeup.png`: front crops of both heroes, before and after, next to sheet 08's front view.
- `clipcheck/rehug_male_1017_before/`, `clipcheck/rehug_male_1017_after/` (clipcheck.csv/txt, cap_region_probe.csv).

## Round 2 (2026-10-18)
The clone was re-synced to the working tree with the male prefab patch, and the clip check and proofs were re-run with the re-hugged caps (`scratch/rehug_unity3.sh`).
Garments now draw and nothing of the polo or trousers enters either cap, so no fix was needed.
Sheet: `proof/rehug_male_1018/sheet_caps_with_garments_1018.png` (sheet 08, tennis and golf rest views, 4 posed golf frames).

## Not done / for others
- **Lobby:** `.ktx` maps and the lobby export of the two male caps are stale. This is chat 6's job; see REQUESTS.md.
- **Clone-only changes:** `HeroClearanceTests.cs` (another chat's new EditMode test) does not compile in a fresh copy of the tree, because `AnimationMixerPlayable.SetInputWeight` etc. need `using UnityEngine.Playables` or a missing assembly reference. I deleted it in my clone only; the repo file is untouched.
- **Rollback:** `git checkout HEAD -- Unity/Assets/Resources/Accessories/Male/{tennis,golf}_cap`. The old `out/` pieces are kept in `scratch/before_1017/`.
