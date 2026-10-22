# Phase 1 shared library record

GATE P1: FAIL. The later valid Unity az35 view fails BASALT_JOINTS (rungs21.1%>20%), and the cliff outline fails the4m requirement. Native mowing and GPU sway measurements now pass. A read-only inherited PCA check also rejects the default18m/4.5m needle (r3.1321<.15). No threshold has been relaxed.

## Completed implementation

- Fairway/green stripes, smoothness differences and normal lean reduced. Fine blade/micro texture variation retained. FIRSTCUT maps to existing darker LK_ROUGH. GREEN_APRON stays LK_FAIRWAY because the frozen material allowlist permits only LK_FAIRWAY/LK_GREEN; a separate darker green collar remains unresolved.
- Basalt_C/E/N regenerated with a full branching joint network, depth-darkened non-glow rock, reduced emission width and exact edge welding. Geometry comes from new world-sized5/6-sided columns with varied top heights and clipped corners. Chunks flush before490faces or20m horizontal AABB diagonal.
- New final-sized needles have tapered layered rock, a shallow supported0.35m turf crown and three broken surf patches; no object stretch. Historic BUILDERS and plant mesh fingerprints remain unchanged.
- New shared cliff builder uses25m sections with horizontal strata,1.1–2.8m headland intervals,42cm outline relief,70cm overhangs,55cm undercuts, and attached vines. Crater uses the new column wall generator over frozen terrain loops. All scoring vertices remain unchanged.
- Shared ruin courses now use genuinely clipped cut stones with varied broken upper corners, rather than six-face cuboids. Existing support-checked build_masonry_arch already uses cut blocks and remains available to Hole8. Hole9 masonry/stone changes belong to the hole agent.
- Smoke outputs route to v3/lib. Positive smoke FBX export uses export_look_fbx with LINEAR colors. The inherited raw SRGB negative-control export remains a deliberately corrupt fixture in scratch. Texture process now returns nonzero for failing gates.

## Binary evidence

| Check | Result | Evidence |
|---|---|---|
| Final ground09 smoke | PASS | final_ground09.log:26/26; frozen terrain geometry preserved |
| Final props smoke | PASS | final_props.log:115/115,163.4s; legacy byte compatibility, plant colors, caps, instancing, export guards and negative controls |
| Earlier ground08 smoke | PASS | ground08.log:26/26 |
| Actual generator test scene | FAIL | test_scene_final.log/test_scene.json:10/11; CLIFF_OUTLINE_RUN fails |
| BASALT_JOINTS, exact Blender PNG bytes | PASS | Three views: base median26.4/26.4/27.4<=55; S.181–.185<=.25; glow10.83–11.26%<=20%; vertical7.6–9.6%<=80%; rungs12.8–16.5%<=20%; junction8.71/100>=3 |
| BASALT_JOINTS, Unity Game view | FAIL | Batch2 all three views pass and remain recorded; the later valid batch3 az35 view has rung share21.1%>20%. Other batch3 shares19.6/17.0%; junction7.5916/100>=3. No valid failing view is excluded. |
| PLANT_SWAY_COLORS, authoring | PASS |21 actual PLANT meshes; roots<=.05, proper rising tips/phases; full props smoke checks B=0,A=1 and FBX |
| PLANT_SWAY_CAPS, authoring | PASS | Actual max R×.06yd:tuft.06,flower/agave.048,shrub.0288,tree.018,vine.06; fixed caps retained |
| PLANT_SWAY_CAPS, Unity GPU | PASS | Parent native fixture proof:15/15 original GPU/import gates plus both retained color/cap aliases pass; proof under lib/unity3 |
| MOW_BAND_CONTRAST, source PNG | PASS | Fairway5.1768%<=12%;Green4.1404%<=8% |
| MOW_BAND_CONTRAST, Game view | PASS | lib/unity3:fairway4.682149%<=12%,green3.775677%<=8%; each supported by600k+ pixels, repeat drift0 |
| Needle height/base | PASS |18m/4.5151m=3.9866;451tri; shape and taper gates pass; object scale1 |
| Needle inherited NO_ROCK_STRETCH_2X PCA | FAIL | Exact verifier rock_shape on default18m/4.5m,seed3:r3=.132107<.15. Wider17.6m/5.5m and16m/5.2m fixtures pass at.161966/.164008. Taper makes PCA narrower than its bounding width; measure every final seed. |
| Column width/sides | PASS |25 columns,0.8262–1.4884m,5/6 sides;16 chipped corners;25 distinct tops |
| Frozen scoring vertices | PASS |8 meshes,2347 vertices,maxdelta0 exactly |
| Cliff outline straight runs<=4m | FAIL |5.5675/5.0639/5.3913m on three loops; intervening plan points remain within10cm of their chord |
| Three-view renders saved | PASS |needle_az0/120/240.png,cliff_az0/120/240.png,basalt_az0/35/-35.png; all inspected |
| Full unchanged texture gate suite | FAIL |final_textures.log:131gates,eightFAILs; seven historical grass minima plus BASALT_BUILDER_WINDOWS |

The old texture-window FAIL is concrete: glow inside five supposedly glow-free Hole10 zones reaches7.6904% against<=.02%; C luminance-profile deviation.0488 against<=.01. Read-only Phase4 planning additionally found that every Basalt_E u-column contains glow (minimum.878906%>.02%), so no nonempty replacement vertical u-zone can pass with this tile. The exact inherited BASALT_PRISMS gate also fails:46.6706% of glow area is in unsuitable large components against<=10%. Hole10-only geometry/UV edits cannot repair these texture gates; preserve their FAILs until an authorized shared texture repair. Measurements and decoder provenance are in v3/hole10/constraint_measurements.json. The inherited verifier and all thresholds remain intact.

## APIs for later phases

```python
PL.build_needle(D, center, height_m=18.0, base_width_m=4.5,
                seed=0, name=None, surf=True) # -> {needle, surf}
L.build_postcard_cliff(D, style="needle", loops=None, seed=0,
                      replace=False) # style needle/split/crater; -> chunks
PL.build_column_wall(D, path, top_z, bottom_z=-1.6,
                     width_m=(.8,1.5), rows=1, closed=False, seed=0,
                     name="ROCK_WALL_V3", max_faces=490,
                     relief_m=.16, clip=None, max_span_m=20.0) # -> chunks
PL.add_cut_stone(mb,cx,cy,cz,sx,sy,sz,rng,yaw=0,broken=False)
PL.build_masonry_arch(D,center,facing_deg,span_m=7.0,height_m=10.0,
                     depth_m=None,broken=False,seed=0,base_rock=True,
                     vines=True,name=None,vine_seed=None)
```

Columns store lk_v3_columns metadata with diameter/sides/top/bottom/chip/vertex ranges. Clip callbacks reject whole cap footprints. A Crater caller must supply appropriate scoring-water exclusion and preserve all frozen nearby-lava chunk checks. The cliff function's sample spacing is not a4m silhouette PASS.

## Native fixture handoff

p1_fixture.fbx contains actual generated needle(x=-34),basalt(x=-11..11),one25m cliff section(x=34),and28×30m FAIRWAY/GREEN lawns(x=-18/+18). fixture_camera.json matches PostcardV3FixtureCapture's shots schema; fixture_layout_blender.json preserves original coordinates. FBX axis/sign and imported bounds must be checked by the native runner. plants_fixture.fbx contains all21 plant kinds for GPU sway. All positive fixture exports use export_look_fbx(colors_type="LINEAR").

The first fixture adapter double-converted PNG gamma and falsely reported basalt median92–94. test_scene.log is preserved. Corrected decoder provenance and all attempts are in DECISIONS.md; no art, lighting or threshold changed to correct that measurement.

Owned changed files and complete hashes are listed in changed_file_hashes.json. No hole builders, baseline/design files, verifier thresholds, runtime Unity source or installed hole models were edited by this subtask.

## Parent completion of Phase1, 2026-10-05 18:19 UTC
GATE P1 FAIL. Required native fixture sway is now15/15 original GPU/import gatesPASS plus both retained color/cap aliasesPASS. Actual imported Gameview lawn band contrast: fairway4.682149%<=12 with600800/618366 supported pixels; green3.775677%<=8 with610655/591887 supported pixels. Original repeat drift0, controlled shadow receiver exclusions36357/35571px; raw masks/images underlib/unity3. Each absent material remains unverified in its individual frame; together the two frames prove both caps.
Additional valid basalt views inlib/unity3 make the overall BASALT_JOINTS resultFAIL: az35 rung share21.1%>20%; other per-shot gatespass, aggregatedjunction7.5916/100>=3. Batch2 all3viewsPASS is retained, but does not erase the laterfailure. Cliff4m outlineFAIL also remains. Required 3-view stack/cliff/wall native renders exist datedthisrun. Shared sources/LookPNGs are nowstable; further shared-library repairs wait for Phase7. Phase2 follows this finite honest FAIL, with no gate relabelled or threshold softened.
