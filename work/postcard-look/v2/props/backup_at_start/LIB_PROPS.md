# LIB_PROPS — role A4: Blender props library (POSTCARD_LOOK)

Status 2026-10-03 22:10: built, **38/38 smoke gates PASS**, guards.sh 7/7 PASS. Blender only (headless), no Unity run, no git writes.
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
| `ROCK_SEASTACK_A` 17 m stepped stack | 129 | 210 | 226 | 8.3 x 8.3 x 21.1 (z -3..18.1) | LK_ROCK + LK_ROUGH ledges |
| `ROCK_SEASTACK_B` 12 m leaning stack | 119 | 196 | 210 | 7.1 x 7.8 x 15.6 (z -3..12.6) | LK_ROCK + LK_ROUGH cap |
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
