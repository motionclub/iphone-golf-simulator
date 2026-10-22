# v2 2026-10-05 00:34 repair round 2 (hole 10 repair agent; staged, NOT installed)

Inputs: the libs fixers' round 2 (pillar prism relief in `postcard_look_lib._basalt_loop`, new Basalt / Lava / Smoke PNGs, `golf_look_textures.py`, `postcard_look_verify.py` with the new `GROUND_UV_LOCAL_SMEAR`; lists `libs_sha_repair_r1.txt` -> `libs_sha_repair_r2.txt`), and the two low review findings
(tee pad edge / tee smoke / dark patch; PROTECTED_FILES). Rebuild `run_all.sh` (2 min). The first rebuild on the new libs (`stage_before_repair_r2/`, the negative control of the new gates) built 21 / 21 and verified 97 / 99: the only failing line was `GROUND_UV_LOCAL_SMEAR` (FAIRWAY_FIRSTCUT, 103 m2): a hole-script item.
Full tables, shas and install commands: `INSTALL.md` ("Repair round 2"). Snapshot of every script / tool of the round with sha256: `scripts_repair_r2/`; working files, probes, before / after renders, smoke trials: `repair_r2/`. `hole10_design.py` byte-identical, scoring meshes bit-identical (H_PLAY_UNCHANGED), no lib / texture / Unity / protected file touched, no Unity run.

## What changed (my files: `blender/scripts/hole10_build.py`, `hole10_look.py`, the tools of this folder)
1. **FAIRWAY_FIRSTCUT UV slivers** (build step 4d, `hole10_look.unfold_sliver_uv`). Cause (measured with `repair_r2/uv_bad.py`, `tri_probe.py`): three triangles of the first cut are 2.8 m wide and 36-52 m long (the strip's outline vertices are 36-52 m apart on the bend at course x 80-100 yd), and
   `assign_uvs` gives each VERTEX the centerline UV of its nearest centerline point, so the three vertices of such a sliver sit at lateral 8-10 m and form a line in UV space: ratio 26:1 / 4.7:1 / collapsed, 103 m2 (the streak band at the right edge of the first cut, hard horizontal streaks in the lava-rim still). The centerline map is a proper rotation, so the repair is a similarity
   per connected cluster of slivers (`w = a z + b` in complex numbers, weighted least squares, weight 4 on vertices a normal triangle shares): ratio 1.000, continuity inside the cluster. A first version unfolded the slivers one from another (BFS from a neighbour) and moved a tip vertex by 10.3 m; the cluster fit moves none by more than 2.53 m (`repair_r2/jump_probe.py`). 2 clusters, 3 triangles, geometry untouched.
   The 2.0-2.2:1 slivers (80.7, 67.5, 58.1, 30.3, 29.9 m2 ...) are left as they are: continuous per-vertex UVs, far under the verifier's 4:1.
2. **Tee kerb** (build step 4e, `hole10_look.tee_kerb_polyline` + the library `build_path`): see INSTALL.md. Why a kerb and not a different grass: LK_GREEN on the pad was the round-4 build's choice and produced the review's hard seam (the grass changes scale / phase / stripes at row 590); a DELIBERATE edge from a different material is what a pad edge is, and the library's overlay is allowed on play surfaces and
   gated (PATH_UNDER_BALL, PROPS_OFF_PLAY). The seam metric (`tools/seam_metric.py`) now leaves the kerb's own rows out (`--exclude-json logs/tee_edge.json`, rows 600-659) and still judges every other row (1040 rows, worst 1.43 x its neighbourhood, limit unchanged 1.6); H_TEE_EDGE_VISIBLE measures that the kerb is a band across the tee frame.
   Limits, said plainly: LK_PATH is the library's pale stone (Path_C.png, cream flagstones with moss joints), not the black rock of crater.jpg's platform; the verifier allows only LK_PATH on a DRESS_PATH (>= 60 % of its area), so a dark kerb needs a texture decision (a new LK_ material), not a hole-script change. The Game view is not measured.
3. **Tee smoke** (build step 5, fifth `smoke_group`): see INSTALL.md. The cards of `smoke_group(..., n=2, spread=0.30)` are 70 x 110 m at 390 m; the soft Smoke_C wisp covers about 25 % of a card's width and 55 % of its height, so the two wisps are about 20 m wide and 60 m tall each (3 degrees x 8 degrees in the tee frame).
   Not measured: the Unity smoke shader (the preview material is a stand-in). The approach frame's smoke in the stand-in render is a bright blob because the stand-in is unlit and white-ish; the real shader tints / softens it (not changed here).
4. **Dark patch** unchanged (round-1 identification stands).

## Gate table of this round (`GATES_hole10.txt`)
| gate | result | numbers |
|---|---|---|
| build gates (hole10_build.py) | 23 / 23 PASS | new H_GROUND_UV_SLIVERS (0.00 m2 above 4:1 on the hole-authored meshes, 3 slivers fixed, residual 2.53 m), H_TEE_KERB (>= 0.33 m inside the pad, >= 1.26 m from the markers, 1.15 cm high); H_NO_PLANT_ON_WATER 210 plants, 0 on water |
| postcard_look_verify blend + FBX | 99 gates, 0 failed, ALL PASS | GROUND_UV_LOCAL_SMEAR PASS (5.2 m2 max, TERRAIN wall UV), PATH_UNDER_BALL PASS (1.17 cm, ball hidden 0.0 %), PROPS_OFF_PLAY PASS, CRATER_TEE_PAD PASS, SMOKE_IN_FRAME tee 2.69 / approach 2.47 / lava rim 3.74 % (limit 1.5), CRATER_WALL_COVERED PASS (0.0 %), NO_ROCK_STRETCH_2X PASS, NO_PLANT_ON_WATER PASS, NO_FOAM_STRIP PASS |
| stage gates blend + FBX | 40 / 40 PASS | new H_GROUND_UV_SLIVERS, H_TEE_KERB; H_NO_STRETCH_2X max scale 1.9990 (limit 2.0: the agave scatter draws up to 2.0 in `scale_range`; unchanged, see the round-1 note) |
| H_TEE_EDGE_VISIBLE | PASS | kerb 3.1 % of the tee frame, full width on 44 consecutive rows (>= 30); control without kerb FAILS |
| ground-UV control | FAIL as it must | the stage before the repair: 103.1 m2 above 4:1, worst 1000:1 |
| H_TEE_SEAM_PREVIEW | PASS (preview) | worst grass row 1.43 x its +-40-row median (limit 1.6), kerb rows excluded |
| H_PLAY_UNCHANGED / scoring | PASS | 2,956 vertices, 3,807 polygons identical to `baseline/blender/hole_10.blend`; `postcard_check` ALL PASS; `postcard_verify` 26 / 29 (3 old-allow-list lines fail by design); `emit_cs --check` no drift; guards 7 / 7 |
| H_REPRODUCIBLE | PASS | geometry hash `fb1019f702d15e25` twice |
| budget | PASS | 225,937 triangles (250k), FBX 3.75 MB (20) |
| not measurable here | UNMEASURED | the 6 `U_*` lines (Game-view proof shots, albedo / normal, grass hue, lava, basalt / smoke, PostcardImportCheck on the installed hole) and PROTECTED_FILES (other chats' files, none written by this job) |

# v2 2026-10-04 22:11 repair round 1 (hole 10 repair agent; staged, NOT installed)

Inputs: the shared fixers had changed `postcard_look_lib.py`, `postcard_props_lib.py`, `postcard_look_verify.py`, `golf_look_textures.py` and 14 Look PNGs after the round-4 stage (sha lists: `libs_sha_repair_r1_before.txt` -> `libs_sha_repair_r1.txt`); the review findings of the Game-view stills
(hole10_1_tee seam, dark patch). Rebuild: `run_all.sh` (this folder, 60 s), snapshot of every script and tool of this round with sha256 in `scripts_repair_r1/`; the round-4 stage is kept as `stage_before_repair_r1/`, its gate table as `GATES_hole10_before_repair_r1.txt`.
Files I own and changed: `blender/scripts/hole10_build.py`, `blender/scripts/hole10_look.py` (+ `smoke_group`, `PROFILE128`), `tools/stage_gates.py` (+ H_TEE_CONTINUOUS), `tools/seam_metric.py` (new), `tools/summarize.py`, `tools/run_all.sh`, `run_all.sh` (new wrapper); `hole10_design.py` (SCENERY included) is byte-identical,
`postcard_emit_cs.py --check`: HOLE_CS_MATCHES_DESIGN PASS, `guards.sh` 7 / 7. No lib, texture, Unity, tennis, shader, QualitySettings, Serve or hole 7 file was touched; no Unity run (instruction); hole 10 scoring meshes are bit-identical to `baseline/blender/hole_10.blend` (H_PLAY_UNCHANGED, PLAY_SURFACE_NAMES/GRID/TOPS/FACES/WALLS, MARKERS_FROZEN at blend and FBX).

## Gate table of this round (`GATES_hole10.txt`)
| gate | result | numbers |
|---|---|---|
| build gates (hole10_build.py) | 21 / 21 PASS | incl. H_UV_WINDOWS (zone glow 0.0000 %, narrowest edge window 9.3 % glow, Basalt_C profile deviation <= 0.01 after the re-bake; was 0.0228), H_NO_PLANT_ON_WATER (210 plants, 0 on water, nearest to a lava edge 1.00 m), LIB_* (wall covered, skin outward, no foam strip, thin shelf n/a) |
| postcard_look_verify, blend | 50 / 51 | only FAIL: SMOKE_VISIBLE_STILLS (no `smoke` block in the old `stills_stats.json`: Unity re-shoot after the install) |
| postcard_look_verify, FBX re-import | 51 / 52 | same single line |
| SMOKE_IN_FRAME (blend + FBX) | PASS | tee 3.03 %, approach 4.01 %, lava rim 4.67 % of the frame at effective alpha >= .30 unoccluded (limit 1.5 %; round 4: 0.47 / 0.01 / 0.00 %) |
| stage gates (blend + FBX) | 36 / 36 PASS | new H_TEE_CONTINUOUS (0.0000 tile max UV difference; controls FAIL as they must) |
| H_TEE_SEAM_PREVIEW | PASS (preview) | worst ground row 1.43 x its +-40-row neighbourhood (limit 1.6); round-4 build 1.98 at row 590, Game-view still 2.90 |
| H_PLAY_UNCHANGED / scoring | PASS | 10 ground meshes 2,956 vertices, max delta 0.00 m; `postcard_check`, `postcard_verify` (26 / 29: the 3 old-allow-list lines fail by design as before), `emit_cs --check` no drift |
| H_REPRODUCIBLE | PASS | two builds, geometry hash `3e191bb53f4f0045` |
| landmark rays | 3 / 3 PASS | cameras unchanged |
| budget | PASS | 220,409 triangles (250k), FBX 3.62 MB (20) |
| not measurable here | UNMEASURED | `U_*` lines (Game-view proof shots, albedo / normal, grass hue, lava, basalt, smoke softness in Unity, PostcardImportCheck on the installed hole) and SMOKE_VISIBLE_STILLS |

## 1. The tee seam (review, medium) and why the fix is a UV, not a texture
Measured first: on the review's Game-view still the row step at row 590 is 21.9 against 7 around it (the review's mean-RGB formula gives 16.4 vs 5.5); the same row on the Blender preview of the round-4 stage (same camera, `repair_r1/pv_old/`) steps 20.4 against ~11, and the crop shows the pad
(smoother, no stripes) against the striped fairway. Ray casts (`repair_r1/pixel_probe.py`): rows 580-700 hit `TEE_BOX` LK_GREEN, row 590 is the far edge of the pad (course (1.1, 5.1) yd), everything beyond is `FAIRWAY` LK_FAIRWAY. `TEE_BOX` is z 6.24, `FAIRWAY` 6.14: a 10 cm raised pad.
Two causes: (1) different material + UV function (`assign_uvs`: LK_GREEN planar 6 m tile, LK_FAIRWAY centerline 10 m tile with the stripes), (2) the pad's lip hides about 0.4 m of fairway behind it for the address camera (eye 2.21 m over the pad, lip 8.9 m away: 8.9 x 0.10 / 2.21), so even identical UVs jump by 0.4 m of texture at the lip.
Fix in `hole10_build.py` 4b / 4c: `TEE_BOX` keeps its outline and height (no vertex moves) and takes LK_FAIRWAY; after `assign_uvs` its UVs are re-evaluated with the library's own `CenterlineParam` at p + (p - eye) x dz / h, i.e. exactly the texel the camera sees past the lip. Result: `repair_r1/sheet_tee_seam.png` (Game-view still, round-4 preview, new preview): no visible seam; row 590 steps 10.8 against 12-13 around it (was 20.4 / ~11);
H_TEE_CONTINUOUS (UV of all 162 loops vs the FAIRWAY's UV at the parallax point: 0.0000 tile) with two negative controls that fail (the round-4 stage: 0.49 tile and LK_GREEN; a constant 0.04 shift: 0.046 tile).
Limits, said plainly: (a) the Game view is not measured (the numbers above are Blender previews; Unity re-shoot needed); (b) the pad is now the same grass as the fairway, so from the tee camera it no longer reads as a separate square pad: the pad is visible as the 10 cm riser line from the back / sides / aerials (`repair_r1/pv0/hole10_teepad_*.png`), and CRATER_TEE_PAD (square, LK_GREEN or LK_FAIRWAY) passes. I did not add a coloured collar or kerb because every
candidate either fails `PROPS_OFF_PLAY` (a prop over the fairway / pad) or re-creates the seam as a deliberate texture change; the other way to get a visible far edge is a change of the pad's height, which the scoring freeze forbids; (c) the 40 cm phase shift of the pad texture is exact for the address camera only (the ball always starts at (0, 0)); seen from elsewhere it is a 40 cm offset of a 10 m tile.

## 2. The dark patch at the right of the tee frame (review, low)
Pixels x 840-899, y 286-310 of `hole10_tee` traced through the tee camera: a 6 x 7 grid of 42 rays: 21 hit TERRAIN_CRATER LK_ROUGH, 8 ROCK_SKIN_70 / _71 (LK_BASALT cladding at z 5.84-5.88), 1 TERRAIN_CRATER LK_BASALT (the lip band at z 5.96), the other 12 PLANT_AGAVE_B.010 / .012, PLANT_AGAVE_A.004 and a tuft in front. World position: course (36-46, 64-80) yd = the crater-side shore bend 75 yd from the tee, seen over the
shelf edge at the extreme right of the 36 degree frame (azimuth 29-30 degrees; the frame edge is 30.2). It is the real cliff drop (dark basalt cladding + lava glow joints, with the crater floor behind), not a bunker (bunker 1, (57.4, 110.3) yd, would be a sliver of about 3 px at that range and a 1.1 degree depression angle), not a hazard object and not a lava puddle. Nothing was changed: any rock added at the lip would be about 8 px at 80 m.

## 3. Smoke (new verifier gate SMOKE_IN_FRAME)
Arithmetic that fixed the design (`repair_r1/smoke_sets.py` = the verifier's own `smoke_frame_alpha` on candidate sets, one Blender session): Smoke_C peaks at alpha .498, GolfLook's AlphaGain 1.35 gives .67, EdgeFade .18 multiplies the border; only **11 %** of a card's area has an effective alpha >= .30 (17 % of a 4-card stack),
so a plume that covers 1.5 % of a 900 x 1600 frame needs 9-14 % of the frame as card area. The tee frame only reaches 8.2 degrees above the horizon (horizon at row 246; sky band rows 0-150, wall rows 150-250), so the tee plume has to be big and low behind the wall window. Final: 4 groups x 3 cards (`hole10_look.smoke_group`, mirrored U on every second card),
tee plume (20, 300, 0) m 120 x 100 m facing the tee camera, approach plume (305, 118, 0) 80 x 70 in front of the east wall right of the flag, lava-rim plume (300, 330, 30) 130 x 110 over the north-east wall, one off the volcano summit (150, 435, 95) 110 x 120; every card beyond the rim circle (CRATER_CONE_SMOKE), LK_SMOKE only, `DRESS_SMOKE_nn` names.
Overlays of the verifier's alpha grid on the Blender previews: `repair_r1/sheet_smoke_frames.png` (the previews do not draw the Unity smoke shader: shapes only). Not measured: the Game view (SMOKE_VISIBLE_STILLS reads the Unity stats; the frame it measures counts a luminance change of >= 10 levels, which a pale plume against the bright dusk sky may reach less easily than the gate's alpha test).

## 4. H_UV_WINDOWS (texture change)
Basalt_C / Basalt_E were rewritten at 21:41 (v6). Re-measured with `r3/basalt_zones_v5.py` / `basalt_profile128_v5.py`: glow cores unchanged (0.123 / 0.446 / 0.534 / 0.718 / 0.806 / 0.930), glow-free zones unchanged ((0.009, 0.061), (0.165, 0.385), (0.576, 0.685), (0.772, 0.796), (0.854, 0.893)), only the Basalt_C luminance profile moved (max 0.023): `PROFILE128` re-baked, the build's own texture-measure guard passes (0.0005).

## Findings that are not mine, for the integrator
* `SMOKE_VISIBLE_STILLS` stays FAIL until `ArtDir/screenshots/golf_postcards/look/stills_stats.json` has a `smoke` block (the stills tool of repair round 1 writes it): re-shoot after the install.
* `H_NO_STRETCH_2X` (my stage gate) counts PLANT_ instances: the agave scatter draws scales up to 2.0 (max 1.9990 in this build, limit 2.0); the verifier's NO_ROCK_STRETCH_2X reports a largest rock-scale component of 1.92. A different seed could put a plant at 2.0001: lib / scatter `scale_range`, not changed here.
* The Blender preview of LK_SMOKE is a stand-in: judge the plumes in the Game view.


# v2 2026-10-04 20:37 round 4: rebuilt on the final textures (rebuild-only step)

`tools/run_all.sh` re-run on the v5 Look PNGs and the new `postcard_look_verify.py`: **49/49 (blend) and 50/50 (FBX re-import) look-verify lines PASS** (round 3 failed LOOK_FILES), 34/34 stage gates, 21/21 build gates, 3/3 landmark rays, H_REPRODUCIBLE, guards 7/7.
The only script change: the UV windows of `hole10_look.py` were re-measured for the v5 Basalt_E (same six joint cores, but fork cracks closed 6 of the 8 old glow-free zones): `ZONES` (5 strictly glow-free zones), `PROFILE128` (Basalt_C luminance, window position drawn dark-weighted),
and the build's `H_UV_WINDOWS` re-measures them from the PNGs on disk. Texture-sampled glow (`H_GLOW_JOINTS`): tops 0.01 %, sides 0.91 %, 18 % of the side area lit (before the re-measure, on stale constants: 0.22 % / 1.28 % / 46 %). `hole10_design.py` and the scoring meshes are unchanged (H_PLAY_UNCHANGED, `emit_cs --check`).
New staged shas and the install commands: `INSTALL.md` ("Round 4"). Tools of this round: `r3/basalt_zones_v5.py`, `r3/zone_stale_v5.py`, `r3/basalt_profile128_v5.py`, `r3/basalt_c_profile_v5.py`. Experiment build: `iter/r4a`. Still FAIL in `GATES_hole10.txt`: `PROTECTED_FILES` (31 tennis / MatchHeroes / Customization / QualitySettings files of OTHER sessions differ from the start-of-job hashes) and the 5 Unity-only `U_*` lines (unmeasured).

# Hole 10 Crater: POSTCARD_LOOK continue pass, round 3 (staged, not installed)

Round 1 staged 14:42, round 2 15:29 (skeptic verdict FAIL, high + 3 medium + 2 low findings), this is round 3 (staged 16:14 EDT, 2026-10-04). Blender 5.2 headless only (no Unity, no Blender MCP, no git writes).
Blender renders are previews, NOT Game-view proof.

| file | what |
|---|---|
| `stage/hole_10.blend`, `stage/hole_10.fbx` | the staged build (FBX written by `postcard_look_lib.export_look_fbx`); `stage/hole_10.fbx.meta` is a throw-away with a fresh GUID: never install it |
| `stage_repro/` | the second build into another `--out` folder (reproducibility gate) |
| `round1/`, `round2/` | the round-1 and round-2 staged blends (`hole_10_round1.blend`, `hole_10_round2.blend` + its FBX and the two scripts as they were), their preview renders (`pv/`) and mask shares (`mask/`): the baselines of the comparisons |
| `INSTALL.md` | exact install / verify / rollback commands + sha256 of the staged files |
| `GATES_hole10.txt`, `gates_hole10.json` | the consolidated `GATE: <ID> PASS|FAIL - <numbers>` lines (written by `tools/summarize.py` from the logs) |
| `logs/` | raw logs: build, repro build, `postcard_look_verify` (blend + FBX), `postcard_verify`, `postcard_check`, `emit_cs --check`, stage gates, play-unchanged, landmark rays, open-lava gate, guards, lib sha256 before / after |
| `landmarks.json` | the proof cameras for `PostcardLookStills` (tee, approach, lava rim); `landmarks_with_aerial.json` adds the preview-only cameras (4 aerials, 2 wall close-ups, cone, rim variants, a plan view) |
| `previews/`, `sheet_*.jpg` | Blender EEVEE previews: tee / approach / lava rim at the Game-view camera rigs (900x1600), 4 aerials, 2 wall close-ups, the volcano, a mask plan view; contact sheets: `sheet_round1_2_3.jpg` (the three rounds, same cameras), `sheet_features.jpg` (what the round-3 findings asked for, close up), `sheet_aerial_vs_still.jpg` (crater.jpg beside two aerials), `sheet_phone_before_after.jpg`, `sheet_aerials.jpg`, `sheet_plan.jpg`, `sheet_overview.jpg` |
| `LIB_BUGS.md` | library findings (no lib file edited) |
| `tools/` | `run_all.sh` (the whole gated run, about 50 s), `summarize.py`, `stage_gates.py` (now with the texture-sampling H_GLOW_JOINTS, H_CRUST, H_CONE_GLOW), `play_unchanged.py`, `landmark_check.py`, `render_views.py`, `open_lava.sh` + `open_lava_gate.py` + `mask_stats.py`, `make_sheets.py`, `iter.sh` |
| `r3/` | round-3 working notes and probes (`basalt_e_profile.py`: where the glow lines of Basalt_E are; `mask_probe.py`: how much of the floor can hold crust; `glowdbg.py`, `uvdbg.py`, `zone_lum.py`, `tri_budget.py`), the round-2 copies of the scripts |
| `iter/` | experiment builds (r3a .. r3k), each with its previews; not part of the result |

Build scripts: `blender/scripts/hole10_build.py -- --out DIR [--no-render]` and `blender/scripts/hole10_look.py` (wall / crust / cone / UV helpers it imports: keep the two together). `hole10_design.py` is unchanged
(`--verify` OK, `postcard_emit_cs --check` no drift). Deterministic: two builds give the same geometry hash, now over vertices + material names + UV0.

## What changed in round 3 (the review's findings, in the review's order)

| finding | what was wrong | what the build does now | evidence |
|---|---|---|---|
| HIGH `LOOK_FILES` | Fairway_C / Green_C flatter than the lead's 0.03 floor (1 % / 0 % of 64 px windows) | NOT FIXABLE HERE and not touched: the PNGs are the texture owner's, the 0.03 floor is the lead's number (TEXTURES.md T.2 argues the floor is stricter than the Game view and calls it the lead's decision). Re-run after the final build: the same two lines, and only those, fail at blend and FBX. Stays a FAIL in the table | `GATES_hole10.txt` H_LOOK_VERIFY_BLEND / FBX |
| MEDIUM wall: glow reads as rain / ladders, flat skyline, brown | the library box UV continues one dash lattice over every face (0.84 m dashes, 12 per tile), flat-topped quantised posts | **UV windows** (`hole10_look.author_uv`): every side face of every wall / stack / crust / skin piece takes ONE slice of the Basalt_C / Basalt_E tile; 31 % of the side faces take a slice that STARTS on a glow line (the glow runs along the face edge = in the joint between two columns), the others and every top take glow-free slices (the 8 glow-free zones of Basalt_E, measured), v density 0.3-0.4 x (long streaks), slices drawn with weight (0.14 / lum)^3 so the walls come out darker than the texture average. **Ragged wall** (`ragged_wall`): same library hex-column primitive, smooth ridge, 1-2 m steps between neighbours, tops tilted up to 0.42 rad and chipped two times in three, ends dropped only 12 % (no battlements) | `H_GLOW_JOINTS`: glow texels sampled from Basalt_E at the authored UVs of 458 ROCK_ objects: tops 0.01 %, sides 0.88 % (the continuous box UV = 2.61 %, so 34 %), median glow dash 3.2 m in the world (box UV 0.84 m), world v tile 30 m; `H_SKYLINE_VARIED` amplitude 46.1 m, mean step 4.8 m; `sheet_features.jpg` (wall close-ups) |
| MEDIUM composition: lake, floating black rectangles, no flanking walls, cone without glow, rim slabs | 45-56 % open lava, 56 isolated flat plateaus, wall 13-42 m, DRESS_CONE a brown mass, rim skin of tilted slabs | **Crust field** (`crust_field`): a jittered hex lattice of 4.3 m plates over the crater floor, tops 1.4-3.6 m above the lava (tilted, chipped, small stumps on some), cut by winding lava rivers; 1,269 plates in 42 `ROCK_CRUST_nn` chunks (<= 480 faces), same keep-outs as round 2's mesas (24 yd off every play surface, 38 yd off the line of play, 25 yd off the chord) + 25 yd off every lava light; replaces the 56 plateaus. **Near wall** raised to 14-58 m (rows 26-40 and 36-52 x a ridge of 0.55-1.45), far ring unchanged in radius. **Volcano** (`build_cone`): 72 sides, five winding LK_LAVA flow strips from the rim to the foot + a molten crater (15 % of its area), basalt at 0.42 x density. **Rim skin**: columns 1.4-2.4 m wide pushed out 5-40 cm (was 1.0-2.0 / 20-120 cm): clean prisms. **Rim lights** 9 yd off the shore | `H_CRUST`, `H_OPEN_LAVA`: lava share of the non-sky pixels on the four aerial cameras 31.6 / 28.4 / 38.8 / 38.6 % (round 2: 42.7 / 47.3 / 44.7 / 56.2, round 1: 59.4 / 69.2 / 71.0 / 71.6), rock 53-68 %; `H_CONE_GLOW`; `sheet_round1_2_3.jpg`, `previews/hole10_cone.png` |
| MEDIUM Unity-side lines unmeasured | no Game-view proof | still none: no Unity run in this phase by instruction (another workflow is calibrating in Unity). These lines are UNMEASURED, not PASS: lit grass hue 64-73, lava orange without bloom, basalt dark with joints only, smoke softness, albedo + normal on the real meshes, the three proof PNGs | `GATES_hole10.txt` U_* lines |
| LOW no DRESS_SAND_* | optional | still none, on purpose: crater.jpg has 4-5 bunkers, the hole has 2 scoring ones; a visual-only patch on the strip would read as a hazard that is not one | |
| LOW smoke not evidenced | the cards sit above the tee frame | unchanged (SMOKE_SOFT passes in the verifier, T.1 measured it in Unity); visible in the aerials | |
| LOW protected hashes | HeroTennisDriver.cs, TennisActor.cs differ from the start hashes | NOT mine: this build writes only under `work/postcard-look/v2/hole10/` and `blender/scripts/hole10_*.py`. The check now lists 28 differing files (tennis scripts, new MatchHeroes emote / intro FBXs, two Customization prefabs), all changed or added by other sessions. QualitySettings.asset was modified by someone else after 15:36. `GATES_hole10.txt` PROTECTED_FILES | `protected_check.sh` |

Landmark change: the lava-rim camera moved from the 2.2 yd shelf eye to a raised camera (14 yd over the lava, just off the inner shoulder of the rim between B and C, looking ESE along the rim cliff): the basalt columns with their
glowing joints and the lava at their foot, the shelf with agave, the pillar with the flag and the tall black wall fill the frame (`landmarks.json`; ray tests pass: lens clear, wall 16 %, lava 42 %, 25 wall / lava contact cells, pillar in frame).
Tee and approach cameras did not move.

## What the build is

Scoring core unchanged (same `postcard_lib` calls, same order); then `look_materials`, `snapshot_ground`, scenery, `retarget_materials(CRATER_OVERRIDES)`, basalt cliff skin, `build_lava`, `compare_ground`, audits, save (absolute image paths), `export_look_fbx`.

* Skin: `build_cliff_skin(basalt)` on the rim loop and the pillar loop (`follow_undercut=1.0`), 129 ROCK_SKIN pieces of <= 15 m of shore (one short tail joined into its neighbour: no rock under 60 welded vertices), UVs re-authored with the windows.
* Near wall (104 segments, ROCK_WALL_BASALT_N1-N3 + F2 / F3, 205-289 yd from the crater centre, tops 13.6-58 m, low in the tee-shot headings so the volcano shows) and far ring (126 segments F1-F3 in 268-339 m = the brief's 295-355 yd, tops 18.8-73.9 m, 7 spires): 100 % of the 360 degrees.
* Crust: 42 chunks, 11,494 faces; highest vertex 4.63 m above the lava (every sight line is above 6.5 m: 1,149 lines, 0 cut).
* Lava: `WATER_LAVA` 13,185 triangles, LK_LAVA, z 0, static; 5 `LAVA_LIGHT_nn` empties 2.5 yd over the lava (3 on the rim side 9 yd off the shore, 2 round the pillar); pillar top = GREEN at play height, sides 100 % LK_BASALT down to z -6.
* 11 basalt stacks in the lava (library ROCK_BASALT_A-F in UV-window variants), <= 12 m above the lava; 30 basalt rubble rocks at the cliff foot; plants on the shelf: 26 agave, 14 shrubs, 170 tufts (tufts cut from 300 to pay for the crust).
* Backdrop: `DRESS_CONE` (1,081 faces) + 3 `DRESS_SMOKE_nn` cards.
* Budget: 227,497 triangles (<= 250k), FBX 3.83 MB (<= 20), 689 mesh objects, no prop over 500 faces (largest rock 377, plant 480).

## Legacy gates rewritten for the new pieces (not dropped, nothing loosened)

* Round 2's `H_MESAS` -> `H_CRUST`: the same three keep-outs (24 / 38 / 25 yd, measured on every vertex incl. stumps; the plan keeps the full plate radius, round 2 kept half of it), PLUS 25 yd off every lava light and a height cap (<= 5.0 m), on `ROCK_CRUST_nn` instead of `ROCK_BASALT_M*`.
* Round 2's `H_UV_PHASE` (per-column random UV shifts, a count of variants) -> `H_UV_WINDOWS` (build: window counts) + `H_GLOW_JOINTS` (stage gates: the glow measured in the texture at the real UVs, blend and FBX). The old gate measured the shifts, not the glow.
* `H_OPEN_LAVA` tightened: round 2 allowed every camera >= 8 points under round 1 and a mean <= 55 %; round 3 demands every camera >= 5 points under round 2, <= 45 %, the mean <= 40 % and >= 10 points under round 2, rock >= 40 %. aerial3 (outer moat of the strip) improves only 6.0 points: its foreground is the 24-yd keep-out round the strip.
* Unchanged: `H_NEAR_WALL` (12-60 m, the 14 yd clearance), `H_FAR_RING`, `H_SKYLINE_VARIED` (>= 40 m amplitude, >= 4 m step), `H_STACKS`, `H_RUBBLE`, `H_SIGHTLINES_CLEAR` (now also run on the crust), `H_ROCK_CHUNKING` (<= 24 yd within 25 yd of a light).

## Open issues / honest limits

* `postcard_look_verify` `LOOK_FILES@blend/@fbx` FAILS (Fairway_C 1 % / Green_C 0 % of 64 px windows reach luminance sd 0.03): a texture-owner / lead decision. Every other look line passes at both stages (46/47 blend, 47/48 FBX).
* `postcard_verify` `MATERIALS@blend/@fbx` and `FBX_BUDGET@fbx` fail by design (old MAT_* allow-list; old 4 MB / 150k-triangle cap).
* The lava is still 28-39 % of the non-sky pixels on the aerials (crater.jpg is about 15-25 % by my estimate, 9.5 % bright orange by the reviewer's): the crater is 340 yd across for a 357 yd hole and the keep-outs round the play surfaces are kept. Inside them (a moat 24 yd off the strip and 38 yd off the carry) the floor stays open lava.
* The wall glow is still dashes (3 m long, 34 % of the box-UV glow), not continuous joint lines: Basalt_E has gaps in every line and its density gate (UV_DENSITY >= 1/3, anisotropy <= 4:1) forbids stretching one stretch over a 40 m face. A non-periodic Basalt_E (texture owner) would fix it.
* Nothing is measured in the Game view. The Blender preview imitates GolfLook / GolfAtmosphere (tints, painted sky, trilight, fog, GolfLava ramp stand-in, LAVA_LIGHT point lights) but is not the Game view; in it the wall reads dark red-brown (the Crater fog), the Game view calibration says the same (TEXTURES.md T.3).
* `DRESS_CONE` now carries LK_LAVA faces: the Blender verifier allows it (`DRESS_CONE` may use LK_BASALT / LK_LAVA / LK_ROCK); GolfLava is world-projected, so the cone's mesh UVs for those faces are ignored in Unity. `PostcardImportCheck` on the installed hole has not been run (no Unity).
* No `DRESS_SAND_*` (see above). Not installed: `blender/hole_10.blend` and `Unity/Assets/Resources/Course/hole_10.fbx` are still the flat baseline (sha b0c478e6.., e99475de..).
