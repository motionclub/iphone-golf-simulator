# PLAN — First-launch onboarding + Golf Lesson (2026-10-24)

Status: **proposal, waiting on Adnan.** Nothing is built yet.
Mock (clickable TV prototype, phone states, flow map): https://claude.ai/artifact/NzHF1LEu7i4K4n25uoPdrA

Ask (Adnan, 10-24): the app greets new players and explains how everything works. Customize the character before any game. The menu intro introduces the game, then funnels into a tutorial game per sport, starting with golf. The tutorial teaches setup and the details of each game, for example that golf contact quality depends on how you swing. It must look solid.

## What exists today (code read 10-24)

- `GolfArcade/Onboarding/*` is a phone-side SwiftUI flow (account → character → connect → motion primer → choose → tutorial → reward). `OnboardingFlow.init` forces `.done` unless `-forceOnboarding` is passed, so **the shipped app never shows it**.
- `Unity/Assets/Scripts/Game/GolfTutorial.cs` has three phases (practice, aim, hole). **No code adds the component.** `TennisMenu.startTutorial` opens a normal round.
- `GolfSwingCalibration.cs` (three practice swings, median) exists. Nothing calls it.
- `HowToCards.swift` holds a 7-card golf guide and loading tips. Players can only reach them through the How-to station.
- There is no practice range. `Course.Meadow()` has an easy 115 yd par 3 (hole 3), but `Course.All()` does not list it, so `ByKey("meadow")` returns null.

## How golf actually grades a strike (the lesson must teach this, not something else)

| Input | Code | Effect |
|---|---|---|
| Backswing length | `MotionSwingDetector` `Load = angle / 2.6 rad`, ≥0.95 snaps to full | **Distance.** Hip-high ≈ 60 %. |
| Downswing speed | `commit = peak / club FullSpeed / 0.5` | Below 1, it loses distance. Below 0.75 it is **THIN** (−45 % launch, −50 % spin). Above 1 it adds only up to +4 %. |
| Face roll at impact | `FaceDegrees`, 10° dead zone, curve 0.5×face (cap 18°), start 0.18×face (cap 8°) | **Direction**: open = slice right, closed = hook left. |
| Tempo | `StrikeGrade` (total − down) / down, good band 2–8 | Part of the grade. |
| Grade | `StrikeGrade.cs` | THIN if thin > 0.25. Else faults: not committed +1, draw/fade +1, hook/slice +2, tempo off +1. 0 = **PERFECT!** (+6 % ball speed), 1 = GREAT! (+3 %), 2+ = GOOD. |

**There is no strike-point, swing-path or fat-shot model.** The gold "sweet spot" on the power rail only marks the backswing that reaches the pin. It does not change the grade. So "where you swing matters for contact" today means: commit through the ball, keep the face square, keep a smooth tempo. **Decision D1 below.**

Touch mode sends a fixed impact (commit 1.2, tempo 0.7/0.25 = 1.8). Every touch shot therefore grades GREAT and flies straight. Touch players need their own short lesson variant.

## Flow (TV-first; the phone is a controller, per the 10-10 UI feedback)

0. **Phone, first open, no TV:** Screen Mirroring in 3 steps. It continues on the TV automatically once a screen connects. "No TV? Play on this phone" is the escape.
1. **Hello (~40 s):**
   - Logo over the plaza.
   - "Your phone is the controller": the player points at a real gold button and presses SELECT. This teaches the new pointer menu by doing (Wii Sports Resort intro).
   - "Give yourself some room" (Wii strap card).
2. **Your player (~90 s):**
   - Body, skin, shirt colour (the real palette), name with suggestions, Shuffle, "That's me!".
   - Club card reveal.
   - Everything else waits for the Locker (Switch Sports, Animal Crossing).
3. **Pick your first lesson:** Golf (start) and Tennis (lesson coming soon). "Skip lessons" is always there.
4. **Golf Lesson, "The Practice Tee" (~6 min).** Eight stations. Each has one instruction, one pass check the game already measures, a Shot Read after every swing, a hint after 2 misses, and a skip offered after 3. No strokes count.

| # | Station | Pass check (existing data) | Teaches |
|---|---|---|---|
| 1 | Grip | ready pose captured calm (`NativeStartSwing` grip sample) | hold + tap SWING + still |
| 2 | Distance | carry within ±8 yd of the 112 yd flag with 7-iron (`Load` 0.7–0.8) | backswing = distance |
| 3 | Commit | 2 in a row with `commit ≥ 1` | THIN vs committed; harder ≠ further |
| 4 | Square face | `abs(FaceDegrees) ≤ 10` and ball through a gate | open slices, closed hooks |
| 5 | Tempo → PERFECT | one `StrikeGrade == Perfect` | tempo + the full grade ladder |
| 6 | Aim & map | ball on the island green (wind 8 mph) | joystick aim, club arrows, map dots = meter marks, wind |
| 7 | Putting | hole an 8 ft putt | tiny strokes, feet on the map, grain chevrons |
| 8 | Play a hole | finish Meadow 3 (cap 6) | everything; coach only speaks on new events |

After the lesson: a completion screen (golf cap unlock via `HeroAccessories`, a lesson badge, the best strike), then PLAY A ROUND or the menu. Lessons stay replayable from Play › Lessons.

**Phone during the lesson:** a big SWING button plus PAUSE. AIM and CLUB stay greyed until station 6 (progressive disclosure).

## Build plan (after approval)

1. **Unity `GolfLesson`** (replaces `GolfTutorial.cs`):
   - data-driven stations with pass predicates over `LastShot`, `StrikeGrade`, `MotionSwingDetector` values;
   - a `LessonHud` on the `GolfShotHud` canvas in brand style (coach card, step dots, Shot Read chips, grade pop);
   - lesson props (flags, gate, target ring).
   - Practice Tee = Meadow's open fairway (or a flat range scene). Meadow hole 3 for station 8.
   - Add a hidden `lesson` course key so `ByKey` works without listing it in `All()`.
2. **Launch path:**
   - `TennisMenu.startTutorial(.golf)` → `startGolf(tutorial: true, course: "lesson")`;
   - Unity adds `GolfLesson` when the start message carries `tutorial`;
   - wire the events `StepChanged`, `StepResolved`, `Finished` → `OnboardingFlow`.
3. **Onboarding on the TV:**
   - move Hello / Player / Pick off the phone (`OnboardingRoot`) onto the TV, in Unity over the live plaza or as `TennisTVRoot` SwiftUI, matching whichever renderer the pointer-menu work picks;
   - the phone shows the pointer remote;
   - re-enable first launch in `OnboardingFlow.init` (drop the forced `.done`), keep `-skipOnboarding`, and keep "Replay onboarding" in Settings.
4. **Proof:** TV captures of every screen vs the mock, plus a scripted run through all 8 stations with synthetic swings (the `GSSPhoneFeed` harness). Binary gates in `proof/onboarding/GATE_RESULTS.md`.

## Tennis lesson, "The Practice Court" (mocked 2026-10-25)

Canvas page "Tennis lesson": an interactive prototype (`TennisLesson.dc.html`), the phone states, and a miss frame and a pass frame for every station. The pick screen's tennis card opens it.

It follows the rules in the code as of 10-24/25: `TennisRules.cs`, `docs/tennis-timing-power-2026-10-24.md`, and `SportsTiming.advice` from the latency P1 work.
- The racket face at contact picks the side. Within ±8° of square goes straight, and about 30° reaches the corner (`SideFromSwing`: dead band .15, full .75).
- Timing picks pace and depth. PERFECT is within 35 ms, EXCELLENT 60, GREAT 95, GOOD 140, and OK out to 340 ms.
- A swing up to 320 ms early is held back and still hits. Rally balls are never out.
- Grade labels: PERFECT! / EXCELLENT / GREAT / GOOD / OK. Speed shows in km/h.

| # | Station | Pass check (existing data) | Teaches |
|---|---|---|---|
| 1 | Court setup | axis gate locked, then TV flashes + 5-bounce timing check (`SportsTiming.advice` line: "Your TV over AirPlay: 140 ms…") | point at the TV once, the TV delay is handled |
| 2 | Forehand | 2 balls returned | swing as the rings close; the player runs for you |
| 3 | Timing | one hit graded GREAT or better | timing = pace (km/h) and depth; early swings are held back |
| 4 | Backhand | 1 backhand returned | the ball's side picks the stroke, no grip change |
| 5 | Aim | land in the left ring, then the right ring | racket face at contact = side |
| 6 | Serve | 1 serve in | TOSS at the meter's middle, swing at the top, aim box |
| 7 | Run and dive | reach a wide ball with DIVE | auto-run, stamina, dive cost and recharge |
| 8 | Play a point | finish one point vs Coach Ray | everything; coach speaks only on supercharge, first spin, low stamina, double fault |

Build notes:
- Replace `TennisTutorial.cs`'s five steps with these eight. Its `Landed`/`DrillPoint`/`ScoreChanged` hooks and gold target ring are reusable.
- Remove its `TouchInstruction`, since touch play is gone.
- Setup reuses the existing scan, flash and timing-check flow, wrapped in lesson UI.

## Decisions (Adnan, 2026-10-24)

- **D1 Contact quality:** teach the real model (commit + square face + tempo). No new mechanic.
- **D2 Touch players:** they should not exist. The lesson is motion only, and the phone mock no longer offers "play on this phone". Touch-screen *gameplay* was removed from the app on 10-24 (uncommitted): the golf power slider, the tennis Swing button and steering slider, every "use touch controls" switch, the settings Controls row and the onboarding "Use touch instead". The phone's controller buttons stay: the aim pad, club arrows, select, pause, toss, dive and emotes.
- **D3 Renderer:** asked for a visual example of both. The canvas page "Renderer options" shows two options:
  - A, Unity over the live plaza: real Unity captures, the real hero, world-space name tag and floor ring, camera moves.
  - B, a SwiftUI TV window: the plaza blurred behind it, and the hero as the app's real SceneKit lobby render in a studio card.
  - **Chosen: B (2026-10-25), built.** See "Built (option B)" below.
- **D4 Tennis lesson:** wait until the tennis gameplay rework lands. Golf only for now. Superseded 10-25: the tennis lesson is built on the 10-24/25 rules.
- **D5 Coach:** text on screen only. No voice.

Mockups: the canvas page "Golf lesson storyboard" holds a miss-with-hint frame and a pass frame for each of the 8 stations, plus the intro, PERFECT and complete frames. The frames are imported from the prototype, so they stay in sync with it.

## Built (option B), 2026-10-25, uncommitted

TV onboarding, all SwiftUI on the TV window (`TennisTVRoot` → `OnboardingTV`). The phone is a remote: D-pad, A and B, plus the name field on the player step.
- Steps: hello → controller (try the arrows/A/B) → room → player (body, skin, shirt, name, shuffle) → player card → choose a lesson → lesson (in the game) → reward → done. The step is saved under `ftue.step.v2`, so a quit resumes where it left off.
- Existing installs with no v2 step skip onboarding. `-forceOnboarding` beats `-skipOnboarding`. "Replay onboarding" in Settings keeps hero progress and doesn't award rewards twice.
- Files: `GolfArcade/Onboarding/OnboardingStore.swift`, `OnboardingFlow.swift`, `OnboardingTV.swift`, `OnboardingRoot.swift`, `LessonCenter.swift`; art `GolfArcade/Unity/MenuArt/onboarding-plaza.jpg`. The old phone screens and `GolfTutorialController` are in `work/onboarding/retired/`.

Lessons in the game. Unity runs the station and reports it as JSON over the `lesson` event. Swift draws the HUD (step pill, dots, coach card, Shot Read chips, grade pop, hint after 2 misses, SKIP after 3).
- Golf: `Unity/Assets/Scripts/Game/GolfLesson.cs` on the hidden `lesson` course (`Course.Lesson()`, the Practice Tee). It has the 8 stations above.
- Tennis: `Unity/Assets/Scripts/Tennis/TennisTutorial.cs` (7 court stations + the phone's court setup) and `TennisGame.Lesson.cs`.
- Bridge: `NativeSportsSession.Lesson.cs` (`LessonAttach`, `lessonSkip`, `LessonJson`).
- The old `GolfTutorial.cs` is retired.

Open follow-ups: the controller step teaches arrows/A/B, so update it when the pointer menu lands. Kanit isn't in the app; Rubik is used. Device test and phone build are not run yet. Gates: `proof/onboarding/GATE_RESULTS.md`.
