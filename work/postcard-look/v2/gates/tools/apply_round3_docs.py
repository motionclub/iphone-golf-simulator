"""One-off: edit v2/gates/GATES_v2_section.md for the round-3 review fixes (rows, run block, review-round-3 table, known gaps). Idempotent via the marker."""
import os, re, sys
G = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
p = os.path.join(G, "GATES_v2_section.md")
s = open(p).read()
if "## Review round 3" in s:
    print("already applied"); sys.exit(0)
L = s.split("\n")


def row_index(gid):
    for i, l in enumerate(L):
        if l.startswith(f"| **{gid}**"):
            return i
    raise SystemExit(f"row {gid} not found")


def edit_row(gid, title=None, measure=None, why=None, mut=None):
    i = row_index(gid)
    c = L[i].split(" | ")
    if title:
        c[0] = "| **" + gid + "** " + title
    if measure:
        c[2] = c[2] + " " + measure
    if why:
        c[3] = c[3] + " " + why
    if mut:
        c[-1] = c[-1] + " " + mut
    L[i] = " | ".join(c)


edit_row("ROCK_NOT_ICOSAHEDRON", title="(repaired three times)",
         measure=("**Round 3: components are SURFACE PATCHES** (`manifold_patches`): polygons are joined only across MANIFOLD edges (an edge used by exactly two polygons), a vertex or an edge "
                  "that cells merely TOUCH at is duplicated per patch - so every icosahedron / icosphere / octahedron / cube of a welded cluster is judged as its own closed solid (a cluster of 6-14 "
                  "icosahedra has valences {5, 10, 15, ...} on the welded mesh, 6-14 patches of 12 interior vertices with valence {5} in the patch view); the exact-regular-solid-by-area test uses the "
                  "same patches. **Closed-solid rule** (`open_edge_fraction`): <= 10 % of the polygon edges of a rock mesh may be open (library hull rocks, spires and stacks: 0 %; basalt prisms, "
                  ">= 60 % vertical area, have open bottoms and are exempt)"),
         why=("round 3 (review): a welded cluster of 6-14 exact 12-vertex icosahedra sharing vertices passed (valences {5,10,15,..} are >= 3 distinct). My own follow-up probe of the next dodge: a bundle "
              "whose every face is split off by 2 mm (beyond the 1e-4 weld) is a triangle soup of single-triangle components, no interior vertex, and passed every valence rule until the closed-solid rule "
              "(100 % open edges). Measured with `tools/probe_cluster.py`: 96 welded clusters (12 / 42-vertex icosahedra, octahedra, cubes x vertex / edge sharing x jitter before / after the weld x n 4..14) "
              "ALL FAIL, the 29 props-library kinds ALL PASS (`tools/probe_open.py`: library open-edge share 0 %, basalt 31 % exempt; `tools/probe_mindist.py`)"),
         mut=("**round 3: welded clusters of 12-v icosahedra (varied sizes, all rocks / loose only), with 12 % jitter after the weld, of 42-v icospheres, of octahedra; bundles of icosahedra with every face "
              "split off by 2 mm (all / loose only)**; control: welded clusters of natural hull stones PASS"))
edit_row("ROCK_VARIETY", title="(repaired twice; round 3: unchanged, it inherits the patch rule)")
edit_row("LOOK_FILES", title="(repaired twice; round 3: provenance / lead decision)",
         why=("**LEAD DECISION, not a measurement (round 3, review low item).** The floor 'luminance sd >= 0.03 in >= 90 % of the windows' is the number in the lead's task (A.2: 'at least 90 % of 64x64 "
              "windows for ground albedos'); the tool only made the window a FOOTPRINT (1/16 of the tile) so it no longer depends on the file size. It was NOT calibrated on the stills and cannot be: "
              "`calib/still_calib.txt` measures the user's stills at 8-16 still-pixel windows (1-3 m of ground) as sd >= 0.03 in only 31-67 % of the windows of the mown fairway / green crops "
              "(split upper_green 31 %, fairway_strip 67 %), and 100 % only at 32 px. If the lead wants a floor grounded in the stills, lower `TH2['win_frac']` (e.g. to 0.5) or `TH2['win_sd']`; if the "
              "lead keeps 0.03 / 90 %, the tex agent has to add blade-scale detail to Fairway_C / Green_C. The tool does not tune either to the live files, which FAIL today (Fairway_C 1 % of windows, "
              "Green_C 0 %)"))
edit_row("NO_FOAM_STRIP", title="(repaired three times; replaces the cap half of SURF_SHORE)",
         measure=("**Round 3: ANY ORIENTATION.** Foam-like geometry = LK_SURF triangles with alpha >= .3 (or a ghost piece), every LK_FALL triangle except a WATERFALL SHEET (`fall_sheets`: a welded "
                  "LK_FALL component of plan extent <= 8 m and mean |nz| <= 0.6, at most 2 per hole and 60 m2 in total, largest first - only its flat part, nz > 0.8, counts), LK_SMOKE on anything but the "
                  "DRESS_SMOKE cards, and ANY white-ish material **whatever its name (MAT_* included; only the collision meshes and the game's hidden placeholders FLAG / HOLE_CUP / BALL_START / MARKER_* are skipped)**, "
                  "facing up, sideways or down. Coverage = exact 3D triangle-triangle overlap (BVH) of the foam with the vertical plane strip over every shore-normal segment (0..10 m, 1 m samples); the "
                  "offshore raster draws the edges of near-vertical triangles; the area cap uses the 3D area"),
         why=("round 3 (review): a continuous white LK_SURF skirt around the whole shore at nz 0.44 (a 63 degree ramp) passed every gate at both stages because only up-facing (nz > 0.5) triangles counted. "
              "My own probe found the same hole for a white material called MAT_* (up-facing only) and a vertical curtain (no plan area). All closed. The lib smoke builds are unchanged: cover 19 % / 17 %, longest run 6 / 9 m"),
         mut=("**round 3: continuous skirt nz 0.45 as LK_SURF, continuous vertical wall (nz 0) as LK_SURF, continuous steep ramp nz 0.1 as LK_FALL named WATER_FALL, continuous skirt nz 0.3 of a white MAT_SPRAY_SKIRT "
              "material**; control: the hole-8 positive carries a real vertical LK_FALL waterfall sheet and passes"))
edit_row("NO_ROCK_STRETCH_2X", title="(repaired three times)",
         measure=("**Round 3**: (a) a mesh is a props-library kind when its topology hash matches OR when it FUZZY-MATCHES (`lib_fuzzy_match`: unique vertices normalised into their own bounding box - a stretch along "
                  "the mesh axes leaves them unchanged -, per-axis quantile prefilter 0.06 over all 48 axis permutations / mirrors, then >= 85 % of the vertices within 0.03 of a library vertex both ways), so a library mesh "
                  "with a face removed, turned 90 degrees or mirrored and baked 4 : 0.6 is still compared with its library bounding box (the ratio uses the matched axis permutation); (b) a ROCK_ / CLIFF_ROCK mesh "
                  "that matches no library kind cannot be compared, so its own PCA extent ratio r3 (third / first principal std of the vertices, mesh space) must be >= 0.15 (`ROCK_TH['stretch_r3_min']`)"),
         why=("round 3 (review low): a library mesh baked 4 : 0.6 with ONE face deleted (topology hash differs) and hand-made rocks baked 4 : 0.5 / 5 : 0.4 passed. Measured with `tools/probe_lib.py` / "
              "`review2/probe_baked.py`: r3 of the 29 library kinds 0.17 (ROCK_SEASTACK_E, ROCK_WALL_BASALT_A) .. 0.89; baked hand-made hulls 4 : 0.5 -> 0.06-0.10, 5 : 0.4 -> 0.06-0.08, 3 : 1 -> 0.18-0.25. "
              "So 0.15 catches a hand-made rock stretched past ~4 : 1 and CANNOT catch 3 : 1 (as long as the library's own ledges): a hand-made rock baked up to ~3 : 1 passes - disclosed in Known gaps"),
         mut=("**round 3: library mesh baked 4 : 0.6 with one face removed (under the name ROCK_SLAB_77), library mesh turned 90 degrees and baked 3 : 1, hand-made hull baked 4 : 0.5 (ROCK_WALL_77) and 5 : 0.4 "
              "(ROCK_LARGE.099)**; controls: hand-made hull baked 1.5 : 1 : 1, library mesh with one face removed unstretched"))
# new row PLAY_SURFACE_WALLS after PLAY_SURFACE_FACES
i = row_index("PLAY_SURFACE_FACES")
L.insert(i + 1, "| **PLAY_SURFACE_WALLS** (new, round 3) | \"Shore, centerline, pin, play height ... unchanged\" / \"Scoring cuts unchanged\" | the NON-up-facing (nz <= 0.5: cliff walls, steep slopes, undersides) "
         "non-degenerate triangles of every TERRAIN / FAIRWAY / GREEN / TEE_BOX / BUNKER / CART_PATH mesh vs the baseline's (`hole_0N_nonup.npz/json`, built ONCE from work/postcard-look/baseline by "
         "`--build-nonup-baseline`, per stage): exact rounded-triangle sets WITH winding equal -> pass; otherwise (re-triangulation) every baseline triangle centroid lies within 1 mm of a current "
         "non-up surface that faces the same way (3D BVH nearest point + normal dot >= .5) and vice versa, and the non-up area matches (1e-6 relative). Together with PLAY_SURFACE_FACES (up-facing) every "
         "non-degenerate collision triangle is covered | round 3 (review low): deleting the largest TERRAIN wall polygon passed on holes 8, 9 and 10: the up-facing face gate saw no change and "
         "`PLAY_SURFACE_ALLVERTS` is an info line (a deleted polygon keeps its vertices). Baseline 2,394 / 4,980 / 1,980 non-up triangles (holes 8 / 9 / 10), the lib smoke builds and the synthetic positives "
         "equal it exactly at both stages (the legal lib output never touches the collision body) | TERRAIN wall polygon deleted, flipped, one vertex moved 5 cm (each on a polygon none of whose vertices is "
         "on an up-facing face: every top-surface gate stays blind); control: a flat wall polygon poked into 3-4 triangles (same surface) passes |")
s = "\n".join(L)
# run block
s = s.replace("$B -b ... -- all --build-face-baseline                       # ONCE (done 2026-10-04): hole_0N_faces.npz/json next to the vertex signature\n",
              "$B -b ... -- all --build-face-baseline                       # ONCE (done 2026-10-04): hole_0N_faces.npz/json next to the vertex signature\n"
              "$B -b ... -- all --build-nonup-baseline                      # ONCE (done 2026-10-04 14:15, round 3): hole_0N_nonup.npz/json = the walls / undersides\n", 1)
s = s.replace("Measurement helpers a hole-build agent can call (all in `postcard_look_verify.py`, pure functions of a `Snap`): `white_geometry`, `white_reach_cover`, `white_union_runs`, `rock_shape`, `rock_components`,\n`shape_families`,",
              "Measurement helpers a hole-build agent can call (all in `postcard_look_verify.py`, pure functions of a `Snap`): `white_geometry`, `fall_sheets`, `white_reach_cover`, `white_union_runs`, `rock_shape`, `rock_components`,\n`manifold_patches`, `open_edge_fraction`, `lib_fuzzy_match`, `nonup_tris`, `shape_families`,", 1)
s = s.replace("Probes: `tools/probe_lib_kinds.py` (valences of the library), `probe_shape.py`, `probe_amin.py`, `probe_repeat.py`.",
              "Probes: `tools/probe_lib_kinds.py` (valences of the library), `probe_shape.py`, `probe_amin.py`, `probe_repeat.py`; round 3: `probe_cluster.py` (welded clusters vs the library), `probe_open.py` (open-edge share), "
              "`probe_mindist.py` (smallest vertex distances), `probe_patch_stats.py` (per-patch valence / edge / area statistics: library vs perturbed icosahedra).", 1)
s = s.replace("python3 work/postcard-look/v2/gates/tools/summarize_mut.py work/postcard-look/v2/gates/runs/selftest_all_fbx.log ",
              "python3 work/postcard-look/v2/gates/tools/summarize_mut.py work/postcard-look/v2/gates/runs/selftest_all_fbx_r3.log ", 1)
s = s.replace("### Superseded rows (above): `ROCK_NOT_ICOSAHEDRON`,", "### Superseded rows (above): `PLAY_SURFACE_FACES` is joined by `PLAY_SURFACE_WALLS` (round 3), `ROCK_NOT_ICOSAHEDRON`,", 1)
s = s.replace("## Where the repo files stand against these gates (snapshot 2026-10-04 11:50; see Evidence for the full lists)",
              "## Where the repo files stand against these gates (snapshot 2026-10-04 11:50, re-run with the round-3 verifier 14:55: no verdict changed except the added PLAY_SURFACE_WALLS PASS; see Evidence for the full lists)", 1)
s = s.replace("The tool does not decide between \"add blade-scale detail\" and \"lower the floor\": that is the lead's call.",
              "The tool does not decide between \"add blade-scale detail\" and \"lower the floor\": that is the lead's call (see the LOOK_FILES row, 'LEAD DECISION').", 1)
# review round 3 section
r3 = """
## Review round 3 (2026-10-04, second skeptic review of this tool): findings and what was done

| finding | severity | fix |
|---|---|---|
| NO_FOAM_STRIP counted only up-facing triangles (LK_SURF / white material nz > 0.5, LK_FALL nz > 0.8): a continuous white LK_SURF skirt at nz 0.44 around the whole shore passed every gate at both stages | medium | foam of ANY orientation; coverage by exact 3D overlap of the foam with the shore-normal plane strips; edges of near-vertical triangles in the offshore raster; area cap on the 3D area; LK_FALL waterfall sheets exempt by geometry (<= 2 components, plan extent <= 8 m, mean abs nz <= 0.6, <= 60 m2), never by name; **my own probe found two siblings and closed them: a white material called MAT_* (was exempt) and a vertical curtain (no plan area)**; mutants: skirt nz 0.45, vertical wall, steep LK_FALL ramp named WATER_FALL, white MAT_ skirt nz 0.3 |
| ROCK gates passed 6-14 exact 12-vertex icosahedra that SHARE vertices (valences {5,10,15,..}) | medium | components are manifold SURFACE PATCHES (touching cells are separated before every per-component rule); closed-solid rule (<= 10 % open polygon edges) for the next dodge (every face split off by 2 mm); mutants: welded clusters of icosahedra / icospheres / octahedra, jitter after the weld, 2 mm split bundles; control: welded natural hull stones |
| NO_ROCK_STRETCH_2X: a library mesh baked 4 : 0.6 with one face deleted and hand-made rocks baked 4 : 0.5 / 5 : 0.4 passed | low | fuzzy library match (bounding-box-normalised vertex sets over 48 axis permutations / mirrors) + PCA r3 >= 0.15 for rock meshes that match no library kind; the residual (a hand-made rock baked <= ~3 : 1) is disclosed |
| deleting a non-up-facing TERRAIN collision polygon (cliff wall / underside) passed | low | new gate PLAY_SURFACE_WALLS (baseline `hole_0N_nonup.npz/json`, winding-aware, re-triangulation tolerated) |
| LOOK_FILES floor 0.03 / 90 % is not calibrated on the stills; the live Look fails it | low | not tuned (the review said not to): GATES.md states it is the lead's number and a decision, with the calibration data, and the failure message says so; **the lead / tex agent decide** |

"""
j = s.find("## Known gaps / limits (honest list)")
s = s[:j].rstrip("\n") + "\n" + r3 + s[j:]
# known gaps
old = s[s.find("* Rocks: the valence rule cannot tell"):s.find("* The FBX format has no shear")]
new = ("* Rocks: after the patch split and the closed-solid rule, a bundle of LOW-POLY STONES whose patches are not regular (one edge subdivided or a face poked into an icosahedron: valences {4,5,6} / {3,5,6}) "
       "still passes: it is built like the library's own cairn (6 stones of 15-16 vertices) and no valence, edge-length or area statistic separates them with a margin (`tools/probe_patch_stats.py`: library "
       "patches have a valence-5 share <= 0.63, 'icosahedra with one or two edge splits' 0.71-1.00, but a poked face drops one under the library band again). The visual checklist (rocks read as rocks "
       "from the tee) is the backstop. Any rock mesh that is NOT a props-library mesh and not stretched past r3 0.15 is judged by shape statistics only. A stretch applied along ROTATED (non mesh-axis) "
       "directions to a library mesh is not caught by the fuzzy match (bounding-box frame); a hand-made rock baked up to ~3 : 1 (r3 0.18-0.25, as elongated as the library's ledges) passes the PCA cap.\n")
s = s.replace(old, new, 1)
s = s.replace("* `NO_FOAM_STRIP` ignores vertical white geometry (a curtain has no footprint) and the faded fringe (alpha < .3) of a piece that does reach .3; the fringe alone would add 0.35 m2/m on Needle.\n",
              "* `NO_FOAM_STRIP` ignores the faded fringe (alpha < .3) of a piece that does reach .3 (the fringe alone would add 0.35 m2/m on Needle) and up to 2 waterfall sheets (<= 8 m wide, <= 60 m2 in total: at most "
              "16 m of the shore); foam farther than 10 m from the shore may be dashed (pieces closer than 8 m merge, merged length <= 11 m).\n"
              "* `PLAY_SURFACE_WALLS` compares triangles to 1 mm; a polygon moved by < 1 mm is not a gate failure (the vertex rounding of the exact path is 0.1 mm).\n", 1)
open(p, "w").write(s)
print("applied")
