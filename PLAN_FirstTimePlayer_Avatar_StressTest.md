# First-time player: avatar + stress-test plan (2026-11-21)

Goal: a normal person picks the game up and hits the first "aha" as fast as possible, with nothing in the way.
This doc has two parts. **Part 1** is the avatar: who they are, how they behave, what they will try.
**Part 2** is the test plan: the sessions this avatar plays, what we measure, and the pass/fail gates.

Grounded in the code of `~/onboarding-1121` (newest onboarding and tennis quick start), `PLAN_Playtest_Fixes_1121.md`
(Adnan's 11-21 playtest notes) and `work/replayability-1121/REPLAYABILITY.md`. Nothing is changed by this doc.

---

## Part 1: the avatar

### Maya, 34. "I'll try it, but if it's annoying I'm deleting it."

| | |
|---|---|
| Job | Office manager at a dental practice. On her feet all day, tired in the evening. |
| Home | Apartment, living room about 3.5 × 4 m. Couch 2.5 m from the TV, with a **coffee table in between**. Partner Dev, a cat, friends over about twice a month. |
| Phone | iPhone 13 (not Pro), 6 months behind on iOS updates, storage 85 % full, **Low Power Mode on** most evenings. Silicone case, no wrist strap. AirPods often connected. Auto-Lock 30 s. |
| TV | 2021 Samsung 55". It supports AirPlay 2, but she doesn't know that. She has mirrored photos once, with help. No Apple TV. |
| Games | Played Wii Sports at her aunt's at Christmas years ago and loved bowling. Plays Royal Match and Wordle on the train. Mario Kart at a friend's house a few times a year. Just Dance at a party once. Never owned a console. |
| How she found it | A friend's Instagram reel: someone swings a phone like a golf club and the ball flies on the TV. Caption: "Wii Sports but it's your phone??" |
| What she expects | "Swing my phone, ball goes. Like the Wii." No accounts, no setup, no reading. |
| Patience budget | About **60 s** to the first moment of fun. About **3 min** of total confusion before she closes the app. Three bad moments and she deletes it. |

### How Maya reads and taps
- Reads the **headline only**, about 5–8 words. Never reads a paragraph, and never scrolls a card.
- Taps the **biggest, brightest button**, whatever it says. Shown "Start" and "Not now", she taps the colourful one.
- Says no to any OS permission whose reason she can't see right now ("Why does a golf game want my camera?").
  She will not go to Settings to undo a "Don't Allow".
- "Calibrate", "latency", "AirPlay", "seat", "lobby", "station" mean nothing to her. "Point your phone at the TV" is unclear too: at the screen? the box? how long?
- Treats a still screen with no animation as frozen after about 4 s, and starts tapping.
- If unsure, she taps the screen. **She expects touch controls** because every mobile game she plays has them.

### How Maya moves
- First swings are **small and polite**: embarrassed, scared of dropping the phone or hitting the TV or the cat. Then, after a weak result, **far too hard**.
- Holds the phone **like a phone**: portrait, screen facing her, thumb resting on the glass. Not like a club grip.
- Often plays **sitting on the couch** at first. Stands only when the game clearly asks her to, or after the first fun moment.
- Swings mostly from the wrist and forearm, not the shoulders. Golf swings are short and quick. Tennis swings are a flat wave.
- Watches the **phone screen** during the swing, not the TV, unless the phone screen tells her to look up.
- Right-handed. Dev, who will grab the phone next, is left-handed.

### What Maya will do with the game (predicted, in order)
1. Opens it on the couch with **no TV**. The TV is showing Netflix.
2. Skims the intro tips. Taps through as fast as they appear.
3. Locker: picks a hair colour and a shirt colour quickly. This is the one place she will happily spend 30 s. It feels like Royal Match decorating.
4. Looks for the sport from the reel: **golf**. If tennis is first or most visible, she taps tennis and hits the "needs a TV" wall.
5. Swings softly at the first golf ball. If it goes 40 yd she laughs once. If it goes 40 yd again, she wonders whether she's doing it wrong.
6. Gets a text after 2–3 min, swipes up to Messages, comes back 1–2 min later. Or the phone auto-locks while she reads a card.
7. Calls Dev over: "Try this." **Hands him the phone** in the middle of a lesson.
8. Decides to try it on the TV: "How do I get it on there?" She opens Control Center and hunts for Screen Mirroring, or gives up.
9. If it worked: plays one full short game, then tries a second sport. Bowling, because she remembers it from the Wii.
10. Next day, or at the weekend with friends: opens the app again expecting to **land straight in a game**, and wants a friend's phone to join without anyone making an account.

### What will make Maya quit (her deal-breakers)
- More than about 5 taps or 45 s before her first swing.
- A swing that "didn't work" with no visible reason (no reaction, no ball, wrong direction).
- A wall of text, or a step that needs a word she doesn't know.
- Being told she needs a TV, or a login, or a permission, before anything fun.
- Losing progress after a text message, a call or a lock screen.
- Feeling stupid in front of a friend: the friend takes the phone and also can't make it work.

### Maya's "aha" (what we are racing to)
The first time **the motion she made shows up as the result she meant**, with a big audio-visual payoff:
- **Golf:** a full swing that sends the drive high and far, with the crowd/whoosh, and she says "I did that." Not a 40-yd dribble.
- **Bowling:** the first big pin crash (strike or near strike) from a swing that felt natural.
- **Tennis:** the first return she hits back on purpose, forehand side, that lands in.

Targets: aha within **90 s of first launch with no TV** (golf), and within **3 min with a TV**.

### Variants to run alongside Maya (same tests, different blind spots)
- **Dev, partner, 36, left-handed.** Gets handed the phone mid-flow and has seen none of the screens. Tests "pick up and play from any screen" and left-handed swings.
- **Linda, Maya's mum, 63.** Larger text setting (Dynamic Type), slower swings, reads every word, worried about the TV. Tests accessibility and the safety card.
- **Theo, a friend's kid, 9.** Swings wildly, taps everything, walks toward the TV. Tests safety, mashing and spam taps.
- **Priya, friend at the party, 29.** Has the app on her own phone and wants to join Maya's game. Tests nearby join with no account.

---

## Part 2: the stress-test plan

### Phase 0: set-up before any test (½ day)

1. **One build to test.** The first-run code is spread over several uncommitted worktrees:
   `~/onboarding-1121` (tutorial + quick tennis start), `~/local-setup-1120` (tennis setup + post-game TV),
   `~/playtest-1121` (golf holes 7 and 13 retired), `~/phone-casting-1120` (local join for golf/bowling, casting) and `~/bowl-airplay-1121.patch`.
   Testing any one of them alone gives wrong answers. Combine them into one test branch and make one Release build.
   Release, not Debug: Debug took 24 s to load tennis on 11-15.
2. **True clean install** each run: delete the app, reboot, install. Also reset Location & Privacy
   (Settings > General > Transfer or Reset > Reset Location & Privacy) so every OS prompt shows again.
3. **Test phones:** Maya's phone class (iPhone 13 or older, Low Power Mode on, storage near full), plus one newer phone. One run on an iPhone 12 or SE for memory (jetsam).
4. **Recording rig:** phone screen recording (it captures the app's audio), a tripod camera filming the whole room from behind the player (it shows grip, stance, swing size, and where they look), and the TV in frame.
5. **Missing analytics events.** `Analytics.track` already writes `t=` seconds since install to `SportsDiagnostics.log`
   (`app_first_open`, `onboarding_*`, `tutorial_*`, `playsafe_*`, `golf_hole_done`). That is the funnel's backbone. Add the events the funnel needs:
   - `permission_prompt` with kind and answer (motion, camera, local network, Game Center sheet, microphone, photos)
   - `first_swing` per sport, and `swing` with power, grade and result
   - `shot_result` (golf carry and finish; bowling pins; tennis in/out)
   - `app_background` / `app_foreground` with seconds away, and whether the game survived
   - `tv_connect` / `tv_drop`
   - `game_start` / `game_finish` / `game_quit` per sport and mode
   - `idle_on_screen` (no input for 8 s or more on a screen with a button), `dead_tap` (a tap that hits nothing), `back_press`
6. **Funnel script** `work/first-player/funnel.py`. It reads a pulled `SportsDiagnostics.log`
   (pull with `devicectl device copy from --domain-type appDataContainer --domain-identifier com.adnanandrew.motionsports --source Documents/SportsDiagnostics.log`)
   and prints the scorecard below, timestamps included.

### Scorecard (binary gates for every run)

| Gate | Pass if |
|---|---|
| G1 Time to first swing (no TV) | `first_swing` ≤ 45 s after `app_first_open` |
| G2 Taps to first swing | ≤ 5 taps, Locker excluded if she chose to spend time there |
| G3 Aha, no TV | first golf drive of 150 yd or more, or a strike or 8+ pins, ≤ 90 s after first open |
| G4 Aha, with TV | the same, ≤ 3 min, including getting the picture onto the TV |
| G5 Every swing answered | every `swing` gives visible + audible feedback within 0.3 s, and a failed swing says why in ≤ 6 words |
| G6 Relaxed swing works | a relaxed, polite swing passes every lesson station on the first or second try |
| G7 No reading needed | every first-run screen is understood from its headline (≤ 8 words) and picture; nothing must be read in the body text |
| G8 Prompts in context | every OS permission appears right when its reason is on screen, and a "Don't Allow" leaves a one-tap way to play anyway |
| G9 Interrupt-proof | after background, call, lock or Control Center for up to 3 min, she returns to the same shot/frame/point, nothing lost |
| G10 No dead ends | `dead_tap` ≤ 3 and no `idle_on_screen` over 15 s on any run |
| G11 Hand-off | a second person handed the phone at any screen gets to a swing within 20 s with no help |
| G12 Stable | no crash, no jetsam kill, no frozen loading in the whole run (check the log for a missing `loaded` after `launch`) |
| G13 Day-2 return | a cold launch the next day puts her into a game within 2 taps, with no repeated tutorial or setup |
| G14 Wants more | she starts a second game or a second sport without being asked |

Failures go in a **friction log** (template at the end), each with a severity:
**Blocker** (she would quit or can't go on), **Confused** (stuck for 5 s or more, wrong tap), **Slow** (works, but is a wait or an extra tap), **Polish**.

### Predicted pain points to check first (from the code today)

These come from the code and earlier audits. Each one needs a device run to confirm.

| # | Where Maya hits it | What the code does | Risk |
|---|---|---|---|
| P1 | First golf swings | A relaxed swing reads about 0.6–0.7 power and lands about 30 % short (`MotionSwingDetector.cs:105`, `GolfClub.ForDistance` picks clubs at full power). The new lesson Drive station passes at 100 yd. | Her polite first drive dribbles. The aha is delayed, and G6 may fail. |
| P2 | Taps before first shot | Playtest audit: about 16 taps / 3–4 min from install to the first golf shot. onboarding-1121 cut the intro to 4 tips, but the safety card, tutorial card, lesson card, loading and flyover remain. | G1 and G2 |
| P3 | Local Network prompt | The nearby browse (`HubSession.wantsNearbyBrowse`) starts as soon as onboarding ends and she sits on the menu. iOS then asks to "find devices on your local network", with no context. | She taps Don't Allow, and Priya's phone later can never join (S6). G8 |
| P4 | Camera prompt | Tennis setup asks for the rear camera to find the TV (`SportsMotion.swift:314`). | "Why does it want my camera?" She says no. Is there a working no-camera path? G8 |
| P5 | Tennis with no TV | Tennis needs an external display. The tutorial order is golf → tennis → bowling. | With no TV, the tutorial reaches tennis and stops. Does "skip" let her reach bowling at once? |
| P6 | Getting onto the TV | No in-app help to start Screen Mirroring. Her Samsung's AirPlay is unknown to her. | G4. The "how do I get it on the TV" moment is entirely outside the app. |
| P7 | Putting | Putter moves only a few inches. The lesson now has an explain card, but she won't read it. | A first putt hit with a full swing flies off the green. Does the miss message teach in ≤ 6 words? |
| P8 | Swipe away / text message | Playtest 11-21: swiping out of the app can kill it. Tennis peaks about 3.2 GB of about 3.4 GB. | G9 and G12, worst on her full-storage, older phone |
| P9 | Safety card | Now remembered per sport for 24 h (it used to come back every cold launch). | Linda reads it. Maya taps through. Theo ignores it. Is it ever a wall? |
| P10 | Bowling feel | Speed range is nearly flat; a non-perfect release adds 5–14 boards of random scatter. | Her natural Wii-style swing gives random results, so no aha (G3). |
| P11 | Tennis start time | Known TV is now about 12–15 s, new TV about 30 s (onboarding-1121 T1–T7). | Check this on a real TV with her real swings, not test swings. |

### The test sessions

Each session is a script of **what Maya does**, plus the gates it checks. Run each one in role (see "How to play Maya" below), filmed, with a clean install unless it says otherwise.

**S1. Couch, no TV, golf first** (the most common first run). Gates G1–G3, G5–G7, G10.
1. Opens the app sitting on the couch. TV off.
2. Taps through the intro tips without reading them. Spends about 20 s in the Locker.
3. Taps PLAY, then the biggest button on each card.
4. First swing: small, wrist only, still seated, phone held portrait with thumb on the screen.
5. Next swing: too hard. Then one "normal" swing.
6. First putt: full swing. Second putt: tiny tap.
7. Finishes the golf lesson or quits. Record which, and when.
Check: when does she first stand up, and did the game ask her to? Does anything tell her that a seated wrist flick is the reason for a short shot?

**S2. "Put it on the TV."** Gates G4, G8, G12.
1. Starts as in S1. After the first golf hole, tries to get the picture onto the TV.
2. Looks for a TV button in the app first. Then Control Center. Then asks Dev.
3. Once it mirrors, plays a hole. Then the TV drops (Dev changes the input). Then it comes back.
Check: does the app show her how to mirror? What happens to the round on TV loss? Run on a Samsung (AirPlay 2 built in) and with an Apple TV.

**S3. Tennis first, no TV** (she saw tennis in an ad instead). Gates G7, G10.
1. Clean install, intro, PLAY. Taps tennis straight away, or follows the tutorial to tennis.
Check: is "you need a TV for tennis" said in ≤ 8 words with a one-tap way to golf or bowling, or does she hit a dead end?

**S4. Tennis on a TV, the full first match.** Gates G4, G5, G8, P4, P11.
1. TV mirrored. Starts tennis from the tutorial.
2. Answers the camera prompt "Don't Allow" on one run and "Allow" on another.
3. "Point at the TV": she points at the TV stand, then at the ceiling light, then at the screen.
4. Timing drill: swings late and flat.
5. Plays a short match. Then Rematch. Then Main Menu and start again.
Check: time from START to first serve, new TV and known TV. Does the second match skip setup? Can she play with the camera denied?

**S5. The interruptions** (run during S1 and S4). Gates G9, G12.
At random moments: a text arrives (banner over the game), she swipes up to reply for 60 s;
a phone call comes in; the phone auto-locks while a card is up; she pulls down Control Center mid-swing;
Low Power Mode toggles; AirPods connect or disconnect mid-round; she force-quits from the app switcher, then reopens.
Check: same shot, same hole, no lost lesson progress, sound comes back on the right output, no crash or freeze.

**S6. The party: Priya's phone joins.** Gates G8, G11, P3.
1. Maya has the app open on the menu, maybe with the Local Network prompt denied from earlier.
2. Priya opens the app on her own phone, in the same room.
3. Maya opens LOCAL PLAY golf. Priya should see "Join Maya's golf game?"
4. Repeat on cellular only (no shared Wi-Fi), and with one phone's Bluetooth off.
Check: no account, no code, ≤ 2 taps for Priya. If local network was denied, does the app say so in plain words, with a Settings link?

**S7. Hand the phone over.** Gate G11.
At each of these moments Maya hands the phone to Dev (left-handed, has seen nothing):
an intro tip, the safety card, the tennis point-and-hold step, a lesson station, mid golf swing, the post-game screen.
Check: can Dev tell what to do in ≤ 20 s, from the screen alone? Do left-handed swings work (golf, tennis forehand/backhand, bowling)?

**S8. Skip everything.** Gates G1, G10, G13.
Taps "Not now" or "Skip" on every card: tutorial, lesson, safety, coach tips.
Check: can she still reach a playable game in each sport, and is anything locked forever with no explanation?

**S9. Every way of saying no.** Gate G8.
Motion & Fitness denied; camera denied; local network denied; Game Center sign-in sheet dismissed; microphone and photos denied when asked.
Check: each "no" leaves a working game and a plain one-line notice. Nothing crashes or hangs on a spinner.

**S10. Wrong-way play** (scripted swings, also replayable in Unity tests). Gates G5, G6.
Seated swings; wrist-only flicks; giant full-body swings; phone held landscape; held upside down; screen facing away;
tapping the screen during the swing; swinging before the ball is ready; walking toward the TV mid-swing; two fast swings in a row; a fake swing.
Check: every one gives clear feedback. None silently does nothing. None does something wildly random.

**S11. Day 2 and day 7 return.** Gates G13, G14.
Cold launch the next day; again after a week; again after an iOS update.
Check: she lands on a "play again" choice within 2 taps. No tutorial or setup repeated. The TV timing is remembered. Something new or a reason to play is visible (daily hole in one, skill level).

**S12. The small living room** (safety). Gate G7, P9.
Coffee table 1 m in front of the couch; Theo, aged 9, playing; Linda reading the safety card at large text size.
Check: does the game tell people where to stand, in a picture, before the first swing? Does any text get cut off at large Dynamic Type?

**S13. Old phone, full storage.** Gate G12.
iPhone 12 or SE, storage 95 % full, Low Power Mode on. Install, full tutorial, tennis match, background for 3 min.
Check: loading times, jetsam kills (`launch` without `loaded` in the log), heat, battery drop per 10 min.

### How to play Maya (rules card for whoever runs the tests)

Print this and follow it strictly. The point is to stop knowing the game.
1. Read only the biggest line on any screen. Never read a second line.
2. Always tap the biggest, brightest button.
3. First swing in each sport: small and polite, seated if the game hasn't asked you to stand.
4. If nothing happens within 4 s, tap the screen.
5. Answer every OS prompt on instinct. The camera or local network with no obvious reason gets "Don't Allow".
6. Never open Settings. Never search the web. Never ask the developer.
7. If you are stuck for 15 s, write down where, then take the most obvious action. If stuck for 60 s, the run ends: Blocker.
8. Say out loud what you think is happening, all the way through.

### Three ways to run it

1. **Real people (best signal). 5 people who match Maya**, one session each, about 20 min, think-aloud, no help at all.
   Five people find most of the big problems. Then fix, and test 5 new people.
   Ask each one afterwards: "What was the most fun moment?" (is it the aha?) and "When did you want to quit?"
2. **Adnan or a teammate in role**, using the rules card, for quick passes between builds. Good for S5, S9, S10 and S13, which are mechanical.
3. **Automated, between builds.**
   - Simulator snapshot walk of every first-run screen (the unsigned sim traps in CloudKit, so use `-clubCloudOff` with `saveHosted` / ImageRenderer snapshots).
     Per screen, count headline words, buttons and taps-to-swing. This guards G2 and G7.
   - Unity PlayMode with **recorded swing traces** replayed: polite, relaxed, hard, wrist-only, seated, left-handed.
     Record them once from real people in sessions S1 and S7 (`aimcal`-style trace logging). Assert every lesson station passes with the polite and relaxed traces (G6),
     and that a relaxed drive reaches 150 yd (G3).
   - Funnel script over every test run's log, so the scorecard comes out of each run with no hand timing.

### Friction log template

| Run | Session | t (s) | Screen | What Maya did | What she expected | Severity | Gate | Fix idea |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

### Order of work

1. Phase 0 (combined build, events, funnel script, rig).
2. Run S1, S3, S8 and S9 in role. These are cheap and find the first-run blockers. Fix the Blockers.
3. Run S2, S4 and S6 with a real TV and two phones. These are where the TV, camera and local network can break it.
4. Run S5, S10 and S13 for robustness.
5. 5 real Mayas through S1 → S2 → S4. Then fix and run 5 more.
6. S11 day-2 and day-7 returns with the same people.

Done when every gate passes on two runs in a row with real people, on Maya's phone class.
