# MALE_PELVIS_FORM3 — results (candidate FORM3 = `data/P_F3B.json`)

**GATE: MALE_PELVIS_FORM3 PASS** (every hard gate is measured; the two visual lines — no point/bulge/wedge, round peach — are my reading of the proofs, Adnan's sign-off is still needed).
**STAGED, NOT INSTALLED.** `ArtDir` was not touched (blend still `fd04bc28…`, FBX `a36b2010…`). Install only after Adnan's OK (`install_f3.sh`, SHA-guarded patch install; not run). Unity copy not refreshed (topology unchanged, 66,158 body tris).

## What the "pointed part" was, and what happened to it
FORM2 lowered the leg-gap roof with a narrow V-shaped bell (cos² half-width 80 mm, up to 31 mm, steep fades front and rear) and then pinched the front walls with an inverted x-profile (k 0.65). That left a **funnel tip hanging at the top of the slot**: at the front it pushed the lip 6–13 mm *forward* of chat-9 (the nub / "genital point", with a bow-tie of pinched flaps around it); at the back the same tip was a **V wedge hanging between the cheeks** (the "back penis"); at the sides it left a hook under the cheek; from below it was an X of pinched creases. In `proof/P09` the bright wedge pointing down into the gap is exactly that feature (chat-9 had a milder spike, FORM2 a full V). In FORM3 the area between the cheeks is a smooth round arch (P09, P09b, P20).

## Files
| item | value |
|---|---|
| Start (chat-9 = ArtDir geometry in the zone) | `baseline/HeroBase_Male_Silhouette.blend` `9bfd788a1a2a10bb6c982820e9b2c65889ef7280448f3d65ed39dcd8634d91ba` |
| FORM2 candidate (verified before work) | `export/candidate_FORM2_FINAL6.blend` `9f8c6de1e531bb0005a5c51ab80538a2d3cc1ed64b4afa327a2228ce28b6a7f7` (= SHA given in the brief) |
| FORM3 candidate blend (start + delta) | `export/candidate_FORM3.blend` `8e341b741d8a78215cbf0926fc96760fc0c4b47bc4f27dc80cb5f91c41367e0d` |
| FORM3 candidate FBX (Body_M + Face_M, `export_final.py`) | `export/candidate_FORM3.fbx` `e7ac3ccf34d7e5d808c55ee02bca8784f0170995c9f2fc6b3580a8aeb6659fbb` |
| Delta (float32 patch: indices / base0 / new) | `export/f3_delta.npz` `4aaceb8777d8391c3e4c0380eecd8cc1489a5cd2cc81ea58601f6c1b03095468`, 2,655 verts (self-contained: includes everything FORM2 did, so FORM2 need not be installed first) |
| Params / positions | `data/P_F3B.json` `122d9bf6…`, `data/V_FORM3.npy` `c5338d29…` (rebuild is bit-exact, tested) |
| ArtDir at stage time | blend `fd04bc286f688b03ea25fbb57e1242bf2f5976c2dc7bbcdfdb0f68b622ab2347`, FBX `a36b2010…` (unchanged) |
| **Staged merge on that ArtDir** | `export/merged_fd04bc28.blend` `d6c4dcfb1150853a8802a8dc7501aa64066adb8b2734c14a4d6ed8e82dada781`, `.fbx` `6ecb41d35392c691c444b0aab7dd32ba00f64ea12ee02c1dcc33bd64f7168f4a`; `export/install_verify_f3.json` PASS (only the 2,655 delta verts differ; topology, Face_M, groups, materials, objects, cameras identical) |
| Proofs / checks | `proof/` (P01–P20), `checks.json`, `export/audit_FORM3.json`, `export/f3_zone_report.json`, `export/normals_staged_f3.json` |

## Gates (numbers in `checks.json`, table in `proof/P18_gate_table.png`)
| gate | result | evidence |
|---|---|---|
| ZONE_OUTSIDE = 0 | PASS | PELVIS z .77–1.07 and LEG_TOP z .705–.77 (both \|x\| ≤ .22, original positions); 0 moved outside; head / arms / hands / calves / feet 0; max move in the zone-edge band 0.76 mm |
| TOPOLOGY_IDENTICAL | PASS | 33,196 verts / 33,484 faces / 66,158 tris, positions only |
| SIL bald front / back ≤ 5.0 % | PASS | **4.289 / 4.952** (chat-9 4.127 / 4.747, FORM2 4.294 / 4.971; margin 0.048 on the back; left/right 9.04 / 9.40, info only) |
| NO_SELF_INTERSECT / NaN | PASS | NaN 0, flipped faces 0, degenerate 0, new self-intersections 0 (6 pre-existing), min face-normal dot .847; dihedral p99 **17.7°** (chat-9 30.9, FORM2 26.4), max 33.9° |
| FRONT_SMOOTH_MOUND | PASS (numeric measured; eye = my reading, P01/P03/P08/P10/P20) | front reach vs chat-9 **−0.24 mm** (rule ≥ −1.0; FORM2 −6.21 FAIL); front dihedral max **21.0°** (≤ 35; FORM2 40.0 FAIL); front lip 18.4 mm above the lowest roof point (≥ 0: nothing hangs) |
| BUTT_ROUND_PEACH | PASS (numeric measured; eye = my reading, P02/P05/P09/P12/P16/P20) | rear dihedral max **30.4°** (≤ 35; FORM2 39.9 FAIL); lobe outline turn ≤ 13.7° per 4 mm (≤ 20) and convex outside the cleft; slot arch radius **12.1 mm** (≥ 9); fold V-ness **−0.13** (U-shaped; FORM2 0.59 = V, FAIL); rear lip 9.3 mm above the lowest roof point (≥ 0) |

Gate definitions are in `gate_metrics.py` (header). Two crude early metrics (front-bump, nub-excess) were dropped: chat-9 itself fails them, so they cannot separate the cases.

## What changed vs FORM2 (model `f3_model.py`, positions only; params in `data/P_F3B.json`)
1. **Roof sag by table along the tunnel** (C1 cosine-eased, mm at y −.30…+.10: 0 / 6 / 12 / 19 / 24 / 26 / 26 / 22 / 8 / 0): lowest in the middle, both lips higher (front lip 18 mm, rear lip 9 mm above the lowest point) so nothing hangs. x-profile is a bell with no flat top (`wx0` 0, `wx1` .115) → the fold under the cheeks is a **U**, not a V. The sag stops right behind the rear lip so the lobe bodies stay registered with the plate (FORM2's trap).
2. **Removed**: front pinch (inverted x-profile), mound bump, V crease (A 9 mm), seam / fseam / Taubin gapsmooth. Arch / slot pinch halved (k .15 / .25). Slot at z .72 / .735 / .745: 44 / 37 / 25 mm, apex .750 front / .749 back (FORM2 41 / 35 / 23, .747; plate front 40 / 37 / 34 at .762, plate back 38 / 28 / 17 at .748).
3. **Thin-plate fairing** (new, `fair.py`): implicit bi-Laplacian solve over the keyhole neighbourhood (669 free vertices, outside ring fixed, τ 40). It rounds the lips, removes creases and flaps (max dihedral 68° → 34°) and evens the quad spacing — Taubin could not do this (it hooked the lip).
4. **Scoop** (S 10 mm, σ 35 × 30 mm at z .79): the rear lip / lower cleft recedes forward into the gap, so the lower end of the cleft is a concave scoop instead of a bulging lip.
5. **Cleft** shallower above z .82 (D mm at z .84 / .86 / .88: 6.5 / 3.5 / 1.5, FORM2 8.5 / 6 / 3.8) — the plate's cleft is subtle. Valley is a rounded bowl (`eps` .45).
6. **Soft U crease** under the cheeks (A 3 mm, parabola `k2` 1.4, σ 14 mm; FORM2 had a 9 mm V groove).
7. Kept from FORM2: lateral fullness, shelf smoothing, rear contour pin / trim (incl. its +3–4 mm boldness bias at the belly), displacement smoothing.

## Moves (documented, positions only)
2,655 verts moved (2,150 PELVIS + 505 LEG_TOP), mean 4.7 mm, max 26.0 mm (roof sag, dz 25.9 / dy 14.2 / dx 10.0); 175 verts below z .735 up to 8.1 mm (inner thigh tops); nothing below z .705.

## Numbers
- **Slot / apex**: see above; plates disagree (back .748, front .762, sheets .724 / .748), FORM3 sits between at .749–.750.
- **Rear contour vs plate** (sections, z .77–.95): mean abs 1.77 mm, max 4.93 mm at the rim z .78 (soft rim 5 mm inside the plate's crisp overhang), belly +3.9 mm (documented boldness bias, unchanged). Sub-pixel plot z .78–.94: chat-9 1.5 / FORM2 1.9 / FORM3 2.1 mm mean (`proof/P13`).
- **Torso FORM3 gate (band-pass r, clay)**: mean .519 (chat-9 .505, FORM2 .535); front_pelvis .856 (.784 / .872); back_abdomen .380; **back_pelvis .156 (.197 / .240)**. Multi-scale on the mid-cheek band z .80–.90: fine .156 (.197 / .240), medium **.510** (.415 / .418), coarse **.843** (.695 / .687) — the dome is closer to the plate, the fine detail (cleft groove, V crease) correlates less because those features were removed or softened on purpose.
- **Custom normals**: pelvis zone ≤ 0.03° (blend), staged FBX re-import matches the blend; the wider `normals_np.py` zone (includes the nape) shows p95 6.7° / max 19.4°, identical to the unmodified ArtDir (head chat), not this change.

## Honest notes
- **Eye lines are my reading.** I judged the proofs against the plate, chat-9 and FORM2; Adnan's sign-off is pending. Under hard top light the lowered centre still shows a soft bright rounded dome between darker side bands (the plate gets a dark gradient there from its own AO, which a sun-only render cannot give); there is no wedge, spike or hanging lobe in any angle (P20 ring, level and from below).
- The plate's deep shading valley under the cheeks (z ≈ .738) vs ours (≈ .78) is shadow / AO on the thigh below the overhang: the side silhouette corner matches (≈ .765) and the 3/4 outline overlay matches (P14); I did not move the fold down.
- SIL margin on the back is 0.048 %. The slot is wider at the top than the plate's back view (25 vs 17 mm at .745) on purpose: round arch, and it costs less silhouette XOR.
- The roof now slopes up toward the front lip (18 mm), so from the front a soft dark band of the sloping roof remains above the slot (the plate has a smaller one).
- Thigh rear contour z .70–.75 is 62 mm in the plate vs 68 mm in the mesh (legs zone, untouched, same as in FORM2).
- Fairing slightly shaves the lobe bellies where it overlaps (z ≤ .83, \|x\| < .10); the pin / trim run before it, residual error is in the contour numbers above.

## Proofs (all plate | FORM2 | FORM3 unless noted)
P01 front groin (front, q_fl, q_fr) · P02 back / 3/4 / side · P03 / P03b front close-ups plain / enhanced · P04 / P04b registered back close-up · P05 / P05b rear 3/4 close-ups · P06 side close-up · P07 top-lit relight · P08 keyhole close-ups (chat-9 / FORM2 / FORM3) · P09 / P09b between the cheeks, normal and top light · P10 low-angle orbit · P11 centre-line sagittal sections · P12 / P12b lobe and tunnel axial sections · P13 / P13b side contour vs plate (sub-pixel) · P14 3/4 silhouette overlay · P15 mesh wireframe at the keyhole · P16 full body 3/4-back · P18 gate table · P19 skin look · P20 360° rings (level and from below).

## Install / rollback / rebuild
- Install (needs Adnan's OK): `./install_f3.sh` (lock, backup of ArtDir blend + FBX to `baseline/pre_install_f3_*`, re-merge on the then-current ArtDir with the zone guard, verify, FBX via `export_final.py`, atomic move). Then refresh the Unity copy and run `HeroBaseMaleFormProof` (no `-nographics`).
- Rollback: restore `baseline/pre_install_f3_<sha8>.blend` / `.fbx`.
- Stage again on a newer ArtDir: `./stage_f3.sh`.
- Rebuild: `python3 f3_model.py data/P_F3B.json F3B` → `python3 finalize_f3.py F3B FORM3` → `blender -b --python make_blend.py -- baseline/HeroBase_Male_Silhouette.blend data/V_FORM3.npy export/candidate_FORM3.blend` → `audit_f3.py … --selfx`. Evaluate: `python3 evalv.py <tag>`, `python3 gate_metrics.py <tag>`, proofs `python3 proofs_f3.py`, checks `python3 gates_f3.py`. System python3 for scripts; Blender needs `PYTHONPATH=../male-micro1i/pylib`.
