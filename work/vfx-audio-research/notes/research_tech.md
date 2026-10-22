# Tech research — game-wide VFX + audio + haptics (2026-10-17)

Scope: iPhone party tennis + golf, Unity **6000.3.24f1**, URP **17.3.0**, Metal, 60 fps at ≥1920×1080 on a TV via AirPlay (mirroring / external display). The phone is the controller. Soft-plastic toy look.

Legend: **[S]** = stated by the linked source. **[I]** = my own inference or general industry knowledge, not verified against a source in this pass. **[R]** = read from this repo.

Repo facts that shape the choices [R]:
- `Unity/Packages/manifest.json`: URP 17.3.0 + `com.unity.modules.particlesystem`. **No VFX Graph, no Cinemachine, no FMOD/Wwise, no Feel.**
- `Unity/ProjectSettings/AudioManager.asset`: `m_DSPBufferSize: 512` (Good latency), `m_RealVoiceCount: 32`, `m_VirtualVoiceCount: 512`, `m_OutputSamplingRate: 48000`, `m_AudioFoundation: 0` (Classic).
- `Unity/Assets/Plugins/iOS/GolfHaptics.mm` + `GolfHitFeel.h` already run one long-lived `CHHapticEngine` (`playsHapticsOnly = YES`, `autoShutdownEnabled = NO`, stopped/reset handlers). They play a **local phone "knock" through System Sound Services** because that path ignores the AirPlay route, and they can **delay haptics by the TV lag** (`Haptics.Play(cue, intensity, delay)`). The research below supports that design. Build on it rather than replacing it.

---

## 1. VFX: VFX Graph vs Shuriken on iOS/Metal, URP 17

### 1.1 VFX Graph status on mobile (sourced)
- Requirements are compute shaders (`SystemInfo.supportsComputeShaders`) and SSBOs in the vertex stage (`SystemInfo.maxComputeBufferInputsVertex > 0`). **VFX Graph 17.3 is still "not out of preview for URP" and "not out of preview for mobile platforms."** No OpenGL ES. [S] https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.3/manual/System-Requirements.html
- Unity staff, 2025-12-01, in a thread about 6000.2 on iPhone 17 and Pixel 6: VFX Graph is "Vulkan only and not officially supported on mobile at the moment." The iOS breakage went away after re-saving all VFX assets. [S] https://discussions.unity.com/t/vfx-graph-not-visible-on-android-and-ios-after-upgrading-from-2022-3-50-to-6000-2/1697740
- In a 2022.3 thread (2024-06/07), a team shipping VFX Graph on iOS and Android reported "serious problems". Workarounds were power-of-two data sizes and driving effects with gradients instead of enabling and disabling VisualEffect components. [S] https://discussions.unity.com/t/vfx-on-mobile-with-unity-2022-3/951037
- Unity staff, 2023-12: still in preview on mobile, and the `maxComputeBufferInputsVertex` limit is easy to hit. [S] https://discussions.unity.com/t/visual-effect-graph-urp-compatibility-and-performance-on-mobile/935454
- Which iPhones: every A11+ iPhone supports Metal compute, and all iOS-17/18-capable devices are A12+. Hardware is not the blocker; Unity's support status is. [I]
- VFX Graph instancing: on by default. It batches effects that share one asset, so they share buffers and simulation steps. It does **not** apply to Output Mesh or Output Event Handlers. GPU events gained instancing in 17.1 (Unity 6.1). Per-effect opt-out is `VisualEffect.allowInstancing`. [S] https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.2/manual/Instancing and https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.2/manual/whats-new-17-1.html
- Performance (inference): VFX Graph's strength is large GPU particle counts (10k–1M). Our toy-hit effects are small: a few to a few hundred particles per burst. At that size Shuriken's CPU cost is negligible, and VFX Graph adds fixed compute dispatch and buffer cost per system. [I]

**Verdict:** Use **Shuriken (Particle System)** as the game-wide VFX system. VFX Graph on URP/iOS is officially preview in Unity 6.3, its bug reports are recent, and we don't need its scale. [I, based on S above]

### 1.2 Shuriken GPU instancing of mesh particles
- Requirements: Renderer mode = **Mesh**, "Enable GPU Instancing" ticked, an instancing-capable shader, and `#pragma target 4.5` for custom shaders. The particle system writes all instance data into one big buffer. Billboards are not instanced. [S] https://docs.unity3d.com/6000.3/Documentation/Manual/PartSysInstancing.html
- **Shader Graph particle instancing only arrives in Unity 6.6.** An official post dated 2026-06-23 says 6000.6.0a8 Particle Lit/Unlit templates default to GPU instancing. Particle nodes (Transforms, Color, Texcoords, AnimFrame) need `#pragma instancing_options procedural:ParticleInstancingSetup`. Fixes to the Particle Color + Mesh + instancing path in URP Particles Lit were **backported to 6000.3.19f1**, so our 6000.3.24f1 has them. URP particle shaders have only just gained a ShadowCaster pass (6.6). [S] https://discussions.unity.com/t/shuriken-particles-shader-graph/1669355/11
- Consequence for 6000.3 [I]: for instanced **mesh** particles, use the built-in URP `Particles/Unlit`, `Particles/Simple Lit` or `Particles/Lit` shaders. Otherwise write a small hand-written HLSL toon particle shader using `UnityParticleInstancing.hlsl` / `ParticleInstancingSetup`. Don't rely on a Shader Graph particle shader instancing on 6.3.
- URP Particles Lit page: Soft Particles, Camera Fading and Distortion **all require the URP Depth Texture**. Flip-Book Blending "might reduce performance". "For optimal performance, disable unused features." [S] https://docs.unity3d.com/6000.3/Documentation/Manual/urp/particles-lit-shader.html

### 1.3 Overdraw on Apple TBDR, blend modes, soft particles
- Apple WWDC20 10632 ("Optimize Metal Performance for Apple silicon Macs", which covers the same TBDR GPU family as iPhone): hidden-surface removal is pixel-perfect and order-independent for **opaque** geometry. Submit opaque first, then alpha-test/discard/depth-feedback, then translucent. Don't interleave them. With translucent geometry, overdraw depends on HSR efficiency. Store only the attachments you need. [S] https://developer.apple.com/videos/play/wwdc2020/10632 and WWDC20 10602 (Apple GPU TBDR) https://developer.apple.com/videos/play/wwdc2020/10602
- What this means for the toy look [I]:
  - **Opaque mesh particles** (solid plastic chunks, confetti, stars, puffs as low-poly spheres, toon-lit) are almost free in fill rate because HSR removes hidden fragments. They also match the soft-plastic toy look best. Make them the default.
  - **Alpha-test/discard** (stepped toon dissolve, erosion with hard step) disables the early-HSR fast path for those draws. It is OK in small screen areas. Keep it after opaques, which URP's AlphaTest queue (2450) already does.
  - **Alpha-blend** quads (smoke, glow, dust) are the classic mobile fill-rate killer at 1080p. Keep them small, few and short-lived, and avoid stacks of full-screen sprites. Prefer additive or premultiplied with tight mesh shapes (custom particle meshes trimmed to the texture alpha) over full quads.
- Soft particles / camera fade / distortion need the Depth Texture. URP produces it by a **CopyDepth after opaques** or a **depth prepass** ("Force Prepass"), and the docs warn that the prepass costs memory and performance. [S] https://docs.unity3d.com/6/Documentation/Manual/urp/urp-universal-renderer.html. On TBDR, off-tile intermediates mean extra passes and main-memory traffic. [S] https://docs.unity.com/en-us/engine/6000.3/manual/xr/graphics/on-tile-rendering.md
- Recommendation [I]: design VFX so they **don't need soft particles**. Use mesh particles that intersect the ground cleanly, with ground decals as flat quads lifted 2–5 mm. Check whether the Depth Texture is already on for other features before deciding. If it's off, keep it off for VFX.
- Unity's mobile optimization e-book (Unity 6 edition, "75+ tips") covers particles and overdraw. Use the Scene view Overdraw mode and the Frame Debugger. [S] https://unity.com/en/resources/unity-e-book-optimize-your-mobile-game-performance

### 1.4 Flipbooks, LOD, force fields, pooling
- Flipbooks: Texture Sheet Animation. URP "Flip-Book Blending" smooths low frame counts but costs performance [S, above]. For a toy look, use **stepped flipbooks** (no blending) at 8–16 frames on a 512² or 1024² atlas, ASTC 6×6 or 8×8 [I]. Hand-drawn stepped frames also read as "stylized" rather than "cheap".
- Particle LOD (Shuriken has no built-in LOD) [I]: use `Max Particles`, a scalable burst count multiplied by a global quality scalar, Culling Mode = Automatic for looping ambient systems, and `ParticleSystem.Stop()` plus a pool instead of Destroy. For the TV camera, rate-limit ambient emitters by distance.
- **Particle System Force Field**: shape plus Directional, Gravity (with focus), Rotation (vortex, attraction), Drag (scaled by size/velocity) and Vector Field (3D texture). Particle systems opt in through the External Forces module. [S] https://docs.unity3d.com/6000.0/Documentation/Manual/class-ParticleSystemForceField.html. Useful for "ball suck-in" or confetti swirls on a perfect hit. Keep it to 1–2 fields active [I].
- Pooling: `UnityEngine.Pool.ObjectPool<T>(createFunc, actionOnGet, actionOnRelease, actionOnDestroy, collectionCheck, defaultCapacity, maxSize)`. [S] https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Pool.ObjectPool_1.html. It has existed since 2021.1, with defaults collectionCheck=true, defaultCapacity=10, maxSize=10000 [I, from memory]. Prewarm by `Get()`-ing N then `Release()`-ing N during the loading cover, so the first ace never instantiates. Set `collectionCheck=false` in release builds. A Shuriken-specific trick: one pooled system per effect type, fired with `Emit(EmitParams, count)` at the hit point. That gives zero GameObject churn, and each emitter stays a single draw (or a single instanced draw for meshes) [I].
- Prewarm shaders too: `ShaderVariantCollection.WarmUp()` or `GraphicsStateCollection` (Unity 6 PSO tracing) during the loading cover. Otherwise the first effect of each type hitches on Metal pipeline creation [I; GraphicsStateCollection is a Unity 6.0+ API].

### 1.5 Unity 6 / 6.3 features that matter
- Unity 6.3: shared Render Graph foundation for URP and HDRP, a **Render Graph Viewer connectable to device players (incl. mobile)**, and **Metal support for NativeGraphicsJobsSplitThreading**. [S] https://docs.unity.com/en-us/engine/6000.3/manual/whats-new/unity63.md. Use the on-device Render Graph Viewer to check that VFX don't add passes such as CopyDepth or CopyColor [I].
- VFX Graph instancing (6.0) and GPU-event instancing (6.1) [S, above]. Not relevant if we pick Shuriken.

### 1.6 Stylized VFX technique references
| Source | Technique (summary) |
|---|---|
| Harry Alisavakis, Unity blog #unitytips (2021-11-04) https://unity.com/blog/games/unitytips-dev-takeover-vfx-and-shaders-with-harry-alisavakis | Shuriken **Custom Vertex Streams** feed particle data to the shader. **Dissolve**: unlit, double-sided URP Shader Graph with alpha clip, driven by `TEXCOORD0.z` = age percent, or by `Custom1.x` from the Custom Data module for a curve over lifetime. Particle systems can go directly on Timeline. |
| Harry Alisavakis, anime beam breakdown, 80.lv https://80.lv/articles/crafting-a-kamehameha-like-vfx-001agt/ | Layered stylized beam: mesh beam, dust rings and charge sphere built from simple meshes + particles. |
| Simon Trümpler, "Stylized VFX in RIME" (ADDON talk + blog) https://simonschreibt.de/gat/stylized-vfx-in-rime/ | Vertex-colour-driven edges, sharpened with a hardness control. Smoke that fades by **alpha erosion/threshold**, with lit particles (RG normal maps) so it keeps volume while eroding. |
| VFX Doc, "Alpha erosion" https://vfxdoc.readthedocs.io/en/latest/shaders/alpha-erosion/ | Animate a threshold on an alpha mask. `step` gives hard, aliased toon edges. `smoothstep` with a small feather gives anti-aliased toon edges. Note that a feathered range may not fully clear at the extremes, so remap. |
| RealtimeVFX.com, Shannon McSheehan LoL FX knowledge share https://realtimevfx.com/t/shannon-mcsheehan-lol-fx-knowledge-share/1133/302 ; Realtime VFX Dictionary https://realtimevfx.com/t/realtime-vfx-dictionary-project | **UV scroll on meshes** with speed and UV scale changing over lifetime, then an erosion pass with a circle mask. Panned noise + UV distortion + erosion mask + control curves, instead of heavy textures or sims. |
| Gabriel Aguiar Prod (YouTube/Skillshare/Udemy) e.g. https://www.skillshare.com/en/classes/unity-vfx-graph-impact-effect/1753498420 , https://www.udemy.com/course/unity-vfx-stylized-ground-slash/ | Impact = triangles/sparks + beam + **mesh shockwave ring** + flipbook smoke + decal. Shockwave = ring/cylinder mesh with a scrolling, dissolving Shader Graph material. (His newer courses use VFX Graph. The same layer recipe ports to Shuriken mesh renderers.) |
| GDC 2017, "Art Directing VFX for Stylized Games" (Kladis, Lindsey, Mitchell, Spurgeon) https://gdcvault.com/play/1024715/Art-Directing-VFX-for-Stylized | Translate the game's art direction (shape language, palette, timing) into VFX. Readability first. |

Toolbox to build (one master toon-FX shader + mesh library) [I, synthesized from the above]:
1. **Mesh shockwave**: flat ring or squashed torus with UV.x around and UV.y across. Scale up with an ease-out curve. Erode with a stepped threshold driven by `Custom1.x`. Opaque or alpha-test, toon-lit. Fits plastic well.
2. **Stepped/toon dissolve**: `step(noise, threshold)` plus a 1–2 px coloured rim band `step(noise, threshold + rimWidth)`, giving the "melting plastic" read. Use `smoothstep(t-fw, t+fw)` with `fw = fwidth(noise)` for AA.
3. **Erosion masks**: a grayscale noise or gradient packed in one channel of a 256² texture. Several effects share one atlas (R/G/B/A = 4 masks).
4. **UV scroll**: `uv + _Time.y * speed` on trail and swoosh meshes (racket swing arcs, golf club swoosh). A swing arc is a **pre-modelled arc mesh** with UV.x along the arc revealed by a threshold, which is cheaper and cleaner than TrailRenderer.
5. **Vertex animation**: squash-and-stretch / wobble in the vertex shader (sin of time + vertex colour mask) for jelly-like "pop" objects, e.g. score stars and confetti. Use Shuriken **Size/Rotation over lifetime with overshoot curves** for the bouncy-toy timing.
6. **Shading**: 2–3 step ramp + fresnel rim, matching the character `TennisCharacter`/`TennisCloth` look, so FX feel like the same plastic.

---

## 2. Audio middleware and iOS/AirPlay routing

### 2.1 Unity built-in audio (Unity 6.3)
- **AudioMixer + snapshots**: groups, sends, ducking, snapshot transitions. Standard since Unity 5 [I].
- **Audio Random Container** (ARC) shipped in **Unity 2023.2**, so it's in Unity 6. [S] https://docs.unity3d.com/2023.2/Documentation/Manual/WhatsNew20232.html. Properties: clip list with per-clip volume, Volume/Pitch randomization (min/max), Trigger Manual or Automatic (Pulse/Offset + Time + Time randomization), Playback Sequential / Shuffle / Random + "Avoid Repeating Last N", Loop Infinite/Clips/Cycles + count randomization. It plays only through an AudioSource. [S] https://docs.unity3d.com/Manual/AudioRandomContainer-UI.html. `AudioSource.resource` takes an `AudioResource` (AudioClip or ARC). [S] https://docs-alpha.unity3d.com/ScriptReference/Audio.AudioResource.html
- **PlayScheduled(dspTime)**: plays at an absolute time on the `AudioSettings.dspTime` clock, independent of frame rate. Schedule ~100–200 ms ahead. If the time has passed it plays ASAP and skips what was missed. [S] https://docs.unity3d.com/6000.0/Documentation/ScriptReference/AudioSource.PlayScheduled.html. For us it's useful for music stingers on the beat and for **deliberately delayed** phone-side cues. Not useful for "play now" hits.
- **Unity 6.3 scriptable audio pipeline**: Burst-compiled C# "scriptable processors" inserted at integration points. [S] https://docs.unity.com/en-us/engine/6000.3/manual/whats-new/unity63.md. Lets us write a procedural layer (e.g. a pitched synth "tick") without native plugins [I].
- **Enhanced Audio Foundation (EAF)**: a new platform layer that supports iOS. On **Classic** (Unity ≤ 6.6, which is us), when the default device changes and the sample rate or layout differs, **"the entire audio engine resets and all engine state, including any playing sounds, stops"**. EAF avoids that when Output Channel Layout and Sampling Rate are set explicitly, and does device switching off the main thread. [S] https://docs.unity.com/en-us/engine/6000.7/manual/audio/foundations.md. **Risk for us [I]:** connecting or disconnecting AirPlay mid-session is a route change, so on Classic it may reset Unity audio (music stops, plus a main-thread stall). Test it explicitly. Our `AudioManager.asset` already has `m_OutputSamplingRate: 48000`, which only helps once EAF is enabled (Unity 6.7+).
- Voices: our project has 32 real / 512 virtual [R], which are Unity's defaults [I]. The loudest real voices win each frame. Virtualize Effects is on. [S] https://docs.unity3d.com/2022.2/Documentation/Manual/class-AudioManager.html
- DSP buffer options: Default / Best Latency / Good Latency / Best Performance. The docs don't give numbers [S] https://docs.unity.com/en-us/engine/6000.0/manual/unity-editor/editor-settings-reference/comp-manager-group/class-audio-manager. Community-known values are 256 / 512 / 1024 samples [I]. A forum report says "Best Latency" was reliable on iOS. [S] https://discussions.unity.com/t/dsp-buffer-size-differences-why-isnt-it-a-setting-per-platform/650034. At 48 kHz, 512 samples ≈ 10.7 ms per buffer and 256 ≈ 5.3 ms [I, arithmetic]. With AirPlay adding ~100–200 ms, this is noise for TV audio. It matters only for any Unity-played sound on the phone speaker.

### 2.2 FMOD Studio
- Unity integration 2.03.14 (2026-05-28). Tested against Unity 2021.3, 2022.3, **6.0 LTS and 6.3 LTS**. iOS/tvOS/visionOS are in the cross-platform package. [S] https://www.fmod.com/docs/unity , https://assetstore.unity.com/packages/tools/audio/fmod-for-unity-2-03-311497
- Licensing (**the sources conflict, so verify on fmod.com/licensing before committing**):
  - A search-engine digest of fmod.com/licensing gives **Indie: budget < $600k, "free or $2,000"**; $6,000 for $600k–$1.8M; $18,000 above $1.8M. [S, secondary] https://fmod.com/licensing ; Wikipedia agrees on the $600k/$1.8M tiers. https://en.wikipedia.org/wiki/FMOD
  - The free tier condition is **annual revenue < $200k** (FMOD quoted by Game Developer), with an older $500k budget figure. [S] https://www.gamedeveloper.com/audio/small-developers-and-creators-can-now-use-fmod-studio-for-free
  - The project must be registered in the FMOD profile. [S, secondary, search digest]
- Pros [I]: event authoring, parameters, live update to device, best-in-class randomization, voice limiting per event. Cons [I]: second audio engine on iOS (memory, a separate AVAudioSession owner, interplay with our voice chat + Core Haptics session), and the build pipeline gets more complex. The local-phone-speaker trick still has to be native code.

### 2.3 Wwise
- Official pricing page (international, read via search, 2026): **Indie free for production budget ≤ $250K** (first and extra platforms free). Pro: $8,000 first platform + $4,000 per extra (≤ $2M). Premium: $25,000 / $17,000. Platinum: $45,000 / $23,000. Licensed per platform. [S] https://www.audiokinetic.com/en/wwise/pricing/for-games/ (page blocks direct fetch, 403). Indie has **no asset limits**, and Audiokinetic re-checks the budget every 6–12 months after launch. [S] https://blog.audiokinetic.com/free-wwise-for-indie-developers/
- The old Starter licence capped at 200 sound files (2014). It is superseded. [S] https://www.gamedeveloper.com/audio/wwise-audio-middleware-is-now-free-to-use----within-limits
- iOS is supported [I]. It's the heaviest integration of the three.

### 2.4 Middleware verdict [I]
Our needs are a few hundred one-shots, randomization, ducking, 2–3 music beds and a TV mix. **Unity built-in (AudioMixer + snapshots + ARC + a thin C# `SfxBank` with per-event voice limits/cooldowns) covers it.** It also keeps one audio engine, which matters because we already juggle AVAudioSession for voice chat and Core Haptics. Revisit FMOD only if a dedicated sound designer joins and wants live-update authoring. Budget-wise FMOD Indie is likely free for us, and Wwise Indie too if the budget is ≤ $250K.

### 2.5 iOS latency and AirPlay
- **AirPlay latency (no Apple figure exists)** [S, community/vendor]:
  - Audio-only AirPlay streams have a **~2 s buffer** [S] https://discussions.apple.com/thread/4173205 ; AirPlay 2 buffering keeps multi-room speakers in sync [S] https://forums.macrumors.com/threads/audio-lag-with-airplay.2306123/
  - **Screen mirroring sends audio with the video and lip-syncs them on the receiver**. Mirroring latency is commonly quoted at **~100–200 ms** to Apple TV (blog estimate) and ~150 ms (AirServer receiver vendor). Old A7/A8 tests showed newer SoCs halving it. [S] https://www.airbeam.tv/how-do-you-mirror-iphone-screen-to-gaming-displays-for-minimal-lag/ , https://support.airserver.com/support/solutions/articles/43000531769-what-is-the-airplay-screen-mirroring-protocol- , https://forums.macrumors.com/threads/mirroring-games.1719825/
  - Wired Lightning/USB-C→HDMI is far lower: "<16 ms" (vendor claim) and 80 ms (old forum measurement). [S, low quality]
  - **Inference:** in mirroring or external-display mode the TV picture and TV sound arrive **together, both late by the same ~100–200 ms**. The hand (phone haptics) and the phone speaker are "now". So the audio design has two clocks: **phone = immediate, TV = delayed**, and our existing `delay` parameter is the right model. Measure the actual offset per session, for example by filming the phone and TV together, or with a calibration screen (tap when the TV flashes or beeps) as many rhythm games do, and store it.
- **External display (non-mirrored)**: a UIWindowScene with role `windowExternalDisplayNonInteractive` spans the external screen full-screen and takes no input. Mirroring is the default if the app doesn't attach a window to it. [S] https://developer.apple.com/tutorials/data/documentation/uikit/presenting-content-on-a-connected-display.md ; forum note that AirPlay to a TV offers this role [S] https://developer.apple.com/forums/thread/773838. `AVRoutePickerView` is the in-app AirPlay picker [I].
- **AVAudioSession categories vs AirPlay** (Apple QA1803, 2014, old but the only explicit table): Ambient/SoloAmbient/Playback support **mirrored and non-mirrored** AirPlay. **PlayAndRecord supports only mirrored AirPlay**. **MultiRoute does not allow AirPlay**. VoiceChat mode disallows AirPlay. VideoChat mode allows mirrored. [S] https://developer.apple.com/library/archive/qa/qa1803/_index.html. **Implication [I]:** while party voice chat (PlayAndRecord + voice processing) is active, game audio can still reach the TV only over mirroring, not over a separate AirPlay audio route, and `.voiceChat` mode would kill AirPlay entirely. Use `.videoChat` or `.default` mode with PlayAndRecord.
- **multiRoute** sends to all connected ports (e.g. USB + headphones), but **not AirPlay**, and a developer reported it disabling the hardware volume buttons. [S] https://developer.apple.com/library/ios/documentation/Audio/Conceptual/AudioSessionProgrammingGuide/AudioSessionBasics/AudioSessionBasics.html , https://developer.apple.com/forums/thread/750211. It is not a way to play "phone speaker + AirPlay" at once.
- **Phone-speaker sound while the main route is AirPlay: yes, via System Sound Services.** The `AudioServicesPlaySystemSound` documentation says: *"The sound is played locally on the device speakers; it does not use audio routing."* Constraints: ≤30 s, linear PCM or IMA4 in .caf/.aif/.wav, system volume only (no programmatic volume), plays immediately, no looping, no stereo positioning, **only one at a time**. [S] https://developer.apple.com/documentation/audiotoolbox/audioservicesplaysystemsound(_:). Apple DTS (2024-12) confirmed it is expected that system sounds ignore Bluetooth A2DP routes because playback is out of process. [S] https://developer.apple.com/forums/thread/770154. This is what `GolfHaptics.mm` already does [R]. It **respects the silent switch** (the reason that developer used it) [S, same thread], so a muted phone gives no knock and haptics must carry the hit [I].
- There's no documented way to make an AVAudioEngine/AVAudioPlayer/Unity voice play on the built-in speaker while the session's output route is AirPlay. `overrideOutputAudioPort(.speaker)` is for receiver→speaker under PlayAndRecord. [S] https://developer.apple.com/documentation/avfaudio/avaudiosession/overrideoutputaudioport(_:).md. Treat **System Sounds as the only phone-local channel** [I].

---

## 3. Haptics (Core Haptics)

- Engine and lifecycle (WWDC19 **520** "Introducing Core Haptics"): create the engine early and keep it running while haptic UI is visible. `stoppedHandler` fires on audio-session interruption or app suspension, and the app must track restarts. Players are fire-and-forget. "Low latency and real-time modulation". UIKit feedback generators sit on Core Haptics with the same latency. Use **CHHapticTimeImmediate** or an absolute engine time to sync with AVAudioEngine, Core Animation or game events. [S] https://developer.apple.com/videos/play/wwdc2019/520/
- Events: **HapticTransient** = a strike ("a gavel"). **HapticContinuous** = sustained, needs a duration, modulatable. **AudioContinuous**, and **AudioCustom** (your own waveform via `CHHapticAudioResource`, played in sync). Parameters: **Intensity 0–1** (like volume) and **Sharpness 0–1** (0 = round/organic, 1 = crisp/precise). Dynamic parameters and **parameter curves** modulate during playback. AHAP = JSON (`Version`, `Pattern` array of Event / Parameter / ParameterCurve). [S, same session]
- `CHHapticAdvancedPatternPlayer`: loop, seek, pause/resume, change during playback, sync with a custom audio track. [S] https://developer.apple.com/documentation/corehaptics/chhapticpatternplayer.md
- Engine time **does not correlate** with AVAudioPlayer/media time, so sync needs explicit offsets. [S] https://developer.apple.com/documentation/corehaptics/chhapticengine/currenttime.md
- Latency figures: **no Apple number exists**. One unverified blog claims 8–15 ms from schedule to onset (iPhone 13 Pro, ±3 ms) and a ~20 ms audio-touch fusion window. [S, low quality] https://omr.it.com/blog/haptic-feedback-timing-audio-tactile-synchronization/. Our own `playsHapticsOnly = YES` [R] matches Apple's guidance that a haptics-only engine starts faster [I].
- Design principles, WWDC19 **810** "Designing Audio-Haptic Experiences": **Causality** (it must be obvious what caused the feedback; imagine the physical object), **Harmony** (it should feel the way it looks and sounds), **Utility** (add only where it provides clear value). The Taptic Engine plays with the speaker in sync, and low frequencies are felt more than heard. [S] https://developer.apple.com/videos/play/wwdc2019/810 , https://wwdcnotes.com/documentation/wwdc19-810-designing-audiohaptic-experiences/
- WWDC21 **10278** "Practice audio haptic design" (Camille Moussette, ~16 min): sample app **HapticRicochet**, which coordinates animation, sound and haptics at key interactive moments (ball/wall collisions, shield, implosion). [S] https://developer.apple.com/videos/play/wwdc2021/10278. Prerequisite: WWDC19 **223** "Expanding the Sensory Experience with Core Haptics" + the HapticBounce sample. [S] https://developer.apple.com/videos/play/wwdc2019/223
- Unity access: Apple's official **Apple.CoreHaptics** Unity plug-in (apple/unityplugins: needs Apple.Core first, built with `python3 build.py`, iOS 15.6+, includes UIFeedbackGenerator). [S] https://github.com/apple/unityplugins (forks: https://github.com/raiha7/unityplugins), WWDC22 10065 https://developer.apple.com/videos/play/wwdc2022/10065/. **We already have a tighter native path in `GolfHaptics.mm` [R], so don't switch.**
- Mapping guidance for a racket/club (from 520/810 parameter semantics; the mapping itself is [I]):
  - Sweet spot = one transient, intensity 1.0, sharpness 0.6–0.8, then a 40–80 ms continuous "body" at 0.3–0.5 intensity and low sharpness.
  - Mishit/frame = sharper (0.9–1.0) shorter double-tap + low-sharpness buzz.
  - Bounce/net seen on the TV = transient at 0.3–0.5, **delayed by the measured TV latency** (we already do this [R]).
  - Avoid continuous rumble outside big moments (Utility). Cap the global intensity and keep a Settings slider (exists [R]).
- Game case studies: no public, sourced Core Haptics postmortem for a party sports game turned up in this pass. HapticRicochet is Apple's canonical "game" example. Nice Vibrations (in Feel) ships 80+ Lofelt-designed royalty-free haptic clips that could serve as reference material. [S] https://nice-vibrations.moremountains.com/

---

## 4. Audio compression and memory in Unity (iOS)

- Load types [S] https://docs.unity3d.com/6000.0/Documentation/Manual/class-AudioClip.html:
  - **Decompress On Load**: for small sounds, no runtime decode. Vorbis expands ~10×, ADPCM ~3.5×.
  - **Compressed In Memory**: decodes during playback, with slight CPU cost, especially Vorbis.
  - **Streaming**: ~200 KB overhead per clip even without data. Decodes on a streaming thread.
- Formats [S] same page + https://docs.unity.com/en-us/engine/6000.0/manual/audio/files/compression:
  - **PCM**: lowest CPU, largest.
  - **ADPCM**: fixed 3.5:1, slightly more CPU than PCM, much cheaper than Vorbis/MP3. Recommended for frequently played noisy sounds (footsteps, impacts, weapons). Artifacts are audible on smooth/tonal signals.
  - **Vorbis/MP3**: smallest, quality slider, for medium/long SFX and music. The default on mobile is Vorbis/MP3. AAC isn't offered for AudioClips. [S]
- Recommended table for us [I]:

| Asset | Format | Load type | Notes |
|---|---|---|---|
| Hits, bounces, UI ticks, footsteps (<1 s, transient-heavy) | ADPCM | Decompress On Load | ~3.5× PCM size in RAM. 100 clips × 0.5 s × 48 kHz mono × 2 B ≈ 4.8 MB, trivial |
| Tonal UI/jingles (<3 s) where ADPCM hiss is audible | PCM or Vorbis q≈70 + Decompress On Load | — | Short and tonal, so ADPCM hiss would be audible |
| Crowd/ambience loops (5–30 s) | Vorbis q 50–70 | Compressed In Memory | Avoids 10× expansion |
| Music (1–3 min) | Vorbis q 60–70 | Streaming | 1–3 streams max (each ~200 KB overhead) |
| Phone-local knock (System Sound) | IMA4/LPCM .caf | — (native) | Required by `AudioServicesPlaySystemSound` [S] |
- Force mono and 44.1/48 kHz for SFX. Preload Audio Data on for gameplay SFX banks and off for menu-only/music. Total audio RAM budget ~20–40 MB [I].
- Voices: 32 real is plenty for a 2–4-player party game. Add per-event voice caps (e.g. max 3 simultaneous "ball bounce", 80 ms cooldown) in our SfxBank so the 32 don't get eaten by crowd layers [I].

---

## 5. Camera feel

- **Cinemachine 3 Impulse**: `CinemachineImpulseSource` (or `CinemachineCollisionImpulseSource`) emits a signal from a point that propagates outward. It has a direction plus a strength curve over time. `GenerateImpulse()` is called from code or UnityEvents. `CinemachineImpulseListener` is an extension on the CinemachineCamera. Channels filter which listeners respond. [S] https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineImpulse.html , https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineImpulseSource.html , https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineImpulseListener.html. Common failure: missing listener or channel mismatch. A Uniform impulse ignores position, which suits global shake. [S, community] https://bugnet.io/blog/fix-unity-cinemachine-3-impulse-source-no-shake
- **Trauma model** (Squirrel Eiserloh, GDC 2016 "Math for Game Programmers: Juicing Your Cameras With Math"): trauma ∈ [0,1] is added by events and decays linearly. Shake = trauma² (or ³) × maxOffset × **Perlin noise** (smooth, continuous), applied to rotation (yaw/pitch/roll) more than translation. [S] https://www.gamedeveloper.com/programming/video-sprucing-up-cameras-with-math , https://bevy.org/examples/camera/2d-screen-shake/ (the squaring detail is [I] from the talk; verify in GDC Vault).
- **Verdict [I]:** we don't use Cinemachine, and the gameplay cameras are hand-framed and locked by AGENTS.md scope. Write a **~100-line trauma shaker** applied as a final additive offset on the existing camera: per-channel trauma, Perlin, decay, a global "TV comfort" scale, and a hard cap that keeps it subtle on a big TV. The cost is a few noise samples per frame, effectively zero. Cinemachine would mean adopting a whole camera system for one feature.
- TV-specific [I]: big screens amplify shake, so keep rotational shake ≤ ~0.5–1° and ≤ 150 ms for normal hits. Reserve bigger shakes for smashes and hole-outs. Pair them with a 2–4-frame hit-stop (timeScale dip) on the TV, because the phone feels the hit ~100–200 ms earlier anyway.

---

## 6. "Feel" toolkits

- **Feel (More Mountains)**: 100+ feedbacks (shakes, transforms, sound, camera, particles, post-processing, time…) via `MMF_Player` (formerly MMFeedbacks). It bundles **Nice Vibrations** (80+ Lofelt haptic clips) and MMTools. Asset Store price **$50** (cached listing; verify). v5.6 (2025-06) requires Unity **6000.0.23f1+**. The publisher says the scripts are cheap and the cost is whatever Feel drives, e.g. post-processing is costly on mobile regardless. [S] https://feel.moremountains.com/ , https://assetstore.unity.com/packages/tools/particles-effects/feel-183370 , https://feel-docs.moremountains.com/nice-vibrations.html
- Alternatives [I]: DOTween / PrimeTween (tween libraries, free) + our own sequencer. Unity Timeline for authored hero moments (particle systems drop straight on Timeline [S, Alisavakis blog]).
- **Verdict [I]:** build our own **lightweight FeelCue system**: a ScriptableObject "cue" = list of {VFX id + offset, SFX event + TV/phone channel, haptic cue + delay mode, camera trauma, hit-stop frames, UI punch}, played by one `FeelDirector` with pools. Reasons:
  1. Haptics and the phone-local knock are native and two-clocked (phone now, TV delayed). Feel's Nice Vibrations path would duplicate or compete with `GolfHaptics.mm`.
  2. We need the same cue fired on host and peer in online VERSUS. A data-only cue id is easy to network, MonoBehaviour chains less so.
  3. It's testable in EditMode (we already have `TennisHitFeelTests.cs`).
  Buying Feel ($50) purely as a **reference and prototyping sandbox** is cheap and fine. Don't ship it as the runtime spine.

---

## 7. SFX sourcing: libraries, AI, Foley

| Source | Cost (date seen) | Commercial game use | Key terms |
|---|---|---|---|
| **Sonniss GDC Game Audio Bundle** https://sonniss.com/gameaudiogdc | Free. 2026 bundle ~7.47 GB / 17 vendors (released 2026-03); archives 2015–2024 (e.g. 2024: 23.5 GB) | Yes, royalty-free, **no attribution**, unlimited projects | **No AI/ML training**. No redistribution as SFX/packs. Don't claim you recorded them. https://rekkerd.org/sonniss-releases-gdc-2026-game-audio-bundle/ |
| **Freesound** https://freesound.org/help/faq/ | Free | CC0: yes. CC BY: yes + credit. **CC BY-NC and Sampling+: no** | Filter to CC0/CC-BY and keep a credits manifest |
| **ElevenLabs Sound Effects** https://elevenlabs.io/sound-effects/commercial | Free tier / paid plans | "Royalty free and can be used in commercial projects". **Free plan requires attribution to elevenlabs.io**, paid doesn't | Don't use the output to build competing products. Check the ToS at ship time |
| **Stable Audio** (Stability AI Community License) | Free if org revenue < **$1M/yr**, else enterprise | Outputs owned by the user and commercializable under the Community License | Secondary sources only (2026). Verify the licence text: https://fast.io/resources/stability-ai-review-2026/ |
| **Splice** https://intercom.help/splice-b7a2d5b83f2e/en/articles/8652642 | Subscription (from ~$12.99/mo [I]) | Yes, royalty-free incl. video games | You licence, not own. Certified licence export for distributors |
| **Soundly** https://getsoundly.com/faq/what-are-the-differences-between-the-subscriptions/ | Free tier, Pro ~$10–15/mo (third-party, undated) | Yes per GameFromScratch | Read the EULA before shipping |
| **BOOM Library** (via Adorama listings) | Per pack, e.g. CASUAL UI **$129** (was $159), Close Combat $189 | Perpetual, royalty-free, multi-project | Retailer summary. Read the BOOM EULA. No dedicated tennis/golf pack found |
| **Krotos Studio** https://krotos.studio/pricing | Subscriptions ~$6.99–34.99/mo; Studio Max launched 2025-03 (36k+ sounds); Weaponiser list $399/$599 (older KVR) | Yes (sound design tool) | Mostly weapon/creature/footstep performance tools. Low value for tennis/golf [I] |
| **SoundMorph** | Not researched in depth this pass | — | — |

- Retro generators (jsfxr, ChipTone) are fine for prototyping blips only. They don't match the soft-plastic toy tone [I].
- **Foley on a budget** [I unless marked]:
  - Recorder: **Zoom F3** 32-bit float, 2 XLR, ~$280–330. 32-bit float makes clipping on sudden impacts (racket strikes, club on ball) "much harder". [S] https://www.thepodcasthost.com/equipment/recording-32-bit-with-the-zoom-f3/. Alternative: a handheld 32-bit-float Zoom H-series "essential" recorder with built-in mics [I].
  - Mics [I]: one small-diaphragm condenser or short shotgun (e.g. Rode NTG-class / Sennheiser MKE 600-class, ~$200–330) close-miked at 20–40 cm, plus a cheap **piezo contact mic** (~$20–40) taped to the racket frame or club shaft for the felt "thock" layer.
  - Record in a closet or duvet room. Sessions: real racket on ball (vary string tension and hit spot), ball bounces on carpet/wood/concrete, net brushes, club on ball off a mat, putter taps, golf ball into cup (a plastic cup works), plus **plastic toys** (squeaky, hollow taps, tupperware) for the toy layer. That layer is what will make it sound "Switch Sports" rather than broadcast tennis.
  - Layering recipe per hit: transient (real racket/club) + toy plastic body (tupperware or bottle tap) + tonal sweetener (pitched blip/ding by hit quality) + TV-only crowd reaction. The phone-local knock stays a short, dry, low-mid tick.
  - Don't feed Sonniss sounds into AI tools: their licence bans ML training [S].

---

## Recommendations for our game

1. **VFX = Shuriken only.** No VFX Graph: it's officially preview on URP/mobile in 17.3, and Unity staff said "not officially supported on mobile" as of 2025-12 [S]. Default to **opaque/toon-lit mesh particles** (plastic chunks, stars, confetti, rings) using URP `Particles/Simple Lit`/`Unlit` with **GPU instancing** (Mesh mode), or a small hand-written HLSL toon particle shader. Shader Graph particle instancing is a 6.6 feature [S].
   - Alpha-test stepped dissolve for "melt-away".
   - Alpha-blend only for small glows/dust. Budget ≤ ~2× full-screen-equivalent transparent overdraw at 1080p [I].
   - **No soft particles**, and keep the Depth Texture off for VFX's sake.
   - One master toon-FX shader with Custom Vertex Streams (age, Custom1 erosion, Custom2 tint) so every effect also follows the **customizable palette**.
2. **Pooling**: one pooled `ParticleSystem` per effect type fired with `Emit(EmitParams)`, plus `ObjectPool<T>` for composite prefabs. Prewarm instances and shader/PSO variants (`GraphicsStateCollection`) during the loading cover. Gate with a perf test: 4-player smash rally plus a confetti burst at 1080p must stay ≥ 60 fps on the oldest supported iPhone (profile on device with the Render Graph Viewer + Xcode GPU counters).
3. **Audio = Unity built-in.** AudioMixer (Music/SFX-TV/UI/Crowd/VO groups, ducking snapshots for point-won and hole-out), **Audio Random Container** per SFX event (pitch ±5–8 %, volume ±2 dB, avoid-repeat), and a thin `SfxBank` with per-event voice caps and cooldowns. No FMOD/Wwise for now: both are likely free for us, but they add a second audio engine that would fight our AVAudioSession / voice chat / Core Haptics setup.
4. **Two-clock sound design.**
   - **TV channel** (Unity audio → AirPlay, mirrored A/V-synced, ~100–200 ms late) carries the full mix.
   - **Phone channel** = haptics (Core Haptics, immediate) + **System Sound knocks** (the only documented phone-local path while AirPlay is active [S]; mono IMA4 .caf ≤ 30 s, one at a time, obeys the silent switch).
   - Keep using `delay` = the measured TV latency for haptics that confirm TV-visible events.
   - Add a **latency calibration screen** and store the offset.
   - **Test AirPlay connect/disconnect mid-match**: Unity's Classic audio foundation may reset the audio engine on a route change [S], and EAF only arrives in Unity 6.7.
   - With voice chat on, PlayAndRecord supports **mirrored AirPlay only** and `.voiceChat` mode disables AirPlay [S]. Use `.videoChat`/`.default` mode.
5. **Import settings**: ADPCM + Decompress On Load for hits/bounces/UI; Vorbis + Compressed In Memory for ambience; Vorbis + Streaming for music (≤ 2 streams); mono SFX at 48 kHz. Keep DSP buffer at Good latency (512). Moving to Best latency (256) buys ~5 ms that AirPlay swamps; only try it if Unity ever plays phone-local audio.
6. **Haptics**: keep `GolfHaptics.mm`/`GolfHitFeel.h`. Codify Apple's **Causality / Harmony / Utility** [S] into a per-cue table: transient for every strike, continuous only for charge/tension, sharpness for quality, intensity for power. A Settings intensity slider is a must. Don't adopt Nice Vibrations or Apple.CoreHaptics on top.
7. **Camera**: our own ~100-line **trauma shaker** (Perlin, trauma², decay, TV-comfort cap ≤ ~1° roll, ≤ 150 ms for normal hits) + 2–4-frame hit-stop on big hits. No Cinemachine adoption; gameplay framing stays untouched per AGENTS.md.
8. **Feel system**: build our own data-driven `FeelCue` ScriptableObject + `FeelDirector` (VFX, TV SFX, phone knock, haptic + delay mode, camera trauma, hit-stop, UI punch), keyed by id so online VERSUS can replay cues on both peers. Optionally buy Feel ($50) as a prototyping reference only.
9. **SFX sourcing**:
   - Start from Sonniss GDC bundles (free, no attribution, no AI training) + Freesound CC0/CC-BY with a credits manifest.
   - Then a 1–2 day home Foley session (Zoom F3 32-bit float + small condenser + piezo contact mic, ~$550–700 total [I]) for rackets, balls, clubs and **plastic-toy layers**, which are the signature of the soft-plastic sound.
   - Use ElevenLabs (paid plan, so no attribution) or Stable Audio (free under $1M revenue, verify the licence) only for ambience and sweetener ideation, and keep a provenance log per file.
10. **Verify before committing money**: FMOD's current tiers (sources conflict, $500k vs $600k budget), Wwise's pricing page (403 to fetch; figures via search digest), Feel's current price, and the Stable Audio licence text.
