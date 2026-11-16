# PLAN — Onboarding v3: intro over the menu + locked Tutorial (2026-11-15)

Adnan 2026-11-15: "first users should not be required to airplay during onboarding … load up, enter menu, then an interactive
intro that welcomes them, prompts them to customize their character, explains how it works (phone is motion controlled, AirPlay
for the best experience or play with just your phone), then prompts them to go to Play; once they do, everything is locked except
a section called Tutorial: golf first (swing, putt…), then tennis (explain calibration, make them do it, then play), then bowling;
once completely done they are free. For each game an animation of how they should look playing in front of their TV, from
behind. Make sure they understand not to stand too close to the TV, and warnings people accept when loading into a game.
Research first, plan, then execute; I am not here to approve anything."

Supersedes the TV-first flow of `PLAN_Onboarding_GolfLesson.md` (10-25). Its lessons (GolfLesson.cs, TennisTutorial.cs) and the
lesson HUD (LessonCenter) are reused unchanged.

## Research (summary; full brief in `work/onboarding-v3/RESEARCH.md`)

| Source | What we take |
|---|---|
| Wii Sports (manual) | one short strap/space reminder before play, confirmed with one press; every sport page repeats *hold it like the real thing · strap on · swing gently*; "no people or objects around you" |
| Switch Sports (press) | warnings about surroundings + straps; **keep away from the TV and children**; first time in each sport is a tutorial; Pro League locked behind 10 matches |
| Ring Fit | the controller itself confirms each setup step; calibration step with a big OK; health & safety confirmed with one squeeze |
| Meta Quest | ~2 m × 2 m clear space; the system cannot see pets or people |
| Golf Clash / Tennis Clash | very short tutorial (power + aim / target drill) then straight into a real match; tutorial replayable from settings |
| Brawl Stars | forced first match, features unlock by milestones |
| GameAnalytics / Roblox / Meta | value within 2–3 min, ~3 successful repetitions per action, instant retry, funnel event per step |
| Apple HIG + "Onboarding for Games" | teach by doing, short steps, defer sign-in/notifications; Review Guideline **1.4.5** (no urging risky physical use → say *swing smoothly*, never *swing hard*); AirPlay: use the system wording/picker, call it "AirPlay" as a noun |

Where the research and Adnan disagree, Adnan wins: customize comes **before** the explanation, and Play is **hard-locked** to
the Tutorial (the research prefers soft "New" badges). Mitigations kept from the research: one-tap confirms, no TV required,
per-station Skip after 3 misses (existing), tennis can be deferred when there is no TV (it cannot be played without one), existing
installs are not forced through, Settings → Replay onboarding stays.

## Flow

1. **Boot → menu.** Nothing blocks the menu any more: the old "Let's get you on the TV" screen and the TV-only SwiftUI
   onboarding are no longer shown. The menu boots on the TV if one is connected, on the phone if not.
2. **Intro over the live menu** (`IntroCoach`, SwiftUI): on the phone always; mirrored big on the TV when one is connected
   (`IntroTVCard` in a window above Unity on the external screen).
   1. **Welcome**: wordmark, one line, *Let's go*.
   2. **Make your player**: *Customize* opens the real Locker (the phone panel). Closing it moves on; *Keep this look* also moves on.
   3. **How it works** (3 short cards, one tap each):
      - *Your phone is the controller*: swing it like a club, racket or ball.
      - *Big screen or just your phone*: AirPlay (Screen Mirroring) to a TV for the best experience, or play golf and bowling on
        the phone alone. Shows live whether a TV is connected. Tennis needs a TV.
      - *Play safe*: hold the phone tight (strap/grip case if you have one), clear about 2 m around you, **stand at least 2 m
        (6 ft) back from the TV**, swing smoothly.
   4. **Go to Play**: the card moves to the top and points at PLAY ("Tap PLAY to start your tutorial"). Pressing PLAY on the menu
      ends the intro.
3. **Play is locked to TUTORIAL** (`TutorialGate`, synced to Unity's MenuHud as `menuTutorialState`). The sports list shows
   TUTORIAL first and lit; Tennis, Golf, Bowling and Daily Challenges are dimmed "Finish the tutorial to unlock". The Swift
   routes refuse locked bays too (a toast), so nothing slips through. Locker and Clubhouse stay open.
4. **Tutorial screen** (Unity, `MenuHud.Tutorial.cs`): 1 GOLF → 2 TENNIS → 3 BOWLING. One lit at a time; done ones get a tick and
   stay replayable; later ones say "Finish golf first".
5. **Before each lesson: How to play** (`PlaySafeSheet`, tutorial variant): a looping 3D back-view animation (SceneKit,
   `HowToPlayScene`) of a player in a living room swinging the phone at the TV, with the 2 m floor marker and the clear-space
   ring, 3 short steps for that sport, the safety checklist, *I'm ready* (one tap = accept). Then the lesson loads.
   - **Golf** (existing 8 stations: grip, distance, commit, face, tempo, aim, putt, a real hole). On the TV, or handheld on the
     phone with no TV.
   - **Tennis**: the explainer says what calibration is (point at the TV, sync the timing) and the lesson's first station *is*
     the court setup (scan + timing check), then the 7 rally stations (forehand, timing, backhand, aim, serve, wide ball, a
     real point). Needs a TV: with none, the sheet says so and offers *Skip tennis for now* (it stays in Tutorial; the gate
     treats it as deferred so golf+bowling players are not stuck forever).
   - **Bowling** (new `BowlingLesson.cs`, 5 stations): roll it, release timing, move & aim, spin, knock 7+ down; then done.
6. **Warnings when loading into any game** (`PlaySafeGate`): the first launch of each sport in an app session holds the game on
   its loading screen (`SportsSession.loadingFinished` waits) until the phone's *Play safe* card is accepted. Online matches
   show it without holding the match.
7. **All three done** (tennis done or deferred) → a short "Everything's unlocked" toast; the gate opens; TUTORIAL stays at the
   top of Play as a replay entry.

## Persistence / migration

- `ftue.step.v3` (`welcome, customize, how, goPlay, tutorial, done`). Tutorial completion: `SportProgress.completeTutorial`
  (already per sport; bowling added). Tennis deferral: `ftue.tennisDeferred.v1`.
- A phone that used the app before (no v2/v3 step, or v2 already finished / a lesson done) is not forced through.
  `-forceOnboarding`, `-resetOnboarding`, `-skipOnboarding`, `-onboardingStep <key>` keep working (DEBUG).

## Gates (binary)

1. NO_AIRPLAY: a fresh install with no display reaches the menu and the intro on the phone. PASS/FAIL.
2. INTRO_ORDER: welcome → customize (Locker opens) → 3 how-it-works cards (incl. the 2 m TV warning) → go-to-Play. Unit test.
3. LOCK: in `.tutorial`, every Play bay except `bay-tutorial-*` is refused by Swift and dimmed in Unity; golf → tennis → bowling
   order enforced. Unit test + Unity EditMode test.
4. UNLOCK: golf+tennis+bowling complete (or tennis deferred with no TV) → gate open, step `.done`. Unit test.
5. SAFETY: first launch of a sport per app session holds loading until accept; second launch does not. Unit test.
6. HOWTO_ANIM: golf, tennis, bowling back-view loops render (frames in `proof/onboarding-v3/`). Snapshot.
7. BOWLING_LESSON: stations advance on passing throws, finish emits `done`. Unity EditMode test.
8. BUILD: iOS simulator build + tests pass; Unity scripts compile in a clone.

Not in this pass: phone/device install (Adnan: no phone builds while away), voice coach, new rewards.

## Revision 2 (Adnan 2026-11-15, later the same evening)

> "we cant do 3d animations … gpt gifs … the animations should only be shown in the tutorial when they are in game, not in the
> onboarding … an onboarding for when they are airplayed to the TV, an overlay type tutorial like most games have, not a dedicated
> screen onboarding … they are on the main menu and they see directions pop up as an overlay … create a recording … start to finish."

- **No 3D.** The SceneKit back-view scene (`HowToPlayScene.swift`, `Tools/howto_render`) is deleted. The how-to animations are 2D GIFs
  made with GPT image generation by Codex: brief `work/onboarding-v3/CODEX_PROMPT_HowToPlay_GIFs.md`, files
  `GolfArcade/Onboarding/HowTo/howto-{golf,tennis,bowling}.gif`. `HowToGIF.swift` plays them.
- **GIFs only in game:** the lesson's first step, in its How it works card on the TV (`LessonExplainer`) or the phone's coach card with
  no TV (`LessonPhoneHUD`). The intro and the play-safe card have no animation (the play-safe card has a still 2 m / 6 ft diagram).
- **Overlay intro:** the full-screen phone cards (`IntroCoach.swift`) are gone. The intro is tips over the live menu, drawn by Unity
  (`MenuHud.Coach.cs`): a card beside the button it is about, a pulsing gold frame round that button, and focus held on it.
  - **On the TV**, the phone stays the remote (arrows + SELECT).
  - **With no TV**, the same tips sit over the menu on the phone; a finger taps them.
  - The phone decides each tip (`OnboardingFlow.coach(tv:)` → `menuCoach` JSON, sent by HubSession); NEXT reports back (`menuCoach <id>`).
  - The tips, in order:
    1. Welcome (NEXT).
    2. Make your player: frames LOCKER. In the Locker, a hint to pick colours and press BACK.
    3. How it works, three tips: swing your phone, big screen or just your phone, play safe.
    4. Start your tutorial: frames PLAY.
    5. Start here: frames TUTORIAL.
    6. The next lesson: frames its row.
  - After a lesson, the menu opens on the Tutorial with "Golf done! Tennis next".
  - At the end: "Everything's unlocked!" (LET'S PLAY).
- **Recording:** `proof/onboarding-v3/onboarding-recording.mp4` is built by `work/onboarding-v3/film.sh`.
  1. The simulator walkthrough test writes the script, the phone frames and the HUD layers.
  2. Unity `OnboardingFilm` replays the script on the real menu and plays the golf lesson's first step.
  3. `film.py` joins it all.
