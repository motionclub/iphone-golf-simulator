# Hole 10: library findings (workarounds are inside `blender/scripts/hole10_build.py`; no library file was edited)

Findings 1-3 were found while building hole 10 on 2026-10-04 (round 1), 4-5 in round 2, 6-8 in round 3, with the libs as they stood (sha256 in `logs/libs_sha_before.txt`; unchanged between the three rounds).

## 1. `place()` / `clamp_scale()` clamp AT the 0.5 limit, and the FBX float round trip turns that into 0.49999997 (NO_ROCK_STRETCH_2X@fbx FAIL)

* Where: `postcard_props_lib.py` `SCALE_LIMITS = dict(lo=0.5, hi=2.0, ...)`, `place(..., clamp=True)`, `fit_plan`, `swap_legacy_rocks`; the gate is `postcard_look_verify.py` `NO_ROCK_STRETCH_2X` (`outside 0.5..2.0`, no tolerance).
* Repro (first scratch build of this hole, ring towers floored at `max(0.5, h / nat_h)`): `PL.place(D, "ROCK_BASALT_A", (x, y, 0), 0.0, 0.5)` then `L.export_look_fbx(D)`;
  `postcard_look_verify.py -- 10 --blend X.blend --fbx X.fbx` prints `NO_ROCK_STRETCH_2X@blend PASS` and `NO_ROCK_STRETCH_2X@fbx FAIL - 4 of 286 instances stretched past 2x: ROCK_BASALT_A.003: scale (0.50,0.50,0.54) outside 0.5..2.0`.
  Cause, measured by `tools/fbx_scale_probe.py` on that FBX: the re-imported object scale is `0.4999999701976776` (float32 of 0.5 minus one ulp).
* Effect: any library instance the lib clamps to its own lower limit (or placed at exactly 0.5) passes in Blender and fails after the FBX stage.
* Workaround (done): hole 10 never places below `MIN_SCALE` 0.58 x a +-5 % jitter (smallest measured instance scale 0.5514, `H_NO_STRETCH_2X` both stages).
* Suggested fix (owner of the lib / gate): clamp to `lo + 1e-3` (or give the gate a 1e-3 tolerance).

## 2. `build_cliff_skin(style="basalt")` default `piece_m=140` breaks the Unity rule ROCK_NEAR_LAVA_CHUNKED (RUNTIME.md v2.2)

* Where: `postcard_look_lib.py` `build_cliff_skin(..., piece_m=140.0, ...)`; the rule is `PostcardImportCheck.RockChunking`: every `ROCK_` renderer within 25 yd of a LAVA_LIGHT must be <= 24 yd across.
* Repro: `tools/build_variant.py` with `SKIN_PIECE_M = 140.0` (the library default) -> `tools/stage_gates.py` prints
  `H_ROCK_CHUNKING@blend FAIL - 20 ROCK_ pieces within 25 yd of a lava light, widest 154.7 yd across ... ROCK_SKIN_03 154.7, ROCK_SKIN_01 133.8, ROCK_SKIN_04 106.1`.
  `postcard_look_smoke.py` hole 10 and the LIB_GROUND.md crater recipe both use the default.
* Workaround (done): `piece_m=15.0` on both crater calls: widest ROCK_ piece near a light 19.9 yd across (limit 24); the skin is 130 ROCK_SKIN pieces (96 on the rim loop, 34 on the pillar loop).
* Suggested fix: default `piece_m=15` for `style="basalt"` (the strata default can stay 140), or a note in the LIB_GROUND.md crater recipe.

## 3. `build_lava` default light placement does not reach the tee-side rim (documentation, not a defect)

* `build_lava(lights=4)` farthest-point-samples inside `ellipse + 45 m`, so every light ends up round the lava ellipse and the pillar; the long rim wall from the tee to B gets none.
  Hole 10 passes explicit `light_points` (3 along the rim shoulder at crater angles 148 / 128 / 113 deg, 130 / 126 / 118 m from the crater centre, 2 round the pillar), all 2.3 m over the lava,
  nearest pair 35.9 yd (>= 8), `H_LAVA_LIGHTS` / `CRATER_LAVA_LIGHTS` PASS. Nothing to fix; a hole that wants the glow on the tee-side wall has to say where.

## 4. Library basalt box UV is one continuous lattice: the same Basalt_E dash pattern on every column of every piece ('windows and ladders', review rounds 1 and 2)

* Where: `postcard_props_lib.py` `_finalize(..., "box")` / `box_uv_expected` (object-space box projection, one tile per 8 m / uv_scale) used by every `build_basalt_cluster` / `build_basalt_wall` kind; `postcard_look_lib.py` `_basalt_loop` (u = arc / tile, v = z / tile, continuous along the loop); `build_background_cone`.
* Effect: the glow mask (regular dashes ~0.7 m apart, 12 per tile) continues unbroken across the 3-6 m wide neighbouring columns, so a wall of columns shows rows of equally spaced dashes up every face. At 250-300 m that is a window lattice. Round 2's answer (random per-column UV SHIFTS) only turned the lattice into scattered dashes: still 0.84 m dashes at 2.6 % of the texels.
* Workaround (round 3, hole script only): `hole10_look.author_uv` rewrites UV0 of every mesh the hole uses (library wall / stack variants cloned per UV window set, the unique `ROCK_CRUST_nn`, the lib's `ROCK_SKIN_*` pieces after `build_cliff_skin`, the cone's own UV): each side face is mapped to ONE slice of the tile, a slice that starts on a glow line (the joint) or one of the 8 glow-free zones of Basalt_E (zone table measured by `r3/basalt_e_profile.py`), tops always glow-free, a low v density. Texture-sampled result (`H_GLOW_JOINTS`): glow texels 0.88 % of the side faces (box UV 2.61 %), 0.01 % of the tops, 3.2 m dashes.
  NOT covered: the 30 `ROCK_BOULDER/BLOCK/SLAB/CAIRN_*_BASALT` rubble rocks at the cliff foot (lib meshes shared with other holes, left alone).
* Suggested fix (lib): `_finalize`/`_basalt_loop` could take the glow-free zones and glow lines from one table (as `author_uv` does), or Basalt_E could be made non-periodic along v.

## 5. `ROCK_NOT_ICOSAHEDRON` needs >= 100 faces (SHAPE_TH min_faces) and `build_basalt_wall` hard-caps at 26 columns (documentation)

* A basalt cluster with big hex columns (col_r 3.4 over a 12 x 10 m ellipse) has only 79 faces and fails `ROCK_NOT_ICOSAHEDRON@blend/@fbx` ("79 faces < 100"), although it is plainly a column plateau. `LOOK_CONTRACT.md` says '>= 60 verts'; the verifier's second floor (100 faces) is not in the contract. Hole 10 sizes its mesa kinds to >= 131 faces (col_r 2.2-3.3).
* `build_basalt_wall(..., max_tris=500)` keeps at most 26 columns (`int(500 / 18.6)`), so a segment longer than ~40 m x 12 m gets chunky columns (2.6 m radius for A); the second cap (`max_faces / 8.4` = 59) is never the binding one. Hole 10 registers its own wall kinds with the same function (N1-N3, F1-F3) instead of scaling the lib's A / B / C up.

## 6. `ROCK_NOT_ICOSAHEDRON` reads a chunk of regular hex plates as a "regular tessellation of a round solid" (documentation)

* A `ROCK_CRUST_nn` chunk of 20-50 identical 4.3 m hex plates (tilt <= 0.07 rad, a few chips) measures edge cv 0.28, area cv 0.30, radius cv 0.23 and fails `ROCK_NOT_ICOSAHEDRON@blend/@fbx` (the test fails only when all three are under 0.30 / 0.45 / 0.25), although it is plainly a plate field.
  Repro: `crust_field` with `chip_p=0.18` and no stumps. Chips alone were not enough (`chip_p=0.55`: edge cv 0.28-0.30, area cv 0.35-0.37, radius cv 0.22-0.24, 6 of 42 chunks still failed). Workaround (done): `chip_p=0.7` and small basalt stumps (r 0.9-1.5 m, 0.6-1.4 m high) standing on one plate in five (their small faces raise the area / edge variation): all chunks pass at blend and FBX.
* Same family as finding 5: the verifier's shape test is written for single rocks; a hole that wants a continuous floor of plates has to break the regularity on purpose.

## 7. `PROP_FACE_BUDGET` applies to every non-skin `ROCK_` mesh, crust included (documentation)

* The contract says "props <= 500 faces"; the verifier also applies it to a hole's own unique `ROCK_*` meshes: a first crust chunk of 506 faces failed `PROP_FACE_BUDGET@blend/@fbx`. `crust_field` now splits any chunk over 480 faces at its median. The lights rule (<= 24 yd across within 25 yd of a lava light) and the 100-face floor of finding 5 bracket the size from the other side: a chunk of 100-480 faces is 25-45 m across with 4.3 m plates, so the crust keeps 25 yd off every light instead of chunking down to the light.

## 8. `build_cliff_skin(style="basalt")` can leave a tail piece under 60 welded vertices (documentation)

* With `basalt_width_m=(1.4, 2.4), disp_m=(0.05, 0.4)` the last piece of a loop came out as `ROCK_SKIN_96` with 48 welded vertices. The verifier exempts `ROCK_SKIN_*` from the rock-shape gates (cladding), but the brief says no rock under 60 welded vertices and the hole's own gate counts them: the build joins any skin piece under 70 vertices into its nearest neighbour (`merge_tiny_skins`, one piece joined; the joined piece stays under 24 yd across). A lib fix would fold the tail into the previous piece when it is shorter than a few columns.

## Not a lib bug but worth knowing

* `postcard_look_verify.py` `LOOK_FILES@blend/@fbx` FAILS on every hole today: `Fairway_C.png` (1 % of its 64 px windows reach luminance sd 0.03) and `Green_C.png` (0 %). The texture owner / the lead
  decides between adding blade-scale detail and lowering the floor; no hole script can change it.

# v2 2026-10-05 repair round 2 (hole 10 repair agent): library findings, no lib file edited

1. **`postcard_look_lib.assign_uvs`, centerline mode is per VERTEX.** Every vertex gets the UV of its nearest point of the smoothed centerline; a long thin triangle between a curved outline and the chord of two far-apart outline vertices (hole 10 FAIRWAY_FIRSTCUT: 2.8 m wide, 36-52 m long, three of them, 103 m2) therefore has three vertex UVs on one line in UV space
   (all at lateral 8-10 m) and a Jacobian of 26:1 / 4.7:1 / collapsed: the texture is smeared into streaks at any filtering level. The verifier's new `GROUND_UV_LOCAL_SMEAR` finds it. Worked around in the hole script (`hole10_look.unfold_sliver_uv`: one similarity per cluster of slivers, geometry untouched). A library fix would do the same inside `assign_uvs`
   for every centerline-mode mesh (holes 8 and 9 have no such triangle today: 1.3:1 max on every FAIRWAY / FIRSTCUT / GREEN / APRON / TEE_BOX / BUNKER mesh, so no change was needed there).
2. **`build_path` clips a vertex to the LOWEST ground in the 3 x 3 cells round it** (z_off 11.5 mm over that), so a kerb vertex within about 0.15 m of a 10 cm step dips under the higher side: keep a path 0.2 m + half its width x 1.25 off a riser (the tee kerb's centre line is inset 1.05 m, outer edge >= 0.33 m). Documented in the docstring; noted here because the pad edge is the first user.
3. **Unchanged, still open from round 1:** `scatter(scale_range=(1.5, 2.0))` draws agave up to 2.0 (max 1.9990 here); a seed that draws 2.0001 would fail the stage gate H_NO_STRETCH_2X: use a `scale_range` upper bound of 1.9 in the hole script if the seed ever changes.

## 9. (round 3, 2026-10-05) a flush LK_BASALT ribbon on a play surface is judged a ROCK by material: no dark overlay can exist under the current verifier

* Where: `postcard_look_verify.py` `rock_candidates()` (>= 50 % of a mesh's area on `ROCK_MATS` = LK_ROCK / LK_ROCK_WET / LK_BASALT / LK_CLIFF / LK_CLIFF_DARK makes it a rock whatever its name, `ROCK_MAT_SHARE` 0.5), `OVERLAY_OK = ("DRESS_PATH", "DRESS_SAND")`, `PROP_RULES` (`DRESS_PATH` = LK_PATH >= 60 %).
* Repro: `blender/scripts/hole10_build.py -- --out DIR --no-render --rim basalt` (a 1.15 cm ribbon DRESS_PADRIM_nn, LK_BASALT, on the TEE_BOX lip), then `postcard_look_verify.py -- 10 --blend DIR/hole_10.blend --fbx DIR/hole_10.fbx`: `ROCK_NOT_ICOSAHEDRON@blend / @fbx FAIL - DRESS_PADRIM_01: 244 welded verts / 180 faces: 3 planar facet orientations < 6; box (90 % ...); 30 % of the polygon edges are open` and
  `NO_ROCK_STRETCH_2X@blend / @fbx FAIL - ... baked flat / long (PCA extent ratio r3 0.01 < 0.15)`; every other line passes (`stage_rim_variant/`, `repair_r3/variant_basalt_logs/`).
* Effect: crater.jpg's pad (a grass square on black rock) cannot be dressed with a flush basalt edge; the only overlays allowed on a play surface are the tan LK_PATH stone and sand, and no dark non-rock LK_ material exists (Basalt / CliffDark are both rock materials).
* Workaround (done): the pad edge is a dark-green LK_PLANTS-atlas ribbon (G_DEEP / G_DARK), width capped by ONE_GREEN's DRESS_ lawn budget (< 20 m2 flat grass-material top).
* Suggested fix (owner of the gate): skip rock classification for meshes whose highest point is <= 3 cm over the ground (the limit PROPS_OFF_PLAY already uses for "standing on"), or admit a named flush overlay (`DRESS_PADRIM`) in `OVERLAY_OK` / `PROP_RULES`. Then `stage_rim_variant/` installs as it is.
