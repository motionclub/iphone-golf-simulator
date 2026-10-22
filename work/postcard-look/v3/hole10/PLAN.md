# Phase 4 Crater implementation and UV plan

Status: scratch plan only. Phase4 source edits require the parent's authorization after Phase3. No hole10 source, shared library, PNG, design, baseline, verifier, or installed asset was changed to prepare this plan.

The target is crater.jpg: real narrow basalt columns with a broken rim, a grass tee on dark stone, a supported column-sided green, a lighter fairway with a darker collar, and a volcano with two or three soft plumes. Phase4 is limited to hole10_*.py. Shared texture repairs wait for the later authorized phase. GATE P4 cannot be ALL PASS with the current basalt tile; the measured inherited texture FAILs below must remain FAIL.

## Read-only measured constraints

The adapter scripts import the unchanged verifier and texture decoder. They write only scratch JSON/logs. PNG values come from decoded file bytes, without Blender image gamma conversion.

| Check | Current binary result | Exact evidence and implication |
|---|---|---|
| BASALT_PRISMS | FAIL | constraint_measurements.json:46.670589% of glow area is in neither vertically elongated nor sufficiently small components; limit10%. Coverage3.889847%, horizontal run5.859375%, spacing4.051434m, and both normal-plane shares individually pass. A geometry-only edit cannot repair the failed PNG component topology. |
| A replacement nonempty vertical ZONES interval | FAIL | Every Basalt_E u-column contains glow above the window mask threshold. The least occupied column is.87890625%, versus the frozen.02% zone limit. There are0 safe columns. Therefore every nonempty interval also fails. Re-baking GLOW_U/ZONES/PROFILE128 alone cannot repair this tile. |
| BASALT_JOINTS in the valid Unity fixtures | FAIL overall | Parent batch2 has3 passing views. Later valid batch3 az35 has rung share21.1%>20%; the other views have19.6/17.0%, with aggregate junction7.5916/100. Preserve both batches; selecting only passing views is not allowed. |
| Direct build_column_wall, 24m path, heights12/30/50m | FAIL inherited rock checks | column_measurements.json:all18 chunks fail PCA r3>=.15. Ranges are.093–.129 at12m,.043–.053 at30m,.026–.032 at50m.16/18 chunks also fail regular-solid component classification. Both rows=1 and rows=2 leave thin row-wise chunks. |
| Direct columns: count/side/span | PASS in these fixtures | Each chunk has29–66 detected caps and side area90.1–97.2%; exact count_columns output is saved. All horizontal AABB diagonals<=17.20m and polygons<=482. This partial PASS does not override PCA or component FAILs. |
| Native mowing | PASS in the current library fixture | Parent Game proof:fairway4.682149%<=12%,green3.775677%<=8%,600k+ supported pixels each. Recheck after Crater lighting/placement changes. |

The direct column measurements use heights above z=-1.6m, width range.6–1.8m, seed4, a24m straight path, and unchanged ROCK_TH/TH values. Detected cap counts can include intermediate fracture caps; they are not a claim that the fixtures contain that many distinct full-height shafts. Each final build needs actual-column metadata and geometric measurements too.

The default18m/4.5m needle also fails inherited PCA at.132107. This affects other phases, not the Crater column plan. Wider seed3 fixtures17.6m/5.5m and16m/5.2m pass at.161966/.164008; every final seed must be measured independently.

## Frozen constraints to preserve

- Keep all hole10_design.py bytes, scoring meshes, topology, markers, cup, tee, pin, centerline, shore, and PLAY_Z=6 unchanged. Max scoring vertex delta is exactly0.000m. Keep the scoring build sequence and take the ground snapshot before scenery.
- Existing TEE_BOX grass top is6.24m; fairway top is6.14m. The square is14yd by12yd. CRATER_TEE_PAD still requires its shape fill>=.90, aspect<=1.3, and only LK_GREEN/LK_FAIRWAY. Dark stone belongs to new scenery beneath/around the grass, not to the scoring grass material.
- Lava stays below the inherited CRATER_LAVA maximum3m. Do not raise it to play height. Preserve the source water mesh/scoring semantics, required3–5 lava lights, and orange/soft-smoke gates.
- Scenery/rock vertices must remain off play; loose green props keep the inherited1m green margin and no obstruction within3m of the pin. A material or object prefix is not an exemption from the physical checks.
- Each rock prop remains<=500 polygons, with inherited minimum60 welded vertices/100 polygons and PCA r3>=.15 when applicable. Nearby-lava chunks remain<=24yd; also preserve the new true horizontal AABB diagonal<=20m guard. Scale1 alone does not prove a non-stretched rock.
- Retain ROCK_WALL_* actual wall clusters, at least5 real cap columns/mesh and side area>=45%, with wall-ring coverage>=80% across the72 angular bins. No renamed walls or fake exempt objects.
- H_NEAR_WALL still requires at least60 near segments,>=14yd clearance, the source radius limits, and tops12..60m. Preserve the proof-heading window and dense tee/approach sightline testing.
- H_CRUST still requires>=20 chunks and>=500 actual plates,>=24yd from play/shore,>=38yd from the line of play,>=25yd from the tee-to-C chord/lava lights, and top<=CRUST_TOP_MAX. The large cooled floor plates are not claimed as.6–1.8m vertical columns.
- Preserve H_GRASS_FRINGE_BUILD's count>=300, clusters>=100, singles>=5, lean<=12.05deg, its plant-kind/height restrictions and FR_BUDGET, plus total triangles<=250000. Reducing hidden scenery is legitimate; reducing a retained threshold is not.
- GREEN_APRON's frozen material allowlist is LK_FAIRWAY/LK_GREEN. FIRSTCUT may use the existing darker LK_ROUGH. A darker green edge may occupy existing non-scoring rough outside GREEN/APRON only; no extra playable green or false hazard overlay.

## Column and wall implementation after authorization

Retire the giant scaled near/far library segments and the old narrow plank-like cliff skin. Use Phase1's real5/6-sided world footprints, varied tops, clipped corners and final world dimensions. Keep actual shaft widths.6–1.8m; no nonuniform instance scaling.

Available API:

```python
PL.build_column_wall(D, path, top_z, bottom_z=-1.6,
                     width_m=(.6,1.8), rows=1, closed=False,
                     seed=0, name="ROCK_WALL_V3", max_faces=490,
                     relief_m=.16, clip=None, max_span_m=20.0)
# returns chunks with lk_v3_columns vertex/face ranges and world-width metadata
```

The current helper is an input generator, not a certified whole-hole solution. Add a hole-specific adapter in hole10_look.py rather than altering the shared library during Phase4:

1. Generate actual world-sized shafts and preserve their metadata. Reconstruct each shaft as continuous connected stone where its intermediate fracture rings currently form isolated regular components. Give visible stones genuine cut arrises/chips; do not add arbitrary vertices to satisfy a classifier.
2. Batch actual neighboring columns across both path and depth, rather than flushing an entire row independently. For tall closed ring walls, divide at genuine irregular geological fracture levels into compact volumetric batches. Test a5–8m vertical band with enough neighboring shafts across2–3 real rows to meet60 vertices/100 polygons,5 columns, PCA>=.15,<=490 polygons and<=20m span. These are starting dimensions, not measured PASS claims. Rebalance small tails across adjacent spatial batches; do not merge blindly into an elongated object.
3. Keep the outer ring geometrically continuous across>=80% of360deg. Use genuine ridge/saddle height variation and staggered top shafts. Re-evaluate far-wall heights rather than retaining the old68–74m spikes: a lower jagged backdrop can expose the135m volcano and reduce texture repetition/triangle cost without moving play. The reference view and all old min/max checks decide the final silhouette.
4. For rim/green-pillar cladding, use the frozen terrain boundary/profile and an actual open exterior shell against that terrain. A legitimate shell may omit buried rear/bottom faces; it must retain real column caps, side facets, relief and undercut support. Do not call a closed skinny prism ROCK_SKIN merely to escape PCA.
5. Keep rim cladding's frozen wall profile and pillar follow_undercut=1 behavior. The new generic helper does not automatically follow that bowl profile or clip scoring-water boundaries. The adapter must reject entire forbidden cap footprints, inset its roots and use the original terrain BVH as backing; record every rejected column.
6. Preserve CRATER_WALL_COVERED: exposed walls<=1%, largest connected bare patch<12m2, link distance4m. Keep terrain sides/underside>=95% LK_BASALT, pillar bottoms reaching lava+.05m, and GroundHeight at the pin hitting the original GREEN at play height.
7. Replace the11 lava stacks with actual compact multi-column clusters at their legal existing scenery locations, retaining supports to the lava and eye/flag corridors. Avoid the prior eight-percent iterative shrink approach as a default: first solve footprints/heights directly, then measure exact sightline clearance. Their genuine closed geometry gets the same shape/PCA checks.
8. Estimate triangle/object/material costs from prototype counts before emitting the full ring. The direct helper at30–50m costs~2020tri per24m per row; copying it around several long rings would exceed the available budget. Remove hidden interior faces and redundant buried scenery, while retaining visible geological structure and every mandatory count. Record exact final triangles and native render batches.

Do not globally use the new build_postcard_cliff(style="crater") without the hole-specific support/clip adapter; it does not preserve the original pillar undercut automatically.

## UV architecture and unavoidable current FAILs

Keep H_UV_WINDOWS, H_GLOW_JOINTS, BASALT_PRISMS and BASALT_BUILDER_WINDOWS unchanged. Keep nonempty GLOW_U/ZONES and the complete128-sample PROFILE128 contract. The current six bright-u anchors/five plain-u strips must not remain merely because the old texture had them, but there is no valid replacement for ZONES with the current tile.

Phase4 can author a real UV layout and report its true failure; it cannot repair the shared PNG:

- Caps receive physically planar world-density charts. Reserve actual certified plain regions only after a tile has them; do not label a cap glow-free because its UV was assigned to a list named ZONES.
- Side charts use their actual tangent/vertical world distances and preserve the8m material contract, density and anisotropy limits. Tie sampled edge branches to real column joints/fractures; do not crop every face into one vertical strip and erase the branching network.
- Use a consistent wall-depth UV origin across adjacent columns and geological batches. Avoid v-resetting at each mesh or repeating a bright horizontal heat band. If fitting a complete depth field requires a density/anisotropy violation, reduce legitimate scenery height or report FAIL; do not silently shrink UV density.
- UV_STATS must describe actual authored geometry and sampled glow. Keep>=60 genuinely authored meshes, top_n==top_free only when measured true, and15–45% side glow faces. Do not duplicate counters, mark plain faces by intention, delete lists, or use empty zones.
- Remeasure source PNG zones:zone_glow_max<=.0002, narrowest edge window at each glow anchor>=.04, and full PROFILE128 deviation<=.01. Store exact sample masks and maxima. Current ZONES/PROFILE deviations remain FAIL.

For the later authorized shared repair, an alternative to retrying the global cell network is a set of bounded elongated fork/zigzag glow components, with faint/depth-faded connecting fractures below the inherited hard glow mask and normal grooves matching the same joints. Reserve real nonempty plain-u chart regions while retaining enough branched edge regions. This is a candidate, not a promised PASS. The candidate must independently meet BASALT_PRISMS component<=10%, coverage<6%, run<=12%, cross-joint spacing>=3m, both normal-plane shares>=8%, as well as Game BASALT_JOINTS junction/vertical/rung/color limits. The PNG and Game masks use different thresholds; passing one does not imply the other.

After such a tile genuinely passes, recompute all GLOW_U/ZONES/PROFILE128 values from its actual decoded pixels, retain nonempty used lists, re-author all affected Hole10 UV charts, and run every unchanged gate. Recomputing constants is measurement, never a texture-window threshold change.

## Tee platform, fairway and smoke

- Replace the flat edge ribbon with a physically supported dark stone body and a cut stone edge. Keep grass geometry/material unchanged. Prototype genuine closed basalt chunks with full thickness below the grass, actual chips and compact dimensions; the existing failed thin-basalt-ribbon idea must not be retried as a renamed ribbon.
- H_TEE_RIM remains exactly:>=1 piece; every top vertex inside TEE outline;>=1.5m from markers/ball; cap lift3–15mm; exact RIM_SPEC material; no DRESS_PATH; rough/plant flat-top area<=18.5m2. Preserve these predicates and calculate stats from real geometry. The cap can sit at the existing11.5mm offset; the substantial stone body belongs below it and must be actually visible/supported.
- Terrain around the tee is also at play height. If a visibly raised stone platform cannot coexist with the frozen grass/fairway and off-play rock constraints, report4.2 FAIL with the obstructing sections. Do not move the scoring tee or claim an occluded thin rim is a raised platform.
- Add two suitable tropical plants at legal corner rough positions, away from markers/ball and water, with authoring colors and native sway caps retained. Use low foliage that does not block the ball/flag corridors.
- Keep the subtle fairway and dark FIRSTCUT materials. Re-run renderer-masked mowing after the full Crater scenery is dressed. GREEN_APRON stays in its frozen allowlist.
- Preserve UV-only sliver repair on FAIRWAY_FIRSTCUT:use its actual material tile contract, retain vertices/faces, and measure the similarity chart/Jacobian result. H_GROUND_UV_SLIVERS retains own bad area<=.5m2, terrain<=15m2/largest10m2, repaired max ratio<=1.001 and>=1 fixed sliver. The inherited GROUND_UV_LOCAL_SMEAR remains a separate exact verifier check.
- Keep the large volcano with genuine glowing lava streams. Build2 or3 spatially coherent soft plume groups rather than an unrelated field of cards. Recheck SMOKE_SOFT, smoke/cone visibility, and SMOKE_IN_FRAME>=1.5% in every required proof. Do not substitute a hard grey sphere or change smoke material/shader thresholds.

## Authorized execution and evidence sequence

1. Before source edits, preserve source/PNG hashes and run read-only scoring guards; prepare exact permitted-file diff. Scratch lives under v3/hole10 only.
2. Prototype the hole-specific column adapter in scratch. Run unchanged count_columns, rock_shape/PCA, face/span/world-width, UV-density and cap/side measurements on near wall, high far wall, ridge and pillar fragments. Inspect side/top silhouettes before full build. Record each FAIL.
3. Once one legitimate adapter works, change only hole10_look.py/hole10_build.py. Keep design/build core and all original gate predicates. Run required shared smokes after any library change; none is authorized in Phase4. Source-only hole edits receive their relevant geometry/UV checks.
4. Stage a full Blender build in v3/hole10 using export_look_fbx(LINEAR), then run the complete unchanged hole10 verifier against baseline scoring. Preserve all failures, including shared texture failures and H_UV_WINDOWS. Save overview and reference/aerial side-by-side.
5. Parent serializes native Unity work through heavy.sh. No changed FBX or Look PNG import while a batch runs. Measure exact Game BASALT_JOINTS masks, lava orange, smoke softness/visibility, mowing, plant import/GPU caps and actual bounds. Retain every valid shot; a later failing view makes the overall gate FAIL.
6. Record finite GATE P4 PASS only if every verifier gate, BASALT_JOINTS, lava/smoke and scoring condition passes. Otherwise record GATE P4 FAIL with numeric causes and continue only as the parent authorizes the phase sequence. Installation uses the mandated installer and7/7 guards, never direct asset/meta copying by this subtask.

The hole agent also measured a later framing limit: the frozen tee proof can expose only~2.26% ideal lava at z0 (~2.30% even at the forbidden5.99m level), well below the15% target. Phase4 must not raise lava or alter gameplay camera code to hide this. Preserve that evidence for Phase5's honest framing gate.

## Decisions after failed ideas

Direct thin closed column rows failed inherited PCA in both rows=1 and rows=2 fixtures. Adding a second row through the current helper does not place both rows in the same volumetric object. Stop this idea before a third retry; the next design must change real chunk construction, not its name or scale.

Re-baking plain-u windows cannot repair current Basalt_E because every u-column is over the frozen glow-free limit. A third selection/crop attempt would be the same impossible idea. Shared texture topology/chart reservations must change in an authorized phase, or the texture/window gates remain FAIL.

All feasibility measurements are in constraint_measurements.json/log and column_measurements.json/log, with scripts alongside. No feasibility candidate described above is labelled PASS until its unchanged gates are actually measured.
