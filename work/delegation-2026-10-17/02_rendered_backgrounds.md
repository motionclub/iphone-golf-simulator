# Chat 2 — Replace painted backgrounds with ones we render ourselves

You are one of 5 parallel chats in this repo; see `work/delegation-2026-10-17/README.md` for who owns what. Read `AGENTS.md` and `CLAUDE.md` first, then the memory notes `tennis-venues-skyscraper-volcano`, `hub-country-club-restyle`, `golf-postcard-look-pass` and `menu-hub-walkable-plaza`.

## Goal
Adnan: "painted backgrounds are too obvious, we need to just render them ourselves and figure out a way to keep the same level of quality." Every distant background has to read as a real place lit by the same sun as the court/course and moving correctly with the camera. Quality must be at least what the paintings give now, and the iPhone must hold 60 fps.

## What exists (verify, the list may be incomplete)
- Painted/AI panoramas: `Course/Resort/SkyCoastalSmall.png`, `SkyVolcanic.png`, `Tennis/Premium/SkyRooftop.png` (+ `CloudTops`, also wrapped onto skyscraper facades), `Tennis/Environment/SkyPanorama`, `Course/Look/Sky_Crater_C`, `Sky_Split_C`, `Environment/LuminousCoast/ArchipelagoSky.png`, `SummerSky.png`.
- Shaders: `TennisSky`, `TennisCoastalSky`, `TennisVolcanicSky`, `TennisRooftopSky`, `GolfResortSky`, `CoastalSky`, `DreamSky`, `Golf/StormSky`.
- Code: `TennisLook.cs`, `TennisVenueBuilder.Skyscraper.cs` / `.Volcano.cs`, `GolfAtmosphere.cs` (per-course `SkyTexture`), `DreamEnvironment.cs`, `LuminousCoastPilot.cs`, `Course/Backdrop.cs` (Higgsfield→Tripo islands and boats), `TennisReferenceMatch.cs`. `TennisPresentation.cs:209` notes that long lenses smear the painted backdrop.
- Hub preview videos (`Resources/Hub/Previews/*.mp4`) show venues. Re-record them only if a venue changes and they now look wrong.

## Do
1. **Inventory and diagnose.** For every venue (tennis resort, skyscraper, volcano, 3 golf courses, plaza/hub, Luminous Coast/dream worlds) and every camera that sees the background (gameplay, serve/ball cam, intro flyovers, result/emote cams, lobby), capture what the player sees. Name what gives the painting away: no parallax, sun direction/colour mismatch, blur/smear, horizon seams, baked clouds, scale, stretching. Write a sheet of captures with notes.
2. **Choose the approach per layer** and write it down before building:
   - Sky dome: an analytic/procedural sky (gradient + sun + scattering) driven by the scene's actual sun, plus clouds rendered by us (layered noise dome, or cloud impostors rendered from 3D) that can drift.
   - Mid/far scenery (islands, skyline, volcano, mountains, sea, trees): real 3D low-poly geometry with aerial perspective/fog matching the near scene, LODs and impostors (rendered from our own 3D) for the farthest layer.
   - Pre-rendered pieces are allowed only if *we* render them from our own 3D scenes with the game's sun and palette (e.g. Blender Cycles → HDR cubemap/impostor atlas), and only for things with no parallax at gameplay distances.
3. **Pilot one venue end to end.** Use the main tennis resort court (coastal). Show Adnan before vs after at gameplay camera, serve cam and one intro flyover. Then roll out to the other venues one at a time, showing each.
4. **Mobile budget.** Measure GPU frame time before vs after in the Editor (frame debugger draw calls, triangles, overdraw) and on the phone if one is available. Use the phone build recipe in memory `phone-build-recipe`. Hold 60 fps; chat 1 depends on that.
5. Remove the painted textures from the runtime path once each venue passes. Keep the files until chat 6 confirms.

## Preserve
Court/course geometry, turf, gameplay-camera framing, character lighting/materials and hero rim light. Change the world sun/fog only where the sky needs it to match, and confirm characters don't change: a character before/after crop must be pixel-close.

## You own
Sky shaders/materials, panorama textures, distant-scenery meshes, `Backdrop.cs`, the sky/backdrop/distant sections of the venue builders, `GolfAtmosphere` sky fields, `DreamEnvironment` and `LuminousCoastPilot` sky parts. Not characters, clips or garments.

## Gates (work/rendered-backgrounds/GATE_RESULTS.md, binary, per venue)
- NO_PAINT: no painted/AI panorama texture is sampled at runtime in that venue (shader/texture audit).
- PARALLAX: a 2 m camera dolly moves the scenery layers by the amounts their depth predicts (measured on 3 landmarks).
- SUN_MATCH: the sky's sun azimuth/elevation is within 3° of the directional light, and cloud/landmark shading agrees with it.
- LONG_LENS: no smear or texel blow-up at the longest lens any camera uses (crop proof).
- QUALITY: side-by-side sheets at each camera, Adnan-reviewed, or listed as awaiting review.
- PERF: GPU frame time delta ≤ +1.0 ms on the Editor proxy; device is PASS or NOT RUN.
- CHAR_SAME: character crops before vs after differ by mean ΔE ≤ 2.

## Rules
Branch `10/13`, big pre-existing staged index: preserve it. Stage only your reviewed files; no commits, resets or broad `git add`. Unity only in your own APFS clone (`cp -cR Unity /private/tmp/backgrounds-UnityClone`), one Editor, `GOLF_MUTE=1`. Headless Blender, not the MCP. Disk ~38 GB: keep proof small and delete nothing that isn't yours. Install into `Unity/` only files you own; shared scenes/prefabs go as a patch plus install script to chat 6. Push proof images to Adnan every ~15–20 min. Needs from other chats go in `work/delegation-2026-10-17/REQUESTS.md`.
