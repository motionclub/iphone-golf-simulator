# GATE_RESULTS — FEMALE LIMBS (chat 8/8) — 2026-10-01 22:26

## GATE: FEMALE_LIMBS PASS

| gate | result |
|---|---|
| G1 OUTSIDE_ZONE = 0 (independent audit vs the start file) | PASS |
| G2 MESH integrity + budget | PASS |
| G3 LIMB SILHOUETTES vs plate consensus (front+back) | PASS |
| G4 SIDE PROFILE of the lower legs vs the plate profile (z 0.17–0.46 m) | PASS |
| G5 DIMENSIONS vs plate | PASS |
| G6 STRUCTURE: 5 toes per foot, 4 fingers + thumb per hand (persistent geodesic extremities) | PASS |
| G7 FBX export re-imports identically (export/ only; NOT installed in ArtDir) | PASS |

### G1 OUTSIDE_ZONE = 0 (independent audit vs the start file) — PASS
- start SHA 200dc3b93e65491a…  final SHA 5ff76a9b1d79baeb…
- baseline verts outside the limb zone: 16854, missing or moved: 0
- removed/moved baseline verts outside zone: 0; new verts outside zone: 0
- untouched faces checked 17159: missing 0, material diffs 0, corner UV diffs 0
- corner normals away from the change: 0 differ of 67788 (174 at the zone boundary, expected)
- Hair_F vertex hash identical: True; all other scene objects identical: True
- zone = z < 0.58 (feet, ankle, shank, calf) OR |x| > 0.18 & 0.60 < z < 0.875 (hands, wrists); arms above the wrist rings and the torso/head are not touched

### G2 MESH integrity + budget — PASS
- non-manifold edges 0, non-contiguous (flipped) edges 0, degenerate faces 0, loose verts 0
- signed volume 0.05454 m³ (>0 = outward winding); materials unchanged: True
- tris: body 44762 (baseline 44708) + hair 4960 = 49722 (limit 50000, base_lock/ACCEPTANCE.md)
- height z_max 1.7038932 (baseline 1.7038932); lowest vertex z -0.059 mm (soles on the ground)

### G3 LIMB SILHOUETTES vs plate consensus (front+back) — PASS
- metric = soft XOR of the model silhouette vs the MEAN of the four plate silhouettes (front-L/R, back-L/R) in each limb zone, divided by how far the plate views are from that same mean (the plates disagree with each other)
- threshold: ratio <= 1.25 (model no further from the plate consensus than 1.25x the plates are from each other)
- arms : model 0.155 vs plate-self 0.184 -> ratio 0.84  (baseline 0.84)
- hands: model 0.131 vs plate-self 0.149 -> ratio 0.88  (baseline 1.11)
- legs : model 0.092 vs plate-self 0.097 -> ratio 0.96  (baseline 0.80)
- feet : model 0.222 vs plate-self 0.207 -> ratio 1.07  (baseline 0.88)
- per-view XOR % vs the plate polygons (baseline -> new; plate-vs-plate floor of the best symmetric mask in brackets) — informational, NOT the gate:
-   legs  front   9.5 ->  10.2   back  11.5 ->  13.4   [floor: mean 8.1%, per view {'frontL': 2.95, 'frontR': 8.86, 'backL': 6.21, 'backR': 14.42}]
-   feet  front  18.9 ->  15.1   back  23.4 ->  33.0   [floor: mean 17.7%, per view {'frontL': 11.2, 'frontR': 4.25, 'backL': 24.63, 'backR': 30.57}]
-   arms  front  11.9 ->  11.7   back  21.0 ->  21.1   [floor: mean 14.1%, per view {'frontL': 4.01, 'frontR': 11.11, 'backL': 20.92, 'backR': 20.24}]
-   hands front  16.7 ->  13.1   back  20.6 ->  17.8   [floor: mean 11.8%, per view {'frontL': 10.02, 'frontR': 5.14, 'backL': 14.89, 'backR': 17.01}]

### G4 SIDE PROFILE of the lower legs vs the plate profile (z 0.17–0.46 m) — PASS
- max front/back edge deviation: baseline 59.6 mm -> new 8.7 mm (threshold 12 mm)
- mean |shank depth deviation|: baseline 22.5 mm -> new 9.4 mm; max 31.9 -> 11.8 mm
- new targets = plate edges pulled in 5 mm per side (the profile plate shows both legs slightly yawed, so its union silhouette is ~10 mm deeper than one leg); the residual -8…-11 mm depth error is that allowance, not a fit error
- front/back (x) silhouettes are unchanged by this step (y-only remap)

### G5 DIMENSIONS vs plate — PASS
- foot length heel->toe: R 0.2398 m, L 0.2397 m (plate profile 0.241 m, tolerance ±8%); toe-out 7.2° / 7.0°
- hand length wrist crease (z 0.8456) -> fingertip: R 0.1537 m, L 0.1537 m (plate 0.153 m, tolerance ±10%)
- sole height: lowest new foot vertex z -0.06 mm / -0.06 mm

### G6 STRUCTURE: 5 toes per foot, 4 fingers + thumb per hand (persistent geodesic extremities) — PASS
- method: geodesic distance over mesh edges from the weld seam; count extremities whose persistence (height above the saddle that joins them to a longer one) is large
- feet: toes with persistence >= 15 mm: R 5 ([248.7, 38.1, 33.3, 29.5, 22.3] mm), L 5 ([249.9, 39.1, 32.4, 29.9, 23.6] mm)
- hands: extremities with persistence >= 8 mm: R 5 ([168.4, 47.1, 20.2, 19.9, 9.9] mm), L 5 ([197.0, 48.4, 23.8, 20.4, 10.2] mm)

### G7 FBX export re-imports identically (export/ only; NOT installed in ArtDir) — PASS
- export/HeroBase_Female_Body_limbs.fbx sha 0b196f4e30a13b8d…; re-import verts 22419 tris 44762 (blend 22419/44762), height 1.70395 m, scale 1, same 10 materials, custom normals True
- exporter settings copied from Tools/HeroBase/export_male_form.py (scale 1, -Z forward, Y up, no leaf bones, no animation)

## What changed (limb zone only)
- Lower legs (z 0.14–0.58): y-only remap of each z-slice to the plate side profile (2491 vertices moved; x untouched, so front/back silhouettes are unchanged).
- Feet: the old skin foot below the ankle ring (z=0.15728) replaced by a new foot (heel, arch/instep wedge, 5 toes, flat sole), welded vertex-to-vertex onto the existing 24-vertex ankle ring; hands: old hand below the wrist ring replaced by a new hand (palm, 4 fingers, thumb), welded onto the existing 18-vertex wrist ring (right ring z=0.8456, left ring z=0.8726 — the only planar rings in the start mesh).
- 6094 old triangles removed, 3028 new vertices; body tris 44708 -> 44762.
- New faces: feet = Skin_F, hands = Base_Grey_F, UVs on flat patches of the existing albedo atlas (skin / grey), smooth normals.

## Not done / limits (honest list)
- Not installed into ArtDir (install rule: only after the torso chat is idle or via a documented vertex mask). Merge map: data/HeroBase_Female_limbs_vertex_map.npz (baseline index -> final index, new vertices = -1, zone mask).
- No Unity import/render was run in this chat; the proof is Blender Workbench renders + the FBX re-import check.
- Plate disagreement: the four plate silhouettes disagree 20–35 % with each other in the hands/feet, and the back plate's soles sit ~8 px higher than the front plate's, so per-view XOR cannot reach 5 % in these zones (floors listed in G3); the feet consensus ratio is 1.07 vs 0.88 for the crude baseline foot — within the gate, but not better than the baseline on that metric (the 3D form, profile, toes and length are much better).
- The hand palm is turned ~55° (from a fit to the plate silhouettes); the profile targets carry a 5 mm-per-side allowance for the plate's yawed legs. Both are judgement calls from noisy plates — Adnan's eye check is final.
- Arms above the wrist were left untouched (already at the plate floor in the front/back silhouettes).
- Toes are stylised soft-plastic lobes (no nails); fingers are capsule-like.

## Files
- work/female-parallel-limbs/HeroBase_Female_limbs.blend (deliverable), export/HeroBase_Female_Body_limbs.fbx, baseline/HeroBase_Female.blend (start copy, SHA 200dc3b9…)
- proof/01_limbs_vs_plate_front_back.png, 02_silhouette_overlay_before_after.png, 03_profile_vs_plate.png, 04_hands_vs_plate.png, 05_feet_vs_plate.png, 06_before_after_limbs.png
- data/audit_final.json (outside-zone), metrics_final.json, measure_final.json, peaks_final.json, silhouette_floor.json, HeroBase_Female_limbs_report.json, HeroBase_Female_limbs_vertex_map.npz
- Reproduce: `blender -b baseline/HeroBase_Female.blend --python make_limbs.py -- HeroBase_Female_limbs.blend 1800 1500 5` (needs data/foot_R_raw.npz, hand_R_raw.npz from shapes.py, data/leg_targets.json from legtargets.py)
