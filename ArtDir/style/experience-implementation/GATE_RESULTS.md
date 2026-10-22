# Experience implementation — October 14, 2026

The implementation and focused scratch checks are complete. Phone feel acceptance remains open; the ordinary-golf 8-second target is not met by the captured shot.

The recommended choices in `EXPERIENCE_PLAN.md` were used: ordinary local cards accept a tap at 0.5 s and auto-advance at 3 s; tennis resets to the serving side inside the existing point beat; safe runout compression is automatic; no extra replay is mandatory. No default shake or timed hit-stop was added. Animation, body, rig, face, clothing, map and lighting assets were not edited. Changes remain unstaged; no Git write commands ran.

## Measured results

| Check | Before/control | After | Gate |
|---|---|---|---|
| Tennis, point end → ready | Original visual-stance proxy: 3.133 / 3.150 s | Actual `ServeReady`: **0.817 / 0.800 s** in the live film; 20 scripted resets across both heroes: **0.883 s** maximum simulated step time, meter visible and TOSS accepted | PASS ≤1.5 s |
| Full-body emote during live rally | Original FistPump: 45 ticks / 0.750 s | **0 of 497 Rally ticks** in the after film; direct live HitPerfect requests rejected | PASS in tested paths |
| Tennis timed hit-stop | 14 / 30 / 45 ms configured | **0**, every grade, supercharge, smash/ultimate policy | PASS |
| Golf ordinary result continuation | Matched untouched card: 3.017 s to Aim | **0.500 s** after result with tap; reject 0.499 s, accept 0.500 s; automatic window still 3 s | PASS |
| Golf visible strike → Aim | Matched control: **13.467 s** | **10.950 s**, saving **2.517 s** | FAIL ≤8 s; one shot, not a median |
| Golf safe runout | Separate same-path flow test: 10.533 s request → Result without compression | **10.033 s** with compression; every precomputed position sample, duration, lie, rest and penalty equal | PASS outcome parity; 0.500 s saved on that fixture |
| Golf near-cup protection | Fixed-wind filmed shot | Compression saves **0 s** on this shot; protected cup approach remains normal speed | PASS safety behavior; no exaggerated compression claim |
| Water outcome → accepted continuation | Old code stacked 1.1 s + 3 s | **0.500 s** at 30 fps; splash and result start together, +1 penalty and next lie retained | PASS local path |
| Golf injected request → visible contact | Original 250 ms | **250 ms** in matched film; this is authored injected downswing, not phone latency | Unchanged intentionally |
| Native golf contact scheduling | Existing native anticipation/impact split | Three motion-readiness tests pass, including no added downswing wait at confirmed impact | PASS engine scheduling; device latency unmeasured |
| Live tennis contact channels | Not previously logged together | Contact and completed FX/audio/haptic requests on **frame 736** | PASS request synchronization for that contact, not physical output |
| Cup feedback | Existing drop + result sound, no cup ring | One cup feedback event at the drop; ring visible in retained view; local holed-card skip stays 3 s | PASS tested tap-in path |
| Wind | Existing arrow, speed/strength text | Direction words plus arrow; measured arrow/shot-relative wind error **<0.1°**, both crosswind directions | PASS mapping; human recognition unmeasured |

The matched golf pair uses hole 12, Driver, clear weather, wind 8 mph toward 90°. Both have CourseShot duration **10.45 s** and exact rest **(-0.9025087233763877, 209.41512785836326)**. Its control uses current visuals with compression disabled and the untouched 3-second card; it is a pace control, not a reconstructed old build. The original audit's golf shot has a different generated outcome and is not used to claim a causal flight saving.

The after tennis film has 1,272 ticks: Rally **39.07%**, including serve toss **57.23%**. Original values were 30.12% and 44.04%. These are descriptive AutoPlay observations with changed point timing, not a controlled human-input pace benchmark or a passed 60% target. Trace resolution is 16.67 ms; video is 30 fps. Editor capture cadence does not establish device performance.

## What changed, by audit item

Paths are relative to `Unity/Assets/`; lines identify the implemented source, not the historical audit.

| Item | Implementation / source |
|---|---|
| #1, result pace | `Scripts/Game/GolfGame.Results.cs:29` separates local non-holed tap threshold from the automatic reading window. Existing network and holed-card thresholds remain. `GolfGame.Experience.cs:16` accelerates only local non-putt, non-penalty, non-holed/lipped post-bounce runout. It samples the upcoming path and terrain, keeps 1× near cups/knocks/hazards/ledges, and excludes moving-obstacle holes. `CameraRig.cs:214` follows the roll from the existing landing view rather than adding another cut. |
| Added priority, hit-stop | `Scripts/Tennis/TennisRules.cs:81` and `:82` return zero timed holds for ordinary and heavy contacts. The single drawn contact frame in `TennisGame.Update` remains. Network timestamps therefore add zero hold. No shake consumer was enabled. |
| #2, input measurement | New `Scripts/Game/ExperienceTrace.cs` records opt-in stroke/event IDs, Unity frame/game/realtime clocks, bridge clock and raw native source times. `NativeSportsSession.cs:473` logs polled onset/confirmation/abort; `GolfGame.Native.cs:297` logs downswing/address-crossing; `TennisGame.cs` logs onset/confirmation/contact/TOSS/readiness. Golf logs impact request/contact/channel requests. No detector thresholds, clip timing or native impact split were retuned from an injected demonstration. |
| #3, tennis reset | `Scripts/Tennis/TennisGame.cs:431` exposes actual readiness and gates TOSS while unplanted. `:2090` resets stance/velocities inside the point transition and shows the existing meter. `HeroTennisDriver.cs:556` clears automatic reaction scheduling. A chosen emote can finish while the player's own serve remains ready; TOSS/movement or receiving returns the body to play. No fast walking or animation edits. |
| #4, quality | `Scripts/Tennis/TennisRules.cs:85`, `TennisFx.cs:158`, `TennisGame.cs:2322` provide grey-blue / cream / gold tiers with restrained size differences and persistent flight color. Supercharge remains cyan. Existing sound tiers are reused; split/versus carries remote grade color. `Scripts/Game/ShotEffects.cs:42` and `Resources/Course/swing_trail.json` change colors without changing grading bands. |
| #5, cause | `Scripts/Tennis/TennisHud.cs:365` shows one 0.6 s cue even in score-only mode. `TennisGame.cs:2016` uses measured EARLY/LATE; confirmed whiffs say NO CONTACT rather than inventing timing. OUT alone never supplies a cause. Existing golf result face/tempo/shape tiles were retained. |
| #6, cup | `Scripts/Course/CourseShot.cs:56,801` exports the first lip event without changing path integration. `Scripts/Game/GolfGame.cs:2344` emits cup/lip feedback once at the event; `ShotEffects.cs:411` reuses the ring. `GolfGame.Results.cs:67` retains the current world view for 0.3 s underneath the existing result window; no extra blocking time/replay. Voluntary result emotes take over immediately. |
| #7, live celebration | `Scripts/Tennis/HeroTennisDriver.cs:565,647` removes automatic live HitPerfect selection and rejects live requests. Point-end reactions and explicit emotes remain; Scuba animation/racket release is unchanged. |
| #8, weather | `Scripts/UI/GolfShotHud.cs:260` puts direction words beside the existing arrow near play. `Scripts/Game/GolfGame.Experience.cs:44` permits a wet landing ring only when rain/storm and existing wet drag/bounce rules apply; `GolfGame.cs:2309` emits it at landing/bounce. Existing flag direction, GolfWindSway amplitude, weather particles/audio/lightning and wet physics were retained. |
| #9, rally growth | `Scripts/Tennis/TennisHud.cs:325` shows count from 4, with brief emphasis at 8/12; `:341` adds BREAK POINT, excluding tiebreaks and preserving MATCH POINT. Both split HUDs get the count. `TennisAudioDirector.cs:100` reuses crowd beats at 8/12/16… once per threshold. Adds no waiting or VO. |
| #10, failure | `Scripts/Game/GolfGame.cs:2363–2375` overlaps local splash/result rather than stacking waits; failure haptic is requested once. Network water's existing timing is preserved. Existing penalty, groan, whiff and next-lie rules remain. No extra joke, fake bounce or cosmetic physics. |

## Checks and proof

**GATE: FOCUSED EDITMODE TESTS PASS — 60 tests.** Shot physics, lip event ordering, weather/wet roll, wind sway, zero timed hold and network point rules. [Result XML](proof/data/verified-edit.xml).

**GATE: FOCUSED PLAYMODE TESTS PASS — 10 unique tests.** Eight in [main run](proof/data/verified-play.xml), plus weather and voluntary-emote coverage; repeated cue/reset runs verify subsequent corrections. [Weather/cues](proof/data/cues.xml), [voluntary Scuba and reset](proof/data/emotes.xml), [final tier proof](proof/data/tier-proof.xml). Coverage includes both heroes, 30/60 capture cadence, 0.499/0.500 skip boundary, automatic 3-second advance, path equality, cup count, water penalty, native motion readiness, rally/cause notices and live celebration rejection.

**GATE: SOURCE/SCRATCH PARITY PASS — 24 source, capture and test files match byte for byte.** [SHA-256 manifest](proof/data/source-manifest.json). The active `~/UnityScratch_depths` was running another character-lighting test, so it was left untouched. An independent APFS clone at `/private/tmp/UnityScratch_experience_20261015` was used, with Assets/Packages/ProjectSettings synced from the workspace. All Unity invocations used foreground batchmode; none targeted the working project. One capture logged a Unity Editor SearchDatabase startup indexing exception from the copied cache; the gameplay capture completed and the focused test runs passed. It was not a gameplay exception.

Proof uses actual game renders. Tier/HUD/weather variants are controlled scene tests, not human recognition trials. No changed art asset is being claimed as approved by these renders.

- [Tennis reset, before/after](proof/tennis-reset.jpg)
- [Live tennis contact, f−8…f+12](proof/tennis-contact-strip.jpg)
- [Contact tiers, both heroes](proof/contact-tiers.jpg)
- [Rally and timing HUD](proof/hud.jpg)
- [Golf matched pace control/after](proof/golf-pace.jpg)
- [Golf contact, f−8…f+12](proof/golf-contact-strip.jpg)
- [Cup event](proof/cup-drop.jpg), [weather and water](proof/weather.jpg)
- [Tennis after video](proof/tennis-after.mp4), [golf after video](proof/golf-after.mp4) — 30 fps, silent; sound output was not recorded.
- [Measurements](proof/data/measurements.json), [golf identical-path test](proof/data/golf-pace.csv), [20 tennis resets](proof/data/tennis-reset.csv), [water](proof/data/water.txt). Recompute with `work/experience-implementation/measure.py` while scratch frames are retained.

## Acceptance still open

**GATE: ORDINARY GOLF ≤8 S FAIL — 10.95 s on the matched captured shot.** The planned safe limits were retained instead of accelerating meaningful cup/hazard action. A ten-shot median across drive/approach/chip/putt has not been collected; this one sample cannot establish that median.

**GATE: DEVICE INPUT → VISIBLE RESPONSE FAIL — not measured.** Elevated read-only CoreDevice discovery succeeded and found a paired iPhone 17 Pro Max; the earlier sandboxed discovery timed out. No updated device build was installed and no physical gesture/display, audio or haptic measurement was made. The native source and engine logs are measurement plumbing, not a sensor-to-photon result. The 250 ms film value belongs to injected anticipation; the native scheduling test does not replace 20 motion/touch/network device trials or separate wired/wireless TV timing.

**GATE: PHONE FEEL / PERFORMANCE ACCEPTANCE FAIL — pending trials.** The ≥80% tier/cause/wind/cup recognition targets, per-tier ≥70%, preference after repeated failures, 60 fps High / 30 fps Low during rain/supercharge and ≤2-frame visual-occlusion target need the plan's phone playtest. Lip event ordering is tested, but a live lip-out film, long putt and chip-in sequence are still missing. Multiplayer point rules are tested; a paired-device presentation/latency session is not. Current proof is sufficient to review the implementation, not to declare all experience targets passed.

Next device pass: use the paired iPhone on its built-in display first, then the actual TV route; record physical movement and display together at 240 fps. Enable `ExperienceTrace.Enabled` in a development capture (or `-experienceTrace` where launch arguments are supported). Join raw native source times/IDs to engine stroke/frame events; distinguish requested sound/haptic time from physical output. Do not ship diagnostic logging enabled by default.
