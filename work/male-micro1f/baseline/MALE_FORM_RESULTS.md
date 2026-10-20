GATE: MALE_FORM PASS

Micro1e · male CHIN + FINGERS · 2026-10-01 · supersedes the Micro1d result (that file recorded FAIL against an invented 2 % gate; the gate is ≤ 5.0 %).

| Line | Result | Evidence |
|---|---|---|
| CHIN | PASS | Profile front surface vs `male_head_detail.jpg` within **4.6 mm max / 2.2 mm mean**, jaw+neck half-width within **4.2 mm max / 1.9 mm mean** over the jaw band z 1.444–1.506 m (table below). Chin is a defined U-chin ball, clear under-chin plane, neck column. No beard slab, no recessed dough chin. Face is still blank (out of scope). |
| FINGERS | PASS | Each hand = palm + 4 separated fingers (rounded tips, visible gaps front / 3-4 / side) + a separate thumb. Not a mitt, no claw spikes. Hand silhouette mass vs plate masks: front view 0.86×, back view 1.03–1.08× (the front and back plates themselves disagree by ~28 % on hand size). |
| SIL_% | PASS | bald_front **4.0007 %**, bald_back **4.1899 %** (gate each ≤ 5.0 %). Unity masks: 4.0963 % / 4.1142 %. |
| SHOULDERS | PASS (unchanged) | 4,806 verts in region, 0 changed (bit-identical). |
| WAIST | PASS (unchanged) | 1,832 verts in region, 0 changed. |
| ARMS_SIDE | PASS (unchanged) | 3,366 verts in region (|x|>0.28, z 1.0–1.3), 0 changed. Forearm depth at the weld matches the old mesh (y-extent 82.7 mm vs 82.6 mm at z 0.98). |
| FEET_SIDE | PASS (unchanged) | 3,482 verts in region (z<0.25), 0 changed. 318 vertices below 4 mm, lowest 2.472 mm (same as before). |

"PASS (unchanged)" means not regressed: those vertices are bit-identical to the Hand_4 lock. Adnan's eye check remains the final authority on CHIN and FINGERS.

## What changed (and what did not)

* Start mesh: `ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend` (Hand_4 lock, SHA-256 `d39c6c5e5157ff15428759c01eaa227a09ea1bcd4b0d1a51acfe4110795d2413`). The `work/male-jaw-5/outline/candidate.blend` was **not** used.
* Edited object: `Body_M` only. Of the 24,578 original vertices, 2,393 moved: 721 in the head/neck zone (z > 1.43), 1,672 in the two hand/lower-forearm zones. **0** other vertices moved. No head vertex below z = 1.35. Cameras, masks, plates, transforms, origin, material, scale untouched.
* CHIN: coordinate-only refit. Lower-face vertices (550 weighted) are projected onto an implicit chin/jaw target (face-plan ellipse ∩ rounded U-superellipse in the front view, smooth-unioned with an elliptical neck column), tangentially relaxed, then a light Taubin pass on the cheeks. Connectivity unchanged, no face flips.
* FINGERS: the old hand had no finger loops (≈110 irregular vertices per hand tip), so coordinate-only fixes tangled into creased blobs. **Adnan approved a local hand rebuild in chat** (“Yes, rebuild hands locally”). Both hands were cut off at ≈ 4 cm above the wrist (weld ring z 0.957–1.003 m, 42 vertices, positions untouched) and replaced with a clean quad palm + 4 fingers + thumb welded to that ring. All non-hand/non-head vertices keep their indices and positions. Vertices 24,578 → **24,652** (+74), faces 24,588 → 24,670, triangles 49,176 → **49,304** (36 triangle faces, rest quads). Closed manifold, 0 boundary edges, 0 zero-area faces, 0 loose vertices. 2 non-manifold edges and 19 folded body edges are inherited from the Hand_4 mesh (not new).
* Height 1.702187 m, METRIC scale 1, A-pose, `Blockout_Grey` material, FBX scale 1 (Blender re-import max vertex error 0.000279 mm).

## Chin vs plate (male_head_detail.jpg, calibrated 1.3044 mm/px)

Left profile, front-most surface of the mesh vs plate (`mesh − plate`, mm):

| z (m) | 1.517 | 1.506 | 1.496 | 1.486 | 1.475 | 1.465 | 1.454 | 1.444 | 1.433 |
|---|---|---|---|---|---|---|---|---|---|
| Δ front surface | −0.7 | +1.3 | −1.3 | −3.9 | +0.7 | +2.6 | +4.6 | −0.7 | −0.7 |
| Δ jaw/neck half-width (front view) | +7.8 (cheek) | −2.9 | +0.3 | +2.3 | +1.6 | +1.6 | −0.3 | −4.2 | −11.1 (neck base) |

Before this pass (Hand_4 lock, same measurement): central side profile |Δ| ≤ 5.9 mm (mean 3.5 mm) — it had already been tuned — but the jaw/neck **front-view width was +4.6…+10.8 mm too wide (mean +5.8 mm)** and the 3D lower-jaw form read as a soft recessed slab with a rippled jaw→neck join. After: width |Δ| ≤ 4.2 mm (signed mean −0.2 mm), profile |Δ| ≤ 4.6 mm (mean 2.2 mm), and the form is a U-chin ball with a clear under-chin plane. Rows 1.517 and 1.433 are outside the chin/jaw band (cheek/ear and neck-base/trapezius) and are listed for completeness. Full tables: `work/male-micro1e/final/chin_profile_numbers.txt` (after) and `chin_profile_numbers_baseline.txt` (before). The numbers are one-plane silhouette measurements; the visual comparison in `01e_chin_fingers_m.png` is the broader check.

## Known remaining differences (not in this pass)

* Face is a blank blockout: nose sits ≈ 2 cm lower than the plate, cheeks/ears are ≈ 1 cm wider, no eyes/mouth.
* Hands: thumb root is thinner than the plate's thenar mass, fingers are straight tapered tubes without knuckle detail.
* Neck base / nape (z < 1.43) is the unchanged Hand_4 geometry.
* Legacy verifiers `Tools/HeroBase/export_male_form.py`, `verify_male_form.py`, `verify_male_form_d.py` hard-code the Hand_4 topology (24,578 verts / 49,176 tris / old connectivity hash) and will fail against this blend by design. Use `work/male-micro1e/audit_final.py` and `export_fbx.py` for this lock.

## Files and hashes

* Blend (installed): `ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend` SHA-256 `35766aea1c493bab0ce1bddd6bc7639c4b304630c500c1d654b4336c2e113d90`
* FBX (source = Unity import): `ArtDir/hero/base_lock/unity_import/HeroBase_Male_Body.fbx` SHA-256 `3268e665ecedb83de441ca4640e5c2aa024e65c2cdd09f3e89c6cf1c7560d3ad`
* Unity prefab `HeroBase_Male.prefab` SHA-256 `f65086bee4edcb9fca339ee58ba4f81a7a851e9428e95757f3354c43738a3338` (unchanged file; it points at the re-imported FBX). Unity importer: scale 1, file scale 1, mesh compression off, normals imported, one opaque grey URP Lit renderer, no hair, no texture.
* Unity audit: `male-form-unity-audit.txt` (MALE_FORM_SAVED_UNITY_VERIFY=PASS, 49,304 triangles, 24,652 vertices, height 1.702187 m) + 13 captures with masks in `male_form_d/unity/` (front, back, left, right, threequarter, head_side, foot_side, chin_front, chin_threequarter, hand_front, hand_side, hand_threequarter, handL_front).
* Prior state kept for rollback in `work/male-micro1e/baseline/`: original blend (SHA `d39c6c5e…`), `proof_prior/HeroBase_Male_Body.prior.fbx`, previous proof sheets and the previous `MALE_FORM_RESULTS.md` (2 % era), original `HeroBaseMaleFormProof.cs.orig`.
* `Unity/Assets/Editor/HeroBaseMaleFormProof.cs`: triangle contract now the constant `ExpectedTriangles = 49304` (was a hard-coded 49176) and six close-up captures added. Capture framing for the original seven views is unchanged.

## Proof

* `01e_chin_fingers_m.png` — body views, plate-vs-mesh chin (front, 3/4, profile), chin close-ups, both hands (4 views each), before/after, plate-vs-mesh hands.
* `03_unity_m.png` — actual Unity captures: five body views, chin and hand close-ups, authority plates.
* `01d_form_m.png`, `01e_head_all_around_m.png`, `01h_hand_form_m.png`, `01_silhouette_overlay_m.png` refreshed for the new geometry.
* Machine-readable: `male-micro1e-checks.json`.

## Reproduce

Scripts and intermediates live in `work/male-micro1e/`: `sculpt_core.py`, `head_edit.py` (chin: `jaw_mode='super', se_a=0.0735, se_b=0.0565, se_zc=1.510, se_p=2.0, z_bottom=1.440, r_round=0.030, k_union=0.024, neck_rx=0.0700, neck_ry=0.0715`), `hand_sdf.py`, `hand_topo.py`, `hand_build.py`, `hand_assemble.py` (hand: `curl=0.005, r_a=0.0130, r_n=0.0186, f_tip=[0.160,0.173,0.164,0.142]`, cut at w₀ = −0.055 with corner peeling), `finalize_blend.py`, `audit_final.py`, `export_fbx.py`, `sil_body.py`/`sil_gate.py` (native gate measurement, reproduces the old 3.7746 % / 3.7819 % on the baseline blend), `compose_proofs.py`. Working copies saved from the live Blender session: `work/male-micro1e/live/`.
