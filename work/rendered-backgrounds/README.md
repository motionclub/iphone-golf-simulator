# Rendered backgrounds (chat 2, 2026-10-17)

Every painted or AI-made panorama and backdrop is replaced by something we render ourselves:
- **Sky** — `RenderedSky.cs` + `RenderedSky.shader`. Single-scattering atmosphere (Rayleigh + Mie + ozone) integrated on the CPU into a 48×48 sky-view LUT. It is rebuilt only when the real directional light's elevation moves more than 0.2°. Sun or moon disc sits at the light. Procedural cirrus, stars and aurora. Open sea below the horizon. The equirect reflection RT replaces the painted `_SkyMap` / `_ReflectionMap` / `_SkyPanorama` textures. DreamEnvironment still drives `_Day/_Sunset/_Cloud` on the material.
- **Clouds** — `blender/clouds/build_clouds.py`: cumulus volumes (numpy SDF → OpenVDB) rendered in Cycles as six-way lightmaps plus ambient and alpha. `RenderedClouds.shader` relights them every frame from the real light. Cards sit at true 3D positions and drift with the wind.
- **Cloud sea** (skyscraper) — `blender/cloudsea/build_cloudsea.py`: a tileable stratocumulus field, six-way lit, on the venue's own cloud-sea mesh (`RenderedCloudSea.shader`).
- **Distant scenery** — `blender/karst/build_karst.py`: 6 tower-karst islands + 2 ranges.
  - Built at high res (SDF → VDB level set), decimated to 37,776 tris.
  - Baked 4096×2048 albedo+AO and normal maps.
  - `DistantScenery.shader`: real sun, sky ambient, per-vertex aerial perspective toward the rendered sky.
- **Far field** — all distant layers keep their true 3D direction (true parallax) but their depth is compressed into the camera's far clip (`RS_FarField`). Renderer bounds are 1e5, so no far-clip change is needed anywhere.

## Venues
`RenderedBackdrop.SkyProfile/Build` sets the per-venue profile and layout. `Live` = resort, skyscraper, volcano, golf, hub.
- Tennis resort: karst islands, clouds, sea horizon.
- Skyscraper: cloud sea + towering cumulus.
- Volcano: ash-haze sky with grey clouds.
- Golf: coastal holes get karst round the hole bounds + clouds. Magma holes (10, 16, 21–23) get the ash sky.
- Hub: the plaza dome and the rooms' domes are shaded by the rendered sky (golden-hour mood, sun at the real light) + clouds.

Dev switches:
- `RENDERED_SKY=0` restores every old painted path.
- `RENDERED_BG_VENUES=resort,...` overrides `Live`.
- `RENDERED_SKY_LOG=1` logs the LUT values.

## Files
- **Owned, installed by `tools/install.sh`:**
  - `Scripts/Environment/RenderedSky.cs`, `RenderedBackdrop.cs`
  - `Resources/Environment/RenderedSky/*` (5 shaders/hlsl + 9 Blender assets)
  - `Editor/RenderedBackgroundsCapture.cs`, `RenderedBackgroundsGolfCapture.cs`
  - `Tests/PlayMode/RenderedBackgroundsHubProof.cs` (ignored unless `BG_OUT` is set)
- **Hooks in partly-owned files:** `tools/patch_shared.py`, one call each, all tagged `// rendered backgrounds`.
  - DreamEnvironment sky section
  - TennisLook / Skyscraper / Volcano sky sections
  - Backdrop.cs islands
  - HubArt.SkyDome
- `install.sh` stages those as index version + hook only, so other chats' unstaged edits stay out of the index.
- **Rollback:**
  - Remove the hook lines; DreamEnvironment falls back to DreamSky by itself when `SkyProfile` is null.
  - Or empty `Live`.
  - The painted textures are still in Resources, unused at runtime, kept until chat 6 confirms.

## Tools
- `tools/capture_tennis.sh <out> <venue> [utc] [weather]`, `tools/capture_golf.sh <out> [holes]` and `tools/capture_hub.sh <out>` capture at 1920×1080, muted, in `/private/tmp/backgrounds-UnityClone`.
- `tools/gates.py <venue> <before> <after> [json]` computes the gates.
- `tools/compare_sheet.py` and `tools/sheet.py` make the sheets.
- `tools/sync_clone.sh` installs sources into the clone.
- `tools/sky_tune.py` is an offline LUT replica for tuning.
- Long jobs run with nohup; Blender scripts are resumable (the Mac restarted 3× on 10-17).
