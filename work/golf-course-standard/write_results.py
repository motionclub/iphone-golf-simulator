from pathlib import Path
import json,hashlib,shutil,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[2];w=Path(__file__).resolve().parent
out=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-2/outputs');proof=root/'ArtDir/screenshots/golf_course_standard'
for name in ['final-play-results.xml','final-edit-results.xml']:
    assert ET.parse(w/name).getroot().get('result')=='Passed',name
baseline=json.loads((w/'baseline-sha256.json').read_text())
protected=[p for p in baseline if p.endswith(('.fbx','.blend')) or p.startswith(('Unity/Assets/Resources/Course/Look/','Unity/Assets/Resources/Course/Surface/')) or p=='Unity/Assets/Scripts/Course/Hole.cs']
assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==baseline[p] for p in protected)
rows=[json.loads(p.read_text()) for p in (w/'proof/release').glob('*audit.json')];targets=sorted([r for r in rows if r['hole'] not in [8,9,10]],key=lambda r:r['hole'])
report='''# Golf course standard — implementation and validation

Implemented October 6, 2026 in the golf simulator’s existing `final-build` working tree, following the saved plan and the user’s instruction to proceed automatically. The rollout is enabled for all **13 selectable non-Postcard holes**. The procedural Meadow holes 1–3 also use the shared ground materials. Postcards 8–10 remain the reference.

[Open the before/after viewer](golf-course-review.html) · [Implementation plan](GOLF_ALL_COURSES_POSTCARD_STANDARD_PLAN.md) · [Course metrics](course-metrics.csv)

## Delivered

- Shared runtime catalog for grass, green, fringe, rough, sand, cliff, rock, masonry, paths, water, surf, falls, basalt, lava, ash, snow, ice, desert, wood, bark, foliage, and painted props.
- The existing Postcard texture and shader library is reused. Eight new specialty surfaces provide 16 deterministic, seamless 512-pixel color/normal maps. iPhone import settings use ASTC 6×6; mipmaps, repeat sampling, and anisotropic filtering are enabled.
- World-scaled ground textures, steep-bank projection, broad mowing bands following the centerline, and optional triplanar normal detail for new rock materials. Postcard shader defaults retain their previous behavior.
- Coastal, volcanic, alpine, desert, woodland, jungle, and links lighting profiles. The actual runtime backdrop sea and Magma lava lake use the shared materials.
- Feathered shoreline foam on visual mesh copies, and the existing Postcard plant atlas, tuft meshes, wind weights, and batching on suitable rough. The new tuft layer is capped at 320 instances / 18,000 triangles per hole.
- Static material batching excludes moving sails and animated water. Per-hole material, texture-map, and visual-mesh ownership supports cleanup and individual rollback.
- Five views for all 16 holes: tee, approach, putting, aerial, and gameplay. Four 4-second camera sweeps cover Island Carry, Frostbite Fjord, Temple Falls, and Obsidian Slab.

No original hole FBX or Blender source was rewritten. Layouts, scoring definitions, physics, characters, and native menus were not changed by this implementation.

## Gate results

| Gate | Result | Evidence |
| --- | --- | --- |
| Catalog coverage | **PASS** | 13/13 selectable targets; three procedural Meadow holes also build with the shared catalog. |
| Materials and profiles | **PASS** | 18/18 focused Edit Mode tests. Required specialty maps load; profile objects are independent of the Postcard reference. |
| Ground and hazards | **PASS** | Final Play Mode comparison covers all 13 targets: ground samples, green height grid, lies, hazards, obstacle data, collider counts, and the windmill remain equal before/after. |
| Original geometry | **PASS** | All 233 captured collision meshes across 16 holes have identical world-space vertex/triangle hashes. All 33 protected FBX/Blend files match the snapshot. `Hole.cs` is unchanged. |
| Material lifetime | **PASS** | Repeated transitions retain only the active hole’s named materials and one course-coordinate map after normal frame-end disposal. This checks new runtime ownership, not total GPU residency. |
| Visual proof | **PASS** | 80 final stills and 80 baseline stills, 16 comparison sheets, plus 384 moving-camera frames. Steep grass stretching and coastal rock emission found in pilots were corrected before final capture. |
| Postcard reference | **PASS, with animated-frame limits** | Source assets unchanged; reference tee views preserve appearance. Baseline-to-final RGB mean absolute differences: 0.0933/255 for 8, 0.0120/255 for 9, 0.00054/255 for 10. See the animation limits below. |
| Existing gameplay checks | **PASS for 7 broad checks; one baseline failure** | Tree collisions, all-hole review, looking toward the pin, controller maps, TV HUD routing, and both native-session flow tests pass in Unity. The legacy next-shot test times out identically on the untouched baseline. |
| Target-device performance | **FAIL — not measured** | No iPhone is connected. Editor counters include additional cameras/passes and cannot certify the 250-draw / 300,000-rendered-triangle / 16.7 ms device target. |
| iOS build and native app rendering | **FAIL — unavailable here** | The installed Unity 6000.3.24f1 has only MacStandaloneSupport. iOS Build Support is absent, and the remembered iPhone is offline. No updated native app binary was built or installed. |

The implementation and local validation are complete. Device performance and native shipping gates remain open; this report does not certify an iPhone release.

## Measurements

Final rendering used **Unity 6000.3.24f1, URP, Metal, Apple M5**, at 900×1600 for stills. New-hole course meshes intersecting the tee camera frustum range from **39,398 to 139,476 triangles**, with **31–92 material passes** before shadow passes, characters, UI, and other cameras. These are mesh inventories, not measured GPU draw counts. The whole Editor frame counters are included separately in the CSV and are not directly comparable to a single-device gameplay budget.

Referenced course-texture runtime allocations range from **10.72 to 18.35 MiB** for the upgraded holes. Textures are deduplicated within each report. This excludes hero/UI resources and does not measure the entire retained cache or actual iPhone GPU residency; the proposed shared-residency budget is still provisional.

| Hole | Collision meshes | Obstacles | Referenced texture MiB | Camera mesh triangles | Camera material passes |
| --- | ---: | ---: | ---: | ---: | ---: |
'''
for a in targets:
    report+=f"| {a['hole']} | {a['colliders']} | {a['obstacleCount']} | {a['textureBytes']/1048576:.2f} | {a['cameraMeshTriangles']:,} | {a['cameraMaterialPasses']} |\n"
report+='''
## Reference-frame limits

The static Postcard surfaces and sky match. Animated flags, ball presentation, waves, water highlights, and particles are not locked to an identical Unity effect clock. A repeat run of the unchanged final implementation establishes that the large aerial water differences are normal capture variance: hole 8 changes 31.44% of pixels by more than 10/255 against baseline and 33.50% against a repeat; hole 9 measures 16.61% versus 17.54%. Putting views also contain different flag poses and ball presentation. These images support visual preservation, not pixel identity for every dynamic object. Detailed numbers are saved in `reference-differences.json`.

## Test accounting and baseline issues

The broad Edit Mode run returned **86 passed / 3 failed**. All three failures reproduce with identical messages on the untouched source snapshot: `CliffsideIsStillHoleSevenAndTheNumbersDoNotClash` still expects one Cliffside hole; `NoForcedCarryOverTheLimitAndDryFairwayShortOfEach(8)` and `(10)` reject existing Fringe lies. The final focused material suite is **18/18 passed**.

The broad Play Mode run returned **7 passed / 2 failed**. The new comparison initially sampled temporary primitive colliders before their scheduled removal; the harness now waits for normal cleanup. Its final run passes for all 13 targets, material disposal, and Meadow 1–3. The other failure, `NewHolesPlayTests.TheNewHolesPlay` timing out while waiting for the next shot, reproduces unchanged on the baseline.

Three unrelated older Play Mode source files referenced retired character APIs and prevented compilation. They were excluded only from both disposable capture projects (`NativeSessionTests`, `PlayerBaseTests`, `StandardCharacterGameplayTests`); the main project’s files were preserved. Runtime source compilation passes, with the existing `TennisGame.audio` hiding warning. Unity’s editor search-index exception appears in both baseline and upgraded captures; all capture jobs finish successfully.

## Files and rollback

Runtime code is in `Unity/Assets/Scripts/Course/GolfCourseLook.cs`, `GolfCourseAtmosphere.cs`, `GolfCourseFringe.cs`, and `GolfCourseFoam.cs`, with scoped integration in `HoleView`, `GolfAtmosphere`, `LavaWorld`, surface batching, edges, and the ground/rock shaders. Assets are in `Unity/Assets/Resources/Course/Standard/`. The source generators are `blender/scripts/golf_course_standard_textures.py` and `golf_course_standard_props.py`.

`GolfCourseLook.Enabled = false` restores the pre-upgrade routing. Add a hole number to `GolfCourseLook.DisabledHoles` to disable just that hole. Postcard-only material defaults are unchanged. Clear/rebuild the current hole after changing a switch.

Original snapshots, compiler logs, NUnit XML, and complete material audits are under `work/golf-course-standard/`. Full-resolution images and comparison sheets are in `ArtDir/screenshots/golf_course_standard/`. Isolated Unity projects and compiler caches are excluded by the scratch directory’s `.gitignore`. No commit, push, deployment, or app installation was performed.
'''
(out/'GATE_RESULTS.md').write_text(report);(proof/'GATE_RESULTS.md').write_text(report)
for n in [12,17,19,21]:shutil.copy2(out/f'course-review/hole{n}_motion.mp4',proof/f'hole{n}_motion.mp4')
for file in ['final-play-results.xml','final-edit-results.xml','edit-results.xml','play-results.xml','baseline-edit-results.xml','baseline-play-results.xml']:
    shutil.copy2(w/file,proof/file)
shutil.copy2(w/'reference-differences.json',out/'reference-differences.json')
plan=root/'ArtDir/environments/GOLF_ALL_COURSES_POSTCARD_STANDARD_PLAN.md';s=plan.read_text().replace('This is an implementation plan; migration has not begun.','Implementation proceeded automatically on October 6, 2026. All 13 selectable targets and procedural Meadow materials are now migrated; local validation is complete. iPhone performance and native build verification remain open because the device is offline and iOS Build Support is absent. See `ArtDir/screenshots/golf_course_standard/GATE_RESULTS.md` for results.');plan.write_text(s);shutil.copy2(plan,out/plan.name)
html=out/'golf-course-review.html';s=html.read_text().replace('<div id="stats"></div>','<div id="stats"></div><video id="motion" controls muted playsinline style="display:none;width:100%;max-width:450px;border-radius:12px"></video>')
s=s.replace('const d=data.find(r=>r.hole===+n);','const film=document.querySelector("#motion");film.pause();film.style.display=[12,17,19,21].includes(+n)?"block":"none";if([12,17,19,21].includes(+n))film.src=`course-review/hole${n}_motion.mp4`;const d=data.find(r=>r.hole===+n);');html.write_text(s)
print('Saved final report, plan status, review viewer, clips, and evidence.')
