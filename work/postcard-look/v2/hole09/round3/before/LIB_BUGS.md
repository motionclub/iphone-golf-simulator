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
