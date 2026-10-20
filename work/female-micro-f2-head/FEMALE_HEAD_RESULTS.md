# FEMALE_HEAD_RESULTS — MicroF2 (round lower face + plate jaw)

**GATE: FEMALE_HEAD_MicroF2 PASS** — every measured gate passes. The three Adnan-eye lines (KILL_MID_CHIN_FAKE_JAW, ROUND_LOWER_FACE, JAW_ROUNDED_PLATE) and OVERALL_HOLD are **my** judgement from Blender renders (the same 4-light Unity-like rig as the F1 match sheet) plus measured proxies, not a Unity capture and not Adnan's eye. Adnan's eye is final; the open questions I could not close are listed under "Honest notes".

Time: 12:14 → ≈13:25 on 2026-10-02 (`START_TIME.txt`; whole pipeline re-runs in ≈65 s with `run_all.sh`).
Stage only: nothing installed. ArtDir `HeroBase_Female.blend` is still SHA `200dc3b9…`; no file outside `work/female-micro-f2-head/` was written by this chat (the other `work/` and `ArtDir/.../parallel_prompts` files that changed during the hour belong to the parallel hands / pelvis chats).

## Where things are
| What | Path / SHA-256 |
|---|---|
| Start (immutable copy, SHA verified before any edit) | `start/F1_STAGED.blend` `4450c644a895fb5d2962ed76077770ea39af21de81482bb275d02510747f876e` (matches the SHA given in the brief) |
| **Staged result blend** | `export/HeroBase_Female_MicroF2_head_STAGED.blend` `bb629a65b4e64e64fad6e5ab07b8c1e8875ec5acbb0f61667d81ee9717daf3e9` |
| **Staged FBX** (Body_F + Face_F, same flags as F1: axis −Z/Y, scale 1, normals only, no leaf bones; re-import max error 0.0003 mm) | `export/HeroBase_Female_Body.fbx` `90a669fa4d712d94bf5ed45d8eef0dc5e9abe2fcfc243db4333eef4204a76210`, report `export/export_report.json` |
| Proofs | `proof/F2_chin_closeups_plate_F1_F2.png` (front, slight-up, both 3/4 from below, profile, under-chin) · `proof/F2_lowerface_BA_plate_F1_F2.png` (plate \| F1 \| F2 at the plate cameras: front, 3/4 L, 3/4 R, profile) · `proof/02_match_f_head_F2.png` (updated 16-crop match sheet) · evidence: `F2_highpass_shading_F1_vs_F2.png`, `F2_curvature_k1_F1_vs_F2.png`, `F2_sections_plan/coronal_F1_vs_F2.png`, `F2_sagittal_profile_vs_plate.png`, `F2_analytic_surface_old_vs_new.png` |
| Numbers / logs | `data/final_tables.json`, `data/final_params.json`, `data/verify_f2.json`, `logs/verify_f2.txt`, `logs/verify_asm_vs_ArtDir_start.txt`, `logs/sil_body_F{1,2}.txt`, `logs/loops_audit_F{1,2}.txt`, `logs/hw_final.txt` |
| Tools (all self-contained here; F1 dir only read) | `tools/` — `geo2.py` (rebuilt head), `exp.py` (zone + normal-direction projection), `make_final.py` (parameters), `assemble2.py`, `verify_f2.py`, `make_proofs.py`; `run_all.sh` reproduces everything |

## What was wrong in F1 (root causes, measured — not guessed)
The "fake jawline near mid-chin" was not one crease; it was four stacked hacks in the analytic head, all of which I can point at in `ArtDir/.../female-micro-f1-head` (`geo.py`, `loftf.py`, `data/prof_corr.json`, `data/a_corr.json`):
1. **Chin-boss step (the belt).** `prof_corr` pushes the chin bottom forward by a **+15 mm (clamped)** and ramps it to 0 over 8 mm (z 1.432→1.440), weighted by a 30 mm Gaussian in x → a horizontal step across the front of the chin. The loft's front plane (`FRONT_BASE` rows 244–250) *recedes 19 mm* toward the chin bottom, so the chin was a boss sitting on a receded plane; the analytic chin bottom overshoots the plate by ~13 mm and F1's fairing (up to 8.7 mm) dragged it back, leaving a dimple and a kidney-shaped chin-bottom section.
2. **Clamped jaw-width hack.** `a_corr` widens the loft half-width by **+12 mm (clamped)** over z 1.444–1.458 (+4…+10 mm below, +2 mm at 1.48) to compensate for the underside plane trimming it later. The clamp corners give curvature spikes of **−1033 / −615 / −534 / +517 m⁻¹** at z 1.444 / 1.458 / 1.462 / 1.478 → horizontal ridges across the lower-cheek wall and the diagonal mouth-corner→chin crease in 3/4. Plate-quantisation ripple in `a, yf` adds the "wood-grain" banding (visible on the analytic surface alone: `F2_analytic_surface_old_vs_new.png`).
3. **Under-chin too high.** The underside plane rose 0.15 toward the neck: the under-chin silhouette sat **+3.3 / +5.8 / +7.5 mm** above the plate line at y = −80 / −70 / −60 mm.
4. **The jaw_ear loop itself** ran along that false line (a vertex group, not geometry).

## What F2 changes (lower face only)
All inside one zone (see gates): rebuilt analytic `Head2` (F1's `Phi` with the construction fixed) and every moved vertex slides **only along its own surface normal** onto the new surface (bisection; F1's vertex spacing and loops are kept; ray-chart deltas squashed three thin chin-underside triangles to 0.06 mm² and were rejected).
- chin front vertical (FRONT_BASE rows 244–250) and F1's +15 mm chin-boss table zeroed below z 1.452;
- underside = plate under-chin line (flat, z 1.4265) with a bowl rising laterally (cx 8.2 at the chin → 6.0 at the back), smooth-min blend radius 25 mm at the midline → 28 mm at the sides (soft roll, no edge);
- loft half-width / front-plane rows smoothed in z (σ 5 mm), spikes gone (peak 1033 → 66 m⁻¹); F1's clamped compensation is no longer needed because the plane no longer over-trims;
- under-chin blends back into F1's own neck-junction shape over y −90 → −46 mm (a short blend left a crisp 74° concave crease and shading flaps; the long blend keeps the junction at 39° max, F1: 36°);
- **+2.8 mm soft lower-cheek / jaw-body fullness** (Gaussian outboard of the lips, x 54 mm, z 1.472; silhouette-neutral) as the only "fill";
- Face_F paint under the moved skin re-projected (194 verts, ≤ 0.022 mm).

## Gates (hard)
| Gate | Result | Evidence |
|---|---|---|
| BODY_BELOW_NECK | **PASS** | 12,421 body vertices (everything at/below the collar ring) **bit-identical to the ArtDir start blend** (max diff 0.0 m, `verify_asm`), and 12,506 verts with z < 1.4225 bit-identical to F1 |
| ZONE_OUTSIDE (head only) | **PASS** | 1,671 Body_F verts moved, z 1425.9–1524.3 mm, y −124…+33, \|x\| ≤ 89, max move 5.0 mm; 0 verts above z 1.53; 0 in the mouth/nose core \|x\|<20 mm; nothing behind the jaw angle |
| TOPOLOGY / loops hold | **PASS** | faces, material indices, smooth flags, UVs, 21 `LOOP_*` groups (membership + weights), 21,780 / 3,611 verts and 42,296 + 5,364 = 47,660 tris identical to F1; boundary edges 256 (the two eye apertures), non-manifold 0; **all eye / ear / nose / mouth loops moved 0.000 mm**; loops audit 21/21 OK. `LOOP_jaw_ear_L/R` keep their vertex ids (still contiguous 44/46-vertex edge paths) and moved ≤ 3.2 mm with the surface — disclosed below |
| SIL bald front/back ≤ 5 % | **PASS** | `sil_body.py` on `female_body_bald.jpg`: front **2.19 %** (F1 2.13), back **4.74 %** (F1 4.68), limit 5.0 % |
| KILL_MID_CHIN_FAKE_JAW | **PASS (eye + measured)** | belt, chin dimple, mouth-corner→chin diagonal, cheek banding and the profile streak are gone in front / slight-up / both 3/4 / profile / under-chin (`proof/F2_chin_closeups…`); causes 1–2 removed at the source; edge-angle across the lower cheek band mean 4.59→3.33°, p99 21.9→13.2°; chin front mean 7.29→6.22°, p99 29.6→20.7° |
| ROUND_LOWER_FACE | **PASS (eye)** | one continuous egg from cheek to chin, no hollow, no cartoon bulge; +2.8 mm lower-cheek fullness; front half-width within +2.4 mm of the plate (F1 +2.0), q3R chin/jaw contour within 1.4 mm rms of the plate (F1 stood out +3.3 mm rms) |
| JAW_ROUNDED_PLATE | **PASS (eye)** | the mandible reads as the soft rolled lower contour (blend radius 25–28 mm) from the chin corner to the gonial angle, at the plate's silhouette, no knife edge and nothing at mid-chin; front/profile/3q silhouettes unchanged vs F1 within 3 mm |
| OVERALL_HOLD | **PASS** | head-region silhouette IoU, F2 (F1): front 0.976 (0.976), left/right profile 0.971/0.970 (0.971/0.970), 3/4 R 0.953 (0.952), 3/4 L 0.810 (0.813, plate inconsistent), top 0.745 (0.745), body-plate front/back head 0.911/0.911 (0.912/0.912) (`proof/proof02_info_F2.json`); eyes, brows, nose, mouth, ears, cranial vertices not moved at all |
| NO densify / NO male jaw copy | **PASS** | tri counts identical; built only from the female plates and F1's own female analytic head |

Extra mesh-health gate (mine): **NO_FOLDS PASS** — faces touching moved vertices: max face-normal change 31.0°, 2 faces > 30°, 0 inverted, min area 0.76 mm² (F1 0.99), edge lengths 1.32–11.97 mm (F1 1.35–11.97).

## Numbers
Under-chin silhouette (min z over x, mm; plate = left profile staircase): y −115 / −110 / −100 / −90 / −80 / −70 / −60 / −55 / −50 → plate 1434.2 / 1431.1 / 1428.0 / 1426.5 ×5; F1 error +0.2 / −2.5 / −2.1 / +1.0 / +3.3 / +5.8 / +7.5 / +7.2 / +5.4; **F2 error +1.3 / −2.2 / −1.6 / −0.3 / +0.1 / +2.1 / +5.5 / +6.2 / +5.1**.
Front jaw half-width vs smoothed plate (mm, rows 1.446–1.497): F1 −1.8…+2.0, F2 −1.9…+2.4 (changes vs F1 ≤ 1.2 mm).

## Honest notes (read these)
1. **Eye lines are my read, not Adnan's, and not Unity.** I did not run Unity: the shared project is open to the parallel chats, so no batch import was started. Proofs are Blender EEVEE with the Unity-like 4-light rig from F1's `ul.py`; Unity's key light clips cheeks harder (F1 note), so the lower cheek may read flatter there than here.
2. **Under-chin line near the neck is still above the plate line** (+5…+6 mm over the last 35 mm, F1 +5…+7.5). I stopped the plate-line underside at y ≈ −80 and blend it back into F1's untouched neck-junction rows; pulling it to the plate line all the way created slivers / a 74° crease at the junction (tried, rejected — `data/trials/`). Lowering it fully needs the neck-front rows (z 1.4225–1.436) to move; that is the neck chat's zone.
3. **"Rounder" came mostly from removing creases and the clamped, boxy wall, not from new volume.** In plan at z 1.45–1.456 the front-lateral jaw wall is now up to 8 mm narrower than F1's (parallel-sided) wall; the consistent 3/4 plate (q3R) says that is closer to the plate, the inconsistent one (q3L, IoU 0.81) says the chin is ~2.4 mm slimmer than F1 (mean contour offset at chin rows: F1 −4.3 mm, F2 −6.7 mm). A wider variant (relaxed underside rise) pushed the *front* silhouette 4–7 mm wide, so I kept the silhouette-faithful one. If Adnan wants a fuller lower face, the knob is the `bumps` entry in `tools/make_final.py` (+2.8 mm now; +3.5 mm with a second chin-side bump created a new fold in a trial).
4. **Metrics I tried and dropped:** shading high-pass energy and band-pass energy of the render (plate vs F1 vs F2) — confounded by the chin-underside roll, they scored F2 *rougher*; not used as a gate. The gates above use geometry (edge angles, curvature, sections) and the plate silhouettes.
5. **Plate disagreements** (unchanged from F1): 3/4 plates are perspective renders (q3L inconsistent), the back body figure is ~4 % narrower than the front (back SIL 4.74 % is only 0.26 % under the limit by that split), top view hides the ears.
6. **jaw_ear loops** were a vertex-group path along F1's false jawline; kept as the same edge paths so loops hold, they now lie on the cheek just above the soft mandible roll. Re-deriving them along the new border is a one-liner for whoever needs the loop for blendshapes.
7. Not done (out of scope / needs a decision): install into the ArtDir blend / Unity prefab, Unity refresh (`ExpectedTriangles` unchanged: 42,296 + 5,364), eyes / brows / nose / mouth / cranial / ears / collar, any hair or clothes.

## Reproduce
`cd work/female-micro-f2-head && zsh run_all.sh` (Blender 5.2.2 headless + system python3 with numpy/Pillow). Needs only `start/F1_STAGED.blend` (SHA-checked) and the F1 data files copied into `data/` (`b17_state.npz`, `ring.npz`, `sil.json`, `prof_corr.json`, `a_corr.json`, `q3.json`, `work_assembled_vmap.json`).
