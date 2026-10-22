# v3 proof-tool drafts

These are proof-only sources. Parent's P1 run compiled the original frame/fixture/importer/shader tools after correcting the iOS report-count fields from uint to int. It initially rendered 11 frames with incorrect camera axes, so required band support honestly failed. Parent corrected proof camera axes in a later run and reports the fixture GPU sway suite 15/15 PASS. The newly added course-model branch and frame-published cost harness are still uncompiled. No Xcode build was performed by this subtask. The Python band-field producer passed a 32px execution check; that self-test does not establish any visual gate. No installed FBX, frozen source, project setting, URP asset, or existing `.fbx.meta` was changed by this subtask.

## What is measured

`PostcardV3FrameProof.Capture(...)` uses the caller's original 900×1600 camera, render target, and full RGB pixels. The JSON records the camera, Unity version/API, frame number, and full-image RGB hash. Its ID renders replace material slots only on live scene instances and restore them in `finally`. Original photos and no-shadow photos remain available for inspection.

- Landmark selections have exact renderer membership, recorded paths/bounds/materials, and conservative opaque ID occlusion. Needle arch is separate from stacks; each stack renderer is measured separately. Split ruins are a semantic group. Crater cone is separate from the pillar. **The template intentionally has no pillar renderer paths or channel polygon: both remain FAIL until these selections are audited.** Whole-ocean coverage cannot count as channel-landmark height.
- Alpha cards occlude their entire geometry during ID renders. This can underestimate visible landmark/category coverage behind cards. It is not an exact opacity reconstruction. Original plant displacement is reproduced in the proof vertex shader so their depth is in the correct place. If this conservative mask is insufficient, fix the proof method; do not substitute projected bounds or color guesses.
- Cliff proof distinguishes vertical cliff-category fragments below frozen play height from grass tops at play height. It records both screen halves and whether a cliff fragment sits within 24px beneath a visible top fragment. A basalt volcano in the background is excluded by source-name selection. This proves side presence; it does **not** implement the separate Split >=80%-outline gate or prove continuous connection to the water by itself.
- Mow labels use the **actual authored band field** at interpolated triangle UV0 with the original material's BaseMap scale/offset. They do not rank pixels by brightness. Python imports the same live generator/noise/seed code and produces little-endian float32 fields, with a source hash and parameters. Generator PNG rows are top-first; field rows are flipped to Unity's bottom-first raw-texture convention. Regenerate these fields after the final texture-generation change, and retain metadata with the measured installed PNG hashes.
- Mow support excludes every RGB-changing shadow receiver in an original-vs-`Light.shadows=None` control, after restoring all lights. A repeated original render must be pixel-identical. Each categorical plateau is eroded by 1px and needs >=512 pixels. Both are fixed validity conditions in `v3/THRESHOLDS.md`. Caps use `abs(Ylight−Ydark)/Ylight <= .12` fairway, `.08` green; relative-to-mean gaps are diagnostics only. Every rendered material requires useful support or fails. An absent material retains an unverified/FAIL individual cap status, and is not claimed as measured; the overall phase gate must require a supported PASS for both materials across its fixture frames. These are whole-frame material means over supported authored plateaus; they are not a percentile gap. Alpha-card occlusion remains conservative, as disclosed above.
- `LK_BASALT` material-mask output supports the existing BASALT_JOINTS image measurement. The helper's basalt-mask `status` reports mask availability only. **It does not claim BASALT_JOINTS PASS.** Use the frozen thresholds in `THRESHOLDS.md` on the original masked RGB frame and retain component/skeleton data.
- Costs snapshot real UnityStats and ProfilerRecorder counters immediately before/after three original-camera renders, with GPU target readback and other cameras disabled. Zero, negative, inconsistent, or cross-source-disagreeing publication yields COST_MEASUREMENT FAIL. Raw snapshots are retained. A mesh/submesh estimate is never substituted for draw calls. Counters include render/shadow passes. The separate mesh-instance triangle sum is active instantiated geometry, not an exhaustive FBX-resource inventory; the original Blender/importer triangle cap is still required.
- Costs are Editor Metal measurements of the specified tee camera. They are not physical-iPhone performance numbers. If the installed Unity version publishes counters only at frame boundaries, the synchronous slices may FAIL and a separate isolated frame-counter harness is needed.

Unity's installed XML describes `ProfilerRecorder.CurrentValue` as immediate counter data and contains `Texture2D.SetPixelData`, `BuildReport.packedAssets`, and the target-build APIs. The [official ProfilerRecorder example](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Unity.Profiling.ProfilerRecorder.CurrentValue.html) supports capacity-zero current-value readers. The [official UnityStats source](https://raw.githubusercontent.com/Unity-Technologies/UnityCsReference/master/Editor/Mono/UnityStats.bindings.cs) shows aggregated frame counters, which is why raw before/after deltas must demonstrate isolation. The installed editor DLL exposes the same properties, but a Unity compile/run remains required.

## Approved physical-v3 scratch import route

Parent approved the new Editor symlink namespace for P1. The setup script does not launch Unity or copy installed course assets. It creates:

```
Unity/Assets/Editor/PostcardV3Scratch -> work/postcard-look/v3/unity-proof
Unity/Assets/Editor/PostcardV3Scratch.meta -> work/postcard-look/v3/unity-proof.folder.meta
v3/unity-proof/fixtures -> v3/lib/unity-inputs
```

Proof C#/shader sources are copied **within v3** into `unity-proof`. Keep `unity-inputs` limited to the finished fixture FBXs so Unity does not import the entire library's `.blend`/script/backup tree. New Unity-generated source/FBX/folder metadata physically reside in v3. `PostcardV3ScratchImporter` scopes baseline course import flags exclusively to this new namespace. Parent's P1 run successfully imported this symlink route (Unity emitted symlink warnings). Absence of a loaded prefab is still FAIL. Do not fall back to replacing `Resources/Course` before phase 6.

From the repository root, after the fixture exporter has completed:

```sh
R="$PWD"
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
env PYTHONDONTWRITEBYTECODE=1 python3 work/postcard-look/v3/proof-tools/prepare_scratch_import.py --root "$R" --fixture-dir "$R/work/postcard-look/v3/lib/unity-inputs"
env PYTHONDONTWRITEBYTECODE=1 python3 work/postcard-look/v3/proof-tools/make_band_fields.py --root "$R" --out "$R/work/postcard-look/v3/lib/band-fields"
```

Copy `proof_cfg.template.json` within v3 and replace the two float-field paths. For fixture-only captures, make landmark groups match the actual fixture names and set `playY` to the fixture's lawn elevation; no gameplay framing PASS is implied by the fixture. Camera config schema:

```json
{"shots":[{"name":"p1_mow","model":"Assets/Editor/PostcardV3Scratch/fixtures/p1_fixture.fbx","hole":8,"pos":[0,12,-28],"look":[0,6.56168,0],"fov":60,"requireBands":true}]}
```

Camera positions/look targets are **Unity world coordinates**, after the fixture FBX's exported axis/unit conversion. `PostcardV3FixtureCapture.Run` creates an unsaved in-memory scene, dresses the imported fixture with live GolfLook materials, applies the actual hole atmosphere, and uses a Game camera. It supports separate three-view stack/cliff/basalt captures and combined fairway/green fixtures. Only `requireBands:true` shots confer a runner band verdict; missing required support fails. Its runner PASS covers import/render plus required band checks, never BASALT_JOINTS or P1 as a whole.

The first actual import showed these exporter prefabs map Blender `(x,y,z)` to Unity `(-x,z,-y)`, including the root's axis conversion. Use the recorded renderer bounds to verify each camera target; do not change mesh transforms merely to make the fixture camera fit.

```sh
GOLF_V3_PROOF_CFG="$R/work/postcard-look/v3/lib/proof_cfg.json" \
GOLF_V3_FIXTURE_CFG="$R/work/postcard-look/v3/lib/fixture_camera.json" \
GOLF_V3_FIXTURE_OUT="$R/work/postcard-look/v3/lib/unity" \
bash work/postcard-look/heavy.sh p1-library-gameview "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.PostcardV3FixtureCapture.Run -logFile "$R/work/postcard-look/v3/logs/p1-library-gameview.unity.log"
```

The generic runner also supports **staged aerials** without installed replacement. In v3 `unity-proof/staged/`, create per-file symlinks named `hole_08.fbx` etc. pointing to the actual phase output; the generated alias `.meta` remains in v3. Use AssetDatabase paths `Assets/Editor/PostcardV3Scratch/staged/hole_08.fbx` in the same shot schema, set `requireBands:false` and **`buildCourseModel:true`** for aerial proof shots, and render them with hole 8/9/10 lighting. This branch uses the actual frozen Course.Postcards hole and HoleView.Build, removes only its original Course model, then invokes unchanged HoleView.BuildFromModel by signature-checked reflection. It therefore applies the real marker alignment, scale, material rules, ground colliders, and hidden gameplay placeholders. It retains the actual HoleView pin/cup objects, and records source SHA256, mesh AssetDatabase paths, raw aligned markers/transform, and a one-model/no-stale-baseline provenance gate. Alignment residuals are recorded without claiming the separate exact scoring gate. Camera positions in this branch are **the real audit/Game world coordinates**; do not apply the raw fixture's FBX sign flips. The raw P1 fixture branch is unchanged. This is a staged scenic render, not a GolfGame address capture. Existing GolfLookProbe can also use `GOLF_LOOK_PROBE_ASSETS=Assets/Editor/PostcardV3Scratch/staged` to call HoleView.BuildFromModel in memory.

### Fixture-only sway entrypoint

After the current Unity batch closes, copy **only** the new `PostcardV3FixtureSway.cs` draft into `v3/unity-proof/` and let the next serialized batch compile it. It validates private method/field signatures on the unchanged `GolfPlantSwayCheck`, imports only the supplied new PLANT fixtures, then invokes original ShaderCompiles, MaterialUnchanged, WindMath, PhaseDecorrelated, GentleContract, MeshGates(fixture list), and the active-pipeline GpuSuite. Missing APIs/assets throw an explicit FAIL. It retains every original gate line, including any shared-GPU FAILs, then emits clearly scoped fixture color/cap aliases. Original MeshGates measures imported color attributes and real pivot/tip weights against caps over the complete mirror loop; unchanged GPU rigs independently validate that formula against the actual GolfPlants shader, FBX strip chain, and shadow pass. This entrypoint does not consume or relabel installed-hole mesh checks. Original full-check reports remain separate evidence.

```sh
GOLF_SWAY_EXTRA_FBX=Assets/Editor/PostcardV3Scratch/fixtures/plants_fixture.fbx \
GOLF_SWAY_REPORT="$R/work/postcard-look/v3/lib/fixture_sway.txt" \
GOLF_SWAY_SHOTS="$R/work/postcard-look/v3/lib/fixture_sway_frames" \
bash work/postcard-look/heavy.sh p1-fixture-sway "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.PostcardV3FixtureSway.Run -logFile "$R/work/postcard-look/v3/logs/p1-fixture-sway.unity.log"
```

## Phase 5 integration

Use the proof-only `PostcardV3ProofMasks.cs` copy together with `PostcardV3StageModel.cs`; the original `PostcardProofMasks.cs` stays unchanged. The copy retains the original GolfGame.StartHole/address CameraRig flow, groups and category masks, and adds the same-frame FrameProof hook. Set `GOLF_PROOF_STAGE_ASSETS=Assets/Editor/PostcardV3Scratch/staged` for Phase 5 before installation; leave it unset for the normal installed Phase 6 branch. Only the settled HoleView's original Course model is removed, then unchanged BuildFromModel installs the staged prefab on the live instance. Provenance includes effective asset SHA, exact mesh source paths, aligned markers/transform, one live HoleView/model and absence of stale baseline meshes. These facts prove source/isolation, not the separate exact frozen geometry/marker gate.

`GOLF_PROOF_REPO_ROOT` selects the actual repository for output restriction when an approved isolated Unity project is used. Effective Unity project paths are recorded. Clone results never confer primary-project compilation PASS. The parent preserves actual protected-source compile FAILs and unrelated protected changes.

At authorized Phase 5 installation, `prepare_scratch_import.py --include-phase5` copies the drafts within v3; optional `--unity-project` points at an approved physical-v3 proof clone. Parent must control installation and serialize the following Unity compile/capture; this setup launches no Unity.

```sh
GOLF_PROOF_REPO_ROOT="$R" \
GOLF_PROOF_STAGE_ASSETS=Assets/Editor/PostcardV3Scratch/staged \
GOLF_V3_PROOF_CFG="$R/work/postcard-look/v3/proof/proof_cfg.json" \
GOLF_PROOF_CFG="$R/work/postcard-look/v3/proof/stills_cfg_12.json" \
GOLF_PROOF_OUT="$R/work/postcard-look/v3/proof/phase5_masks" \
GOLF_STILLS_SWAY=0,0,0 \
bash work/postcard-look/heavy.sh p5-staged-masks "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.PostcardV3ProofMasks.Run -logFile "$R/work/postcard-look/v3/logs/p5-staged-masks.unity.log"
```

The per-stack 64px statuses remain honest individual diagnostics. Required address framing aggregates any audited semantic landmark >=64px; Hole 9 can use ruins or the audited channel, Hole 10 cone or pillar. Both H8 fixed address frames additionally need at least two occlusion-tested visible stacks (>0 mask pixels), without inventing a 64px requirement for every background stack.

### Future frame-published cost harness

The parent's synchronous counter slices were all zero even on valid geometry. That evidence remains a COST_MEASUREMENT FAIL. The separate uncompiled `PostcardV3FrameCosts.cs` + `PostcardV3CostDriver.cs` drafts attempt the actual published-frame path requested for P5. Do not install them while another batch runs. They open the real Golf scene in Play mode, optionally use the same scoring-aligned staged swap before Phase 6, use normal StartHole/CameraRig fixed address framing, disable every other camera and all canvases/game dressing overlays, and leave the sole **automatic** Game camera targeting the same 900×1600/4×MSAA texture. They never call `Camera.Render()`.

`ProfilerRecorder.StartNew` enables collection with 16 frame slots. After three completed warm frames, a temporary PlayerLoop.Update callback reads `LastValue` in the next Update, before that frame's camera rendering. The original PlayerLoop is copied in memory and restored at completion; no Editor-assembly MonoBehaviour is added to the scene. SRP camera begin/end events identify the completed frame and detect other cameras. Exactly three consecutive completed sole-camera frames, positive counter samples advancing once per frame, stable triangle/draw/SetPass values, and agreement with any positive UnityStats source are required. Unavailable, zero, inconsistent, or unisolated publication is FAIL. A 30s no-publication timeout records FAIL explicitly; automatic Game-camera rendering in Editor batch mode is not assumed to work. The already rendered target is read back after measurement and saved with raw frame/counter/event data. The optional `GOLF_STILLS_SWAY=mph,deg,time` matches the still-capture hook and is restored afterward. These remain Editor Metal counters, not device runtime performance.

When P5 is ready, install **both** cost files under the approved golf Editor proof path and compile them. Use the six fixed address config (exclude landmark/aerial shots):

```sh
GOLF_COST_CFG="$R/work/postcard-look/v3/proof/gameplay_address_cfg.json" \
GOLF_COST_OUT="$R/work/postcard-look/v3/proof/frame_costs" \
bash work/postcard-look/heavy.sh p5-frame-costs "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.PostcardV3FrameCosts.Run -logFile "$R/work/postcard-look/v3/logs/p5-frame-costs.unity.log"
```

Only each tee's measured draw-call gate confers the <=250 verdict. SetPass has no invented cap. Actual render-triangle counts include shadow passes and are reported as counters; the separate per-hole FBX/imported geometry cap is still required.

## Safe iOS / Metal export

`BuildMenu.BuildIOS()` is unsuitable: its `TropicalArenaImporter.Prepare()` writes protected tennis/racket assets. The new exporter deliberately omits it and writes no PlayerSettings. It requires the existing Metal-only iOS API setting, enabled Golf scene, iOS module, explicit iOS build target, successful BuildPlayer, a generated Xcode project, no errors, and detailed packed-source evidence for the actual three installed golf shaders/FBXs. Missing evidence fails. Its verdict proves the Unity export stage; require the actual iOS device native compilation result as separate evidence before the overall P6 gate.

```sh
GOLF_IOS_OUT="$R/work/postcard-look/v3/ios/export" \
GOLF_IOS_REPORT="$R/work/postcard-look/v3/ios/export_report.json" \
bash work/postcard-look/heavy.sh p6-metal-export "$U" -batchmode -quit -buildTarget iOS -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.PostcardV3IOSExport.Run -logFile "$R/work/postcard-look/v3/logs/p6-metal-export.unity.log"
```

The stage-only exporter verdict is `UNITY_IOS_EXPORT`. It SHA-compares the effective project's required course FBXs and three shaders against the current primary repo, including when a proof clone is used. The overall `METAL_IOS_COMPILE` still requires the actual device compilation and retains any primary-project compile FAIL.

A faithful device sandbox is already prepared at `v3/ios/device/`: `Unity/Tools/build-integrated-ios.sh` and `project-unity.yml` are byte-identical copies. Script source and copy SHA256 are both `8ede694e5e16397264a952eaa08259a67f508bd13986a0e28d9f46c5162e2e67`. The copied `project.yml` only routes native source, plist, entitlement and bridging-header paths absolutely back to the real repository. A physical-v3 symlink `device/Unity/Builds/iOS -> v3/ios/export` resolves the untouched script's existing export check and overlay paths to the actual current export. Generated Xcode files remain beneath device; explicit DerivedData remains beneath v3. `prepare_device_build.py` prepares this layout and records source/copy/spec SHA equality; it does not export or build.

After a successful current export, the required repo build script is actually invoked through its identical copy:

```sh
env SPORTS_DERIVED_DATA="$R/work/postcard-look/v3/ios/device/DerivedData-p6" \
bash work/postcard-look/heavy.sh p6-device-script "$R/work/postcard-look/v3/ios/device/Unity/Tools/build-integrated-ios.sh" > "$R/work/postcard-look/v3/logs/p6-device-script.log" 2>&1
```

Report the copy invocation explicitly, its equality with the source script, and the actual exit/result. This subtask has not launched the device script or xcodebuild. A failed current export must not be replaced by the stale existing main `Unity/Builds/iOS` export.

Before P8, remove only the two new Assets symlinks (after confirming they still point to v3); preserve v3 proof outputs. Keep permanent golf proof-tool changes under the allowed paths. Do not stage `work/`, the temporary symlinks, or unrelated concurrent changes. The parent's strict protected snapshot currently has honest FAILs from unrelated concurrent multiplayer/locker modifications; none were touched here.

## Split aerial outline draft

`PostcardV3SplitOutline.cs` uses actual top/cliff ID masks and actual RGB-difference SURF pixels at the same 900×1600 aerial. Fixed pre-measurement support in `THRESHOLDS.md` is 2px Euclidean cliff adjacency from the frozen top edge and 6px SURF adjacency from the frozen sea-level base. Every hidden/backside/out-of-frame boundary pixel remains in the denominator, sampled at <=0.5px and deduplicated on the raster. Raw nearest-distance histograms (0..32,33=farther) and all masks are retained. SURF alpha-zero card geometry cannot count because it must also change actual RGB with SURF removed. Component counts are diagnostic; brokenness and the inherited foam cap stay separate checks.

The frozen hole09 baseline has **one** connected C-shaped outer loop with415 edges, not two island loops. `make_split_cfg.py` copies the exact SHA-backed baseline top boundary from `audit/split_frozen_boundary.json`, verifies the frozen design/blend sources, and classifies original directed edges into ridge/fairway with89 explicitly shared north/south join edges. No virtual closing shoreline is added; none of the415 edges is dropped. The draft records per-arc >=80% visibility and SURF-base presence, but cannot claim two independent island-outline masks; its strict `SPLIT_CLIFF_ISLANDS` status remains FAIL with this limitation explicit. Set `GOLF_V3_SPLIT_CFG` for a real Hole9 landmark/aerial in the v3 gameplay mask copy, or `splitCfg` on a generic staged aerial shot. The full-game copy calls it only for Hole9 aerial-named shots. Boundary projection temporarily uses the identical render target, so its viewport aspect exactly matches the actual masks.

## Strict runner draft

`v3/proof/runtime/run_proof.sh` preserves pre/install, installed Blender verification, Unity import/smoke/probe active+studio/tests,12 fixed stills+extras, studio comparison, original category masks, floors, PostcardCheck, mesh checks, pixel metrics, sheets, protected diff/guards and report. New optional costs/iOS steps use the new drafts. Every command exit/raw FAIL survives; missing metrics are FAIL. A new `PROOF_TAG` creates a new per-run directory and refuses overwriting previous evidence. All adapted reads/results/logs stay beneath v3. Legacy protected causal exemptions and unconditional pipeline assertions are retained as clearly labelled diagnostics only; the original-start strict protected gate is authoritative.

The510-path legacy protected-tree baseline was derived from original `start_sha.json`, using the same `.DS_Store/.meta/.jpg/.anim` filter, never current protected bytes. Its provenance is recorded; no start snapshot is reset. Current actual `v2/proof/install_holes.py` still uses v2 stage paths, so the draft refuses to install it until the parent adapts that actual installer to v3 at the authorized integration phase. The actual installer pre/install entrypoint is preserved; no alternate copier replaces it.

`GOLF_PROOF_UNITY_PROJECT` optionally selects an approved clone; default is actual `Unity`. ASSET_SCOPE/main-project compile provenance is separate from the measured golf framing gate. Shell, original/adapted Python sources and path adapter setup passed syntax checks only. Neither this runner, its installer, Unity nor Xcode was launched by this subtask.
