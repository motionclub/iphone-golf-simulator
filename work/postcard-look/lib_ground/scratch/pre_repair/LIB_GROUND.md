# LIB_GROUND: Blender ground / water / wall / path / lava library (role A3)

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
L.build_sea(D)                           # Needle / Split: ocean grid, WATER_SHELF, WATER_SURF_nn
L.assign_uvs(D)                          # LAST (after any region material)
ok, detail = L.compare_ground(D, snap)   # must be True
for name, ok, detail in L.audit_look(D):
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}")
P.render_overview(D); P.save(D)
L.export_look_fbx(D)                     # NOT P.export_fbx (see section 4)
```

Per hole (these exact calls are exercised by `postcard_look_smoke.py`):

```python
# Needle (hole 8): pale stone path on a pad + smaller shelf for the small pads
L.build_sea(D, shelf_m=(6.0, 14.0))                                   # default (10, 24) also passes the gates
L.build_path(D, [(-9.0, -6.0), (-8.5, 12.0), (-6.0, 28.0), (-3.0, 40.0)], width_m=2.6)   # course yards -> DRESS_PATH_01
L.surf_patch(D, (x_m, y_m), radius_m=6.0)                             # whitewater at the waterfall foot (WATER_SURF_nn)

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
| `build_cliff_skin(D, style, loops=None, seed=0, step_m=1.5, lip_m, bottom_z=-1.6, disp_m=(0.2,1.2), follow_undercut, bands=4, wet_z=1.0, piece_m=140, replace=False, ...)` | `ROCK_SKIN_nn` cladding (section 5) |
| `build_sea(D, ocean=True, ocean_cell_m=16, shelf=True, shelf_m=(10,24), inner_m=4, surf=True, surf_m=(1.8,6.5), surf_gap=0.40, shelf_surf=True, cluster_m=90, seed=0)` | WATER_OCEAN grid, WATER_SHELF, WATER_SURF_nn; deletes WATER_SHALLOW / WATER_FOAM / WATER_FOAM_CREST and its own earlier surf (re-runnable) |
| `surf_patch(D, center_m, radius_m=6, name=None, seed=0, strength=1)` | one radial whitewater patch (waterfall foot) |
| `build_lava(D, cell_m=3.5, near_m=45, mid_m=130, extent_m=None, inner_margin_m=8, lights=4, light_z=2.2, light_points=None)` | subdivided WATER_LAVA + LAVA_LIGHT_nn empties |
| `build_path(D, polyline, width_m=2.4, units="yd", seed=0, step_m=0.6, z_off=0.035, wobble=0.16, notch=0.22, skirt_m=0.04, clip_to_land=True)` | `DRESS_PATH_nn` (LK_PATH, collection STRUCTURES) |
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
