# LIB_BUGS - hole 9 (Split) builder, 2026-10-04

Libraries are not edited by the hole builders; each bug is worked around inside blender/scripts/hole09_build.py / hole09_look.py.

## 1. postcard_look_lib.build_sea: rock puffs read a STALE matrix_world (0 candidates)

`build_sea(..., rock_puffs=6)` collects "rocks standing in the sea 3-12 m off the shore" from `o.matrix_world @ v.co`
(postcard_look_lib.py ~line 1750). Objects that were created in the same session have an identity `matrix_world` until the view layer
is updated, so every rock is measured at the library origin (signed distance -20 m = "on land") and the log says
`build_sea: 0 rock-puff candidates` however many wet rocks stand in the water.

Repro (Blender -b): `P.start`, `build_terrain`, `build_play_surfaces`, `PL.scatter(D, [...], 10, region=PL.region_band(D, 3.6, 11.0, "sea"),
z=(-0.15, 0.25), sink=0.0, wet=True, surface="sea")`, then read `o.matrix_world @ v.co` of the new rocks: bounding box at (0, 0, 0..1.4),
`P.signed_dist_m` = -20 m. Run `bpy.context.view_layer.update()` first and the real positions appear. The lib smoke never noticed because its
scenes are saved and re-opened before the puffs matter or hold no rocks.

Workaround (hole09_build.py): `bpy.context.view_layer.update()` right before `L.build_sea(D)`.
Suggested fix in the lib: call `bpy.context.view_layer.update()` at the top of `build_sea` (and in any helper that reads `matrix_world` of objects
created in the same run).

## 2. postcard_props_lib.build_ruin: `doorway_w` is not the clear width of the doorway (minor, documented behaviour)

`build_ruin(..., doorway_w=2.1, doorway_h=2.6)` only skips blocks whose CENTRE lies within `doorway_w / 2` (+ 0.35 m at the lintel course) of the doorway
point. With blocks 1.3-2.1 m long, the neighbouring blocks extend up to half a block length into the opening, so the free span is narrower than
`doorway_w`: measured with horizontal rays through the wall (every 0.25 m of height from 0.3 to 2.4 m), `doorway_w=2.1` left only 0.9 m clear (a
person-sized slot, and below the 1.5 m my gate wants), `doorway_w=3.0` left 2.7 m. Repro: `PL.build_ruin(None, [(0, 0), (12, 0)], height_m=5.6,
thickness_m=1.5, doorway_at=0.5, doorway_w=2.1, doorway_h=2.6, seed=52, course_h=0.85, block_l=(1.3, 2.1), base_z=0.0)` then ray-cast through the wall at x = 6.
Workaround (hole09_look.py): `doorway_w=3.0`. Suggested fix in the lib: trim or drop any block that overlaps the doorway span instead of testing its centre only.

## 3. Not bugs, but behaviours that cost time (for the next hole builder)

* `PL.scatter` keeps EVERY registered footprint (any kind) at least `min_gap` away: an agave with `min_gap=8` found no place after 110 shrubs and 70 stones were registered
  (0 placed, silently). Scatter the sparse / large-gap kinds first. Props placed with `PL.place` (outcrops, arch, stacks) are NOT registered; register them by hand
  (`PL._occ(D).append((x, y, r))`, `hole09_look._register`) before the plants, or the plants grow through them.
* `scatter(..., masks=[...])` tests user masks at the prop CENTRE only (only the safety masks test the footprint ring), so a clearance rule (route, channel lip) must add the prop's
  radius to the mask distance (`hole09_look.far_route(r)`); a 9 m crag centred 7.3 m from a route violated an 8 yd clearance by 6 m before this was done.
* `bpy.data.libraries.load(..., link=False)` turns the list you assign to `data_to.objects` into the loaded objects in place (copy the name list first).

## ROUND 2 additions (2026-10-04, after the skeptic review)

No library file was edited. Two more behaviours that cost time:

### 4. postcard_lib.build_play_surfaces does not return the lip ring data (DRESS_SAND needs it)

`BUNKER_nn_LIP` is built from per-angle ring points (inner scale 1.0 at play+0.32, mid 1.0+0.45*(s_out-1) at play+0.57, outer s_out at play+0.22; s_out from the candidate scales
1.22 .. 1.03 that stay off the water). A visual overlay that has to follow the lip (hole09_look.build_sand_overlay) must know the ring points, but only the finished mesh is returned.
Workaround: `hole09_look.bunker_lip_geometry` replays the same functions (`P._bunker_ring_pts`, `P.lie_codes_m`) and the build RAISES if any replayed ring point is not a vertex of the
real BUNKER_nn_LIP mesh (tolerance 1e-4 m: the mesh stores float32), so a change in postcard_lib cannot silently misalign the sand. Suggested lib change: return the arrays (inner / mid / outer / good) next to the object.

### 5. Down-rays that start exactly on a mesh boundary edge are ambiguous

An overlay vertex placed exactly on the outer edge of the lip (the lip ends there with no skirt; the fairway is 8-14 cm lower) or on the inner edge (the sand plateau is 2 cm lower than the lip foot) can be
ray-cast onto the surface BELOW (float noise), which reads as 9 cm / 3 cm "above the ground" in PATH_UNDER_BALL. The first round-2 build measured 8.9 cm for exactly this reason. Workaround: the end rows of
the sand overlay sit 1.5 % inside the lip edges. (`postcard_look_lib.measure_path` / `path_gate` only look at DRESS_PATH_*; DRESS_SAND_* is measured by postcard_look_verify PATH_UNDER_BALL and by hole09_qa H_BUNKER_SAND_OVERLAY.)

### 6. PL.scatter and PL.place keep no occupancy for hand-placed objects (unchanged from round 1) and DRESS_ objects are not plant supports

`SUPPORT_RE` in the verifier lets a plant stand on ROCK_ (not skins) and DRESS_ARCH / RUIN / BLOCK, but not on other DRESS_ pieces: the round-2 DRESS_KNOLL hummocks therefore carry no plants (the thickets stand round them, the footprints are registered with `_register`).

## ROUND 3 additions (2026-10-04, after the second skeptic review)

No library, verifier, texture or design file was edited. Findings of this round:

### 7. LOOK_FILES fails for Fairway_C / Green_C on every hole (texture owner / lead, not a hole script problem)

Repro: `Blender -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 9 --blend work/postcard-look/v2/hole09/stage/hole_09.blend --fbx work/postcard-look/v2/hole09/stage/hole_09.fbx`
-> `LOOK_FILES@blend` and `@fbx` FAIL (Fairway_C 1 % of its 64 px windows reach luminance sd 0.03, p10 0.0140; Green_C 0 %, p10 0.0101). TEXTURES.md T.2 already says the floor is stricter than the Game view
(the phone camera shows 0-5 % flat tiles) and calls it the lead's call. Measured fix (not applied, not mine): `round3/proposal_textures/` (README.md): 6-24 px multiplicative zero-mean noise, amplitude 0.06 / 0.07; with
the two PNGs substituted the whole verifier run has LOOK_FILES PASS at both stages and no other new FAIL (`round3/evidence/look_verify_with_candidate_textures.log`).

### 8. postcard_look_verify.py --look-dir with a staged BLEND: LK_TEXTURED@blend reports "resolves outside the Look folder"

The staged blend's images keep the absolute path of the repo Look folder, so a verifier run with `--look-dir <other folder>` fails `LK_TEXTURED@blend` (an artefact of the scratch folder, the FBX stage is unaffected). Seen only in the candidate-texture experiment above.

### 9. Not a library bug but a gameplay-visibility fact for the lead: props on the Rough ridge can hide a ball

Every ROCK_ / PLANT_ / DRESS_ prop is non-colliding and the ridge is Rough (Hole.LieAt, frozen), so a ball can come to rest inside a prop. `tools/ball_cover.py` (report only, `round3/evidence/ball_cover.json`):
8.2 % of 3,677 Rough ridge positions are inside a prop; within 8 yd of the dry safe route 1.6 % (knolls 1.4 %, masonry and chain rocks 0.1 % each: the classes the design allows at 4-6 yd), off the route 13.5 % (knolls 9.1 %,
rocks 1.8 %, crags 1.5 %, plants 0.7 %, masonry 0.4 %). Hidden from the phone address camera off the route: 27 % per heading. The footprints of the 30 knolls are unchanged since round 2 (round 3 made them taller and
craggier, not wider). If this matters, the options are outside a hole script: a HoleView ball marker / camera lift when the ball rests under a non-colliding mesh, or fewer/smaller knolls (a design trade against the relief the reviewer asked for).

## REPAIR ROUND 1 additions (v2 2026-10-04, after the third review; libs / textures / Unity untouched, hole scripts + this folder only)

### 10. postcard_props_lib.build_ruin / build_masonry_arch cannot make a believable ruin (replaced in the hole script: `blender/scripts/hole09_masonry.py`)

* `build_ruin` decides every block by its OWN height test (`z0 + course_h * U(.35,.75) > profile(s)` skips it) and by `clip(x, y)` on its centre: a block can stay above a skipped one (a floating slab) and a lintel
  course is a 0.6 m box of `doorway_w + 0.7` with no check that the jambs under it exist. All blocks are axis-aligned `_box_block` boxes with +-0.025 rad yaw, flat-shaded, one box UV for the whole mesh (the painted
  brick grid of Masonry_C.png runs across every block), nothing is buried (`-0.08`), and the arch is regular cut voussoirs with a proud keystone. The reviewer read this as stacked Lego boxes.
* The replacement keeps the names (`DRESS_RUIN_nn_pp`, `DRESS_ARCH_nn_pp`), LK_MASONRY only and the QA / verify contracts (doorway free span, lintel above it, >= 12 pieces, arch present, 7 yd off the cliff, 6 yd off the route, 12 m off the centerline).
  It calls the props lib's PRIVATE `PL._hull` (convex hull of a point set, planar facets merged): if the lib renames it, `hole09_masonry.py` fails at import, not silently.
* Gate-writing lessons (all in `tools/ruin_check.py`, every one cost an iteration): (a) a vertical ray from a block corner passes through the 2.5 cm joint of the course below and sees the ground: judge the bed face with a 4 cm cross of rays, centroid + 60 % samples,
  and count a point INSIDE another stone (the ray meets a back face first) as touching; (b) voussoirs rest on their neighbours (thrust), not on what is straight below: only DRESS_ARCH stones may be supported by face contact with an already supported stone (>= 3 vertices within 6 cm);
  (c) a lintel spans the doorway: its middle is over the opening by design, judge its two bearing ends (12-32 cm in from each end) and the clear opening, not the centroid; (d) the doorway rays must ignore a fallen DRESS_BLOCK 4 m behind the wall (the QA looks at DRESS_RUIN_* only);
  (e) the first-pass bearing samples sat at 0.3-0.45 m from the lintel end, i.e. exactly on the door-side edge of the 0.55 m bearing: sample 12-32 cm.
* Construction rule that mattered: "centre over the course below" is not enough (a long stone over a short one with its neighbour dropped cantilevers half its length): >= 60 % of the bed must be supported, and the two jamb stones beside the doorway are forced (profile and support tests skipped) with the quoin lengths
  chosen so the short one is >= 62 % of the long one; the height profile beside the door steps down over 2.4 m so the jambs are not lone towers.
* The arch was moved 1.5 yd east (`ARCH_SHIFT_YD = (1.0, 5.5)`): with the west pier's vertices 6 yd off the dry safe route the clip cut a block of the pier and the voussoirs above it floated (the support gate caught it at once).

### 11. The ruin landmark gate counted buried vertices as "blocked by the terrain"

`tools/make_landmarks.py` / `tools/landmarks_check.py` sample random masonry vertices and ray-cast them to the camera. With a buried first course (0.25-0.45 m under the ground by design) ~5 % of the samples are under the ground and
are blocked by TERRAIN_SPLIT by construction (95.5 % < the 97 % threshold). Both tools now sample only vertices >= 6 cm above the ground (a ground-only BVH: the masonry must not count as ground) and the landmark core is "the arch + the masonry within 6.5 m of the design doorway"
(there is no `DRESS_RUIN_00` tall-wall mesh any more). The threshold is unchanged (97 %): 800 of 800 samples reach the camera.

### 12. TEE_BOX material

The hole 9 tee box was LK_GREEN (planar UV: no mow stripes) beside the LK_FAIRWAY ribbon (centerline UV: stripes): a ruler-straight tone step at the tee far edge. `TEE_BOX` is LK_FAIRWAY now (postcard_look_verify allows both): `assign_uvs` gives it centerline UVs (TEE_BOX {'centerline': 54}), so the pattern is continuous.
Diagnosis by bisection in the preview: with TEE_BOX hidden no step; with the tee box lowered 10 cm no step; so the ~2 levels that remain are the 10 cm plateau (scoring height, frozen), not material or UV. Preview numbers only: tools/seam_check.py.

### 13. FIRSTCUT collar -> LK_ROUGH; things NOT done on purpose (finding "island does not read as Split at tee / approach")

* DONE: `FAIRWAY_FIRSTCUT` is LK_ROUGH. `postcard_lib` builds it as "fairway / tee / rough within 3 yd of the fairway edge" at +0.08 (the FAIRWAY mesh is +0.14 over it), so its VISIBLE part is the rough lie (`tools/collar_lie_check.py`: 1947 of 1947
  visible points are Rough; the hidden part under the FAIRWAY is 98 % Fairway). The look lib's RETARGET maps MAT_FIRSTCUT to LK_FAIRWAY (verify allows LK_ROUGH too), which made a 3 yd stretch of rough lie look like fairway. Swapping the material BEFORE `assign_uvs` gives it
  planar+warp UVs and the long n-gons of that mesh (up to 108 m2, anisotropy 200:1 at the loop corners) streak (seen in the preview); swapping AFTER keeps the centerline UVs (smooth). The same would apply to holes 8 / 10 (not touched).
* NOT done: no fringe props at the near lip: the lip of the first ribbon section is FAIRWAY (play surface); `PROPS_OFF_PLAY` / `mask_off_play` forbid props there, and a sea rock beyond the lip is hidden behind it from the 2.4 yd address camera (approximate sight line: ~4.6 m under ground level 10 m beyond the lip).
* The lower 60 % flatness of those frames is also a texture property (Fairway_C mid-frequency grain, owned by the shared fixers) and of the framing (36 deg across). Re-judge on the re-shot Game-view stills.

## ROUND 6 additions (2026-10-05, repair round 2: "the ruin still reads as stacked bricks")

No library, verifier, texture or design file was edited (shas at the start of the round: `lib_sha_r6_start.txt`; unchanged at the end). Behaviours that cost time:

### 10. `postcard_look_lib._new_piece` / `_finish_mesh` always smooth-shade (shade_smooth + set_sharp_from_angle): a big n-gon gets a vertex-normal gradient and the triangulation shows as a diagonal

Measured on the round-1 ruin (`r6/face_stats.py`): 20.7 % of 2,388 masonry faces had a loop normal more than 3 deg (worst 28 deg) off their own face normal (the 32 deg crease angle averages a stone's chamfer facets into
the vertices of its big faces). UVs were exact (affine residual 0), so the review's "UV shear / triangle splits" was the shading. Workaround (hole09_masonry.StoneSet.flush): `ob.data.shade_flat()` right after `_new_piece`.
Suggested lib change: a `flat=True` parameter of `_new_piece` (hard-surface pieces: masonry, blocks) that skips `shade_smooth`.

### 11. Masonry_C.png: the brick interiors can not be found by a pixel scan alone

The mortar columns of the 8 course rows were scanned from the pixels (darker than the row median by 0.07): 5 of the 46 vertical joints of the generator (`golf_look_textures.mat_masonry`, seed 1001) were missed (rows 4, 6, 7: one detected "brick" spanned two joints),
and the texture carries weathering stains (`stain`, thin vertical drips in the lower 70 % of each course) and moss that read as dark / green streaks inside a brick. hole09_masonry.brick_segments intersects the pixel scan with the generator's joint table
(re-derived from its random tables: `default_rng([1001, 1])`, per course `integers(4, 8)` bricks, `uniform(0.6, 1.4, nb)` widths, one phase); ruin_check.py RUIN_UV_BRICK_INTERIOR uses the generator table alone. If the texture owner changes `mat_masonry`, both break loudly (the gate drops under 95 %).

### 12. `bmesh.ops.convex_hull` + `dissolve_limit`: a pillow apex on a face is a pyramid

PL._hull(points, dissolve_deg=0.8) with an apex pushed 1-5 cm out of a face turns the face into 4-6 triangles at 2-6 deg to each other. With smooth shading they were the diagonal artefact again, with flat shading an X on every face. Removed (rough_points p_bulge = 0).

### 13. Not bugs, but behaviours of the support gate (tools/ruin_check.py RUIN_SUPPORTED) that cost time

* A bed that sinks 3 cm into the stone below (tried to make a chipped top safe, then REVERTED: SINK = 0 in hole09_masonry) is read as a hole by the ray test when a THIRD stone's top face is the first front face under the bed point (the ray starts inside stone B and meets
  stone C, which B overlaps, first). The gate got a convex-hull inside test (every stone is a convex hull) before the ray test (kept: exact for convex stones, harmless without overlap).
* A bridging stone's centre sample can sit exactly over a joint between two stones below (a 5 cm gap + the corner chips of both, 13 cm): the support cross now reaches 8 cm (was 3 cm).
* Two stones that overlap in depth by < 72 % (depth 0.78 of the wall, centres offset +-0.17 m) leave the outer face of the upper one unsupported: depth is now 0.86-1.0 of the wall.

## REPAIR ROUND 3 (2026-10-05) - what the review of round 2 found behind "stacked boxes", and library / verifier behaviours worth knowing

### 14. `PL._hull` faces are not planar when the 8 corners are twisted / tapered / sheared: the ROOT cause of the 'diagonal triangle shading'

`PL._hull(points, merge=0.012, dissolve_deg=0.8)` returns the convex hull of the stone's points with coplanar triangles (within 0.8 deg) dissolved into polygons. The six faces of a hand-hewn stone (taper + shear + twist + tilted top) are NOT planar quads, so the hull keeps each as two triangles whose normals differ by 1-7 deg
(round-2 stage, `r7/face_split_stats.py`: 4,477 faces, 2,467 triangles, 1,411 near-coplanar adjacent pairs (< 20 deg, median 1.6 deg), 1,092 of them with a different UV along the shared edge, because `StoneSet.add` drew one random brick window PER POLYGON). Flat shading (round 2) removed the normal gradient but not this.
Fix: `blender/scripts/hole09_stone.py` builds stones as half-space intersections (planes), so a face can not be a non-planar quad; `hole09_masonry.py` no longer calls `PL._hull`. Gates RUIN_PLANAR_FACES / RUIN_NO_UV_SPLIT keep it that way. The library's own props are untouched.

### 15. The verifier classifies a mesh as a ROCK by MATERIAL (>= 50 % of its area on LK_ROCK / LK_ROCK_WET / LK_BASALT / LK_CLIFF*), whatever it is called

`postcard_look_verify.rock_candidates` + `ROCK_MAT_SHARE = 0.5`: a DRESS_BLOCK or a DRESS_ARCH mesh whose area is mostly LK_ROCK is held to ROCK_NOT_ICOSAHEDRON (>= 100 faces, facet orientations, not sphere-like, not a box). The first round-3 build (LK_ROCK fallen blocks of 98 vertices, a DRESS_ARCH mesh with 59 % rock) failed it with
'sphere-like (whitened radius cv 0.087 < 0.15)' / '75 faces < 100'. The DRESS_BLOCK variants stay LK_MASONRY (exempt, TINY_SOLID_EXEMPT_MATS), and `StoneSet` keeps LK_ROCK <= 36 % of the area of the mesh it is filling (`ROCK_MAX`), which also satisfies PROP_MATERIALS (DRESS_ARCH / DRESS_RUIN need >= 50 % LK_MASONRY).

### 16. The generic `^DRESS_` rule forbids LK_FAIRWAY / LK_GREEN: no grass-coloured skirt can dress the tee plate

`PROP_RULES`: `^DRESS_` may use every LK material except LK_GREEN, LK_FAIRWAY, LK_WATER*, LK_SURF, LK_FALL. A sloped skirt from the 10 cm tee plate down to the fairway (the geometric cure of the plate's parallax) would have to be an LK_FAIRWAY DRESS_ mesh (rejected), a ground-prefixed mesh (a new collider, and the
frozen ground gates) or LK_ROUGH (a darker grass: another visible edge). The plate's UVs are compensated instead (`hole09_build.tee_parallax_uvs`, UV data only). Not a library bug; recorded because the review's hint 'add a feathered blend' had no mesh-level implementation under the contract.

### 17. `postcard_lib.save` (P.save) remaps image paths RELATIVE to the staging folder

`bpy.ops.wm.save_as_mainfile(filepath=path)` with the default `relative_remap=True` stores `//../../../../../Unity/Assets/Resources/Course/Look/*.png`, valid only from `work/postcard-look/v2/hole09/stage/`: copied to `blender/hole_09.blend` the textures are 'not found' (LK_TEXTURED@blend FAIL in the proof pass, PROOF.md rounds 1 and 2).
hole08_build / hole10_build already save with `relative_remap=False`; hole09_build does now (a lib fix in `P.save` would serve every hole: not mine to edit).

### 18. The props library's new shrub meshes cost +3.9k triangles on the same placement

`postcard_props_lib` (sha 971cce75.. -> 6cdc5c6d..): PLANT_SHRUB_C 392 -> 472 triangles, SHRUB_A 400 -> 320, SHRUB_B 480 -> 320. The same hole 9 build went 244,825 -> 248,693 triangles (limit 250,000) before any round-3 change; the masonry (+5k) was paid with `N_SHRUB_RIDGE` 132 -> 116 and `N_TUFT_OUT` 64 -> 56.

## v2 2026-10-05 GRASS + SWAY pass (hole 9 repair round 0): library / verifier behaviours found while adding the fringe

### 19. `PL.tuftify_shrubs` / `PL.tuftify_crowns` cannot pass the plant gates (hole 9 does not call them)

The tufts stand ON the shrub lumps (origin 0.7-0.9 m above the ground) / on a sea-stack crown (a WATER lie under the base, blades overhanging the rim). Measured on the first full build (`r8/gates_g1/`): `postcard_look_verify` NO_PLANT_ON_WATER@blend + @fbx FAIL (`15-42 of 915 plants fail ... no ground or rock under it`: the lowest blade needs ground or a ROCK_ / DRESS_RUIN / ARCH / BLOCK top
within 0.5 m under it; a shrub is not a support), and the hole's own `H_NO_PLANT_ON_WATER` FAIL (`base on water 27`, `worst |origin z - ground| 0.905 m` against the 0.06 m a plant may sink / float). The libraries' own smoke gates (CROWN_TUFTS_08, SHRUB_TUFTS_08_09_10) do not run the verifier. Neither gate was touched; hole 9 puts a ground-rooted tuft SKIRT round the bushes near the ruin instead
(`hole09_look.build_grass`). If the lib owner wants tufts on shrubs, NO_PLANT_ON_WATER needs a rule for `lk_shrub_tuft` (support = the shrub, which itself stands on the ground).

### 20. `scatter_fringe` default `lip_margin_m` is 0.9 m, the hole gate wants 1.0 m

The first fringe tufts stood 0.91 m from the shore (`H_NO_PLANT_ON_WATER: within 1.0 m of the shore 5 (nearest 0.91 m)`). The hole script passes `lip_margin_m=1.1`. (The library's own GRASS_NOT_ON_WATER gate accepts 0.8 m.)

### 21. `scatter_fringe` cluster ids (`lk_fringe`) restart at 0 on every call

Several calls (zones) put several tufts with the same `lk_fringe` id in the scene, so a clump statistic over the whole scene merges them (30 'clumps' of up to 30 tufts in the first gate run). The hole script tags every fringe tuft with `h9_zone`; `tools/grass_gates.py` groups by (zone, id).

### 22. `build_cliff_skin(step_m=...)` has no effect on Split

`_loop_columns` spaces columns at <= step_m along each outline EDGE, but every TERRAIN outline edge on this hole is shorter than 2.4 m: `SKIN_STEP_M` 2.4 -> 2.7 gave exactly the same 60,720 skin triangles. The skin density is the TERRAIN outline's, not a hole script knob (the strata columns only get denser with a smaller step).

### 23. `PL.scatter_fringe` budget vs coverage on a ribbon island

One call over the whole island (2 km of cliff lip + 2 x 450 m of ribbon) spreads 24k triangles at 1 tuft / 5 m: 19 % edge coverage, mostly where no camera looks. The hole script calls it per ZONE (`region=` bbox, `focus=` the camera's look point) and a thin far-field call: tee view 40 %, green end 23 % coverage of the 2 m-grid edge strips. The camera sees the rough edge of a 41-45 yd ribbon only from ~35 m ahead of the ball (the fairway + 3 yd collar fill the frame sides before that),
so a tee-zone fringe that starts nearer is wasted triangles.
