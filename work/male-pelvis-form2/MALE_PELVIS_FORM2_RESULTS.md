# MALE_PELVIS_FORM2 — results (candidate FINAL6)

**GATE: MALE_PELVIS_FORM2 PASS** (hard gates measured; the three EYE lines are my reading of the proofs, Adnan's sign-off still needed).
**STAGED, NOT INSTALLED.** ArtDir was not touched. Install only after Adnan's OK (`install_f2.sh`, SHA-guarded patch install; not run).

## Files
| item | value |
|---|---|
| Start blend (chat-9) | `9bfd788a1a2a10bb6c982820e9b2c65889ef7280448f3d65ed39dcd8634d91ba`, FBX `69428fc8…` |
| Candidate blend | `export/candidate_FINAL6.blend` `9f8c6de1e531bb0005a5c51ab80538a2d3cc1ed64b4afa327a2228ce28b6a7f7` |
| Candidate FBX (Body_M+Face_M, `export_final.py`) | `export/candidate_FINAL6.fbx` `6dad29772e74d15fb992f49630fbee2f74e5fc9e252928710d8fd5268715ef20` |
| Delta (float32 patch, indices/base0/new) | `export/f2_delta.npz` `a01e7667637e62de364077601157bf405f9225db835f3a8596812deb80e1c0f5`, 3,007 verts |
| Params / positions | `data/P_FINAL6.json` `2e678d4a…`, `data/V_FINAL6.npy` `55f54834…` |
| ArtDir at stage time | blend `fd04bc286f688b03ea25fbb57e1242bf2f5976c2dc7bbcdfdb0f68b622ab2347`, FBX `a36b2010…` |
| Staged merge on that ArtDir | `export/merged_fd04bc28.blend` `a64c8f30…`, `.fbx` `0c54d9da…`; `export/install_verify_f2.json` PASS (only the 3,007 delta verts differ; topology, Face_M, groups, materials, objects, cameras identical) |
| Proofs / checks | `proof/` (P1–P14), `checks.json`, `export/audit_FINAL6.json`, `export/form3_gate.json`, `export/slot_widths_FINAL6.json` |
| Earlier iterations | `archive_FINAL3/`, `archive_FINAL4/`, `archive_FINAL5/` (each with delta, proofs, checks) |

ArtDir moved three times while I worked (`9bfd788a` -> `0f742186` -> `8a9ad64b` -> `fd04bc28`): head/face chat only (3,066 body verts, z 1.433–1.598). My 3,007 delta verts were at start positions every time, so the merge applies cleanly. Unity copy not refreshed; the topology is unchanged (66,158 body tris).

## Gates
| gate | result | evidence |
|---|---|---|
| ZONE_OUTSIDE = 0 | PASS | zones PELVIS z .77–1.07 and LEG_TOP z .705–.77 (both \|x\| <= .22, original positions); 0 moved outside; head/arms/hands/calves/feet 0; max move at the zone edge band 1.75 mm |
| TOPOLOGY_IDENTICAL | PASS | 33,196 verts / 33,484 faces / 66,158 tris unchanged, positions only, no densify |
| NO_SELF_INTERSECT / NaN | PASS | NaN 0, flipped faces 0, degenerate 0, new self-intersections 0 (6 pre-existing), dihedral p99 26.4° (start 30.9°), max 40.0°, new_sharp 0 |
| SIL bald front/back <= 5.0 % | PASS | candidate 4.294 / 4.971; staged on current ArtDir 4.297 / 4.975; ArtDir without my delta 4.130 / 4.751; chat-9 4.127 / 4.747 |
| GLUTE_LOBES_EYE | PASS (author read, caveats below) | P1, P3, P3b, P4, P4b, P5, P13 |
| FOLD_PLATE_EYE | PASS (author read) | keyhole apex .772 -> .747 (plate luminance .748); soft underbutt curve; P1, P3, P4, P5, P10, P14 |
| GROIN_EYE | PASS (author read) | soft short V + mound, tapered slot, no dark flat bar; P2, P8, P8b |

The SIL rise vs chat-9 (+0.17 front, +0.22 back) is intentional: the plate masks count the shadowed crotch as background, so a slot that follows the plate's real slot costs XOR. Margin to 5.0 is 0.03.

## What changed vs chat-9's five rejection reasons (model `f2_model2.py`, v2; params in `data/P_FINAL6.json`)
1. **Lobes too soft/flat.** Side contour pinned to the plate sub-pixel contour (mean abs error 1.66 mm over z .76–.95, max 3.7) with a documented +3–4 mm boldness bias at the lobe bellies (z .82–.86); flank fullness fixes the 3/4 outline (P9).
2. **Upper shelf / M-dip.** The cleft is an explicit target valley (rounded V, no cusp, no flat floor; depth 13–15 mm at z .80–.82, 8 mm at .86, 2.6 mm at .90; chat-9 was a flat-floored trench 25 mm deep at .80 and a dome above .88). Shelf smoothing kept. Horizontal sections above z .94 are single smooth arcs (P11).
3. **Fold ~3 cm too high.** Roof grab lowers the see-through apex .772 -> .747 (back and front); documented leg-top strip moves (below).
4. **Back-glute band-pass.** Not improved, see Honest notes.
5. **Front groin.** Mound + converging V crease + front pinch; the slot now tapers to a rounded top. See-through slot width at z .72 / .735 / .745: 40 / 34 / 22 mm (start 50 / 51 / 52; plate back 38 / 28 / 17, plate front 40 / 37 / 34).
Soft-plastic: the crease is A 9 mm / sigma 30 mm, `gapsmooth` 220 iterations rounds the keyhole lip, no striations.

Term order: roof, arch, slot, fpinch, cleft, shelf, lateral (+dn), pin, trim, crease, mound, seam, fseam, gapsmooth, displacement-field smoothing, hard zone mask. Compared with FINAL3 (first complete version): new `slot` term (k .35), cleft scale 1.8 -> 1.1 with rounded V, crease A 14 -> 9 / sigma .018 -> .030, gapsmooth 40 -> 220 iterations.

## Moves (documented, positions only)
3,007 verts moved: 2,376 in PELVIS, 631 in LEG_TOP (z .705–.77); max 31.2 mm (roof drop), 190 verts below z .735 up to 10.7 mm (slot taper, inner thighs); nothing below z .705.

## Numbers
- Torso FORM3 gate (clay band-pass r, \|x\| < .12): mean .535 (start .505); back_pelvis .240 (.197), back_abdomen .376 (.331), front_pelvis .872 (.784). FINAL3 had regressed back_pelvis to .160; the shallower, broader cleft fixed it.
- Custom normals: <= 0.027° in the pelvis zone (candidate and staged merge). `normals_np.py` over its wider zone (includes the nape) shows p95 6.7° / max 19.4°; the unmodified current ArtDir blend has exactly the same values, so that is pre-existing (head chat), not this change.

## Honest notes
- **Eye gates are my reading.** GROIN and FOLD look plate-like. GLUTE_LOBES: soft, readable twin lobes, no shelf, soft V; the plate still "pops" more at full-body scale (P13) under its own top light, which the Unity-like rig cannot reproduce. This is the line most likely to be contested.
- **Band-pass correlation with the plate is lower than chat-9 in the glute boxes.** `metric2.py` (clay rig), back_lowglute: DoG 3/12 .59 -> .36, 5/20 .77 -> .63; back_pelvis 3/12 .59 -> .43; front_groin 3/12 .88 -> .79; 3/4 panels unchanged. `relitcorr.py` (rig / top-light): lowglute 5/20 .64 -> .42 / .70 -> .56. Ablation: the roof lowering needed for the fold causes most of it (roof off recovers .47/.63), not the cleft or crease. The plate lighting is soft with strong occlusion; a sun-only relit pass blacks out the overhang, so shading metrics under the lobes are unreliable. Plate cleft contrast (centre vs lobe, top-lit) is 13 / 9.8 / 7.2 / 4.0 / 2.0 % at z .82–.90; FINAL6 is 8.5 / 13.5 / 8.5 / 6.5 / 2.7 % (FINAL3 was ~1.5–2x too deep).
- The "lumbar band" in enhanced renders is the plate's own lordotic hollow (rear contour error <= 1.5 mm at z .94–1.07), not a mesh shelf.
- Plates disagree: slot apex back .748 / front .762 (sheets .724 / .748); thigh rear contour z .70–.745 is 62.5 mm in the plate vs 68 mm in the mesh (legs chat's zone, untouched).
- A small rounded step remains where the far thigh's rear-inner shoulder meets the keyhole lip in the rear 3/4 (P4 bl, zoom `r/diag/`). Arch/trim ablations do not change it; it is not a spike or fold.
- The fold groove at x = 90 mm is 4 mm deep (thigh 63 mm -> 59 mm at z .75), shallower than FINAL3 (6.6 mm).
- Stretched quads (2–3x) around the keyhole after the roof drop; topology is fixed, so smoothing hides it.

## Proofs
P1 back/3q/side plate | chat-9 | FORM2; P2 front/groin; P3 / P3b registered back close-up plain / enhanced; P4 / P4b 3q close-ups; P5 plate-like top-light relit; P6 / P6b side contour vs plate (sub-pixel); P7 side; P8 / P8b front groin; P9 3/4 silhouette overlay; P10 / P10b gap sections; P11 / P11b coronal rear profiles; P12 skin look; P13 full body 3q back; P14 sagittal profiles vs plate.

## Install / rollback / rebuild
- Install (needs Adnan's OK): `./install_f2.sh` (lock, backup of ArtDir blend + FBX to `baseline/pre_install_f2_*`, re-merge on the then-current ArtDir, verify, FBX via `export_final.py`, atomic move). Then refresh the Unity copy and run `HeroBaseMaleFormProof` (no `-nographics`).
- Rollback: restore `baseline/pre_install_f2_<sha8>.blend` / `.fbx`.
- Rebuild: `python3 f2_model2.py data/P_FINAL6.json <tag>`, then `python3 finalize_f2.py <tag> <out>` (mask + float32 + delta). Variants: `python3 mkv2.py --base data/P_FINAL6.json 'tag={json}'`. Proofs: `./make_proofs.sh FINAL6`. System python3 for scripts; Blender python needs `PYTHONPATH=../male-micro1i/pylib`.
