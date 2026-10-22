# LIB_GROUND: Blender ground / water / wall / path / lava library (role A3)

**v2 2026-10-04 (continue pass): sections 4.4, 4.8, 5 (skin), 6 (gate numbers) and the `build_sea` / `build_path` / `build_cliff_skin` / `surf_patch` rows of section 2 are SUPERSEDED by the last section of this file, "v2 2026-10-04" (thin shelf, sparse surf patches, path under the ball, basalt backing + prisms, jagged strata). Read that section first.**

Status 2026-10-03: `blender/scripts/postcard_look_lib.py` is done and gated on all three holes (smoke builds in scratch,
nothing in the repo's hole files touched). `blender/scripts/postcard_lib.py` was NOT edited (identical to
`work/postcard-look/baseline/scripts/postcard_lib.py`). All A1 textures were present at the last run (`D.look_missing == []`).

Blender renders below are previews for judging shapes and texture scale. They are not Game-view proof; the integrator
shoots that in Unity.

## 1. Copy-paste: what a hole build script adds

Run after the hole's existing build and BEFORE `render_overview` / `save` / export.

```python
import postcard_look_lib as L

L.look_materials(D)                      # LK_* materials (call early; props libs reuse them by name)
snap = L.snapshot_ground(D)              # proof that play surfaces do not move
# ... the hole's own scenery: rocks, sea stacks, arch, plants (A4's postcard_props_lib) ...
L.retarget_materials(D)                  # MAT_* -> LK_*, WATER_FOAM* deleted (idempotent: call again after more MAT_* geometry)
L.build_cliff_skin(D, style="strata")    # Needle / Split
L.build_sea(D)                           # Needle / Split: ocean grid, THIN WATER_SHELF edge, sparse WATER_SURF_nn (after the skin)
L.assign_uvs(D)                          # LAST (after any region material)
ok, detail = L.compare_ground(D, snap)   # must be True
for name, ok, detail in L.audit_look(D) + L.v2_gates(D, pockets=L.sea_pockets(D, pockets)):   # pockets: the list you gave build_sea
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}")
P.render_overview(D); P.save(D)
L.export_look_fbx(D)                     # NOT P.export_fbx (see section 4)
```

Per hole (these exact calls are exercised by `postcard_look_smoke.py`):

```python
# Needle (hole 8): waterfall foot = shelf pocket + surf patch at the SAME centre, pale stone path (v2 2026-10-04)
fp = L.open_shore_point(D, (30.0, 160.0), free_m=40.0)                # (x, y, nx, ny): shore column with open water in front
foot = (fp[0] + fp[2] * 3.0, fp[1] + fp[3] * 3.0)                     # 3 m out from the cliff foot
L.build_sea(D, pockets=[(foot[0], foot[1], 6.0)])                     # AFTER build_cliff_skin; thin shelf, sparse surf
L.surf_patch(D, foot, radius_m=4.0)                                   # whitewater at the waterfall foot (radius <= 4.2)
L.build_path(D, [(-9.0, -6.0), (-8.5, 12.0), (-6.0, 28.0), (-3.0, 40.0)], width_m=2.6)   # course yards -> DRESS_PATH_01

# Split (hole 9): olive scrub on the left ridge (material only, the lie stays Rough)
R = D.SCENERY["ridge"]
L.assign_region_material(D, L.spine_polygon(R["spine"], max(R["width_yd"]) / 2 + 12.0), "LK_SCRUB")   # before assign_uvs

# Crater (hole 10): basalt everywhere, lava instead of sea
L.retarget_materials(D, overrides=L.CRATER_OVERRIDES)                 # MAT_CLIFF / MAT_CLIFF_DARK / MAT_ROCK_DARK -> LK_BASALT
loops = L.terrain_top_loops(D)
pin = P.m(*D.hole.pin)
pillar = [i for i, (Pl, _) in enumerate(loops) if P.point_in_poly(pin, [tuple(p) for p in Pl])]
rim = [i for i in range(len(loops)) if i not in pillar]
L.build_cliff_skin(D, style="basalt", loops=rim)                                  # vertical columns into the lava
L.build_cliff_skin(D, style="basalt", loops=pillar, follow_undercut=1.0, seed=1)  # tapered bowl like crater.jpg
L.build_lava(D, lights=4)                                                         # WATER_LAVA + LAVA_LIGHT_01..04
```

Run the gates the smoke test runs:
`/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/postcard_look_smoke.py -- --hole 09 [--live-build] [--verify] [--no-render]`
(`--live-build` runs your edited `holeNN_build.py`; the default is the frozen baseline copy. Output goes to
`work/postcard-look/lib_ground/smoke_holeNN/`, never into the repo's hole files.)

## 2. API

| call | what it makes / changes |
|---|---|
| `look_materials(D=None, rebuild=False)` | all 19 LK_* materials of LOOK_CONTRACT §3 (Principled + image nodes on `Unity/Assets/Resources/Course/Look/<Stem>_C/_N/_E.png`, `_C`/`_E` sRGB, `_N` Non-Color via Normal Map, Roughness = 1 - S, emission for LK_BASALT/LK_LAVA). Missing PNG = flat fallback colour of the right hue, listed in `D.look_missing`. Materials made by another lib (no `lk_by` tag) are left alone. |
| `look_material(name, D=None)` | get-or-create ONE LK_* material by exact name (never `LK_ROCK.001`). A4's `lk_material` uses the same get-first rule, so whoever runs first wins and the names stay the same. |
| `refresh_look_textures()` | rebuilds my materials' node trees once new PNGs exist |
| `retarget_materials(D, overrides=None, delete_foam=True, purge=False)` | per LOOK_CONTRACT / the task: ROUGH→LK_ROUGH; FAIRWAY, FAIRWAY_STRIPE, FIRSTCUT→LK_FAIRWAY (duplicate slots merged; the stripes live in the texture); GREEN, BUNKER_LIP→LK_GREEN; SAND→LK_SAND; CLIFF→LK_CLIFF; CLIFF_DARK→LK_CLIFF_DARK; ROCK, ROCK_DARK→LK_ROCK; WATER→LK_WATER; WATER_SHALLOW→LK_WATER_SHALLOW; LAVA→LK_LAVA. MAT_FOAM objects are deleted. MAT_FLAG/POLE/CUP/BALL stay. Only slots and indices change. |
| `assign_region_material(D, polygon, material="LK_SCRUB", units="yd", objects=None, top_only=True)` | per-face material by face centroid in the polygon; geometry untouched (the boundary follows the ~6.5 m terrain triangles) |
| `spine_polygon(spine_yd, half_width_yd)` | buffers a polyline into a polygon for the call above |
| `assign_uvs(D, objects=None, fill_missing=True)` | UV0 on every ground + WATER_* mesh (section 3). `fill_missing`: any other exported LK_ mesh with NO UV layer (library rocks, hole 9's ROCK_STACK columns) gets object-space box UVs, each face in its own material's tile |
| `build_cliff_skin(D, style="strata", loops=None, seed=0, step_m=1.5, lip_m=None, bottom_z=-1.6, disp_m=(0.2,1.2), follow_undercut=None, bands=4, wet_z=1.0, piece_m=140, replace=False, keep_out_water=True, max_out_m=2.6, jag_m=2.0, wall_material="LK_BASALT", basalt_backing=True)` | `ROCK_SKIN_nn` cladding (v2 section): strata = jagged headlands + no up-facing face in a water ellipse; basalt = backing sheet + hex prisms, tops 6.8-8.5 cm under PLAY_Z, wall lip band re-materialled |
| `build_sea(D, ocean=True, ocean_cell_m=16, shelf=True, shelf_m=(0.5,2.9), shelf_break=0.2, shelf_rag_m=0.6, pockets=None, pocket_m=4.2, auto_pockets=True, inner_m=4, surf=True, surf_cover=0.19, surf_min_cover=0.10, surf_len_m=(4,7), surf_reach_m=(2.2,3.6), surf_gap_m=12.5, rock_puffs=6, seed=0, cell=0.75)` | WATER_OCEAN grid, THIN WATER_SHELF edge, sparse WATER_SURF_nn patches (v2 section). Run it AFTER `build_cliff_skin`. Deletes WATER_SHALLOW / WATER_FOAM* and its own earlier output (re-runnable) |
| `surf_patch(D, center_m, radius_m=4.0, name=None, seed=0, strength=1)` | one radial whitewater patch (waterfall foot); radius <= 4.2 m keeps the run <= 10 m; build_sea never deletes it |
| `build_lava(D, cell_m=3.5, near_m=45, mid_m=130, extent_m=None, inner_margin_m=8, lights=4, light_z=2.2, light_points=None)` | subdivided WATER_LAVA + LAVA_LIGHT_nn empties |
| `build_path(D, polyline, width_m=2.4, units="yd", seed=0, step_m=0.15, across_m=0.15, z_off=0.0115, wobble=0.16, notch=0.22, skirt_m=0.04, clip_to_land=True)` | `DRESS_PATH_nn` (LK_PATH, collection STRUCTURES): conformal to the collider, top <= 1.15 cm over it (v2 section) |
| `export_look_fbx(D, path=None, colors_type="LINEAR")` | postcard_lib.export_fbx (same selection, axes, .meta, hole 7 guard) + `path_mode='STRIP'`, `embed_textures=False`, LINEAR vertex colours, and NO texture references |
| `box_uv(ob, tile=None)` | dominant-axis box UV for a prop mesh |
| `snapshot_ground(D)`, `compare_ground(D, snap, tol=1e-5)`, `audit_look(D)`, `fbx_check(path, expect_ground)` | gates (`fbx_check` resets the scene, so run it last) |
| `terrain_top_loops(D)` | boundary loops traced from the TERRAIN mesh itself (correct after hole 8's welds), land on the left |
| `CenterlineParam(D).uv(X, Y)` | (lateral m, arc m) around the smoothed centerline |

## 3. UV rules (UV0 only, tile units = metres / tile)

- **Planar**: LK_ROUGH, LK_SCRUB, LK_GREEN, LK_SAND, LK_PATH, water and lava use u = x/tile, v = y/tile in world space.
  - LK_ROUGH, LK_SCRUB and LK_LAVA get a smooth domain warp first (`UV_WARP`, gradient ≤ ~0.45). Without it the 24 m lava tile showed as a diagonal grid in the overview. With it there are no seams, and A5's UV_DENSITY gate measures 1.00x.
- **Centerline** (LK_FAIRWAY on FAIRWAY, FAIRWAY_FIRSTCUT, GREEN_APRON): u = signed lateral metres (+ = right of play), v = arc length.
  - The design centerline is Chaikin-smoothed (5 rounds), extended 120 m past both ends and sampled every 0.25 m.
  - The kinks, round tee end, apron past the pin and Needle's water-clipped pads therefore all get continuous UVs, and the stripes follow the line (visible on Crater's curve).
  - Measured UV×tile/world edge ratio over all flat faces: 0.53–1.47 (hole 10, warp + bend), 0.60–1.40 (hole 8), 0.63–1.38 (hole 9).
- **Wall**: TERRAIN faces that are not top faces get u = arc metres of the top-loop vertex the column hangs from (per-face unwrap at the seam), v = z.
  - Under hole 10's 6 m undercut this is stretched up to 3.36x, but no seam jumps (gate ≤ 8). These walls are 100% hidden by the skin.
- **ROCK_SKIN**: u = arc/tile, v = (z − outward offset)/tile, so ledges unroll instead of smearing.
- **Integer shift**: every object's UVs are shifted by a whole number of tiles so values stay near 0. Max |uv| is 250, on the 2 km ocean, which TennisWater does not sample.

## 4. Decisions (made here, not asked)

1. **No texture references in the FBX** (beyond the contract's STRIP/no-embed). All four hole `.meta` files have `materialName: 0`, which is Unity's "By Base Texture Name".
   - If the FBX names `Fairway_C.png`, Unity can import the material as `Fairway_C`. Then `GolfLook.Handles("LK_…")` never fires and the hole renders untextured.
   - My materials route every image through an identity Gamma node; the FBX exporter only records direct image links (tested: direct link → `Fairway_C` in the file, Gamma → not).
   - `export_look_fbx` also cuts, for the duration of the export, any direct image link on an LK_* material made by another lib (A4).
   - Gate FBX_NO_TEXTURE_REFS: re-import finds 0 images on all three holes.
   - **Hole agents must export with `L.export_look_fbx`.** Plain `P.export_fbx` would write A4's direct links and the SRGB vertex-colour default.
2. **WATER_OCEAN is still one flat object at z 0, but now a graded grid**: 16 m cells over the course, growing ×1.22 to 400 m cells at the 2 km rim; cells more than 12 m under the land are dropped.
   - Reason: TennisWater computes linear fog per vertex and saturates it in `vert`. A 4-vertex 4000 m plane has every vertex past the fog end, so the whole sea comes out fog-coloured.
   - Cost: 7,280 tris (hole 8) / 8,830 (hole 9).
3. **WATER_LAVA covers the whole crater floor, not just the lava ellipse.** The task said "clipped to the lava ellipse(s)", but hole 10 scores everything outside the shore as lava too, and postcard_verify's WATER_LEVEL gate needs WATER_LAVA to cover the shore + 20 m.
   - Shape: a disc out to the wall ring r_outer + 40 m.
   - Cell size: 3.5 m within 45 m of land and over the ellipse, 8.75 m to 130 m, 24.5 m beyond.
   - The land interior deeper than 8 m inside the walls is cut out. Total 13,185 tris.
4. **Depth stack** (all inside postcard_verify's z 0..0.2 water band):

   | surface | z above sea / lava |
   |---|---|
   | ocean / lava | 0.00 |
   | WATER_SHELF | 0.06 |
   | WATER_SURF | 0.12 |
   | DRESS_PATH | 0.035 above the highest play surface within 0.5 m |

   - Metal uses reversed-Z float depth, so these steps are far below 1 mm of error at 300 yd.
   - Even a 24-bit fixed buffer with near 0.3 yd resolves 274² / (0.27 × 2²⁴) = 0.017 m at 300 yd, so each 6 cm step is at least 3 depth steps.
   - The old build used 4 / 8 / 9 cm without fighting.
5. **Surf vertex colour** `Col` (FLOAT_COLOR, point domain, exported LINEAR):
   - A = shoreline closeness: 1 from under the cliff out to ~0.3 m, then 0 at the open edge AND at the lateral ends of every piece (the break-up noise mask also fades A).
   - R = smooth noise phase 0..1. UV0 = world/8 m.
   - Shelf-edge "reef break" patches peak at A 0.7.
   - Objects whose A never reaches 0.5 are dropped, because A5's SURF_SHORE wants an alpha ramp ≥ 0.5 per object.
   - Surf starts 2.5 m inside the top outline, i.e. under the cliff skin, so the wet line hugs the real rock.
6. **retarget keeps the old MAT_* datablocks with 0 users** (`purge=False`). Hole code that still reads `D.mats['MAT_ROUGH']` after retarget (hole 9's `sea_stack`) keeps working; 0-user data is neither saved nor exported.
7. **FIRSTCUT → LK_FAIRWAY** (task table). Visually the fairway texture runs 3 yd past the fairway lie; the stripes continue into it.
8. **Path**: skirt foot 4 cm under the ground directly below it (lowest vertex 5.96 m). A5's NEEDLE_PATH wants 5.95..6.60, and the skirt hides the step where the path crosses the fairway edge.
9. **LAVA_LIGHT_nn** sit 2.2 m above the lava, 3–14 m off the walls, within the lava ellipse + 45 m and inside `SCENERY['crater'].rim_radius` − 10 m. They are spread by farthest-point sampling starting next to the pillar; `light_points=` overrides.

## 5. Cliff skin (the "smooth extruded wall" FAIL line)

**strata** (Needle, Split): one continuous skin per boundary loop, cut into ≤ 140 m pieces.

- The shore is split into fissure blocks 3–9 m long, each with a crisp vertical joint made of doubled columns 0.18 m apart.
- 4 strata bands run from 0.15–0.45 m below PLAY_Z down to −1.6 m (below the water). About 35% of ledges merge, so two bands make one taller face.
- Every block × band cell has its own outward offset inside 0.2–1.2 m, its own ledge-height step (±0.42 band height) and its own overhang. A 22 m buttress swell and a height-dependent shear make the joints lean.
- A cap ledge tucks 0.25 m into the wall just under the grass lip. The TERRAIN's 1 m LK_ROUGH lip band shows above it as a grass fringe.
- `follow_undercut` 0.5 (default): halfway between plumb and hugging the undercut.
- Faces centred below z 1.0 use LK_CLIFF_DARK (wet).
- Smooth shading with sharp edges at 38°.

**basalt** (Crater): two rows of hexagonal prisms 1.0–2.0 m across.

- The outer row stands 0.2–1.2 m proud of the edge. Stepped tops sit 0.2–1.4 m under PLAY_Z, and each prism has 1–3 fractured segments.
- Prisms go from −1.6 m (into the lava) to their tops. `follow_undercut=1` leans them into the pillar's undercut, giving the tapered bowl of crater.jpg.

Measured on all three holes:

| gate | hole 8 | hole 9 | hole 10 |
|---|---|---|---|
| highest skin vertex (gate ≤ 5.95 m) | 5.78 m | 5.83 m | 5.88 m |
| up-facing skin faces above play − 0.1 | 0 | 0 | 0 |
| rays reaching the smooth wall below the skin top | 0 / 421 | 0 / 220 | 0 / 261 |
| skin tris | 14,880 | 54,240 | 29,712 |

- Shrink hole 9's skin with `step_m` (1.5 now → 2.0 is about −25%).
- A5's verifier, run on my smoke outputs:
  - SPLIT_SHORE_SKIN 100% (need 50%)
  - NEEDLE_CLIFF_SKIN 62% (need 20%; its samples include the design shore inside the water gaps, where there is no wall)
  - CRATER_PILLAR: sides 100% LK_BASALT down to z −6

## 6. Gates (binary, measured; `work/postcard-look/lib_ground/smoke_holeNN/gates_holeNN.json`)

Same 18 gates on every hole: 18 PASS / 0 FAIL on 8, 9 and 10 (last run, with `--verify`).

- **LOOK_TOP_SURFACES_UNCHANGED**: every vertex of every TERRAIN/FAIRWAY/GREEN/TEE_BOX/BUNKER mesh before vs after, max |Δ| = 0.00e+00 m.

  | hole | ground meshes | vertices |
  |---|---|---|
  | 8 | 8 | 2,492 |
  | 9 | 12 | 5,628 |
  | 10 | 10 | 2,956 |

- **LOOK_NO_COLLISION_PREFIX**: no new object uses a ground prefix (lib objects: 22 / 44 / 16).
- **LOOK_NO_MAT_FOAM**, **LOOK_GROUND_WATER_ARE_LK**, **LOOK_WATER_STACK**: PASS.
- **LOOK_UV_SANE**: no NaN/inf; edge ratios as in section 3.
- **LOOK_SURF_BROKEN**: ≥ 12 pieces, longest ≤ 140 m.

  | hole | pieces | objects | longest piece |
  |---|---|---|---|
  | 8 | 28 | 14 | 41.8 m |
  | 9 | 67 | 25 | 93.2 m |

- **LOOK_LAVA_MESH** (hole 10): 13,185 tris (≥ 3000), LK_LAVA only, 4 LAVA_LIGHT empties.
- **LOOK_BUDGET** (≤ 250k tris, ≤ 20 MB, before props):

  | hole | tris | FBX |
  |---|---|---|
  | 8 | 32,846 | 0.93 MB |
  | 9 | 93,786 | 2.74 MB |
  | 10 | 52,471 | 1.29 MB |

- **FBX re-import**: FBX_GROUND_SET, FBX_LK_MATERIALS, FBX_UV0, FBX_SURF_COLOURS (max A 1.00), FBX_NO_TEXTURE_REFS, FBX_NO_MAT_FOAM all PASS.
- **POSTCARD_VERIFY_NO_REGRESSION**: `postcard_verify.py` on the base build (29/29 PASS) and on the look build (blend + FBX). Every gate still passes (MARKERS, ONE_HEIGHT, NO_UPFACE_OUTSIDE_LAND, LIES_MATCH_MESH, SHORE_MATCH, HAZARD_PLACEMENT, PADS, WATER_LEVEL, FBX_GLOBALS, FBX_BUDGET, HOLE07_UNTOUCHED…) except **MATERIALS@blend/@fbx, which FAILs by design**: it only accepts the old MAT_* names and is superseded by LOOK_CONTRACT §3 (A5's NO_LEGACY_MATERIALS / GROUND_MATERIALS pass).
- **A5's `postcard_look_verify.py`** on my smoke outputs: every gate in my scope PASSES on blend and FBX — PLAY_SURFACE_GRID (0 mismatches), PLAY_SURFACE_TOPS, MARKERS_FROZEN, NEW_OBJECT_PREFIXES, GROUND_MATERIALS, UV_DENSITY, OCEAN_WATER, SURF_SHORE, the scrub, skin, path and lava/pillar gates above, plus TRIANGLE_BUDGET. Coverage:
  - SURF_SHORE: 95% of hole 9's surf_stretches (need 60%), 68% of hole 8's shore (need 40%)
  - SPLIT_SCRUB_RIDGE: 92% (need 60%); SPLIT_NO_SCRUB_RIBBON: 0 hits
  - NEEDLE_PATH: z 5.96..6.18, 105 m², 43 m long
  - CRATER_LAVA, CRATER_LAVA_LIGHTS, CRATER_PILLAR
- **A5 gates still failing** are owned by others: plants, masonry arch/ruin, icosahedron rocks / rock variety, waterfall, cone/smoke, crater wall column clusters, LK_REQUIRED/LK_TEXTURED (LK_MASONRY/LK_PLANTS unused in a lib-only build).

## 7. Previews (Blender EEVEE, not Game view)

- Contact sheets (oblique overview, phone tee, phone mid, low shoreline): `lib_ground/sheet_hole08.jpg`, `sheet_hole09.jpg`, `sheet_hole10.jpg`.
- Single renders: `lib_ground/smoke_holeNN/render_*.png`.
- Extra close-ups in `lib_ground/scratch/`:
  - `x_channel.png`: Split from the ribbon across the turquoise channel to the olive ridge's layered cliff
  - `x_path.png`: Needle flagstone path
  - `x_pad_edge.png`, `x_water.png`: shoreline
- `lib_ground/smoke_hole09.blend` = the hole 9 smoke scene (task deliverable).

Phone camera = CameraRig.FrameAddress in metres: 4.5 yd back, 2.4 yd up, looking 1.5 yd ahead, 60° vertical FOV, 900×1600. At that distance fairway / rough / green read as textured grass with soft mottling. Lengthwise stripes of about 5 m follow the line of play. No visible tiling at 2–30 yd.

## 8. Open items / notes for other roles

- **Hole agents**
  - Use `L.export_look_fbx`.
  - Call `retarget_materials` after your own MAT_* scenery (or call it again).
  - Run `assign_uvs` last.
  - Needle probably wants `shelf_m=(6, 14)`: the default 10–24 m shelf nearly fills the gaps between pads.
  - The path polyline in the smoke is a demo on the tee pad; choose the real one.
  - postcard_verify's 4 MB / 150k FBX_BUDGET may fail once props are added; the contract budget is 20 MB / 250k.
- **A2 (Unity)**
  - Surf colours are FBX LINEAR (raw A/R).
  - WATER_OCEAN / WATER_SHELF have UV0 = world/8 but TennisWater ignores it.
  - `LAVA_LIGHT_nn` are EMPTY objects 2.2 m above the lava.
  - The FBX material DiffuseColor is the fallback colour only.
- **A1 (textures, optional)**
  - At the 12 m tile, Cliff_C's crack network reads as rectangular blocks (a little "brick wall" next to the skin's own joints).
  - Basalt_E's glow forms ladder-like rectangles on 1–2 m column facets.
  - Surf_C alpha averages 0.35, so the Blender preview boosts it ×1.8 (preview only).
- **Scrub boundary**: follows the ~6.5 m terrain triangles (visible zigzag at the two ends of the ridge in the overview). Plants (A4) should cover it. The task forbids changing geometry, so there is no smoother option in the material.

---

# v2 2026-10-04 (continue pass: shelf, foam, path, crater wall, skin)

Scope of this pass: user lines 2 (water shelf), 4-cover (crater wall), 6 (foam), 7 (cart path) and the secondary skin items 8a/8b, all in
`blender/scripts/postcard_look_lib.py` (+ `postcard_look_smoke.py`). `postcard_lib.py` is byte-identical to `baseline/scripts/postcard_lib.py`.
Evidence: `work/postcard-look/v2/ground/` (`GATES_v2_ground.txt`, `before_holeNN*` = the old lib measured with the new auditors,
`final/` = official runs + the A5 verifier logs, `sheet_holeNN_v2.jpg` + `sheets/` = Blender previews, NOT Game view, `tools/` = auditors).
Official outputs of the smoke: `work/postcard-look/lib_ground/smoke_holeNN/` (blend, `look/hole_NN.fbx`, `gates_holeNN.json`) and
`lib_ground/smoke_hole09.blend`.

## v2.1 Results (binary, measured; `before` = the v1 lib of 2026-10-03 run through the same auditors)

| gate | hole | before | now |
|---|---|---|---|
| SHELF_THIN (visible WATER_SHELF width beyond the skin, waterline, every 1 m) | 8 | median 17.6 m, p95 20.2 m, max 22 m, ring on 100 % of the shore, area 13,105 m2 | **PASS** median 1.30, p95 2.50, max 3.10 m outside pockets, 5.60 m in the waterfall pocket (11 samples), breaks on 10 %, where present median 1.40 m / CV 0.54, area 2,645 m2 (**-80 %**); top-down footprint median 0.50 / p95 1.66 m |
| | 9 | median 18.3 m, p95 37.2 m, area 38,377 m2 | **PASS** median 1.40, p95 2.60, max 4.20 m, 3.10 m in the channel pocket (118 samples), breaks on 6 %, CV 0.44, area 10,507 m2 (**-73 %**); top-down median 0.50 / p95 1.60 m |
| NO_FOAM_STRIP | 8 | 69.6 % of the shore, longest run 45.8 m, gap 0.2 m, 5 strip components | **PASS** 12.2 % of 522 m, 14 runs, longest 7.5 m, min gap 15.0 m, 0 strips (aspect >= 4 and width CV <= 0.35), 0 components with alpha > 0.1 at an end, max aspect 1.46; 0 MAT_FOAM / WATER_FOAM / DRESS strips |
| | 9 | 71.3 %, longest 121.5 m, gap 0.5 m, 22 strips | **PASS** 15.4 % of 1,895 m, 62 runs, longest 7.5 m, min gap 14.0 m, 0 strips |
| PATH_UNDER_BALL | 8 | top up to 11.5 cm over the collider (median 3.5 cm), ball hidden up to 95.6 % (98 % of positions > 10 %) | **PASS** vertices max 1.15 cm (<= 1.2), dense 2.75 cm lattice max 1.15 cm (<= 1.5), skirt feet 10 cm under the ground, border step 0.13 cm, ball r 0.055 m: 35,747 resting positions, max hidden 3.5 %, 0 positions > 5 % |
| CRATER_WALL_COVERED | 10 | 24.33 % of 10,488 rays see bare wall, 2,549 at z >= 5 m on vertical LK_ROUGH | **PASS** 0 of 10,488 (0.00 %), 0 at z >= 5 m, 0 on LK_ROUGH, 0 up-facing skin faces above PLAY_Z - 0.05 (highest vertex 5.9495) |
| | 8 / 9 (strata, report only) | 19.8 % / 18.8 % | 18.96 % / 18.24 %: the grass lip band above the 0.15-0.45 m cap ledge (the short fringe that matches the stills) |
| SKIN_NOT_OVER_WATER (up-facing skin face deeper than 0.15 m inside a scoring water ellipse) | 8 | 118 grid cells, 29.5 m2, worst 0.83 m (top z 5.74), 178 faces by centre | **PASS** 0 cells, 0 faces |
| | 10 | 99 cells, 24.8 m2, worst 1.04 m (top z 5.86) | **PASS** 0 cells, 0 faces |
| | 9 | 0 | **PASS** 0 |
| SKIN_JAGGED (plan tortuosity, reviewer's measure) | 8 / 9 | 1.065 / 1.026 | **PASS** 1.183 / 1.160 (>= 1.15), outward offsets <= 2.6 m |
| PLAY_TOPS_UNCHANGED (`LOOK_TOP_SURFACES_UNCHANGED`) | 8 / 9 / 10 | | **PASS** max |delta| 0.00e+00 m on 2,492 / 5,628 / 2,956 vertices (A5's PLAY_SURFACE_GRID / TOPS / FACES also PASS) |
| LIB 18 gates (the 17 of v1 + POSTCARD_VERIFY_NO_REGRESSION) | 8 / 9 / 10 | 18/18 | **18/18 PASS on each hole**; plus the new ones: 25 / 25 / 24 gates in total, 0 failed |

Triangles / FBX (look build, before props): hole 8 48,638 (32,846 before) 1.55 MB; hole 9 115,622 (93,786) 4.48 MB; hole 10 62,731 (52,471) 1.70 MB.
`postcard_verify`'s old FBX_BUDGET (4 MB) now fails on hole 9 (4.48 MB) like MATERIALS: both are superseded by LOOK_BUDGET (250k tris / 20 MB, PASS).

A5's `postcard_look_verify.py` (the parallel gates agent's v2 file, read 2026-10-04 10:04) on the official outputs: every gate in this area PASSES on
blend and FBX: UV_DENSITY, PATH_UNDER_BALL (top 1.17 cm, 87 % of samples >= 3 mm up, ball hidden 0.0 %), NO_FOAM_STRIP (8: 11 % of 522 m, min gap 14 m; 9: 14 %,
gap 13 m), SURF_SHORE (8: 10 %, 9: 14 %), SHELF_THIN, CRATER_WALL_COVERED (0.2 %, 3 of 1,450), CRATER_PILLAR, BASALT_PRISMS, NEEDLE_PATH,
NEEDLE_CLIFF_SKIN, SPLIT_SHORE_SKIN, PLAY_SURFACE_*, NEW_OBJECT_PREFIXES, TRIANGLE_BUDGET. Its remaining FAILs are other areas (rocks, plants, arch,
ruin, waterfall sheet, smoke cone, textures).

## v2.2 What changed and why (read before editing)

1. **Shelf** (`build_sea`). The shelf polygon is now built relative to the skin, not to the shore: outer edge = (mean of the skin's waterline face and its
   top-down footprint, 5.5 m moving average) + v(s), v(s) = `shelf_m` (0.5-2.9 m, low-frequency noise), v = 0 on `shelf_break` (20 %) of the shore, +-`shelf_rag_m`
   (0.6 m) ragged outer edge, `inner_m` 4 m of hidden shelf under the walls. Pockets `[(x, y, r)]`: inside r the visible width grows to `pocket_m` (4.2 m; measured max
   5.6 m, limit 6). `auto_pockets`: every water hazard whose tag contains "channel" (Split's `channel_gap`, r = larger semi-axis + 6 m) is a pocket. The depth stack is
   unchanged (ocean 0, shelf .06, surf .12). An old-style `shelf_m` with hi > 6 is clamped to 6 and logged. Needle no longer needs a smaller shelf than Split.
2. **Foam** (`build_sea`, `surf_patch`). `WATER_SURF_nn` is now isolated ragged blobs, one object each (`_surf_blob`: A = 1 - smoothstep(.35, 1, rho), so alpha is exactly 0 on
   the whole rim; `surf_kind` 'blob'), 4-7 m along x 2.2-3.6 m out beyond the skin and reaching 2 m back under the overhang, `surf_gap_m` 12.5 m nominal between
   patches (measured gaps >= 13 m), nominal `surf_cover` 0.19 (measured 11-15 %, hard cap 25 %), `surf_min_cover` 0.10 (it re-plans with closer patches when the hole's
   shore is short, as on Needle), plus up to `rock_puffs` (6) puffs at rocks standing 3-12 m off the shore (any `ROCK_*` / `CLIFF_ROCK*` object, not `ROCK_SKIN` / `ROCK_WALL`).
   Patches that touch a notched shore twice (two runs < 8 m apart) are dropped and logged. `surf_patch` (waterfall foot) default radius is 4.0 (4.2 max = a 10 m run);
   build_sea never deletes it (`surf_kind` 'patch'). The coverage rule is the verifier's: a shore sample is covered when an up-facing LK_SURF triangle with mean
   alpha >= 0.3 lies within 1 m of (x, y, 0.12); the verifier samples the DESIGN shore, which is longer than the terrain loops on Needle (737 m vs 522 m), hence the 0.10 floor.
3. **Cart path** (`build_path`). A fine conformal lattice (rows every `step_m` 0.15, columns every ~`across_m` 0.15; Needle's demo path 5,720 faces, was 438). The collider
   (up-facing faces of the ground meshes) is sampled on a lattice twice as fine; every vertex = (LOWEST ground sample of the up-to-four cells around it) + `z_off` (0.0115).
   Consequences: every vertex is <= 1.15 cm over the collider right below it, the surface is <= 1.15 cm over the ground everywhere, and where the path crosses a
   6-14 cm surface step (rough 6.00 / first cut 6.08 / fairway 6.14 / apron .18 / tee .24 / green .26 / sand .30) it dips UNDER the higher surface for one cell instead of rising
   over the ball (6 % of the demo path's area is buried; route real paths so they do not run along a fairway edge). The skirt runs down to `skirt_m` (4 cm) under the lowest ground
   of the cell AND of the spot outside the outline (ends too), so the border is never a gap. Z-fighting: see the module docstring "Z-FIGHTING OF THE PATH": float
   reversed-Z depth resolves ~2e-5 m at 300 yd, margin > 50x; remedy for the Unity owner if a shimmer ever shows: render queue Geometry+10 + ZWrite Off + ZTest LEqual on LK_PATH
   (or a -1,-1 polygon offset). The path must NOT be raised.
4. **Crater wall** (`build_cliff_skin(style='basalt')`). (a) tops: every prism top is 6.8-8.5 cm under PLAY_Z (+-1 cm chipped tilt), so nothing is above PLAY_Z - 0.05 and
   the bare wall above them is a 5-8 cm sliver (the user's "within 3-10 cm"); the old 0.2-1.4 m stepped tops were the exposed band. (b) a BACKING sheet (`_basalt_backing`): a
   vertical quad strip 5 cm in front of the TERRAIN wall, built on the wall's own ring heights (-6, -3, 0, 1.25, 2.5, 3.75, 5.0 and PLAY_Z - 0.0505), from the wall's foot (z -6, so nothing
   under the opaque lava stays bare) up; it fills every groove between prisms and every undercut. (c) `wall_to_material`: the TERRAIN wall faces (incl. the 1 m grass lip band) with LK_ROUGH
   become LK_BASALT (slot only, geometry untouched), so the sliver is dark, not grass. (d) keep-out: prism caps stay <= 0.10 m inside the lava ellipse (moved away along the
   ellipse gradient, not along the corner-averaged normal). **The backing initially faced INWARD** (rows run up, the strata winding runs down): invisible to a Blender render, caught only by
   the verifier's back-face-culled ray test (18.3 % exposed): now `skin_facing_gate` (SKIN_FACES_OUTWARD) checks first-hit FRONT-facing >= 99 % and `wall_cover_test` culls back faces
   like Unity's single-sided materials. Keep that in mind for any new one-sided piece.
5. **Strata skin**. (a) `keep_out_water=True`: no skin vertex deeper than 0.10 m inside a scoring water ellipse (R pulled back by bisection, corner leftovers projected out along
   the ellipse gradient). (b) `jag_m=2.0`, `max_out_m=2.6`: an independent set of headland blocks 2-4.8 m long (crisp doubled columns at every edge), ~45 % bays and 55 % headlands, offsets
   growing toward the foot of the cliff, capped at 2.6 m outward (about the 2.5 m asked). (c) UVs are now unwrapped per quad in its own plane (`_quad_uv`), anchored on the plan length along
   the row: UV anisotropy 0 % of the area > 4:1 (a naive plan-length/(z - R) unwrap gave 25-55 % and fails the verifier's UV_DENSITY; the v1 skin had 2.7 %). The same unwrap is used for the
   basalt backing. Hole 9's skin is 79k tris (`step_m` 2.0 saves ~25 %).
6. **Auditors** (all in the lib, all read-only, find the TERRAIN by name so they also work on a re-opened blend): `shelf_gate`, `surf_gate`, `path_gate`, `wall_cover_gate`,
   `skin_over_water_gate`, `skin_facing_gate`, `skin_tortuosity`, `v2_gates(D, pockets)`; building blocks `measure_shelf`, `measure_surf`, `measure_path`, `wall_cover_test`,
   `skin_over_water`, `skin_facing`. `audit_look`'s LOOK_SURF_BROKEN was redefined: >= 8 pieces (was 12) and longest piece <= 14 m bbox diagonal (was <= 140 m); the real caps live in
   NO_FOAM_STRIP (run <= 10 m, gap >= 8 m, <= 25 %). LOOK_SKIN_NO_UPFACE_IN_PLAY / LOOK_WALL_HIDDEN_BY_SKIN in the smoke now use PLAY_Z - 0.05 and PLAY_Z - 0.12 (basalt) and front faces only.
   Re-audit any saved look blend: `Blender -b --factory-startup --python work/postcard-look/v2/ground/tools/measure_blend.py -- --hole 08 --blend PATH [--pockets "x,y,r"]`.

## v2.3 Exact calls for the hole builders (defaults as of this file)

```python
L.build_cliff_skin(D, style="strata")                       # Needle / Split; jag_m=2.0, max_out_m=2.6, keep_out_water=True
L.build_cliff_skin(D, style="basalt", loops=rim)            # Crater rim; wall_material="LK_BASALT", basalt_backing=True
L.build_cliff_skin(D, style="basalt", loops=pillar, follow_undercut=1.0, seed=1)
fp = L.open_shore_point(D, (30.0, 160.0), free_m=40.0)      # Needle waterfall foot: nearest shore column with 40 m of open water
foot = (fp[0] + fp[2] * 3.0, fp[1] + fp[3] * 3.0)
L.build_sea(D, pockets=[(foot[0], foot[1], 6.0)])           # AFTER the skin and AFTER the hole's rocks (rock puffs read them); Split: L.build_sea(D)
L.surf_patch(D, foot, radius_m=4.0)                         # after build_sea (build_sea would otherwise treat it as a run)
L.build_path(D, polyline_yd, width_m=2.6)                   # step_m=0.15, across_m=0.15, z_off=0.0115
L.assign_uvs(D)                                             # last
gates = L.audit_look(D) + L.v2_gates(D, pockets=L.sea_pockets(D, [(foot[0], foot[1], 6.0)]))
```
Needle's waterfall sheet (`WATER_FALL_nn`, props area) should end at `foot`; the shelf pocket and the foam patch are already there.

## v2.4 Open issues / not done / disclosed

* Blender previews only; no Game-view proof from this area (Unity is the integrator's). The path's z-fighting analysis above is arithmetic, not a Game-view test.
* The strata walls keep a short grass fringe above the cap ledge (18-19 % of rays at z 5-5.9 m see the LK_ROUGH lip band): wanted by the stills, reported not gated.
* On Crater a 5-8 cm sliver of bare TERRAIN wall (LK_BASALT) stays above the prisms (`CRATER_WALL_COVERED` tolerates it; A5's gate: 3 of 1,450 rays).
* `build_sea` needs the skin to exist (it measures it) and, for rock puffs, the hole's rocks; with no skin the shelf follows the TERRAIN wall's waterline face.
* The surf coverage floor 0.10 exists only because the verifier divides by the DESIGN shore length (Needle 737 m vs 522 m of loops). If the verifier changes its denominator, `surf_min_cover` can drop.
* `lib_ground/smoke_hole0N/a5_verify.json` are stale (2026-10-03); the current ones are `v2/ground/final/a5_verify_holeNN.{log,json}`.
* Props area: NO_ROCK_STRETCH_2X, SEASTACK_TAPERED, plant / arch / ruin / waterfall gates still FAIL in the A5 verifier on a lib-only build (not this area).


---

# v2 repair round 1, 2026-10-04 (review K/L: strata joints, pillar, foam, depth)

Repair agent "libs". Blender headless only, no Unity, nothing installed. Backup of the files before: `work/postcard-look/v2/libs_r1/backup/`. Evidence: `v2/libs_r1/gsmoke2/h0N.log` (the lib smoke on the three
baseline holes with the repaired lib: 25 / 25 / 23 gates PASS, 0 failed), `v2/libs_r1/hb2/` (scratch builds of the LIVE hole scripts + postcard_look_verify), `img/cliff_cmp.png`, `img/pillar_cmp.png` (Blender previews, NOT Game view).
**Holes 8, 9 and 10 need a rebuild** (`build_cliff_skin` draws a different rock; hole 8 / 9 strata, hole 10 columns); the hole fixers do that.

## Findings and what changed

| finding | root cause / decision | change |
|---|---|---|
| low, hole 9: "cliff strata repeat in regular columns, like a wall" (hole09_2_approach, far cliff) | `_strata_loop`: fissure blocks uniform 3-9 m (CV 0.29), all bands of a block share one `push` (weight 0.40), so every fissure was a lit step face in EVERY band (47 % of the fissures were a straight line through all 4 bands) and the 3 visible bands were equal slabs | `_blocks_mixed` (22 % 1.6-3 m, 56 % 3-8 m, 22 % 8-15 m: CV 0.56), `STRATA_TUNING = dict(mixed_blocks, push_w=0.10, b_w=0.56, closure=0.40, partition=True)`: the per-(block, band) offset weighs 0.56, the shared push 0.10, 40 % of the (joint, band) cells are closed (the block takes its neighbour's offset: a hairline), band boundaries come from a random partition (thickness ratios 0.55..1.75) with +-0.34 x thickness jitter. Same call signature (new optional `strata_tuning`). New gate `strata_gate` -> **STRATA_JOINTS_STAGGERED** in `v2_gates` (also in the smoke): block CV >= 0.40 and <= 25 % full-height fissures, with a NEGATIVE CONTROL (the previous layout, `STRATA_TUNING_PREV`, rebuilt on the same loops and deleted again). Measured: hole 8 CV 0.55, 17 % full-height lines of 92 fissures (control CV 0.27, 46 %); hole 9 CV 0.57, 18 % of 324 (control CV 0.30, 43 %); 55-58 % of the (fissure, band) cells stay open, so the cliff still reads as jointed rock. |
| medium, hole 10: the pin pillar "reads as a box": flat vertical faces, four horizontal courses of plank-like blocks, flat bottom, flared dark collar, no lava rim light, 2 px flag | the PLANK look is the Basalt_C texture's own cross cracks plus 1-3 fractured segments per column (`nseg` from (1, 2, 2, 3), cut heights random); every column top at one height (PLAY_Z - 5.5..9.5 cm = a ruler-flat skyline); the TAPER is the TERRAIN wall's (`P.build_terrain(undercut_m=6)` in hole10_build.py), which the skin and its backing sheet can only follow; the flag is `postcard_lib` gameplay geometry; the rim light is the hole script's `light_points` / Unity | `build_cliff_skin(basalt)` gets `basalt_segments=(1, 1, 1, 2, 2)` (mostly ONE prism over the whole height) and `basalt_stagger=(0.30, 0.12, 0.55)` (30 % of the columns stop 12-55 cm lower: a ragged crown; the backing sheet fills the gap): `v2/libs_r1/img/pillar_cmp.png`. CRATER_WALL_COVERED still PASS (hole 10: 3 of 10,488 rays see bare wall = 0.03 %, none at z >= 5 m; was 0). NOT done in the lib, hand-offs: (1) a visible bowl underside needs a bigger `undercut_m` in hole10_build.py (the lib cannot taper outside the wall it covers); (2) flag size / colour = postcard_lib / hole script; (3) lava-tinted foot = `light_points` near the pillar (hole script) or a Unity shader term by world height; `ROCK_` objects may not carry LK_LAVA (A5 gate g_rock_mats), so no emissive band could be added as geometry. |
| low, hole 10: ROCK_SKIN cladding UV stretched ~2.2x along the columns (p95 2.1-2.3, up to 34 % of a piece above 2:1) | not the lib: `tools/uv_stretch.py` (UV Jacobian, area weighted) on the lib's own cladding (smoke blend, 15 pieces, 30,788 tris): p50 1.08, p95 1.21 (max piece 2.26), 2.4 % of the area above 2:1 (max piece 14.9 %), 0 degenerate. After `hole10_look.author_uv` (the hole script's glow-slice mapping, low v density on purpose, 128 pieces): p50 1.44, p95 1.80, 7.1 % above 2:1 (max piece 33.6 %) | none in the lib; hole fixer's call (author_uv trades texture density for fewer glow ladders) |
| low, hole 9: no whitewater at all / flat water (id_surf 0 px in the ruin still) | the lib makes sparse broken patches by design: hole 9 68 WATER_SURF patches, 15.6 % of the shore, longest run 7.5 m, shortest gap 14.0 m, 0 strips (NO_FOAM_STRIP PASS); the ruin camera simply looks at a water stretch without one. Brief item 2/6 asks for a THIN shelf and no strips, so a depth gradient built as a wider shelf would contradict item 2; the ocean's own gradient is `GolfLook` Kind.Water (Shallow/Deep colours, DeepDistance) | none; not changed on purpose |
| low, all holes: no WATER_FOAM / MAT_FOAM, discrete LK_SURF patches remain | by design (see above): longest 8.5 m (Needle) / 7.5 m (Split) here, centre gaps >= 14 m | none |
| (hole builders' LIB_BUGS) `build_sea` rock puffs read a stale `matrix_world` (0 candidates) | objects created in the same run have an identity world matrix until the depsgraph is evaluated | `bpy.context.view_layer.update()` at the top of `build_sea` |
| (LIB_BUGS hole 8 #1) `audit_look` LOOK_WATER_STACK fails on any hole with a waterfall | `WATER_FALL_nn` is vertical by design (prefix mandated by LOOK_CONTRACT section 2) | `WATER_FALL*` excluded from that check (said in the gate text) |

## Gates run (all PASS unless noted)

* Lib smoke `postcard_look_smoke.py --hole 08|09|10 --no-render` (frozen baseline hole scripts): 25 / 25 / 23 PASS, 0 failed, including LOOK_TOP_SURFACES_UNCHANGED (max |delta| 0.00e+00 m on every play top), SHELF_THIN, NO_FOAM_STRIP, CRATER_WALL_COVERED, SKIN_NOT_OVER_WATER, SKIN_FACING, LOOK_WALL_HIDDEN_BY_SKIN, LOOK_SKIN_NO_UPFACE_IN_PLAY, LOOK_BUDGET, FBX re-import checks; new STRATA_JOINTS_STAGGERED on holes 8 and 9.
* Props smoke 76 / 76 PASS (LIB_PROPS.md, v2 repair round 1).
* Scratch builds of the live `hole08|09|10_build.py` against the repaired libs (outputs only under `v2/libs_r1/hb2/`, nothing installed), then `postcard_look_verify.py -- N --blend ... --fbx ...` on each result:

| hole | build gates | postcard_look_verify (blend + FBX re-import) |
|---|---|---|
| 8 Needle | exit 0, 30 PASS, 0 FAIL (ARCH, ARCH_FALLEN_BLOCKS_REST, NEEDLES, LOOK_TOP_SURFACES_UNCHANGED, ...) | RESULT: ALL PASS (95 PASS; LOOK_STILLS_TEXTURED skipped: no new stills yet) |
| 9 Split | exit 0, 16 PASS, 0 FAIL | RESULT: ALL PASS (91 PASS) |
| 10 Crater | exit 0, 20 PASS, 1 FAIL: `H_UV_WINDOWS` = its sub-clause "Basalt_C luminance profile deviation 0.0228 (<= 0.01)": Basalt_C / Basalt_E were rewritten by the texture agent while this ran (Basalt_E.png mtime 21:27; the 20:36 build passed with 0.0005); the glow-line / glow-free-zone clauses of that gate pass | 94 PASS, 3 FAIL: SMOKE_VISIBLE_STILLS, SMOKE_IN_FRAME@blend, SMOKE_IN_FRAME@fbx (smoke cards 0.47 / 0.01 / 0.00 % of the three frames, need 1.5 %; the stills carry no 'smoke' block): new verifier gates of the gates / texture areas about `build_smoke_cards` placement in hole10_look.py and Smoke_C, not touched by this round; NO_ROCK_STRETCH_2X, ROCK_*, CRATER_* and the skin gates PASS |

## Not done / limits

* No Game-view re-measure from this area: the holes are not rebuilt or installed here (hole fixers, then the stills).
* The pillar taper, the flag and the lava rim light are outside the two libs (above).


---

# v2 repair round 2, 2026-10-05 (libs agent): one change in `postcard_look_lib.py`

`_basalt_loop` (the hexagonal prisms of `build_cliff_skin(style='basalt')`): the outer face of every prism of the outer row stands at least `BASALT_MIN_RELIEF` = 0.14 m proud of the lip (`out = max(disp, 0.14)`), and the straight lean that makes a prism follow the undercut wall (`follow_undercut`) is now limited so that the outer face stands >= 0.14 m in front of the TERRAIN wall at 8 heights between bottom_z and the top (the old lean was fitted at z -1 only, so on a curved wall the prism was level with the wall and the 5 cm backing sheet over much of the height: the Game view showed a flat sheet with horizontal courses = the sheet rows at the wall ring heights; the pillar of hole 10). The keep-out against the scoring water ellipse (<= 0.10 m deep) is untouched, nothing goes beyond the lip + 0.4 m, prisms stay inside the outline. Ground-lib smoke: hole 10 23 / 23, hole 8 34 / 34, hole 9 25 / 25 PASS; the live hole 10 script builds with 21 / 21 build gates, `postcard_look_verify` 97 / 99 (the 2 are GROUND_UV_LOCAL_SMEAR, identical on the existing stage). Measured: `tools/pillar_seams.sh` row-step std 1.263 -> 0.161.
**Tried and removed:** a `taper_pillar_wall` (pull the TERRAIN wall vertices of a pillar loop in by a bowl profile) moved 288 wall vertices and failed `H_LOOK_TOP_SURFACES_UNCHANGED` (compare_ground checks every ground vertex, and the verifier's PLAY_SURFACE_WALLS freezes the non-up triangles): the collision body is frozen, the library never edits TERRAIN geometry. A merge of collinear wall rings in `_basalt_backing` (to cut the horizontal sheet rows) found deviations of 0.6-2.6 m between rings (the wall is a curve), so there is nothing to merge: also removed.


---

# v2 repair round 3, 2026-10-05 (libs agent): no change in `postcard_look_lib.py`

sha256 19e01c57... = the start of the round. Findings of review 3 that touched this lib's area and why nothing changed here: the hole 9 scrub / rough step is `hole09_look.assign_scrub_soft` (not `assign_region_material`), the channel's stone ring is the strata skin's top ring (round 1-2 findings: silhouette fidelity vs outline), the flat water / flecks follow the 'no continuous white band' reading, SHELF_THIN's max 33 m is the excluded sea pocket. Hole 10's pillar silhouette is the frozen wall (the basalt skin only stands outside it and never beyond lip + 0.4 m). Details and numbers: LIB_PROPS.md "v2 repair round 3". Ground-lib smoke on the final props lib: hole 8 / 9 / 10 = 34 / 25 / 23 PASS (`v2/libs_r3/lsmoke_hole0N.log`).
