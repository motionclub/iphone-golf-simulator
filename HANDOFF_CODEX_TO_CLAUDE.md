# Codex to Claude handoff — 2026-10-16

Adnan stopped this run to switch agents because Codex usage was at 3%. This is a handoff, not a completion claim. No commits. I did not stage any new files in this run. There is a large pre-existing dirty/staged index: preserve it.

## Goal and authority

Implement BOTH `work/female-soulful/PROMPT_SHADER_FIXES.md` and `PROMPT_SHIRT_FIXES.md`, not just recommendations. Read AGENTS.md first, then those prompts. The explicit prompts override older garment-only restrictions.

Improve female skin, eyes, fabric, cap and shoes toward the neutral reference pack. Finish separate female tennis and golf tops that survive intended movement with one general construction/deformation solution. Preserve the accepted skirts, original face/mouth (no teeth changes), body/head/hair geometry, accepted arm/grip behavior, body bindings, original rig/clips, male appearance, customization/saved colors, maps, lighting and gameplay-camera framing. Keep audio muted. Phone performance is deferred by the user.

Reference pack: `ArtDir/style/alive/neutral-reference-pack-2026-10-15/START_HERE.md`. Actual sheets and clothes-with-weight board were viewed. The generated reference is appearance guidance, not a shader specification or calibrated camera. No new identity work.

Deliver in Unity AND native SceneKit. Actual screenshots and honest binary gates required. Stage only explicit reviewed task files; no commits, resets or broad git add. Do not blindly run either installer.

## Environment right now

- Repo: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`.
- Reuse the ONE running Unity Editor at `/private/tmp/female-soulful-UnityClone`, Unity 6000.3.24f1, Pipeline port7800. Do not launch batch Unity or another Editor.
- Last checked Editor: NOT playing, NOT compiling, temporary unsaved studio scene (`scene` path empty).
- Editor environment: `GARMENT_SLEEVE_SWEEP=0`, `GARMENT_CLOTH_PROTOTYPE=0`, `GARMENT_TOP_DQ=0`. These matter! Current successful-looking proofs use ordinary garment interpolation, while body/glove HeroArmSkinning is still enabled.
- Unity CLI lives at `~/.unity/bin/unity`. In this sandbox it reports no instances unless run with appropriate local execution permission. Escalated `unity status --format json` finds the existing clone. Every command needs `--caller plugin --skill unity-cli --project-path /private/tmp/female-soulful-UnityClone`.
- A CLI eval often times out after the Pipeline's 5-second main-thread limit while the operation CONTINUES and completes. Do not immediately repeat exports/captures. Check files, report timestamps and console. The CLI `--timeout` does not fix that internal server timeout.
- Explicit `AssetDatabase.Refresh()` is necessary. Auto-refresh was not importing changes reliably. Check actual DLL timestamps/compiler state before capturing. One early skin capture was pixel-identical because the shader had not refreshed; it was recaptured correctly.
- `set_autotick` is already enabled16ms. Actual tennis capture eventually completed correctly. `FemaleAliveCapture.Run()` was fixed to reset its static iterator/frame and clear the old golf recorder session flag; without that, stale capture state can stop the next recording.
- Blender MCP initially worked, then timed out at localhost9876. Background MCP variant could not find `blender`. Fallback used installed `/Applications/Blender.app/Contents/MacOS/Blender` with local execution permission. Sandboxed Blender crashed before reading the file; outside the restrictive sandbox it worked. No second Unity was used.
- Disk was ~374MB free at start, later system reclamation gave6GB; last check ~3.8GB. Keep proof small. I removed37MB clone crash reports and114MB redundant UNTRACKED failed-prototype JPG frames, preserving8 milestones per set, logs, sources and tracked files. Do not delete arbitrary data.

## What is done

### Female material candidate

Four shaders changed in clone `Assets/Resources/Tennis/Shaders/`, mirrored in `work/female-soulful/unity/`:

- `HeroLighting.hlsl`: stronger, broader female satin skin lobe, reduced female diffuse fill/ambient, no fixed tan pigment.
- `HeroFaceSkin.shader`: female skin branch, controlled highlight/fill, unchanged face geometry and existing expressions. Reflection initialization and safe blink pow handling.
- `TennisCharacter.shader`: explicit female eye material response/corneal highlight. Defaults retain male behavior.
- `TennisCloth.shader`: female rough diffuse/fiber response, finer neutral knit breakup, controlled grazing sheen; existing V1/V2 fabric-map ID/version encoding preserved. Golf cap flag2 suppresses extra textile breakup on existing white badge mask.

`FemaleGarmentFinish.cs` work+clone wires actual female materials:

- Sclera/Iris materials get `_FemaleSurface=1`, `_FemaleEyeRole`1/2, smoothness .84/.92, environment .34/.60.
- Cloth weave normal .10, thread .09, original weave density multiplied1.5 ONCE per material; sheen .32, smoothness .08, normal .75, wrap .18, rim .025.
- Female golf Acc_Cap uses `_FemaleSurface=2`; other female cloth1.
- Golf top `_Cull` restored to2, NOT old two-sided diagnostic0.
- Palette controls and tennis binding-color .88 logic retained.

Native counterpart is in `GolfArcade/Unity/MatchHeroSurfaces.swift` (unstaged new changes on top of previous staged changes). `MatchHeroData.swift` did not need another edit this run. New branches are female-only. Actual source Swift renderer compiled.

Material evidence:

- `proof/combined-fixes/material-before/`: fresh current-clone baseline, NOT historical original BEFORE.
- `material-skin/`, `material-full/`, `material-refined-tennis-top/`: successive actual Unity studio captures.
- `materials-before-after.jpg`: first full candidate; its fabric breakup was too coarse and was refined afterward. Do not present that first candidate as final.
- `skin-before-after.jpg`: refreshed skin difference. C# cloth parameters also changed, so not a pure isolated cloth experiment.
- `revisions/shader-improvements-20261016/MATERIAL_REPORT.md`: specialist report and backups.
- `proof/combined-fixes/native-material-diagnostic/`:8 actual SceneKit renders compiled from app sources, BUT historical garment exports plus explicitly temporary metadata. Provenance says this. Material-execution proof only, NOT final garment parity.

Material improvement is implemented and visibly more differentiated. User appearance acceptance/reference match is NOT established. Do not call the whole task finished just because shaders compile.

### Tennis top construction

Changed the independent pattern in `build_garments.py`: broader preserved shoulder strap region and higher rounded underarm opening (arm ellipsoid Z radius .125 instead of original .168; strap range .055..127, threshold .35). Body was a fit/weight source, not the garment surface.

Rebuilt editable `source/tennis_top.blend`, exported `source/tennis_top_export.blend` (ignored working file), `out/MatchHero_Female/unity/Kit_Top*`. Current export10213 vertices,19799 triangles,1K maps,7-bone torso binding, zero top pose shapes. Source export deviation about0.5mm. No degenerate triangles or nonmanifold outer edges in the checked export.

Top-only `FemaleGarmentInstall.RefreshTennisTop()` updates mesh, top palette names in the female prefab, top maps/corrective descriptor in the CLONE. It does not copy skirts. The clone now contains this tennis candidate.

Actual muted tennis scene captured idle, wave, joy and slump using current real gameplay sources and unchanged gameplay camera. Bounded capture stride12:

- `proof/combined-fixes/tennis-live/`
- `tennis-game-motion.jpg`
- Actual detail shown to Adnan: `tennis-live/wave/detail_00060.jpg`.
- Gameplay view: `tennis-live/idle/f_00060.jpg`.

It looks like a separate eased garment in those captures. Still do NOT infer all-motion pass from these4 modes alone; see stress report below.

### Golf polo construction — most important current candidate

After rejecting multiple deformation-only attempts, rebuilt NEUTRAL construction with higher armhole and fuller collar:

- Armhole center(.174,.004,1.317), radii(.067,.072,.064).
- Sleeve radii(.064,.058).
- Collar stand .015, fall .060, point .052, thick .0028, splay .45.
- New sleeve root Z1.257..1.366, versus old1.202..1.364. Root center is now about5mm ABOVE shoulder pivot, previously20mm below. Root circumference374mm, cuff359mm; old root469mm. This is a genuine construction improvement.

Current source `source/golf_top.blend`, `source/golf_sleeve_pattern.json`. Clean export `out/GolfKitHero_Female/unity/Kit_Top*`:10558 vertices,19724 triangles AFTER removing76 zero-area BUTTON-pole triangles. There were no degenerate cloth-shell triangles. `clean_polo_export.py` does the face-only cleanup without moving vertices; pipeline now invokes it after polo export. Checked source triangles were initially19800; helper removed76 button pole faces. Need refresh geometry audit JSON before final because its earlier golf entry still reports76degenerate/19800.

`pipeline.py` now exports golf maps at1024 and supports scoped coverage work. `bind_polo_harmonic.py` was rerun against the NEW clean `cage-prototype/unprojected-top.npz`, with construction-only weights and zero sampled corrective shapes. Do NOT rerun retired `bind_polo_sleeves.py` or `wrap_correctives.py`.

Top-only maps rebuilt. Coverage/contact regenerated against new source and existing body/motion samples with `CV2_PIECES=Kit_Top`; accepted masks for other pieces carried through. Old generated golf `correctives.npz` was copied to `revisions/combined-fixes/golf-old-correctives.npz` and removed from working output so an old pose bank could not contaminate the new source. This is generated data, not source animation deletion.

Clone has latest golf mesh/maps/coverage/contact and ordinary garment skinning. Latest cleaner proof:

- `proof/combined-fixes/golf-high-covered-linear/`
- `golf-high-covered-sheet.jpg`
- `golf-high-covered-linear/1.20-kit.jpg` shows a SMALL remaining body-colored underarm patch. Do not call it fully passing. Other typical poses are much cleaner than the prior ripped prototypes.

## Comprehensive stress review already run

NEW `unity/FemaleGarmentStressReview.cs` exists in work and clone Editor. It compiles. It measures the ACTUAL enabled generated surface when a sweep is active, not a hidden source top.

`proof/combined-fixes/stress-plain/` is a finished1048-sample run on BOTH new tops with all garment prototypes OFF:

-422 golf samples,626 tennis.
-12 samples per available clip plus0..170degree elevation, cross-body yaw, axial twist, torso twist, combined sweeps and bone-blended transitions.
-23 bounded images; `stress-plain-sheet.jpg` is the gallery.
-0 exceptions,0 nonfinite samples,0 duplicate-weld gap failures; max weld gap0.
-Report also records243 samples with area-collapse indicators and634 with transported-normal inversion indicators. Worst p95 absolute edge strain .654 golf /1.466 tennis.
-These metrics are NOT yet interpreted sufficiently. They include trims/inner surfaces/small edges; use of renderer.lossyScale versus bone-matrix scale may distort the baseline. An independent audit of their reliability was requested but was interrupted by Adnan switching agents.
-Do NOT dismiss the metrics or label all motions PASS. Inspect worst rows and actual images. The helper explicitly writes DIAGNOSTIC_REVIEW_REQUIRED, not PASS.
-`05-golf-anatomy_elevation-left.jpg` is the170degree overhead case. It looks substantially intact with ordinary new construction. The tiny underarm patch in the golf Drive representative still needs attention.
-Synthetic sweeps bypass gameplay IK and transitions blend bones, not the whole game state machine. Actual game proof is separate.

## What failed, and why

1. Original dense Unity Cloth / decimated cage experiments from prior handoff remain rejected. Cage edges were very uneven (median27mm,p95 70mm,max140mm), no meaningful bending/area control, cuff detail bypassed cage. Edge-distance preservation was not proof of a good garment.
2. This run tried `FemaleSleeveSweep.cs` + `build_sleeve_field.py`: source11-ring sleeve field, outer/lining/cuffs transported together. First center interpolation still took a collapsing LBS chord. It exposed body patches.
3. Shared anatomical collision field removed some patches but introduced severe crumpling. A24-pass stretch/bend/positive-area PBD version also visibly crumpled and penetrated. Those FAIL proofs are `golf-sweep`, `golf-shared-contact`, `golf-metric`, with corresponding sheet JPGs. Do NOT install.
4. After rebuilding high armhole, a cleaner shoulder-pivot slerp field was tested with contactMode0 (no collision/PBD). It preserved radial center distance but still exposed MORE body patches than simple harmonic skinning. `golf-high-pivot/` FAIL. Ordinary new construction currently looks better.
5. Underarm strip length analysis says fixed-root low-stretch cloth cannot satisfy full overhead reach without more fabric or garment-only root/side-seam travel. The new high root improves it considerably. If additional correction is truly needed, add proper gusset/ease or a continuous anatomical garment-only lift, NOT another per-animation bank or blind PBD scalar tuning.
6. First full material candidate was dirty/coarse. Refined shader and C# weave settings corrected that. First native material test produced magenta because a SceneKit shader helper lacked a declaration; fixed, then clean historical diagnostic renders succeeded.
7. Fresh final native tennis render initially failed honestly with 'Incomplete garment maps': native loader expects KTX, exporter writes PNG. This is now prepared for retry as below.

## Native state — important distinction

`GolfArcade/Unity/MatchHeroMotion.swift` has NEW experimental female golf sleeve kernel and HeroRig hooks from this run. It mirrors all experimental ring/contact/PBD modes and supports optional contactMode0. It compiles and missing/incompatible-field fallback was tested on real SceneKit/Metal: ordinary female golf skinner retained, male golf and both tennis variants unchanged. It requires matching vertex count plus `sourceToHero` metadata. No final reviewed golf field/export parity exists.

Current leading candidate uses ordinary harmonic skinning and therefore does NOT need this new runtime kernel. If that candidate passes, remove only THIS RUN'S experimental native additions/hooks and opt-in shipping integration; preserve previous accepted native work. Keep experiment files as nonshipping working evidence if useful. Do not ship hundreds of lines of failed solver accidentally.

Similarly, clone/work `MatchHeroLook.cs` currently has opt-in sweep wiring at female golf Kit_Top, PLUS older prototype and top HeroArmSkinning attachment. **Current env topDQ0 is masking a shipping-default pitfall:** unset environment currently permits top DQ again. If ordinary bindings are selected, explicitly remove/bypass top-only DQ/prototype attachment for the new female top; keep accepted BODY and GLOVE HeroArmSkinning untouched. Do not rely on Editor environment variables for production behavior.

Fresh real TENNIS native export is COMPLETE:

- `native-combined/assets/MatchHero_Female.json`, base/swing blobs and `_Rig.lzfse`.
- Current top10213 vertices and actual latest eye/fabric metadata (not temporary overrides).
- `native-combined/golden/`: fresh golden, blink and emote JSON.
- `logs/combined-native-tennis.txt`: exporter selfchecks all listed motions, deviations below0.001mm. Export cleanup emitted existing edit-mode Destroy warnings; rig export itself completed.
- Native Distance and Golf have NOT been exported for this pass.

Material specialist just completed conversion of15 fresh referenced tennis normal/mask/atlas PNGs to sibling KTX in `native-combined/assets` using Xcode TextureConverter. These are staging outputs only, not production installs. Full hashes: `native-combined/proof/tennis/map-compression.json`; log `map-compression.log`. Fresh actual native tennis render has NOT been rerun after conversion. Do that next.

Ready compiled actual-source renderer: `/private/tmp/female-material-lobby-render`.
Experimental kernel checker: `/private/tmp/native-sleeve-check`; source `native_sleeve_sweep.swift`. Only fallback is proven; no final deformer parity. It requires sourceToHero row-major16 floats from root.worldToLocalMatrix * top.transform.localToWorldMatrix if the sweep is ever revived. Do not mistake compilation/fallback for garment success.

## Files touched and uncommitted changes

Exact scoped status snapshot: `work/female-soulful/proof/combined-fixes/handoff-scoped-status.txt`. It shows M/MM/AM and untracked files. MM/AM means earlier staged content plus THIS run's unstaged edits; don't overwrite the index broadly.

Main source edits this run:

- Native `GolfArcade/Unity/MatchHeroSurfaces.swift` (material candidate), `MatchHeroMotion.swift` (experimental, possibly remove additions).
- Work `build_garments.py`, `pipeline.py`, new `clean_polo_export.py`, `COMBINED_FIXES_BRIEF.md`.
- Work+clone `FemaleGarmentFinish.cs`, `FemaleGarmentInstall.cs`, `FemaleAliveCapture.cs`, `FemaleGolfRuntimeReview.cs`, `HeroTurnaround.cs`, `MatchHeroLook.cs`.
- Four shader work mirrors+clone files listed above.
- New experiment `FemaleSleeveSweep.cs`, `build_sleeve_field.py`, `experiments/sleeve-field/golf_sleeve_field.json` and reports; do not ship failed candidate.
- New diagnostic `FemaleGarmentStressReview.cs`, `native_sleeve_sweep.swift`.
- Editable source tennis/golf top blends and golf sleeve pattern. Exported blends, NPZ/bin/maps, logs, fresh native staging outputs and proof captures under work (many ignored).
- Top mesh/material-map/coverage and tennis prefab palette updates in CLONE only.

No Unity production `Unity/Assets` installation this run. Production still has the earlier rejected garment candidate described in CURRENT_STATUS.md. Native Swift SOURCE files in repo ARE modified, but no new production native payloads installed. CURRENT_STATUS.md/GATE_RESULTS.md still describe earlier state and have NOT been updated for this run; this handoff supersedes them where newer.

Skirts: snapshot `proof/combined-fixes/skirt-protected.json` covers18 clone skirt mesh/map/coverage files; rechecked all18 unchanged. One early map bake regenerated Bottom output maps in the ignored work output accidentally, but they were NOT copied to clone or production. Preserve accepted installed skirt files; install TOP ONLY.

Protected accepted arm-source hashes and shader baseline: `proof/combined-fixes/clone-before-hashes.json`. No edits to HeroPoseSafety, HeroGripPolish, body HeroArmSkinning, HeroAccessories or HeroShoulderWeights in THIS run. Those clone sources may differ from older production because they are the previously accepted arm improvement; preserve them during guarded integration.

## Exact next steps

1. Read this handoff plus both task prompts. Inspect latest plain construction proof/stress report, not rejected cage/pivot shots. Interpret stress warnings and inspect worst actual poses. Resolve remaining golf underarm body patch and any real collapse. Keep body motion frozen. Prefer simple construction/bindings if it passes; don't reintroduce rejected solvers.
2. Decide whether ordinary harmonic binding suffices across intended motion range. If yes, make it the real runtime default for this female top (remove top DQ/prototype path), and remove only new experimental native kernel hooks/additions. If not, improve garment construction/ease or a general anatomical garment-side correction, not named-clip repairs.
3. Check true neutral collar/cuff/hem air gaps, underarms and straps against reference. Rerender material light/dark/saturated choices if geometry/maps change. Update geometry-audit.json after76 button-pole faces were removed.
4. Run actual muted GOLF game capture with fresh output path and all selected runtime flags. Inspect whole swing/overhead/transition at gameplay and close view. Real tennis proof already exists but rerun only if new changes require it.
5. Rerun fresh TENNIS SceneKit render now that15 KTX maps exist. Then export Female Distance and Golf serially from the same Editor after final garment selection. Compress fresh referenced maps into staging. Render both actual app/native motion sources; numerical native checks are helpful but actual renders required.
6. Run relevant existing female tests, shader error checks, protected hash checks and scoped geometry/motion checks. Device timing/memory remains deferred; do not request a device or claim mobile readiness.
7. Only after reviewed results: guarded explicit install into production Unity and native assets, preserving original face/accepted arms/skirts/male/defaults. Existing `install_unity.py` and `install_native_revision.py` span stale/prototype paths: DO NOT run blindly. Use current before-hash guards and explicit paths/new-file packaging.
8. Update CURRENT_STATUS.md, GATE_RESULTS.md, manifest/proof inventory and final inline images. Honest FAIL lines for anything unresolved. Stage explicit reviewed files only. NO COMMIT.

## Useful commands

From repo root. Unity commands require local permission to reach the existing Editor.

```sh
unity status --format json
unity command eval --caller plugin --skill unity-cli --project-path /private/tmp/female-soulful-UnityClone --format json 'UnityEditor.AssetDatabase.Refresh();return "refreshed";'
unity command console_status --caller plugin --skill unity-cli --project-path /private/tmp/female-soulful-UnityClone --format json
```

Render latest ordinary golf diagnostic (do not overlap another Editor task):

```sh
unity command eval --caller plugin --skill unity-cli --project-path /private/tmp/female-soulful-UnityClone --format json 'System.Environment.SetEnvironmentVariable("GARMENT_SLEEVE_SWEEP","0");System.Environment.SetEnvironmentVariable("GARMENT_CLOTH_PROTOTYPE","0");System.Environment.SetEnvironmentVariable("GARMENT_TOP_DQ","0");System.Environment.SetEnvironmentVariable("GOLF_RUNTIME_REVIEW_OUT","/private/tmp/claude-golf-review");GolfArcade.EditorTools.FemaleGolfRuntimeReview.RunTopOnly();return "done";'
```

Stress review (new fresh proof output; helper writes diagnostic result, not automatic PASS):

```sh
unity command eval --caller plugin --skill unity-cli --project-path /private/tmp/female-soulful-UnityClone --format json 'System.Environment.SetEnvironmentVariable("GARMENT_STRESS_OUT","/private/tmp/claude-garment-stress");System.Environment.SetEnvironmentVariable("GARMENT_STRESS_MODE","both");System.Environment.SetEnvironmentVariable("GARMENT_STRESS_IMAGES","24");GolfArcade.EditorTools.FemaleGarmentStressReview.Run();return "done";'
```

Actual muted game capture uses `FemaleAliveCapture.Run()`. Set ALIVE_MODE=tennis|golf, ALIVE_OUT absolute fresh folder, ALIVE_DETAIL=1, ALIVE_CAPTURE_STRIDE=12. Golf additionally needs FILM_OUT fresh folder, FILM_AUDIO=0, FILM_COURSE=cliffside, FILM_HOLE=12, FILM_COMPRESS=0, FILM_TAP_SKIP=1. Do not reuse an existing FILM_OUT with f_*.jpg. Verify advancing frameCount and muted audio; entering Play alone isn't evidence. Helper stores a temporary worn golfer look before selecting female, preserving device saved look.

Rebuild/export TOP ONLY if geometry changes (do not rebuild skirts):

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python work/female-soulful/build_garments.py -- tennis_top
/Applications/Blender.app/Contents/MacOS/Blender -b work/female-soulful/source/tennis_top.blend --python work/female-soulful/pipeline.py -- export MatchHero_Female Kit_Top tank2 work/female-soulful/source/tennis_top_export.blend res=1024
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python work/female-soulful/build_garments.py -- golf_top
/Applications/Blender.app/Contents/MacOS/Blender -b work/female-soulful/source/golf_top.blend --python work/female-soulful/pipeline.py -- polo_export GolfKitHero_Female
```

After golf export, replace cage-prototype/unprojected-top.npz with that fresh clean top NPZ BEFORE running bind_polo_harmonic.py. It reads that file, not current output. Do not mismatch new pattern and old NPZ. Harmonic uses Blender Python/mathutils:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python work/female-soulful/bind_polo_harmonic.py
CV2_PIECES=Kit_Top /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python work/female-soulful/pipeline.py -- maps GolfKitHero_Female
CV2_PIECES=Kit_Top /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python work/female-soulful/pipeline.py -- cover GolfKitHero_Female
```

`FemaleGarmentInstall.RefreshGolfTop()` copies mesh/correctives ONLY; copy reviewed Top_N/M PNG and Top_hide/contact bytes explicitly to matching clone Resources/Golf/KitsV2/Female paths, refresh. `RefreshTennisTop()` also handles maps and prefab top bone names. Both use CV2_SRC=<repo>/work/female-soulful/out. Never invoke broad installer over stale output.

Fresh real tennis native render ready to retry, Metal permission required:

```sh
LP_ASSETS="$PWD/work/female-soulful/native-combined/assets" LP_FRAMINGS=head,torso,body /private/tmp/female-material-lobby-render "$PWD/work/female-soulful/native-combined/proof/tennis" default,s3
```

Native compile if actual sources change:

```sh
xcrun swiftc -module-cache-path /private/tmp/female-soulful-swift-modules -parse-as-library -o /private/tmp/native-sleeve-check GolfArcade/Unity/MatchHeroData.swift GolfArcade/Unity/MatchHeroSurfaces.swift GolfArcade/Unity/MatchHeroMotion.swift work/female-soulful/native_sleeve_sweep.swift
```

Native export via Editor: set MH_LOCKER_SEX=Female, MH_LOCKER_OUT=<repo>/work/female-soulful/native-combined/assets, MH_LOCKER_GOLDEN=<repo>/work/female-soulful/native-combined/golden, MH_LOCKER_REPORT to a task log. Run MatchHeroLockerExport.RunDistance() then RunGolf() SERIAL, checking complete outputs and actual errors after internal CLI timeouts. Run() tennis already completed.

No agent is supposed to continue implementation after Adnan's stop request. All specialist agents were told to stop; final in-flight texture conversion completed successfully and no render was started afterward.
