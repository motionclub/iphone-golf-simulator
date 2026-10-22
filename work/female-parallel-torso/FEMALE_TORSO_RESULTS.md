# FEMALE TORSO — results (parallel chat 7 / 8)

**GATE: FEMALE_TORSO PASS** (torso zone only — see "Not claimed" at the bottom)

Start: `ArtDir/hero/base_lock/blender/HeroBase_Female.blend`
SHA-256 `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` — verified before work, verified again at the end (ArtDir blend untouched; nothing installed into ArtDir).
Work folder: `work/female-parallel-torso/` (everything below lives here).
Staged result: `export/HeroBase_Female_torso_candidate.blend` (+ `export/torso_delta.npz`, `export/merge_torso_delta.py`, `export/README_MERGE.md`).

## What changed

Female torso only — chest → waist → pelvis shell, **3,317 vertices moved, 44,708 triangles before and after, vertex order/topology/UV/materials identical.**

The old torso was a straight, front/back-symmetric slab (an ellipse tube, 0.16 m deep at the waist). The plate side profile (left + right panels of `female_multiangle_body.jpg`, edge-extracted, anchored on the knee centre) says the torso is deeper at the front and has real shape. The new torso follows that contour:

| z (m) | feature | plate front / back (mm) | before | after |
|---|---|---|---|---|
| 1.20 | bust apex | −131 / +81 | −97 / +95 | **−135 / +84** |
| 1.08 | waist | −120 / +75 | −80 / +80 | **−120 / +74** |
| 1.00 | lumbar hollow | −120 / +61* | −85 / +85 | −119 / +69 |
| 0.94 | glute top | −120 / +105 | −102 / +102 | −117 / +100 |
| 0.86 | glute peak / hip | −102 / +117 | −119 / +119 | −111 / +117 |

(y in mm from the knee-centre plane, − = forward. *plate lumbar edge is ambiguous: gradient edge 0.0605 m, background-mask ≈ 0.08 m; model 0.069.)

Added forms, all plate-visible: two compact-support bust mounds (soft lower contour, gentle upper slope), lumbar curve, round glute lobes with a soft gluteal cleft that deepens toward the crotch, flat belly line. Torso x-widths were **already** within ~3 mm of the plate (waist/hip notch) and are kept (x moves ≤ 2.6 mm from denoising only).

## Zone (merge key)

* `z ≥ 0.795` (crotch plane — below it the legs are separate components) up to the neck base `z ≤ 1.37`; displacement weight is 0 at z ≤ 0.795, full from 0.88, and fades to 0 between z 1.25 and 1.34 so the neck/shoulder seam never moves.
* Arms: below the armpit (z < 1.165) arms are separate connected components → excluded exactly. Above it, arm = `|x| > X_B(z)` (0.124 m up to z = 1.28, ramping to 0.17 at z = 1.34). Weight tapers to 0 over 7.5 cm toward the arm.
* Zone mask = `export/torso_delta.npz:zone_mask` (3,320 vertices; 3,317 actually move). Picture: `proof/06_zone_map.png`.

## Gate lines (binary)

| # | line | result | evidence |
|---|---|---|---|
| 1 | start SHA verified | **PASS** | `outside_zone_audit.json` |
| 2 | vertices moved outside the zone = 0 (float32 bit-exact); max displacement outside = 0.0 m | **PASS** | `outside_zone_audit.json` — head/neck 0, arms 0, hands 0, legs/feet 0, everything-else 0 |
| 3 | topology / UV / material ids / smooth flags / **custom-normal raw codes** / attribute list / other objects (Hair_F, plates, lights, camera) identical | **PASS** | `outside_zone_audit.json` |
| 4 | tris unchanged (44,708 ≤ 50k budget), 0 flipped, 0 degenerate | **PASS** | `checks.json: mesh_quality` |
| 5 | torso side-profile silhouette vs plate ≤ 5 % (rows z 0.82–1.30) | **PASS 2.6 %** (was 15.5 %) | `proof/02_side_profile_overlay.png`, `checks.json` |
| 6 | torso visible-edge silhouette front/back ≤ 5 % (rows below armpit, arms excluded) | **PASS 3.4 % / 4.4 %** (unchanged: widths were already right) | `proof/03_front_back_silhouette_overlay.png` |
| 7 | surface quality: regular mirror-stripe test, no creases/lumps/tears at neck, arm, leg seams (only deviations: the intended bust/glute rings and a mild stripe bend where the chest wraps toward the arm) | **PASS** | `proof/05_smoothness_mirror_test.png` |
| 8 | plate forms present (bust, waist depth, lumbar curve, glute lobes + cleft) | **PASS** | `proof/01`, `04`, `07` |
| 9 | proof images + checks json delivered | **PASS** | `proof/` |

Side contour error (mean / max, mm): front 26 / 42 → **3.5 / 12**, back 8 / 30 → **2.5 / 16**.

## Method (reproducible: `bash run_all.sh`, ~2 min)

1. `extract.py` dumps the start mesh; `extract_side_profile.py` gets the plate contour; `zone.py` builds zone + weights.
2. `fit_torso_final.py` remaps each torso ring's depth to the plate front/back targets (`targets.py`), adds bust + cleft, with all fields evaluated on a Taubin-denoised copy of the surface so the original surface-nets jitter does not show up as creases. An iterative loop makes the section extents hit the targets.
3. `apply_coords_plain.py` writes **positions only**. The authored custom normals are untouched (bit-identical codes; they are stored relative to the computed loop normal, so they follow the new geometry). Clearing them would have changed shading on the head and arms (measured: up to 64° on 20k loops) — so they are deliberately kept.
4. `audit_zone.py`, `final_metrics.py`, `make_proofs.py` produce the audits and images.

## Hand-offs / honest notes for the other chats

* **Arms (chat 8):** in the plate side view the arm axis hangs ≈ 0.03 m *behind* the knee-centre plane and its back edge is flush with the upper back; the model arms are centred on y = 0. I did not touch arms. The torso now reads correctly in front of them (arm front edge ≈ 8 cm behind the chest, as in the plate); moving the arms back ≈ 0.03 m would finish the plate pose. Shear at the armpit is absorbed by the 7.5 cm taper.
* **Neck base (chat 6):** plate neck half-width ≈ 0.036 m at z ≥ 1.40, model ≈ 0.048–0.057. The ring at z ≥ 1.34 is fixed by design; blend the neck over z 1.34–1.40 when you slim it.
* **Thighs (chat 8):** plate thigh front at z 0.73–0.81 sits ≈ −0.107 m, model legs ≈ −0.095; the pelvis taper (z 0.795–0.88) hides the step but the plate wants ~1 cm more forward thigh.
* The multi-angle sheet figure (3/4 panels) has visibly wider hips/thighs and thinner arms than the bald plate. Widths follow the bald plate (it is the ≤5 % silhouette authority); see `proof/04_plate_vs_model_3q.png`.
* Residuals worth knowing: lumbar z≈0.98 back +16 mm vs the gradient edge (ambiguous plate edge); upper chest z 1.24–1.30 ±11 mm because the weight fade protects the neck seam.

## Not claimed

* Whole-body front/back silhouette (bald plate): 7.9 % / 11.0 % — **unchanged and still > 5 %**; that error lives in head, arms, legs (other zones). This chat's x-widths were already inside the gate.
* No Unity import / prefab / FBX re-export was done, and **nothing was installed into ArtDir** (install rule: others stay in `work/*/export` until merge; ArtDir female blend is still `200dc3b9…`). No clothes, no hair change, no rig.
* Combined with chat 8's limbs (preview merge) the whole-body front/back silhouette is 8.2 % / 11.8 % — still not ≤ 5 %; the remaining error is head, arm/hand placement and the plates' own centre/pose disagreements.

## Files

| file | purpose |
|---|---|
| `export/HeroBase_Female_torso_candidate.blend` | start blend + torso only (positions) — sha256 `696e1be4…45310e9` |
| `export/torso_delta.npz` | `moved_idx, start_co, new_co, zone_mask, weights` — sha256 `bed6438f…45e827` |
| `export/merge_torso_delta.py` | applies the delta onto any same-topology blend; reports conflicts instead of overwriting |
| `outside_zone_audit.json` | outside-zone = 0 audit |
| `checks.json` | all gate numbers incl. per-height side table |
| `proof/01…07_*.png`, `proof/final/*` | before/after, side overlay, front/back overlay, 3/4 vs plate, mirror test, zone map, close-ups |
| `export/PREVIEW_torso_plus_limbs_UNOFFICIAL.blend` | torso delta merged into chat 8's `HeroBase_Female_limbs.blend` via `--vmap` (3,317/3,317 applied, 0 conflicts) — preview only, `proof/08_merged_preview_torso_plus_limbs.png` |
| `HeroBase_Female_torso.blend` | untouched byte-copy of the start blend (sha `200dc3b9…`) |
