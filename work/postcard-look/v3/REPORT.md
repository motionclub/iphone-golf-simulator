# POSTCARD LOOK REPORT

Overall **FAIL**; **33/41 PASS, 8/41 FAIL**. Eye review overrides numerical PASS. Earlier failed attempts remain recorded.

Installed run: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/proof/runtime/runs/p7_installed_round2`. Numbers, raw failures and hashes: [authoritative 41-row extraction](</Users/adnanyonathan/Documents/Codex/2026-10-05/ope/outputs/final_summary.json>).

| Gate | Result | Measured number |
|---|---|---|
| GUARDS_7_OF_7 | PASS | 7/7 PASS, 0 FAIL |
| PROTECTED_FILES | FAIL | Strict original-start protected changes: 61 |
| POSTCARD_LOOK_VERIFY_H08_ALL | PASS | 100/100; failed: |
| POSTCARD_LOOK_VERIFY_H09_ALL | PASS | 96/96; failed: |
| POSTCARD_LOOK_VERIFY_H10_ALL | PASS | 103/103; failed: |
| PLANT_SWAY_COLORS | PASS | 2960 objects; 58/58 meshes coloured; six installed blend/FBX verifier subsets PASS |
| PLANT_SWAY_CAPS | PASS | tuft 0.0591yd at20mph <= 0.06yd; flower 0.0472yd at20mph <= 0.05yd; shrub 0.0283yd at20mph <= 0.03yd; vine 0.0591yd at20mph <= 0.08yd; installed tree none coloured (fixture measured separately); 25 native gate lines PASS |
| BASALT_JOINTS | PASS | hole10_1_tee: 118274px, S0.092, Y31.0, glow0.0044, vertical0.0, rung0.119; hole10_2_approach: 88803px, S0.191, Y22.7, glow0.0278, vertical0.609, rung0.0; hole10_3_lavarim: 292436px, S0.121, Y28.0, glow0.0158, vertical0.772, rung0.0; junctions 159/2943px = 5.403/100 |
| MOW_BAND_CONTRAST | PASS | H8 fairway max9.576% (cap12%, minimum plateau5713px); H8 green max4.204% (cap8%, minimum plateau406468px); H9 fairway max8.070% (cap12%, minimum plateau12167px); H9 green max4.055% (cap8%, minimum plateau415208px); H10 fairway max9.857% (cap12%, minimum plateau1149px); H10 green max3.696% (cap8%, minimum plateau411433px); original repeat drift0px |
| SPLIT_CLIFF_ISLANDS | FAIL | Frozen closed boundaries1 (requires2); control drift0px; ridge_shore_with_shared_north_south_joins: cliff196/5036 = 3.892% (minimum80%); SURF364px; fairway_shore_with_shared_north_south_joins: cliff255/5380 = 4.740% (minimum80%); SURF490px |
| RUIN_NOT_BOXES | PASS | .blend: 0/394 unbroken cuboids (0.000%; cap20%); .fbx: 0/394 unbroken cuboids (0.000%; cap20%) |
| GAMEPLAY_FRAMING | FAIL | H08 tee: water1.7298%, landmark209px PASS, cliffPASS; H08 approach: water1.5933%, landmark198px PASS, cliffPASS; H09 tee: water0.4840%, landmark0px FAIL, cliffPASS; H09 approach: water1.5164%, landmark24px FAIL, cliffPASS; H10 tee: water0.2362%, landmark197px PASS, cliffPASS; H10 approach: water12.4008%, landmark98px PASS, cliffPASS; water minimum15%: all6FAIL; each landmark minimum64px, single alternative |
| NEEDLE_STACK_VISIBILITY | PASS | hole08_1_tee: 9 visible stacks (minimum2); hole08_2_approach: 4 visible stacks (minimum2) |
| GRASS_HUE_H08 | PASS | tee fairway hue69.6, clipped0.000%, support701531px; approach fairway hue68.6, clipped0.010%, support713760px; original hue60..76, clip<=5% |
| GRASS_HUE_H09 | PASS | tee fairway hue70.3, clipped0.000%, support861826px; approach fairway hue70.6, clipped0.000%, support861814px; original hue60..76, clip<=5% |
| GRASS_HUE_H10 | PASS | tee fairway hue69.2, clipped0.010%, support861846px; approach fairway hue66.1, clipped0.000%, support861930px; original hue60..76, clip<=5% |
| SHELF | PASS | hole09_3_ruin: shelf451px, brightness ratio0.865, brightest2% share0.00%; hole08_aerial: shelf2445px, brightness ratio1.15, brightest2% share1.00%; hole09_aerial: shelf8993px, brightness ratio0.997, brightest2% share0.24%; caps1.3ratio/10% |
| LAVA_ORANGE | PASS | hole10_1_tee: band91.15%, V0.822, dark1.06%, G>=250:0.00%; hole10_2_approach: band95.04%, V0.862, dark1.68%, G>=250:0.00%; hole10_3_lavarim: band93.29%, V0.858, dark2.55%, G>=250:0.00% |
| SMOKE_SOFT | FAIL | hole10_1_tee: changed43050px, dYp9578.47, max88.43, edgep9935.11/px on1540px; hole10_2_approach: changed51433px, dYp9562.64, max72.28, edgep990.95/px on3315px; hole10_3_lavarim: changed66810px, dYp9548.53, max57.11, edgep990.7/px on2263px; original caps p95>=8/max<=110/edge<=6; original FAIL retained |
| NO_PLANT_ON_SEA | PASS | hole8: 0/1675 plants on sea, 0 floating; hole9: 0/720 plants on sea, 0 floating; hole10: 0/565 plants on sea, 0 floating |
| NO_ROCK_STRETCH_2X | PASS | hole8: scaleMax1.45, anisotropyMax1.946; >2scale0, >2anisotropy0; hole9: scaleMax1.999, anisotropyMax1.346; >2scale0, >2anisotropy0; hole10: scaleMax1.4, anisotropyMax1.286; >2scale0, >2anisotropy0 |
| NO_FOAM_STRIP | PASS | Native gate PASS: all LK_SURF patches <=12yd long and >=7yd apart; numerical minimum spacing not emitted; original visual/mesh metric PASS retained |
| PATH_UNDER_BALL | PASS | 2 path meshes/14506 samples; top maximum1.15cm (cap1.5cm), above cap0; native ball visibility verified |
| GOLF_LOOK_SMOKE_BOTH_URP | FAIL | 158/161 native checks PASS; summaryFAIL; SMOKE_SOFT_INTERSECTION; [TennisURP] SMOKE_SOFT_INTERSECTION; [HeroBaseStudioURP] SMOKE_SOFT_INTERSECTION |
| POSTCARD_IMPORT_CHECK | PASS | 61 native gate lines/0failed |
| EDITMODE_POSTCARD_HOLE_TESTS | PASS | 37 tests PASS/0 FAIL/skipped0 |
| TOOLS_POSTCARD_CHECK | PASS | 50 design gates PASS; 37/37 tests PASS |
| SCORING_BIT_IDENTICAL | PASS | 12 installed/staged format comparisons; maximum vertex0m/marker0m; exact threshold0m |
| FBX_META_UNCHANGED | PASS | 3/3 original FBX.meta SHA hashes equal; 0 changed |
| TWELVE_CURRENT_GAMEVIEW_STILLS_AND_THREE_VS_REF | PASS | 12 exact current native900x1600PNG + 3 current/reference JPG; image identity PASS; eye review separate |
| TRIANGLE_CAP_H08 | PASS | 240380 installed FBX geometry triangles (goal<=300000; original<=250000) |
| TEE_DRAW_CALL_CAP_H08 | FAIL | 422962 rendered triangles, 406 draws (cap250), 38 SetPass; 3 stable published frames |
| TEE_TRIANGLES_DRAWCALLS_SETPASS_REPORTED_H08 | PASS | 422962 rendered triangles, 406 draws (cap250), 38 SetPass; 3 stable published frames |
| TRIANGLE_CAP_H09 | PASS | 248807 installed FBX geometry triangles (goal<=300000; original<=250000) |
| TEE_DRAW_CALL_CAP_H09 | FAIL | 313882 rendered triangles, 810 draws (cap250), 32 SetPass; 3 stable published frames |
| TEE_TRIANGLES_DRAWCALLS_SETPASS_REPORTED_H09 | PASS | 313882 rendered triangles, 810 draws (cap250), 32 SetPass; 3 stable published frames |
| TRIANGLE_CAP_H10 | PASS | 248314 installed FBX geometry triangles (goal<=300000; original<=250000) |
| TEE_DRAW_CALL_CAP_H10 | FAIL | 157787 rendered triangles, 525 draws (cap250), 30 SetPass; 3 stable published frames |
| TEE_TRIANGLES_DRAWCALLS_SETPASS_REPORTED_H10 | PASS | 157787 rendered triangles, 525 draws (cap250), 30 SetPass; 3 stable published frames |
| METAL_IOS_COMPILE | PASS | Primary Unity Metal-only export Succeeded, errors0; actual unsigned iphoneos Release build exit0; physicalDeviceRun=false |
| IOS_DEVICE_BUILD | PASS | Unsigned iphoneos Release exit0; initial exit0 retained; physicalDeviceRun=false |

Thresholds unchanged: fairway≤12%, green≤8%, water≥15%, landmark≥64px, outline≥80%, cuboids≤20%, geometry≤300,000/hole, tee≤250 draws. Retain stricter original checks; SetPass uncapped; scoring exactly0m; unsupported/stale measurements FAIL.

| Phase | Result | Completed work / limit |
|---|---|---|
| P0 | PASS | 389-line audit, full installed/staged table, three aerial comparisons and30 ranked differences; guards7/7, compile0 errorCS. |
| P1 | FAIL | Entry smokes26/26+115/115 and sway15/15; three-view fixtures saved. Basalt fixture rungs21.1%>20%; latest child checks3 FAIL/grass7 FAIL. Cliff H8 5.3545m/H9 5.1865m>4m; H10 unsupported FAIL. |
| P2 | PASS | Formal gate100/100, scoring0m, aerial and10 differences explained. Requirement2.2 UV scroll unfinished FAIL; eye remains NO. |
| P3 | FAIL | 96/96 verifier,27/27 QA, scoring0m, ruin0/394. One frozen boundary; cliff coverage3.892%/4.740%<80%. H9 draws794→810 despite renderers1415→1195; merging did not meet250. |
| P4 | FAIL | Fresh103/103 verifier,24/24 builder, basalt/lava PASS, scoring0m. Actual tee smoke edge35.11>6; synthetic intersection6.20>6. |
| P5 | FAIL | 12 play-mode frames, RGB drift0; cliff6/6, Needle stacks9/4 PASS. All six water shares<15%; Split landmarks0/24px<64. Gameplay camera/scoring bytes frozen. |
| P6 | FAIL | Original pre/install completed; final installed33/41 PASS,8 FAIL;101/101 inputs unchanged. Import61/61, EditMode37/37, exact scoring12/12; iOS build0. Native smoke emitted158/161 PASS (summary94/95), three copies of the same intersection failure. |
| P7 | FAIL | Stopped after third physical review: recognition0/3 YES, unwanted read3/3 YES, original differences0/30 fixed. Earlier failures/rethinks preserved; no fourth round. |
| P8 | PASS | 137 approved paths committed/pushed; forbidden committed paths0, unrelated index tuples/full flags preserved. Additional whitespace diagnostic FAIL:287 reviewed trailing spaces; frozen bytes retained. |

The original Phase0 protected snapshot was never reset. Narrow7/7 guards cannot clear broader changes. Concurrent changes remain preserved and count in the hard-rule result.
Hard-rule failures: Project-wide serialization FAIL: foreign Unity pairs/triples simultaneously observed; our Unity/Xcode admissions used unchanged heavy.sh. No root Unity overlap inferred from queued waits.; PROTECTED_FILES FAIL: Strict original-start protected changes: 61

Native 900×1600 captures use the primary Unity Editor Game view and actual StartHole/CameraRig/URP. Costs: one camera, three stable positive frames; Editor counters, no physical iPhone capture. Geometry and rendered/shadow triangles differ. Metal export/unsigned iphoneos Release build does not prove physical execution.

All three holes share [the complete 12-still contact sheet](</Users/adnanyonathan/Documents/Codex/2026-10-05/ope/outputs/sheet_all_12.jpg>). Their individual 4-frame sheets follow.

**Hole8**: NO recognition; unwanted box/plank/flat-strip/stripe/plastic read remains.
[Hole8 4-frame contact sheet](</Users/adnanyonathan/Documents/Codex/2026-10-05/ope/outputs/sheet_hole08.jpg>); [Hole8 versus reference](</Users/adnanyonathan/Documents/Codex/2026-10-05/ope/outputs/hole08_vs_ref.jpg>).

- P0#1 FAIL: Broad patchy grass bands.
- P0#2 FAIL: Low separated pads lack deep layered island mass; aerial tee cropped.
- P0#3 FAIL: Shallow horizontal cliff courses; outline4.936–5.354m>4m.
- P0#4 FAIL: Arch too small relative to islands.
- P0#5 FAIL: Thin separate spikes with tiny caps.
- P0#6 FAIL: Short waterfall, faint mist; UV scroll absent.
- P0#7 FAIL: Sparse faint hanging vines.
- P0#8 FAIL: Repeated large white ocean ovals; sparse foam.
- P0#9 FAIL: Narrow regular paving lane.
- P0#10 FAIL: Washed distant rocks; weak cloud depth.

**Hole9**: NO recognition; unwanted box/plank/flat-strip/stripe/plastic read remains.
[Hole9 4-frame contact sheet](</Users/adnanyonathan/Documents/Codex/2026-10-05/ope/outputs/sheet_hole09.jpg>); [Hole9 versus reference](</Users/adnanyonathan/Documents/Codex/2026-10-05/ope/outputs/hole09_vs_ref.jpg>).

- P0#1 FAIL: Long C-shaped low ribbon reads as parallel flat strips.
- P0#2 FAIL: Small sparse knolls lack eroded ridge mass.
- P0#3 FAIL: Shallow repeated cliff edges; outline5.186m>4m.
- P0#4 FAIL: Tiny aerial ruin; gameplay supports0/24px<64.
- P0#5 FAIL: Repeated mow bands remain conspicuous.
- P0#6 FAIL: Smooth dull rough lacks dense heather slopes.
- P0#7 FAIL: Sparse isolated shoreline foam.
- P0#8 FAIL: Straight parallel banks lack eroded coves.
- P0#9 FAIL: Detached small rocks lack massive outcrops.
- P0#10 FAIL: Flat sand ellipses lack soft rocky margins.

**Hole10**: NO recognition; unwanted box/plank/flat-strip/stripe/plastic read remains.
[Hole10 4-frame contact sheet](</Users/adnanyonathan/Documents/Codex/2026-10-05/ope/outputs/sheet_hole10.jpg>); [Hole10 versus reference](</Users/adnanyonathan/Documents/Codex/2026-10-05/ope/outputs/hole10_vs_ref.jpg>).

- P0#1 FAIL: Far wall remains a dark plank fence.
- P0#2 FAIL: Orange ticks/seams lack a deep natural joint network.
- P0#3 FAIL: Patchy mow strips; dull central cut.
- P0#4 FAIL: Low green slab lacks deep round pillar silhouette.
- P0#5 FAIL: Regular rim bands, tall rectangular panel, detached foreground columns.
- P0#6 FAIL: Clipped volcano flank lacks distinct background peak.
- P0#7 FAIL: Tee bead outline lacks readable stone platform.
- P0#8 FAIL: Dense repeated wormlike lava swirls.
- P0#9 FAIL: Revised parallel smoke still has detached star/card outlines.
- P0#10 FAIL: Flat elliptical bunkers lack soft rocky margins.

Files changed, grouped from the actual owned course diff/commit:

- Builders/libraries (22): hole08/09/10 builders/look, masonry/stone/QA, postcard/look/props libraries and checks, golf_look_textures.py.
- Installed assets (9): Three blend files, three FBX files and three original byte-preserved FBX metadata files.
- Course materials/textures/shaders (74): 63 Look texture/folder/meta files, nine shader/folder/meta files, two GolfLookVariants material/meta files.
- Golf Editor proofs (15): Seven PostcardV3 C#/meta pairs and GolfFlyoverCapture.cs.
- Brief/captures (17): Goal brief,12 native PNGs, three versus-reference JPGs and stills_stats.json. work/ excluded.

Commit **PASS**: f18dc4a1c95b534a72715d4c607fa788cdd9d2b0; 137 course paths, zero forbidden paths; exact raw/LFS payloads verified, unrelated ordinary index tuples/full flags preserved. Git whitespace diagnostic FAIL/exit2:287 reviewed trailing spaces retained without editing frozen bytes. Clean-checkout reproduction FAIL: excluded pre-existing runtime/core/design/checker prerequisites.
Push **PASS**: Explicit commit pushed to origin/newmapsandmenus, exit0;52/52 LFS objects uploaded,83MB. No force-push/rebase over others’ work.
Unfinished work and exact next step: Before another geometry merge, profile H9 tee batch owners at810 draws; the previous merge added16 draws despite fewer renderers. Resolve island/cliff silhouettes, six water masks, Split landmarks, Needle UV scroll, Crater tee smoke and all30 visual differences; then measure on a physical iPhone. Establish a quiet serialized run and reconcile protected-file ownership. Clean-checkout reproduction FAIL: excluded pre-existing runtime/core/design/checker prerequisites require separate work; this working-tree build does not certify a standalone course commit.

History: 6 original command failures; 37 raw FAIL lines. First P6 and prior eye scores remain separate.
