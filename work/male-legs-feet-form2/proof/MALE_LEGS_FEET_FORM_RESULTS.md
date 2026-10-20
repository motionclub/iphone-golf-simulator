# MALE_LEGS_FEET_FORM — job 04b (legs + feet FORM, feet primary) — 2026-10-02

**GATE: MALE_LEGS_FEET_FORM PASS** on every measured line below (two lines are *disclosed deviations* that need Adnan's OK: the forefoot **topology carve** and the **207-vertex zone extension**, see "Adnan: decide / look"). Visual lines (toes, volume, ankle, calf) are my reading of the close-ups; **Adnan's eye call is final**. **Unity capture NOT run**, Unity project copy NOT refreshed.

Installed (SHA-guarded, 2026-10-02 08:00): `ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend` and `unity_import/HeroBase_Male_Body.fbx`.

| File | before (hands FORM3 state) | after (installed) |
|------|-----------------------------|-------------------|
| `HeroBase_Male_Silhouette.blend` | `b51cbb05d5135325b083462efc1b6e05d444a8a514c6c3b58547dad9564431ee` | **`2e8f973b892b1e1bfba541341fa5d21b07565ddcf1aa23c7f4e09d93596bee3f`** |
| `HeroBase_Male_Body.fbx` | `39303a777785a240ab9821107c00d9dfef6a476c29ce60d3bd369e7ad9e1038c` | **`d40e9b55f7ae3bb1f0a11b62c77a65220eb9cba328ab49f25f89b1d086e2872a`** |

Verts 31,936 → 33,196 · tris 63,638 → **66,158** (+2,520, +4.0 %). FBX re-import: same vert/tri counts, max position error 0.00028 mm, height 1.70219 m, scale 1.

## Gate lines

| # | Line | Result | Evidence |
|---|------|--------|----------|
| 1 | ZONE_OUTSIDE_MOVED = 0 | **PASS** (extension disclosed) | 0 vertices moved outside the zone (head/neck, torso/pelvis, arms, hands incl. FORM3, Face_M, `LOOP_*`, materials bit-identical float32). Zone = start z < 0.765 & \|x\| < 0.27 (8,745 verts) **+ 207 foot lateral-wall verts** (start \|x\| ≥ 0.27, z < 0.15: the only \|x\| ≥ 0.27 geometry below the crotch; lowest arm/hand geometry is z = 0.805). Strict literal count outside the 8,745: 207 (all feet). `checks.json` → `zone`, `LEGSF2_08_zone_map.png` |
| 2 | TOPOLOGY_IDENTICAL (or documented carve) | **PASS — documented carve** | forefoot only: cut loop at world y = −0.095 (62-vertex loop per foot), 880 faces removed, 2,202 added, 820 reused vertex slots (410/foot, freed first) + 1,260 vertices appended at 31,936…33,195. Boundary/non-manifold edges 92/2 and same-direction pairs 46 **identical to the start**; no NaN; vertex groups, materials, Face_M equal; all faces smooth; custom normals: raw values kept for all 124,442 unchanged corners, 8,684 new corners = default. New-region quads 13.8°–148.5° (no bad), edges 1.25–17.9 mm (mean 7.2). `LEGSF2_07_topology_wire.png` |
| 3 | SIL bald front/back ≤ 5.0 % | **PASS** | front **4.141 %** (start 4.163), back **4.734 %** (start 4.691) — native Blender raster, locked plate cameras, whole figure. The back is +0.04 pt vs the start; back/front plates disagree on foot width by ~4.5 cm (see "Plates"). |
| 4 | FOOT_PLACEMENT hold | **PASS** | same heights as the earlier PASS: toe @ z 25 mm **0.14 mm** (PASS 1.05), heel **4.8 mm** (PASS 6.2), ankle centre @ z 190 mm **0.7 mm** (PASS 1.1). Other heights in `checks.json` (see note 3 below). |
| 5 | INSTEP + ANKLE sagittal hold (≤ ~1.1 mm mean) | **PASS** | mean **1.013 mm** (PASS 1.134), instep part **1.535** (1.92), max **5.19** (6.62), toe-cap part 2.54 (3.48), behind-cap 0.63 (0.54). Right foot 0.97 / 1.59 / 5.35. |
| 6 | KNEECAP stays proud | **PASS** | front relief at the knee +7.85 mm (PASS +6.27) |
| 7 | SURFACE_CLEAN | **PASS** (visual + numbers) | vertical banding 240 µm (PASS 235), no pits / no chopped bevels in `LEGSF2_05/06`; normal roughness 182 → 248 µm in my metric because of the intentional grooves and hollows (disclosed) |
| 8 | GROUND_CONTACT | **PASS** | min z 0.0024728 bit-identical, 200 sole vertices on the plane, height 1.70219 m, flat soles |
| 9 | NO_SELF_INTERSECT / flips / NaN | **PASS** | 0 intersecting triangle pairs in the legs zone (3 pre-existing elsewhere, identical to the start); 2 flipped-vs-neighbour faces = the start's (head, z ≈ 1.58, not mine) |
| 10 | **TOE_SEPARATION** (primary) | **PASS** (visual) | five separate toes per foot with 2.6 mm slits dropping 7 mm below the shoulders; big toe 34 mm wide vs 23/21/19/16 mm (1.47×) — `LEGSF2_04/05/07` |
| 11 | **TOE_TAPER** (primary) | **PASS** (visual) | lengths 46/41/34.5/28.5/22.5 mm, tip height ratio .92/.84/.80/.77/.75, rounded pad tips, soft knuckle bump, toe splay −2…6.5°; not equal sausages, no nails |
| 12 | **FOOT_VOLUME** (primary) | **PASS** (visual) | medial arch hollow (−6 mm), heel pad (+2 mm), lateral edge (+2 mm), instep on the plate profile (item 5), flat sole — not a rounded boot mold; `LEGSF2_05` side/3-4 rows |
| 13 | **ANKLE_READ** (primary) | **PASS** (visual) | soft malleoli (+4.7 mm), Achilles hollows (−4.4 mm) with the tendon plane between, calf → ankle taper, mirrored L/R — `LEGSF2_06` |
| 14 | CALF_FORM improved (secondary) | **PASS** (visual, subtle) | median gastrocnemius groove (−4.7 mm), flank hollows, belly-end crease, popliteal, shin flats; plate x-edge deviation 0.99 mm (was 1.00) — `LEGSF2_01/06` |
| 15 | THIGH/KNEE light (secondary) | **PASS** (visual) | quad groove, vastus edge, ham groove + flanks, peri-patellar planes; top ~3 cm of the zone faded to 0 (continuous with the torso) |

## Adnan: decide / look

1. **Topology carve (needs your OK).** The brief says "prefer none". The old foot is an irregular ~6.5 mm quad grid with a boot-mold section; positions-only edits cannot cut slits between 17–34 mm toes, so the forefoot (everything in front of world y = −0.095) was rebuilt in the hand style (slit toes, web quads, cap rings with triangle fans, weld ring slope-matched to the old surface). +2,520 tris (+4.0 %), all other topology untouched. AGENTS.md says 35–50k tris per base — the file was already at 63,638 before this job. **Revert path:** `work/male-legs-feet-form2/baseline/pre_install/` (blend + fbx, `b51cbb05…` / `39303a77…`). A positions-only alternative (old wedge feet + calf/shin/ankle/thigh relief) is the array `tmp/V1_f2.npy`; not staged, not audited.
2. **Zone extension (207 vertices).** The earlier legs job's zone ended at \|x\| < 0.27 and left the outer foot wall (\|x\| 0.270–0.284, z < 0.15) unmoved, so the old forefoot could not be replaced without them. No other chat owns them (arms/hands start at z = 0.80). Listed separately in `checks.json` (`moved_outside_literal_zone: 207`).
3. **Tall chunky toes are a gate trade-off.** The near-foot contour in both profile plates is a tall blunt cap (z = 30 mm at the tip, 54 mm 8.5 mm behind it). INSTEP_SAGITTAL (hold ≤ 1.1 mm) is a hard gate, so toe root heights are 60/50/45/40/36 mm. Earlier variants with low natural toes scored 4.8 mm mean on that gate (FAIL). If you prefer lower, more natural toes, say so — the gate line then has to be re-negotiated. Related: at z = 45/55 mm the toe cap front is 4.6/4.4 mm forward of the earlier chat's `plate_toe` table but within 0.8 mm of the near-foot contour used by the sagittal metric (the two plate readings disagree, the sagittal one is the gate-defining one).
4. **Soft form is subtle by design.** Relief is carving only (grooves/hollows ≤ ~5 mm) so the silhouette stays on the plate consensus (x-edge 0.99 mm, y-edge 2.95 mm vs 2.62 before). Roughness rises 36 % with the grooves (see line 7).
5. **Look at:** `LEGSF2_05` (front feet, side near-foot, 3/4 feet, plate | PASS | FORM2), `LEGSF2_06` (calf/knee/Achilles), `LEGSF2_07` (wire).

## Plates (why some numbers cannot be pushed further)

- Plates show featureless wedge feet — no toe cues — so the toes are designed (hand-form spirit), not read from the plates.
- The profile plates contain a **raised far foot**; only the near-foot contour was used.
- Front vs back plates disagree on the foot's lateral extent by ~4.5 cm (front union x 0.16–0.29, back 0.135–0.245); silhouette cost is flat across that range, so the toe row sits on the consensus centre (row shifted 9 mm medially, widths ×0.95).
- Left/right profile plates disagree by up to ~2 cm at the shin front edge; calf width on front/back plates by ~2 cm. The mesh already sits on the consensus.

## What changed

1. Fairing of the leg tube (Taubin, 12 it) + **silhouette-neutral carving relief** on the old topology (facing-weighted Gaussians): gastrocnemius groove + flank hollows, belly-end crease, popliteal, shin flats, Achilles hollows, malleoli, medial arch, heel pad, lateral edge, quad/vastus/ham grooves, peri-patellar planes. Kneecap relief 6.3 → 7.9 mm.
2. **Forefoot rebuild** (documented carve above): five toe tubes (rings, triangle-fan caps), valley columns between toes, ball ring with lobes, 11 body rings morphing from a planar slice of the original surface (Hermite, slope matched at the weld), instep height corrected to the plate profile, per-toe lift.
3. Soles clamped to the existing ground plane (min z unchanged).

Parameters: `design_v19.json`; scripts: `extract_base.py` → `build_all.py <name> design_v19.json` (`ff_build.py`, `ff_assemble.py`, `ff_cut.py`, `ff_slopes.py`, `ff_loop.py`, `relief.py`, `ff_blend.py`) → `audit_ff.py` → `metrics_ff.py` / `metrics_q.py` / `check_normals.py` → `export_fbx.py` → `install_legsfeet_form2.sh`. The edit is deterministic from the base; to re-apply on a newer ArtDir blend whose legs zone is unchanged: re-extract, set `BASE_TAG/BASE_BLEND/BASE_SHA` in `ff_common.py`, rebuild, re-audit, install under the guard (that is exactly how it was moved from `4287ba52…` to `b51cbb05…` when the hands FORM3 chat installed at 07:53; legs zone bit-identical in both, forefoot vertices identical, appended ids shifted by +308).

## Not mine / open

- Torso/pelvis chat: crotch roof and hip crease above z ≈ 0.765 untouched.
- 2 flipped faces (head, z ≈ 1.58) and 3 non-adjacent self-intersecting pairs outside the legs zone exist in the start file.
- Unity: `HeroBaseMaleFormProof.cs` `ExpectedTriangles` must become **66158** when the Unity project copy is refreshed; no capture was run, so "looks the same in Unity" is **not** claimed.
- Heel outer-bottom corner has a ~3 mm irregularity comparable to the start's roughness (checked in `proof/hA|hB|iA|iB|jA|jB`); seen from behind, the outer midfoot / little toe sits ~3–7 mm outboard of the heel (the forefoot is wider than the heel; the back plate has the narrower foot, which is why the back-view silhouette is 0.04 pt above the start).

## Proof files (`work/male-legs-feet-form2/proof/`)

`LEGSF2_01_legs_front_back` · `02_profiles` · `03_threequarter` (plate | PASS | FORM2 | outlines) · `04_feet_locked` · `05_feet_closeups` (plate | PASS | FORM2: front, back, left, right, 3/4 front ×2) · `06_calf_knee_closeups` · `07_topology_wire` (PASS vs FORM2, q3/top/side/front) · `08_zone_map` (displacement map) · progress: `progress_v2.png`, `progress_b25.png` · numbers: `male-legs-feet-form2-checks.json` (+ `tmp/audit_f2.json`, `tmp/quality_f2.json`, `tmp/metrics_f2_vs_base.json`, `tmp/normals_f2.txt`) · renders are Blender clay (EEVEE, 3 suns) from the locked plate cameras and fitted close-up cameras — not Unity captures. The legs/feet geometry in the proof renders (built on `4287ba52…`) is bit-identical to the installed build (built on `b51cbb05…`).
