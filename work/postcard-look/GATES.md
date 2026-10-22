# POSTCARD_LOOK — Blender-side gates (role A5)

Tool: `blender/scripts/postcard_look_verify.py` (owner A5). Authority: `ArtDir/environments/14_POSTCARD_LOOK.txt` (GATE POSTCARD_LOOK +
per-hole FAIL lines) and `LOOK_CONTRACT.md`. **A Blender PASS is never the Game-view PASS**: these gates prove the meshes, names,
materials, UVs and files that the Game view needs. What only eyes can judge is in `VISUAL_CHECKLIST.md`.

## Run

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
# check one hole: opens blender/hole_0N.blend, then re-imports Unity/Assets/Resources/Course/hole_0N.fbx into an EMPTY scene
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 8 [--json out.json] [--blend P] [--fbx P] [--no-blend|--no-fbx]
# prove every gate can PASS and FAIL (writes ONLY under DIR; ~50 s for all three holes)
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- all --selftest --selftest-dir DIR [--keep]
# frozen play-surface signature: built ONCE (done 2026-10-03 21:44), refuses to overwrite without --force
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- all --build-baseline
```

Output: `GATE: <ID>@<stage> PASS|FAIL - <measured numbers>` (stage `blend` = the export set of the opened .blend, i.e. every
MESH/EMPTY in COURSE/ENVIRONMENT/STRUCTURES/GAMEPLAY + the root, exactly what `postcard_lib.export_fbx` exports; stage `fbx` = every
object of the re-imported FBX; file-level gates have no stage), `INFO:` measurement lines, `RESULT: ALL PASS | FAILURES [...]`.
Exit 1 on any FAIL; a gate that raises FAILS (fail closed). `--json` writes every gate + info line. Runtime ~1-3 s per hole
plus Blender start. Read-only on every input (it never saves a .blend or writes an FBX in check mode).

## Baseline signature (`work/postcard-look/baseline_signature/hole_0N.json + .npz`)

Built once from `work/postcard-look/baseline/blender/hole_0N.blend` (sha 38c25178 / 8846a99f / b0c478e6) and
`baseline/fbx/hole_0N.fbx` (d19a46b6 / 88005a32 / e99475de), recorded in the json with the npz sha256. Per stage (blend, fbx):
the collision-prefix object names; for every TERRAIN/FAIRWAY/GREEN/TEE_BOX/BUNKER/CART_PATH mesh the sorted world vertex set
(rounded 1e-4 m) hash of the up-facing (nz > 0.5) vertices and of all vertices + the arrays; MARKER_TEE/PIN/UP and the gameplay
placeholders (FLAG, FLAG_POLE, HOLE_CUP, BALL_START, TEE_MARKER_1/2) world positions; every object name; a GroundHeight grid:
single-sided (front faces only, like a Unity MeshCollider) downward rays from z 1000 over the collision meshes, 1.5 m step over
the design shore bbox (+ water ellipses) + 3 m: hole 8 39x231 = 9,009 rays (2,137 hit ground), hole 9 93x347 = 32,271 (16,110),
hole 10 187x136 = 25,432 (3,948). Blend vs FBX of the same baseline: 0 hit/miss mismatches, max dz 0.31 mm (the FBX cm round
trip), so each stage is compared with ITS OWN baseline stage, never blend with FBX.

## Gates

`brief` = the line of 14_POSTCARD_LOOK.txt (or LOOK_CONTRACT) the gate transcribes. Thresholds marked * are A5 decisions (the brief
names the thing, not a number); every one is a constant at the top of the script (`TH`, `PROP_FACES`, ...).

### File level
| gate | brief | measurement / threshold | why |
|---|---|---|---|
| BASELINE_SIGNATURE | KEEP: shore, centerline, pin, play height unchanged | signature json + npz present, npz sha matches | the frozen gates below cannot run without it |
| HOLE07_UNTOUCHED | "hole_07.fbx is unchanged" / "Do not edit hole 7" | sha256 of hole_07.blend, .fbx, .fbx.meta = guards.sh hashes | same hashes as `guards.sh` |
| FBX_FILE@fbx | budgets; contract §4 | FBX exists, <= 20 MB; .meta has `isReadable: 1` and `tangentImportMode: 3` | contract §6 budget; Unity needs readable meshes + imported tangents for normal maps |
| FBX_REIMPORT@fbx | "FBX re-import ok" | Blender re-imports it; MARKER_TEE/PIN/UP present | HoleView maps the hole by these markers |

### Frozen scoring geometry (per stage)
| gate | brief | measurement / threshold | why |
|---|---|---|---|
| PLAY_SURFACE_NAMES | "HoleView only collides meshes whose names start with TERRAIN, FAIRWAY, GREEN, TEE_BOX, BUNKER, or CART_PATH" / "Do not rename a play surface" | set of objects with a collision prefix == baseline set, all MESH | a new collision-prefixed prop gets a MeshCollider |
| PLAY_SURFACE_GRID | "Shore, centerline, pin, play height ... unchanged" / "One play height" | every grid ray: same hit/miss, same hit object, |dz| <= 1e-3 m | this is GroundHeight, sampled exactly as Unity does it |
| PLAY_SURFACE_TOPS | contract §0: top surfaces keep exact outlines and heights ("bit-identical", §1) | up-facing vertex set of every collision mesh == baseline (hash; fallback: every vertex has a partner within 0.2 mm both ways) | catches outline/height edits finer than the 1.5 m grid. INFO `PLAY_SURFACE_ALLVERTS` reports wall/underside vertex changes (allowed, scoring-neutral) |
| MARKERS_FROZEN | "pin positions ... unchanged" | MARKER_TEE/PIN/UP + FLAG, FLAG_POLE, HOLE_CUP, BALL_START, TEE_MARKER_1/2 within 0.1 mm of baseline, no duplicates | the lie-relevant markers |
| RESERVED_NAMES | contract §2: no new FLAG/HOLE_CUP/BALL_START/MARKER_ | every object with those prefixes is a baseline placeholder | HoleView hides those names |
| NEW_OBJECT_PREFIXES | "Every new rock, plant, path, arch, vine, waterfall, sea stack, and the background cone must use some other prefix (ROCK, PLANT, DRESS, WATER, LAVA)" | every object name not in the baseline starts ROCK_/PLANT_/DRESS_/WATER_/LAVA_ and not with a collision prefix; offenders listed. INFO `NOT_EXPORTED` lists scene objects outside the export collections | new props never collide; non-exported objects are a common "it is in Blender but not in the game" trap |
| ONE_GREEN | "No second green." | exactly one GREEN, MARKER_PIN, FLAG, FLAG_POLE, HOLE_CUP; no other GREEN* than GREEN_APRON; LK_GREEN / LK_FAIRWAY only on the play objects | a DRESS_ disc with green grass is a second green |

### Materials, textures, UVs (per stage; LK_TEXTURED blend only)
| gate | brief | measurement / threshold | why |
|---|---|---|---|
| NO_MAT_FOAM | "No MAT_FOAM strip remains." / "Delete the white foam strips" | no mesh uses MAT_FOAM*, no object named *FOAM* | |
| NO_LEGACY_MATERIALS | "FAIL if they are still MAT_FAIRWAY / MAT_FAIRWAY_STRIPE flat colors" | every mesh material is a contract LK_ name or a gameplay MAT_FLAG/POLE/CUP/BALL; empty slots fail | any other MAT_ goes through HoleView.Palette = flat colour |
| LK_REQUIRED | shared surface work + per hole | 8: FAIRWAY GREEN ROUGH SAND PLANTS CLIFF ROCK WATER WATER_SHALLOW SURF PATH MASONRY FALL; 9: ... SCRUB MASONRY (no PATH/FALL); 10: FAIRWAY GREEN ROUGH SAND PLANTS BASALT LAVA SMOKE | each look element of the brief has its material |
| GROUND_MATERIALS | "Fairway, green, rough, sand, cliff, and rock each get a unique albedo and a normal, assigned on the material the Game view renders" / "Mow stripes ... in the fairway albedo. Not a second untextured material" | FAIRWAY only LK_FAIRWAY; FIRSTCUT LK_FAIRWAY/ROUGH; GREEN LK_GREEN; APRON LK_FAIRWAY/GREEN; TEE_BOX LK_GREEN/FAIRWAY; BUNKER_nn LK_SAND; lip LK_GREEN/FAIRWAY/ROUGH/SAND. TERRAIN tops: 8 LK_ROUGH, 9 + LK_SCRUB, 10 + LK_BASALT; walls/undersides: 8/9 LK_CLIFF/CLIFF_DARK/ROCK/ROCK_WET, 10 LK_BASALT; a 1.0 m grass lip band under PLAY_Z may use the top materials; *wall area >= 50 % LK_CLIFF* (8/9) / >= 80 % LK_BASALT (10) | "Dark stratified cliff texture on the terrain walls"; "Walls are columnar basalt". The lip band is the baseline's top wall row (centroids z 5.5) |
| ROCK_MATERIALS | "Rocks ... No albedo, no normal" (the fail) | every ROCK_*/CLIFF_ROCK* mesh only rock/ground/plant/masonry LK_ materials and >= 60 %* of its area LK_ROCK/ROCK_WET/CLIFF/CLIFF_DARK/BASALT; crater ROCK_WALL_* >= 60 % LK_BASALT | a sea stack may carry a grass cap, a rock must read as rock |
| PROP_MATERIALS | contract §2-3 | PLANT_ = LK_PLANTS; DRESS_PATH >= 60 % LK_PATH; DRESS_ARCH/RUIN >= 50 % LK_MASONRY; DRESS_CONE basalt/lava/rock; DRESS_SMOKE LK_SMOKE; DRESS_SAND LK_SAND; other DRESS_ no grass-green/water; WATER_OCEAN LK_WATER; WATER_SHELF LK_WATER_SHALLOW; WATER_SURF LK_SURF; WATER_FALL LK_FALL(+SURF); WATER_LAVA LK_LAVA | |
| LK_TEXTURED (blend) | "In the Game view, fairway, green, rough, cliff, and rock show an albedo and a normal" | for every used + required LK_: an Image Texture feeds Principled Base Color (any nodes between allowed, e.g. A3's Gamma) with the contract file (`Fairway_C.png` ...); Normal Map node fed by `<X>_N.png` into Normal (exempt: WATER*, SURF, FALL, SMOKE, PLANTS); `<X>_E.png` into Emission Color for BASALT and LAVA; every image file exists INSIDE the Look folder | blend-only by design: A3's `export_look_fbx` strips texture references and Unity's GolfLook loads the PNGs by material name |
| LOOK_FILES | "Generate new golf textures" | contract PNGs of every used + required LK_ exist in `Resources/Course/Look`, >= 64 px; albedo luminance sd >= 0.008*, normal maps mean xy tilt >= 0.006* and mean blue >= .55, emission masks max >= .25 and mean <= .5 | catches a one-colour fill. Calibrated: an 8-bit flat fill = 0.002 / 0.003, the tennis bar Island_Normal.png = 0.010, A1's Sand_C = 0.0148 (soft sand), Green_C 0.024. Readability is the eye check |
| UV_DENSITY | "show an albedo" (no UVs = one flat colour on screen) | every collision mesh and rock has a UV map; for every tiled LK_ material: area-weighted UV density (mesh space for props, world for ground) within 1/3..3 x 1/tile of the contract*, and <= 15 %* of its area with per-triangle density outside 1/4..4 x; atlas UVs inside 0..1; sheet/card UVs not collapsed; FAIRWAY/GREEN/ROUGH/SAND/CLIFF/ROCK (BASALT on 10) must be measured | catches missing UVs, 0..1-over-the-whole-hole UVs, planar UVs smeared down walls. A3's real UVs measure 0.84-1.00 x |
| SAND_NAMES | "Any extra sand in the still is a visual patch only, and its mesh name must not start with BUNKER." | BUNKER_nn count = design bunkers; every other LK_SAND mesh is DRESS_SAND_* | |

### Rocks and props (per stage)
| gate | brief | measurement / threshold | why |
|---|---|---|---|
| ROCK_NOT_ICOSAHEDRON | "No rock on holes 8-10 is a 12-vertex icosahedron." / "FAIL if ROCK_WALL_BLUNT or ROCK_WALL_FLAT is still a 12-vertex icosahedron" | no ROCK_*/CLIFF_ROCK*/ROCK_WALL_* mesh with <= 12 vertices; no 12-vertex 20-face mesh on any non-plant object except BALL_START. INFO `ROCK_DETAIL` lists rock meshes under the contract's 60-vertex target | the extension catches an icosahedron renamed DRESS_ |
| ROCK_VARIETY | "At least four unique rock meshes per hole, instanced. None of them may be the current 12-vertex icosahedron." | among ROCK_* (excl. ROCK_SKIN_*): >= 4 unique mesh datablocks with > 12 vertices, >= 3 of them used >= 2 times | instancing = shared mesh data (the FBX keeps it: one Geometry, many Models) |
| PROP_FACE_BUDGET | "meshes under about 500 faces" / "Same face budget as EnvV4" | every unique PLANT_ and loose rock (ROCK_*/CLIFF_ROCK* except SKIN/WALL) mesh <= 500 polygons, PLANT_TUFT*/PLANT_GRASS* <= 120 | contract §6 |
| PLANTS_SHARED_MATERIAL | "one shared palette" | every PLANT_* object has exactly the LK_PLANTS material | |
| PLANTS_INSTANCED | "instanced" | >= 80 %* of PLANT_* objects share their mesh with another plant | lets a few unique vines pass |
| PROPS_OFF_PLAY | "Do not spawn them on the green in a way that hides the pin" / contract §6 | no plant/loose rock whose bbox centre is >= 1.0 m* inside FAIRWAY/GREEN/TEE_BOX/BUNKER(_LIP) (all 8 points 1 m around also over them) with its top reaching that surface; none within GREEN_RADIUS + 1 m of the pin | edge tufts allowed; a rock on the cliff face under an overhang is not ON the fairway |
| NO_ANIMATION | "No animated lava, no flowing shaders, no moving platforms." | no action, driver, shape key, armature anywhere | static |
| TRIANGLE_BUDGET | budgets | <= 250,000 triangles over every exported mesh object (instances counted each time) | contract §6 |

### Water / lava (per stage)
| gate | brief | measurement / threshold | why |
|---|---|---|---|
| OCEAN_WATER (8, 9) | "Ocean uses GolfArcade/TennisWater." | WATER_OCEAN only LK_WATER, WATER_SHELF only LK_WATER_SHALLOW, no *FOAM* | GolfLook maps LK_WATER* to TennisWater |
| SURF_SHORE (8, 9) | "Whitewater comes from TennisWater [GolfSurf], not a MAT_FOAM band" / "TennisWater foam" | >= 8 WATER_SURF pieces (mesh islands over all WATER_SURF* objects), only LK_SURF, a colour attribute with alpha range >= .5 (A = shoreline closeness, contract §4); surf surface within 6 m of >= 40 %* of the shore (8) / >= 60 %* of the design `surf_stretches` (9) | the GolfSurf shader needs the vertex alpha |
| CRATER_LAVA (10) | "FAIL if WATER_LAVA is one flat orange polygon." / "Lava is lower and still scores as water" | WATER_LAVA > 500 triangles, only LK_LAVA, top z <= PLAY_Z - 3.0 m*, XY covers the scoring lava ellipse | below the play band; a WATER_ name never collides |
| CRATER_LAVA_LIGHTS (10) | "emission, so it lights the nearby rock" | 3..5 LAVA_LIGHT_nn EMPTY objects (contract §4), z in (lava top + .2, PLAY_Z + 15], within the crater rim radius + 20 m | GolfLook turns them into static orange point lights |

### Per hole
| gate | brief | measurement / threshold |
|---|---|---|
| NEEDLE_PATH | "Left pad: a pale stone path ... The path is a textured mesh on the pad, not a new CART_PATH and not a lie change." | >= 1 DRESS_PATH_*; >= 30 m2* up-facing LK_PATH, >= 15 m* long; z within PLAY_Z - .05 .. + .6; >= 95 % of its faces over land |
| NEEDLE_FLOWERS_SHRUBS_TUFTS | "shrubs, and purple flowers" / "Grass: short tuft meshes on the rough edges and around the pads" | >= 20 PLANT_FLOWER_* on land whose mesh samples >= 10 % purple from Plants_C.png (hue 250-325 deg, s, v >= .2; A4's purple flower = 50 %, white/yellow = 0 %); >= 6* PLANT_SHRUB*/BUSH* and >= 40* PLANT_TUFT*/GRASS* on land |
| NEEDLE_ARCH | "A vine-covered stone arch on its own rock, beside the bunker ... Masonry blocks and hanging vines. FAIL if it is still ROCK_LARGE icosahedra." | DRESS_ARCH_* with >= 12 LK_MASONRY blocks (mesh islands of >= 8 triangles); bbox centre within 15 m* of SCENERY arch; >= 6 m* tall; >= 6 PLANT_VINE_* touching its bbox (+1.5 m); a ROCK_* (not ROCK_SKIN_) overlapping it in plan with its top within 1.5 m of the arch foot |
| NEEDLE_WALL_VINES | "hanging vines" (on the terrain walls) | >= 6* PLANT_VINE_* within 4 m of the shore, top PLAY_Z - 2 .. + 1.5, hanging below PLAY_Z - .5 |
| NEEDLE_WATERFALL | "A waterfall off the lower right pad ... A sheet mesh plus whitewater at the bottom. It does not collide, it does not move, and it is not a platform." | WATER_FALL_* (no collider by prefix); >= 8 m2* near-vertical (abs nz <= .6) sheet from z >= PLAY_Z - 1.5 down to <= 1.5; top within 4 m of a pad edge; UV v vs z correlation <= -.5 (v runs down); <= 20 % of its area faces up above z 1 m; a WATER_SURF surface within 15 m of its foot |
| NEEDLE_SEA_STACKS | "a few sea stacks in the water" | >= 4 ROCK_* in the water (bbox centre outside the dry shore), rising >= PLAY_Z above the sea, > 12 vertices, >= 60 % LK rock material |
| NEEDLE_CLIFF_SKIN | "Dark stratified cliff texture on the terrain walls" (task: + ROCK_SKIN_*) | >= 1 ROCK_SKIN_*; skin surface within 3 m of the wall at mid height for >= 20 %* of the shore (4 m samples) |
| SPLIT_SCRUB_RIDGE | "Left ridge: olive dry scrub ... FAIL if that ridge is still the same flat green as the fairway. The scrub is a material and plant scatter." | ridge core = dry, within max ridge width / 2 of the SCENERY ridge spine and >= fairway/2 + 30 yd from the centerline (4,069 points on a jittered 2 yd grid): the visible ground (first front face going down from PLAY_Z + .8 over collision + DRESS meshes) is LK_SCRUB at >= 60 %*; >= 95 %* of up-facing LK_SCRUB area lies on the ridge side (closer to the spine than to the centerline) |
| SPLIT_NO_SCRUB_RIBBON | "Right ribbon: manicured emerald fairway" (task: NO LK_SCRUB on the right ribbon) | ribbon core = dry, within fairway/2 + 10 yd of the centerline and >= 30 yd from the spine (4,033 points): 0 LK_SCRUB; no play mesh uses LK_SCRUB |
| SPLIT_RIDGE_SCATTER | "olive dry scrub, rocks" / "plant scatter" | on the ridge side: >= 30* PLANT_* and >= 8* loose ROCK_* |
| SPLIT_RUIN | "The ruin reads as broken stone masonry, visual only. Not a pile of 12-vertex rocks." | DRESS_RUIN_* with >= 12 LK_MASONRY pieces; within 20 m* of the SCENERY ruin walls; top >= 2 m* above PLAY_Z |
| SPLIT_SHORE_SKIN | "Shore is jagged rock with a normal map ... FAIL if the shore is a smooth extruded wall in flat MAT_CLIFF gray." | ROCK_SKIN_* within 3 m of the wall at mid height along >= 50 %* of the shore |
| CRATER_COLUMNS | "Walls are columnar basalt with a normal and a crack mask." / contract: hex prisms, visibly columns | every ROCK_WALL_* and every rock in the SCENERY wall ring (+-40 m) is a column cluster: >= 5 columns (a column = a connected up-facing cap, nz > .8, whose plan hull has 5-8 corners after merging chamfer edges, with near-vertical sides under it reaching >= .6 x its diameter) and >= 45 % of its area near-vertical; column clusters cover >= 80 %* of the ring's 72 5-degree bins. Real A4 clusters: 12-27 columns / 85-98 % side; boulders, slabs, stacks, cairns: <= 5 columns / <= 42 % side |
| CRATER_PILLAR | "Pillar sides drop into the lava and read as rock, not as a green disc floating on orange. Top stays at fairway height." | GroundHeight at the pin = GREEN within PLAY_Z .. + .6; TERRAIN side faces within r_top + 3 m of the SCENERY pillar (below the lip band) >= 95 % LK_BASALT and reaching below the lava top; underside >= 95 % LK_BASALT |
| CRATER_CONE_SMOKE | "A background cone and a little smoke card behind the bowl, visual only, non-colliding." | DRESS_CONE >= wall_ring r_inner - 10 m from the crater centre; its top elevation from the tee eye (+2.2 m) >= the walls in front of it (+-4 deg azimuth) + .5 deg; >= 2 DRESS_SMOKE* with LK_SMOKE, beyond the crater rim radius |
| CRATER_SHELF_PLANTS | "Plants along the grass shelf." | >= 10* PLANT_* standing on rough land (TERRAIN / FIRSTCUT / APRON at play height) |
| CRATER_TEE_PAD | "Square tee pad, textured." | TEE_BOX plan: min-area-rectangle fill >= .90, aspect <= 1.3 (frozen geometry: 12.8 x 11.0 m, fill .99, aspect 1.17) and LK_GREEN/LK_FAIRWAY (+ UV_DENSITY) |

## Evidence (2026-10-03)

* **Baseline** (`work/postcard-look/baseline/...`, = the current `blender/hole_0N.blend` + Unity FBX, sha unchanged): every frozen gate
  PASS (grid max |dz| 0, 0 mismatches), look gates FAIL as the brief says: hole 8 30/71 pass, hole 9 32/67, hole 10 32/67 (e.g.
  NO_MAT_FOAM, NO_LEGACY_MATERIALS, ROCK_NOT_ICOSAHEDRON 87/450/227 rocks, CRATER_LAVA 2 triangles, CRATER_COLUMNS 1 column per wall
  rock, no path/arch/waterfall/ruin/scrub/plants).
* **Self-test** (`--selftest all`): a synthetic positive per hole built on the frozen baseline geometry (written only under the
  self-test dir) passes ALL gates at both stages (71/67/67), then 109 negative mutations each make their named gate FAIL
  (green up 2 mm, pin moved 1 cm, plant renamed BUNKER, MARKER_/ARCH names, MAT_FOAM strip, MAT_FAIRWAY, 12-vertex rock, one rock
  mesh, normal link removed, UVs removed / 0..1, 600-face plant, 2-material plant, unique plants, plant on the green, DRESS second
  green, BUNKER_PATCH sand, keyframed rock, 300k triangles, MAT_WATER ocean, surf removed / no vertex colour, path removed /
  floating, white flowers, 10 flowers, icosahedron arch, arch without vines / rock, vines removed, flat or upward-UV waterfall,
  waterfall without surf, stacks removed, skin removed, scrub on the ribbon, green ridge, bare ridge, ruin removed, 1 skin piece,
  blob crater walls, 1-polygon / raised lava, 0 or 9 lava lights, LK_ROCK pillar, low cone, smoke removed, bare shelf, MAT_GREEN
  tee, flat Fairway_C.png, isReadable 0, corrupt FBX, missing signature, changed hole-7 copy): **112 / 112 expectations met**.
* **Integration with the real libs** (read-only): A3's smoke builds `work/postcard-look/lib_ground/smoke_hole0N` pass every frozen
  gate and every ground/water/UV gate at blend and FBX (UV density .84-1.00 x, surf 68 % / 95 %, skin 62 % / 100 %, Split scrub
  92 % of the ridge core and 0 on the ribbon, lava 13,185 tris, 4 lights, pillar 100 % basalt), failing only the props gates
  they do not build. A scratch hole 8 = A3 smoke + real A4 props (arch, vines, flowers, shrubs, tufts, sea stacks, waterfall)
  passes ALL 36 gates (34 blend-stage + 2 file-level; 63 masonry blocks, 20 arch vines, 17 wall vines, 30 purple flowers,
  24 m2 sheet, 23 stacks).

## Decisions (made without asking; change the constant if the lead disagrees)

1. Each stage is compared with its own baseline stage (FBX cm round trip moves vertices up to 0.31 mm).
2. PLAY_SURFACE_TOPS is hard (contract: tops bit-identical); the full-vertex hash is INFO (walls may change, scoring-neutral).
3. ROCK_VARIETY counts only meshes with > 12 vertices ("None of them may be the current 12-vertex icosahedron").
4. The icosahedron check also runs on non-plant objects of any name; plants are exempt (a 12-vertex bloom is not a rock).
5. LAVA_LIGHT count is 3..5 (contract §4), not just >= 3 (URP: 2 additional per-pixel lights per object).
6. "Not a platform" for the waterfall: a WATER_ name already means no collider; the gate only rejects a mostly-flat object
   (> 20 % up-facing above z 1 m). A4's ballistic sheet measures 6 %.
7. Split's ridge/ribbon split is the design SCENERY ridge spine vs the centerline (Voronoi); cores exclude the joins.
8. The crater "walls" are every ROCK_WALL_* plus any rock in the SCENERY wall ring, so a renamed replacement still counts.
9. Textures: "not flat" thresholds calibrated on the tennis bar (see LOOK_FILES); taste is the eye check.
10. Square tee: the TEE_BOX is frozen geometry (rounded 12.8 x 11.0 m); the gate measures it and requires it textured.

## Interplay with the other gate tools (not A5's files)

* `blender/scripts/postcard_verify.py` stays the scoring authority (ONE_HEIGHT, NO_UPFACE_OUTSIDE_LAND, LIES_MATCH_MESH,
  SHORE_MATCH, HAZARD_PLACEMENT, PADS, MARKERS must still PASS). Three of its lines FAIL on any LOOK build by design: MATERIALS
  (only MAT_* names), WATER_LEVEL (every WATER* mesh must face up within z 0..0.2: a WATER_FALL sheet is vertical) and
  FBX_BUDGET (4 MB / 150k tris; LOOK budget is 20 MB / 250k). Their LOOK replacements here: NO_LEGACY_MATERIALS +
  GROUND/ROCK/PROP_MATERIALS, CRATER_LAVA / OCEAN_WATER, FBX_FILE + TRIANGLE_BUDGET. Lead decides whether to patch postcard_verify.
* `Unity/Assets/Editor/PostcardImportCheck.cs` palette-override counts and lava colour gates need LK-aware updates (CONTEXT.md);
  its ground-height / lie / marker gates must stay.
* `work/postcard-look/guards.sh` = the hole-7 / Hole.cs / Postcards() lines (HOLE07_UNTOUCHED here uses the same hashes).

---

# v2 2026-10-04 — POSTCARD_LOOK CONTINUE: repaired and new gates (area V, Blender-side)

Owner files: `blender/scripts/postcard_look_verify.py`, this file, `v2/gates/` (evidence, fixtures, tools). Authority for this pass:
`ArtDir/environments/14b_POSTCARD_LOOK_CONTINUE.txt` (the user's seven fix lines + GATE POSTCARD_LOOK) on top of `14_POSTCARD_LOOK.txt`.
Rows above that are listed in "Superseded" below were replaced; every other row is unchanged. **A Blender PASS is never the Game-view PASS.**

## Run (new bits)

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 8 --json out.json            # blend + FBX of one hole, ~3-8 s
$B -b ... -- 9 --blend X.blend --fbx X.fbx --look-dir DIR                                                 # any build, any texture folder
$B -b ... -- all --build-face-baseline                       # ONCE (done 2026-10-04): hole_0N_faces.npz/json next to the vertex signature
$B -b ... -- all --build-nonup-baseline                      # ONCE (done 2026-10-04 14:15, round 3): hole_0N_nonup.npz/json = the walls / undersides
$B -b ... -- all --selftest --selftest-fbx --selftest-dir DIR # ~10 min: positives + every mutant at blend AND FBX stage; ends with one
                                                             # `SELFTEST_GATE <ID> MUT_FAILS_ON_BAD a/b ..; MUT_PASSES_ON_GOOD c/d ..` line per v2 gate
$B -b ... -- 8 --selftest --selftest-only tex_lava,stacks     # only mutants whose names contain a fragment (blend stage unless --selftest-fbx)

# fast iteration on one gate function of one file (v2/gates/tools/run_gate.py; also the reviewer's attacks, tools/skeptic_mut.py = a pointed copy of review_V/mut.py)
$B -b --factory-startup --python work/postcard-look/v2/gates/tools/run_gate.py -- 8 file.blend|file.fbx g_no_foam_strip,g_rock_variety [look_dir]
$B -b --factory-startup --python work/postcard-look/v2/gates/tools/skeptic_mut.py -- 8 fbx1 foam_squares_touching_off2,st_shear_parent      # needs --selftest ... --selftest-dir v2/gates/st first
python3 work/postcard-look/v2/gates/tools/summarize_mut.py work/postcard-look/v2/gates/runs/selftest_all_fbx_r3.log                              # per-gate MUT_FAILS_ON_BAD / MUT_PASSES_ON_GOOD table
```

Measurement helpers a hole-build agent can call (all in `postcard_look_verify.py`, pure functions of a `Snap`): `white_geometry`, `fall_sheets`, `white_reach_cover`, `white_union_runs`, `rock_shape`, `rock_components`,
`manifold_patches`, `open_edge_fraction`, `lib_fuzzy_match`, `nonup_tris`, `shape_families`, `lib_signature`, `mesh_components_world`, `albedo_structure`, `pair_correlation`. Probes: `tools/probe_lib_kinds.py` (valences of the library), `probe_shape.py`, `probe_amin.py`, `probe_repeat.py`; round 3: `probe_cluster.py` (welded clusters vs the library), `probe_open.py` (open-edge share), `probe_mindist.py` (smallest vertex distances), `probe_patch_stats.py` (per-patch valence / edge / area statistics: library vs perturbed icosahedra).

## What the unit of measurement is (read this before reading a number)

* **Real shoreline = the boundary loops of the TERRAIN top** (`terrain_loops`, from the mesh itself), not the design `SHORE` polygon: Needle's polygon is
  737 m because it also spans the water between the pads, the three real pad loops are 522 m, Split 1,895 m. Surf coverage, runs, gaps and shelf width
  are measured along these loops (every 2 m, outward normal into the sea), one circular list per loop.
* **Textures are measured from the PNGs in `Look/`** (stored sRGB values, `image.pixels`), not from what Unity imports. The structure window is 1/16 of the tile edge (1024 px: 64 px = 0.6 m of a 10 m Fairway tile, 0.375 m of the 6 m Green tile).
* Meshes are measured **per stage**: the opened `.blend` (export set) and the re-imported FBX, both through the same functions.
* Play surfaces are NOT one height: rough 6.00, first cut 6.08, fairway 6.14, apron 6.18, tee 6.24, green 6.26, bunker 6.30 (Needle). Anything "above the ground
  beneath" is measured against the single-sided collision ray at that (x, y).

## Gate table (v2). `MUT` = mutation tests run by `--selftest` (each must FAIL its gate; controls must PASS it)

| gate | brief line | measurement / threshold | why / calibration | MUT (bad -> FAIL, good -> PASS) |
|---|---|---|---|---|
| **ROCK_NOT_ICOSAHEDRON** (repaired three times; **area U: rocks are classified by SHAPE and MATERIAL, not by name, see 'v2 area U' below**) | "No rock on holes 8-10 is a 12-vertex icosahedron" (+ the reviewers' findings) | every `ROCK_*`/`CLIFF_ROCK*` mesh except `ROCK_SKIN_*` is judged on the WELDED mesh (merge 1e-4 with two half-cell grids; degenerate, < 1 % of the median area and duplicate faces dropped): >= 60 welded vertices, >= 100 faces, >= 6 planar-facet orientations (polygon normals in 16 deg cones holding >= 2 % of the area), NOT sphere-like (PCA-whitened radius cv < 0.15), NOT a regular tessellation of a round solid, NOT a box (>= 85 % of the area on three orthogonal planes), and **every connected component is judged on its own vertex-valence topology** (`rock_components`, polygon mesh, interior vertices only): FAIL for a component with 6..64 interior vertices taking <= 2 distinct valences (icosahedron {5}, octahedron {4}, cube / dodecahedron / football {3}, jittered or stellated or not), for a ROUND larger lattice with <= 2 valences (UV sphere: whitened radius cv < 0.15), and for a geodesic sphere (>= 30 interior vertices, >= 95 % valence 5/6 with 8..16 fives: any subdivided icosahedron, noised +-40 % or not). Hex-prism basalt columns (>= 60 % of the area on vertical faces) are exempt. Any non-plant object that welds to 12 vertices / 20 faces fails whatever its name **Round 3: components are SURFACE PATCHES** (`manifold_patches`): polygons are joined only across MANIFOLD edges (an edge used by exactly two polygons), a vertex or an edge that cells merely TOUCH at is duplicated per patch - so every icosahedron / icosphere / octahedron / cube of a welded cluster is judged as its own closed solid (a cluster of 6-14 icosahedra has valences {5, 10, 15, ...} on the welded mesh, 6-14 patches of 12 interior vertices with valence {5} in the patch view); the exact-regular-solid-by-area test uses the same patches. **Closed-solid rule** (`open_edge_fraction`): <= 10 % of the polygon edges of a rock mesh may be open (library hull rocks, spires and stacks: 0 %; basalt prisms, >= 60 % vertical area, have open bottoms and are exempt) | v1: raw vertex count (split / padded icosahedra passed). v2 round 1: shape tests on the welded mesh. v2 round 2 (review): a bundle of 5-8 jittered 12-vertex icosahedra (60-96 vertices, 100-160 faces) passed everything because jitter beats every geometric test; valences do not change with jitter. Measured on the props library (`probe_lib_kinds.py`, 11 land rocks, 5 sea stacks + spire, 6 + 6 basalt kinds): every hull component has 15-38 vertices and 3-6 distinct valences ({3..8}); the only 5/6-only component is a 20-vertex ROCK_CRAG_A piece (so the geodesic rule starts at 30 vertices); library rocks are bundles of 2-6 such hulls (ROCK_CAIRN_A = 6 stones of 15-16 vertices) so the bundle itself is legitimate, regular components are not round 3 (review): a welded cluster of 6-14 exact 12-vertex icosahedra sharing vertices passed (valences {5,10,15,..} are >= 3 distinct). My own follow-up probe of the next dodge: a bundle whose every face is split off by 2 mm (beyond the 1e-4 weld) is a triangle soup of single-triangle components, no interior vertex, and passed every valence rule until the closed-solid rule (100 % open edges). Measured with `tools/probe_cluster.py`: 96 welded clusters (12 / 42-vertex icosahedra, octahedra, cubes x vertex / edge sharing x jitter before / after the weld x n 4..14) ALL FAIL, the 29 props-library kinds ALL PASS (`tools/probe_open.py`: library open-edge share 0 %, basalt 31 % exempt; `tools/probe_mindist.py`) | 12-v ico, ico split to 60 v, ico + 60 loose verts, icosphere subdiv 3, UV sphere 24x12, subdivided cube, **bundles of 5-8 jittered 12-v icosahedra (all rocks / loose rocks only), bundles of 42-v icospheres, icosphere subdiv 3 with +-40 % noise**; positive = hull rocks, spires, column clusters, the real props library (60 rock objects, 10 meshes) | **round 3: welded clusters of 12-v icosahedra (varied sizes, all rocks / loose only), with 12 % jitter after the weld, of 42-v icospheres, of octahedra; bundles of icosahedra with every face split off by 2 mm (all / loose only)**; control: welded clusters of natural hull stones PASS
| **ROCK_VARIETY** (repaired twice; round 3: unchanged, it inherits the patch rule) | ">= 4 unique rock meshes per hole, instanced" | among shapes that pass the test above: >= 4 unique SHAPE FAMILIES and >= 3 families with one mesh datablock used by >= 2 objects. Two meshes are ONE family when their topology hash is equal (welded vertices, faces, vertex-valence histogram: independent of scale, stretch, rotation, name) OR they are geometric near-duplicates (PCA extent ratios r2 = lambda2/lambda1 and r3 within 0.04 of each other, welded vertex counts within 10 %, planar-facet orientation counts within 2; union-find) | the v2 detail line claimed PCA ratios + facet shares while the code hashed only counts and valences: bundles of n = 5..8 icosahedra gave four 'unique' shapes. Now the one-extra-chip variants of one hull are one family. Library: 10 meshes of the props test hole 8 = 7 families, hole 10 = 5 | one mesh for all, the same mesh copied into unique datablocks, **one hull re-issued as six edge-split variants with 2 % jitter (topology hash differs, geometry does not)**, every blob / bundle variant above |
| **LOOK_FILES** (repaired twice; round 3: provenance / lead decision; **area U 2026-10-04: the floor is now the stills' own, see 'v2 area U' below**) | "Generate new golf textures", albedo + normal must be real | spatial structure, not noise, **at a footprint that does not depend on the resolution**: grass ground albedos (Fairway, Green, Rough, Scrub): luminance sd >= 0.03 in >= 90 % of the windows of **1/16 of the tile edge** (64 px of a 1024 px map, 32 px of a 512 px map, 8 px of a 128 px map) AND sd >= 0.4 x floor after 8x8-ish block averaging in >= 90 % (white noise has no block structure); other opaque albedos >= 0.012 (Sand 0.008) at the same shares; **ground albedo and normal maps must be >= 512 px, other albedos / normals >= 256, cards >= 128** (contract: 1024 / 512); ground albedos are not periodic: <= 25 % of the spectral power above 5 cycles/tile in ONE frequency (an 8 px checkerboard holds ~100 %, grass < 5 %); alpha is NEVER a shortcut (RGB only) except for Surf / Fall / Smoke where the alpha IS the map (alpha sd >= 0.05); normals: xy deviation sd >= 0.04 AND neighbour autocorrelation >= 0.30 AND mean blue >= .55; emission max >= .25, mean <= .5; Plants_C >= 12 distinct swatches | the review: a fixed 64 px window made the verdict depend on the file size (Fairway_C 1024 px FAILED, the same artwork downsampled to 128 px PASSED), and a grass albedo that is an 8 px checkerboard of 14 % contrast passed. The numbers 0.03 / 90 % / 64 px-at-1024 are the lead's; **calibration against the stills is impossible below ~1.5 m footprint** (`calib/still_calib.txt`: the 1280x720 stills' mown fairway / green crops measure window sd median 0.02-0.04 at 8-16 still-pixel windows = 1-3 m of ground, 0.05-0.13 at 32 px; the 0.4-0.6 m windows of this gate are below one still pixel). The real Look folder FAILS this gate today (Fairway_C 1 % of windows, Green_C 0 %, global sd 0.047 / 0.025: a smooth mow) - the tex agent must add blade-scale detail or the lead must lower the floor; the tool does not decide **LEAD DECISION, not a measurement (round 3, review low item).** The floor 'luminance sd >= 0.03 in >= 90 % of the windows' is the number in the lead's task (A.2: 'at least 90 % of 64x64 windows for ground albedos'); the tool only made the window a FOOTPRINT (1/16 of the tile) so it no longer depends on the file size. It was NOT calibrated on the stills and cannot be: `calib/still_calib.txt` measures the user's stills at 8-16 still-pixel windows (1-3 m of ground) as sd >= 0.03 in only 31-67 % of the windows of the mown fairway / green crops (split upper_green 31 %, fairway_strip 67 %), and 100 % only at 32 px. If the lead wants a floor grounded in the stills, lower `TH2['win_frac']` (0.90; e.g. to 0.5) or `TH2['win_sd']` (0.03, the grass ground albedos' window floor): two named constants, nothing else changes; if the lead keeps 0.03 / 90 %, the tex agent has to add blade-scale detail to Fairway_C / Green_C. The tool does not tune either to the live files, which FAIL today (Fairway_C 1 % of windows, Green_C 0 %) | flat RGB + random alpha, near-flat sd 0.0095, flat fill, flat normal + dither, flat lava (also LAVA_TEXTURE), **the synthetic Fairway averaged down to 128 px, an 8 px checkerboard**; the synthetic ground maps are 512 px with blade-scale detail (window p10 0.05) |
| **ALBEDO_DISTINCT** (repaired twice) | "a unique albedo" | among Fairway, Green, Rough, Scrub, Sand, Cliff, Rock, Path, Masonry, Basalt (those the hole uses): the channel fields (luminance, R, G, B at 64 x 64) of every pair correlate < 0.85 at every rotation, mirror and circular shift - **whatever their mean colours** (the CIE76 dE is reported, not used) | v2 round 1 allowed `dE >= 6 OR corr < 0.85`: Scrub_C = Fairway_C with hue -28 deg and value x0.85, or a channel-scaled tint (corr ~0.9) passed. Fairway and Green are the same green in the stills (dE 3.2) and their independent noise correlates 0.39 on the real Look | Green = copy of Fairway, tint x0.97, rotated copy, shifted copy; Scrub = copy; **Scrub / Green = the Fairway pattern with the hue shifted, Scrub = a channel-tinted Fairway** |
| **GRASS_ALBEDO_HUE** (new) | line 1: "grass reads ~20 degrees too blue-green ... stills sit at hue 64-73" | mean AND median pixel hue, saturation, value of the albedo: Fairway_C / Green_C hue 66-82, S .50-.90, V .40-.75 (Green .80); Rough_C hue 58-78, S .45-.90, V .28-.65; pixel hue p10..p90 inside 40-105 (no two-tone). INFO prints the estimated lit hue (albedo - 7) | stills lit hue 64-73 (Needle 65-67, Split 71-73, Crater 67-71). The golf key light measured a -6..-8 deg hue shift (albedo 94-97 -> lit 86-89): so albedo 71-80 lands in the stills' band, the bands add 4-5 deg slack | Fairway hue 97, Rough hue 95, Fairway desaturated to S .2 |
| **SHELF_THIN** (new) | line 2: "turquoise ring ... Narrow the shelf until it is a thin edge" | holes 8/9: `WATER_SHELF` visible width BEYOND the cliff skin along every shore normal (2 m samples): median <= 2.5 m, p95 <= 4 m; not a closed uniform ring (present on >= 90 % of the shore with width cv < 0.2). Width = outer edge of the shelf found by vertical rays along the normal (gap tolerance 2 m) minus the outermost ROCK_SKIN vertex offset within +-2 m. Hole 10 n/a | the old shelf measures median 15-17 m, p95 18-36 m | halo 16 m, thin closed uniform ring 1.5 m, 12 m wide broken patches |
| **NO_FOAM_STRIP** (repaired three times; replaces the cap half of SURF_SHORE; **area U: the white test also reads the sRGB-encoded base colour, see 'v2 area U' below**) | line 6: "Delete the white foam strips. A continuous white surf band is not a pass" | no MAT_FOAM / `*FOAM*` object; no DRESS_ object with LK_SURF / LK_FALL. **Foam-like geometry** = up-facing triangles of LK_SURF (vertex alpha >= .3; a PIECE that never reaches .3 counts whole, only the faded fringe of a visible piece does not), flat LK_FALL (nz >= .8) and ANY white-ish material (albedo V >= .8, S <= .15 / base colour V >= .8, S <= .2 / a name with FOAM, SURF, SPRAY, WHITE), on every non-collision mesh whatever its name. Holes 8/9: the foam reached by the shore normals within **10 m** (vertical rays every 0.5 m along the outward normal of every 1 m shore sample) covers <= 25 % of the shoreline, in runs <= 10 m, >= 8 m apart (per loop, circular); white area <= 1.0 m2 per metre of shoreline. All holes: foam pieces farther than 10 m from every shore loop merge when closer than 8 m (raster 0.5 m, disc dilation 4 m) and no merged piece is longer than 11 m (geodesic length minus the dilation; 10 m + 1 m raster tolerance) **Round 3: ANY ORIENTATION.** Foam-like geometry = LK_SURF triangles with alpha >= .3 (or a ghost piece), every LK_FALL triangle except a WATERFALL SHEET (`fall_sheets`: a welded LK_FALL component of plan extent <= 8 m and mean |nz| <= 0.6, at most 2 per hole and 60 m2 in total, largest first - only its flat part, nz > 0.8, counts), LK_SMOKE on anything but the DRESS_SMOKE cards, and ANY white-ish material **whatever its name (MAT_* included; only the collision meshes and the game's hidden placeholders FLAG / HOLE_CUP / BALL_START / MARKER_* are skipped)**, facing up, sideways or down. Coverage = exact 3D triangle-triangle overlap (BVH) of the foam with the vertical plane strip over every shore-normal segment (0..10 m, 1 m samples); the offshore raster draws the edges of near-vertical triangles; the area cap uses the 3D area | v2 round 1 counted only LK_SURF within 1 m of the shore and tested ribbons by per-piece constant width: touching 4 m squares laid 2-6 m off the shore and a ragged continuous band at 2.5 m both PASSED. Lib smoke (10:44): cover 19 % / 17 % (hole 8 / 9), longest run 6 / 9 m, min gap 13 / 10 m, 0.68 / 0.54 m2 per m. Lowering the alpha threshold to .15 for every piece would measure 1.04 m2/m on Needle (over the cap) - the fringe stays out round 3 (review): a continuous white LK_SURF skirt around the whole shore at nz 0.44 (a 63 degree ramp) passed every gate at both stages because only up-facing (nz > 0.5) triangles counted. My own probe found the same hole for a white material called MAT_* (up-facing only) and a vertical curtain (no plan area). All closed. The lib smoke builds are unchanged: cover 19 % / 17 %, longest run 6 / 9 m | A3's strips: 36-70 % coverage, runs 39-83 m, gaps 1 m. Patches of N m measure N m along the normals (the 1 m disc of round 1 measured N + 2) | white band as DRESS_ LK_SURF, continuous alpha-1 strip, 14 m patch, patches over 25 %, two patches 4 m apart, 3 m ribbon 8 m offshore, flat LK_FALL ribbon (also when named WATER_FALL_xx), MAT_FOAM strip, white-textured mist, **touching squares 2-6 m off the shore, ragged continuous band at 2.5 m (width 0.3-5.5 m), offshore dashes 14-17 m with 7 m gaps, a white strip made of a non-LK material, a continuous band at vertex alpha 0.29** | **round 3: continuous skirt nz 0.45 as LK_SURF, continuous vertical wall (nz 0) as LK_SURF, continuous steep ramp nz 0.1 as LK_FALL named WATER_FALL, continuous skirt nz 0.3 of a white MAT_SPRAY_SKIRT material**; control: the hole-8 positive carries a real vertical LK_FALL waterfall sheet and passes
| **SURF_SHORE** (repaired) | whitewater exists but is not a band | >= 8 `WATER_SURF` pieces, LK_SURF only, vertex colour alpha range >= .5, surf touches >= 5 % of the shore (the upper cap moved to NO_FOAM_STRIP; the old "within 6 m of 40 / 60 %" is gone) | the lead's cap (25 %) contradicts the old floor | surf removed, no vertex colour |
| **LAVA_TEXTURE** (new) | line 3: "dark polygonal cells ... swirling molten flow, mostly bright ... orange with emission alone" | composite = clip(Lava_C + Lava_E): bright (V >= .55, hue 5-40) >= 60 %, dark (V < .35) <= 25 %, value sd >= 0.10 and >= 75 % of the 1/8-tile windows with sd >= 0.04 (flow, not a flat fill); emission ALONE bright orange (V >= .5, hue 5-40) >= 40 %; emission peak texel G <= 190 and B <= 70; tiling seam error <= 1.6 x the neighbour difference (C and E); cell-network detector: connected components (4-neighbour, pooled to 256 px) of dark and of bright texels that are compact (solidity >= .80, 0.1-6 % of the tile, not touching the edge): FAIL if >= 12 cells carry >= 40 % of that mask | crater.jpg's pool measures 65 % bright / 21 % dark, a clean flow crop 79 % / 5 %; the pre-repair lava 27 % / 50 %, 58 compact dark cells = 67 % of the dark area, E peak (255,222,128) | pre-repair Voronoi crust, synthetic dark plates, bright cells with dark cracks, flat orange E + structured C, yellow E peak, tile seam, 40 % dark crust |
| **BASALT_PRISMS** (new) | line 4: "Columns should read as prisms, glow only in the joints" | Basalt_E at 512 px: glow (lum >= .15) covers < 6 %; <= 10 % of the glow area is in components that are neither vertical-elongated (h/w >= 2) nor small (<= 4 % of the tile); no horizontal glow run > 12 % of the tile width; Basalt_N: cross-joint spacing >= 3 m (thin horizontal |ny| >= .25 segments >= 4 % wide: mean count per column of the 8 m tile); bevel planes: >= 8 % of the tile width in runs (>= 2.5 % wide) of median nx >= +0.25 AND >= 8 % of <= -0.25 | pre-repair basalt: 55 % of the glow in blobs, cross-joints every 0.9 m, bevel planes 0 % (nx +-0.13 over 10-25 px) | old basalt, glow ladders, cross-joint bricks, flat bevels |
| **SMOKE_SOFT** (new) | line 4: "Smoke_C is a hard grey ball. Make it a soft wisp" | alpha border (2 px) <= 0.02; alpha max <= 0.60; alpha-weighted elongation (major / minor axis) >= 1.6; max alpha gradient <= 0.030 per texel at 512 px | pre-repair ball: alpha max .90, elongation 1.13, gradient .042; the repaired soft wisp (looked at: a soft curl) measures .026 (p99.9 .022), so the bound sits between them (first guess .025 was tighter than a visibly soft wisp). Honest note (review): .030 was set AFTER seeing the .026 artefact; the live Smoke_C of 11:09 measures .016, the hard ball .042, so .030 now sits 1.9x above the accepted wisp and 0.71x of the hard ball - an eye-calibrated bound, not a derived one | old ball, hard-edged, visible card border, opaque core, round ball |
| **SPLIT_SCRUB_RIDGE** (repaired twice) | "FAIL if that ridge is still the same flat green as the fairway" | (material share as before) AND Scrub_C mean hue differs from Fairway_C by >= 12 deg OR value by >= 0.12, AND Scrub_C is olive-khaki-dry (hue 32-70, S .20-.65, V .28-.75), AND **Scrub_C is not the Fairway_C pattern recoloured (channel-field correlation < 0.85)** | the old gate read the material NAME; round 1 accepted a hue-shifted copy | Scrub_C = Fairway_C copy, Scrub_C = another green, ridge on LK_ROUGH, **Scrub_C = hue-shifted / channel-tinted Fairway** |
| **PROPS_OFF_PLAY** (repaired twice) | contract section 6: nothing hides the pin or sits on play surfaces except the DRESS overlay allow-list | EVERY ROCK_/CLIFF_ROCK/PLANT_/DRESS_/WATER_FALL/LAVA_GLOW mesh (walls and cladding included) except `DRESS_PATH_*` and `DRESS_SAND_*`: no triangle above any FAIRWAY/GREEN/TEE_BOX/BUNKER 1.5 m grid point (vertical rays, 0.03-8 m above the ground), **and every DRESS_-type object narrower than 3 m is re-sampled every 0.25 m inside its own bounding box**, no vertex within 3 m of the pin at play height; plants and loose rocks keep GREEN_RADIUS + 1 m (unchanged) | the old one exempted DRESS_, ROCK_WALL_, ROCK_SKIN_, WATER_FALL_; round 2: a 0.7 m DRESS_ boulder between two grid points passed (any footprint >= 1.5 m cannot hide from a 1.5 m grid) | DRESS boulder 0.5 m from the pin, ROCK_WALL pile on the pin, DRESS slab over the fairway, plant on the green, **0.7 m DRESS_ boulder between grid points**; controls: DRESS_SAND overlay on rough |
| **NO_PLANT_ON_WATER** (repaired twice) | line 5: "Plants land on the water when no region is passed" | judged PIECE BY PIECE (connected pieces of the mesh, world space): the lowest piece of every PLANT_ stands on ground (z >= PLAY_Z - 1 = 5 m, a ground / rock top within -0.5..+0.4 m under it, inside the dry land when the support is ground, not on a play surface, not on DRESS_PATH); every other piece has ground or a rock top within 6 m below it; **a rock that carries a plant must itself stand on ground (the ground at the plant lies between 0.6 m under the rock's lowest point and its top) or reach below z 3 (stacks, outcrops)**; PLANT_VINE_*: attach point (top of each piece) z >= 3 m and a surface within 1.5 m | round 2: a plant mesh with a copy over the sea merged into one object and a plant on a slab floating at z 5.2 over water passed (one point per object, any rock counted as support) | plant at sea level, plant at z 6 over water, on the fairway, on the green, on the stone path, a vine attached to nothing, **a merged mesh with a copy over the sea, a plant on a floating rock slab**; control: a plant on a rock that stands on the ground |
| **NO_ROCK_STRETCH_2X** (repaired three times; **area U: anisotropy / upper cap / lower bound judged separately, rocks classified by shape + material, see 'v2 area U' below**) | line 5: "Legacy rock swap stretches wall pieces past 2x" | every ROCK_/CLIFF_ROCK/DRESS_ mesh object (DRESS_SMOKE and DRESS_CONE excepted): each **singular value** of matrix_world[:3,:3] (not the column norms: a sheared parent chain hides in them) normalised by the TERRAIN meshes' own scale is in [0.5, 2.0] and max/min <= 2.0; **baked stretch, any name, both stages**: an instance whose mesh has the TOPOLOGY HASH of a props-library kind (`lib_signature()`: postcard_props_lib imported read-only, `library_object(kind)` per kind in an empty scene before any hole is opened; `ensure_library()` is NOT used, it writes Plants_C.png) is compared with that library mesh's bounding box, mesh axes x instance scale: each ratio in [0.5, 2.0], max/min <= 2.0. Meshes that match no library kind are judged by their scale alone **Round 3**: (a) a mesh is a props-library kind when its topology hash matches OR when it FUZZY-MATCHES (`lib_fuzzy_match`: unique vertices normalised into their own bounding box - a stretch along the mesh axes leaves them unchanged -, per-axis quantile prefilter 0.06 over all 48 axis permutations / mirrors, then >= 85 % of the vertices within 0.03 of a library vertex both ways), so a library mesh with a face removed, turned 90 degrees or mirrored and baked 4 : 0.6 is still compared with its library bounding box (the ratio uses the matched axis permutation); (b) a ROCK_ / CLIFF_ROCK mesh that matches no library kind cannot be compared, so its own PCA extent ratio r3 (third / first principal std of the vertices, mesh space) must be >= 0.15 (`ROCK_TH['stretch_r3_min']`) | round 2: a library mesh stretched 4 : 0.5 in its vertices passed under another name, and at the FBX stage nothing was compared; the sheared 3.17 : 1 chain read 1.41 / 1.41 / 1.0. **The FBX exporter has no shear**: the sheared mutant reaches the FBX as 1.41 / 1.41 / 1.0 (blend stage fails, FBX stage legitimately cannot) round 3 (review low): a library mesh baked 4 : 0.6 with ONE face deleted (topology hash differs) and hand-made rocks baked 4 : 0.5 / 5 : 0.4 passed. Measured with `tools/probe_lib.py` / `review2/probe_baked.py`: r3 of the 29 library kinds 0.17 (ROCK_SEASTACK_E, ROCK_WALL_BASALT_A) .. 0.89; baked hand-made hulls 4 : 0.5 -> 0.06-0.10, 5 : 0.4 -> 0.06-0.08, 3 : 1 -> 0.18-0.25. So 0.15 catches a hand-made rock stretched past ~4 : 1 and CANNOT catch 3 : 1 (as long as the library's own ledges): a hand-made rock baked up to ~3 : 1 passes - disclosed in Known gaps | scale x3, uniform x2.6, anisotropy 2.5, **sheared parent chain 3.17 : 1 (blend only), real library mesh baked 4 : 0.5 under the name ROCK_CAIRN_01**; controls (1.8, 1.5, 1.2) and a library mesh baked 1.5 x 1.3 x 1.1 under scale (1.2, 1.1, 1.0) | **round 3: library mesh baked 4 : 0.6 with one face removed (under the name ROCK_SLAB_77), library mesh turned 90 degrees and baked 3 : 1, hand-made hull baked 4 : 0.5 (ROCK_WALL_77) and 5 : 0.4 (ROCK_LARGE.099)**; controls: hand-made hull baked 1.5 : 1 : 1, library mesh with one face removed unstretched
| **PATH_UNDER_BALL** (new) | line 7: "Cart path ... hides the ball. Keep it under the ball" | every `DRESS_PATH_*` / `DRESS_SAND_*` up-facing triangle: vertices, edge midpoints, centroids and quarter points <= 1.5 cm above the collision ground beneath, its vertices <= 1.2 cm; >= 60 % of the samples >= 3 mm up (not buried / z-fighting); a 0.055 m ball resting on every ~1 m cell of it, seen from a camera 4.1 m behind / 2.2 m up (48 rays at the visible hemisphere) is hidden <= 10 % everywhere | the old Needle path: max 11.5 cm, 137 of 157 positions > 10 % hidden (worst 74 %). Steps: a path triangle that spans a play-surface step (up to 14 cm) fails: build it per surface or with vertices on both sides of each step | 3.5 cm, 11 cm, buried, floating 2 m; control 1 cm |
| **CRATER_WALL_COVERED** (repaired) | line 4: "The crater wall still shows a band of smooth grass texture at the top. Cover it" | rays (front-facing hits only) from 5 aerial (+60 m), 5 low (ball camera on the line of play) and 8 oblique (rim, +25 m) viewpoints at **every TERRAIN wall triangle below PLAY_Z sampled on a ~4 m2 lattice** (up to 3 viewpoints that face the sample): of the rays whose first hit is below PLAY_Z - 0.02, <= 1 % hit a smooth TERRAIN wall / underside face or any vertical LK_ROUGH face, AND **no connected patch of exposed samples (within 4 m of each other) is larger than 12 m2**; >= 200 such rays | the pre-repair crater: 11.8 % exposed, 94 % on the baseline. Round 2: 900 sampled face centres let a 24 m wide hole (29 cladding faces) through. Now 3,238 wall faces -> ~4,900 rays: the 12 m radius hole measures 10.6 % / 565 m2; lib smoke 0.2 % / 3 m2, the synthetic positive 0.3 % / 7 m2. A cladding offset 0.35 m cannot hide the last 0.5 m of the lip from a steep view: cap the lip (skin top above PLAY_Z - 0.02) | no cladding, cladding without the lip band, **a 12 m radius hole in the cladding where the cameras look** |
| **SEASTACK_TAPERED** (repaired; **area U: the tall rocks are found by shape / material, not by the ROCK_ prefix**) | line 5: "Sea stacks read as stacked boxes" | holes 8/9, every tall ROCK_ in the water (height above z 0 >= PLAY_Z, centre not on dry land, not SKIN / WALL): section diameter at 90 % height / at 10 % height <= 0.45; flat cap (largest connected nz >= .9 face group above 20 % height) <= 25 % of the 10 % section area; worst silhouette bbox fill over 4 azimuths <= 0.62. **A rock ISLAND is the only exemption and it is decided by geometry, never by the name**: height / d10 < 1 AND >= 50 % of the upward area in the top fifth carries LK_ROUGH (the library's flat-topped ROCK_OUTCROP_A with its grass cap) | round 2: names containing OUTCROP or PEDESTAL were skipped, so a 20 m stepped tower called ROCK_PEDESTAL_99 passed. Now it is judged and fails | boxes 0.60-0.67 / 43-53 % / 0.69-0.75 (hole 9 baseline stacks) | two stacked boxes, cylinders, flat lid, **a 20 m tower named ROCK_PEDESTAL_99, a bare flat-topped island named ROCK_OUTCROP_99**; control: a flat-topped island with a grass cap |
| **NEEDLE_SEA_STACKS** (repaired) | "a few sea stacks" | >= 4 stacks that pass BOTH the rock shape test and SEASTACK_TAPERED | the old one counted 18 icosahedra | stacks removed, stacked boxes not counted |
| **PLAY_SURFACE_FACES** (new; TOPS and GRID unchanged) | "Shore, centerline, pin, play height ... unchanged" | up-facing triangles of every TERRAIN/FAIRWAY/GREEN/TEE_BOX/BUNKER mesh vs the baseline's (`hole_0N_faces.npz`, per stage): exact rounded (1e-4) triangle sets, else every baseline triangle still has a top surface under its centroid at the same height (+-1 mm) and vice versa and the top area matches (re-triangulation passes) | the reviewer deleted / flipped one BUNKER lip polygon (445 mm above the terrain): vertex sets + the 1.5 m grid passed | polygon deleted, polygon flipped, polygon added; control: two triangles re-triangulated with the other diagonal (FACES and TOPS pass) |
| **PLAY_SURFACE_WALLS** (new, round 3) | "Shore, centerline, pin, play height ... unchanged" / "Scoring cuts unchanged" | the NON-up-facing (nz <= 0.5: cliff walls, steep slopes, undersides) non-degenerate triangles of every TERRAIN / FAIRWAY / GREEN / TEE_BOX / BUNKER / CART_PATH mesh vs the baseline's (`hole_0N_nonup.npz/json`, built ONCE from work/postcard-look/baseline by `--build-nonup-baseline`, per stage): exact rounded-triangle sets WITH winding equal -> pass; otherwise (re-triangulation) every baseline triangle centroid lies within 1 mm of a current non-up surface that faces the same way (3D BVH nearest point + normal dot >= .5) and vice versa, and the non-up area matches (1e-6 relative). Together with PLAY_SURFACE_FACES (up-facing) every non-degenerate collision triangle is covered | round 3 (review low): deleting the largest TERRAIN wall polygon passed on holes 8, 9 and 10: the up-facing face gate saw no change and `PLAY_SURFACE_ALLVERTS` is an info line (a deleted polygon keeps its vertices). Baseline 2,394 / 4,980 / 1,980 non-up triangles (holes 8 / 9 / 10), the lib smoke builds and the synthetic positives equal it exactly at both stages (the legal lib output never touches the collision body) | TERRAIN wall polygon deleted, flipped, one vertex moved 5 cm (each on a polygon none of whose vertices is on an up-facing face: every top-surface gate stays blind); control: a flat wall polygon poked into 3-4 triangles (same surface) passes |
| **UV_DENSITY** (repaired) | "show an albedo" / smeared | + per-triangle UV Jacobian: <= 15 % of any tiled material's area with anisotropy > 4:1 | u x4 / v x0.25 (16:1) passed (equal area density); hole 10's hidden walls reach 3.4:1 | 16:1 smear |
| **NEEDLE_ARCH** (repaired) | "a vine-covered stone arch" | + a through-opening: horizontal rays through the thickness over a 0.25 m (span, height) grid find >= 1.5 m clear span x 2 m clear height with masonry above (crown) and on both sides (piers), tried along both horizontal axes | a solid 6 x 7 wall of blocks passed | solid wall (no opening) |
| **ONE_GREEN** (repaired) | "No second green" | + flat (nz > .95) grass-material area >= 10 m2 on one DRESS_/PLANT_ object (or >= 20 m2 over all DRESS_), and objects named like FLAG / FLAGSTICK / POLE / PIN / CUP / LAWN / GREEN | an 8 m plant-green DRESS_LAWN + DRESS_FLAGSTICK passed | lawn + flagstick |
| **NEEDLE_CLIFF_SKIN / SPLIT_SHORE_SKIN** (repaired) | "FAIL if the shore is a smooth extruded wall" | + relief: sd of the skin's outward offset from the real shore (vertices z < PLAY_Z - 0.05 within 6 m) >= 0.15 m | A3's strata skin measures 0.7 m (the reviewer's 0.23-0.37 used the design polygon); a constant-offset curtain 0.00 m | smooth curtain |
| **PROP_MATERIALS** (repaired) | foam | generic `DRESS_*` no longer allows LK_SURF / LK_FALL | DRESS_SHOREBAND passed | white band as DRESS_ |
| **SHADERS_STATIC** (new file gate) | "No animated lava, no flowing shaders" | `GolfSurf.shader` and `GolfLook.cs` contain no `_Time`, `Time.time/deltaTime`, `SetTextureOffset`, `mainTextureOffset`, scroll speed or `Update(` (comments ignored) | review item (no gate existed) | temp shader with `_Time`, temp C# with SetTextureOffset; control: the real files |
| **HOLE07_UNTOUCHED** | "hole_07.fbx is unchanged" | unchanged: sha256 of hole_07.blend, .fbx, .fbx.meta | | meta copy changed |

### Superseded rows (above): `PLAY_SURFACE_FACES` is joined by `PLAY_SURFACE_WALLS` (round 3), `ROCK_NOT_ICOSAHEDRON`, `ROCK_VARIETY`, `SURF_SHORE`, `LOOK_FILES`, `PROPS_OFF_PLAY`, `SPLIT_SCRUB_RIDGE`, `NEEDLE_SEA_STACKS`, `NEEDLE_ARCH`,
`ONE_GREEN`, `*_SKIN`, `UV_DENSITY`, `PROP_MATERIALS` (generic DRESS row), `FLAT_ALBEDO` / `FLAT_NORMAL` constants (deleted). `PLAY_SURFACE_TOPS` / `GRID` unchanged.

## Where the repo files stand against these gates (snapshot 2026-10-04 11:50, re-run with the round-3 verifier 14:55: no verdict changed except the added PLAY_SURFACE_WALLS PASS; see Evidence for the full lists)

* **Live `Look/` PNGs** (tex agent, Smoke_C 11:09, Basalt_C/N/E 11:12; `runs/livelook_0N.*`): GRASS_ALBEDO_HUE PASS (Fairway 73.6, Green 72.5, Rough 68.1 deg), ALBEDO_DISTINCT PASS (closest
  Fairway/Green: channel-field correlation 0.39), LAVA_TEXTURE PASS (bright 84 %, dark 12 %, emission alone 77 %, peak (218,126,50), no compact cells, seam 1.22x), BASALT_PRISMS PASS
  (glow 2.2 %, cross-joints every 3.7 m, planes +10 / -17 %), SMOKE_SOFT PASS (alpha max .50, elongation 2.26, gradient .016), **LOOK_FILES FAIL**: Fairway_C only 1 % of its 256 windows
  of 64 px (1/16 of the tile) reach luminance sd 0.03 (window p10 .0140), Green_C 0 % (p10 .0101) - a smooth mow: the lead's floor for grass albedos is not met, whatever the
  resolution (Rough_C 100 %, Scrub_C 98 %; the other albedos and every normal map pass). The tool does not decide between "add blade-scale detail" and "lower the floor": that is the lead's call (see the LOOK_FILES row, 'LEAD DECISION').
* **Baseline hole files (what is installed today)**: fail the look gates as the brief says (no rocks / plants / path / arch, flat MAT_ materials, foam strips); every frozen gate PASS.
* **A3's lib smoke builds of 10:44** (not installed): SHELF_THIN, NO_FOAM_STRIP (cover 19 % / 17 %, longest run 6 / 9 m, min gap 13 / 10 m on holes 8 / 9), SURF_SHORE, PATH_UNDER_BALL (top 1.17 cm),
  CRATER_WALL_COVERED (0.2 % / 3 m2), UV_DENSITY, skins, PLAY_SURFACE_* PASS; they fail only the gates of the props still to be built (rocks, plants, stretch, stacks, arch, waterfall, cone) and LOOK_FILES.
* **The real props library** (`v2/review_V/props_test_08.fbx`, `v2/props/scratch/props_test_10.fbx`, `tools/probe_lib_kinds.py`): ROCK_NOT_ICOSAHEDRON PASS (60 rock objects, 10 / 8 meshes), ROCK_VARIETY PASS
  (7 / 5 shape families), NO_ROCK_STRETCH_2X PASS (60 of 60 instances match a library mesh by topology, largest scale 2.00, anisotropy 1.24-1.27). Library rocks sit 1 vertex / 2 faces above the
  60 / 100 floors (ROCK_LEDGE_A 61 v / 101 f, ROCK_BOULDER_B 62 v / 102 f): any chip removal in the props lib flips them to FAIL.

## Unity-side companions (NOT in this tool; the integrator measures them in the Game view)

* **Lit grass hue**: Game-view 16x16 mean of lit fairway / green / rough at the golf key light (not the PNG): hue 64-73 on Needle / Split / Crater tee and approach
  stills (fairway/green; rough 59-66), S .57-.84, V .53-.73. Before this pass: albedo 94-97 -> lit (132,187,81) hue 89. This tool only bounds the albedo (66-82).
* **Lava orange without bloom**: post-processing does not render (TennisURP_Renderer has no postProcessData): Game-view lava samples hue 5-40, V >= .55,
  no cream / white clipping, with the emission multiplier dropped. This tool bounds the PNGs (emission alone >= 40 % bright orange, peak G <= 190 / B <= 70).
* **Water edge**: the Game view must show the shelf as a thin edge, not the brightest shape in the aerial (visual V-checklist); this tool measures the mesh.
* **Albedo + normal in the Game view, `LK_` materials accepted by `PostcardImportCheck`, proof shots exist**: Unity / integrator.

## Decisions (made without asking; every number is a constant in `TH2`, `ROCK_TH`, `GRASS_BANDS`)

1. Shore = TERRAIN loops (see above). 2. `ROCK_VARIETY` counts shape FAMILIES: equal topology hash, or geometric near-duplicate (PCA ratios +-0.04, vertex counts +-10 %, facet orientations +-2).
3. Sphericity uses the PCA-whitened radius cv with 0.15; **per-component rock tests use vertex valences, not sphericity**: the library's own hull stones are as 'sphere-like' (whitened radius cv 0.08-0.17)
   as a noised icosphere, valences are what jitter cannot hide. 4. The window floor 0.03 / 90 % is the lead's number for the grass albedos; since the review it is a FOOTPRINT (1/16 of the tile), sand
   gets 0.008 and the other opaque albedos 0.012. 5. Lava "emission alone >= 40 %" is my reading of "read orange with emission alone". 6. PATH_UNDER_BALL: buried-path floor 60 % of samples >= 3 mm (my
   addition). 7. Cell detector polarity-agnostic (dark plates AND bright cells). 8. NO_FOAM_STRIP: reach 10 m, area cap 1.0 m2/m, 8 m merge gap and 11 m merged-length limit are mine (the lead's numbers are the
   25 % / 10 m / 8 m); the lib's measured 0.68 / 0.54 m2/m and 7.7 m leave 30-45 % margin. 9. The FBX stage of the sheared-parent mutant is waived (`MUT_BLEND_ONLY_NAMES`): the FBX format has no shear.
   10. `lib_signature()` imports `postcard_props_lib` (read-only use, `library_object(kind)`; never `ensure_library()`, which writes Plants_C.png) once per process in an EMPTY scene before any hole is
   opened; if the import fails the stretch gate FAILS closed on holes that have rocks.

11. Round 3 (all mine, constants `ROCK_TH['max_open_edge']` 0.10, `ROCK_TH['stretch_r3_min']` 0.15, `FALL_SHEET_MAX_EXTENT` 8 m / `_MAX_NZ` 0.6 / `_MAX_COMPONENTS` 2 / `_MAX_AREA` 60 m2, wall tolerance 1 mm in `surface_cover3d`):
    the closed-solid limit 10 % sits between the library (0 %) and any soup (100 %); the PCA floor 0.15 sits 12 % under the flattest library mesh (0.17); the waterfall-sheet budget is the library's own
    sheet (3 m wide, 36 m2) with margin; none of these is a number from the brief. 12. The wall baseline is a NEW pair of files (`hole_0N_nonup.*`) so the vertex / grid / up-facing signatures stay exactly as
    built on 2026-10-03 / 04. 13. Fuzzy library matching (0.06 quantile prefilter, 0.03 / 85 % nearest-vertex test) is deliberately tolerant: a false match only means a rock is compared with a library
    bounding box, a missed match falls back to the PCA floor.

## Reviewer items (review_gates, 2026-10-03)

Fixed: all 6 high/medium (rocks, flat textures, foam strip, scrub, props off play, face-level frozen tops) and the cheap lows: UV anisotropy, arch opening, skin relief,
second-green dressing, shader static grep, self-test negatives at the FBX stage (`--selftest-fbx`, mutants checked at both stages, collateral failures printed).
NOT fixed (judgement calls, not mechanisable from the repo): pad assignment of the path / flowers / waterfall ("left pad", "lower right pad" refer to the still, the
design pads are tee / middle / green with no mapping); the proof-shot file-exists gate (integrator tool).

## Review round 2 (2026-10-04, skeptic reviewer of this tool): findings and what was done

| finding | severity | fix |
|---|---|---|
| NO_FOAM_STRIP measured within 1 m of the shore: continuous white rings at 2-6 m passed (touching squares; ragged band at 2.5 m, width cv > 0.3) | medium | foam reach 10 m along the shore normals, union of ALL white geometry (any material, any name), merged-piece length rule beyond the reach, area per metre cap; mutants: touching squares, ragged band, offshore dashes with 7 m gaps, non-LK white material, vertex alpha 0.29, flat LK_FALL named WATER_FALL |
| rock gates passed a bundle of 5-8 jittered icosahedra (60-96 v, 100-160 f); variety hash only counted verts / faces / valences | medium | per-component valence topology (regular solids, geodesic spheres), shape FAMILIES in the variety hash; mutants: bundles of 12-v and 42-v icosahedra, noised subdiv-3 icosphere (+-40 %), edge-split variants |
| LOOK_FILES: fixed 64 px window = verdict depends on resolution; checkerboard passes; floor not calibrated | medium | window = 1/16 of the tile, minimum sizes (ground 512 px), spectral peak and tiled-cell autocorrelation tests; calibration against the stills documented as impossible below ~1.5 m footprint (`calib/still_calib.txt`); the real Look still FAILS and the lead decides |
| NO_ROCK_STRETCH_2X: column norms hid a sheared chain; baked stretch only caught for library names at the blend stage | low | SVD singular values; topology-hash match to the props library at BOTH stages; the FBX has no shear (documented, blend-only mutant) |
| NO_PLANT_ON_WATER: one point per object; floating slab accepted as support | low | per-piece judgement; the supporting rock must stand on ground or reach the sea |
| PROPS_OFF_PLAY: 0.7 m DRESS_ boulder between grid points | low | 0.25 m re-sampling of every DRESS_-type object narrower than 3 m |
| CRATER_WALL_COVERED: 900 face centres, 1 % global limit let a 24 m hole through | low | every wall triangle on a 4 m2 lattice, plus a connected-patch limit of 12 m2 |
| ALBEDO_DISTINCT / scrub: recolour of the fairway pattern passed | low | channel-field correlation < 0.85 whatever the colour, also in SPLIT_SCRUB_RIDGE |
| SEASTACK_TAPERED: names OUTCROP / PEDESTAL exempted | low | island exemption by geometry (H / d10 < 1 and a grass cap), never by name |
| SMOKE_SOFT gradient bound fitted to the artefact | note | disclosed in the row; the live Smoke_C now measures .016 |

## Review round 3 (2026-10-04, second skeptic review of this tool): findings and what was done

| finding | severity | fix |
|---|---|---|
| NO_FOAM_STRIP counted only up-facing triangles (LK_SURF / white material nz > 0.5, LK_FALL nz > 0.8): a continuous white LK_SURF skirt at nz 0.44 around the whole shore passed every gate at both stages | medium | foam of ANY orientation; coverage by exact 3D overlap of the foam with the shore-normal plane strips; edges of near-vertical triangles in the offshore raster; area cap on the 3D area; LK_FALL waterfall sheets exempt by geometry (<= 2 components, plan extent <= 8 m, mean abs nz <= 0.6, <= 60 m2), never by name; **my own probe found two siblings and closed them: a white material called MAT_* (was exempt) and a vertical curtain (no plan area)**; mutants: skirt nz 0.45, vertical wall, steep LK_FALL ramp named WATER_FALL, white MAT_ skirt nz 0.3 |
| ROCK gates passed 6-14 exact 12-vertex icosahedra that SHARE vertices (valences {5,10,15,..}) | medium | components are manifold SURFACE PATCHES (touching cells are separated before every per-component rule); closed-solid rule (<= 10 % open polygon edges) for the next dodge (every face split off by 2 mm); mutants: welded clusters of icosahedra / icospheres / octahedra, jitter after the weld, 2 mm split bundles; control: welded natural hull stones |
| NO_ROCK_STRETCH_2X: a library mesh baked 4 : 0.6 with one face deleted and hand-made rocks baked 4 : 0.5 / 5 : 0.4 passed | low | fuzzy library match (bounding-box-normalised vertex sets over 48 axis permutations / mirrors) + PCA r3 >= 0.15 for rock meshes that match no library kind; the residual (a hand-made rock baked <= ~3 : 1) is disclosed |
| deleting a non-up-facing TERRAIN collision polygon (cliff wall / underside) passed | low | new gate PLAY_SURFACE_WALLS (baseline `hole_0N_nonup.npz/json`, winding-aware, re-triangulation tolerated) |
| LOOK_FILES floor 0.03 / 90 % is not calibrated on the stills; the live Look fails it | low | not tuned (the review said not to): GATES.md states it is the lead's number and a decision, with the calibration data, and the failure message says so; **the lead / tex agent decide** |

## Known gaps / limits (honest list)

* Rocks: after the patch split and the closed-solid rule, a bundle of LOW-POLY STONES whose patches are not regular (one edge subdivided or a face poked into an icosahedron: valences {4,5,6} / {3,5,6}) still passes: it is built like the library's own cairn (6 stones of 15-16 vertices) and no valence, edge-length or area statistic separates them with a margin (`tools/probe_patch_stats.py`: library patches have a valence-5 share <= 0.63, 'icosahedra with one or two edge splits' 0.71-1.00, but a poked face drops one under the library band again). The visual checklist (rocks read as rocks from the tee) is the backstop. Any rock mesh that is NOT a props-library mesh and not stretched past r3 0.15 is judged by shape statistics only. A stretch applied along ROTATED (non mesh-axis) directions to a library mesh is not caught by the fuzzy match (bounding-box frame); a hand-made rock baked up to ~3 : 1 (r3 0.18-0.25, as elongated as the library's ledges) passes the PCA cap.
* The FBX format has no shear: a sheared parent chain reaches Unity as the nearest shear-free matrix. The blend stage catches the chain, the FBX stage cannot.
* `NO_PLANT_ON_WATER` / `PATH_UNDER_BALL` / `CRATER_WALL_COVERED` pass vacuously when the hole has no plants / no overlay / (hole 8, 9) no crater: other gates require the content.
* Textures are measured as PNG files; Unity's import (compression, mips) is not simulated. LOOK_FILES cannot tell fine grass from fine noise of the same sd (the block-mean test is the only guard).
* `CRATER_WALL_COVERED` uses 18 fixed viewpoints: it cannot see a gap hidden from all of them; it samples faces below PLAY_Z only.
* `NO_FOAM_STRIP` ignores the faded fringe (alpha < .3) of a piece that does reach .3 (the fringe alone would add 0.35 m2/m on Needle) and up to 2 waterfall sheets (<= 8 m wide, <= 60 m2 in total: at most 16 m of the shore); foam farther than 10 m from the shore may be dashed (pieces closer than 8 m merge, merged length <= 11 m).
* `PLAY_SURFACE_WALLS` compares triangles to 1 mm; a polygon moved by < 1 mm is not a gate failure (the vertex rounding of the exact path is 0.1 mm).
* `SEASTACK_TAPERED` tests rocks whose centre is not on dry land; a tower whose centre sits on the dry side of the shore line escapes it (other gates still see it).
* The Unity-side lines (lit grass hue, lava orange without bloom, water edge in the aerial, `LK_` accepted by PostcardImportCheck, proof shots) are not in this tool.

## Evidence (2026-10-04)

Files: `v2/gates/runs/*.json|log` (verify runs), `v2/gates/runs/selftest_all_fbx_r3.log` (self-test of the round-3 verifier; the round-2 self-test log is `runs/selftest_all_fbx.log`), `v2/gates/fixtures/` (old failing textures, lib smoke builds of 2026-10-03 22:00 and 2026-10-04 10:44, the Look snapshot the runs used + sha256), `v2/gates/tools/run_evidence.sh` (re-creates it all), `v2/gates/st/` (the synthetic positives), `v2/gates/postcard_look_verify.py.at_start` / `.before_review_fix` / `.before_review2_fix` (the file before this pass / before the first / before the second review fix), `runs_prev_r2/` (the verify runs of the round-2 verifier), `review3/` (the skeptic's mutants replayed against the round-3 verifier), `r3/` (round-3 working logs), `v2/gates/calib/still_calib.txt` (stills vs the window statistic), `v2/gates/tools/*` (probes, run_gate.py, skeptic_mut.py).

Verifier `blender/scripts/postcard_look_verify.py` sha256 `edc96d4d755bb248439603be3bf97a783dbfd930cd654b2189b10fa7eac420fd` (8134 lines) = the file the self-test below ran against (`runs/verify_sha_for_selftest_r3.txt`).

**Self-test** (`--selftest --selftest-fbx`, all holes): SELFTEST: 434 lines, 0 expectations not met; files under /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/gates/st

(An earlier run of the same verifier minus two edits - `runs/selftest_all_fbx_r3_first_run.log`, 434 lines - ended with ONE expectation not met: the hole-9 control `ctl_terrain_wall_polygon_poked_same_surface` raised 'no isolated non-up-facing TERRAIN polygon' because hole 9's smallest wall-polygon non-planarity is 1.5e-5 m, over the control's own 1e-5 m flatness filter. The filter became 2e-4 m (far under the gate's 1 mm) and the LOOK_FILES window floor became the named constant `TH2['win_sd']` (same value 0.03); no gate verdict changed. The run below is the full self-test of the final file.)

```
SELFTEST_GATE PLAY_SURFACE_WALLS MUT_FAILS_ON_BAD 9/9 PASS; MUT_PASSES_ON_GOOD 9/9 PASS
SELFTEST_GATE PROP_MATERIALS MUT_FAILS_ON_BAD 2/2 PASS; MUT_PASSES_ON_GOOD 6/6 PASS
SELFTEST_GATE ROCK_NOT_ICOSAHEDRON MUT_FAILS_ON_BAD 51/51 PASS; MUT_PASSES_ON_GOOD 9/9 PASS
SELFTEST_GATE ROCK_VARIETY MUT_FAILS_ON_BAD 57/57 PASS; MUT_PASSES_ON_GOOD 6/6 PASS
SELFTEST_GATE LOOK_FILES MUT_FAILS_ON_BAD 22/22 PASS; MUT_PASSES_ON_GOOD 6/6 PASS
SELFTEST_GATE NO_FOAM_STRIP MUT_FAILS_ON_BAD 37/37 PASS; MUT_PASSES_ON_GOOD 6/6 PASS
SELFTEST_GATE SURF_SHORE MUT_FAILS_ON_BAD 4/4 PASS; MUT_PASSES_ON_GOOD 4/4 PASS
SELFTEST_GATE SPLIT_SCRUB_RIDGE MUT_FAILS_ON_BAD 5/5 PASS; MUT_PASSES_ON_GOOD 2/2 PASS
SELFTEST_GATE PROPS_OFF_PLAY MUT_FAILS_ON_BAD 15/15 PASS; MUT_PASSES_ON_GOOD 9/9 PASS
SELFTEST_GATE PLAY_SURFACE_FACES MUT_FAILS_ON_BAD 12/12 PASS; MUT_PASSES_ON_GOOD 9/9 PASS
SELFTEST_GATE GRASS_ALBEDO_HUE MUT_FAILS_ON_BAD 9/9 PASS; MUT_PASSES_ON_GOOD 6/6 PASS
SELFTEST_GATE ALBEDO_DISTINCT MUT_FAILS_ON_BAD 18/18 PASS; MUT_PASSES_ON_GOOD 6/6 PASS
SELFTEST_GATE SHELF_THIN MUT_FAILS_ON_BAD 8/8 PASS; MUT_PASSES_ON_GOOD 4/4 PASS
SELFTEST_GATE LAVA_TEXTURE MUT_FAILS_ON_BAD 8/8 PASS; MUT_PASSES_ON_GOOD 2/2 PASS
SELFTEST_GATE BASALT_PRISMS MUT_FAILS_ON_BAD 4/4 PASS; MUT_PASSES_ON_GOOD 2/2 PASS
SELFTEST_GATE SMOKE_SOFT MUT_FAILS_ON_BAD 5/5 PASS; MUT_PASSES_ON_GOOD 2/2 PASS
SELFTEST_GATE NO_PLANT_ON_WATER MUT_FAILS_ON_BAD 22/22 PASS; MUT_PASSES_ON_GOOD 9/9 PASS
SELFTEST_GATE NO_ROCK_STRETCH_2X MUT_FAILS_ON_BAD 27/27 PASS; MUT_PASSES_ON_GOOD 18/18 PASS
SELFTEST_GATE PATH_UNDER_BALL MUT_FAILS_ON_BAD 3/3 PASS; MUT_PASSES_ON_GOOD 10/10 PASS
SELFTEST_GATE CRATER_WALL_COVERED MUT_FAILS_ON_BAD 3/3 PASS; MUT_PASSES_ON_GOOD 2/2 PASS
SELFTEST_GATE SEASTACK_TAPERED MUT_FAILS_ON_BAD 10/10 PASS; MUT_PASSES_ON_GOOD 6/6 PASS
SELFTEST_GATE UV_DENSITY MUT_FAILS_ON_BAD 9/9 PASS; MUT_PASSES_ON_GOOD 6/6 PASS
SELFTEST_GATE NEEDLE_ARCH MUT_FAILS_ON_BAD 5/5 PASS; MUT_PASSES_ON_GOOD 2/2 PASS
SELFTEST_GATE ONE_GREEN MUT_FAILS_ON_BAD 6/6 PASS; MUT_PASSES_ON_GOOD 6/6 PASS
SELFTEST_GATE NEEDLE_SEA_STACKS MUT_FAILS_ON_BAD 2/2 PASS; MUT_PASSES_ON_GOOD 2/2 PASS
SELFTEST_GATE NEEDLE_CLIFF_SKIN MUT_FAILS_ON_BAD 2/2 PASS; MUT_PASSES_ON_GOOD 2/2 PASS
SELFTEST_GATE SPLIT_SHORE_SKIN MUT_FAILS_ON_BAD 2/2 PASS; MUT_PASSES_ON_GOOD 2/2 PASS
SELFTEST_GATE SHADERS_STATIC MUT_FAILS_ON_BAD 1/1 PASS; MUT_PASSES_ON_GOOD 3/3 PASS
SELFTEST_GATE HOLE07_UNTOUCHED MUT_FAILS_ON_BAD 3/3 PASS; MUT_PASSES_ON_GOOD 3/3 PASS
```

**Per-gate mutation table of EVERY gate** (all holes, both stages; MUT_FAILS_ON_BAD = mutants that must fail the gate and do; MUT_PASSES_ON_GOOD = positives + controls that pass it; the first table's V2 rows are the tool's own SELFTEST_GATE counts):

```
gate                               MUT_FAILS_ON_BAD   MUT_PASSES_ON_GOOD
ALBEDO_DISTINCT                        18/18                6/6       
BASALT_PRISMS                           4/4                 2/2       
BASELINE_SIGNATURE                      3/3                 0/0       
CRATER_COLUMNS                          1/1                 0/0       
CRATER_CONE_SMOKE                       2/2                 0/0       
CRATER_LAVA                             2/2                 0/0       
CRATER_LAVA_LIGHTS                      2/2                 0/0       
CRATER_PILLAR                           1/1                 0/0       
CRATER_SHELF_PLANTS                     1/1                 0/0       
CRATER_TEE_PAD                          1/1                 0/0       
CRATER_WALL_COVERED                     3/3                 2/2       
FBX_FILE                                3/3                 0/0       
FBX_REIMPORT                            3/3                 0/0       
GRASS_ALBEDO_HUE                        9/9                 6/6       
GROUND_MATERIALS                        3/3                 0/0       
HOLE07_UNTOUCHED                        3/3                 3/3       
LAVA_TEXTURE                            8/8                 2/2       
LK_TEXTURED                             3/3                 0/0       
LOOK_FILES                             22/22                6/6       
MARKERS_FROZEN                          3/3                 0/0       
NEEDLE_ARCH                             5/5                 2/2       
NEEDLE_CLIFF_SKIN                       2/2                 2/2       
NEEDLE_FLOWERS_SHRUBS_TUFTS             2/2                 0/0       
NEEDLE_PATH                             2/2                 1/1       
NEEDLE_SEA_STACKS                       2/2                 2/2       
NEEDLE_WALL_VINES                       1/1                 0/0       
NEEDLE_WATERFALL                        3/3                 0/0       
NEW_OBJECT_PREFIXES                     6/6                 0/0       
NO_ANIMATION                            3/3                 0/0       
NO_FOAM_STRIP                          37/37                6/6       
NO_LEGACY_MATERIALS                     6/6                 0/0       
NO_MAT_FOAM                             3/3                 0/0       
NO_PLANT_ON_WATER                      22/22                9/9       
NO_ROCK_STRETCH_2X                     27/27               18/18      
OCEAN_WATER                             2/2                 0/0       
ONE_GREEN                               6/6                 6/6       
PATH_UNDER_BALL                         3/3                10/10      
PLANTS_INSTANCED                        3/3                 0/0       
PLANTS_SHARED_MATERIAL                  3/3                 0/0       
PLAY_SURFACE_FACES                     12/12                9/9       
PLAY_SURFACE_GRID                       3/3                 0/0       
PLAY_SURFACE_NAMES                      6/6                 0/0       
PLAY_SURFACE_TOPS                       3/3                 3/3       
PLAY_SURFACE_WALLS                      9/9                 9/9       
PROPS_OFF_PLAY                         15/15                9/9       
PROP_FACE_BUDGET                        3/3                 0/0       
PROP_MATERIALS                          2/2                 6/6       
RESERVED_NAMES                          3/3                 0/0       
ROCK_NOT_ICOSAHEDRON                   51/51                9/9       
ROCK_VARIETY                           57/57                6/6       
SAND_NAMES                              3/3                 3/3       
SEASTACK_TAPERED                       10/10                6/6       
SHADERS_STATIC                          1/1                 3/3       
SHELF_THIN                              8/8                 4/4       
SMOKE_SOFT                              5/5                 2/2       
SPLIT_NO_SCRUB_RIBBON                   1/1                 0/0       
SPLIT_RIDGE_SCATTER                     1/1                 0/0       
SPLIT_RUIN                              1/1                 0/0       
SPLIT_SCRUB_RIDGE                       5/5                 2/2       
SPLIT_SHORE_SKIN                        2/2                 2/2       
SURF_SHORE                              4/4                 4/4       
TRIANGLE_BUDGET                         3/3                 0/0       
UV_DENSITY                              9/9                 6/6       
positives failed gates: {'8': [], '9': [], '10': []}
```

**The skeptic's own mutants replayed against this verifier** (`v2/gates/review3/mut2.py`, `mut3.py` = pointed copies of the reviewer's `review_V` harness, FBX stage included; positives = `review_V/st2`):
```
hole 8: 97 mutants run (blend + FBX), 4 harness errors ['st_lib_unit_scale_baked_swap_stretch', 'st_lib_unit_scale_baked_swap_stretch_wallname', 'st_lib_baked_swap_stretch', 'st_lib_baked_swap_fit'], 6 fail NO gate (controls / design passes): ['st_scale_1_2.0_1', 'st_lib_unit_scale_control', 'shelf_ring_2.4_uniform', 'pr_boulder_on_apron_edge', 'LB_libkind_baked_1.8x_control_pass', 'LB_lib_scale_1.9_1.9_1.0_control']
hole 9: 89 mutants run (blend + FBX), 4 harness errors ['st_lib_unit_scale_baked_swap_stretch', 'st_lib_unit_scale_baked_swap_stretch_wallname', 'st_lib_baked_swap_stretch', 'st_lib_baked_swap_fit'], 7 fail NO gate (controls / design passes): ['st_scale_1_2.0_1', 'st_lib_unit_scale_control', 'shelf_ring_2.4_uniform', 'pr_boulder_on_apron_edge', 'LB_libkind_baked_1.8x_control_pass', 'LB_lib_scale_1.9_1.9_1.0_control', 'LB_lib_rock_normal_control']
hole 10: 87 mutants run (blend + FBX), 53 harness errors ['rk_ico_sub2_noise10', 'rk_ico_sub2_noise25', 'rk_ico_sub2_noise40', 'rk_ico_sub1_42v', 'rk_ico_sub1_noise20_split', 'rk_bundle5_ico_jitter'], 1 fail NO gate (controls / design passes): ['st_lib_unit_scale_control']
attacks of the review rounds and the gates that catch them (hole 8 / 9):
  h8 rk_ico_sub2_noise10                                  -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 rk_ico_sub2_noise25                                  -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 rk_ico_sub2_noise40                                  -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 rk_ico_sub1_42v                                      -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 rk_ico_sub1_noise20_split                            -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 rk_bundle5_ico_jitter                                -> NEEDLE_SEA_STACKS,NO_ROCK_STRETCH_2X,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 rk_bundle8_ico_jitter                                -> NEEDLE_SEA_STACKS,NO_ROCK_STRETCH_2X,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 rk_ico_sub3_noise15                                  -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 rk_ico_sub3_noise40                                  -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 rk_bundle_variety_loose_only                         -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY
  h8 st_scale_0.5_2_0.5                                   -> NO_ROCK_STRETCH_2X
  h8 st_scale_1_2.0_1                                     -> (none)
  h8 st_scale_1_2.15_1                                    -> NO_ROCK_STRETCH_2X
  h8 st_shear_parent                                      -> NO_ROCK_STRETCH_2X
  h8 st_baked_stretch_wall                                -> NO_ROCK_STRETCH_2X
  h8 st_lib_unit_scale_baked_swap_stretch                 -> (none)
  h8 st_lib_unit_scale_baked_swap_stretch_wallname        -> (none)
  h8 st_lib_baked_swap_stretch                            -> (none)
  h8 st_lib_baked_swap_fit                                -> (none)
  h8 st_baked_stretch_loose                               -> NO_ROCK_STRETCH_2X
  h8 foam_dash_9m_gap27                                   -> NO_FOAM_STRIP
  h8 foam_dash_9m_gap7                                    -> NO_FOAM_STRIP
  h8 foam_dash_9m_gap9_fail_cov                           -> NO_FOAM_STRIP
  h8 foam_two_rows_union50                                -> NO_FOAM_STRIP
  h8 foam_dash_offshore_ring_20m                          -> NO_FOAM_STRIP
  h8 foam_ribbon_far_30m                                  -> NO_FOAM_STRIP
  h8 foam_in_ocean_material_white                         -> NO_FOAM_STRIP,OCEAN_WATER,PROP_MATERIALS,UV_DENSITY
  h8 foam_ragged_continuous_band_off1.6                   -> NO_FOAM_STRIP,SURF_SHORE
  h8 foam_ragged_continuous_band_off1.2                   -> NO_FOAM_STRIP,SURF_SHORE
  h8 foam_ragged_continuous_band_off0.3                   -> NO_FOAM_STRIP,SURF_SHORE
  h8 foam_ragged_hicv_band_off1.6                         -> NO_FOAM_STRIP,SURF_SHORE
  h8 foam_ragged_hicv_band_off2.5                         -> NO_FOAM_STRIP
  h8 foam_squares_touching_off2                           -> NO_FOAM_STRIP
  h8 pl_on_sea_z0                                         -> NO_PLANT_ON_WATER
  h8 pl_on_sea_z5.2                                       -> NO_PLANT_ON_WATER
  h8 pl_on_floating_rock_z5.2                             -> NO_PLANT_ON_WATER,NO_ROCK_STRETCH_2X
  h8 pl_merged_far_copy_over_sea                          -> NO_PLANT_ON_WATER,UV_DENSITY
  h8 pl_on_play_edge_fairway                              -> NO_PLANT_ON_WATER,ONE_GREEN,PROPS_OFF_PLAY
  h8 stack_ziggurat_named_SEASTACK                        -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,SEASTACK_TAPERED
  h8 stack_ziggurat_named_PEDESTAL_extra                  -> ROCK_NOT_ICOSAHEDRON,SEASTACK_TAPERED
  h8 stack_boxes_named_WALL_extra                         -> ROCK_NOT_ICOSAHEDRON
  h8 terrain_wall_poly_deleted                            -> PLAY_SURFACE_WALLS
  h8 LB_libkind_baked_4x0.5_unit_scale                    -> NO_ROCK_STRETCH_2X,PROPS_OFF_PLAY
  h8 LB_libkind_baked_3x1_renamed_CAIRN                   -> NO_ROCK_STRETCH_2X,PROPS_OFF_PLAY
  h8 LB_libkind_baked_1.8x_control_pass                   -> (none)
  h8 LB_libkind_baked_stretch_plus_chip_removed           -> NO_ROCK_STRETCH_2X,PROPS_OFF_PLAY
  h8 LB_lib_scale_2_2_0.5                                 -> NO_ROCK_STRETCH_2X
  h8 LB_lib_scale_1.9_1.9_1.0_control                     -> (none)
  h8 LB_lib_rock_normal_control                           -> PROPS_OFF_PLAY
  h8 RK_welded_ico_cluster_6                              -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 RK_welded_ico_cluster_varied                         -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 RK_welded_ico_cluster_jitter12                       -> NEEDLE_SEA_STACKS,ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h8 FM_sloped_white_skirt_nz0.45                         -> NO_FOAM_STRIP
  h8 FM_offshore_dashes_9m_gap9_at_12m                    -> NO_FOAM_STRIP
  h8 FM_tiny_gaps_ring_at_12m_wide                        -> NO_FOAM_STRIP
  h8 PL_on_floating_rock_lo2.9                            -> NO_PLANT_ON_WATER
  h8 PL_on_floating_DRESS_BLOCK_z5.2                      -> NO_PLANT_ON_WATER
  h8 UP_del_TERRAIN                                       -> PLAY_SURFACE_FACES
  h8 UP_flip_TERRAIN                                      -> PLAY_SURFACE_FACES,PLAY_SURFACE_WALLS
  h8 UP_del_FAIRWAY                                       -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h8 UP_flip_FAIRWAY                                      -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h8 UP_del_GREEN                                         -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h8 UP_flip_GREEN                                        -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h8 UP_del_TEE_BOX                                       -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h8 UP_flip_TEE_BOX                                      -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h8 UP_del_BUNKER                                        -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h8 UP_flip_BUNKER                                       -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h8 UP_del_TERRAIN_rim_tri                               -> NO_FOAM_STRIP,PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h8 UP_flip_TERRAIN_idx200                               -> NO_PLANT_ON_WATER,PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h8 UP_del_TERRAIN_idx200                                -> NO_PLANT_ON_WATER,PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h9 rk_ico_sub2_noise10                                  -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 rk_ico_sub2_noise25                                  -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 rk_ico_sub2_noise40                                  -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 rk_ico_sub1_42v                                      -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 rk_ico_sub1_noise20_split                            -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 rk_bundle5_ico_jitter                                -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 rk_bundle8_ico_jitter                                -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 rk_ico_sub3_noise15                                  -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 rk_ico_sub3_noise40                                  -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 rk_bundle_variety_loose_only                         -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 st_scale_0.5_2_0.5                                   -> NO_ROCK_STRETCH_2X
  h9 st_scale_1_2.0_1                                     -> (none)
  h9 st_scale_1_2.15_1                                    -> NO_ROCK_STRETCH_2X
  h9 st_shear_parent                                      -> NO_ROCK_STRETCH_2X
  h9 st_baked_stretch_wall                                -> NO_ROCK_STRETCH_2X
  h9 st_lib_unit_scale_baked_swap_stretch                 -> (none)
  h9 st_lib_unit_scale_baked_swap_stretch_wallname        -> (none)
  h9 st_lib_baked_swap_stretch                            -> (none)
  h9 st_lib_baked_swap_fit                                -> (none)
  h9 st_baked_stretch_loose                               -> NO_ROCK_STRETCH_2X
  h9 foam_dash_9m_gap27                                   -> NO_FOAM_STRIP
  h9 foam_dash_9m_gap7                                    -> NO_FOAM_STRIP
  h9 foam_dash_9m_gap9_fail_cov                           -> NO_FOAM_STRIP
  h9 foam_two_rows_union50                                -> NO_FOAM_STRIP
  h9 foam_dash_offshore_ring_20m                          -> NO_FOAM_STRIP
  h9 foam_ribbon_far_30m                                  -> NO_FOAM_STRIP
  h9 foam_in_ocean_material_white                         -> NO_FOAM_STRIP,OCEAN_WATER,PROP_MATERIALS,UV_DENSITY
  h9 foam_ragged_continuous_band_off1.6                   -> NO_FOAM_STRIP,SURF_SHORE
  h9 foam_ragged_continuous_band_off1.2                   -> NO_FOAM_STRIP,SURF_SHORE
  h9 foam_ragged_continuous_band_off0.3                   -> NO_FOAM_STRIP,SURF_SHORE
  h9 foam_ragged_hicv_band_off1.6                         -> NO_FOAM_STRIP,SURF_SHORE
  h9 foam_ragged_hicv_band_off2.5                         -> NO_FOAM_STRIP
  h9 foam_squares_touching_off2                           -> NO_FOAM_STRIP
  h9 pl_on_sea_z0                                         -> NO_PLANT_ON_WATER
  h9 pl_on_sea_z5.2                                       -> NO_PLANT_ON_WATER
  h9 pl_on_floating_rock_z5.2                             -> NO_PLANT_ON_WATER,NO_ROCK_STRETCH_2X
  h9 pl_merged_far_copy_over_sea                          -> NO_PLANT_ON_WATER,UV_DENSITY
  h9 pl_on_play_edge_fairway                              -> NO_PLANT_ON_WATER,ONE_GREEN,PROPS_OFF_PLAY
  h9 terrain_wall_poly_deleted                            -> PLAY_SURFACE_WALLS
  h9 LB_libkind_baked_4x0.5_unit_scale                    -> NO_ROCK_STRETCH_2X
  h9 LB_libkind_baked_3x1_renamed_CAIRN                   -> NO_ROCK_STRETCH_2X
  h9 LB_libkind_baked_1.8x_control_pass                   -> (none)
  h9 LB_libkind_baked_stretch_plus_chip_removed           -> NO_ROCK_STRETCH_2X,PROPS_OFF_PLAY
  h9 LB_lib_scale_2_2_0.5                                 -> NO_ROCK_STRETCH_2X
  h9 LB_lib_scale_1.9_1.9_1.0_control                     -> (none)
  h9 LB_lib_rock_normal_control                           -> (none)
  h9 RK_welded_ico_cluster_6                              -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 RK_welded_ico_cluster_varied                         -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 RK_welded_ico_cluster_jitter12                       -> ROCK_NOT_ICOSAHEDRON,ROCK_VARIETY,SEASTACK_TAPERED
  h9 FM_sloped_white_skirt_nz0.45                         -> NO_FOAM_STRIP
  h9 FM_offshore_dashes_9m_gap9_at_12m                    -> NO_FOAM_STRIP
  h9 FM_tiny_gaps_ring_at_12m_wide                        -> NO_FOAM_STRIP
  h9 PL_on_floating_rock_lo2.9                            -> NO_PLANT_ON_WATER
  h9 PL_on_floating_DRESS_BLOCK_z5.2                      -> NO_PLANT_ON_WATER
  h9 UP_del_TERRAIN                                       -> NO_FOAM_STRIP,PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h9 UP_flip_TERRAIN                                      -> NO_FOAM_STRIP,PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h9 UP_del_FAIRWAY                                       -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h9 UP_flip_FAIRWAY                                      -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h9 UP_del_GREEN                                         -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h9 UP_flip_GREEN                                        -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h9 UP_del_TEE_BOX                                       -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h9 UP_flip_TEE_BOX                                      -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h9 UP_del_BUNKER                                        -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h9 UP_flip_BUNKER                                       -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h9 UP_del_TERRAIN_rim_tri                               -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
  h9 UP_flip_TERRAIN_idx200                               -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID,PLAY_SURFACE_WALLS
  h9 UP_del_TERRAIN_idx200                                -> PLAY_SURFACE_FACES,PLAY_SURFACE_GRID
```

**The builder's own extra attacks** (`v2/gates/review3/extra_attacks.py`, FBX stage included): continuous white curtains / ramps 6, 9, 11 m offshore and underwater, a white skirt named FLAG, welded icosahedra sharing a FACE, icosahedra with poked faces. The poked-face bundle with only 14 pokes over 7 cells fails (4-7 of 11 rock meshes still regular); one with >= 2 pokes in every cell is the disclosed residual (Known gaps):
```
MUT 8 foam_vertical_curtain_6m_offshore_continuous -> FAILED ['UV_DENSITY@blend', 'NO_FOAM_STRIP@blend', 'UV_DENSITY@fbx', 'NO_FOAM_STRIP@fbx']
MUT 8 foam_sloped_skirt_underwater_z-1 -> FAILED ['NO_FOAM_STRIP@blend', 'NO_FOAM_STRIP@fbx']
MUT 8 foam_skirt_at_9m_offshore_continuous_steep -> FAILED ['NO_FOAM_STRIP@blend', 'NO_FOAM_STRIP@fbx']
MUT 8 foam_skirt_11m_offshore_continuous -> FAILED ['NO_FOAM_STRIP@blend', 'NO_FOAM_STRIP@fbx']
MUT 8 foam_white_skirt_named_FLAG -> FAILED ['RESERVED_NAMES@blend', 'NEW_OBJECT_PREFIXES@blend', 'RESERVED_NAMES@fbx', 'NEW_OBJECT_PREFIXES@fbx']
MUT 8 rock_welded_icos_edge_shared_aligned -> FAILED ['ROCK_NOT_ICOSAHEDRON@blend', 'ROCK_VARIETY@blend', 'SEASTACK_TAPERED@blend', 'NEEDLE_SEA_STACKS@blend', 'ROCK_NOT_ICOSAHEDRON@fbx', 'ROCK_VARIETY@fbx', 'SEASTACK_TAPERED@fbx',
MUT 8 rock_poked_icosahedra_bundle_welded -> FAILED ['ROCK_NOT_ICOSAHEDRON@blend', 'ROCK_VARIETY@blend', 'SEASTACK_TAPERED@blend', 'NEEDLE_SEA_STACKS@blend', 'ROCK_NOT_ICOSAHEDRON@fbx', 'ROCK_VARIETY@fbx', 'SEASTACK_TAPERED@fbx', 
MUT 9 foam_vertical_curtain_6m_offshore_continuous -> FAILED ['UV_DENSITY@blend', 'NO_FOAM_STRIP@blend', 'UV_DENSITY@fbx', 'NO_FOAM_STRIP@fbx']
MUT 9 foam_sloped_skirt_underwater_z-1 -> FAILED ['NO_FOAM_STRIP@blend', 'NO_FOAM_STRIP@fbx']
MUT 9 foam_skirt_at_9m_offshore_continuous_steep -> FAILED ['NO_FOAM_STRIP@blend', 'NO_FOAM_STRIP@fbx']
MUT 9 foam_skirt_11m_offshore_continuous -> FAILED ['NO_FOAM_STRIP@blend', 'NO_FOAM_STRIP@fbx']
MUT 9 foam_white_skirt_named_FLAG -> FAILED ['RESERVED_NAMES@blend', 'NEW_OBJECT_PREFIXES@blend', 'RESERVED_NAMES@fbx', 'NEW_OBJECT_PREFIXES@fbx']
MUT 9 rock_welded_icos_edge_shared_aligned -> FAILED ['ROCK_NOT_ICOSAHEDRON@blend', 'ROCK_VARIETY@blend', 'SEASTACK_TAPERED@blend', 'ROCK_NOT_ICOSAHEDRON@fbx', 'ROCK_VARIETY@fbx', 'SEASTACK_TAPERED@fbx']
MUT 9 rock_poked_icosahedra_bundle_welded -> FAILED ['ROCK_NOT_ICOSAHEDRON@blend', 'ROCK_VARIETY@blend', 'SEASTACK_TAPERED@blend', 'ROCK_NOT_ICOSAHEDRON@fbx', 'ROCK_VARIETY@fbx', 'SEASTACK_TAPERED@fbx']
```

**The real props library** (props-only test FBXs of the props agent; `run_gate.py`):
```
RG g_rock_verts@fbx PASS (0.0s) - 60 rock objects / 10 unique rock meshes (ROCK_*/CLIFF_ROCK*/ROCK_WALL_*) are real faceted rocks on the WELDED mesh: >= 60 verts, >= 100 faces, >= 6 planar facet orientations, not sphere-like, not a box; no welded 12-vertex ico
RG g_rock_variety@fbx PASS (0.0s) - 7 unique rock SHAPE FAMILIES among ROCK_* (10 distinct meshes; families merge equal topology hashes (welded verts/faces + vertex-valence histogram) and geometric near-duplicates (PCA extent ratios +-0.04, vertex counts +-10%
RG g_rock_stretch@fbx PASS (0.0s) - 60 ROCK_/DRESS_ instances: every scale component (singular value) in [0.5, 2.0], max/min <= 2.0 (largest component 2.00, largest anisotropy 1.24); 60 of them are props-library meshes (topology hash, or shape match 0) and kee
RG g_props_off_play@fbx PASS (0.3s) - 732 scenery meshes (ROCK_/PLANT_/DRESS_/WATER_FALL, walls and cladding included): none above the 0 play-surface grid points (+ 0 samples at 0.25 m under 0 small DRESS_-type objects), none within 3 m of the pin, plants / lo
RG g_rock_verts@fbx PASS (0.0s) - 60 rock objects / 8 unique rock meshes (ROCK_*/CLIFF_ROCK*/ROCK_WALL_*) are real faceted rocks on the WELDED mesh: >= 60 verts, >= 100 faces, >= 6 planar facet orientations, not sphere-like, not a box; no welded 12-vertex icos
RG g_rock_variety@fbx PASS (0.0s) - 7 unique rock SHAPE FAMILIES among ROCK_* (8 distinct meshes; families merge equal topology hashes (welded verts/faces + vertex-valence histogram) and geometric near-duplicates (PCA extent ratios +-0.04, vertex counts +-10%,
RG g_rock_stretch@fbx PASS (0.0s) - 60 ROCK_/DRESS_ instances: every scale component (singular value) in [0.5, 2.0], max/min <= 2.0 (largest component 2.00, largest anisotropy 1.27); 60 of them are props-library meshes (topology hash, or shape match 0) and kee
RG g_props_off_play@fbx PASS (0.3s) - 793 scenery meshes (ROCK_/PLANT_/DRESS_/WATER_FALL, walls and cladding included): none above the 0 play-surface grid points (+ 0 samples at 0.25 m under 0 small DRESS_-type objects), none within 3 m of the pin, plants / lo
```

**Baseline holes 8-10 (= the files in the repo today; Look = snapshot 2026-10-04 10:45)**
```
baseline_08.json: Needle 92 gates, 51 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=PASS, NO_FOAM_STRIP=FAIL, SURF_SHORE=FAIL, SHELF_THIN=FAIL, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, SEASTACK_TAPERED=FAIL, NEEDLE_SEA_STACKS=FAIL, NEEDLE_ARCH=FAIL, ONE_GREEN=PASS, UV_DENSITY=FAIL, NEEDLE_CLIFF_SKIN=FAIL, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
baseline_09.json: Split 88 gates, 45 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=PASS, NO_FOAM_STRIP=FAIL, SURF_SHORE=FAIL, SHELF_THIN=FAIL, SPLIT_SCRUB_RIDGE=FAIL, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, SEASTACK_TAPERED=FAIL, ONE_GREEN=PASS, UV_DENSITY=FAIL, SPLIT_SHORE_SKIN=FAIL, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
baseline_10.json: Crater 92 gates, 41 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=PASS, NO_FOAM_STRIP=PASS, LAVA_TEXTURE=PASS, BASALT_PRISMS=PASS, SMOKE_SOFT=PASS, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, CRATER_WALL_COVERED=FAIL, ONE_GREEN=PASS, UV_DENSITY=FAIL, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
```

**A3 lib smoke builds of 2026-10-03 (pre-repair; Look = the old failing textures)**
```
libsmoke_old_08.json: Needle 92 gates, 35 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=FAIL, NO_FOAM_STRIP=FAIL, SURF_SHORE=PASS, SHELF_THIN=FAIL, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=FAIL, SEASTACK_TAPERED=FAIL, NEEDLE_SEA_STACKS=FAIL, NEEDLE_ARCH=FAIL, ONE_GREEN=PASS, UV_DENSITY=PASS, NEEDLE_CLIFF_SKIN=PASS, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
libsmoke_old_09.json: Split 88 gates, 27 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=FAIL, NO_FOAM_STRIP=FAIL, SURF_SHORE=PASS, SHELF_THIN=FAIL, SPLIT_SCRUB_RIDGE=PASS, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, SEASTACK_TAPERED=FAIL, ONE_GREEN=PASS, UV_DENSITY=PASS, SPLIT_SHORE_SKIN=PASS, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
libsmoke_old_10.json: Crater 92 gates, 31 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=FAIL, NO_FOAM_STRIP=PASS, LAVA_TEXTURE=FAIL, BASALT_PRISMS=FAIL, SMOKE_SOFT=FAIL, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, CRATER_WALL_COVERED=FAIL, ONE_GREEN=PASS, UV_DENSITY=PASS, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
```

**A3 lib smoke builds of 2026-10-04 10:44 (`lib_ground/smoke_holeNN`, work in progress of the ground agent; Look snapshot)**
```
libsmoke_now_08.json: Needle 92 gates, 27 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=PASS, NO_FOAM_STRIP=PASS, SURF_SHORE=PASS, SHELF_THIN=PASS, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, SEASTACK_TAPERED=FAIL, NEEDLE_SEA_STACKS=FAIL, NEEDLE_ARCH=FAIL, ONE_GREEN=PASS, UV_DENSITY=PASS, NEEDLE_CLIFF_SKIN=PASS, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
libsmoke_now_09.json: Split 88 gates, 21 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=PASS, NO_FOAM_STRIP=PASS, SURF_SHORE=PASS, SHELF_THIN=PASS, SPLIT_SCRUB_RIDGE=PASS, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, SEASTACK_TAPERED=FAIL, ONE_GREEN=PASS, UV_DENSITY=PASS, SPLIT_SHORE_SKIN=PASS, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
libsmoke_now_10.json: Crater 92 gates, 21 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=PASS, NO_FOAM_STRIP=PASS, LAVA_TEXTURE=PASS, BASALT_PRISMS=PASS, SMOKE_SOFT=PASS, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, CRATER_WALL_COVERED=PASS, ONE_GREEN=PASS, UV_DENSITY=PASS, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
```

**the same lib smoke holes against the LIVE `Unity/.../Look` folder at the time of the run (the tex agent keeps writing it)**
```
livelook_08.json: Needle 92 gates, 27 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=PASS, NO_FOAM_STRIP=PASS, SURF_SHORE=PASS, SHELF_THIN=PASS, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, SEASTACK_TAPERED=FAIL, NEEDLE_SEA_STACKS=FAIL, NEEDLE_ARCH=FAIL, ONE_GREEN=PASS, UV_DENSITY=PASS, NEEDLE_CLIFF_SKIN=PASS, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
livelook_09.json: Split 88 gates, 21 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=PASS, NO_FOAM_STRIP=PASS, SURF_SHORE=PASS, SHELF_THIN=PASS, SPLIT_SCRUB_RIDGE=PASS, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, SEASTACK_TAPERED=FAIL, ONE_GREEN=PASS, UV_DENSITY=PASS, SPLIT_SHORE_SKIN=PASS, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
livelook_10.json: Crater 92 gates, 21 failed
   ROCK_NOT_ICOSAHEDRON=FAIL, ROCK_VARIETY=FAIL, LOOK_FILES=FAIL, ALBEDO_DISTINCT=PASS, GRASS_ALBEDO_HUE=PASS, NO_FOAM_STRIP=PASS, LAVA_TEXTURE=PASS, BASALT_PRISMS=PASS, SMOKE_SOFT=PASS, PROPS_OFF_PLAY=PASS, NO_PLANT_ON_WATER=PASS, NO_ROCK_STRETCH_2X=FAIL, PATH_UNDER_BALL=PASS, CRATER_WALL_COVERED=PASS, ONE_GREEN=PASS, UV_DENSITY=PASS, PLAY_SURFACE_FACES=PASS, PLAY_SURFACE_WALLS=PASS, PLAY_SURFACE_GRID=PASS, PLAY_SURFACE_TOPS=PASS, SHADERS_STATIC=PASS, HOLE07_UNTOUCHED=PASS
```


# v2 area U 2026-10-04 — gate-tool finish (area U: Unity + gate tool, second continue pass)

Owner files: `blender/scripts/postcard_look_verify.py` (sha256 in `v2/gates/runs_u/verify_sha_for_selftest_final.txt`), this file, `v2/gates/` (`tools/still_floor.py`, `tools/probe_objects.py`, `tools/run_stills_gate.py`, `tools/tex_window_probe.py`, `calib/still_floor*.txt|json`, `runs_u/`). Rollback copies of the file as this pass found it: `v2/gates/postcard_look_verify.py.at_u_start`, `v2/gates/GATES.md.at_u_start`.
Everything above stays; the rows named below are REPLACED by what this section says. **A Blender PASS is never the Game-view PASS.**

## Run (new bits)

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 8 --blend work/postcard-look/v2/hole08/stage/hole_08.blend --fbx work/postcard-look/v2/hole08/stage/hole_08.fbx --json out.json   # a staged build
$B -b ... -- 8 --stills-dir DIR --require-stills        # LOOK_STILLS_TEXTURED reads DIR/hole08_tee.png + hole08_approach.png (default ArtDir/screenshots/golf_postcards/look); a missing still FAILS instead of skipping
$B -b ... -- all --selftest --selftest-fbx --selftest-dir DIR                    # full self-test (one process per hole is fine: `-- 8`, `-- 9`, `-- 10` in parallel, ~12 min each)
python3 work/postcard-look/v2/gates/tools/still_floor.py                         # re-measure the target stills (Pillow, no numpy) -> calib/still_floor_crops.txt|json
$B -b --factory-startup --python work/postcard-look/v2/gates/tools/probe_objects.py -- 8 file.blend           # every mesh object: material shares, welded vertices, open edges, box share, rock_shape verdict
$B -b --factory-startup --python work/postcard-look/v2/gates/tools/run_stills_gate.py -- DIR [DIR ...]       # STILL_FLOOR_SELFCHECK + LOOK_STILLS_TEXTURED on a folder of stills, holes 8 / 9 / 10
```

## What changed (five review findings, none weakened)

| # | finding | what the gate does now | mutants that must FAIL (all do, blend AND FBX stage) | controls that must PASS (all do) |
|---|---|---|---|---|
| 1 | rock / sea-stack / stack-taper gates selected objects by NAME (`ROCK_*`): a noisy 42-vertex icosphere named `DRESS_BOULDER`, 13-vertex icosahedra, welded icosahedron clusters and a stacked-box ziggurat named `DRESS_STACK` passed | **`rock_candidates(S)`**: a mesh is a ROCK when it is called ROCK_* / CLIFF_ROCK* **OR** >= 50 % of its area wears `LK_ROCK` / `LK_ROCK_WET` / `LK_BASALT` / `LK_CLIFF` / `LK_CLIFF_DARK` (or the legacy `MAT_ROCK*` / `MAT_CLIFF*`), whatever it is called; collision meshes and the hidden placeholders are not rocks; a rock-material mesh larger than 100 m in any direction is a backdrop (the Crater cone, 265 m) and is neither judged nor credited. **Cladding is judged by geometry**: a `ROCK_SKIN_*` mesh is exempt only when it is an OPEN SHELL (>= 5 % of its polygon edges open, >= 3 m across: the real skins measure 8-33 %); a closed compact solid called `ROCK_SKIN_99` is judged as the rock it is. `ROCK_NOT_ICOSAHEDRON`, `ROCK_VARIETY` (families), `NO_ROCK_STRETCH_2X`, `SEASTACK_TAPERED`, `NEEDLE_SEA_STACKS` all select through it (the sea-stack set no longer exempts `ROCK_WALL_*` by prefix). **Tiny closed solids anywhere**: any other non-plant, non-masonry, non-placeholder mesh that is a closed solid (<= 10 % open edges) of <= 64 welded vertices fails `ROCK_NOT_ICOSAHEDRON` (the old test was 'welded 12 vertices / 20 faces, not called PLANT_*': one poked face, 13 v / 22 f, beat it) | `dress_boulder_noisy_icosphere_42v`, `dress_pebble_icosahedron_13v_poked_face`, `dress_pebble_icosahedron_13v_on_grass_material` (a 13-vertex toy rock wearing LK_ROUGH: only its shape gives it away), `dress_cluster_welded_icosahedra`, `rock_skin_named_closed_icosahedron` (ROCK_NOT_ICOSAHEDRON); `dress_stack_ziggurat_boxes_named_DRESS_STACK` (SEASTACK_TAPERED + ROCK_NOT_ICOSAHEDRON), `stack_boxes_named_ROCK_WALL` (SEASTACK_TAPERED), `rock_named_PROP_7_stretched_3to1` (NO_ROCK_STRETCH_2X) | `ctl_dress_boulder_real_library_rock` (a real library rock under a DRESS_ name: classified, judged, passes ROCK_NOT_ICOSAHEDRON and NO_ROCK_STRETCH_2X) |
| 2 | `NO_ROCK_STRETCH_2X` used one window [0.5, 2.0] for the scale: a uniform 0.4 pebble was reported 'stretched' | three separate rules (constants `STRETCH_TH`): **anisotropy** (max / min singular value of matrix_world, and of the baked-mesh-vs-library size ratios) <= 2.0 = the STRETCH; **absolute upper cap** largest component <= 2.0; **lower bound** smallest component >= 0.4 (a library kind may shrink uniformly to 0.4). The messages say STRETCHED / scaled UP / shrunk below, so a pebble is never called stretched. Same rules at the FBX stage. The r3 PCA cap for rocks that are no library kind now applies to every classified rock | `rock_stretched_x3`, `rock_uniform_2p6` (upper cap), `rock_anisotropy_2p5`, `rock_uniform_shrunk_0p3` (lower bound), the library-baked / sheared / fuzzy-match mutants of round 3 | `ctl_uniform_0p4_pebble` (library rock at uniform 0.4: passes), `ctl_rock_scale_1p8_1p5_1p2`, `ctl_library_mesh_scaled_within_2x` |
| 3 | `LOOK_FILES` floor (0.03 in 90 % of the 1/16-tile windows) was the lead's number, not a measurement: the user's stills fail it | **Floors are the stills' own window statistic at the same window scale** (below). Grass ground albedos (Fairway, Green, Rough, Scrub): luminance sd >= **0.012** in >= 90 % of **1.2 m ground windows** (`TH2['win_sd']`, `TH2['win_foot_m']`; window = 1.2 m / tile metres x pixels, placed every half window); the iid-noise block-mean test, size floors, spectral-peak and repeated-cell tests are unchanged; every other opaque albedo keeps its 1/16-tile window and floor (the stills pass them: sand p10 0.0166 >= 0.008, stone / basalt p10 0.0182 >= 0.012). **New gate `STILL_FLOOR_SELFCHECK`** re-measures 22 clean crops of needle / split / crater.jpg with the verifier's own statistic and FAILS if the stills do not pass the floors. **New gate `LOOK_STILLS_TEXTURED`** (Game view): the lower 60 % of every `ArtDir/screenshots/golf_postcards/look/holeNN_tee.png` / `_approach.png` has <= 15 % flat 8 px windows (sd < 0.006, or the sd of the 4x4 block means < 0.003 = noise only); SKIPPED (PASS, said so) while the stills do not exist, FAIL under `--require-stills` | `tex_fairway_flat_rgb_noisy_alpha`, `tex_fairway_near_flat_dither`, `tex_fairway_flat_fill`, `tex_fairway_artwork_downsampled_to_128px`, `tex_fairway_8px_checkerboard`, `tex_fairway_random_16px_cell_tiled`, `tex_fairway_normal_flat_dither`, `tex_lava_flat_orange`, **`tex_fairway_smooth_below_stills_floor`** (new: structured but sd 0.01); Game view: flat colour, flat colour + noise sd 2.4 levels, stills missing under `--require-stills`; **`STILL_FLOOR_SELFCHECK` is itself mutation-tested**: floor 0.03 (the old number) and a flat threshold 0.03 both make it FAIL | `tex_ctl_fairway_at_stills_level` (window p10 0.0135: just above the floor, passes), a textured Game-view frame, 'no stills yet' (skipped), and the stills themselves |
| 4 | `NO_FOAM_STRIP`: the white test read the Principled base colour as stored (linear): a pale non-LK band slipped through | `white_materials`: a non-LK material is white-ish when its base colour is (V >= 0.8, S <= 0.2) **as stored OR sRGB-encoded** (a linear 0.75 reads 0.88 on screen), and when a base colour fed by an image texture has a white-ish mean | `foam_pale_non_LK_band_srgb_0p88` (linear 0.75, name without FOAM / SURF / SPRAY / WHITE) and the older white-material mutants | `ctl_foam_sand_coloured_non_LK_band` (sand colour V .74 S .32: not white) |
| 5 | the 1 mm collision tolerance was undocumented | see the next section | the 5 cm / 2 mm collision mutants of rounds 1-3 | the re-triangulation controls |

## How the stills' floors were measured (`tools/still_floor.py`, Pillow, no numpy; `calib/still_floor_crops.txt|json`)

Statistic = the verifier's own: luminance (Rec. 709 weights on the STORED sRGB values 0..1) standard deviation of every non-overlapping window of a crop. 11 clean MOWN-grass crops (needle mid_green / top_green; split upper_green / lower_green / fairway_strip / fairway_long / lower_fairway; crater pillar_green / tee_box x2 / fairway_mid), 6 sand crops and 5 stone / basalt crops, all drawn on the stills (`v2/gates/u/crops_*.png`), none touching rock, ball or flag.
* **Window scale.** The stills are 1280 x 720 aerials at ~0.13-0.18 m per pixel (Crater green 29.3 m across = ~220 px; Split green 31.1 m = ~177 px), so their 8 px window is ~1.1-1.4 m of ground. The old texture window (1/16 of a 10 m tile = 0.6 m) is below what the stills resolve (`calib/still_calib.txt` said so). The texture window is therefore a GROUND footprint of 1.2 m (the same scale as the stills' 8 px window): the floor is read at the same window scale, with no extrapolation. Sensitivity: the live Fairway_C reaches 10th-percentile window sd 0.0197 / 0.0248 / 0.0293 / 0.0353 at 0.4 / 0.75 / 1.2 / 1.6 m, Green_C 0.0222 / 0.0275 / 0.0319 / 0.0367, Rough_C 0.051+, Scrub_C 0.030+ (`tools/tex_window_probe.py`): every footprint from 0.4 to 2.4 m clears the floor, so the 20 % uncertainty of the stills' scale cannot flip a verdict.
* **The number.** 10th percentile of the 8 px windows over the 11 grass crops: lowest crop **0.0121** (split upper_green; median 0.018), then 0.0159 at 16 px; the old floor (0.03 in 90 % of windows) is failed by 10 of the 11 crops (they reach it in 19-78 % of their 8 px windows; only the Crater tee box reaches 93 %). The floor is 0.012 in 90 % of the windows (the lead's 90 % share kept).
* **Honest limits.** The stills are generated JPEGs (8 x 8 DCT blocks sit exactly at the finest window); 11 crops are a small sample; the lowest crop sits only 0.8 % above the floor. A texture can pass the floor and still look like the wrong grass (the other tests and the Game-view floor are the guard). The live Look PNGs pass at 52 % / 29 % of the OLD 1/16-tile windows >= 0.03 and at 100 % of the new windows (p10 0.029 / 0.032).
* **Game-view floor.** `flat_sd` 0.006 = HALF the stills' lowest p10 (0.0121): the Game view's 8 px window covers ~0.05-0.4 m of ground against the stills' ~1.2 m, and in the stills' own w8 / w16 / w32 series the window sd grows ~ footprint^0.4 (needle mid_green median 0.0386 / 0.0517 / 0.0674), so a 1/4-1/20 footprint is worth ~0.5. `flat_max` 15 % = the Unity probe's PROBE_GROUND_TEXTURED cap; the stills' own clean crops have <= 5 % flat windows (grass 5 %, sand 4 %, stone 3 %). Measured on real-geometry Game-view frames (K's probe, JPEG): flat baseline tee frames 99-100 % flat, textured tee frames 1.9 / 4.9 / 0.1 % (Needle / Split / Crater), the close putting-green views 15-27 % (smooth by nature: the gate reads tee and approach stills only; a hole whose APPROACH still is a close view of a smooth green can fail it, report it, do not tune it).

## The 1 mm collision tolerance (item 5)

Every comparison of the scoring surfaces against the baseline signature tolerates **1 mm** of geometric difference and no more, because that is the noise of the pipeline, not a dial:
* `PLAY_SURFACE_GRID`: the single-sided ray height of every 1.5 m grid point of the shore bounding box equals the baseline's within `HEIGHT_TOL` = 1e-3 m (mismatching hit / miss at any point fails outright).
* `PLAY_SURFACE_TOPS`: vertex sets match when every vertex has a partner within `VERT_TOL` = 2e-4 m; `PLAY_SURFACE_FACES`: a re-triangulated top surface passes when every baseline triangle centroid has a top surface under it at the same height within `cover_check(tol=1e-3)` and vice versa, top areas equal; `PLAY_SURFACE_WALLS`: a re-triangulated wall passes when every baseline triangle centroid is within `surface_cover3d(tol=1e-3)` of a current non-up surface that faces the same way (normal dot >= .5) and vice versa, areas equal (1e-6 relative); `MARKERS_FROZEN`: `MARKER_TOL` 1e-4 m.
* Why 1 mm: the Blender -> FBX -> Unity chain round-trips vertices at ~0.1 mm (the exact path rounds at 1e-4 m, float32 at 600 m holds ~0.06 mm), and re-triangulating one planar polygon moves a sampled height by < 0.01 mm. 1 mm leaves ten times that noise and is 0.1 % of the 0.7 m play band the game accepts (Unity ground height band 6.51..7.26 yd).
* Consequences, stated plainly: a collision vertex or surface moved by LESS than 1 mm is not a gate failure; 2 mm is (mutant `green_up_2mm` fails GRID / TOPS / FACES), 5 cm is (`terrain_wall_vertex_moved_5cm`, WALLS), a deleted / flipped / added polygon is at any size. Nothing a player can measure (LieAt, ball height, PLAY_Z = 6 m) changes below 1 mm. The tolerance applies ONLY to the frozen collision meshes (TERRAIN, FAIRWAY, GREEN, TEE_BOX, BUNKER, CART_PATH); every new object is judged without it.

## Known gaps added by this pass (honest list)
* Shape-based rock classification is by SHAPE + MATERIAL: a toy rock wearing `LK_PLANTS` or `LK_MASONRY` is exempt from the tiny-solid rule on purpose (shrubs are blobs, masonry blocks are boxes) and is policed by the plant / arch / ruin gates instead; a bundle of low-poly stones wearing the GRASS material with > 64 welded vertices is not classified as a rock at all.
* `ROCK_MATERIALS`, `PROP_FACE_BUDGET`, `SPLIT_RIDGE_SCATTER` and the loose-rock margin of `PROPS_OFF_PLAY` still select rocks by the ROCK_ name (they measure materials / budgets / placement of the objects the hole builder DECLARES as rocks; a disguised rock is the rock gates' business).
* A `ROCK_SKIN_*` that is an open shell is exempt whatever its shape: a cheater can delete half the faces of an icosphere and call it cladding; the skin gates (relief against the real shore) still see it.
* `STILL_FLOOR_SELFCHECK` is only as good as its 22 hand-picked crops; the 15 % Game-view cap is borrowed from the Unity probe, not derived from the stills; JPEG block artefacts sit at the stills' finest window.
* `LOOK_STILLS_TEXTURED` skips (PASS) until the stills exist; the final proof run must pass `--require-stills`.

## Evidence (area U, 2026-10-04)

Verifier `blender/scripts/postcard_look_verify.py` sha256 `884448e1fc042aa94d3a0d4f55f726e2c77ebff131e6d48e4d792c80564cda8f` = the file the full self-test below ran against (`v2/gates/runs_u/verify_sha_for_selftest_final.txt`; the file as this pass found it: `v2/gates/postcard_look_verify.py.at_u_start`).
**Self-test** (`--selftest --selftest-fbx`, one process per hole, `v2/gates/runs_u/selftest_final_h8|9|10.log`, combined `selftest_final_all.log`, per-gate table `selftest_final_summary.txt|json`): 201 + 190 + 176 lines, **0 expectations not met**, every mutant at the blend AND the FBX stage. Per gate, summed over the three holes (MUT_FAILS_ON_BAD / MUT_PASSES_ON_GOOD): ROCK_NOT_ICOSAHEDRON 68/68 / 12/12 (round 3: 51/51), ROCK_VARIETY 57/57 / 6/6, NO_ROCK_STRETCH_2X 33/33 / 24/24, SEASTACK_TAPERED 14/14 / 6/6, NO_FOAM_STRIP 39/39 / 8/8 (round 3: 37/37), LOOK_FILES 25/25 / 9/9 (round 3: 22/22), STILL_FLOOR_SELFCHECK 6/6 / 6/6, LOOK_STILLS_TEXTURED 9/9 / 9/9, PROPS_OFF_PLAY 15/15 / 9/9, PLAY_SURFACE_WALLS 9/9 / 9/9, PLAY_SURFACE_FACES 12/12 / 9/9. The synthetic positives pass all 94 / 90 / 94 gates.
**Staged builds** (`v2/gates/u/stage08|09|10.log|json`): hole 8 94 gates, hole 9 90, hole 10 94, **0 failed** at both stages (ROCK_NOT_ICOSAHEDRON judges 79 / 284 / 329 rocks, open-shell cladding excepted; NO_ROCK_STRETCH_2X 86 / 351 / 329 instances; LOOK_FILES PASS on the live Look; `LOOK_STILLS_TEXTURED` SKIPPED: no Game-view tee / approach stills exist yet). **Installed baseline holes** (`v2/gates/u/baseline_installed_8|9|10.log`): 49 / 43 / 39 gates fail, the same verdicts as before this pass except LOOK_FILES (now PASS) and the two new gates.
**Textures this pass was measured with:** the Look PNGs the texture agent re-installed at 19:52:35 (Fairway_C, Green_C, Lava_C/E/N, Rough_C/N, Scrub_C/N; sha256 prefixes in `v2/gates/runs_u/look_sha256_at_u_check1.txt`): LOOK_FILES PASS, window p10 at 1.2 m Fairway_C 0.0385, Green_C 0.0436, Rough_C 0.0620, Scrub_C 0.0537 (floor 0.012), and the old 0.03 floor at 1/16-tile windows is met too (Fairway_C 99 % of the 0.75 m windows, Green_C 99 % of the 0.4 m windows); GRASS_ALBEDO_HUE, ALBEDO_DISTINCT, LAVA_TEXTURE, BASALT_PRISMS, SMOKE_SOFT PASS on all three staged holes. Re-run on the final PNGs: see the last line of this section.

**Final re-run on the final PNGs (20:05, after the texture agent's last install: Fairway_C / Green_C / Rough_C / Scrub_C / Rough_N / Scrub_N at 19:52:35, Lava_C / Lava_E / Lava_N at 19:57:22; sha256 prefixes `v2/gates/runs_u/look_sha256_at_final_check.txt`):** `postcard_look_verify` on the three staged builds at both stages: hole 8 94 gates, hole 9 90, hole 10 94, **0 failed** (`v2/gates/runs_u/final_stage_08|09|10.log|json`), LOOK_FILES PASS on all three, LAVA_TEXTURE PASS (bright 88 %, dark 8 %, emission alone 83 %). The texture agent was still writing at the end of this pass: re-run `blender -b --factory-startup --python blender/scripts/postcard_look_verify.py -- N --blend ... --fbx ...` after any further `Look/` change (the floor is the stills', not the live files').


# v2 repair round 1 2026-10-04 — area unity + gates: the smoke has to be READABLE in the proof frames (two new gates, nothing weakened)

**Finding (independent review, high, hole 10):** no readable smoke plume in any of the three Crater proof stills (a ghostly streak in the aerial), while `SMOKE_SOFT` passed. Why it passed: every smoke gate measured ONE card
on a test board (`SMOKE_SOFT`: peak alpha, border, edge step, how far a card at 130 yd moves a frame) or the Game-view `SMOKE_SOFT` of the proof (`proof/measure.py`: |dLum| p95 >= 8, no minimum share of the frame): a card that moves 0.44 % / 0.07 % of the frame by a few
levels passed. Nothing asked "can a phone user pick out a plume in the tee, approach and lavarim stills?". Root causes (runtime side in RUNTIME.md "v2 repair round 1"): (1) the plume stood in the Game view at 390+ m inside Crater's fog and came out DARKER than the sky behind it
(fixed in the material), (2) the hole's three cards stand behind the wall / above the frame (hole builder: placement and size; the Smoke_C plume covers only 19 % of its card).

| gate (hole 10) | stage | what it measures | MUT / CTL (`--selftest`) |
|---|---|---|---|
| `SMOKE_IN_FRAME` | blend + FBX (Blender, ~8 s, no Unity) | for each proof shot of `v2/proof/stills_cfg_9.json` (fallback: three constants in the tool) a 72 x 128 ray grid with the game's camera (4.5 yd behind the ball, 2.4 yd up, 60 deg; the landmark camera of the cfg): the share of the frame covered by an UNOCCLUDED smoke card at accumulated effective alpha >= .30; every other opaque mesh occludes; the alpha is the shader's (`Smoke_C` alpha x `LK_SMOKE` AlphaGain / AlphaPower / `_EdgeFade` parsed from `GolfLook.cs`). Each of tee, approach, lavarim needs >= 1.5 % (the reviewer's number) | smoke_removed, smoke_cards_off_every_frame, smoke_cards_a_quarter_size, smoke_cards_behind_an_opaque_wall, tex_smoke_faint_alpha_0p06 FAIL it; the synthetic positive passes (self-test 5/5 bad, 2/2 good) |
| `SMOKE_VISIBLE_STILLS` | file level (Game view) | `stills_stats.json` written by `PostcardLookStills` (v2 repair round 1 renders every proof shot a second time with the `DRESS_SMOKE*` cards off): `smoke.share_readable` = the share of the frame the plume moves by >= 10 luminance levels; each Crater proof still needs >= 1.5 %. Stats of an older stills tool (no `smoke` block) FAIL ("re-shoot"); no stats = SKIPPED (PASS), `--require-stills` makes that a FAIL (the stats are looked for in `--stills-dir`, then next to the real stills in `ArtDir/.../look/`) | one frame at 0.04 %, one at 1.49 %, no `smoke` block, missing + `--require-stills` FAIL; all frames readable, all at 1.51 %, not yet there PASS (self-test 4/4 bad, 4/4 good) |
The first gate predicts the second (same cameras, same occlusion, the shader's alpha) but not the colour: it is the one the hole builder iterates against, the second is the proof.

**Calibration of the geometric threshold (alpha >= .30) against the Game view** (`v2/unity_r1/calib_smoke_frames.py`, current staged hole 10 vs `v2/unity_r1/stills_new2/stills_stats.json`, LK_SMOKE as installed): share of the frame covered at accumulated alpha >= .30 / Unity share of pixels moved by >= 10 levels:
tee 0.47 % / 0.30 %, approach 0.01 % / 0.04 % (1 pixel of the grid = 0.011 %: noise), lavarim 0.00 % / 0.00 %, aerial extra 1.42 % / 1.85 %. How readable a covered pixel is depends on the backdrop (the bright orange tee horizon needs more alpha than the aubergine cloud of the aerial), so .30 is a conservative middle:
at alpha >= .05 the tee reads 0.85 %, at >= .60 0.09 %.

**Where hole 10 stands today (staged = installed build, 20:36):** `SMOKE_IN_FRAME` FAIL (blend and FBX): tee 0.47 %, approach 0.01 %, lavarim 0.00 % (3 of 3 below 1.5 %); `SMOKE_VISIBLE_STILLS` FAIL (the stats in `ArtDir/.../look/` predate the tool: no `smoke` block; the re-shot scratch stats `v2/unity_r1/stills_new2/` read tee 0.30 %, approach 0.04 %, lavarim 0.00 %). Everything else of hole 10 passes (97 gates, 3 failed = these). Holes 8 and 9: unchanged
(94 / 90 gates, only the known `LK_TEXTURED@blend` relative-path FAIL of the installed blends, `proof/PROOF.md`).
**The fix is the hole builder's** (placement and size of the `DRESS_SMOKE_nn` cards; the contract keeps UV 0..1 over the card, so the runtime cannot enlarge a plume): the tee frame sees only 5.3 % open sky and the approach frame 0.3 % (the wall fills it), so the plumes have to stand IN FRONT of the wall (between the rim, 150 yd from the crater centre, and the wall ring at 295 yd:
`CRATER_CONE_SMOKE` already requires >= rim) and be big. `v2/unity_r1/smoke_place_probe.py` (read-only, `Blender -b --factory-startup --python ... --`) searches placements with the verifier's own camera, occlusion and alpha model and confirms them on real card meshes: **two cards pass every frame**
(bottom centre / z / width / height in Blender metres: (37, 137) z 4, 148 x 90 and (220, 188) z 1, 153 x 90, bowed like `build_smoke_cards`) with tee 1.54 %, approach 2.00 %, lavarim 9.73 %. A builder can use them or search again; the numbers are candidates, not a design.

**Decisions:** 1.5 % per still is the reviewer's example and is a constant (`SMOKE_VIS['share_min']`); the gate asks it of all three stills (the review: "no readable smoke plume in any of the three stills"); it is a floor, the plume of crater.jpg covers several %. `alpha_readable` .30 and the 10-level `readable_delta` are calibrated above.
**Limits:** one sample per pixel at 72 x 128 (0.011 % of the frame per sample), flat per-pixel alpha accumulation over at most 4 overlapping cards, no fog / sky colour (the Unity numbers carry those), the camera model is `CameraRig.FrameAddress` as of today and the shots of `stills_cfg_9.json` (a changed shot list is followed automatically; a changed `FrameAddress` is not).
**Run:** `$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 10` (97 gates, ~8 s) ; `-- 10 --selftest --selftest-fbx --selftest-only smoke --selftest-dir DIR` (~25 s). **Full self-test of this verifier** (`-- all --selftest --selftest-fbx`, sha256 `3fe3083eec7d7765beed6bc8a19b27763bb24dc6dc82d8d80f2a780d74f464a4`, `v2/unity_r1/selftest_all_fbx.log`, ~19 min): **498 lines, 0 expectations not met, RESULT SELFTEST ALL PASS**; positives 94 / 90 / 97 gates (holes 8 / 9 / 10) pass at both stages; all 33 per-gate `SELFTEST_GATE` lines PASS, incl. `SMOKE_IN_FRAME` 5/5 bad + 2/2 good, `SMOKE_VISIBLE_STILLS` 4/4 + 4/4, `SMOKE_SOFT` 5/5 + 2/2. The smoke mutants changed: `smoke_removed` now expects `CRATER_CONE_SMOKE` and `SMOKE_IN_FRAME`; new `smoke_cards_off_every_frame`, `smoke_cards_a_quarter_size`, `smoke_cards_behind_an_opaque_wall`, `tex_smoke_faint_alpha_0p06` and the seven stats-file unit tests; the synthetic hole 10 gets its own camera for the synthetic cards (`st_smoke_shots`).
Evidence: `v2/unity_r1/` (`verify/h10_b.log`, `selftest_smoke.log`, `selftest_all_fbx.log`, `calib_smoke_frames.json`, `smoke_place_probe.py`, rollback copies `postcard_look_verify.py.at_r1_start` and `GATES.md.at_r1_start`).


# v2 repair round 2 2026-10-04 — area unity: one new gate (GROUND_UV_LOCAL_SMEAR), nothing weakened

**Finding (independent review, low, hole 10):** the lava-rim still shows a wedge of hard horizontal streaks in the far fairway; the reviewer's hint was "raise the anisotropic level, check the UV density on the shelf strip". Measured (RUNTIME.md "v2 repair round 2"): part of it IS filtering (the importer's level 4: fixed at runtime, 16, and gated by the Unity smoke `LOOK_TEXTURE_ANISO_RUNTIME`);
the wedge is **UV smear in the installed hole 10 `FAIRWAY_FIRSTCUT`**: 3 triangles with UV Jacobian ratio 26:1, 4.7:1 and collapsed, 103 m2 (largest 72.8 m2), projected into the still with its real camera they cover exactly the wedge (`v2/unity_r2/lavarim_uv_overlay.png`), and no filtering level removes it.
`UV_DENSITY` could not see it by design: it allows 15 % of a material's area to be smeared beyond 4:1 (right for a wall draped over rocks) and this is 1.8 % of the first cut.

| gate | stage | what it measures | MUT / CTL (`--selftest`) |
|---|---|---|---|
| `GROUND_UV_LOCAL_SMEAR` | blend + FBX (Blender, < 1 s) | for every PLAY-SURFACE mesh (collision prefixes TERRAIN / FAIRWAY / GREEN / TEE_BOX / BUNKER / CART_PATH, so FAIRWAY_FIRSTCUT, GREEN_APRON and the bunker lips too) the per-triangle UV -> WORLD Jacobian singular-value ratio (closed form, 2 x 2 Gram matrix of dP/du, dP/dv; a UV triangle that collapses to a line counts 1000:1). Triangles above **4:1** must add up to **<= 15 m2 per mesh** and none may exceed **10 m2** | mutant `ground_uv_smear_local_64to1` (the FAIRWAY polygons nearest the mesh centre, ~45 m2, UVs scaled (8, 1/8) about each polygon's centre = 64:1) FAILs it on holes 8, 9, 10 at blend AND FBX; control `ctl_ground_uv_aniso_2p9` (same polygons, (1.7, 1/1.7) = 2.9:1) PASSes it. `SELFTEST_GATE GROUND_UV_LOCAL_SMEAR MUT_FAILS_ON_BAD 3/3 PASS; MUT_PASSES_ON_GOOD 9/9 PASS` |
**How the numbers were chosen (measured, `v2/unity_r2/uv_ground.py` on the installed blends, worst triangle ratio per mesh; area of the triangles over 4:1):** hole 8: every mesh <= 2.4:1 (FAIRWAY 1.1, FIRSTCUT 1.1, GREEN 1.0, APRON 1.0, TEE_BOX 1.0, TERRAIN_NEEDLE 2.4), 0 m2 over 4:1; hole 9: <= 3.3:1 (TERRAIN_SPLIT; FAIRWAY 1.2, FIRSTCUT 1.3), 0 m2; hole 10: every mesh <= 3.4:1 (FAIRWAY 3.4) with 0 m2, **except TERRAIN_CRATER 5.2 m2 (3 triangles, largest 2.3 m2, worst 6.4:1: the largest LEGAL value) and FAIRWAY_FIRSTCUT 103.1 m2 (3 triangles, largest 72.8 m2, collapsed one)**.
The limits sit between: 15 m2 is 2.9x the largest legal mesh and 6.9x under the defect; 10 m2 per triangle is 4.3x the largest legal triangle and 7.3x under the defect; a 3 x 3 m patch is what a golfer's camera (2.2 m up) resolves as a visible streak. Constants: `UV_SMEAR = dict(ratio=4.0, total_m2=15.0, single_m2=10.0)` at the top of `g_uv_local_smear`.
**Where the repo stands:** `v2/unity_r2/verify/installed_hole8|9|10.log` (installed files, both stages): hole 8 **96 PASS, 0 FAIL**; hole 9 91 PASS, 1 FAIL (the known `LK_TEXTURED@blend` relative image path of the installed blend); **hole 10 97 PASS, 2 FAIL = `GROUND_UV_LOCAL_SMEAR@blend` / `@fbx` ("FAIRWAY_FIRSTCUT: 3 triangle(s) ... cover 103 m2 (largest 73 m2, worst 1000:1)")**. That FAIL is the real defect and stays until the hole builder re-UVs the first cut; it is not a threshold problem (nothing else is within 2.9x of the limit).
With the level-16 Game-view stills (`--stills-dir v2/unity_r2/gate_stills_final --require-stills`): `LOOK_STILLS_TEXTURED` PASS on all three holes with the same flat shares as the proof stills (hole 8 4.8 % / 3.9 %, hole 9 3.7 % / 4.9 %, hole 10 0.4 % / 2.4 %), `SMOKE_VISIBLE_STILLS` PASS (2.54 / 5.65 / 5.27 %); the filtering level moves neither.
**Limits (honest):** world-space ratio of a triangle's own Jacobian: it sees a stretched triangle, not a seam where two correct UV islands meet; 4:1 of a single triangle is not a visual-quality proof for the rest of the mesh (UV_DENSITY still judges the mean density and the 15 % smear share); a mesh without a UV map is skipped here (UV_DENSITY fails it). The Unity-side companion is `LOOK_TEXTURE_ANISO_RUNTIME` in `GolfLookSmoke` (RUNTIME.md).
**Full self-test of the verifier with this gate** (`-- all --selftest --selftest-fbx`, verifier sha256 `5287deeda74460e7e4967efe93f1c615a351a3c27fa62133ee97966ada50e195`, `v2/unity_r2/selftest_full_r2.log`, ~21 min): **505 lines, 0 expectations not met, RESULT SELFTEST ALL PASS**; positives 96 / 92 / 99 gates (holes 8 / 9 / 10) pass at both stages; all 34 per-gate `SELFTEST_GATE` lines PASS (was 33; `GROUND_UV_LOCAL_SMEAR` 3/3 bad, 9/9 good; `UV_DENSITY` unchanged 9/9, 6/6).
**Run:** `$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 10` ; `-- all --selftest --selftest-fbx --selftest-only ground_uv --selftest-dir DIR` (~1 min). Evidence: `v2/unity_r2/` (`selftest_ground_uv.log`, `verify/`, `uv_ground.py`, `uv_bad.py`, `uv_bad_json.py`, rollback copies `postcard_look_verify.py.at_r2_start`, `GATES.md.at_r2_start`).


# v2 repair round 3 2026-10-05 (area unity + gate tool)
Evidence `v2/unity_r3/` (rollback copies `postcard_look_verify.py.at_r3_start`, `GATES.md.at_r3_start`, `measure.py.at_r3_start`; `GATE_LINES_r3.txt`). Where this section disagrees with the sections above, THIS section wins.

| gate | where | change | proof |
|---|---|---|---|
| `BASALT_JOINTS` (Game view, `v2/proof/measure.py`, additive edit of area I's file; helpers `basalt_shot_ok`, `basalt_network_ok`, `zhang_suen`, `skeleton_junctions`) | the three Crater proof stills + PostcardProofMasks id render | + non-glow mean S <= .25 (crater.jpg basalt (26,25,29) S .10, (39,32,34) S .18); + glow vertical-line share <= .80 (not streak-only); + aggregated Zhang-Suen skeleton junction clusters >= 3.0 per 100 skeleton px of the glow over all proof shots (crater.jpg wall crops 8.3-8.8, the streaky Game-view basalt .6-2.4: `branch_probe.py`). **The old floor "glow in vertical lines >= 50 %" is no longer applied**: crater.jpg's own wall crops measure vertical 5 / 5 / 37 % by that classification (a connected branching network is one blob), so the floor failed the reference and ASKED for the streak pattern the review rejected; horizontal rungs <= 20 %, coverage <= 20 %, median luminance <= 55 stay | `selftest_basalt_joints.py`: neutral branching network **PASS**, maroon branching network **FAIL** (S .54), neutral parallel vertical streaks **FAIL** (100 % vertical, .29 junctions), neutral horizontal ladders **FAIL** (100 % rungs). On the final stills: S .128 / .17 / .118 and median lum 35.5 / 23.5 / 28 **pass**; **BASALT_JOINTS FAILs on structure** (vertical 92.5 / 92.6 / 97.2 %, 1.27 junctions per 100 px): the content the texture / hole areas still owe |
| `SMOKE_IN_FRAME` twin (verifier `SMOKE_VIS.alpha_readable`) | Blender, blend + FBX | .30 -> **.20**, same calibration rule as the first one (the geometric share must not exceed the Game-view share): LK_SMOKE now peaks at .33 per card, Game view `share_readable` tee 1.89 % / approach 3.23 % / lava rim 3.88 %; geometric share at alpha >= .30: 0.97 / 1.31 / 2.12 % (2x under), >= .25: 1.43 / 1.57 / 2.48, **>= .20: 1.84 / 1.91 / 2.94 (<= Game view in all three)**, >= .15: 2.40 / 2.26 / 3.42 (tee above: not conservative) | `--selftest-only smoke`: SMOKE_IN_FRAME 5/5 bad + 2/2 good, SMOKE_SOFT 5/5 + 2/2, SMOKE_VISIBLE_STILLS 4/4 + 4/4, 0 expectations not met |
| `SMOKE_SOFT` / `SMOKE_SOFT_FAR` / `SMOKE_SOFT_GAMEVIEW` (runtime boards) | GolfLookSmoke | `SmokeAlphaMin` .55 -> **.30** (a first-build visibility proxy that cannot coexist with the Game-view cap on a 3-card stack; visibility stays gated by median >= 8, p99 >= 28 and by SMOKE_VISIBLE_STILLS); `SmokeAlphaMax`, border, edge bands unchanged | board card: alpha max .33, median 11.9 / 10.5, p99 40.7 / 37.0, edge 2.22 / 1.89 |
| `SMOKE_SOFT` (Game view, measure.py) | proof stills | thresholds unchanged (p95 >= 8, max <= 110, edge p99 <= 6) | tee edge 17.0/18.0 -> **3.05**, approach max 132.2 -> **101.6** (p95 117.5 -> 89.6), lava rim ok: **PASS** |
| `SMOKE_SOFT_INTERSECTION` (new) | runtime board | a card cutting an opaque wall at 40 deg: edge step p99 <= 6 with the table's `_SoftFade`, the control with `_SoftFade` 0 > 6 and >= 2x, the soft card still moves >= 3000 px | soft **5.03**, control **38.03**, 24,895 px, PASS under TennisURP and HeroBaseStudioURP |
| `BASALT_SHADOW_SIDE_NEUTRAL` (new) | runtime board | a wall facing AWAY from the key, 250 yd out, emission off (fog + ambient + lava lights): mean S <= .25, median luminance <= 40 | now S .13 / lum 28; **control `GOLF_LOOK_CRATER_OLD_ATMOSPHERE=1` + old tint: S .63 FAIL** while `BASALT_RENDERS_DARK` still passes (the board wall faces the key: the blind spot the review found) |
| `LAVA_FAR_ORANGE` (new) | runtime board | a lava slope 160 x 90 yd at 430 yd through the fog: >= 85 % in the orange band, <= 5 % G clipped | 94.4 %; **control `GOLF_LOOK_LAVA_FOG=1`: 68.2 % FAIL** (the grey fog without `_FogShare`) |
| `MATERIAL LK_SMOKE` / `LK_LAVA` | runtime | `_SoftFade` (smoke) / `_FogShare` (lava) exist on the shader and equal the table | PASS |
| `BASALT_NOT_GREEN`, `BASALT_RENDERS_DARK`, `BASALT_GLOW_ORANGE`, `GRASS_HUE_GAMEVIEW hole10`, `LAVA_ORANGE_NO_BLOOM`, `LAVA_LIGHTS_*`, `GOLFER_*` | unchanged | re-measured after the Crater atmosphere / tint / grass tint change | PASS (smoke_r3d 88/88, probes) |
**Totals (final run):** GolfLookSmoke **88/88** (TennisURP 33/33, HeroBaseStudioURP 33/33, URP_BOTH_ASSETS PASS); PostcardImportCheck 57 gate lines 0 failed; EditMode PostcardHoleTests 37/37; golfer probes hole 8 / 9 / 10 PASS; verifier hole 10 with the Game-view stills (`--stills-dir ... --require-stills`) **ALL PASS, 99 gates** (SMOKE_VISIBLE_STILLS, SMOKE_IN_FRAME @blend / @fbx, LOOK_STILLS_TEXTURED); Game-view measure: GRASS_HUE_GAMEVIEW 8 / 9 / 10, NOT_FLAT_PER_STILL, SHELF_NOT_LOUDEST, LAVA_ORANGE_AND_BRIGHT, SMOKE_SOFT, NO_PLANT_ON_SEA, NO_ROCK_STRETCH_2X, NO_FOAM_STRIP, PATH_UNDER_BALL PASS, **BASALT_JOINTS FAIL (structure only)**. The full verifier self-test (19 min) was NOT re-run: only the smoke subset (a threshold constant changed, no code path).


# v2 2026-10-05 area U: plant sway (user, 2026-10-04: "i want the gentle sway of the plants with the wind") - new gates, nothing weakened

Files: `blender/scripts/postcard_look_verify.py` (Blender side), `Unity/Assets/Editor/GolfPlantSwayCheck.cs` (Unity, `run_swaycheck.sh`), `Unity/Assets/Editor/PostcardLookStills.cs` (Game-view frame pairs, `v2/sway/run_swaystills.sh` + `v2/sway/sway_gates.py`),
`GolfLookSmoke` / `PostcardImportCheck` (material + shader rules). Contract: RUNTIME.md "v2 2026-10-05 area U". Evidence: `v2/sway/` (swaycheck_*.txt, stills_*/, rig_*/, selftest/, logs/).

| gate | where | rule | MUT / how it is proven able to fail |
|---|---|---|---|
| `PLANT_SWAY_COLORS` | verifier, blend AND FBX re-import (every hole) | every unique PLANT_* mesh: exactly one colour attribute; R = weight: root (lowest 4 % of the height, vines: the top) <= .05, tip > .6 (shrub / tree > .25: "shrubs low", see Decisions), rising with the distance from the root (corr >= .5); G in 0..1; B = 0; A = 1. FLOAT_COLOR point attribute in the blend, BYTE_COLOR corner attribute after the FBX re-import (`color_srgb` = the raw value: `v2/sway/blender/fbx_color_roundtrip.py`) | MUT: plants_without_sway_colors, plant_one_shrub_mesh_without_sway_colors, plants_root_weight_one_everywhere, plants_tip_weight_0p4, plants_B_one_no_sway_marker, plants_two_colour_layers; CTL: ctl_plants_sway_power_1p4_ramp |
| `PLANT_SWAY_CAPS` | verifier, blend + FBX | the user's caps at 20 mph (tuft .06, flower / agave .05, shrub / tree .03, vine .08 yd) as caps on the tip weight: AmpFull (read from GolfWindSway.cs, .058) x tip x 1.0198 <= cap | MUT: shrub_tip_weight_1p0_over_the_0p03_cap, flower_tip_weight_1p0_over_the_0p05_cap |
| `SHADERS_STATIC` (extended, not relaxed) | verifier, file gate | GolfLava.shader, GolfSurf.shader, GolfLook.cs, GolfAtmosphere.cs (sky), HoleView.cs: no `_Time` / `Time.time` / texture offset / `Update(`, and no `_GolfWind`. ONLY `GolfPlants.shader` and `GolfWindSway.cs` may read the clock; GolfPlants.shader must read `_GolfWind`; GolfWindSway.cs must exist | MUT (unit): lava_shader_reads__GolfWind, lava_shader_reads__Time, sky_script_reads_Time_time, shader_with__Time_and_texture_scroll (old); CTL: GolfPlants.shader + GolfWindSway.cs read the clock next to a static shader |
| `SWAY_SHADER_COMPILES` | Unity | imported without errors on Metal (the editor's API), supported, passes ForwardLit / ShadowCaster / DepthOnly / DepthNormals, SRP Batcher compatible (`ShaderUtil.GetSRPBatcherCompatibilityCode` reads 1 like URP Lit / Unlit / GolfSurf; "UI/Default" reads 10 and "Standard" 0: the probe is calibrated), no `exclude_renderers metal`, `#pragma target` <= 3.5, no geometry / tessellation / compute constructs | calibration controls are in the INFO line |
| `SWAY_MATERIAL_UNCHANGED` + `HOLE{8,9,10}_PLANTS_SWAY_SHADER` + `PLANTS_USE_SWAY_SHADER` | GolfLookSmoke, PostcardImportCheck | `GolfLook.Get("LK_PLANTS")` = GolfArcade/GolfPlants with `Plants_C`, the table tint, smoothness .10, metallic 0, instancing; no other table row is on it; every LK_PLANTS slot of the three instantiated holes renders it (hole 7 never comes here) | - |
| `SWAY_MIRROR_MATCHES_SHADER` | Unity, GPU | a weight-graded strip rendered by the REAL LK_PLANTS material (ortho camera, black background): the silhouette at 9 heights vs `GolfWindSway.Displacement`, 5 winds x 6 clocks x 2 camera axes x 2 instance poses (plain; rotated 25 deg + scaled 1.5 / .7 / 1.2: world-space displacement must not care): worst error <= 1.2 px (= 2 mm of a yard) | - |
| `SWAY_ROOT_PINNED` / `SWAY_NO_COLOURS_STATIC` | Unity, GPU | the weight-0 root row moves <= .35 px; a plant mesh WITHOUT colours and one with WHITE colours (B = 1) move <= .35 px under 20 mph | - |
| `SWAY_SHADOW_FOLLOWS_PLANT` | Unity, GPU | the ShadowCaster pass applies the same sway: a ShadowsOnly strip casts onto a ground quad from a slanted sun, the far end of its shadow moves with the plant tip over 9 wind / clock cases: slope .7-1.3 (measured .94 / .96 under TennisURP / HeroBaseStudioURP), correlation > .93 (.977 / .985), worst single difference <= .016 yd | negative control: GOLF_SWAY_NEGATIVE=1 (mirror halved) -> slope 1.88 FAIL |
| `SWAY_FBX_COLOURS_REACH_UNITY` + `SWAY_FBX_CHAIN_ON_GPU` | Unity | a fixture written by Blender with the libs' exporter options (`colors_type LINEAR`): Unity imports exactly (row/8, .37, 0, 1) as raw bytes, and the imported hierarchy (its node's axis conversion applied) through GolfPlants matches the mirror (<= 1.2 px) | - |
| `SWAY_WIND_DRIVEN` (`_MATH`, `_GPU`, `SWAY_HOOK_ON_HOLE_START`) | Unity + stills | amplitude strictly increasing over 0..20 mph, 0 mph = 25 % of full (> 0), clamped above 20; `_GolfWind` direction = (sin d, 0, cos d) for 10 headings; 600 s clock loop seamless; on the GPU the tip of a weight-1 strip leans toward the wind for 90 / 270 / 0 / 180 deg (mean over 18 clocks, > .004 yd); in the Game view `GolfGame.Wind` equals what `StartHole` handed to `GolfWindSway` after every hole start | - |
| `SWAY_PHASE_DECORRELATED` | Unity (mirror) | 300 pivot pairs 0.3-3.3 yd apart: displacement series correlated > .9 in <= 3 % of pairs, mean |corr| < .5 | - |
| `SWAY_GENTLE_CONTRACT` / `SWAY_GENTLE` | Unity | the mirror sampled over the whole 600 s loop at 0 / 10 / 20 mph: the authoring table's tip weights (CONTRACT) and the REAL PLANT_* meshes of the three holes at their real pivots (SWAY_GENTLE; FAILS "NOT MEASURED" while no installed mesh carries sway colours) stay under the caps | - |
| `PLANT_SWAY_COLORS_UNITY` | Unity | the verifier's rule on the meshes as Unity imported them (world heights through the FBX node) | - |
| `SWAY_FRAME_PAIR` | Game view (`sway_gates.py`) | each shot rendered twice, same camera, 1.2 s apart (fixed 12 mph wind, frozen clock): only plant pixels change (outside the plant mask 0 px), >= 150 px change per hole, repeat render identical, the mirror's max displacement of the hole's coloured plants at both clocks <= caps | the plant mask = the frame minus the same frame with every PLANT_ renderer off |
| `SWAY_ONLY_PLANTS` (`_RIG`, `_FRAMES`, `_REALTIME`) | Unity | 16 other LK_ materials in one frame: 0 differing px under 3 winds / clocks; the plant-less frames of the two clocks identical in every shot; and the REAL-TIME pair: 1.2 s of wall-clock time later (player loop running) 0 px differ outside the sea | the sea (TennisWater = the tennis shader's own engine-clock swell; frozen file) moves as before and is masked (`<shot>__sway_water.png`) |
| `SWAY_STILLS_DETERMINISTIC` | Game view | the frame rendered twice at the frozen clock is identical, and two separate Unity runs agree pixel for pixel outside the sea (Crater, which has no sea, is bit-identical in full) | - |

## Decisions (disclosed)
* **"tip weight > .6" and "shrubs low"**: the user's line asks for a tip weight above .6 on every PLANT_ mesh and says "shrubs low" in the same sentence. The caps are linear in the weight (AmpFull .058 yd x w x up to 1.02: the user's "weight x amplitude x waves"), so a shrub tip above .507 breaks its .03 yd cap. Tufts, flowers, agave and vines are held to > .6 as written; shrubs and trees to > .25 plus the cap gate. The props area builds shrubs at .48 and trees at .30.
* **AmpFull .058 yd**: .058 x sqrt(1 + .2^2) = .0592 <= the tuft cap .06; flowers at .84 -> .0497 <= .05; shrubs at .5 -> .0296 <= .03; vines at 1.0 -> .0592 <= .08. The idle breeze (0 mph) is 25 % of that.
* **Plants with no colours are static** (B = 1 reads as "no sway data", measured: SWAY_NO_COLOURS_STATIC). Until the rebuilt plant meshes are installed the Game-view frame pairs use IN-MEMORY synthetic height-based colours (`GOLF_STILLS_SWAY_TESTCOLORS=1`, flagged `test_colours` in the stats): they prove the shader and the pipeline on the real holes, not the library's colours.
* **The sea is not ours**: TennisWater reads the engine clock (`_Time.y`), is frozen by the brief and is not "plants". Frame pairs are rendered inside ONE player frame so it does not move between them; across separate runs and across real time it does move, so those comparisons mask it. `Time.timeScale = 0` was tried and does NOT make it reproducible (both runs froze at Time.time 0.044 and the sea still differed in 12 of 18 frames).
* **Metal / iOS**: compiled for Metal in the macOS editor only; no iOS player build, no device frame time (not measurable here).

## Evidence (area U, 2026-10-05)
* Unity: `v2/sway/swaycheck_a17.txt` (23 / 25: the installed holes' meshes carry no sway colours yet), negative control `swaycheck_neg.txt` (17 / 25: the three mirror-dependent GPU gates FAIL under both URP assets), `runtime/smoke_u2.txt` 95 / 95, `runtime/importcheck_u2.txt` 60 lines 0 failed, `editmode_golfwindswaytests.xml` 16 / 16.
* Game view: `v2/sway/stills_final_r1|r2/` (+ `sheet_sway_pairs_hole08|09|10.jpg`, `sway_gates_final.txt`): SWAY_FRAME_PAIR, SWAY_ONLY_PLANTS_FRAMES, SWAY_ONLY_PLANTS_REALTIME, SWAY_STILLS_DETERMINISTIC, SWAY_HOOK_ON_HOLE_START PASS with SYNTHETIC in-memory colours (the installed FBXs have none).
* Verifier: `--selftest --selftest-fbx` on all three holes, 538 lines (`v2/sway/logs/selftest_full2.log`): `SELFTEST_GATE PLANT_SWAY_COLORS MUT_FAILS_ON_BAD 18/18, MUT_PASSES_ON_GOOD 9/9`, `SHADERS_STATIC 4/4 + 4/4`, `PLANT_SWAY_CAPS 4/6` on that run because the flower mutant had no flower to mutate on holes 9 / 10 (fixed in `m_sway_flower_over`, re-run: PASS on both, `logs/selftest_h9_flower.log`, `selftest_h10_flower.log`); the synthetic positive of every hole passes all 100 gates in blend + FBX; the rest of the suite unchanged (0 FAIL lines other than that).
* Installed holes, verifier: `verify_installed_hole{8,9,10}_final.json`: the only failures are PLANT_SWAY_COLORS / PLANT_SWAY_CAPS (blend + FBX).
* Props library (Blender `v2/sway/blender/props_lib_sway_probe.py`; Unity via `make_lib_fixture.py` + GolfPlantSwayCheck "[props library fixture]"): 21 / 21 plant kinds pass every sway rule and the caps (the props area's weights: tuft 1.0, flower / agave .8, shrub .48, tree .3, vine 1.0).
* Carry-over: `v2/proof/measure.py` (additive, `.before_u` copy kept): frame consistency without the water pixels; arch 8.24 % -> 0.00 % (scratch run `v2/sway/measure_test_METRICS.md`).
* Scratch rebuild of hole 8 with the current libs (`v2/sway/scratch_h8/`, never installed): verifier RESULT: ALL PASS (PLANT_SWAY_COLORS / PLANT_SWAY_CAPS on the blend and the FBX re-import), Unity `swaycheck_scratch8.txt`: PLANT_SWAY_COLORS_UNITY + SWAY_GENTLE PASS on its 809 plants. Re-run for the installed holes with `v2/sway/run_all.sh <label>` (add `testcolors` only while the installed FBXs predate the sway colours).
