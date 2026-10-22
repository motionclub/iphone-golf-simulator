# LIB_PROPS — role A4: Blender props library (POSTCARD_LOOK)

Status 2026-10-03 22:10 (v1): built, 38/38 smoke gates PASS. **v2 2026-10-04 + review-P repair + repair round 1 + repair round 2 (review 3, the LAST section: 83/83 smoke gates PASS); where v1 text below disagrees (sea stacks, swap, scatter default region, smoke cards, atlas greens), v2 wins, and where v2.1/v2.2 disagree with the final section `v2 repair`, the repair wins.** Blender only (headless), no Unity run, no git writes.
Proof (Blender renders, NOT Game-view proof): `ArtDir/screenshots/golf_postcards/look/props_sheet.png` (12 panels, 2424 x 2030).

| file | what |
|---|---|
| `blender/scripts/postcard_props_lib.py` | the library (API + copy-paste examples in the module docstring) |
| `blender/scripts/postcard_props_smoke.py` | gates + contact sheet + per-hole scatter tests (scratch only) |
| `Unity/Assets/Resources/Course/Look/Plants_C.png` | LK_PLANTS palette atlas, 256 x 256 RGB, written by `write_plants_atlas()` (sha256 `d9f90637…`) |
| `work/postcard-look/lib_props/` | scratch: panel renders, `smoke_log.txt`, `kinds_table.md`, `props_test_08.fbx`, scratch scripts |

Run (about 15 s, prints `GATE:` lines, exit 1 on a FAIL):

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/postcard_props_smoke.py
    #   -- --no-render  |  --no-holes  |  --holes 08,10  |  --scratch DIR

The smoke never writes `blender/hole_NN.blend`, the hole FBXs or `previews/`: hole tests use `P.start(design, out_dir=scratch)`
and never call `save`/`export_fbx`. `P.import_rocks` is only read (hole_07.blend sha256 checked unchanged by postcard_lib).

## 1. How a hole build uses it (copy-paste)

```python
import postcard_props_lib as PL          # after P.start / build_terrain / build_play_surfaces (masks need D.loops + the lie mirror)

# --- order matters: big things first, later scatter calls keep clear of the registered footprints
PL.scatter_rocks(D, 24, zone="rim", seed=4)                    # land, 0.4-10 m inside the cliff edge
PL.scatter_rocks(D, 30, zone="sea", seed=5)                    # in the water 3-26 m off the edge, LK_ROCK_WET twins
PL.scatter(D, ["PLANT_SHRUB_A", "PLANT_SHRUB_B"], 40, region=PL.region_band(D, 0.6, 6.0), seed=2)
PL.scatter(D, {"PLANT_FLOWER_PURPLE": 3, "PLANT_FLOWER_WHITE": 1}, 80, region=PL.region_band(D, 0.4, 10.0), seed=3)
PL.scatter(D, {"PLANT_TUFT_A": 3, "PLANT_TUFT_B": 2}, 600, region=PL.region_band(D, 0.3, 14.0), seed=1)
PL.hang_vines(D, PL.cliff_lip_points(D, spacing_m=7.0, seed=6), seed=6, skip=0.3)   # vines down the cliff walls

# --- Needle (8): arch on its own rock, waterfall, sea stacks, plants along the path (A3 builds DRESS_PATH)
PL.place_outcrop(D, x, y, 5.0, 6.4, seed=8)                     # flat-topped rock island, top exactly 5.0 m
arch = PL.build_masonry_arch(D, (x, y, 5.0), 171.2, span_m=7.5, height_m=11.0, seed=8, base_rock=False)  # vines included
top, out = (xf, yf, D.play_z - 0.3), (nx, ny)                   # a ledge point + outward normal (cliff_lip_points gives both)
PL.build_waterfall_sheet(D, top, out, width_m=3.0)              # WATER_FALL_00, LK_FALL
foot = PL.waterfall_foot(top, out, 3.0)                         # {'pos', 'width', 'dir'} -> A3's WATER_SURF patch there
PL.place_sea_stack(D, xs, ys, height_m=16.0, radius_m=4.0, seed=3)
PL.scatter(D, ["PLANT_SHRUB_A", "PLANT_FLOWER_PURPLE"], 30, region=PL.region_polyline(path_xy, 2.5), seed=9)

# --- Split (9): olive scrub ridge (material + plants only, the lie stays Rough), ruined arch, broken masonry
PL.scatter(D, {"PLANT_TUFT_C": 4, "PLANT_SHRUB_C": 1}, 500, masks=[on_left_ridge], seed=11)
PL.build_masonry_arch(D, (xa, ya), 30.0, span_m=6.0, height_m=9.0, broken=True, seed=12)
PL.build_ruin(D, [(x0, y0), (x1, y1), (x2, y2)], seed=12, clip=on_ridge_xy)          # DRESS_RUIN_nn_mm + fallen DRESS_BLOCK_*
PL.scatter_rocks(D, 30, zone="foot", seed=13)                  # jagged wet rocks at the shore foot

# --- Crater (10): basalt everywhere
PL.swap_legacy_rocks(D, basalt=True)        # existing ROCK_WALL_FLAT/BLUNT/CLIFF/ROCK_* instances -> ROCK_WALL_BASALT_* / ROCK_BASALT_*
PL.scatter_rocks(D, 20, zone="foot", seed=7, variant="BASALT")
PL.build_basalt_skin(D, pillar_loop, D.play_z - 0.04, -6.0, col_r=1.1, seed=3)       # columns INSIDE the outline, under the lip
PL.scatter(D, {"PLANT_AGAVE_B": 2, "PLANT_TUFT_B": 3}, 60, region=PL.region_band(D, 0.4, 3.0), seed=13)
PL.build_background_cone(D, (xc, yc, -8.0), seed=1, notch_deg=250)                   # DRESS_CONE
PL.build_smoke_cards(D, [((xc, yc, 70.0), 70.0, 90.0), ((xc + 80, yc + 20, 60.0), 50.0, 70.0)])   # DRESS_SMOKE_nn
```

Full signatures: module docstring of `postcard_props_lib.py` (API section). Everything takes the postcard_lib handle `D`
(parenting to `HOLE_NN_ROOT`, masks); `place`, `scatter` with a `region`, arch/ruin/waterfall/cone/smoke also run with `D=None`.

## 2. Library (built lazily into the hidden, excluded `ASSET_LIBRARY` collection; postcard_lib.export_fbx skips it)

Library object name == mesh name == KIND. Placed props are **linked duplicates** (`bpy.data.objects.new(name, lib_mesh)`) named
`KIND.nnn`; the FBX exporter writes each shared geometry once (gate FBX_GEOMETRY_ONCE: 19 Geometry nodes for 780 Model nodes).
Twins: `KIND_WET` (LK_ROCK_WET) and `KIND_BASALT` (LK_BASALT, grass cap included) for every ROCK_ kind of the first block.

| kind | verts | faces | tris | size x*y*z m | materials |
|---|---:|---:|---:|---|---|
| `ROCK_BOULDER_A` round boulder | 61 | 105 | 110 | 3.0 x 2.2 x 1.5 | LK_ROCK |
| `ROCK_BOULDER_B` lumpy boulder | 62 | 102 | 112 | 2.0 x 1.6 x 1.3 | LK_ROCK |
| `ROCK_SLAB_A` flat stepped ledge slab | 64 | 109 | 116 | 4.1 x 3.0 x 1.0 | LK_ROCK |
| `ROCK_BLOCK_A` chipped block | 64 | 111 | 120 | 2.4 x 1.8 x 1.3 | LK_ROCK |
| `ROCK_CAIRN_A` 6-stone cluster | 93 | 158 | 162 | 1.6 x 1.5 x 1.3 | LK_ROCK |
| `ROCK_STONE_A` / `_B` small stones | 69 / 63 | 115 / 109 | 126 / 118 | 0.8-0.9 x 0.6-0.7 x 0.4-0.5 | LK_ROCK |
| `ROCK_LEDGE_A` long low outcrop | 61 | 101 | 110 | 7.1 x 2.3 x 1.3 | LK_ROCK |
| `ROCK_SEASTACK_A` (v1 text, SUPERSEDED by v2.1: now a 13 m tapering spire) 17 m stepped stack | 129 | 210 | 226 | 8.3 x 8.3 x 21.1 (z -3..18.1) | LK_ROCK + LK_ROUGH ledges |
| `ROCK_SEASTACK_B` (v1 text, SUPERSEDED: now an 18 m spire) 12 m leaning stack | 119 | 196 | 210 | 7.1 x 7.8 x 15.6 (z -3..12.6) | LK_ROCK + LK_ROUGH cap |
| `ROCK_OUTCROP_A` flat-topped island | 101 | 163 | 178 | 13.6 x 14.3 x 11.0 (z -3..8, top flat) | LK_ROCK + LK_ROUGH cap |
| `ROCK_BASALT_A` dome cluster | 334 | 193 | 460 | 7.8 x 6.8 x 6.5 | LK_BASALT |
| `ROCK_BASALT_B` stepped ridge | 218 | 126 | 300 | 7.2 x 3.4 x 5.1 | LK_BASALT |
| `ROCK_BASALT_C` tall pillar, tapered capped underside | 152 | 100 | 256 | 5.5 x 4.8 x 12.2 | LK_BASALT |
| `ROCK_BASALT_D` low shelf | 288 | 167 | 392 | 9.6 x 7.6 x 2.7 | LK_BASALT |
| `ROCK_WALL_BASALT_A` / `_B` / `_C` wall segments (front rows -Y lower) | 336 / 334 / 320 | 194 / 193 / 185 | 464 / 460 / 440 | 41.5 / 37.7 / 31.1 long, 49 / 43 / 36 tall (z -6..) | LK_BASALT |
| `DRESS_BLOCK_A` / `_B` fallen cut blocks | 24 | 43 | 44 | 1.0 / 1.4 long | LK_MASONRY |
| `PLANT_TUFT_A` / `_B` / `_C` (green / dark / olive-straw) | 91 | 78 | 117 | 0.4-0.5 wide, 0.4-0.5 tall | LK_PLANTS |
| `PLANT_SHRUB_A` / `_B` / `_C` (round / dark tall / olive scrub) | 210 / 252 / 224 | 400 / 480 / 368 | 400 / 480 / 392 | 1.6-2.0 wide, 0.8-1.4 tall | LK_PLANTS |
| `PLANT_FLOWER_PURPLE` / `_WHITE` / `_YELLOW` | 179-203 | 182-247 | 221-283 | 0.4-0.5 wide, 0.5-0.7 tall | LK_PLANTS |
| `PLANT_VINE_S` / `_M` / `_L` (hang -Z, bulge +Y) | 39 / 81 / 135 | 44 / 96 / 162 | 56 / 120 / 204 | 1.0 / 2.0 / 3.5 long | LK_PLANTS |
| `PLANT_AGAVE_A` (blue-green) / `_B` (green spiky) | 123 / 150 | 112 / 136 | 164 / 200 | 1.1 / 1.4 wide | LK_PLANTS |
| `PLANT_PINE_A` / `PLANT_TREE_A` (cliff pine / windswept tree) | 111 / 150 | 105 / 258 | 198 / 276 | 2.7 / 3.1 tall | LK_PLANTS |
| `DRESS_SMOKE_CARD` (library card of `DRESS_SMOKE_nn`) | 15 | 8 | 16 | unit card, front -Y | LK_SMOKE |

Unique (not instanced, one per call): `DRESS_ARCH_nn` (339 faces: 2 piers of coursed blocks on a plinth, 13 voussoirs with
5 cm mortar gaps, proud keystone, recessed haunch blocks, recessed mortar core so joints read dark; broken = left pier lost its
top courses + crown and left half of the ring gone), `DRESS_RUIN_nn_mm` (coursed running-bond blocks, broken height profile with
stubs and collapsed gaps, doorway with lintel; split into objects of <= 500 faces), `ROCK_SKIN_BASALT_nn` (<= 500 faces each),
`WATER_FALL_nn` (8 x 12 grid, 96 faces), `DRESS_CONE` (421 faces).

Construction: rocks = convex hulls of 16-56 superellipsoid points cut by chip planes (flat tops/bottoms, corner chips) so every
rock is a few big planar facets; several overlapping hulls per rock give ledges/steps/buttresses; smooth shading with sharp
edges above 13 deg (facets read). Sea stacks = a wide lower core + an offset narrower upper core (shoulder ledge) + flat-topped
buttresses + a jagged flat-topped crown (no spike). Basalt = tight hex prisms (4.5 % gap so joints read dark), tilted/chipped tops;
walls use straight rows along X (front rows lower, smooth low-frequency skyline, grouped broken steps: an earlier version
alternated row offsets and read as castle battlements). Plants = chunky 3-sided tapered blade prisms, icosphere lumps, octahedral
blooms/leaf clumps, all smooth shaded, UVs on swatch gradients (dark base, light tips = free fake AO).

## 3. Conventions

* Origin = footprint centre at the ground contact, z = 0 ground (land rocks reach 8 cm below), +Z up. Sea stacks / outcrop: z = 0 is
  the waterline, they reach 3 m below. Basalt walls: z = 0 = lava line, 6 m below; front rows face -Y. Vines: origin = top attachment,
  hang -Z, bulge +Y (hang_vines turns +Y onto the given outward normal). Smoke card: bottom centre, front -Y.
* UV0 only, tile units: rocks / masonry / basalt / cone = object-space box projection (per face, the dominant normal axis picks the
  plane, side faces v = z) / contract tile (LK_ROCK 4 m, LK_BASALT 8 m, LK_MASONRY 4 m, the LK_ROUGH grass caps 12 m). Waterfall:
  u across 0..1, v 0 top .. 1 foot. Smoke: 0..1. Instances keep library UVs, so a non-uniformly scaled instance stretches its texture
  (library meshes are built at natural size for scale ~0.6-1.6; legacy-swapped walls land at scale ~1).
* Collections: rocks -> ENVIRONMENT/ROCKS, plants -> ENVIRONMENT/PLANTS, smoke/cone/waterfall -> ENVIRONMENT, arch/ruin/blocks ->
  STRUCTURES; parent = HOLE_NN_ROOT when D is given. All names start ROCK_/PLANT_/DRESS_/WATER_ (gate NAMES_SECTION2), never a
  collision prefix, never FLAG/HOLE_CUP/BALL_START/MARKER_.
* Materials: `lk_material(name)` is get-or-create. If A3's `postcard_look_lib` (or anyone) made `LK_*` first, it is reused
  untouched (no `lk_props` property); if this lib made it first it is a Principled BSDF with Image Texture nodes on the Look PNGs
  (normal map node for `_N`, emission for `_E`, a 0.62 tint multiply for LK_ROCK_WET), flat fallback colour while a PNG is missing,
  rebuilt by `refresh_materials()` once the PNG exists.

### Plants_C.png atlas (4 x 4 swatches of 64 px, row 0 at the TOP of the image; UV v0..v1 below)

| idx | swatch | sRGB | u | v | idx | swatch | sRGB | u | v |
|---|---|---|---|---|---|---|---|---|---|
| 0 | G_DEEP | 36,92,44 | .00-.25 | .75-1.0 | 8 | OLIVE_KHAKI | 160,150,92 | .00-.25 | .25-.50 |
| 1 | G_DARK | 54,122,50 | .25-.50 | .75-1.0 | 9 | STRAW | 208,184,112 | .25-.50 | .25-.50 |
| 2 | G_MID | 84,156,56 | .50-.75 | .75-1.0 | 10 | FLOWER_PURPLE | 150,88,210 | .50-.75 | .25-.50 |
| 3 | G_LIGHT | 122,186,66 | .75-1.0 | .75-1.0 | 11 | FLOWER_WHITE | 248,246,240 | .75-1.0 | .25-.50 |
| 4 | G_LIME | 156,206,80 | .00-.25 | .50-.75 | 12 | FLOWER_YELLOW | 252,204,52 | .00-.25 | .00-.25 |
| 5 | G_EMERALD | 42,136,92 | .25-.50 | .50-.75 | 13 | VINE | 72,134,56 | .25-.50 | .00-.25 |
| 6 | OLIVE_DARK | 98,104,46 | .50-.75 | .50-.75 | 14 | TRUNK | 112,78,52 | .50-.75 | .00-.25 |
| 7 | OLIVE | 132,134,62 | .75-1.0 | .50-.75 | 15 | AGAVE | 96,154,140 | .75-1.0 | .00-.25 |

Inside a swatch: brightness x0.68 (bottom) .. x1.12 (top) (flowers x0.82 .. x1.08) + a +-3 % hash noise. Every plant face's UVs sit in
ONE swatch, at least 6 px inside its border (gate UV_IN_SWATCH), none degenerate (UV_NONDEGENERATE). Wanted import: Clamp, mipmaps on,
no crunch (A2's importer). `Plants_C.png.meta` was created by someone else at 21:46 (not by me).

## 4. Scatter safety (what `safe=True`, the default, guarantees)

* `mask_off_play(D, margin)`: never within margin of fairway + first cut (`firstcut_yd` used as metres exactly like postcard_lib),
  green + apron (`GREEN_RADIUS + apron_yd`), the tee box (half-diagonal of `tee_box_m` + 0.4 m) or any bunker lip (1.22 x ellipse).
  Margins: tufts 0.35, flowers 0.4, agave 0.8, shrubs 0.8, trees 2.5, rocks 1.5, stacks/basalt 3.0 m.
* `mask_pin_clear(D, 6 m)` always; tall kinds (rocks, shrubs, trees, pine, agave B) also stay out of a corridor of fairway half-width
  + 3 m around the whole tee-to-pin centerline (land and water legs: the ball camera looks along it).
* The whole footprint (8 points at 0.75 x the scaled half extent) passes the same masks, and a land prop keeps its footprint on land
  (no overhang over the cliff edge).
* Measured on the real hole designs (scratch builds, 600 tufts + 40 shrubs + 80 flowers + 60 rocks each): 0 footprint rays hit any
  FAIRWAY/FAIRWAY_FIRSTCUT/GREEN/GREEN_APRON/TEE_BOX/BUNKER(+LIP) mesh, 0 land props in water, nearest prop to the pin 15.9 / 19.1 /
  17.8 m, 113.9k-114.1k tris per hole (gate <= 150k; worst case from library maxima 122.7k).

## 5. Gate results (latest run, `work/postcard-look/lib_props/smoke_log.txt`)

PLANTS_ATLAS, LIB_FACES (41 library meshes, max 480 faces / 480 tris, tufts 78 faces), ROCK_UNIQUE (11 unique rocks, min 61 verts,
101..210 faces), ROCK_VERTS_60, NO_ICOSAHEDRON, BASALT_COLUMNS (4 clusters 12-26 column tops + 3 walls, 72-83 % vertical faces),
UV_TILE_UNITS, UV_NONDEGENERATE, UV_IN_SWATCH, PLANTS_ONE_MATERIAL, SCATTER_BUDGET_WORST (122,720), CONE_NO_UNDERCUT (0 radius growth,
0 z folds), WATERFALL_SHEET, BASALT_SKIN_INSIDE, MASONRY_ARCH (62 separate blocks, 339 faces, 20 vines), MASONRY_RUIN, NAMES_SECTION2,
NO_ANIMATION, and per hole 08/09/10: SCATTER_SAFE, INSTANCED (780 objects / 17-19 meshes), HOLE_BUDGET, PROP_NAMES, DETERMINISTIC
(library rebuilt in a fresh file is identical), LEGACY_SWAP (20-21 icosahedra -> library meshes, local box kept 0.0 mm, 0 left),
FBX_GEOMETRY_ONCE (hole 08 test export: 19 Geometry nodes for 19 meshes, 780 Model nodes), PROPS_SHEET. **38/38 PASS.**

## 6. Decisions (made without asking)

* Rock kinds are NEW names (`ROCK_BOULDER_A` ...), not the old `ROCK_SMALL/MEDIUM/LARGE/CLIFF_ROCK`, so the hole-7 library import can
  coexist; `swap_legacy_rocks()` is the migration path (keeps every carefully placed box, renames `CLIFF_ROCK.*` to `ROCK_*`).
* Wet rocks are separate twin meshes (`_WET`), not object-level material overrides (FBX shares geometry per mesh datablock and
  object-linked slots are fragile through the exporter).
* Sea stacks / outcrop carry a second slot `LK_ROUGH` for grass caps (A5's rock-material gate allows LK_ROUGH, >= 60 % rock area holds).
* Pillar cladding (`build_basalt_skin`) stands INSIDE the outline under the lip (tops clamped <= top_z) so nothing passes the play
  outline in plan; it intersects the undercut TERRAIN walls on purpose (visible below the lip only).
* Waterfall whitewater is NOT built here (contract: WATER_SURF is A3's); `waterfall_foot()` returns where it goes.
* Cone defaults changed during iteration to a steeper stratovolcano (base_r 115, height 118, 7 terrace bands, 20 % rim notch).

## 7. Hand-offs / notes for other roles

* **Hole agents**: `swap_legacy_rocks` changes rock geometry, so hole08's own ROCKS_CONTACT_CHAIN / ROCKS_REST gates must be re-run
  after it. hole09's `ROCK_STACK_nn` are custom MAT_ meshes (not icosahedra): replace them with `place_sea_stack` or they keep flat
  MAT_ colours. hole10's 3-part stacks swap to 3 basalt clusters; cleaner is one `place_fit(D, "ROCK_BASALT_C", ...)` per stack.
* **A2 (GolfLook)**: rock meshes with two slots (`LK_ROCK` + `LK_ROUGH`) need per-slot material swap; LK_ROCK_WET = Rock maps, darker
  + S .35; LK_PLANTS = Plants_C, _BaseColor ~.94 grey like EnvV4, instancing on; library meshes rely on imported normals (sharp
  facet edges are authored), so the hole FBX import must keep "Import" normals (hole_07 meta), not "Calculate".
* **A1**: Rock_C's wavy strata lines read like contour lines on 1-3 m rocks at the 4 m tile (seen in props_sheet panel 1); acceptable,
  a slightly less banded Rock_C would read cleaner. Basalt_E crack glow shows on every column face of the walls; fine for the crater.
* **A3**: `waterfall_foot()` for the WATER_SURF patch; `cliff_lip_points()` gives lip points + outward normals if you want them too.

## 8. Open issues / limits

* No Game-view proof from this role (Blender renders only; Unity not run by A4 by contract).
* The hole panels in props_sheet use flat MAT_ terrain and the old MAT_FOAM bands (scratch builds without A3's look pass): they prove
  the scatter placement, not the final look.
* Strongly non-uniform scaling of an instance stretches its box UV (no per-instance UV fix possible with shared meshes).


---

# v2 2026-10-04 (continue pass: line 5 of the brief)

Status of the first v2 build: 57/57 smoke gates PASS (log kept as `v2/props/smoke_full_before_repair.log`). **After the review-P repair: 67/67 PASS (`v2/props/smoke_full_final.log`, 132 s); see the section `v2 repair` at the end, which supersedes the swap text, the swap table and the sea-stack list of v2.1 / v2.2.** Blender headless only, no Unity,
no git writes. Backup of the v1 files: `work/postcard-look/v2/props/backup_at_start/`. Contact sheets (Blender renders, NOT Game-view proof):
`v2/props/seastack_sheet.png` (old stacks vs new spires from 3 azimuths), `v2/props/towers_sheet.png`, `v2/props/props_sheet_v2.png` (12 panels).
Numbers: `v2/props/swap_stats.json`, `v2/props/old_swap_stats.txt` (the v1 swap on the same blends), `v2/props/baseline_dump_NN.txt` (legacy rock inventory); scratch tools in `v2/props/tools/` (try_*.py).

Run: `Blender -b --factory-startup --python blender/scripts/postcard_props_smoke.py -- [--no-render] [--no-holes] [--no-baseline] [--holes 08,10]
[--scratch DIR] [--sheet PNG] [--baseline DIR]` (about 2 min; `--no-render --no-holes --no-baseline` = 1.4 s of library gates).

## v2.1 Sea stacks (gate SEASTACK_TAPERED, SPIRE_TAPERED) [repair: + ROCK_SEASTACK_D / _E, softer ledges, satellites; see `v2 repair`]

`ROCK_SEASTACK_A / _B / _C` and the new `ROCK_SPIRE_A` are ONE tapering spire each (`_spire_mesh`, params in `SPIRE_SPECS`): 13-20 stacked slices of
irregular 5-9 corner polygons (zipped between rings of different corner counts), radius `R1 + (R0-R1)(1-u)^p` (concave profile), lean + twist,
1-3 shelves (next slice steps in 16 %), 1 overhang (slice bulges 13 %), chipped corners, per-slice tilt, a pointed (A, SPIRE) / chiseled (B) /
double-summit (C) top, a small grass crown (slot 1 = LK_ROUGH on the roof, the top 20 % and the shelf tops). Z from -3 m (under water) to the
summit; the vertex attribute `lk_slice` stores each vertex's slice so the gate reads slices from the mesh. 207-363 triangle faces.

| kind | above water | base r | top r / base r | faces | taper w90/w10 | max band widening | flat cap | facet orientations | bbox fill 0/45/90/135 deg |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ROCK_SEASTACK_A | 13 m | 3.1 | 0.30 | 260 | 0.33 | 1.03 | 2 % | 14 | .52 .53 .55 .52 |
| ROCK_SEASTACK_B | 18 m | 2.9 | 0.22 | 285 | 0.23 | 0.98 | 7 % | 16 | .53 .47 .52 .54 |
| ROCK_SEASTACK_C | 24 m | 3.5 | 0.17 | 363 | 0.21 | 1.01 | 1 % | 15 | .50 .44 .46 .47 |
| ROCK_SPIRE_A | 11 m | 1.8 | 0.28 | 207 | 0.28 | 0.94 | 0 % | 18 | .56 .51 .49 .53 |

Thresholds (`SHAPE_TH`): taper <= 0.45, band widening <= 1.12, flat cap (largest connected face group with normal.z >= 0.9) <= 25 % of the base
section area, >= 6 facet orientations (14 degree cones, clusters >= 2 % of the area), silhouette bbox fill <= 0.62 from 4 azimuths (part above the
water), >= 10 slices all with different outlines and 5-9 corners. **Negative control (the v1 two-block stacks, verbatim, built in the smoke): old A
FAILS (taper 0.48, flat cap 53 %, fill 0.66), old B FAILS (taper 0.65, flat cap 52 %, fill 0.76).**
`place_sea_stack(D, x, y, height_m, radius_m, seed=0, kind=None, wet_foot=True, skirt=3)`: kind = `seastack_kind_for(height_m)` (the one whose natural height
x 1.1 is closest, so uniform scale 0.8-1.6 covers 10-35 m), scale = height / natural height, footprint follows radius_m only within x0.8-1.25. Natural
heights (above water): A 13, B 18, C 24, SPIRE_A 11. `place_outcrop` is unchanged except its xy scale is clamped relative to its z scale (top height stays exact).

## v2.2 No stretching, legacy swap (gates SWAP_NO_STRETCH_2X_08/09/10 + _scene_NN) [SUPERSEDED in part by `v2 repair`: no z tiling, spire clusters, piles, upright instances]

* `SCALE_LIMITS = dict(lo=0.5, hi=2.0, aniso=2.0)`; `clamp_scale(sc)`; `place(..., clamp=True)` and `place_fit` clamp (object property `lk_clamped=1` when it
  changed anything); `stretch_report(objs=None)` -> dict(ok, n, min_scale, max_scale, max_ratio, violations); `instance_scales(objs=None)` lists the library
  instances (objects whose mesh is a hidden-library mesh).
* `fit_plan(W, D, H, kinds, rng)` composes instances for a box: kind x quarter turn x nx,ny,nz tiles (<= 4 per axis), clamps, cost = box-size error +
  instance count + anisotropy + distance from scale 1.15, picks randomly among near-best plans (variety).
* `swap_legacy_rocks(D, objs=None, basalt=False, rename=True, seed=0, purge=True, report=None)`: legacy = the icosahedron instances (mesh data ROCK_SMALL /
  MEDIUM / LARGE, CLIFF_ROCK, ROCK_WALL_FLAT / BLUNT), hole 9's `ROCK_STACK_nn` and any other non-library `ROCK_*`/`CLIFF_ROCK*` with < 60 welded vertices
  (never `ROCK_SKIN_*`). Each is replaced by `fit_plan` instances standing on the legacy box bottom, legacy rotation kept; the first tile reuses the object (renamed
  `<KIND>.nnn`), extra tiles are new linked duplicates (same parent / collections); `purge` deletes the hidden legacy template objects (so no 12-vertex rock stays in the
  .blend); `report` collects one dict per legacy rock (box, kind, tiles, scale, err). Plain family (`SWAP_ROCK_FAMILY`, `_WET` twin when the box reaches below z 0.3) or
  `basalt=True` (`SWAP_BASALT_FAMILY`). It raises RuntimeError if anything legacy is left. D may be None (works on a bare opened .blend).
* `assert_no_legacy_rocks(D=None, objs=None, raise_on_fail=True)` -> dict(ok, rocks, min_verts, offenders): call it after the swap in every hole script.
* New kinds so that boxes need no stretching: `ROCK_CRAG_A` (8.9 x 6.3 x 4.8 m), `ROCK_CRAG_B` (6.5 x 5.5 x 6.4), `ROCK_SPIRE_A`, `ROCK_SEASTACK_C`,
  `ROCK_BASALT_E` (12 m column cluster), `ROCK_BASALT_F` (8 m), and the wall-ring towers `ROCK_WALL_BASALT_S / _M / _L` (14 x 15 x 26, 20 x 21 x 38, 35 x 28 x 54 m).
* `build_smoke_cards` no longer instances the unit card scaled 35-90x: every `DRESS_SMOKE_nn` is its own mesh with the size baked in (scale 1). Arch base rocks and
  everything else go through `place()` and are clamped.

Baseline blends after the swap (`work/postcard-look/baseline/blender/hole_NN.blend`, sha12 in swap_stats.json; v1 = the old swap on the same files):

| hole | legacy -> instances | per-axis scale min..max | max/min | violations | v1 swap (outside 0.5-2.0 / ratio > 2) | kinds | swapped tris | box size error mean / max |
|---|---|---|---:|---:|---|---:|---:|---|
| 08 | 87 -> 97 (10 composed of several) | 0.50 .. 1.97 | 1.85 | **0** | 69 of 87 / 28 | 15 | 16,668 | 0.013 / 0.31 |
| 09 | 458 -> 476 (12 composed) | 0.50 .. 2.00 | 2.00 | **0** | 199 of 450 / 13 | 16 | 72,640 | 0.003 / 0.13 |
| 10 | 227 -> 227 (0 composed) | 0.50 .. 2.00 | 2.00 | **0** | 177 of 227 / 181 | 6 | 92,160 | 0.006 / 0.38 |

Hole 10: the 154 wall-ring boxes (32-48 x 30-44 x 46-73 m: CLIFF_ROCK, ROCK_WALL_BLUNT, ROCK_WALL_FLAT) become 154 single towers (117 x L, 37 x M); the 73 lava rocks
become BASALT_A/B/D/F. Tris of the whole swap 92k: if the hole's budget (250k with plants, skin, cone) is tight, drop every second ring tower (they are far away) or
let the hole script place S/M/L itself. Hole 9's 8 custom `ROCK_STACK_nn` meshes (64-80 vertices, cylinder stacks) and hole 8's tall thin stacked-rock boxes become `ROCK_SEASTACK_*` / `ROCK_SPIRE_A` (renders of the swapped baselines: `v2/props/swap_baseline_hole08|09|10.png`; flat MAT_ terrain, Blender only).
The v1 numbers in the review (155 of 227) used a slightly different counting; the v1 swap run again on these files is in old_swap_stats.txt.

## v2.3 Scatter: land only (gates SCATTER_DEFAULT_ON_LAND_NN, PLANT_ON_WATER_ZERO_NN)

`scatter(D, kind, count, region=None, masks=(), seed=0, min_gap=None, scale_range=None, avoid=(), z=None, sink=None, tilt=None, safe=True, corridor_m=None,
respect=True, register=True, wet=False, max_tries=12, yaw=True, margin_m=None, footprint_k=0.45, surface=None, shore_margin_m=1.0)` (the last two are new, appended).

* `surface`: `None` (default) = `'land'` for PLANT_/DRESS_ kinds and `'any'` for ROCK_ kinds (v1 behaviour); `'sea'` (rocks only, centre must be water); `'land'` for
  anything. A land scatter ALWAYS ANDs the caller's region with `mask_real_land(D, shore_margin_m=1.0, ring=12)`: lie != water at the point and on a 12-point ring of 1.0 m
  round it, plus (after build_terrain) the exact distance to the TERRAIN top outlines (`D.loops`, cliff lip + water ellipses) >= 1.0 m. So `region=None`, a rect tuple, a
  huge `region_disc`, a polyline over the sea, `region_band(side='sea')`, `safe=False` ... can never put a plant on the water. Plants refuse `surface='sea'` (ValueError).
* `region=None` = `region_land(D)` = the shore bounding box (v1: the box + 40 m with no mask).
* `safe=True` adds, per prop: `mask_off_play` (play surfaces + margin), `mask_pin_clear(6 m)`, **`mask_off_objects(('DRESS_PATH',), 0.4)`** (footprint of every `DRESS_PATH*` mesh
  in the scene + 0.4 m, read when scatter is called: BUILD THE PATH FIRST), **`mask_off_markers(1.5)`** (TEE_MARKER*, HOLE_CUP, BALL_START, FLAG*; call `P.build_gameplay` first),
  and the corridor for tall kinds. The 8-point footprint ring must also pass them and stay on land.
* Height: with `z=None` a land prop stands on the TOP found by casting down onto the TERRAIN / FAIRWAY / GREEN / TEE_BOX / BUNKER meshes of the scene (`ground_sampler(D)`; only triangles
  with unit normal.z > 0.2 count as a ground top), minus its sink; no ground under it = not placed. Without those meshes (only `P.start`) it falls back to `D.play_z`.
  Plant sinks are <= 0.045 m (shrub 0.04, tree/pine 0.045, tuft/flower 0.02, agave 0.03), so `|origin z - ground| <= 0.05`.
* Regions that bring their own heights (`region_on_objects`: arch / stack tops) skip the land mask and the ray cast; their props get `lk_on_object = 1` (a gate on "plants on water" by x,y
  must skip those).
* `scatter_rocks(...)`: signature unchanged; zones 'rim' / 'ledge' are `surface='land'`, 'sea' / 'foot' are `surface='sea'`. 'sea' scale default 1.0-2.0 (was up to 2.2).
* New helpers: `ground_sampler(D=None)`, `mask_real_land`, `mask_off_objects(prefixes=('DRESS_PATH',), margin_m=0.4, cell=0.25)`, `mask_off_markers(r_m=1.5, names=...)`, `region_land(D)`.

Gate results on all three hole designs (scratch builds: P.start + build_terrain + build_play_surfaces + water + build_gameplay + a DRESS_PATH_00 ribbon through the land rough):
`SCATTER_DEFAULT_ON_LAND` 08/09/10: 672 / 740 / 733 plants from `region=None`: on water 0; nearest shore edge 1.00 / 1.03 / 1.00 m; ray cast onto the real TERRAIN/FAIRWAY/GREEN/TEE_BOX/BUNKER
meshes (independent BVH of properly triangulated top faces): max |dz| 0.040 m, lowest z 5.96; pin >= 16 m; markers >= 10.8 m; path ribbon >= 1.16 m. `PLANT_ON_WATER_ZERO`: 51 adversarial calls per hole
(regions None / rect +300 m / disc over the sea / polyline over water / sea band / land band x tuft, shrub, flower, agave, pine+tree x seeds 11-13 x counts 40/150/600, one with `safe=False`)
placed 4.5k / 9.2k / 5.8k plants: **on water 0**, ground deviations 0.

## v2.4 No 12-vertex rock, shape gates (NO_12_VERTEX_ROCK, ROCK_SHAPE_NOT_BLOB, NO_ICOSAHEDRON, ROCK_VERTS_60)

* Library: all 34 rock meshes (twins included) have >= 61 welded vertices and >= 100 faces (min 61 / 100), 7-19 facet orientations. `ROCK_SLAB_A` was rebuilt with more chips (it had 5 orientations).
* `rock_shape_report(me)` -> dict(verts (welded), faces, tri_share, facets, radius_cv, edge_cv, area_cv, blob, ok, why). Blob = normalised-radius CV < 0.10 (a sphere / icosphere / UV sphere,
  stretched or not) OR (all triangles AND edge CV < 0.20 AND area CV < 0.45 AND radius CV < 0.18). `SHAPE_TH` holds every threshold. Library rocks: radius CV 0.13-0.39.
* NEGATIVE CONTROLS (all FAIL): icosahedron (12 v), icosphere sub 2 (42 v), sub 3 (162 v), split flat-shaded icosahedron (60 verts -> 12 welded), stretched sub 3, 8 % noised sub 3, UV sphere 16x10.
* `assert_no_legacy_rocks` FAILS on a scene with 3 icosahedra (raises) and PASSES after `swap_legacy_rocks`; every hole test re-asserts (min welded verts 61).

## v2.5 Wall columns (WALL_COLUMNS_HEX, BASALT_COLUMNS)

Towers S / M / L: 19 / 20 / 23 hex column tops (>= 12), 10 / 12 / 14 distinct top levels over 9.5 / 16.2 / 18.4 m, 8 / 12 / 12 chipped tops, 97 % vertical area, 141 / 152 / 173 faces, sizes 14x15x26 /
20x21x38 / 35x28x54 m (6 m buried). Box UV: `_finalize(..., uv_scale=s)` bakes UV = object / (tile / s) and stores `lk_uv_scale` on the mesh; towers use 1.3 / 1.5 / 1.5 (the nominal instance
scales of the wall ring), so at that scale the 8 m LK_BASALT tile measures 8 m (measured density ratio median 0.94: hex side faces are oblique to the box axes). `box_uv_expected` reads
`lk_uv_scale`. Clusters E / F and segments A / B / C stay at 1.0.

## v2.6 Atlas (Plants_C.png) and budget

* `Plants_C.png` greens moved from hue 92-129 to 66-96 (the stills' vegetation sits at hue 64-77): G_DEEP (55,87,35), G_DARK (87,117,47), G_MID (125,153,58), G_LIGHT (165,189,72), G_LIME (201,214,86),
  G_EMERALD (56,128,54), VINE (100,138,58), AGAVE (105,148,89); olives, straw, flowers, trunk unchanged; layout, UV rects and the 6 px margin unchanged (sha256 5fc472d9...).
  Reason: the ground textures are being retuned to the same hue, tufts / shrubs at 100 degrees would sit blue-green on yellow-green ground.
* `PROPS_BUDGET`: 50 library meshes, max 480 faces, tufts 78; dressed scene (600 tufts + 40 shrubs + 80 flowers + 20 agave + 60 rocks + 3 stacks + outcrop + arch + vines + legacy swap + smoke) =
  124k / 150k / 138k tris on 08 / 09 / 10 (the 250k hole budget leaves room for terrain, water, skin).

## v2 hand-offs

* Hole scripts: `scatter(...)` needs no region any more; build the DRESS_PATH and `build_gameplay` BEFORE scattering; after the legacy `P.import_rocks / place_rock / scatter_rocks` calls run
  `PL.swap_legacy_rocks(D, basalt=(hole == 10))` then `PL.assert_no_legacy_rocks(D)`; replace hole 9's `ROCK_STACK_nn` and hole 8's stacked rocks by `place_sea_stack` (or let the swap do it);
  re-run the hole's own ROCKS_CONTACT_CHAIN / ROCKS_REST gates (the swap changes rock geometry). Do not call `place` with scales outside 0.5-2 (it clamps).
* A5 (postcard_look_verify): the library exposes `rock_shape_report` / `seastack_report` / `stretch_report` if you want the same shape / stretch gates there (ROCK_NOT_ICOSAHEDRON in v1 only counted vertices).
* A2 (GolfLook): new library meshes with two slots (`LK_ROCK` + `LK_ROUGH`): SEASTACK_A/B/C, SPIRE_A, OUTCROP (as before); towers / clusters are `LK_BASALT` only.
* Not done / limits: no Game-view proof (Blender renders only); the wall-ring towers are dense (92k tris on hole 10) and tall; `ROCK_SEASTACK_*` crowns are small grass caps, not the lush moss of the stills;
  `fit_plan` stacks 2-3 clusters for very tall thin boxes (> 30 m): none occurs on the three baseline holes.

---

# v2 repair 2026-10-04 (review P: tiled sea stacks, scatter/place without D, short/blob mutants, anchoring)

Status: **67/67 smoke gates PASS** (`v2/props/smoke_full_final.log`, 132 s, `Blender -b --factory-startup --python blender/scripts/postcard_props_smoke.py`),
`guards.sh` 7/7 PASS. Blender headless only, no Unity run, no git writes. Backup of the files before this repair: `v2/props/backup_before_repair/`. Library 52 meshes
(was 50: + ROCK_SEASTACK_D, _E), max 480 faces. Plants_C.png unchanged (sha256 `5fc472d9...`).
Contact sheets (Blender Workbench / EEVEE renders, NOT Game-view proof): `v2/props/swap_stacks_sheet.png` (the swapped hole 9 stacks and hole 8 piles from 2 azimuths),
`v2/props/swap_baseline_hole08|09|10.png` (whole swapped baselines), `v2/props/seastack_sheet.png` (old two-block stacks vs the spires A-E + SPIRE_A, 3 azimuths),
`v2/props/towers_sheet.png`, `v2/props/props_sheet_v2.png`. Numbers: `v2/props/swap_stats.json`. Scratch tools: `v2/props/tools2/` (swap_check.py, swap_seeds.py, swap_many.py,
swap_render.py, spire_sheet.py).

## What the review found and what changed

1. **medium: tiled stacks.** `swap_legacy_rocks` composed tall legacy boxes by tiling nx x ny x **nz**: hole 9 ROCK_STACK_02/03 became two ROCK_CRAG_A_WET loaves stacked at one xy
   (0.5 m overlap, a flat contact plane), _04/_05/_06 became 2 x 2 lattices of four identical ROCK_SEASTACK_A clones, hole 8 CLIFF_ROCK.000 two stacked crags, 10 + 6 small boulders two high.
   Now: **never more than one tile along z** (`SWAP_MAX_TILES_Z = 1`); a tall sea box (or any `ROCK_STACK_nn`) becomes ONE tapering spire with its summit at the legacy top + 0-2 LOWER
   satellite spires of other kinds beside it + 2 wet skirt boulders that touch a spire foot; **piles** of legacy rocks resting on each other (hole 8's rock-on-rock towers) are merged into
   one such spire cluster; the remaining boxes get one instance or an xy tiling of ONE layer whose tiles each have their own kind / scale / yaw (identical neighbours are forbidden,
   `_distinct`). New gate counts stacks and clones (below).
2. **low: `scatter(None, plant, region=...)` and `place()` had no water protection.** `scatter(D=None, <PLANT_/DRESS_>)` now raises ValueError; `place()` refuses a PLANT_ kind below z 0.3 m
   (ValueError); both take `allow_low=True` for test scenes on a reference ground (the smoke panels use it).
3. **low: the swap left a 12-vertex ROCK_SKIN_BAD and a 162-vertex blob.** The swap now ends with `assert_no_legacy_rocks` (RuntimeError naming the offender: a <60-vertex rock is replaced
   or the swap raises), and any non-library ROCK_* / CLIFF_ROCK* mesh that `rock_shape_report` calls a blob (any vertex count) is a legacy rock and is replaced.
4. **low: anchoring.** Boxes are measured on the real vertices in their own yaw frame (not the rotated bbox corners), replacements stand upright (yaw only: the old icosahedra's tilt and 180 degree
   flips are dropped), a rock in the sea keeps its legacy TOP (foot never above the legacy foot), a rock that rests on something keeps its legacy BOTTOM, the sea floor is clamped at z -3 m.
   Measured over all baseline boxes: plain boxes never lower than the legacy by more than 0.13 m, tops -0.50 .. +0.15 m (hole 8 / 9 / 10: -0.50..+0.02 / -0.42..+0.15 / -0.01..+0.15).
   The two boxes the reviewer quoted (ROCK_MEDIUM.008 / .009 at z 15-17 m): tops 17.67 / 16.91 m against 17.89 / 16.91 m legacy (were 2.9 m low).
5. Not asked but needed: the spires read as stacked blocks where the shelves stepped in 20 % through a 2.6 %-height crack; the step is now 8 % over 5 % of the height and the shelf grass is patchy
   (a continuous green stripe made two blocks). Two more variants (D 16 m pointed, E 21 m slender twin summit) so a hole with a dozen stacks does not repeat four meshes.

## API (exact signatures and defaults; the hole-build agents code against these)

```python
place(D, kind, loc, yaw=0.0, scale=1.0, tilt=(0.0, 0.0), name=None, clamp=True, allow_low=False)   # PLANT_ kind with loc.z < PLANT_MIN_Z (0.3) -> ValueError unless allow_low
scatter(D, kind, count, region=None, masks=(), seed=0, min_gap=None, scale_range=None, avoid=(), z=None, sink=None, tilt=None, safe=True,
        corridor_m=None, respect=True, register=True, wet=False, max_tries=12, yaw=True, margin_m=None, footprint_k=0.45, surface=None,
        shore_margin_m=1.0, allow_low=False)       # D=None + land kinds (PLANT_/DRESS_) -> ValueError unless allow_low=True; ROCK_ kinds with D=None still work with a region
seastack_kind_for(height_m, radius_m=None, rng=None, near=0.25) -> kind
    # radius_m=None: unchanged (A/B/C by height, ROCK_SPIRE_A below 8 m). With radius_m: A-E and SPIRE_A compete (height fit + 0.6 x base-radius fit, scale outside 0.5-2 excluded);
    # with rng, one kind within `near` of the best cost is drawn (variety).
place_sea_stack(D, x, y, height_m, radius_m, seed=0, kind=None, wet_foot=True, skirt=3, satellites="auto") -> [main, satellites..., skirt boulders...]
    # main summit exactly height_m above the water (scale 0.5-2; heights 5.5-48 m). satellites "auto" = 0 for radius_m < 5, 1 below 8.5, else 2 (an int overrides). With satellites the main spire
    # takes 0.62 x radius_m; satellites are 0.5-0.72 x height_m, other kinds, own yaw / scale, feet overlapping the main foot. Skirt boulders touch a spire foot and never stand on a spire origin.
    # With satellites=0 and radius_m < 5 it still returns [main, skirt...] like before (kind choice now also sees ROCK_SPIRE_A / D / E, so the default kind can differ from v2).
fit_plan(W, D, H, kinds, rng, pref_scale=1.15, near=0.35, max_tiles=None, overlap=None)
    # max_tiles default (SWAP_MAX_TILES=4, 4, SWAP_MAX_TILES_Z=1); overlap default SWAP_TILE_OVERLAP=0.85; spire kinds only as a single instance; height error counts double in the cost.
swap_legacy_rocks(D, objs=None, basalt=False, rename=True, seed=0, purge=True, report=None) -> [objs]
    # report entries: dict(legacy, mesh, box=(W, D, H), cls="stack"|"rock", z=(bottom, top), members=[legacy names], kind, n, scale, err, instances).
    # Every replacement has the custom property lk_swap = the (lowest) legacy object's name. Class "stack": the rock reaches below z 0.3 and its top is >= 8 m above the water and it is a ROCK_STACK_nn
    # or >= 11 m tall (sea floor clamp -3 m) and >= 1.15 x its footprint, or it is a pile (members > 1: the upper legacy objects are DELETED, the cluster takes the lowest object's name in lk_swap).
    # rename is ignored for class "stack" (the legacy object is deleted, the cluster objects are named by place()). Ends with assert_no_legacy_rocks(D, objs) (RuntimeError).
    # basalt=True: no stack class and no piles; wall-ring boxes are single ROCK_WALL_BASALT_S/M/L towers as before.
swap_composition_report(objs=None) -> dict(ok, groups, pieces, vertical_stacks=[(a, b)], clones=[(a, b)])
    # vertical stack: two pieces of one lk_swap group whose ORIGINS are within 0.25 x the smaller footprint in plan but whose bbox centres differ in height by > 0.35 x the smaller height;
    # clone: same mesh, every scale component within 3 %, same yaw mod 90 degrees (within 4). Call it after the swap in every hole script and assert ok.
assert_no_legacy_rocks(D=None, objs=None, raise_on_fail=True)   # now also counts blob-shaped non-library ROCK_* meshes
SPIRE_SPECS / SEASTACK_CORE = (A, B, C) / SEASTACK_KINDS = (A, B, C, D, E) / SPIRE_KINDS = SEASTACK_KINDS + ("ROCK_SPIRE_A",) / SWAP_TALL = dict(min_h=8.0, aspect=1.15, sea_floor=-3.0, min_top=8.0)
```
New library kinds: `ROCK_SEASTACK_D` (16 m above the water, base r 3.3, 245 faces, 20 facet orientations), `ROCK_SEASTACK_E` (21 m, base r 2.7, twin summit, 295 faces); `_WET` / `_BASALT` twins as for the others.
Hole-script notes: (a) for the Needle / Split stacks prefer `place_sea_stack(D, x, y, height, radius)` (a radius of 9 m gives a main spire + 2 satellites + skirt) over relying on the swap;
(b) `ROCKS_CONTACT_CHAIN` / `ROCKS_REST` style checks must be re-run after the swap (rock geometry and the number of objects changed: hole 8 87 -> 93 instances, 18 upper pile rocks deleted);
(c) spire tails reach 3 m x scale below the water by design (never visible in the sea; cut by nothing); (d) the swap never produces a rock tilted off vertical.

## Gate table (all gates of the area; `v2/props/smoke_full_final.log`)

Gate ids asked for, with the final numbers:

| gate | result | measured |
|---|---|---|
| SEASTACK_TAPERED | PASS | A/B/C/D/E: 245-345 faces, taper w90/w10 0.33 / 0.24 / 0.20 / 0.28 / 0.23 (<= 0.45), band widening <= 1.06 (<= 1.12), flat cap <= 7 % of the base (<= 25 %), 14-20 facet orientations (>= 6), silhouette bbox fill 0.43-0.55 from 0/45/90/135 deg (<= 0.62); negative controls (v1 two-block stacks) FAIL (taper 0.48 / 0.65, cap 53 / 52 %, fill 0.66 / 0.76) |
| SPIRE_TAPERED | PASS | ROCK_SPIRE_A taper 0.28, fills 0.49-0.56, 207 faces, 18 facets |
| SWAP_NO_STRETCH_2X_08 / _09 / _10 | PASS x3 | 93 / 483 / 227 instances; per-axis scale 0.50..2.00, max/min 1.69 / 1.90 / 2.00 (<= 2.0), violations 0 / 0 / 0; hole 10: 154 wall-ring boxes -> 154 single towers |
| SWAP_NO_STRETCH_2X_scene_08 / _09 / _10 | PASS x3 | whole dressed scenes (scatter, stacks, outcrop, arch bases, vines, swap) >= 500 instances each, violations 0 |
| SWAP_NO_STACKED_CLONES_08 / _09 / _10 (new) | PASS x3 | stacked pairs 0 / 0 / 0, identical clones 0 / 0 / 0; stack-class boxes 12 / 8 / 0; 40 further seeds each on 08 / 09 (+ 8 on 10): 0 bad (`tools2/swap_many.py`) |
| SWAP_COMPOSITION_GATE (new) | PASS | negative control (a vertical ROCK_CRAG_A_WET pair + a 2 x 2 lattice of identical ROCK_SEASTACK_A_WET) FAILS: 1 stacked pair, 7 identical pairs; new place_sea_stack clusters: 0 / 0 |
| SWAP_TALL_IS_ONE_SPIRE (new) | PASS | synthetic ROCK_STACK_01 (14 x 15 x 21 m) and a 2 x 12 m thin rock -> one spire with the summit at the legacy top (17.2 / 12.0 m) + satellites / skirt beside it |
| SWAP_ANCHORED_08 / _09 / _10 (new) | PASS x3 | plain boxes lowest point >= -0.13 m (limit -0.2), stack groups above their designed tail >= -0.19 m (limit -0.5), tops -0.50..+0.15 m (limit -1.5..+1.0) |
| SWAP_REFUSES_SHORT_AND_BLOB (new) | PASS | 12-vertex ROCK_SKIN_BAD: the swap raises RuntimeError naming it; 162-vertex ROCK_BIGICO (radius CV 0.000) flagged legacy and replaced by ROCK_CRAG_B |
| PLANT_PLACE_GUARDS (new) | PASS | place at z 0 / 0.2 and scatter(None, plant) with and without z=0: all refused; z 5.98 fine; allow_low=True works |
| SCATTER_DEFAULT_ON_LAND_08 / _09 / _10 | PASS x3 | 672 / 740 / 733 plants from region=None: on water 0, shore edge >= 1.00 m, max abs dz to the ray-cast ground 0.040 m, lowest z 5.96 |
| PLANT_ON_WATER_ZERO_08 / _09 / _10 | PASS x3 | 51 adversarial calls per hole: 4,517 / 9,230 / 5,769 plants, on water 0 |
| NO_12_VERTEX_ROCK, NO_ICOSAHEDRON, ROCK_VERTS_60 | PASS x3 | 36 library rock meshes (twins included): min 61 welded verts / 100 faces; scenes with icosahedra FAIL the assert before and pass after the swap |
| ROCK_SHAPE_NOT_BLOB | PASS | 36 library rocks pass (radius CV 0.13-0.39, 7-20 facets); 7 negative controls (ico 12 / 42 / 162, split, stretched, 8 % noised, UV sphere) all FAIL |
| WALL_COLUMNS_HEX, BASALT_COLUMNS | PASS x2 | towers S / M / L 19 / 20 / 23 hex tops (>= 12), 10 / 12 / 14 distinct top levels, 97 % vertical area; UV density ratio 0.94 |
| PROPS_BUDGET | PASS | 52 library meshes, max 480 faces (<= 500), tufts 78 (<= 120); dressed scenes 124k / 151k / 138k tris (<= 250k); swapped baselines 15.7k / 73.0k / 92.2k tris |
| PROPS_SMOKE_PASS | PASS | 67/67 gates |

The other 44 gates (PLANTS_ATLAS, LIB_FACES, ROCK_UNIQUE, UV_*, PLANTS_ONE_MATERIAL, SCATTER_BUDGET_WORST, CONE_NO_UNDERCUT, WATERFALL_SHEET, BASALT_SKIN_INSIDE, MASONRY_*, NAMES_SECTION2,
NO_ANIMATION, PROPS_SHEET, per hole SCATTER_SAFE / INSTANCED / HOLE_BUDGET / PROP_NAMES / DETERMINISTIC / LEGACY_SWAP, FBX_GEOMETRY_ONCE) all PASS in the same log.

Baseline blends after the swap (`work/postcard-look/baseline/blender/hole_NN.blend`, opened, never saved):

| hole | legacy -> boxes -> instances | stack class | per-axis scale | max/min | violations | stacked pairs / clones | kinds | swapped tris |
|---|---|---:|---|---:|---:|---|---:|---:|
| 08 | 87 -> 69 (18 upper pile rocks merged) -> 93 | 12 | 0.50 .. 2.00 | 1.69 | 0 | 0 / 0 | 17 | 15,706 |
| 09 | 458 -> 458 -> 483 | 8 (ROCK_STACK_nn) | 0.50 .. 2.00 | 1.90 | 0 | 0 / 0 | 19 | 72,952 |
| 10 | 227 -> 227 -> 227 | 0 | 0.50 .. 2.00 | 2.00 | 0 | 0 / 0 | 6 | 92,152 |

Independent re-runs of the reviewer's scripts (`v2/review_P/mutants.py`, `buried.py`, `nz.py`, read-only): mutants: every <60-vertex / blob rock replaced, ROCK_SKIN_BAD raises; `nz.py` lists every hole 9 stack as
one spire + satellites (n = 3-5 objects, none vertically stacked); `buried.py` compares each group with the LOWEST legacy rock only, so its hole 8 top deltas now show the merged piles (expected).

## Limits / not done

* No Game-view proof (Blender renders only). The grass crowns on the spires are small caps, not the lush moss of the stills.
* Pile merging only applies to piles whose lowest rock stands in the sea and whose top is >= 8 m above the water; dry piles keep their individual rocks (each one still upright, in one layer).
* Spire satellites are other kinds at 0.5-0.72 x the main height; an extremely short main (< 11 m) gets none (a satellite must be >= 5.5 m).
* The wall-ring towers are unchanged (still dense: 92k tris on hole 10).


---

# v2 repair round 1, 2026-10-04 (review K/L: ruin arch slivers, faceted sea stacks, scale limits)

Repair agent "libs". Blender headless only, no Unity run, no git writes, nothing installed. Backup of the files before this round: `v2/libs_r1/backup/`
(also the frozen negative control of the new look gates). Evidence: `v2/libs_r1/` (`smoke_props_2.log` = the full smoke, 76/76 PASS in 171 s; `img/` = Blender
previews, NOT Game-view proof; `tools/` = arch_gate.py, arch_test.py, spire_test.py, spire_metrics.py, uv_stretch.py, prev.py). **The hole 8, 9 and 10 builds must be
re-run** (arch, every stack cluster, the legacy swap and the scale clamp changed): the hole fixers do that next; scratch builds of the live scripts against these libs
(`v2/libs_r1/hb/`, `hb2/`) exit 0 on all three holes; holes 8 and 9 pass every build gate and `postcard_look_verify` (RESULT: ALL PASS, 95 / 91 gates), hole 10's failures (H_UV_WINDOWS, SMOKE_*) are
texture / smoke-card placement gates of other areas (table in LIB_GROUND.md).

## What the reviewers found and what changed

| finding | root cause | fix |
|---|---|---|
| medium, hole 8: the ruin arch has dark slivers and a notched edge (hole08_3_arch.png) | `_arch_mesh`: every stone was 5 cm smaller than its cell in every direction (`gap`), with a recessed mortar core behind: each joint was a 5 cm slot 8-14 cm deep that the sun shadowed to black (the "slivers": 13 radial voussoir joints + every pier course), and every pier block was rotated +-0.02 rad / jittered +-1.5 cm in plan, so the outer face stair-stepped (the "notches") | `_arch_mesh` rewritten around `_cut_block(mb, poly, yf, yb, c, cy, bevel_back, hide)`: a stone is a convex (x, z) polygon extruded along Y whose front AND back edges are chamfered 2.2 x 1.4 cm, so two stones that touch exactly leave a closed V-groove (never a see-through slot, never a thin quad); piers = courses that tile the pier section exactly (running bond, every course flush, outer face coplanar, no rotation, no plan jitter), the ring = n wedges sharing their radial faces (n = pi (r_in + t/2) / max(0.7, 0.12 span), odd), haunch = a staircase of whole blocks (each row up to 0.5 m narrower than the one below, recessed 7 cm so the ring stands proud), plinth = a proud chamfered block. Side faces that coincide with a neighbour are not emitted. No mortar core any more. Face budget: `ARCH_MAX_FACES` 490 (smoke cap 500): up to 12 attempts with other random streams, then the back chamfer is dropped (not needed so far: 489 / 286 / 434 faces for the hole 8 / hole 9 broken / span-6 intact arches). API, `dims`, vine points, plinth footprint and the arch height are unchanged (hole08_look's outcrop fit, vines and fallen-block gates all PASS in the scratch build). |
| medium, hole 8: the sea stacks look like faceted grey blobs | `_spire_mesh`: 12-20 rings with a RANDOM corner count (5-9) per ring, so arrises never ran up the spire; every edge sharp above 12 degrees (flat shading, 25-30 % smooth edges); no strata | `_spire_mesh_try`: 25-32 rings (spacing ~0.5-1.1 m, budget loop `SPIRE_MAX_FACES` 470), the corner COUNT changes by one only now and then and the corner ANGLES persist (vertical striation), corner radius = noise with a low frequency in height (ridges and grooves climbing many rings) + vertical chips (a corner pushed in 16-30 % for 15-35 % of the height) + a faint hard/soft strata saw (+-2.5 %), 7-8 LEDGE PAIRS (two rings 6-20 cm apart: the spire steps in / out; 2-4 major steps of 7-16 %, the rest 2-4 %), slanted bedding (ring tilt 0.1 rad), a buttress on one side of the lower third (+16..30 %), smooth shading (sharp edges only above `SPIRE_SMOOTH` = 30 degrees: 52-62 % of the interior edges smooth, was 21-31 %), up-facing ledges carry patchy grass (LK_ROUGH 2-5 % of the area, still >= 60 % rock). Heights, base radii, summit styles, `SPIRE_SPECS` keys and every gate of the v2 section are unchanged (SPIRE_A: top ratio .26, p 1.3 to keep the silhouette fill under .62). |
| (not in the list, hole builders' LIB_BUGS) a clamp at exactly 0.5 became 0.49999997 after the FBX round trip and failed NO_ROCK_STRETCH_2X@fbx | `SCALE_LIMITS` lo = 0.5 | `SCALE_LIMITS = dict(lo=0.501, hi=1.999, aniso=1.998)`: the contract (0.5 .. 2.0, max/min 2) holds with a 1e-3 margin; all swap / scene gates re-run and PASS |
| low, hole 9 `DRESS_BLOCK_A.*` degenerate UV triangles (0.9 % of the area) | not reproducible on the library mesh | `tools/uv_stretch.py` on `DRESS_BLOCK_A` / `_B`: 44 tris, UV Jacobian p50 1.00, p95 1.07, 0 degenerate, 0 % of the area above 2:1 (box projection can not collapse a face: UV area >= 0.58 x its area); spires p95 1.34-1.41, arch p95 1.24. Nothing to change in the lib; instances in the hole are scaled 0.8-1.1 uniformly |

## Numbers (smoke_props_2.log)

* Arch (hole 8 size, span 7.5 / height 11, 489 faces): ARCH_NO_SEE_THROUGH_08 PASS (71,920 rays at 2 cm through the solid masonry: 0 pass through), ARCH_PIER_COPLANAR_08 PASS (12 outer pier faces within
  0.000 mm), ARCH_NO_DEEP_SLITS_08 PASS (1 of 82,189 front cells > 3 cm deeper than both cells 4 cm to either side, 0.0012 %; negative control = the previous arch: 2,036 cells, max relief 41 cm),
  ARCH_FACES_08 PASS; the same four for the hole 9 broken arch (span 6 / 9 m): 0 / 0.000 mm / 1 cell (0.0029 %; control 1,064 cells) / 286 faces. `tools/arch_gate.py` repeats them standalone plus an intact span-6 arch.
* Sea stacks: SEASTACK_TAPERED PASS for A-E (401 / 461 / 437 / 439 / 439 faces, 28-32 slices, taper w90/w10 0.25 / 0.23 / 0.20 / 0.27 / 0.21, band widening <= 0.94, flat cap <= 6 %, 11-13 facet orientations, fill <= 0.54);
  SPIRE_TAPERED PASS (421 faces, taper 0.28, fill 0.57); new SEASTACK_CRAGGY PASS: smooth-edge share / ledge pairs A 0.52/7, B 0.59/8, C 0.53/8, D 0.58/8, E 0.60/7, SPIRE_A 0.59/10 (need >= 0.45 and >= 4); negative
  control (the previous round's spires, same measure): 0.21-0.31 smooth, 0-1 ledge pairs, all FAIL. The SEASTACK_TAPERED face window changed from 150..400 to 150..480 (`PL.SPIRE_MAX_FACES + 10`): 400 was a self-imposed aim of the
  first v2 build, the contract limit (PROP_FACE_BUDGET, LIB_FACES) is 500 and stays; LIB_FACES PASS (52 meshes, max 480).
* Everything else in the 76 gates PASS (SWAP_*, SCATTER_*, PLANT_ON_WATER_ZERO, ROCK_SHAPE_NOT_BLOB with its 7 negative controls, PROPS_BUDGET 125k / 152k / 139k tris dressed, FBX_GEOMETRY_ONCE, MASONRY_ARCH 43 components / 489 faces, ...).
* The scratch build of the live hole 8 script (hb/h08): 29 build gates PASS, among them ARCH (foot vertices on the outcrop), ARCH_FALLEN_BLOCKS_REST, NEEDLES (9 clusters, 26.1 yd from the centerline), ROCKS_STAND_IN_THE_SEA, ARCH_NOT_HIDDEN_BY_NEEDLES.

## Visual check (Blender EEVEE at the Game cameras, NOT Game view)

`v2/libs_r1/img/arch_cmp_blender.png` (left installed hole 8, right the scratch build with these libs, camera hole08_arch): the dark diagonal strips and the stepped right pier edge are gone, the stacks behind the arch show
ledges instead of one faceted blob; `img/spire_new_*.png`, `img/arch_a_*.png`. The Game-view re-measure needs the rebuilt + installed holes (hole fixers, then the Unity stills).

## Limits

* The stacks are smooth shaded with 30 degree sharp edges: the FBX import must keep "Import" normals (as before). In Unity the look relies on Rock_N for surface detail; at the tee distance a stack is 30-50 px wide.
* The arch spandrel is a staircase of whole blocks, not an arc-following fill; the ring only stands 7-10 cm proud of it.
* Boulders, crags and slabs (`_chunks_mesh`, smooth angle 13 degrees) keep their stylised flat facets on purpose: only the sea stacks were reported.


---

# v2 repair round 2, 2026-10-05 (review 3: hairline slivers on the hole 8 ruin arch, tapered-obelisk sea stacks, vine tip line, hole 10 pillar)

Repair agent "libs" (round 2). Blender headless only, no git writes, nothing installed in the repo's holes / FBXs. Backup of the files before this round: `v2/libs_r2/backup/` (the frozen NEGATIVE CONTROL of the new gates).
Evidence: `v2/libs_r2/` (`smoke_full.log` = the full props smoke, **83/83 PASS**; `lsmoke_hole08|09|10.log` = the ground-lib smoke 34 / 25 / 23 PASS; `h08|h09|h10/` = scratch builds of the LIVE hole scripts against the repaired libs + `verify.log`;
`probe_r2b/` = Unity Game-view probe on those scratch FBXs (real HoleView, 900 x 1600, TennisURP) with `probe_stage_control/` (the hole fixers' existing stage, same probe) as the control; `img/` = previews; `tools/` = every measuring script; `final_run.sh` reruns all of it).
Files changed: `blender/scripts/postcard_props_lib.py`, `postcard_props_smoke.py` (+ `postcard_look_lib.py`: one change, below). **The hole scripts must be re-run: hole 8 (arch, vines, every stack), hole 9 (every stack cluster), hole 10 (basalt skin lean).**

## Findings and what changed

| finding (review 3) | root cause (measured) | fix | gate |
|---|---|---|---|
| medium, hole 8: the ruin arch still has hairline slivers across its face | **(1) real cracks.** Round 1 drew the extrados radius (-1..+4.5 cm) and the front offset (0..3 cm) per ring wedge and hid the shared radial side faces. Wherever two neighbours differ, the proud wedge's side face (hidden) leaves a hollow slot: a ray at an oblique angle enters the stone through the joint and sees its inside (back faces are culled) = a 1 px pale / dark diagonal. The same happened at the spring: the wedge (proud by 2 cm) rests on the pier top, its bottom face hidden, leaving a 1.9 cm slot between the pier-top face and the wedge's chamfer. The round-1 gate ARCH_NO_SEE_THROUGH casts frontal +Y rays only: blind. Measured with oblique rays: 143 of 274,652 (0.052 %) at the hole 8 arch (9.1 m span), 124 of 223,972 at 7.5 m, 47 of 85,680 on the broken span-6 arch. **(2) the joints themselves read as scratches:** the chamfer faces of a joint carried the stone texture, so a joint was a lit or shaded 1 px line whose colour depends on the sun; the courses stood at random heights, cutting through painted blocks; the step between the ring and the recessed haunch was a pale, lit step face seen at a grazing angle (the long curved line from the keystone to the spring) | `_arch_mesh_try` rewritten: **wedges flush** (same extrados radius, no front offset; only the keystone is larger and keeps its side faces), block side faces are hidden only where the neighbour's face is identical; a broken top that ends at different heights keeps its shared side face; **mortar joints:** every joint chamfer (`_cut_block(..., joints=)`, tag 1) and a 15 cm strip along the extrados step (`strips=`, squeezed 3.4:1 to stay inside the mortar row) carries a UV on a MORTAR ROW of Masonry_C (`masonry_grid()` measures pitch 0.500 m / phase 0.254 m / row V 0.0635 / depth 0.070 from the PNG, so a re-generated texture follows; `_mortar_uv`: isotropic or squeezed <= 3.5:1, V extent < 6 px); **courses on the mortar grid:** the pier is n whole pitches (plinth top = spring - n x pitch), course and haunch-row heights are multiples of the pitch, the mesh carries `lk_uv_voff` (v = (z - voff) / tile puts a mortar row on the spring line), so a geometric joint plane IS a painted mortar row (one bold joint, no extra line through a stone); haunch recessed 12 cm (`HAUNCH_RECESS`) so the ring's step is a clear dark band instead of a hairline. API, `dims` keys (+ `voff`, `plinth_h`, `pitch`), the plinth footprint, the arch height and the vine points are unchanged: hole 8's own gates ARCH, ARCH_FALLEN_BLOCKS_REST, ARCH_OPENING_CLEAR, ARCH_NOT_HIDDEN_BY_NEEDLES all PASS in the scratch build. Polygons 489 -> 429 (hole 8 size) | **ARCH_NO_OBLIQUE_LEAK_08 / _09_BROKEN / _SMALL** PASS: 0 of 154,420 / 47,740 / 40,796 oblique rays enter through a crack; NEGATIVE CONTROL (the start-of-round arch): 71 / 21 / 16 leaking rays. **ARCH_JOINTS_ON_MORTAR_ROWS** PASS: painted luminance at the 5 exposed joint planes 0.405 vs stone 0.474 (mortar rows 0.371); control 0.489. **ARCH_JOINT_FACES_MORTAR_UV** PASS: 147 of 429 faces, none > 0.3 m2. The old ARCH_NO_SEE_THROUGH / PIER_COPLANAR / NO_DEEP_SLITS / FACES keep passing (0 pass-through of 69,469 rays, max relief 2.0 cm, 429 polygons) |
| low, hole 8: a 1 px white line hangs from a vine tip | **not reproducible as geometry**: rays through the 8 x 140 px region at 0.25 px steps hit only the vine stub and the sea stack (`tools/pixel_probe.py`), a 6x Blender crop shows leaf + 5 px stub and nothing below; the Unity pixels are a 2 px wide, 40 px long line (252,238,194) over sky (255,248,182): R -3, G -10, B +12 (bluer, not greener) that no vine geometry in the .blend can produce. The vine stalk, however, WAS sub-pixel at the tip (ring radius 0.02 -> 0.01 m = 1.7 cm across = 0.9 px at 25 m) | stalk ring radius 0.026 m tapering to x 0.65 (4.5 cm -> 2.9 cm across; was 3.5 -> 1.7 cm): 1.6 px at the tip at 25 m (was 0.96 px) | **VINE_TIP_WIDTH** PASS: 2.9 cm at the tip (>= 2.7), 4.5 cm at the top (>= 4). The hairline in the Unity still is NOT claimed fixed (only the thin stalk is); re-check it in the next Game-view still |
| low, hole 8: sea stacks are straight symmetric tapered obelisks with pointed bright-green pyramid caps | the summit was a 4-9 triangle pyramid of LK_ROUGH (the tuned bright ground rough) on a straight concave profile with leans of 3-5 % | `_spire_mesh_try`: the summit is a **flared neck + overhanging shrub dome**: the top ring flares into a lumpy 7-corner dome (3 rings + apex, off-centre, jitter 20-34 %) of **LK_PLANTS faces** with ONE atlas swatch per face (G_DEEP / G_DARK / OLIVE_DARK / G_MID / OLIVE only: muted, dark base to lighter top; UV tag 2 in `_MB`, `_variant` keeps them in the _WET / _BASALT twins); the dome is sized from the MEASURED neck radius (overhang 0-15 %) and sits exactly under the design summit (`HC_T = min(1.7, 0.085 H + 0.2)`, the mesh keeps its documented height H); **asymmetry:** lean 9-12 % of the height (was 3-8 %), an S-bend of the axis (`bend`, 3-5 %), a swelling low on the stack (`bulge` 10-20 % at u 0.16-0.24: bulbous foot); top radius ratio raised (0.25-0.35) so the neck carries the dome; ledge grass is patchy LK_ROUGH only (no green top fifth). 377-479 faces (limit 500) | **SPIRE_SHRUB_CROWN** PASS: crown 35-37 faces, summit at the design height (13.00 / 18.00 / 24.00 / 16 / 21 / 11 m), crown / neck width 1.1-1.5, axis offset 0.07-0.11 H, muted swatches only; control (start-of-round stack): 0 LK_PLANTS faces. SEASTACK_TAPERED, SPIRE_TAPERED, SEASTACK_CRAGGY, LIB_FACES, UV_TILE_UNITS / UV_IN_SWATCH (extended to the crown faces), PLANTS_ONE_MATERIAL (spires allowed) all PASS (taper 0.27-0.35 <= 0.45, band rise <= 1.06, fill <= 0.60) |
| medium, hole 10: the pin pillar reads as a flat-topped slab with horizontal blocks, no rim light, a 2 px flag | the pillar wall is the frozen TERRAIN wall (build_terrain undercut) + the basalt skin. The 5 horizontal courses are the **backing sheet's rows** (one per terrain wall ring: z 0 / 1.25 / 2.5 / 3.75 / 5 m, 5 cm in front of the wall) that show wherever a prism does not stand clear of it, and every row gets its own UV window from `hole10_look.author_uv`. The prisms follow the wall by ONE straight lean fitted at z -1 and stand only 0.05-0.4 m proud of the lip, so on the curved wall they were level with the wall + sheet over much of the height (Game view: a flat dark sheet with vertical dashes) | `postcard_look_lib._basalt_loop`: the outer face of every prism of the outer row stands >= `BASALT_MIN_RELIEF` (0.14 m) proud of the lip, and the lean is limited so that it stands >= 0.14 m in front of the wall at 8 heights (never in plan beyond the lip + 0.4: the keep-out against the scoring lava ellipse is unchanged). **What the library cannot do:** a rounded / tapered underside: the NON-up triangles of the TERRAIN walls are a frozen collision body (verifier PLAY_SURFACE_WALLS, hole gate H_LOOK_TOP_SURFACES_UNCHANGED compares every ground vertex): a `taper_pillar_wall` experiment moved 288 wall vertices and failed H_LOOK_TOP_SURFACES_UNCHANGED (13.7 m), so it was REMOVED; the visible taper stays the wall's (21 m at the lip -> 17 m at the lava line, undercut_m is the hole script's knob). The lava rim glow gradient is a UV choice of `hole10_look.author_uv` (pick the Basalt_E glow windows for faces below z ~ 1.5 m), the flag is a gameplay object (MAT_FLAG, size): both belong to the hole 10 script | **LIB_PILLAR_COURSES_NOT_STACKED** (`tools/pillar_seams.sh`, Blender 3x crop at the approach camera, NOT Game view) PASS: row-to-row luminance step std 0.161 / max 1.02 (limits 0.6 / 4.0) vs the control (the stage on the old lib) 1.263 / 12.94; vertical-streak ratio 2.33 -> 3.24. Game view (probe, lavaedge address camera = the approach framing): streak ratio 2.46 -> 2.93, the courses are gone from the middle ~70 % of the wall, they remain at the two ends (`img/gameview/pillar_stage_vs_new.png`). Ground-lib smoke 23 / 34 / 25 PASS on 10 / 08 / 09, hole 10 scratch build 21 / 21 build gates PASS |
| low, hole 10 / 9: texture-space UV anisotropy of cladding, DRESS_BLOCK_A p95 2.21, DRESS_CONE p95 2.17 | box projection: a face tilted 45-60 degrees off its projection plane has a 1.4-2:1 Jacobian by construction; library DRESS_BLOCK p95 1.07 (round 1, `tools/uv_stretch.py` unchanged); the cone's UV is rewritten by `hole10_look.author_uv` anyway | none (note); the verifier's UV_DENSITY passes on all three scratch builds | verifier UV_DENSITY PASS (hole 8 / 9 / 10) |
| low, all: LK_SURF patches are an interpretation of "delete the foam strips" | no WATER_FOAM / MAT_FOAM exists; the small white patches at the cliff bases are the shore whitewater the brief's stills show | none from the lib (the gate NO_FOAM_STRIP: longest run 7 m, shortest gap 9-15 m, coverage 16-17 % of the shore); mentioned for the user | verifier NO_FOAM_STRIP PASS |

## Numbers (final_run.out, the whole run on the final files)

* Props smoke `v2/libs_r2/smoke_full.log`: **83/83 PASS in 70 s** (76 old + ARCH_NO_OBLIQUE_LEAK x3 + ARCH_JOINTS_ON_MORTAR_ROWS + ARCH_JOINT_FACES_MORTAR_UV + VINE_TIP_WIDTH + SPIRE_SHRUB_CROWN; no old gate weakened: the SEASTACK_TAPERED face window and numbers are unchanged, UV_TILE_UNITS / UV_IN_SWATCH / PLANTS_ONE_MATERIAL were extended to the crown, `solid()` of the arch gates reads the plinth from `dims`).
* Scratch builds of the live hole scripts (`h08|h09|h10`): hole 8 build 35 gates / 0 FAIL, hole 9 16 / 0, hole 10 21 / 0; `postcard_look_verify`: hole 8 **96 / 96 ALL PASS**, hole 9 **92 / 92 ALL PASS**, hole 10 97 / 99 (the 2 failing lines are `GROUND_UV_LOCAL_SMEAR` on FAIRWAY_FIRSTCUT, 3 triangles of 103 m2 at 1000:1; they fail identically on the hole fixer's existing stage: not caused by this round, a hole 10 script item).
* Unity Game-view probe on the scratch FBXs (`probe_r2b/probe_report.txt`, TennisURP, 900 x 1600): 60 gates PASS, 3 FAIL, the same 3 as the control run on the hole fixers' stage FBXs (`probe_stage_control/`): PROBE_SURF_ALPHA hole 8 / 9 (an old gate that encodes the superseded continuous-surf design, RUNTIME K.3 #3) and PROBE_LAVA_LIGHTS_REACH_BASALT hole 10 (1.0 % of the visible basalt lifted by the lights in both, a lights / witness-view item of the hole 10 script and the runtime). `img/gameview/tee_stacks_old_new.png`: the hole 8 tee still (installed, 22:56) against the same address camera on the scratch build: the stacks lean and bend, the caps are dark shrub domes.
* guards.sh: 7 PASS.

## Hand-off (what the hole fixers do after this)

1. Re-run the three hole builds (`hole08_build.py`, `hole09_build.py`, `hole10_build.py`: unchanged scripts, only the libs moved) and their stage gates; nothing in the API changed (new optional `_cut_block(joints=, strips=)`, `_finalize(uv_voff=)`, `_spire_mesh(bend=, bulge=, bulge_u=)`, `masonry_grid()`, `BASALT_MIN_RELIEF`, `HAUNCH_RECESS`).
2. Hole 8: the arch dims now also carry `plinth_h` (0.51 m at the 9.1 m span, was a constant 0.36), `pitch`, `voff`; the pier is a whole number of 0.5 m pitches: `hole08_look`'s outcrop fit is unaffected (foot vertices at z 0).
3. Hole 10 script (not mine): author_uv could give the backing sheet faces one window per COLUMN (the same u across the rows) and the Basalt_E glow windows to the faces below z 1.5 m (the lava rim light), and the flag could be sized / coloured for the approach camera; the TERRAIN wall taper is a `build_terrain(undercut_m=)` question that the frozen collision body (PLAY_SURFACE_WALLS) answers: no.
4. After the rebuild + install: the Game-view stills (`run_stills.sh`) are the proof; the arch hairline of the Unity still (and the 2 px vine line) must be re-looked at there.

## Limits / not done

* No Game-view still of the REPAIRED landmark cameras (hole08_arch / hole10_approach): the real `Resources/Course` FBXs belong to the install step; the Game-view evidence here is the probe on scratch FBXs (tee / lavaedge address cameras, real HoleView and lighting) and Blender EEVEE crops at the landmark cameras (`img/after*/`, `img/h08_scratch/`, NOT Game view).
* The pillar is still a slab with a flat top: rounded / tapered underside, rim glow gradient and flag size are outside the library (frozen collision walls, hole script UV and gameplay objects).
* The vine line is not reproducible in the .blend; only the sub-pixel stalk was fixed.
* The shrub dome is a 7-corner faceted lump (35 faces); it reads as a dark cap, not as the lush moss of needle.jpg. A bigger dome needs more faces than the 500 budget leaves with 25+ strata rings.
