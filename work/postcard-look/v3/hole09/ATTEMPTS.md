# Phase 3 attempts

## Attempt 1 — FAIL

Only H9 scenery changed; original scoring snapshot measured delta0m. The actual three-bed shell has76 chunks and50,400 triangles, with maxskin z5.814m. All30 narrow ridge hummocks were placed with radius2.8–4.1m and authored height2.1–3.8m. The Phase1 ruin generated18 meshes,381 stones,23 wall-foot rubble stones and13 fallen cut blocks. Original plants: ridge76 / outer20 shrubs,6 agaves,20 flowers,140 old tufts; camera fringes142 tee /68 ribbon-mid /113 green-end /45 ruin /36 far-green /19 far-olive. Near camera budgets remained8496/3978/6966/2484 triangles.

Measured original tests passed material/UV/scoring, maxskin height, waterstack, sparse surf, shelf, no foam strip, water-ellipse avoidance and outward-facing shell. STRATA_JOINTS_STAGGERED FAIL:26% full-height joints, limit25%; block CV0.55, limit>=0.40. The unchanged skin_tortuosity helper assumes13 rows/four beds, returnedNone on10 rows/three beds, and the existing builder formatting raised TypeError before save. No stage, total triangle result, full verifier or exact final comparison exists for this failed attempt.

Decision for attempt2: restore four actual beds; keep the original utility/predicate/1.15threshold. Close more actual bed joints (closure0.55 vs0.40), retain the existing regular-grid negative control metadata, and use only far-field filler reductions to fund the additional cliff geometry. Authoring counts: ridge shrubs76 unchanged; outer shrubs20→16; ridge pebble filler44→36; far-green budget2000→400 triangles and far-olive1000→200. Tee8500, ribbon-mid4000, green-end7000, ruin2500 budgets,32 ruin grass clumps/130 tufts,60 wall-foot tufts and12 shrub skirts all remain unchanged.

Masonry batching will preserve whole disconnected stones, exact geometry/UVs/materials/flat normals,12m bounds and<=36% rock. Custom-normal meshes will remain intact to avoid re-encoding deltas found twice in the isolated control. No geometry/check threshold is softened. Actual attempt2 counts, ridges, outline and all gate outcomes will be appended after measurement.

## Attempt2 — FAIL before save

The four-bed skirt generated76 chunks /67,200 triangles. Actual near-fringe counts: tee142 (8469tris), ribbon-mid68 (3978), green-end113 (6966), ruin49 (2484). Far-green5 (396tris), far-olive3 (180). Ridge shrubs76, outer16, agave6, flowers20, old tufts140; ruin field130/32clumps, wall-foot60 and48tufts round12bushes remain.30 narrow ridges still placed. First genuine ruin batch:14→6 meshes,297 whole pieces and3885polygons preserved,11.995521m span,64.7047% minimum masonry/35.2953% maximum rock.

My wrapper scanned the original combined object list for the second category after the first batch had removed its source objects, causing ReferenceError. No arch batch, audits, total-triangle measurement, saved stage or final verifier exists for this attempt. Source lists must be classified before any deletion. Geometry settings and test thresholds remain unchanged for attempt3.

## Attempt3 early restart

The parent requested an explicitly unverified pre-batch checkpoint after this run had started. The early process was stopped before batching, then restarted with a checkpoint blend and resume metadata under checkpoints/. This is a scheduling restart, not a claimed geometry/check pass or a threshold change. The removed-reference wrapper fix and all attempt2 geometry remain unchanged.

## Attempt3 final geometry checks — FAIL on actual UVs

Native builder16/16PASS; full required verifier91/96PASS with LOOK_STILLS_TEXTURED and two real UV gates failing in both formats. Nine tall rock caps had17–41% area over4:1 anisotropy (cap15%); firstcut11 triangles covered342m2 of smear (largest108m2/worst201:1, caps15m2total/10m2each). Original holeQA27/27PASS, all13 independent ruin checks PASS in each format,0/394 unbroken cuboids in each format, and four installed/staged exact scoring comparisons PASS0m.

Decision: repair UV mapping only. Steep rock facets get real metre-density UVs in their own best-fit plane, preserving all vertices/faces/normals; frozen firstcut tops get unwarped world-planar rough UVs. Resume the saved unverified checkpoint, re-batch identically, and require original audits before export. No plant batching speculation or geometry/budget/check relaxation. A scratch resume adapter first omitted the verifier config's hole field and stopped before stage mutation; the adapter now supplies hole9.

### Count correction

The raw archived pre-repair verifier JSON has96 gates and91 passes, with the five listed actual failures. An earlier agent summary incorrectly stated99/104. Final records use raw JSON counts; the pre/final96 gate-name sets are identical. No gate was removed or changed.

### Fresh native evidence and scratch serializer repair

Root produced actual tee/approach/aerial frames from the frozen stage and a vs-reference sheet; this agent opened all three images. Original required stills verifier is rerun against gate_stills. The first scenery diagnostic JSON attempted to serialize a NumPy bool and failed; no geometry or gate calculation changed. The adapter casts that result to Python bool. Previous missing-frame verifier and adapter error logs are preserved as *.before_stills.

## Attempt3 final UV-only repair and complete checks

Native checkpoint resume repaired519 real rock facet UVs and771 firstcut top UVs without changing geometry/normals/plants. Builder 16/16 PASS; final required verifier 96/96 PASS, actual failures []. Original holeQA 27/27 PASS, independent ruin13/13 eachformat, cuboids 0/394 blend and 0/394 FBX; allfour exact scoring comparisons PASS at zero tolerance. Actual248868tri/1417meshes unchanged. Outer cliff straight-run diagnostic FAIL 14.844193m cap4m. Literal2-islands FAIL; fresh native image/masks/costs remain FAILunmeasured at this frozenhandoff. No checker threshold relaxed.
