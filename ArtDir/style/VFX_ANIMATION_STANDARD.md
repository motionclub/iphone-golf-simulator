# Party Sports: VFX + Animation Standard v0.1

> **Core principle: every effect must serve responsiveness, readability, or reward. No effect for its own sake.** Before adding or keeping an effect, ask: *what does the player understand or feel faster because of it?* If nothing, cut it. Effects never add waiting and never cover the ball or hero for more than 2 frames. The ranked opportunities are in `EXPERIENCE_AUDIT.md`.

This is the companion to `ART_BIBLE.md`. Same rule: **numbers are starting targets to tune by eye**. Look: **bouncy, cartoon, readable**, modern Nintendo charm.

## A. Effect style
1. **Shapes:** round puffs, chunky stars, soft rings, thick streaks. No realistic smoke, no grey fog blobs and no hard white squares (except confetti, which must be colored).
2. **Colors:** only from the bible palette. Contact FX are warm white #FFFDF2 plus the ball yellow #FFF36B. Dust takes the surface color (court #2089D8 lightened, grass #A1C33E, sand). **Orange-red #FF5A1F is only for hazards and warnings.** Shot-quality colors: Pure = #FFF36B gold, Fair = #FFFDF2 white, Off-line = #8CB2CB grey-blue (not red).
3. **Glow:** additive and bloom only on contacts, sparkles, lava, neon and supercharge (bible §9). Dust, water and confetti are alpha, never additive.
4. **Size and readability:** no effect may cover the hero or ball for more than 2 frames. Rings max out at about 1.5 m world size (about 12% of screen width at the play camera).
5. **Lifetimes:** contact flash 0.06–0.12 s, sparks 0.2–0.4 s, puffs 0.3–0.6 s, splash 0.5–0.9 s, confetti 1.5–2.5 s, ambient (embers, steam) loops. Nothing gameplay-related lingers past 1 s.
6. **Counts:** keep effects light enough to hold frame rate. Judge by FPS on device, not by particle counts.
7. **One master particle shader set**, `FX_Additive`, `FX_Alpha`, `FX_Distort` (optional, High tier only). One shared atlas, `Resources/Fx/fx_atlas.png` (puff, star, ring, streak, droplet, leaf, confetti, ember). Shader-missing fallbacks must log an error **and** use a magenta debug color in development, so they get caught. They must never silently become white.
8. **One FX library:** a `FxLibrary` ScriptableObject lists every effect (id, atlas cell, palette color, count, life, size curve, sound id, haptic id, hit-stop). TennisFx, ShotEffects, WeatherView and LavaWorld read from it instead of hard-coding colors.
9. **Pooling:** build once and `Emit()` (already the pattern). Never Instantiate or `new Material` per event. Destroy runtime materials in `OnDestroy`.

## B. Timing (feel)
- **The effect fires on the contact frame** (gameplay contact = clip contact frame = FX = sound = haptic, in the same call).
- **No camera shake and no hit-stop by default** (Adnan's call). Weight comes from the per-tier contact sound, flash, ball trail and haptics.
- **Quality tiers are distinct at the ball:** 3 tiers that differ in sound, color and trail (EXPERIENCE_AUDIT #4). Misses show EARLY or LATE (#5).
- **Effects never add waiting:** reactions overlap the reset, and failure beats are ≤ 1.5 s and skippable (#1, #3, #10).
- **Swing phases:** anticipation 6–10 frames (visible windup), contact 1–2 frames, follow-through 10–16 frames, settle 6–10 frames. Don't remove anticipation to cut latency; shorten it instead.
- **Squash and stretch (bouncy cartoon):**
  - ball on bounce: 0.75× and 1.25× for 2 frames
  - ball on hit: stretch along velocity 1.3× for 2 frames
  - UI pops: 0 → 1.15 → 1.0 over 0.18 s (ease OutBack)
  - props hit by the ball: 0.9 → 1.08 → 1.0
  - Heroes: through clips only (don't touch animation rigs unless Adnan asks).
- **Input to visible contact** under about 100 ms on device. Golf currently measures about 270 ms in the film; check that.

## C. Animation rules
1. **No clipping:** hands, racket and club stay out of the body and clothes (0 hand-mesh points deeper than 5 mm). Clothes never show skin or lining (0 patches over 40 px at 1080p full body). The same detectors as `work/emote-standard/CLIPPING_AUDIT`.
2. **Grip:** the racket or club stays in the hand in every clip (grip-socket to hand-bone distance ≤ 1 cm), except in clips that explicitly release it and re-attach before the clip ends. The off hand follows the authored `leftRelease`.
3. **Feet:** planted feet slide ≤ 10 mm. Soles stay within −6 mm to +3 mm of ground on contact frames. Foot lock on the stance foot in all sports, including golf and the hub.
4. **Transitions:**
   - locomotion 0.15–0.25 s
   - into a stroke 0.08–0.12 s
   - stroke to idle 0.2–0.3 s
   - emotes in and out 0.2 s
   
   No pose pop over 8 cm of hand travel in one frame unless it's authored.
5. **Root motion** stays off for match heroes (gameplay drives position). Emotes must start and end at the same root position (≤ 2 cm).
6. **Clip contact metadata:** every stroke clip has a `contact` time. A test checks the racket is fastest at contact (already true; keep it tested).
7. **Props and obstacles:** idle motion is always on (windmill, twister, movers). Any hazard telegraphs 0.5 s before it's dangerous (wind-up plus a hazard-color pulse).
8. **New clips go through the emote-standard pipeline** (Blender solve → clipping gates → in-game film), and they need the clipping gate to pass.

## D. Per-event checklist (every event needs ≥ 3 channels)
For each event in `VISUAL_STANDARD_AND_JUICE.md` §4, fill in: Visual ☐ Sound ☐ Motion (squash, slow-mo, camera) ☐ Haptic ☐ UI ☐. Ship only when at least 3 are ticked and the visual one is **where the player is looking**. Current gaps: golf strike haptic, net-cord sound and haptic, putt-drop visual at the cup, shot-quality tiers at the ball, early/late feedback, weather audio and flash.

## E. Automated checks (run on every VFX or animation change)
1. **Clipping gate:** run the emote-standard detectors (hands, racket, cloth tears, feet) on every changed clip × 2 heroes × 2 kits. FAIL on any "very obvious" result. **Add this as gate G0 in `work/emote-standard/GATE_RESULTS.md`.**
2. **Pace check:** from the film traces, measure point end to serve-ready (≤ 1.5 s) and golf strike to next aim (≤ 8 s). FAIL if worse than the last golden run.
3. **Missing material and shader scan:** a test that asserts every `Shader.Find` and `Resources.Load<Shader>` used by FX resolves and is in Always Included Shaders. FAIL on any fallback. Also FAIL on `Texture2D.whiteTexture` in FX.
4. **Golden frame strips:** reuse `CurrentTennisPointFilm`, `CurrentGolfSwingFilm` and `EmoteFilm` in a scratch clone (foreground batchmode). Build contact strips f−8 to f+12 and compare them with the approved golden strips by eye, plus a perceptual diff. Extend `EmoteFilm` to accept the 7 new emote names.
5. **Timing check:** a PlayMode test that records the frames where gameplay contact, the FX emit, the sound and the haptic happen. FAIL if any differ by more than 1 frame.
6. **Grip check:** per clip, the max grip-socket-to-hand distance is ≤ 1 cm, except clips that drop the racket on purpose (Scuba).
7. **Perf:** an on-device FPS check, Low and High tiers, in the busiest moment (a supercharge rally in rain).
