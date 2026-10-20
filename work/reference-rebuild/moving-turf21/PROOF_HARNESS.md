# Focused moving-turf desktop proof harness

Candidate files only. No Unity process was launched and no Assets file was edited by this subtask. Runtime candidate compiles with the current full 219-source runtime response. `GolfMovingTurfProofRunner.cs` compiles against that candidate runtime and current editor references with zero warnings; `compile-proof.log` is empty on success.

## Root integration and launch

Install the latest runtime `GolfCoastalTurf.cs`/patch and copy `GolfMovingTurfProofRunner.cs` into `Unity/Assets/Scripts/Course/` (entire file is UNITY_EDITOR guarded; attaching a MonoBehaviour from the Editor assembly is prohibited). The filename matches the runner MonoBehaviour for direct Unity import; the static entry point is `GolfArcade.EditorTools.GolfMovingTurfProof.Run`.

Set `GOLF_MOVING_TURF_CONFIG` to the absolute `proof-config.json` path and invoke that entry point using the root's existing serialized Unity execution workflow. The harness opens the existing Golf scene, enters play mode, starts the real GolfGame and exits with code 0 only on a completed PASS; exceptions/timeouts write FAIL JSON and exit 1. `VISUAL_MOVING_TURF` unset keeps pilots12/14; `all` allows only the existing Supports nine routes. `VISUAL_MOVING_TURF=0` plus `proof-control-config.json` provides matching static-tee control captures with moving checks appropriately omitted. Control still checks exact physics, material lifetime, caps and no Flight rebuild.

The root owns actual execution/approval. Use a separate run for moving and static control so queued submissions, material cloning and dressing audits are isolated. Existing root canopy/material changes may remain installed in both, provided their own synchronous physics dressing gate passes. Compare portable collider mesh/transform/shape and obstacle hashes between those runs with the existing audit tooling; runtime Unity instance IDs differ between processes, so whole JSON equality is used only within each actual hole instance.

## Actual samples and production movement

Each pilot gets seven separate camera renders: tee, tee plus0.5m X (same station), tee plus4.1m X (one coarse crossing), 45% distance along the authored centerline (fairway), near the end of that same centerline (approach), return to fairway, and return to tee. The golfer, ball and actual address camera remain visible; shot UI is hidden for the images. Images should be reviewed for rooted grass, ball/club readability and actual role exclusions; automatic invariants do not replace that visual review.

Every address calls only the existing public `game.DropBall`. This establishes actual Aim state, position, club and golfer. The harness disables game/rig ticking to freeze that address, frames the real production CameraRig, and leaves GolfCoastalTurf enabled. It never calls `RefreshForAddress`, private turf `LateUpdate`, or `Camera.Render`. This catches a cached-owner/state/BallPosition wiring failure that explicit manual refresh would hide.

A runner with execution order32000 observes the production turf after its ordinary LateUpdate. The normal camera renders to a persistent RenderTexture. `RenderPipelineManager.endContextRendering` reads that completed texture and writes one image per actual `Time.frameCount`, after the full camera context/stack. The next address starts on another frame. No WaitForEndOfFrame dependency (which can stall batch-mode coroutine captures), and no multiple-address submission queue in one frame.

## Automatic checks and outputs

`moving-turf-proof.json` records actual placed/rendered/LateUpdate frames, the addressed ball and snapped patch center, production rebuild counts, calls/raycasts, visible LOD/resident counts, material counts, retained cells, regenerated comparison counts and timing. `rebuildOccurred` disambiguates actual measured crossings; `rebuildMilliseconds` is0 on unchanged-station poses, while `lastRebuildMilliseconds` preserves the runtime's most recent rebuild measurement. These are desktop CPU durations inside only the production pool rebuild, not image/audit overhead or any phone-performance claim.

The harness verifies the private cached GolfGame is exactly the real ancestor; expected snapped PatchCenter matches the actual addressed ball; 0.5m shift causes no rebuild/query-diagnostic changes; 4.1m shift causes exactly one rebuild; every retained block and Cell keeps object identity and exact root/matrix/bounds/rough/surface hashes; the returned fairway compares regenerated cells; owned material IDs/counts remain exact; resident/LOD caps stay640/48/96. Regeneration compares existing block admission count too, intentionally exposing any return-station coverage drift due to capacity admission.

Before and after each address it uses the existing GolfVisualPhysicsGate Capture implementation against the actual model root. Full original collider records, meshes, transforms, collision settings, obstacles, surface data, ground samples and windmill values must be exactly identical inside the same hole instance. It saves these audit JSON files plus the existing pre/post visual-dressing gate. The latter must be present and PASS before address movement is accepted.

After the image stations, it enables actual GolfGame Update and performs the existing public `StrikeToward` from the tee. The late witness must observe real Flight for multiple4m X/Z stations with an unchanged production RebuildCount. Physics and owned materials must remain exact through the shot. A post-flight Result/Aim rebuild is permitted. The watchdog measures240s per hole by editor wall clock and handles stalled camera/flight pipelines as FAIL.

The source stats and images support the narrow pilots only. Path/bunker/shore/green-edge visual checks and optical proof on the remaining seven existing supported routes still belong to the root's later serialized rollout. No general scenery proof or phone test is included.
