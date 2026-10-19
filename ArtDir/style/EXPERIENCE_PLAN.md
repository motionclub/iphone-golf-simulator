# Experience plan — October 14, 2026

**Implementation update:** Authorized by “proceed with implementation.” The audit below is the original pre-change record. Implemented changes, measured after-results, proof and remaining acceptance failures are in [GATE_RESULTS.md](experience-implementation/GATE_RESULTS.md).

Every effect, animation and pause must improve responsiveness, readability or reward. The first gains are shorter result waits and clearer readiness. New spectacle comes last.

Audit and proposals only. This document is the only file written. No Unity project, animation, body, rig or face changes; no staging or other Git mutations. No new captures or Unity runs were needed: I read the existing scratch captures and recomputed their CSV measurements. Any later capture must use the APFS scratch clone, sync Assets/Packages/ProjectSettings there, and run light tests in foreground batchmode. Never run a capture in the working project.

## Evidence and limits

Read: `GPT_VFX_AUDIT_PROMPT.md`, `EXPERIENCE_AUDIT.md`, `VFX_ANIMATION_STANDARD.md`, `ART_BIBLE.md`, all 17 sheets in `vfx-anim-audit/`, both gameplay traces, capture scripts/metadata, and the relevant input, gameplay, animation-driver, audio and effects code. The Scuba release is intentional; the old clipping sheet is historical evidence, not a current clipping verdict. No animation repairs belong in this pass.

Paths below are relative to the repository. `T/` means `Unity/Assets/Scripts/Tennis/`; `G/` means `Unity/Assets/Scripts/Game/`; `C/` means `Unity/Assets/Scripts/Course/`. Evidence root: `/Users/adnanyonathan/UnityScratch_depths/work/vfxaudit/`. The 21 checked Unity source/capture files match their scratch counterparts byte for byte. Capture provenance remains the existing run, not a new benchmark.

Independent method: parse every CSV row; difference transition timestamps; count phase/clip rows; measure horizontal ball displacement from X/Z. Trace resolution is 16.67 ms; images are 30 fps, so visual boundaries have roughly one-frame uncertainty. Golf's CSV `videoFrame` is the next frame counter after saving (`Unity/Assets/Editor/CurrentGolfSwingFilm.cs:70–73`); match images using simulation tick/time, not that counter alone.

| Recomputed baseline | Result and qualification |
|---|---|
| Tennis, two completed reset intervals | PointOver 7.33333 → PlayerServeHold 8.15000 = **0.817 s**; 18.98333 → 19.78333 = **0.800 s**. |
| Tennis, visible serve stance | First stable post-walk Serve clip at 10.46667 / 22.13333: **3.133 / 3.150 s** after the point. This is a visual-readiness proxy, not a measured earliest accepted TOSS. |
| Tennis, active share | Rally alone **500/1660 ticks = 30.12%**. Including toss/opponent-serve phases **731/1660 = 44.04% = 12.183 s**. The audit's 44% includes toss. AutoPlay wait and initial walk affect this ratio. |
| Golf, injected request → visible strike | Stage 3 / Flight begins at **3.06667**. First ball movement at **3.31667**, also the burst/contact image `f_00069.jpg`: **250 ms**, not a measured phone latency. `impactFrame=62` labels the test request. |
| Golf, request → Result | **13.58333 − 3.06667 = 10.517 s**. Film ends at 15.56667, still in Result: next Aim is not captured. Adding the coded 3 s hold predicts **13.517 s**, plus transition/render overhead. |
| Golf, landing/tail | First vertical trough/rebound at **8.350 s**, about **5.033 s after visible strike**. This identifies first bounce, not the start of uninterrupted rolling. Last 3 s before Result travel **6.399 yd**; last 1 s **0.681 yd**. |
| Tennis, live celebration | **45 ticks / 0.750 s** of FistPump during Rally, 16.51667–17.25000 inclusive; player X varies **0.06951 m**, rather than staying exactly zero. |

Trace SHA-256: tennis `1cd5c11625390d2f8900d8514b92ea4374fd00ab96dbab5cd19cffff1bcbc222`; golf `9ae1048c9546dc673ccd832a032abee5299b1c3414a6cde796dc423560d571b5`.

**Device limitation:** `xcrun devicectl list devices` failed with “Timed out waiting for CoreDeviceService to fully initialize.” No physical phone or external-display timing was measured. Editor capture cadence is not device FPS. Haptics are no-ops in Editor (`G/Haptics.cs:11–30`). No device latency or haptic gate can pass from these films.

## Work order: player impact per effort

Effort estimates are rough focused engineering days, excluding device access. Numbers in the last column are targets, not achieved after-results.

| Order / phase | Work | Effort | Baseline → acceptance target |
|---|---|---|---|
| 1 / A | #1a: unlock ordinary local result continuation | 0.25 d | 3.0 s → tap accepted at 0.5 s; predicted sample 13.517 → 11.017 s when tapped |
| 2 / A | Added finding: remove default hit-stop | 0.25–0.5 d | 14/30/45 ms configured holds → 0 extra simulation-hold frames |
| 3 / A | #7: suppress full-body perfect celebration during live play | 0.25–0.5 d | 45 live emote ticks → 0 |
| 4 / A | #3: finish tennis reset within its existing beat | 1–2 d | 3.133/3.150 s visible stance → ≤1.5 s with meter ready |
| 5 / B | #2: measure real input paths; fix only any observed contact delay | 0.5 d measurement; 0.5–1 d if needed | injected 250 ms; device unknown → confirmed impact to visible contact p95 ≤100 ms |
| 6 / B | #1b: follow the roll, then compress unimportant runout | 1–2 d | predicted 13.517 s sample → ordinary local strike-to-Aim median ≤8 s |
| 7 / C | #4 and #5: readable quality and honest cause | 1–2 d together | existing partial/hidden feedback → ≥80% tier/cause identification |
| 8 / C | #6: make the existing cup event readable | 1–2 d | no cup-specific FX call → visible payoff within 0.2 s |
| 9 / D | #8: communicate existing weather rules | 1–2 d | subtle sway; wet rules already active → ≥80% wind-direction recognition |
| 10 / D | #9: expose rally growth and break point | 0.5–1 d | no live total counter → visible from shot 4 within 1 rendered frame |
| 11 / D | #10: test one contextual failure beat | 0.5–1 d | water 1.1 s + result 3 s → failure-specific blocking time ≤1.5 s |

Phase A ships no new artwork. Measure after each small change; proceed only when it improves its target without harming ball tracking, scoring or input acceptance. Phase B's latency measurement is a prerequisite to altering swing timing, not a reason to rewrite the detector now.

## Confirm/correct the ten audit items

### #1 — Golf waiting: confirmed; split the fix

**Evidence / correction.** `G/GolfGame.HoleOut.cs:90–96` fixes local results at 3 s; `G/GolfGame.Results.cs:29,95–101` rejects earlier continuation. `G/GolfGame.cs:2232–2237` auto-continues at that same deadline. `G/GolfGame.Native.cs:45–49` has no Flight continuation. The measured request-to-Result is 10.517 s; 13.517 s to Aim is a code-derived projection. The capture stops after only about 2 s of Result (`Unity/Assets/Editor/CurrentGolfSwingFilm.cs:69`). One drive cannot establish a median across golf.

The low landing view already exists: `G/CameraRig.cs:205–219` fixes its position at touchdown, then tracks the ball with its look direction. Change that existing view to maintain a readable ball size during runout; do not add another camera cut. “5.1 s rolling” conflates bounces and roll.

**Smallest fix / files.** First change only the ordinary non-holed local skip threshold in `GolfGame.Results.cs` to 0.5 s; retain the 3 s automatic reading window and existing multiplayer/holed-card policy. This saves 2.5 s when tapped. Next, adjust `CameraRig.cs` and the presentation clock in `GolfGame.cs`: compress already-computed, noncritical post-bounce runout at 2–3× while preserving the path, final lie, penalties and ordered event crossings. Stay at 1× around cup approaches, obstacles, hazards and ledge falls. Do not snap the ball to rest or change physics. A speed-under-1-m/s rule alone cannot promise the 8 s target; the last second here travels only 0.681 yd. Stop expanding this change if safe compression does not meet the budget; report the actual result.

**Phone feel / number.** Ten ordinary shots spanning drive, approach, chip and putt; tap at 0.4 and 0.5 s on separate results, then allow an untouched card. Require rejection before 0.5 s, acceptance by 0.5 s + one frame, auto-advance still 3 s, and median visible strike → controllable Aim ≤8 s after runout work. Compare saved shot outcomes before/after exactly. Exclude hole/match celebrations from that median, but report their times separately.

### Added finding — Default tennis hit-stop contradicts the brief

**Evidence / measurement.** `T/TennisRules.cs:84–86` returns 14 ms for Great/Excellent, 30 ms for Perfect and 45 ms for supercharge. `T/TennisGame.cs:1998,2038–2039` assigns/raises the hold; `:1088` skips simulation while it counts down. At 60 Hz these values nominally consume 1/2/3 subsequent Update frames. Keep the single drawn contact frame (`:1111–1113`); it makes contact readable without adding a timed freeze.

**Smallest fix / files.** Default the timed holds to zero through one policy in `TennisRules.cs` and guard all assignments in `TennisGame.cs`. `TennisGame.Versus.cs:198` includes hit-stop in an outgoing timestamp, so check parity there. `TennisFx.cs:169` still writes a Shake value, but I found no consumer of it; `TennisJuice.cs:159` makes Punch a no-op. Do not infer visible camera shake from dead values or comments, and do not activate them.

**Phone feel / number.** Alternate ordinary, Perfect, smash and supercharge returns. Require zero additional simulation-hold frames and zero contact-induced camera-shake displacement; no lost follow-up input or change in scoring/ball origin. This outranks adding any new reward effect.

### #2 — Golf contact delay: confirmed in the injected path; real motion already differs

**Evidence / correction.** First burst is raw frame 69, seven video frames after request-labelled frame 62; timestamp alignment gives 250 ms. `G/GolfGame.cs:1992,2023` calls `golfer.Strike(...)` and starts flight at negative time. `G/GolferView.cs:731–757` returns a downswing duration; `:644–645` configures 250–260 ms for full/half swings. Ball, sound, FX and haptic wait together at `G/GolfGame.cs:2214–2221`. This is scheduled anticipation, not evidence that physics launched before visible contact.

Crucially, native motion already starts the downswing at `G/GolfGame.Native.cs:293–308` and Launch uses `atImpact=true` for native non-touch play (`GolfGame.cs:1992`); `GolferView.cs:748–752` samples contact immediately and returns zero. The audit's proposed onset/contact split is already implemented on that path. Network behavior depends on `networkWoundUp`. The 250 ms injected demonstration must not be assigned to all three paths.

**Smallest fix / files.** Instrument before tuning. If native motion exceeds the target, fix event delivery/contact scheduling in `GolfGame.Native.cs`, `GolfGame.cs` and `GolferView.cs`; retain the authored anticipation and contact metadata. If only touch is slow, shorten the release-to-contact playback or begin anticipation during the held load; do not apply native `atImpact` blindly and introduce a pose pop. No clip edits.

**Phone feel / number.** Twenty strokes per motion/touch path, full swing and putt, plus a separate network sample. Use the latency protocol below. Require registered impact → visible contact p95 ≤100 ms locally and gameplay contact/FX/audio/haptic calls within one rendered frame. Inspect pre-contact pose continuity. Report physical gesture → display separately, including TV transport.

### #3 — Tennis reset: visible delay confirmed; emote hold diagnosis is wrong

**Evidence / measurement.** Two resets reach the stable serve stance in 3.133/3.150 s, although PlayerServeHold starts in 0.817/0.800 s. `T/TennisGame.cs:67` explicitly clears `tauntHold`: calls from `HeroTennisDriver.cs:522` do not extend the reset. `TennisGame.cs:1209–1210,1344–1352` walks the server to the opposite service side at up to 1.35 m/s; `:1406–1414` hides the meter and resets the AutoPlay clock until planted. TOSS itself has no planted check (`:430–436`), so early input acceptance needs testing. The first Shock clip begins at 7.38333, only 50 ms after PointOver, not 0.8 s later.

**Smallest fix / files.** In `TennisGame.cs`, restore the valid service-side starting position during the existing point beat, clear walk velocity, and show the meter when ready. Use the existing reset transition rather than sliding an emote across the court or increasing walk speed enough to cause foot skating. Preserve baseline nudging after arrival. If a reaction visually covers readiness, end it through existing driver scheduling in `HeroTennisDriver.cs`; no animation edits or new layer masks.

**Phone feel / number.** Ten ordinary points alternating service sides, including a miss at the net; tap TOSS at 0.8, 1.2 and 1.5 s on different resets. Require point end → planted server + visible meter + accepted TOSS ≤1.5 s, no toss-origin jump, and no extra wait for ordinary reactions. Report 44.04% inclusive live share and 30.12% Rally share separately. A 60% share is a secondary target under a fixed human-input schedule, not a valid gate from this short AutoPlay film alone.

### #4 — Shot quality: three sound tiers already exist; ball trail is the gap

**Evidence / measurement.** `T/TennisFx.cs:158–167` already scales flash size/color continuously and adds sparkles from Great, not only Perfect. `T/TennisSounds.cs:31–39` has normal pop, sweet pop from Great, and Perfect sting: **three audio signatures**. `T/TennisGame.cs:2036` resets the ordinary ball trail to white. `HeroTennisDriver.cs:474` changes the racket trail, which is different from carrying quality on the ball. The film contains only one successful player rally contact, at 16.01667, so it cannot measure three-tier recognition.

**Smallest fix / files.** Group existing contact shapes into three readable tiers in `TennisFx.cs`; reuse the sounds. In `TennisGame.cs`, carry a restrained quality tint on the ball trail until the next contact, with grey-blue/cream/gold and shape/size differences as redundant cues. Keep supercharge distinguishable without a second giant burst. Normal match text is intentionally restricted (`TennisGame.cs:108`, `TennisHud.cs:316,350`); do not restore the long feedback paragraph.

**Phone feel / number.** Five friends identify 12 mixed contacts each with grade text hidden: ≥80% correct overall and ≥70% for each tier, including with low volume. Ball remains discernible through every hit; effects occlude it or the hero for no more than 2 display frames. Reuse `T2_tennis_contact_crop.jpg` as the current Perfect baseline; capture all three tiers before/after.

### #5 — Why a shot failed: existing data, partly hidden feedback

**Evidence / correction.** Tennis already formats EARLY/LATE in `T/TennisGame.cs:2000–2005`; `T/TennisRules.cs:51` uses ±35 ms and `:912–917` includes placement direction. This is not haptics-only. Normal-match `ScoreOnlyText` suppresses the grade panel (`TennisHud.cs:316,348–354`). Whiffs instead get a generic message (`TennisGame.cs:1367–1368`). Golf already displays face, tempo and shape (`G/GolfGame.cs:2598–2618,2665`). The audit's golf “Timing, Center, ErrorDegrees” citation actually names the tennis struct (`T/TennisRules.cs:5–9`). Golf's `SwingImpact` has face, start line, curve, tempo and Thin (`Unity/Assets/Scripts/Swing/MotionSwingDetector.cs:26–49`).

**Smallest fix / files.** Allow one compact 0.6 s timing hint beside the existing tennis cue, even in score-only mode, through `TennisHud.cs` and the actual shot/miss classification in `TennisGame.cs`. Use measured timing or face error, not outcome alone: OUT does not prove LATE, and an out-of-reach ball is not a timing mistake. Reuse golf's existing grade/shape/face data in `GolfGame.Results.cs`; do not invent a golf early/late diagnosis. `G/ShotEffects.cs:37–48` and `Unity/Assets/Resources/Course/swing_trail.json` currently use green/yellow/red; remap the existing three bands to gold/cream/grey-blue without changing grading thresholds.

**Phone feel / number.** Ten labelled controlled errors per sport and five new players: ≥80% correctly name the actual cause; zero unsupported diagnoses. Tennis hint appears within one display frame of the confirmed outcome, lasts 0.6 s, and adds zero blocked-input frames. Compare the same players' first/fifth-rally grades as exploratory learning evidence, not a guaranteed five-rally improvement.

### #6 — Cup/near misses: improve the live moment, defer automatic replay

**Evidence / measurement.** `G/GolfGame.cs:2897–2904` hides the holed ball and calls cup/fanfare/crowd/haptic; **zero cup-specific visual calls** occur in that branch. The ball already has a cup-crossing/drop path (`C/CourseShot.cs:768–801`), so “nothing visual” overstates it. `G/GolfGame.cs:2674–2678` groans for lip-outs and nearby putts; “So close” is not always text-only. `:2975–2977` adds a 2 s badge. The supplied drive has **zero hole-outs/lip-outs**, so no cup-response latency is established.

**Smallest fix / files.** Trigger one small cup-local ring/sparkle and the existing cup sound/haptic on the actual drop crossing in `GolfGame.cs`/`ShotEffects.cs`. Reuse `CameraRig.HoleCam` (`:225–233`) only for approach readability if needed, and keep the cup visible through the drop before the result framing. Trigger a lip-out groan at the lip event rather than at rest. Do not add a mandatory 1.5 s replay, flag-animation system or extra score delay. Existing big-moment rewards can scale sound/FX, with no longer ordinary wait.

**Phone feel / number.** Tap-in, long putt, chip-in, lip-out and just-short putt on phone. Require visible cup payoff ≤0.2 s after drop, lip reaction ≤0.3 s after lip crossing, and no duplicate sound/haptic. The ordinary result becomes skippable on the #1 schedule; optional replay must be user-selected or replace existing waiting. Friends identify drop versus lip-out ≥80% without reading the card.

### #7 — Live celebration: confirmed appearance problem, not proven input lock

**Evidence / measurement.** One full-body FistPump occupies 45 Rally ticks (0.750 s). X moves 6.95 cm, so the trace does not prove a frozen controller. `T/HeroTennisDriver.cs:632` explicitly starts HitPerfect outside BetweenPoints; `:657` cancels only after 0.35 s when movement exceeds 0.9 or another action starts. That selection can make a live player look unready even while gameplay continues.

**Smallest fix / files.** Suppress queued/pending HitPerfect full-body playback while the rally is live in `HeroTennisDriver.cs`; preserve contact FX, sound, haptics and existing point-end celebrations. Do not build a new upper-body/face animation just to replace it.

**Phone feel / number.** Rally through ten Perfect contacts while immediately moving or swinging again. Zero full-body emote ticks during Rally, immediate normal movement response, and ready pose restored within 0.25 s after the authored stroke finishes. Preserve complete voluntary emotes between points and the intentional Scuba release.

### #8 — Weather: mechanics, sound and lightning exist; decision cues need testing

**Evidence / measurement.** `C/RoundEvents.cs:139–144` already multiplies wet fairway drag by **1.6**, green drag by **1.3**, bounce by **0.7**. `G/GolfGame.Events.cs:155–160` applies the rules. `WeatherView.cs:428–432` drives rain/wind audio; `:277–286,307–326` implements lightning and delayed thunder. Rain is not just a grey overlay. Wind-driven plants exist (`C/GolfWindSway.cs:23–28,67–70,92`), but their computed maximum weight-1 tip displacement at 20 mph is only **5.41 cm**, versus **1.35 cm** in calm. Still sheets cannot measure motion readability. No weather-choice trial exists in the supplied gameplay traces.

**Smallest fix / files.** Use the existing Wind value for an obvious near-play flag/directional cue before adding more ambient particles. Candidate files: `GolfWindSway.cs`, the existing flag view, `GolfGame.Events.cs` and `WeatherView.cs`. Make the cue agree with the HUD and physics; add a small wet-landing ring in `GolfGame.cs`/`ShotEffects.cs` only when wet rules actually apply. Preserve current geometry/light rigs; no aim guide. Reuse the weather audio, and do not make global sway stronger without checking phone readability.

**Phone feel / number.** Hide wind numbers for ten random directional reads: ≥80% correct within 2 s; then reveal numbers and compare players' chosen aim in opposite crosswinds. Scripted identical shots must show less wet roll, with unchanged outcomes relative to current wet physics. Require directional cue/HUD agreement within 15° and wet landing cue within one frame. Measure at 60 fps High / 30 fps Low on device; current capture FPS proves neither.

### #9 — Rally growth: add the missing live count, preserve existing tension

**Evidence / correction.** The film tops out at four contacts, so **zero 8+ rallies** support the hype claim. `T/TennisAudioDirector.cs:100–113` already adds live crowd beats at **6, 10, 14…**, mixes music for match point and hushes serving. `T/TennisGame.cs:2089–2092` already computes match point/hush; `TennisHud.cs:324–334` has a MATCH POINT notice. Game/break-point voice requests exist (`TennisAudioDirector.cs:43–48`), but no announcer assets are in the loader's Resources path. No live total rally counter is rendered; streak pips are not a rally total (`TennisHud.cs:337–340`).

**Smallest fix / files.** `TennisHud.cs` shows a small count from 4, updated at contact with restrained emphasis at 8 and 12. `TennisAudioDirector.cs` reuses existing crowd calls, without stacking voices over contact. Add BREAK POINT to the existing notice logic using the current match rules. Do not rebuild match-point presentation or add comeback VO before testing the counter.

**Phone feel / number.** Script rallies of 4/8/12 and ordinary/break/match-point score states. Count updates within one rendered frame, resets to zero correctly, and each threshold fires once. Notice is readable before serve without blocking TOSS. Five friends identify long-rally versus ordinary intensity ≥80%; no ball occlusion. Added waiting: **0 s**.

### #10 — Failures: keep one short contextual beat; no extra queue

**Evidence / measurement.** `G/GolfGame.cs:2351–2359` already gives water a splash/gasp and **1.1 s** before FinishShot; the local result then costs **3 s**, about **4.1 s after splash** before continuation under current policy. OOB groan and failure haptic exist (`:2682,2908`). Tennis already has comic whiff audio (`T/TennisSounds.cs:43`), reactions and point audio. The supplied films do not cover water/OOB; 4.1 s is code-derived, not a captured event. Announcer loader path `Resources/Tennis/Announcer` has **zero files**; `T/TennisAnnouncer.cs:69` silently skips missing keys. `/workspace/audio/AUDIO_PLAN.md` cited by the audit is absent here, so its claimed 42 lines were not verified.

**Smallest fix / files.** Reuse the splash/groan and one concise outcome call. In `GolfGame.cs` and `GolfGame.Results.cs`, overlap the water beat with the result/skip window rather than appending a second pause. Keep penalty and next-shot location obvious. No duck, fake water skip or sarcastic VO by default: none has demonstrated player value. If later testing supports one comic line, it must fit the same window and be cancellable. No hero clip changes.

**Phone feel / number.** Repeat water, OOB and whiff five times with friends; the losing player can explain the penalty and act again. Failure-specific blocking time ≤1.5 s from outcome, tap skip accepted by 0.5 s where safe, and no voice/reaction continues into the next action. Test first occurrence and repetition; retain the beat only if players prefer it without poorer outcome recognition. Record laughter/preference as observation, not a fabricated pass metric.

## Measurement and proof for implementation

**Input → visible response.** Use one event ID and a common monotonic clock for sensor onset/peak or golf address crossing, detector confirmation, native enqueue, Unity poll, swing-pose start, gameplay contact, FX emit, audio/haptic request and displayed frame. Existing native input is already 100 Hz (`GolfArcade/Unity/SportsMotion.swift:208–222`) and carries onset/confirmation timestamps (`:444–450`). Unity polls at most 64 samples per Update and forwards tennis onset/confirmation separately (`G/NativeSportsSession.cs:413–421,489–504`). Tennis starts provisional motion on onset (`T/TennisGame.cs:374–398`); preserve that.

Tennis detector onset requires 30 ms above the rate/force thresholds (`GolfArcade/Unity/SteeringFilter.swift:151,258–265`); proof confirmation waits ≥60 ms after onset unless the existing peak predictor wins (`:290–301`). Those are configured windows, not measured end-to-end latency. Standalone `TennisPhoneInput.cs:41–45` instead waits over 40 ms; it disables itself for native sessions (`:23`). Golf uses address-plane crossing/cancellation, not the Swift tennis confirmation rule (`MotionSwingDetector.cs:327–344`). Keep these paths separate in results.

On device, record at 240 fps with the physical gesture and actual playing display in the same view; align event-ID diagnostics to a visible marker in a development build. Timestamp audio/haptic requests separately from physical output. Test built-in phone display and the actual wired/wireless TV route separately. Targets: threshold crossing → first visible tennis response p95 ≤100 ms locally; confirmed golf impact → visible contact p95 ≤100 ms; all engine contact-channel calls within 1 rendered frame. Report medians/p95/max and display transport separately. Lag compensation changes judgement timing; it does not remove display latency. Twenty trials/path give a provisional p95 only. No such measurements exist yet.

**Pace and safety.** Extend the golf film through the next Aim and first accepted input, rather than stopping two seconds into Result. Log touchdown, bounce-end, true rest, result visible/skip-enabled/continue and input-ready, with wall-clock and simulation-clock fields. Tennis needs actual planted/meter-ready/TOSS-accepted events, rather than a Serve-clip proxy. Preserve identical seed, outcome, club, weather, camera setup and AutoPlay timing for comparison. Do not call a projected 11.017 s or ≤8 s an after-result.

**Proof bundle, later in scratch only.** For each phase retain before/after CSV + measured table + contact strips f−8…f+12 + phone-rate video. Reuse current strips below as BEFORE, but align golf f0 to actual contact and correct the frame counter. Add tennis reset strips at point end / +0.5 / +1.0 / +1.5 s; golf runout/result/next-Aim strips; cup and failure event strips; quality/early-late variants with text hidden. Use both heroes, 30/60 fps, local motion/touch and affected multiplayer paths. Test Low/High device frame times during rain and supercharge; require no regression and 33.3/16.7 ms frame budgets respectively. Do not infer performance from particle counts.

Existing visual proof: [golf request/contact](vfx-anim-audit/G1_golf_strike_crop.jpg), [golf runout/result](vfx-anim-audit/G2_golf_flight_land_result.jpg), [tennis contact](vfx-anim-audit/T2_tennis_contact_crop.jpg), [tennis point sequence](vfx-anim-audit/T0_tennis_point_overview.jpg). These are BEFORE evidence only. No AFTER strips exist because nothing was implemented.

**Standard conflicts to resolve when implementation is authorized.** The user brief and VFX standard's no-default-hit-stop rule override the older Art Bible §12 reference to 50–80 ms hit-stop. “Three channels” never justifies adding a camera/time effect. Weather audio/lightning and golf strike haptics already exist; the VFX standard's gap list is stale there. Net impact already has sound + particles (`T/TennisGame.cs:1536–1539`), so it is not a missing-sound task. Keep visual readability and actual synchronization as gates; defer a wholesale FxLibrary/shader/atlas migration until a concrete fault requires it.

GATE: SOURCE AND TRACE AUDIT PASS — all ten items checked, corrections and evidence recorded.
GATE: DEVICE LATENCY VERIFICATION FAIL — no device run; CoreDevice discovery timed out.
GATE: AFTER-CHANGE EXPERIENCE ACCEPTANCE FAIL — no implementation or after-proof in this audit-only task.

## Decisions for Adnan

1. Keep ordinary local golf cards auto-advancing at 3 s with tap available at 0.5 s (recommended), or also shorten automatic advance?
2. Accept repositioning the tennis server during the existing point beat to meet ≤1.5 s, or preserve the full walk and accept a longer readiness target?
3. For ordinary golf runout, prefer automatic safe compression after bounces, or an explicit phone “finish shot” action? Cup/hazard moments remain fully readable.
4. Which iPhone and display route should define latency acceptance: phone screen, wired TV, or wireless TV? Measure the others separately.
5. Keep lip-out replay user-requested (recommended), or let it replace the existing result wait? It must add no waiting.

## Five-line summary

Golf's ordinary result lock is the cheapest substantial pace win.  
Tennis has a 3.14 s visual reset and a 0.75 s live celebration to address.  
The golf film measures a 250 ms injected downswing; native motion latency remains unknown.  
Reuse existing sounds, weather mechanics and timing data before adding effects.  
Keep default shake and timed hit-stop off; require phone measurements and after-proof before acceptance.

**First change I'd make:** allow continuation at 0.5 s on ordinary non-holed local golf results, leaving the automatic 3 s reading window and multiplayer timing intact; then capture through next Aim to verify the actual saving.


## Implementation outcome

The planned small fixes are implemented and left unstaged. Actual tennis reset readiness is 0.817 / 0.800 s in the live capture, with zero live full-body emote ticks. Ordinary local golf continuation accepts a tap at 0.5 s; the matched shot reaches next Aim 2.517 s sooner. Its visible strike-to-Aim remains 10.95 s, so the 8-second target is not passed. Safe runout compression preserves every path sample and saves 0.5 s on a separate fixture; it stays off on the filmed cup approach.

Sixty focused EditMode tests and ten unique PlayMode tests passed. Phone latency, human recognition and device frame budgets remain unmeasured. Read-only discovery now finds a paired iPhone 17 Pro Max, but no physical gesture/display capture has been performed. See the implementation report for source locations and the exact proof/limitations.
