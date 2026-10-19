# Frame budget: 60 fps at 1080p or more (2026-10-17)

Adnan: *"need to make sure everything is working to get to 60 fps with at least 1080p quality or higher as well, make sure that is understood everywhere"*.
Every chat's work must fit inside this. Owner: chat 1 (`work/frame-rate-60b`).

## The rule
- **Frame rate:** 60 fps held: median ≥ 58, no 30 fps lock, on the phone and on the AirPlay/external TV. 120 Hz is optional (ProMotion phone without a TV, setting on).
- **Resolution:** the frame the player sees is never drawn below **1920×1080**.
  - TV: a real 1920×1080 swapchain (`NativeSportsSession` caps a larger TV at 1920×1080, never below).
  - Phone: native resolution (Player setting *Resolution Scaling Mode* = Disabled; URP `renderScale` = 1).
- **Quality step-downs** (`TennisQuality.StepDown`, called by `TennisFrameGovernor` / `LuminousCoastFrameBudget`) may drop effects only: MSAA 4→2→1, SSAO, shadow cascades, shadow distance (to 25 m minimum), LOD bias. They **never** lower the render scale or the frame rate. This is enforced by `FrameRate60bEditTests.StepDownNeverLowersTheResolution`. Until 10-17 the step-down set the render scale to 0.85, which drew a 1080p TV at 918 lines.
- **The only path below 60** is iOS's own *Critical* thermal state: Player setting `thermalStateCriticalIOSFPS: 30`. It protects the phone from overheating; *Serious* stays at 60.

## Per-frame budget (16.67 ms at 60 fps)
These are targets for the High tier (A17/A18-class iPhone) drawing the TV at 1920×1080 plus the phone's controller UI. Keep about 25 % headroom for heat and AirPlay encoding.

| | budget | notes |
|---|---|---|
| CPU main thread | **≤ 8 ms** | game logic + animation + `HeroPoseSafety`/clearance + garment correctives + UI |
| CPU render thread | **≤ 6 ms** | SRP batcher on; ≤ 400 SRP batches / ≤ 250 draw calls per camera |
| GPU, TV view 1080p | **≤ 11 ms** | everything below added up |
| · environment (terrain, court, venue, sky/backdrop) | ≤ 5 ms | chat 2's rendered skies and backgrounds live here |
| · characters (2–4 heroes, skin/cloth/hair shaders) | ≤ 2.5 ms | each base 35–50 k tris + garments ≤ 20 k; skinned verts ≤ 120 k on screen |
| · shadows | ≤ 1.5 ms | 1 cascade tennis, 2–4 golf (`TennisQuality.GolfShadowDistance`) |
| · post (bloom, colour, SSAO on High only) | ≤ 1.5 ms | |
| · UI / HUD / intro graphics | ≤ 0.5 ms | |
| GPU, phone view (controller, or the game without a TV) | ≤ 3 ms with a TV / ≤ 11 ms alone | the phone must not render the 3D scene while a TV is the screen |
| Visible triangles | ≤ 1.0 M per view | |
| Texture memory | ≤ 600 MB resident | ASTC on device; no uncompressed 4K maps |

Animation and pacing rules (what chat 1 checked across the game):
- Every played clip is keyed every 1/60 s (an FBX's header must say 60 fps: Unity's *Resample Curves* resamples at the file's frame rate, so 60 Hz keys in a 30 fps file still play at 30 Hz).
- `.fbx.meta` clip ranges (`firstFrame`/`lastFrame`) are in frames: double them when a file goes from 30 to 60 fps.
- Baked tracks (camera paths, signature shots, lobby bone tracks) are sampled with a smooth curve or at ≥ 60 Hz, never joined by straight lines between 30 Hz samples.
- Nothing updates every other frame (no 30 Hz timers, network positions without interpolation, or SpriteKit/SceneKit views at 30 fps).

## How to check your work against it
- **Editor proxy (anyone, any time):** `FrameRate60bTests.RuntimeHoldsSixty`. It runs windowed and muted, sets the Game view to 1920×1080, and gives median fps per scene in `runtime.jsonl` plus a 1920×1080 screenshot. It must stay ≥ 58 median after your change. The Editor on this Mac is not the phone: treat a drop of more than 1 fps, or any new hitch, as a signal to profile.
- **No 30 Hz motion:** `FrameRate60bTests.NothingStepsAtThirty` + `work/frame-rate-60b/scripts/no_step.py`. Duplicate frames < 5 % and parity ratio < 2.5 on every tracked mover.
- **Clip key rate:** `-executeMethod GolfArcade.EditorTools.FrameRate60bInventory.Run`. Every shipped clip should have `moving_curves_at_30hz` = 0.
- **Device (the real budget):** Unity Profiler (development build, autoconnect) for the CPU numbers; Xcode GPU Frame Capture for the GPU ms on the TV view. **Not run yet:** no device and no AirPlay measurements exist for this budget.

## Measured in the Editor (2026-10-17, this Mac, 1920×1080 Game view, muted)
See `GATE_RESULTS.md` (RUNTIME / RES_1080) for the per-scene numbers.
