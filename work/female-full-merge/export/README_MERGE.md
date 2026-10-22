# FEMALE FULL MODEL - staged merge (FORM5 torso + arms + hands + MicroF3 head) on the hands base

**STAGED ONLY. Nothing installed. ArtDir `HeroBase_Female.blend` SHA `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` before AND after. No Unity, no clothes, no male.**
**This is a shape ASSEMBLY, not a form pass: nothing here claims the body matches the plate.** Proofs are studio clay light, not plate-matched.

Result: **GATE: FEMALE_FULL_MERGE FAIL - NECK_WELD** (NECK_STEP_MM 7.92 > 2.0). Two more gates are flagged because their *literal* wording is not met although nothing is broken (VMAP_CLEAN, TOPOLOGY - see "Gates"). Staged blend delivered anyway.

## Files (all under `work/female-full-merge/export/`)
| file | SHA-256 |
|---|---|
| `HeroBase_Female_FULL_STAGED.blend` (Body_F 22,123 verts / 43,990 tris + Face_F + hidden Hair_F; FBX/Unity scale 1 m, height 1.7044 m) | `a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1` |
| `HeroBase_Female_FULL_STAGED.fbx` (Body_F + Face_F, F3's exporter flags, scale 1, -Z forward / Y up, custom normals; `.fbm` = texture copy) | `f49c1758a1be87a572389e292508126cabbccdcff47e12810e08d014e3db0a07` (FBX embeds a timestamp: its SHA changes per export) |
| `full_merge_delta.npz` (delta from the hands base, see below) | `9baf67d44cb36a72bb496ecd0b31b4ced10327751481fdd1df68ac4f62df6d8a` |
| `merge_full_delta.py` (replay: hands base + delta + F3 blend -> this blend, bit-identical, verified) | `eb0c0ae5afef2c15edc30253993590ffdf87cfce4773b996cba0b8c60c8f0836` |
| `vmaps_full_merge.npz` (all index maps, see "The vmap") | `383b68ad923e44f83b71c75b0039564be68508ec17a5a21f1f815381e53e2615` |
| `export_report.json` (FBX round trip), `checks/*.json` (every number quoted here) | |
Proofs: `proof/FULL_FIGURE_5VIEWS.png`, `proof/CLOSEUPS_SHEET.png`, **`proof/SEAMS_SHEET.png`** (the one sheet that shows the seams), single images in `proof/raw/`. Gate table: `GATE_RESULTS.md`. Definitions fixed before measuring: `GATE_DEFS_preregistered.md` (+ one dated amendment).

## Inputs (SHA verified before any edit; copies in `start/`, read-only)
| piece | SHA-256 |
|---|---|
| BASE = hands candidate `work/female-hands-fingers/export/HeroBase_Female_hands_candidate.blend` (arms + chat-7 torso + hands; 23,247 verts, 46,402 tris) | `1149e620985248e546e2fab93eb19f447f1a5ae673d50a2525fcae5769529ff4` |
| TORSO = FORM5 `torso_form5_delta.npz` (4,540 moved, `cn_vertex_weight`) + stock `merge_torso_delta.py` (FORM5 candidate `7aa351d5...` used only to verify) | delta `f8dd0a57bbddd3c4a6ae1e0ceba41f990712a0bc8992249fb7b9f2db15e2618e` |
| HEAD = `HeroBase_Female_MicroF3_head_STAGED.blend` | `7d78b3a3f1224fe68d1f92665f5b3554eb25264bec803b9befdcaf5489e59e02` |
| ARMS (already in the base; arms candidate) | `573ab4431d83f8651936f0081ad3bda9c6890c56ee5dce3061140198c9455f0e` |
| chat-7 torso delta (superseded, used only to retire it) / limbs vertex map / arms delta / hands delta | see `data/start_sha256.txt` |

## The vmap (ArtDir -> base -> final)
* **ArtDir (22,444) -> hands base (23,247)**: the limbs chat's index map `work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz` (`base_to_final`), extended with the 828 appended hand verts. Checked against positions: 19,391 ArtDir verts map to a base vertex, 3,053 were removed by the limbs chat (old SDF hands/feet); 3,856 base verts have no ArtDir counterpart (3,028 limbs SDF hand/foot verts + the 828 appended hand verts, indices 22,419..23,246).
  The 7,352 mapped ArtDir verts that moved in the base are fully explained: chat-7 torso 3,317 + arms 1,592 + limbs legs 2,443 (0 unexplained). Map is injective; no FORM5 delta vertex shares its position with another base vertex (0 ambiguous).
* **base -> final**: retained base vertices keep their order (new index = old index minus the removed old-head vertices below it): 13,224 kept, 10,023 old-head vertices (z > 1.40545) removed with the 10,417 faces that touch them; F3's 8,899 head vertices are appended in F3 order (final idx >= 13,224); the 30 collar-ring vertices are base vertices (exact position match with F3's ring). Final 22,123 verts.
* All maps are in `vmaps_full_merge.npz`: `artdir_to_base`, `base_to_artdir`, `base_to_final`, `final_to_base`, `artdir_to_final`, `final_to_artdir`, `f3_to_final` (-1 = no counterpart).
* Torso delta applies only through the ArtDir->base map; it writes **0** vertices in 22,419..23,246 and 0 in the 1,326 reused hand-shell slots (guard in the replay script asserts it).

## What was done (3 steps, `export/merge_full_delta.py`)
1. **RETIRE chat 7's superseded torso.** The base carries chat 7's OLD torso (`arms candidate = limbs + chat-7 torso + arms`). FORM5's README: "apply exactly ONE of them (never stack)"; for an arms-candidate base it says the delta needs `--force`.
   **The literal stock script on this base gives 3,194 conflicts** (applied 1,346 of 4,540; `checks/s3_stock_merge_on_UNRETIRED_base_literal.txt`): every conflict is a vertex sitting exactly at chat 7's position (0 are arms/hands/limbs). I therefore set chat 7's 3,317 moved vertices back to the ArtDir original (guard: each must be bit-exactly at chat 7's position; chat 7 left the raw custom normals untouched, verified) and only then ran the **unmodified** stock `merge_torso_delta.py --vmap`: **4,540 applied, 0 conflicts, 0 missing, 13,131 custom-normal corners rescaled** (`checks/s3_stock_merge.txt`).
   Of chat 7's 3,317: 3,194 are overwritten by FORM5; **123 are FORM5 border-ring vertices (not in the delta, FORM5 pins them at the original): they moved back to the original by 0.000-2.455 mm** (the 69 at z > 1.3 moved <= 0.022 mm, the 54 at z <= 1.3 (armpit ring) <= 2.455 mm). Result: the merged torso zone (4,762 vertices) is **bit-identical to the FORM5 candidate** and raw custom normals equal the candidate's on all 19,532 compared corners.
   Alternative not taken (`--force`, residue kept): the displacement steps would not be worse (armpit 8.47 vs 9.42 mm) but the ring would sit up to 2.455 mm off FORM5's pinned position and the torso zone would not equal the FORM5 candidate. To get that variant drop the 123 residue indices from `c7_idx` in the delta.
2. **TORSO FORM5** (above). Positions only + the weighted code0 rescale of FORM5 (same arithmetic as the stock script; the replay is bit-identical to the stock-script output on every retained vertex, loop, UV, material index and raw normal - `REPLAY_EQUALS_STOCK_SCRIPT`).
3. **HEAD graft (zone replacement, not a position copy).** F3's head is NOT a position edit of the ArtDir head: F1 rebuilt everything above the 30-vertex collar ring (z 1.3965-1.4053) with a new topology (ArtDir 10,023 head verts -> F3 8,899 used head verts; F3 Body_F indices < 12,421 are the original lower body). A nearest-vertex transfer is impossible for a different topology, so the head zone was grafted: faces touching old-head vertices removed, F3's 8,578 head-zone faces (8,488 head + 90 collar-crossing) added and welded to the 30 base ring vertices. **F3's 12,421-vertex lower body was not copied** (it is the ArtDir original; it was only checked against). F3 head vertices, per-corner UVs, raw custom normals, materials and the 21 `LOOP_*` groups are copied bit-exactly (verified); `Face_F` (F3's face paint + eye shells and its 14 materials) is appended unchanged - without it the eye openings would be holes.
   * **460 orphan vertices of F3's Body_F are not carried** (no face, edge or group uses them; all sit inside the two eye openings). Not a form change.
   * Body_F material slots are now `Base_Grey_F, Skin_F` (as F3's Body_F); the old head-only materials (`Eye_White`, `Iris_Dark`, `Pupil`, `Brow`, `Mouth`, `Teeth`, `Lip_F`, `Ear_Shadow_F`) belonged to the removed head faces.
   * Custom normals are never cleared; raw INT16 codes are copied. Decoded normals at the 30 collar-ring vertices differ from F3's by <= 1.67 deg (cause not investigated; most likely the loop-normal-space reference depends on the mesh's loop/edge order); the retained lower loops at the ring decode differently from the OLD head's fan by up to 22 deg exactly as they do in F3's own assembly (21.8 deg there).

## Gates (details in `GATE_RESULTS.md`)
| gate | verdict | key numbers |
|---|---|---|
| BASE_SHA | PASS | `1149e620...` verified before edit (copy read-only, replay guard) |
| VMAP_CLEAN | **literal FAIL on the base as handed over, PASS as delivered** | stock script on the base: 3,194 conflicts (chat-7 old torso); after retiring it: 4,540 applied / 0 conflicts / 0 missing; writes on 22,419-23,246: 0; ambiguous matches 0 |
| HEAD_ZONE_ONLY | PASS | only F3's 8,578 head-zone faces taken; head verts/corners/UV/normals/materials bit-equal F3; lower body = base (not F3): 12,431 lower verts differ from F3's lower body, all explained (FORM5 4,540 + arms 1,592 + limbs legs 2,443 + new hand/limb verts 3,856) |
| ARMS_KEPT | PASS | 1,699 arm-zone verts and 107 pins: 0 changed vs the arms candidate; the "torso border pin" exception was not needed (only torso-zone ring verts moved) |
| LEGS_UNSCULPTED | PASS | 0 vertices moved below z 0.62; the only leg vertices that differ from the hands base are FORM5's documented LEG-TOP band (1,346 verts z .62-.795, all in the FORM5 delta) |
| SEAMS | reported (below) | positions 0.000 mm at every ring |
| **NECK_WELD** | **FAIL** | **NECK_STEP_MM = 7.92** (limit 2.0) |
| OPEN_FAILS_DISCLOSED | PASS | next section |
| TOPOLOGY | **literal FAIL (boundary count), merge-created PASS** | Body_F boundary edges 256 = F3's two eye openings (2 x 128), identical to F3's own Body_F, covered by Face_F; created by the merge: 0; non-manifold 0; winding inconsistencies 0; loose verts 0; connected components 1; hand-vs-hand 0, hand-vs-body 0 (hands base: 0); non-adjacent overlap pairs 32 = F3's own head pairs (32/32 identical by position; hands base had 3,053 in the old head), FORM5 added none (3,053 = base) |
| ARTDIR_UNCHANGED | PASS | `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` before and after |
| PROOFS | PASS | `proof/` |
| NOT_A_FORM_PASS | PASS | this merge does not claim plate fidelity |

## Seams (mm). Definitions fixed in `GATE_DEFS_preregistered.md` before measuring
POSITION_STEP = distance between a ring vertex in the merged mesh and where the other piece(s) expect it. DISPLACEMENT_STEP = FORM5's own SEAM_CLEAN convention (change of the edges that cross the ring vs the original); my numbers reproduce FORM5's reported 0.57 / 9.42 / 1.35.
| ring | POSITION_STEP | DISPLACEMENT_STEP | note |
|---|---|---|---|
| neck/shoulder border (FORM5, z 1.363-1.370) | 0.000 | 0.567 | FORM5 budget 1.0 |
| **collar ring (30 verts, z 1.3965-1.4053): F3 head <-> original neck** | 0.000 | **COLLAR_OFFSET 7.92** (row 1 max, mean 2.98); row 2 9.32, row 3 11.20, row 4 8.86 | head vertices vs the ORIGINAL ArtDir neck/head surface they replaced |
| armpit: FORM5 border / arm pins | 0.000 / 0.000 | torso side 9.415 (FORM5 budget 10); relative across border/pins 9.88 (mean 2.68) | arm side of the pins is the arms chat's own |
| wrist rings (36) | 0.000 | 0.000 merge-induced (forearm side vs ArtDir 0.498, the arms chat's) | merge touches neither side |
| leg-top floor ring (FORM5, 88 verts, z .62) | 0.000 | 1.353 | FORM5 budget 8 |
**NECK_STEP_MM = 7.92 -> NECK_WELD FAIL.** What it is: pins stay pins (0.000), but above the collar ring the F3 head piece's neck column leaves the original neck: its first 60 vertices sit 2.98 mm (mean) / 7.92 mm (max) from the old surface, up to 11.2 mm by row 3. In the neck contour the front line (min y) is -48.7 mm at z 1.405 vs the original -45.9, and -46.0 vs -34.8 at z 1.425; the front-contour slope changes by 26.6 deg across the ring (original 7.7 deg); the dihedral across ring edges reaches 52.4 deg (original 28.2). The wire view (`proof/raw/38_wire_neck_side.png`) shows a density jump at the ring (coarse collar ring -> finer head grid, with transition triangles). **Verified: every vertex above z 1.372 is exactly an F3 vertex (9,060 of 9,060 used ones; F3's other 460 are the orphans) and the 133 neck-band faces between z 1.37 and the collar are an identical multiset to F3's, so this is exactly the weld F3's own assembly on ArtDir has; it is not caused by FORM5, arms or hands. Nothing was moved to reduce it** (no chest, jaw or neck edit); FORM5's neck-base ring is still ~30 mm in front of the plate neck (its hand-off), F3 did not slim the neck (collar ring and everything below are the original). Cause of the departure is not verified here (F1's notes say the neck column comes from a plate-silhouette loft pinned to the collar ring).
The alternative classification of the FORM5 border (z-based) gives the same steps (0.567 / 9.415 / 1.353), so the verdict does not depend on it.

## OPEN failures carried (not fixed here, not hidden)
* **FORM5 BUST side fill: FAIL.** The merge shows it: flat flank / small mound in the side views (`proof/raw/20_bust_side.png`, `19_bust_3q.png`).
* **FORM5 UNDERBUTT crease: FAIL.** Wide soft dark band with the slit-top cusp (`proof/raw/17_underbutt_back.png`, `18_underbutt_3q.png`); clay thigh streaks are FORM5's own (its notes).
* **Neck weld** above (also: FORM5 neck-base ring ~30 mm in front of the plate neck; the head chat was supposed to slim it and did not, so there is no slimming to reconcile).
* Hands: 51,362 tris with hair on the hands base (46,402 body), disclosed, not densified.
* F3's own notes carry over (jaw profile luminance step, flat lip paint, thin streak at the neck/under-chin junction; F3 head overlaps 32 non-adjacent triangle pairs of its own; Hair_F is the old hair, hidden, not refit to F3's head).
* Triangle counts: Body_F 43,990 (hands base 46,402); Body+Face_F 50,042; Body+Hair 48,950; Body+Face_F+Hair 55,002. Against AGENTS.md's 35-50k guide: Body+Face_F is 42 over, Body+Hair under; disclosed, nothing densified or decimated. Unity `ExpectedTriangles` was not touched (would be 43,990 + 6,052).

## Verified (all in `checks/`)
* Replay: re-running `merge_full_delta.py` from the hands base reproduces this blend **bit-identically** (15 Body_F arrays incl. vertex groups and decoded normals, 14 Face_F arrays).
* FBX round trip: Body_F 22,123 verts / 43,990 tris / height 1.7044 m, max position error 0.0003 mm; shading normals of all 91,052 Body_F loops max 0.029 deg (0 > 1 deg); Face_F max 0.056 deg.
* Untouched by the merge (compared with the hands base): Hair_F (vertex + topology hash identical), plates, lights, camera, scene units; Face_F identical to F3's (positions, topology, normals, gaps to the skin).
* Height 1.7044 m (guide 1.65-1.75).

## Reproduce
```
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup start/base_hands_candidate.blend --python export/merge_full_delta.py -- export/full_merge_delta.npz start/F3_head_STAGED.blend out.blend report.json
# delta from raw sources: ./py.sh tools/make_full_delta.py   (needs data/*.npz dumps made by tools/dump_obj.py; stage 1-3 evidence: tools/s1_vmap.py, s2_retire_c7.py, stock merge_torso_delta.py)
# verification: tools/verify_full.py, verify_seams.py, verify_bvh.py (inside Blender), verify_neck.py, verify_ring_classes.py, verify_force_variant.py
```
