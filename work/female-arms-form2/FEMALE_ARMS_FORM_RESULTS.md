# FEMALE ARMS FORM — results (chat B, 2026-10-01)

**GATE: FEMALE_ARMS_FORM PASS** (by my own measured gates below; Adnan's eye check is final)

## Start / lineage
- Start = torso candidate + limbs merged (`work/female-parallel-torso/export/PREVIEW_torso_plus_limbs_UNOFFICIAL.blend`), copied to `start/start_torso_plus_limbs.blend`, SHA-256 `5c54f3959a92f4bbe8185a13442cfd6104bff10c51466c43eaedbaaa44ea5920`.
  It is `HeroBase_Female.blend` (ArtDir SHA `200dc3b9…`) + chat 7 torso (3,317 verts) + chat 8 limbs (22,419 verts).
- ArtDir `HeroBase_Female.blend` SHA at the end: `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` (unchanged, **nothing installed**).
- Candidate = `export/HeroBase_Female_arms_candidate.blend`, SHA-256 `573ab4431d83f8651936f0081ad3bda9c6890c56ee5dce3061140198c9455f0e`.

## What was wrong
The arms were two straight elliptical tubes at y = 0 (half-width 0.04 / half-depth 0.042 m the whole length, linear taper). Widths already matched the plate; the faults were *form*: no deltoid cap, no upper-arm/elbow/forearm structure, arms hanging ~3 cm too far forward (chat 7 hand-off), and the upper arm sitting 5–9 mm too far from the body in the front/back plates (outer edge +5.3 mm mean).

## What changed (arms only: deltoid -> wrist, both sides)
1,592 vertices moved of the 1,699-vertex arm zone; positions only (topology, UV, normals codes, materials untouched).
- **Hang**: arm axis shifted back (+30 mm at the elbow level, +10 mm at the armpit seam, 0 at the wrist ring) so the forearm leans forward like the plate (side profile). 
- **Inward axis shift** up to 8 mm in z 1.0–1.2 (front/back outer edge now 3 mm mean off the plate vs 5.3).
- **Soft-plastic form** (smooth cross-section modulations, 4–11 % of the radius, no sharp creases): deltoid cap (all-round + front/back), triceps and biceps lobes, a slight narrowing above the elbow, olecranon (elbow point), forearm belly (lateral + front) then taper to the wrist.
- **Seam**: every arm vertex that shares an edge with a non-arm vertex (torso border, wrist rings) is pinned; displacement fades in over 8 cm (shift 15 cm) and the displacement field is Laplacian-smoothed (8 it) with pins at 0, so no shelf/crease at the shoulder or armpit. Surface-nets jitter is preserved (the displacement is evaluated on a Taubin-denoised copy and added to the raw positions).

## Gates
| gate | result | evidence |
|---|---|---|
| ZONE_OUTSIDE=0 | **PASS** | moved 1592 of 1699 arm-zone verts; moved outside zone 0 (max disp outside 0.0 m, float32 bit-exact); pinned seam verts 107 moved 0 (max 0.0 mm); wrist rings moved R 0 / L 0; Hair_F + all other objects identical |
| TOPOLOGY | **PASS** | verts/edges/loops/polygons/material ids/smooth flags/UV/attribute data (incl. raw custom_normal codes) identical to start; tris 44762 (+4960 hair = 49722 <= 50000); non-manifold 0, degenerate 0, loose 0, signed volume 0.05590 m3 (>0); self-intersecting face pairs 2004 = start 2004 (all in the head: eyes/lashes; 0 in the arms) |
| ARMPIT_CLEAN | **PASS** | torso/arm seam verts moved 0 (limit 0.3 mm); face-normal flips 0; max face-normal change in arm zone 28.7 deg; armpit/shoulder-seam dihedral max 94.3 -> 96.3 deg, p99 58.3 -> 61.6 deg (limit +5 deg); edge stretch 0.76..1.37 (limit 0.6..1.5) |
| SIL_NOT_WRECKED | **PASS** | arm-zone XOR vs plate polygon front 11.67 -> 9.86 %, back 21.12 -> 21.31 % (limit start+1 pt; the plate back view is itself ~20 % off its own mean); consensus ratio (model/plate-self, <=1.25 and <= start) 0.835 -> 0.798; outer-edge deviation to plate consensus rows y175..340: mean 5.32 -> 3.05 mm, max 12.98 -> 12.98 mm |
| ARM_FORM_DEFINED | **PASS** | R: arm axis y at z1.08 = +29.7 mm (start +0.3; plate ~ +35; limit >= +25), at z0.92 = +6.8 mm (leans forward toward the wrist); elbow-neck dip in half-width = 2.39 mm (start 1.05; limit >= 1.8); added relief (per-slice displacement with the rigid shift removed, z0.90-1.30) RMS 5.38 mm (limit >= 1.5), p95 10.96 mm (limit >= 3.0) -> ok | L: arm axis y at z1.08 = +30.0 mm (start +0.1; plate ~ +35; limit >= +25), at z0.92 = +3.8 mm (leans forward toward the wrist); elbow-neck dip in half-width = 2.07 mm (start 1.11; limit >= 1.8); added relief (per-slice displacement with the rigid shift removed, z0.90-1.30) RMS 5.34 mm (limit >= 1.5), p95 10.98 mm (limit >= 3.0) -> ok |

Proof (`proof/`): `01_front_back_vs_plate.png` (plate | start | final), `02_side_vs_plate.png` (plate left profile with 2 cm grid | start | final), `03_arm_closeups_start_vs_final.png` (clay shading, front/3-4/side/3-4 back/back; top = start, bottom = final), `04_silhouette_overlay.png`, `05_zone_map.png`. Machine-readable: `checks.json`, `data/audit_final.json`, `data/metrics_start.json`, `data/metrics_final.json`.

## Known limits (honest)
- **Wrist rings are fixed** (the hand weld belongs to the limbs zone). The plate's hand sits ≈ 3 cm *in front of* the knee-centre plane; ours stays at y ≈ 0, so the forearm lean is only ≈ 2/3 of the plate's. Hand-off: shift the hands ~ −0.03 m (y) in a hands pass, then re-run the wrist-ring weld.
- Because the seam verts are pinned, the arm axis hang falls from +30 mm (z 1.08) to ≈ +10 mm at the armpit (z 1.2) instead of the plate's ≈ +40 mm. Fixing that needs torso-seam verts to move (outside this zone).
- The relief gate measures displacement with the rigid slice shift removed; it includes the shoulder blend, so read it as "form was added", not as a muscle-detail score.
- The plate itself is smooth and low-resolution (arm ≈ 28 px wide); the amplitudes are a design choice consistent with the plate's elbow break and soft forearm, not read from the pixels.
- Back-view arm XOR (21 %) is dominated by plate asymmetry (plate back views are 20 % off their own mean); front arm XOR improved 11.7 -> 9.9 %.
- Left/right use the same displacement functions; wrist rings differ (R z 0.8456, L 0.8726) as in the start file.

## Reproduce / merge
- `python3 arm_model.py out.npy` (needs `data/start_cur.npz`, `data/zones_cur.npz`; parameters in `DEF`), then `blender -b start/start_torso_plus_limbs.blend --python apply_blend.py -- out.npy out.blend`; `bash full.sh <tag>` also renders metrics.
- Merge into other blends: `export/merge_arms_delta.py` (+ `export/arms_delta.npz`), see `export/README_MERGE.md`. Tested: onto the limbs blend, the torso candidate and ArtDir `HeroBase_Female.blend` (22,444-vert order) -> 1,592/1,592 applied, 0 conflicts.
