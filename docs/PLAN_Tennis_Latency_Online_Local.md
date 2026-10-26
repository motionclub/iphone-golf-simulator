# Tennis: near-zero latency, crash-free online, easy local play — plan (2026-10-24)

Ask (Adnan): figure out the best way to (1) set tennis up so there is next to no latency and (2) have it work
online without crashing, with local multiplayer convenient. This is the research and the plan; nothing in it is
built yet. Every number is from the code on disk today (file:line in the "Evidence" notes) or from outside sources
listed at the end.

## 0. One thing to look at first (crash risk, not mine)

The working tree has an **uncommitted** change that deletes `NSGKFriendListUsageDescription` and
`NSLocalNetworkUsageDescription` from `GolfArcade/Unity/SportsInfo.plist` and from both build configs in
`GolfArcadeUnity.xcodeproj/project.pbxproj`. The code still asks Game Center for the friends list
(`GolfArcade/Social/FriendsSource.swift`) and browses Bonjour (`GolfArcade/Multiplayer/LocalMultiplayerTransport.swift`).
HEAD's own comment on those keys says "without these iOS ends the app". `project.yml` has neither key, so an
xcodegen regenerate also drops them. **Unless they were removed on purpose, restore them before the next build.**

## 1. Latency

### Where the time goes today (phone swing → seen/felt on the TV)

| Stage | Today | Compensated? |
|---|---|---|
| Swing detector: onset (rate 4.2 rad/s + 0.45 g held 30 ms) | ~40–60 ms after the real swing starts | serve yes, **rally no** |
| Hit waits for the phone to *confirm* the swing (peak or 60 ms proof) | +0–40 ms | flight re-simulated, feel not |
| Assisted contact lead (ball flown on to meet the racket) | +45–180 ms before the strike | no |
| Unity: poll once per frame, 120 Hz step, render thread, up to 3 queued drawables on the TV layer | ~25–60 ms | in Lag |
| Game loop paced by the **phone's** display clock, not the TV's | ~1 frame of jitter | in Lag |
| **AirPlay mirroring + Apple TV + TV processing** | **~100–250 ms** (Apple TV measured by others ~100–150) | in Lag (timing only) |
| Wired USB-C/Lightning HDMI instead | ~1 frame + TV processing | — |

What `Lag` (the TV delay the game measures with the camera flash probe) does: it makes a swing that is late by the TV
delay count as on time. It does not make the picture or the TV sound arrive sooner. The strike haptic fires at game
contact, i.e. a full Lag *before* the TV shows the hit.

**Bottom line:** over AirPlay, true zero latency is impossible: the picture is always ~100–250 ms behind the hand.
"Next to no latency" is achievable in what the player *feels*: the hand and ears react instantly, the timing judges
what the player saw, and the picture delay is shrunk where we can.

### Recommended approach (in order of value)

**A. Make the hand and ears the instant channel (feel = 0 ms).** The player's own arm is the reference.
1. Strike haptic and a *phone-speaker* "pock" fire at the moment the phone's own motion reaches contact, judged on
   the phone, not when Unity's racket meets the ball. The phone knows the swing peak within ~10 ms. Today the knock is
   off by default (`arcade.racketSound`). Test it on by default; the TV sound becomes the crowd and the bounce.
2. Keep the TV-side bounce/point cues delayed by Lag (already done) so they line up with the picture.

**B. Remove the delays we add ourselves (~60–120 ms).**
1. Compensate the rally onset's rise and hold (~40 ms) the same way the serve already does (`ServeOnsetLatency`).
2. Resolve the hit on a strong onset when the ball is inside the contact window ("swing prediction" exists as a
   setting). Confirmation can then cancel a false start instead of gating every real hit. Tune with device
   `swingtrace` logs, not by guessing.
3. Shorten the assisted contact lead (max 0.2 s) now that early swings are held (2026-10-24 timing pass).
4. Render: cap queued frames to 1–2 on the **TV** layer (Unity's setting only reaches the phone view), drive the loop
   from the TV's display link, and test with the render thread off. Poll native samples as they arrive.
5. Fix the compensation itself. The lag learner never learns from rally hits (it only runs from TOSS, and only
   without a camera prior). A large Lag also skips almost the whole swing animation, so the racket pops to contact
   on the TV. Advance less and pace the rest.

**C. Shrink the picture delay (the biggest single number).**
1. Detect wired vs AirPlay (today only the AirPlay audio route is checked) and say so in setup. On a cable, expect
   about one frame plus the TV. iPhone 15 and later output HDMI over USB-C; older phones need the Lightning AV adapter.
2. Keep the TV "Game Mode" hint (already there), and show the measured delay in setup ("Your TV: 140 ms — Game
   Mode or a cable makes it faster").
3. **Strategic option (the Wii model): an Apple TV app.** The game runs *on* the Apple TV and phones are controllers
   over local Wi-Fi (a few ms of radio). There is no video stream at all: what remains is the TV panel's own delay,
   like a console. It is a large project (tvOS Unity build, controller pairing, store listing), but it is the only
   way to "next to no latency" for Apple TV owners without a cable. Decide after B and C are measured.

**Targets to measure on device:** hand feel (haptic + pock) ≤ 15 ms after the swing peak. Swing → TV picture:
≤ 80 ms on a cable, ~150 ms on AirPlay to an Apple TV. Measure by filming the phone and the TV together at 240 fps,
alongside the existing `swingtrace` / `-experienceTrace` logs.

## 2. Online that doesn't crash

### What is live today

Tennis online and local both run **peer "Versus"**: each phone runs the full single-player `TennisGame`, judges its
own swings with no network delay, and sends its pose (30 Hz) and its hit launches. The ball's receiver calls the
point. The host-authoritative `NetworkTennisMatch` is not used for tennis (golf still uses the host path).
Transports: Game Center `GKMatch` peer-to-peer online, Bonjour + TCP locally. The Club Hub relay is dormant: it is
not hosted and `ClubHubServerURL` is empty.

**Keep the Versus model. It is the right one for tennis.** Your own hit is instant and judged locally. The other
player's shot is 0.9–1.5 s of deterministic ball flight (Wii pace), which hides a 50–150 ms internet delay; the
code already re-simulates it from the shared-clock launch time. Rollback or host authority would add complexity
for no gain here.

### Fix list, ranked (all found in code; none verified on two phones yet)

1. **Restore the two privacy keys** (section 0).
2. **Never end a match over the bridge queue.** A full reliable queue sets `networkFault` and the guest ejects
   itself, and a failed Unity emit sets `Running=false` for good. Instead: coalesce/drop unreliable traffic, grow the
   queue, call `SportsClear` between matches, and log rather than eject.
3. **One score.** Each phone keeps its own score; nothing checks the two agree, and an 8 s ready fallback can start
   points out of step. Add a point number and score checksum to the ready handshake; on a mismatch the host's score
   wins and is re-sent.
4. **Survive blips.** Today the owner suspends the match after 0.4 s of guest silence, only the owner watches, and
   no transport reconnects (local TCP gives up after ~5 s). Plan: suspend after ~1.5 s, let both sides watch, keep the
   match alive ~30 s for a reconnect, and resume with a state sync (the AwayPolicy's 180 s promise needs this).
5. **Small, always-unreliable pose packets.** The peer JSON is nested and escaped. If Game Center refuses an
   unreliable packet over 900 bytes, the whole peer channel switches to reliable for good, adding head-of-line lag.
   Use a compact binary pose (<200 bytes) and measure it.
6. **Guard the Unity hang paths:** `Configure` throwing inside the loading coroutine, the null `ApplySync`
   result, and the un-null-checked `fx`/`sounds` in Versus.
7. **Test the live path.** `Tools/netsim` only covers the unused host path. Add a Versus harness with loss,
   reliable-packet loss, disconnect and reconnect, plus a two-phone field test (FIELD_TEST.md tables are empty).
8. **NAT fallback (decision):** a direct `GKMatch` sometimes can't connect. Hosting the Club Hub relay (Fly) gives a
   fallback and the friends/invite features. That needs your hosting decision.

## 3. Local multiplayer that's convenient

Today: the host takes 3 taps (Play → Local → Tennis · Two Phones). The guest, on the same Wi-Fi, takes 4 (Play →
Local → Join a Friend → pick the lobby). The 6-character code only picks among lobbies already found nearby. There
is no Plaza bench for local tennis.

Recommended:
1. **One-tap join.** While in the Plaza, browse nearby lobbies in the background and show "Join Adnan's tennis
   game?" as a banner. One tap joins. The host's flow becomes sitting on a local tennis bench in the Plaza.
2. **No shared Wi-Fi needed.** Peer-to-peer Wi-Fi (AWDL) is already enabled on the browser. Make sure the listener
   allows it too, and say "nearby" rather than "same Wi-Fi".
3. **UDP for pose locally.** Today everything local goes over TCP, so one lost packet stalls the stream. Keep TCP
   (or reliable framing) for events.
4. **Fair one-TV play.** On one TV both players watch the same delayed picture, so both must get the same Lag
   credit. Today the controller-only player gets none (the plan's own experiment: 150 ms makes a serve unreturnable).
5. Later: the controller-only phone runs a hidden Unity. A lighter controller mode would save battery and heat.

## 4. Phases

| Phase | What | Size |
|---|---|---|
| P0 | Privacy keys; bridge never ejects; Unity hang guards | ~1 day |
| P1 | Latency quick wins: rally onset compensation, phone-side hit haptic + pock, lag learner + swing-pop fix, TV-layer frame queue / display link, wired detection + setup copy | ~2–4 days + device measurement |
| P2 | Online resilience: score checksum, silence thresholds + reconnect, compact pose packets, Versus test harness | ~1 week + two-phone test |
| P3 | Local convenience: Plaza bench + one-tap nearby join, AWDL listener, UDP pose, shared Lag for one TV | ~3–5 days |
| P4 (decide) | Apple TV app (console model); hosted relay | weeks / your call |

Sources: AirPlay to Apple TV ~100–150 ms (high-speed-camera measurement, moonlight-ios issue #643); wired HDMI ~one
frame (consumer guides; unmeasured); Apple DTS on Bonjour vs MultipeerConnectivity and AWDL peer limits (Apple
Developer Forums threads 687435, 785308, 751839).

## 5. P1 results (2026-10-24): built, EditMode-tested, not yet on a device

Not committed. Everything below is in the working tree. The 10-24 timing pass is untouched: swing direction aims, timing
sets pace, `EarlySwingHold` stays as it was, and grading keeps the old timeline (see 1d).

### 1. Unity (`TennisGame.cs`, `TennisActor.cs`, `TennisRules.cs`)

a. **Rally onset compensation (B1).** A rally stroke now loses the detector's delay, as the serve does:
   `TennisRules.SwingDetectionLatency` gives 40 ms (`ServeOnsetLatency`) for a stroke reported at onset (`BeginSwing`),
   and 100 ms (`ServeLatency`) for one first seen at confirmation on the phone. Keys and tests get 0. The delay is added to
   `inputAge` in `StartRallySwing` → `CompensateDisplayDelay`.
b. **Swing pop (B5).** `CompensateDisplayDelay` used to skip the whole shift in one frame, stopping 20 ms short of
   contact. With ~150 ms of AirPlay, a fast forehand popped straight onto the ball. Now `TennisRules.CatchUp` jumps at
   most 50 ms, plays the rest of the approach up to 3× faster (`PaceToContact`), and never reaches contact in under 60 ms
   (~4 frames at 60 Hz). A small shift (cable, fast TV) is still one plain jump, exactly as before.
c. **Real time to contact.** New `TennisActor.SignedRealTimeToContact` / `RealTimeToContact`: the swing time divided by
   the approach pace. `HoldEarlySwing` and the two rally lateness gradings use it. The hero's clip timing still reads the
   swing-time `SignedTimeToContact`.
d. **Grading unchanged.** The paced racket reaches contact up to 40 ms later than the old jump did (`catchUpLate`), and
   grading subtracts that, so every swing is judged on the old one-jump timeline (asserted over a sweep in
   `TennisLatencyTests`).
e. **Lag learner (B5).** `Learn` no longer stops when a camera measurement exists. The measurement is the learner's prior
   (two votes), as `TennisLagLearner` intends. Rally hits now feed it too, with `hitLateness` plus the share of the TV delay
   that swing really received (`lagApplied`). Overheads and dives are excluded. Still phone-only: no AutoPlay, keyboard,
   touch or tests.
f. **Hand-first strike (A1).** The player's rally and serve strikes go through `StrikeFelt` → `Haptics.HitOnSwing(feel,
   wait = clamp(Lag, 0.12, 0.35))` instead of firing at game contact. The bounce and point cues still play delayed by Lag
   (A2, unchanged).

### 2. Native and Swift

- `GolfHaptics.mm`: every haptic call now runs on one serial queue (`Feel()`) instead of the main thread. UIKit
  fallbacks hop to main. `GolfHaptics_HitOnSwing` holds the strike. `GolfHaptics_SwingContact` (exported for dlsym)
  plays it. A strike decided within 200 ms after a contact plays at once. Otherwise it plays at the next contact, or
  after `wait`. While a strike waits, the confirmation swish is skipped. The phone-speaker knock plays with the strike.
- `SteeringFilter.swift`: new `contacts` counter. It ticks once per stroke, the first time the rotation tops out
  (`topping`, arc ≥ 0.3 rad, stroke force), whether swing prediction is on or off.
  `SportsMotion.consume` calls `RacketFeel.swingReachedBall()` (nonisolated, dlsym) straight from the motion queue,
  with no main-thread hop.
- `SportsSession.racketSound` is **on by default** (unset key → true), per A1's "test it on by default". It is a proposal:
  flip the default back in `SportsSession.swift` if the device listen says no. Note: system sounds obey the ring/silent
  switch, so a silenced phone gives no knock.
- `SportsUnityAppController.mm`: the TV's `CAMetalLayer` gets `maximumDrawableCount = 2` (Metal's minimum; Unity's
  `maxQueuedFrames` only reaches the phone layer). Launch with `-sportsTVQueuedFrames 3` to compare. **Experiment, off by
  default:** `-sportsTVClock YES` drives Unity's loop from the TV screen's display link. If any TV scene disconnects,
  the loop goes back to the phone's link.
- Wired vs AirPlay (C1–2): `SportsTiming.Link` / `currentLink()` reads the audio route (`.HDMI` = cable, `.airPlay`).
  `SportsTiming.advice` writes the setup line. Example: "Your TV over AirPlay: 140 ms. A USB-C to HDMI cable or the TV's
  Game Mode makes it faster." `delayTip` was set before but never shown. It now appears in the timing step and on the
  Ready panel, and the link type is logged in SportsDiagnostics.

### 3. Verification so far

- EditMode, APFS clone (`~/p1-latency-UnityClone`, Unity 6000.3.24f1 through heavy.sh, GOLF_MUTE=1): 678/681 pass,
  including the 5 new `TennisLatencyTests`. The 3 failures are not P1: two tests read paths outside the clone
  (`../GolfArcade`, `../proof`), and `BowlingPhysicsTests.PinDeckSmoke` belongs to the untracked bowling work.
- `GolfHaptics.mm` and `SportsUnityAppController.mm` pass a clang syntax check against the iOS SDK. `swiftc -typecheck`
  of all GolfArcade sources (Swift 6, iOS simulator SDK) passes: no errors, and the only warnings are old ones.
- **Not run:** PlayMode, XCTest (`SportsDelayProbeTests.testScreenLinkAndAdvice` was added), and any device test.
  PlayMode tests that call `BeginSwing` mid-rally now get the 40 ms onset compensation. Sweeps keyed to the exact swing
  moment (`TennisTimingBalancePlayTests` onset path) may shift by that amount, which is intended, so re-baseline them
  rather than revert.

### 4. Still needs a device measurement

Film the phone and the TV together at 240 fps, with `swingtrace` and `-experienceTrace` logs on:

1. **Hand feel:** strike haptic + knock after the swing's rotation peak. Target ≤ 15 ms. Check how often the strike falls
   back to `wait` (no peak seen), and that a premature `topping` on gyro noise doesn't fire it early.
2. **Onset compensation:** the median rally `lastLateMs` with and without the 40 ms. It should centre on 0 for a player
   who is on time.
3. **Lag learner:** over a match, does `lagMs` settle near the camera prior plus the player's real bias, without
   drifting? Watch the `[TennisBalance]` lines.
4. **Swing pop:** at Lag ≥ 150 ms, the racket should travel visibly (≥ 3 frames) into the ball. Also confirm the
   up-to-40 ms later visible contact doesn't make honest-contact misses (`HonestMisses`) go up.
5. **TV queue:** swing → TV picture with 2 vs 3 drawables (`-sportsTVQueuedFrames 3`), and the frame rate under load
   (2 drawables can stall a heavy frame).
6. **TV clock:** `-sportsTVClock YES` vs off. Measure jitter and swing → picture, and unplug or stop AirPlay mid-match
   to confirm the loop falls back to the phone and never freezes.
7. **Cable:** swing → picture over USB-C HDMI (target ≤ 80 ms), and that the route reports `.HDMI` so setup says "cable".
8. **Knock default:** does on-by-default sound right next to the TV's hit sound (echo or double hit)? Adnan decides.

## 6. P0 + P2 results (2026-10-24/25): online resilience, built and tested off-device

Not committed; everything is in the working tree. The live peer Versus model stays (`SportsMultiplayer.TennisVersusEnabled`
is still true; `NetworkTennisMatch` is untouched). The two privacy keys of section 0 were restored separately (Adnan approved;
the keys are in `SportsInfo.plist`, both build configs and `project.yml`), not in this work. No touch-play paths were touched.

### 1. What changed

**Bridge never ends a match (P0, fix 2).**
- `SportsBridge.mm`: the network queues never refuse a match's packet. Past 128 entries an unreliable packet (pose, clock)
  evicts the oldest unreliable one, or is dropped itself. Reliable packets grow the queue to 1024, and only past that is the
  oldest lost. The loss is reported as a `bridgeError` that carries a count. New `SportsNetworkClear()` empties only the two
  network queues; a sport session's inputs and motion samples stay.
- `SportsRuntime.h/.mm`: `clearNetwork`. `MultiplayerService.launch` calls it (`clearRuntime`) at every match launch.
- `MultiplayerService`: a `bridgeError` is logged, never an interrupt (owner) or a self-eject (guest).
- `SportsMultiplayer.Send`: a refused emit is counted (`EmitFailures`) and logged; it no longer sets `Running=false`.

**Unity hang guards (P0, fix 6).**
- `NativeSportsSession.Load`: a `SportsMultiplayer.Configure` that throws ends the load with an `error` event (the phone's
  `failStartup`), instead of killing the coroutine with the cover up.
- `SportsMultiplayer.Configure`: a half-done `Initialize` is undone (`Shutdown`) before the error goes up.
- Versus `ApplySync`: an empty, unreadable or unplayable score (`VersusWire.Playable`; JsonUtility makes an empty
  `TennisMatch` of "") is refused and the phone keeps waiting. `RemoteHit` null-checks `fx` and `sounds`.

**One score (P2, fix 3).**
- Every `ready` carries the point number and a checksum of the whole score as seat 0 sees it (`VersusWire.ScoreChecksum`).
- A point starts only when the other phone is ready for the same point with the same checksum. The 8 s "playing on"
  fallback is gone.
- The phones are out of step when the other is ready for another point, has another checksum, or is still not ready 6 s
  (`VersusBehindAfter`) after this phone. Then the **host's score wins**: it sends `sync` (reason `resync`) and goes back to
  its own ready gate. If the host is mid-point, that point starts again on both phones. The guest takes the score and says
  ready again. A guest that finds the mismatch first asks with `resync`.
- **Rally stall watch:** a rally that has waited 6 s (`VersusStallAfter`) on the other phone's shot or call means a message
  was lost while the link stayed up. The same resync runs and the point is replayed. Before this fix, a lost `hit` or
  `point` left both phones waiting forever.
- AwayPolicy hand-back: when both phones thought the other was away and both handed back, the host's score now stands
  (it was "seat 0's"). A single hand-back is still taken as before.
- A sync no longer clears the inbox, so the ready that follows it is not lost.
- **CPU cover keeps the pose** (found by the link-cut harness). After a dropped link, *both* phones put the CPU on the other
  player after 2 s. While the CPU covered, a phone used to send nothing but `sync`, so neither phone heard the other come
  back, and each played its own match against the CPU to the end. Now the 30 Hz pose still goes out, so each phone hears the
  other, hands back at its next point, and the host's score stands.

**Survive blips (P2, fix 4).**
- `MultiplayerTuning.silenceSeconds` 0.4 → **1.5 s**. Tennis flights are 0.9–1.5 s of deterministic ball, so a shorter gap
  is played through.
- **Both sides watch.** A guest that hears nothing from the owner for 1.5 s holds its own game: a local `suspend`, which
  Unity now accepts from this phone itself. It resumes after 3 packets and never speaks for the lobby.
- Nearby (Bonjour/TCP): mid-match, a guest whose connection to the host breaks dials the same lobby again, once a second, for
  **30 s** (`MultiplayerTuning.reconnectSeconds`, `LocalMultiplayerTransport.holdForReconnect`). Only after that does the
  error end its match. The host takes the re-dial in place of the dead connection (same id, same lobby secret).
- When the reconnected guest repeats its old load report, the owner reads it as the same Unity load: the guest is marked
  loaded again and play resumes, with no reload.
- The TCP keepalive is unchanged (~5 s): it still finds a dead connection fast, and the re-dial does the rest.
- Game Center already re-invites a dropped player (`shouldReinviteDisconnectedPlayer` → true). The owner holds the place
  for 180 s (AwayPolicy). Unity's CPU covers after 2 s of silence (`RivalAwayAfter`) and hands back with a score sync.

**Compact, always-unreliable pose (P2, fix 5).**
- The 30 Hz pose is one line of text (`VersusWire.EncodePose`: `P|seat|point|time|x|z|vx|vz|prep|pt|wind|flags`).
- **Measured:** a 61-byte payload in a 298-byte packet with real-length ids. The old JSON pose was a 491-byte payload in an
  826-byte packet, against the 900-byte refusal limit.
- `MultiplayerService.sendPacket`: a refused unreliable `peer` packet is dropped and counted. The `peer` kind is never
  switched to reliable.

### 2. Tests

| Test | Result |
|---|---|
| Unity EditMode, full suite, APFS clone `~/online-resilience-UnityClone/U` (heavy.sh, GOLF_MUTE=1) | **688/688 pass**. That includes 7 new `VersusWireTests` (pose round trip, size, broken poses, both seats' checksum agree, one point more changes it, empty sync not playable, ready keeps n+sum). The two tests that read `../GolfArcade` and `../proof` pass once those are linked into the clone. |
| XCTest `GolfArcadeTests/MultiplayerTests` (GolfArcade.xcodeproj, iPhone 17 Pro simulator) | **96/96 pass**. New: bridge overflow plays on; silence limit (no pause at 1.2 s, pause by 1.7 s); guest holds for a quiet owner and resumes; reconnected guest resumes without a reload; refused pose dropped, peer stays unreliable; pose packet < 400 bytes; full reliable bridge + launch clears it. Updated: the old 0.4 s and bridge-interrupts tests. |
| Native bridge (`work/tennis-online-resilience/bridge_test.cpp`, the real `SportsBridge.mm`) | **PASS, 10/10.** The same test on HEAD's bridge fails 6 of 10. |
| Versus harness, baseline (60 ms ± 25 ms, 3 % pose loss; both seats batch mode) | **PASS**: both matches finished (6 points), same score, 0 mismatches, 0 bridge refusals, 0 exceptions. |
| Versus harness, reliable loss (`MP_RELIABLE_LOSS=0.03`: 3 % of every non-pose message lost) | **PASS**: a 3-game match of 27 points. 18 calls, shots or readies were lost; 8 rally stalls and 2 out-of-step readies were caught, and 6 host resyncs were taken. Same final score on both phones. |
| Versus harness, link cut (`MP_CUT_AT=40 MP_CUT_FOR=20`, with the 1.5 s silence watch played) | **PASS**: both phones held at 1.5 s and the CPU covered at 2 s. When the link came back they heard each other, both handed back, and the guest took the host's score at point 6. 25 points, same final score. (The first run FAILED: see "CPU cover keeps the pose" above.) |
| Versus harness, app away (`MP_AWAY_SEAT=1`, 20 s out of the app; existing AwayPolicy path, regression) | **PASS**: the CPU covered, and the guest rejoined at point 5 with the host's score. Same final score. |

The baseline and loss runs were made before the CPU-pose fix. They never entered CPU cover (0 takeovers), so that fix
cannot change them; the link-cut and app-away runs used the final code.

How to run (Unity runs go through heavy.sh, in the APFS clones `~/online-resilience-UnityClone/U` and `U2`; `retry.sh` waits
for a quiet machine and re-runs when heavy.sh's brake stopped a seat):

```bash
work/tennis-online-resilience/retry.sh loss "--loss" -- MP_GAMES=3 MP_SECONDS=600 MP_RELIABLE_LOSS=0.03
work/tennis-online-resilience/retry.sh cut "--cut" -- MP_GAMES=3 MP_SECONDS=600 MP_CUT_AT=40 MP_CUT_FOR=20
```

The harness is `Unity/Assets/Tests/PlayMode/VersusPeerCapture.cs`. It is skipped unless `MP_VERSUS=1`. The gate is
`vcheck.py`. It also logs a `state` line every 10 s (`TennisGame.VersusState`).

The harness also got a fix: a scripted toss made before the serve was ready (during a long intro) was never retried, so
one seat sat in serve-hold forever. That was a harness bug, not a game bug.

### 3. Two-phone field test (P2): fill in on real phones

Use two iPhones, each with its own TV (AirPlay or cable), plus one run on one shared TV. Before each match, set
`SportsDiagnostics.log` to collect. After each match, note the `multiplayer … owner/guest:` stats line and any `[Versus]`
lines.

| # | Setup | What to do | Pass when | Result |
|---|---|---|---|---|
| 1 | Online (Game Center), same Wi-Fi | Play a full one-set match | Same score on both phones at every point, no "out of step" line, no suspend in the log | |
| 2 | Online, one phone on 5G/LTE | Full match | As 1. Note the stats' rtt median/p95, ping loss, quiet pauses | |
| 3 | Online | Mid-rally, turn Wi-Fi off on the guest for ~1 s, then on | No pause (< 1.5 s), point plays on, same score | |
| 4 | Online | Guest Wi-Fi off for ~5 s mid-point | Both hold at 1.5 s; the CPU covers after 2 s; on return "is back" at the next point; same score after | |
| 5 | Online | Guest Wi-Fi off for 40 s | As 4; the guest's place kept (180 s); match finishes | |
| 6 | Online | Host leaves the app for 20 s mid-match | The guest plays the CPU; the host rejoins with the guest's score; same score after | |
| 7 | Nearby (Bonjour) | Full match | As 1 | |
| 8 | Nearby | Mid-match, walk the guest out of Wi-Fi range for ~10 s and back | The guest re-dials (log: no "local lobby closed" error within 30 s), resumes without reloading, same score | |
| 9 | Nearby | Same as 8 for 45 s | After 30 s the guest's match ends with an error; the host's continues vs CPU and finishes | |
| 10 | Either | During a heavy moment (intro flyover, replay) send emotes and chat | No `bridge overflow` line in the log; if one appears, the match still plays on | |
| 11 | Either | 20 matches back to back, rematch each time | No match fails to start (the bridge is cleared at each launch), no growth in packet loss | |
| 12 | One shared TV, two phones | Full match | Same score; note any `out of step` lines | |

Record any `[Versus] out of step`, `no shot or call` or `starts again` line with the time. They are recoveries, but each
one means a message was lost and should be rare on a real link.

### 4. Open / follow-ups

- The privacy keys (section 0) are restored (Adnan approved, done in another session).
- The two-phone field test (§6.3) is for Adnan, once all the changes are in.
- The silence watch only holds the game. Deciding when the CPU takes over is still Unity's `RivalAwayAfter` (2 s), so a
  blip between 1.5 and 2 s pauses and then resumes. Tune `RivalAwayAfter` after field tests 3–4 if that feels jumpy.
- When the score check finds the phones out of step, the host's score wins, so a point only one phone saw is replayed or
  dropped. This is by design (fix 3). A lost call on a real link should be very rare. Count the `out of step` lines in the
  field test.
- The NAT fallback / hosted relay (fix 8) is not started. P3 (local convenience): see §7.

## 7. P3 results (2026-10-25): local play made convenient, built and tested off-device

Not committed; everything is in the working tree, on top of §6 (nothing there was reverted). Adnan's correction mid-way: the game
now has a regular menu, not the walk-around Plaza, so nothing here depends on walking. A walk-in bench was built first and then
removed again (Unity `HubLayout`/`HubBayScreen`/`HubLayoutTests` are back as they were). No touch-play paths. `TennisGame.cs`,
`TennisRules`, `TennisActor` and `SteeringFilter` are untouched; the only TennisGame change is one method in the `TennisGame.Split.cs`
partial (below). `SportsInfo.plist`, `project.pbxproj` and `project.yml` are untouched.

### 1. What changed

**One-tap host and join (item 1).**
- Host: one menu action, "Tennis with a friend nearby". On the phone menu it is a new row on the Play list (`partyNearbyTennis`,
  `TennisMenu.rows(.party)`, `IslandScreens`). It opens the station id `bay-tennis-nearby` → `HubSession.useNearbyBench()`: a quick
  nearby lobby (`hostLocal(quick: .tennis)`) that readies the host and starts the match by itself as soon as a friend's phone is in.
  Its panel (`HubNearbyBenchPanel`: "Waiting for a friend nearby…", the 6-character code as a fallback, Cancel) shows over any menu
  (`SportsHome`). Cancel before a match ends the hosted game. In a friends' party it is refused (it would break the party up).
- Guest: while this phone could join (`ClubHub.canJoinNow`, the same rule the 10-25 Game Center invite handshake uses: no match,
  nothing loading, not onboarding, in the foreground) and it is in no lobby and not searching, it browses Nearby in the background
  (`browseLocal(quiet: true)`: errors are not shown; a refused Local Network permission just stops it). A tennis game with room shows
  as a banner over any menu: **"Join Adnan's tennis game?" [Join] [✕]**. Join connects and the match starts by itself on both phones;
  ✕ hides that game (a new game from the same phone shows again). When the phone cannot join now, the browse pauses and nothing is
  offered, so there is no deferred join; the Game Center invite handshake is unchanged. `SportsHome` drives it 4×/s
  (`HubSession.nearbyTick`). The first browse is when iOS asks for Local Network access.
- `MultiplayerService.leave()` and `bind()` now stop a browse-only Nearby transport (it used to keep browsing unowned).
- **Pointer menu** (branch `menu/pointer-menu`, checkout `outputs/pointer-menu`, not edited here): add one row to the tennis list in
  `Unity/Assets/Scripts/Hub/Menu/MenuHud.cs` (the `var rows = tennis ? new[] { … }` line). It sends `menuOpen bay-tennis-nearby`,
  which `HubSession.useStation` routes to `useNearbyBench()` (bring this HubSession change along when the branches meet):

  ```csharp
  ("bay-tennis-nearby", "NEARBY", "Two phones, one TV", true),
  ```

  (insert it after the `bay-tennis-online` entry; `true` = locked while friends are in your party, like the solo modes; add
  `case "bay-tennis-nearby": "Nearby"` to `HubSession.menuLaunchLabel` there for the loader's mode name.)

**Tap counts (from the menu's home screen, up to the match loading; the tennis setup, point at the TV + Ready, is unchanged):**

| | Before | Phone menu (now) | Pointer menu (with the row above) |
|---|---|---|---|
| Host | 3 (Play → Local → Tennis · Two Phones) | **2** (Play → Tennis with a friend nearby) | **3** selects (Play → Tennis → Nearby), the same depth as every tennis mode |
| Guest | 4 (Play → Local → Join a Friend → pick the lobby), same Wi-Fi only | **1** (Join on the banner) | **1** (Join on the banner) |

**No shared Wi-Fi needed (item 2).** The listener, the browser and every connection already used `includePeerToPeer` (AWDL); the new
UDP listener and flows do too. Multiplayer copy now says "nearby" / "phones in the same room (no shared Wi-Fi needed)" instead of
"same Wi-Fi" (Local/Join a Friend rows, the nearby screen, How-to cards, the join-code and timeout errors). The AirPlay lines that
really need the TV's Wi-Fi are unchanged.

**Pose over UDP locally (item 3).** `LocalMultiplayerTransport`: the host also listens on a UDP port (no Bonjour service of its own,
so no Info.plist change) and names it in its TCP hello (`Hello.udp`; an older phone sends none and everything stays on TCP). The guest
opens a datagram flow to the host's address and sends a datagram hello (its id + the lobby secret) every 0.5 s, which the host answers.
Unreliable packets (the 30 Hz VersusWire pose, pings, heartbeats) go as one datagram each while a datagram from that peer arrived in
the last 1.5 s and the packet fits 1200 bytes; otherwise they fall back to TCP (a network that blocks UDP still plays). Lobby, hit,
point, ready and sync messages stay on TCP. The sequence check in `MultiplayerService.receive` drops late or reordered datagrams.
Reconnect (§6) keeps working: a re-dialled guest opens a fresh flow, which replaces the old one on the host; a guest flow that fails
is reopened after 1 s. UDP uses Wi-Fi's voice queue (`serviceClass = .interactiveVoice`). The match's stats line now ends with
`datagrams=sent/received` (0/0 = everything went over TCP).

**Fair one-TV play (item 4).** The controller-only phone did get the TV phone's delay, but only a camera/timing measurement stored
before the match (`setScreenDelay(startingLag)` at launch, only if > 0). Online and Nearby matches run neither the flash probe nor the
timing check, so on a TV without a stored measurement the controller-only player got 0 while the TV phone's game learned its own TV
credit from play (P1 lag learner). Now:
- The TV phone (view `split`) reports its game's live TV credit: Unity emits `screenLag` (ms) whenever `TennisGame.Lag` moves by
  ≥ 10 ms (`NativeSportsSession`, 4 Hz block); `SportsSession` sends it to the lobby (`setScreenDelay`).
- The controller-only phone applies each new value with a new `sharedLatency` command → `TennisGame.ShareDisplayLatency`
  (`TennisGame.Split.cs`, the one TennisGame change): the first value seeds the lag learner like `DisplayLatency`; later ones move only
  its prior, so this phone's own swings keep refining it (setting `DisplayLatency` again would have thrown them away). Before any
  learning both players get exactly the same credit; after, each is the shared TV delay plus that player's own timing.

### 2. Tests

| Test | Result |
|---|---|
| XCTest `GolfArcadeTests/MultiplayerTests` (iPhone 17 Pro simulator) | **99/99 pass** (§6's 96 + 3 new). New: `testOneMenuActionHostsAndTheBannerJoinsInOneTap` (one action hosts; a free phone browses; the banner offers the game; one tap joins and the match starts on both phones; joining ends the browse without a second call), `testNearbyBannerDismissBusyPhonesAndCancelling` (only tennis games with room; ✕ per game; browse pauses while loading/onboarding per `canJoinNow`; cancel ends the hosted game; refused inside a friends' party), `testNearbyPosesTravelAsDatagramsAndSurviveAReconnect` (real sockets on loopback: unreliable → UDP, reliable → TCP, oversize → TCP; the host's TCP side is cut mid-match, the guest re-dials within the 30 s hold with no error and datagrams flow again on a fresh flow). |
| XCTest `HubPartyTests`, `HubSessionTests` | 16/16, 8/8 pass. |
| XCTest `MenuBetaTests` | 7/7 pass on `GolfArcade.xcodeproj` (Play list now has the nearby row). |
| Unity EditMode, full suite, APFS clone `~/p3-local-UnityClone/U` (heavy.sh, GOLF_MUTE=1) | **700/700 pass.** |
| Versus harness, baseline (`work/tennis-online-resilience/retry.sh`, clones `~/p3-local-UnityClone/U` + `U2`) | **PASS**: both matches finished, same final score, no exceptions, the bridge never refused a packet. |
| Versus harness, link cut (`MP_CUT_AT=40 MP_CUT_FOR=20`, 3 games) | **PASS**: both held at 1.5 s, the CPU covered at 2 s, both heard each other again, the guest rejoined at point 6 with the host's score; 28 points, same final score. |

Notes:
- The Versus harness drives Unity's own peer sockets, not `LocalMultiplayerTransport`, so it proves the Unity side (VersusWire,
  `sharedLatency`/`screenLag` additions) is intact; the Swift UDP path is covered by the loopback XCTest above.
- Mid-session another session deleted 8 `GolfArcade/Onboarding/*.swift` files and added `LessonCenter.swift`/`OnboardingTV.swift`
  without updating `GolfArcade.xcodeproj`, so that project stopped building. The last full run above was made on a temporary xcodegen
  project from `project.yml` (deleted afterwards; `project.yml` untouched), where `MenuBetaTests.testFeedbackAndBundledGameplay` fails
  only because that scratch project does not set the "Motion Club" display name; it passed on `GolfArcade.xcodeproj` before.
- Not run: PlayMode beyond the harness, any device test, the split-screen `screenLag` → `sharedLatency` round trip (needs a TV
  phone; see field test 9–10).

### 3. Two-phone local test (Adnan, on real phones)

Before each match set `SportsDiagnostics.log` to collect; after it note the `multiplayer … owner/guest:` stats line (with
`datagrams=`) and any `[Versus]` lines.

| # | Setup | What to do | Pass when | Result |
|---|---|---|---|---|
| 1 | Phone A with a TV, phone B without, same Wi-Fi | A: Play → Tennis with a friend nearby. B: stay on the menu | Within ~5 s B shows "Join A's tennis game?"; one tap on Join → the match loads on A's TV, B is the controller (split screen) | |
| 2 | As 1, B not joined to any Wi-Fi network (Wi-Fi on), or the two on different networks | Same | The banner still appears and the match plays (peer-to-peer Wi-Fi) | |
| 3 | Fresh install on B | Open the app, reach the menu | iOS asks for Local Network once. Allow → banner works. Deny → no banner, no error on the menu | |
| 4 | As 1 | B taps ✕; then A cancels and hosts again | ✕ hides it; A's new game shows on B again | |
| 5 | As 1 | A cancels before B joins | B's banner disappears within a few seconds; tapping Join on a stale banner says it couldn't reach the game (no hang) | |
| 6 | As 1, B in a match / loading / onboarding | A hosts | No banner on B until B is back on the menu | |
| 7 | As 1, full match | Play a set | Stats line shows `datagrams=` well above 0 on both phones; poses smooth; same score | |
| 8 | As 7 | Mid-match walk B out of range ~10 s and back | B re-dials (§6 test 8), play resumes, `datagrams` keeps rising after the return | |
| 9 | One TV, TV phone with **no** stored timing for this TV | Play 3+ games, controller-only player receiving serves | The controller-only phone's `[TennisBalance] lagMs` follows the TV phone's (not 0) after the TV phone's first learned hits; serves are returnable for both | |
| 10 | One TV, TV phone with a stored timing (run the timing check once solo on that TV) | Same | Both phones start at the same lagMs from the first point | |
| 11 | Two phones, two TVs, nearby | Host + Join as in 1 | Each phone shows its own court (near view); plays as an online match does | |
| 12 | Nearby on a network that blocks UDP (if available, e.g. a guest network) | Full match | Plays; `datagrams=0/0` (TCP fallback) | |

## 8. P1b results (2026-10-25): the rest of section 1 B, and the test runs P1 skipped

Not committed; everything is in the working tree. The 10-24 timing rule (swing direction aims, timing sets pace and depth,
`EarlySwingHold`, Wii pace) and P1's grading timeline are unchanged. No touch-play, multiplayer, Versus, Split or Hub file
was edited.

### 1. B2: a stroke that proves itself strikes without waiting for confirmation (built)

Today a rally stroke starts at the phone's onset (provisional). A contact before the phone's confirmation waits in
`PendingHit` for up to `ConfirmGrace` (0.14 s). Replaying the 45 real strokes in the device swingtrace logs
(`work/timing-point-fix/phone-before.log`, `work/latency-fix/phone-before.log`) through today's detector shows that
confirmation comes a median of **60 ms** after onset (30–132 ms). P1's catch-up never brings the racket to the ball sooner
than 60 ms after onset, so for about half of all strokes the hit sat waiting.

- **What "proven" means.** Swing prediction on (the phone's setting) and, since onset, a rotation of at least
  `TennisRules.ProvenRate` = 7 rad/s with `ProvenArc` = 0.3 rad of turn. That is the evidence the phone's own peak
  confirmation already accepts (`SteeringFilter.peakConfirmRate` / `peakArc`, after an onset that held the stroke's force
  for 30 ms), without waiting for the rate to top out. The SteeringFilter thresholds are unchanged. An EditMode test fails
  if the two copies drift apart.
- **On the device data:** 44 of 45 confirmed strokes are proven, a median **20 ms** (0–41 ms) before their confirmation. The one
  stroke the phone wrote off was never proven (peak 4.8 rad/s): **0 false starts** (`work/tennis-latency-p1b/replay_swingtrace.py`).
- **Code.**
  - `SportsMotion.swift` sets a new sample flag `SportsSamplePrediction` (= 4, `SportsRuntime.h`) while the filter's
    `peakConfirm` is on.
  - `NativeSportsSession` feeds every polled sample, not only the newest, to `TennisRules.OnsetStrength`. When a stroke is
    proven, it calls `TennisGame.SwingProven()` after that stroke's onset has been applied.
  - In `TennisGame`, `StrikeReady` (confirmed **or** proven) replaces "not provisional" in `Strike` and `ResolvePending`. A
    contact on a proven stroke strikes at once, and a held one goes as soon as the racket reaches the ball.
  - A proven stroke is not dropped by the 0.32 s provisional timeout. Its aim locks at the proof, as it would at confirmation.
- **False starts.** A write-off (abort) before the ball leaves still cancels the stroke and its hit. A proven stroke whose ball
  has already left stands. It is counted in `TennisGame.ProvenWriteOffs` and logged `[TennisLatency] proven stroke written off
  after it struck`; the device data says this never happens. A late confirmation only settles the power; it no longer
  overwrites the hit's feedback line.
- **Measured** with a PlayMode sweep through the real `TennisGame` (`work/tennis-latency-p1b/ZLatencySweep.cs.txt`, results in
  `runs/U-sweep-fresh2`). It steps the swing time by 20 ms on three ball sides, and each trial uses one of the 45 device strokes'
  onset → proven → confirmed timings. The rally, stamina and lag learner are reset every trial. Paths: "today" waits for the
  confirmation; "B2" strikes when proven.

| TV delay | path | swings | returned | honest misses | lateness of returns (s) | mean grade | mean pace (m/s) |
|---|---|---|---|---|---|---|---|
| 0 ms | today (waits for confirmation) | 138 | 61 | 20 | -0.30 … +0.14 | 2.38 | 16.6 |
| 0 ms | B2 (strikes when proven) | 138 | 70 | 12 | -0.31 … +0.15 | 2.36 | 16.5 |
| 0 ms | confirmed at start (keys, stale onset) | 138 | 62 | 9 | -0.30 … +0.10 | 2.45 | 16.6 |
| 150 ms | today (waits for confirmation) | 138 | 48 | 22 | -0.34 … +0.02 | 1.62 | 14.6 |
| 150 ms | B2 (strikes when proven) | 138 | 56 | 13 | -0.35 … +0.04 | 2.14 | 15.8 |
| 150 ms | confirmed at start (keys, stale onset) | 138 | 58 | 14 | -0.36 … +0.04 | 2.12 | 15.8 |

  - **Late swings now connect.** Swings that are late but in reach used to sit in `PendingHit` until a slow confirmation
    (70–130 ms on the device), and the racket had passed the ball by the time it was released: an honest-contact miss, seen
    as NO CONTACT. With B2 they connect: **+9 / +8 returns and 8–9 fewer honest misses** at 0 / 150 ms of TV delay.
  - **The contact window gets no narrower** (lateness of returns −0.31 … +0.15 s at 0 ms, −0.35 … +0.04 s at 150 ms, vs
    −0.30 … +0.14 and −0.34 … +0.02 today). Timing grades are unchanged, because a hit is still graded on when the player swung.
  - **Swings that connect either way strike at the same moment** (matched trials differ by a mean of ≈ 1 ms). Early swings held by
    `EarlySwingHold` had their confirmation long before the ball arrived, so B2 doesn't change them; they show ±1–2 frames of
    jitter in both directions.
  - **Harness caveat.** An earlier version of this sweep let the lag learner drift from trial to trial (the sweep sets
    `NativeControlled`, so every hit teaches it). That made the earliest held swings flip between the paths. With the learner
    reset per trial, one or two flips are left per delay, in both directions.

### 2. B3: shorter assisted contact lead (measured, not adopted)

Swept `MinContactLead` / `MaxContactLead` / the 1.6 × time-to-contact factor at 0.05/0.2/1.6 (today), 0.04/0.12/1.2,
0.03/0.1/1.2, 0.03/0.08/1.0 and 0.02/0.06/1.0, each at 0 and 150 ms of TV delay, on the confirm, onset and proven paths
(`runs/U-leads2`):

| lead min/max/factor | path | returned (0 / 150 ms) | honest misses (0 / 150 ms) | swing → strike, unheld (ms) |
|---|---|---|---|---|
| 0.05 / 0.2 / 1.6 | confirm | 60 / 57 | 12 / 13 | 56 |
| 0.05 / 0.2 / 1.6 | onset | 62 / 58 | 15 / 13 | 81 |
| 0.05 / 0.2 / 1.6 | proven | 63 / 56 | 11 / 14 | 80 |
| 0.04 / 0.12 / 1.2 | confirm | 60 / 58 | 14 / 14 | 53 |
| 0.04 / 0.12 / 1.2 | onset | 60 / 59 | 20 / 18 | 85 |
| 0.04 / 0.12 / 1.2 | proven | 63 / 58 | 12 / 13 | 74 |
| 0.03 / 0.1 / 1.2 | confirm | 61 / 59 | 14 / 13 | 47 |
| 0.03 / 0.1 / 1.2 | onset | 59 / 56 | 24 / 23 | 91 |
| 0.03 / 0.1 / 1.2 | proven | 63 / 59 | 14 / 13 | 70 |
| 0.03 / 0.08 / 1.0 | confirm | 61 / 59 | 14 / 13 | 47 |
| 0.03 / 0.08 / 1.0 | onset | 59 / 56 | 24 / 23 | 83 |
| 0.03 / 0.08 / 1.0 | proven | 63 / 59 | 14 / 13 | 65 |
| 0.02 / 0.06 / 1.0 | confirm | 61 / 59 | 15 / 16 | 42 |
| 0.02 / 0.06 / 1.0 | onset | 56 / 53 | 28 / 29 | 74 |
| 0.02 / 0.06 / 1.0 | proven | 64 / 60 | 15 / 17 | 55 |

(138 swings per cell: swing time stepped by 20 ms over three ball sides. "Unheld" = swings not held by `EarlySwingHold`.)

The lead is mostly the racket's own travel to the ball, not added delay. For an on-time swing the planned meeting point *is*
when the racket arrives, so a shorter cap only hurries the swing. Every shorter cap raised honest-contact misses, worst where
a hit waits for confirmation (prediction off: 15 → 20–28 misses). A first try also lost the earliest held swings
(`EarlySwingHold`). The gain on unheld swings is ~5 ms, and 0 ms on on-time ones until the caps get so short that misses climb.
That fails the brief's "HonestMisses must not rise", so the lead stays 0.05/0.2/1.6. This sweep still had the lag-learner
drift noted under B2, which moves a trial or two at the edges. The steady climb in misses on the waiting path, as the cap
shrinks, is not that noise. B2 gives the gain this item was after: the
honest misses it removes are exactly the ones a waiting hit caused.

### 3. B4: polling samples as they arrive (not done: no cheap gain)

- **Swing timing is already independent of when Unity polls.** Every onset, confirmation and abort carries its sensor timestamp.
  `NativeSportsSession` passes its age (`EventAge`) into `BeginSwing` / `RequestSwing`, and the swing is put ahead by it
  (`CompensateDisplayDelay`). Polling sooner would not change a single grade.
- **The strike in the hand doesn't wait for Unity either.** It fires from the phone's own motion queue (`RacketFeel.swingReachedBall`).
- **What's left is when the character starts moving: up to one loop.** Unity's player loop gives no hook that runs while the
  main thread waits for the next display-link tick. Extra polls inside the same frame (EarlyUpdate, PreLateUpdate) land within
  ~1 ms of the existing one, which already runs first in `Update` (`DefaultExecutionOrder(-1000)`) right before the 120 Hz steps.
- **Running the game from the sensor callback is not possible.** `TennisGame` moves transforms and animators, which must stay on
  the main thread.
- **The cheap version is already in.** `InputRate`'s 120 Hz loop halves the wait (mean ~4 ms, at most 8.3 ms).
- **The one thing that needed every sample now reads every sample.** The proven check above walks each polled sample, not
  just the newest.

### 4. Tests

Unity 6000.3.24f1 through `heavy.sh` with GOLF_MUTE=1, in two APFS clones: `~/p1b-latency-UnityClone/base` (the tree before P1b)
and `.../U` (with P1b). Runs are in `work/tennis-latency-p1b/runs/`. The Mac was short of memory all day, so heavy.sh's brake kept
stopping big runs. The PlayMode tests therefore ran one class (or a light subset) per launch (`queue7.sh`; `run2.sh` waits for
free memory and retries).

| Run | Base | With P1b | Fails only with P1b |
|---|---|---|---|
| **EditMode**, full suite | – | **700 / 700** | – (includes 4 new `TennisLatencyTests`: device swing proven before its confirmation, steps/flinches/the device write-off never proven, per-stroke reset, thresholds match `SteeringFilter.swift`) |
| **XCTest** `SportsDelayProbeTests` + `SportsIntegrationTests` (iPhone 17 simulator; builds the app with the new sample flag) | – | **47 / 47**, incl. `testScreenLinkAndAdvice` | – |
| PlayMode `ControllerTimingRegressionTests` + `TennisTimingBalancePlayTests` + `TennisSpatialContactPlayTests` | 4 / 7 | 5 / 8 | none. New `ProvenOnsetStrikesWithoutConfirmationAndAWriteOffCancelsIt` passes |
| PlayMode `ControllerTimingRegressionTests` after re-baselining one test (below) | – | 3 / 5 | none: the 2 left fail on base too |
| PlayMode `TennisGameplayTests` | 3 / 6 | 3 / 6 | none |
| PlayMode `TennisGameplayImprovementPlayTests` | 4 / 6 | 4 / 6 | none |
| PlayMode `NativeTennisSetupTests` | 4 / 6 | 4 / 6 | none |
| PlayMode `TennisAbilitiesPlayTests` (behind a test that takes the scene's error log) | 1 / 2 | 1 / 2 | none: `SelectionDiveAndConfirmedContactRules` passes on both |
| PlayMode `TennisPolishPlayTests`: onset/confirmation and timing-check tests | 1 / 3 | 1 / 3 | none: `OnsetStartsTheSwingConfirmationEnablesContact` passes on both |
| PlayMode sweeps `ZTimingPowerSweep` (10-24), `ZLatencySweep` (this work) | pass | pass | results in 1–2 and below |

- **The failures are the same on both clones and predate P1b.** All but one are among the ones the brief listed: the
  `HeroFaceReferenceFit` error log that fails whichever test loads the scene first, `OnTimePhoneServeMakesRealContact…` (failing
  since 10-18), and the native/gameplay setup tests. The other, `LateConfirmationStillHits`, fails because its ball is now
  played as an overhead smash, which the test predates. It has also failed since 10-18.
- **Re-baselined, not reverted:** `LatestPacketRetainsStrokeAgeAndIgnoresAnOlderAbort` passed on 10-18 and failed on base. P1's
  paced catch-up (B5) jumps at most 50 ms, so `SwingAge > 0.1` no longer measures compensation. The test now checks the advance
  the swing is graded with (`swingAdvance > 0.1`). It passes.
- **Not run.** The capture/film classes (cameras, venues, stances, reference captures), match stats, lob cinematic and
  `TennisOverheadProbeTests` (a 30-minute explicit probe) were left out: none touches swing or contact timing, and they are the
  heaviest. `TennisTutorialPlayTests` was left out too; another session is rewriting the tutorial now. Of
  `TennisPolishPlayTests` only the three onset/confirmation/timing tests ran: the full class tripped the brake on every attempt.
- **`ZTimingPowerSweep` (10-24 harness) re-baselined for P1.** Against the 10-24 run (before P1), the late edge of the
  connect window moved from +0.18 s to +0.10 s on the confirmed path and +0.13 s on the onset path. The early edge is still about
  −0.31 s, held by `EarlySwingHold`. That is P1's detection compensation counting the detector's 100 ms / 40 ms, as intended,
  so it stays. P1b changes nothing there. On the confirmed path, which P1b's code does not touch, base and P1b give
  188 / 185 returns and 28 / 37 honest misses of 414: the edge trials flip both ways, as they do between two runs of identical
  code (next point).
- **`TennisTimingBalancePlayTests` needed no re-baselining.** Its sweep and capture both pass on base and with P1b, P1's 40 ms
  onset compensation included.
- **Run-to-run noise in the sweeps.** The same code and harness, run twice, gives a different result in 134 of 276 trials, mostly
  a one-frame shift in lateness. Totals vary by ±1–2 returns and ±3 honest misses per 138 swings. The sweeps also let the lag
  learner drift unless it is reset per trial (`ZLatencySweep` now resets it). So only effects that hold across runs and delays,
  like B2's, are reported as real.

### 5. For the device test (Adnan), in addition to section 5.4

1. **Proven strikes.** Swing prediction on (default). In `swingtrace` lines, compare onset → `confirmed … at=peak`. In play,
   confirm `[TennisLatency] proven stroke written off` never appears. A step, a shuffle or a flinch must never return a ball:
   stand still during an incoming rally ball and take a quick side-step without swinging.
2. **Honest misses.** Count `honestMisses` in the `[TennisBalance]` lines with prediction on vs off over a few games. On should be
   lower or equal.
3. **Feel.** A late-ish swing that used to whiff ("NO CONTACT" after a visible swing) should now connect.
4. **Versus (two phones).** A proven hit is sent before the phone's confirmation, so the other phone may mirror the swing as still
   provisional for a frame or two when the hit lands. Its hold-for-rival path covers that (`atLine`). Watch for a rival racket
   that visibly misses a ball that still comes back.
5. **Sweep timing.** These sweeps time strokes from 45 device swings recorded in early October. Re-run
   `replay_swingtrace.py` on a fresh `SportsDiagnostics.log` from the device test to confirm the 60 ms / 20 ms figures.

## 9. Serve on slow TVs (2026-10-25): built and tested off-device

Not committed. Since 10-10 (`ServePace` .75 → .9), an on-time phone serve failed on a slow TV. The player swings at the top of
the toss they see, and that swing reaches the game a TV delay late. At 0.6–0.68 s of delay the ball had already fallen past the
strike point (racket gap 0.51–0.57 m). At 0.7 s the toss was caught (`ServeCatch`, 1.3 s) before the swing arrived. Found by the
test-repair session (`ControllerTimingRegressionTests.OnTimePhoneServeMakesRealContact…`).

**Fix: a slow TV gets a slower fall after the top of the toss.**
- **Rule** (`TennisRules.ServeFallGravity`, used by `TennisGame` at each toss): the fall from the top of the toss to the strike
  point lasts at least the TV delay (`Lag`), the swing's report (`ServeSwingReport`, 70 ms) and `ServeLateReach` (0.15 game s of
  lateness the strike still reaches).
- **What it changes:** gravity after the top of the toss, with the catch moved out by as much as the slower fall takes. The ball's
  sideways drift is planned on the same flight.
- **Unchanged:** the rise, the top, the power bar, the perfect windows, the grading (still judged on when the player swung,
  `serveOnsetAt`), and the serve for everyone else.
- **Normal delays keep the toss exactly as it was** (full gravity up to ~0.27 s at `ServePace`). With the real heroes:

| TV delay | 0–0.25 s | 0.4 s | 0.6 s | 0.7 s | 0.85 s | 1 s (`TennisLagLearner.Max`) |
|---|---|---|---|---|---|---|
| Gravity after the top (m/s²) | 9.81 | 8.8–9.2 | 5.1–5.3 | 4.1–4.2 | 3.0–3.1 | 2.3–2.4 |
| On-time serve | connects (gap 0.045 m) | connects | connects | connects (was: caught) | connects | connects (gap 0.02 m) |

**Tests** (Unity 6000.3.24f1 via heavy.sh, GOLF_MUTE=1, APFS clones `~/serve-lag-UnityClone/{base,U}`; runs in `work/tennis-serve-lag/runs`):
- **`OnTimePhoneServeMakesRealContact…`** now covers 0, 0.18, 0.25, 0.4, 0.6, 0.7, 0.85 and 1 s (both heroes, both hands, two toss
  accuracies; 64 serves). All 64 connect with no honest miss. It also asserts full gravity at ≤ 0.25 s. It fails on base, as before.
- **EditMode 702 / 702.** New `SlowTvTossFallsSlowlyEnoughForTheOnTimeSwing`: full gravity at 0 and 0.25 s, slower only as the
  delay grows, always long enough for the swing, capped at 1 s.
- **PlayMode, base vs fix:**
  - `ControllerTimingRegressionTests`: 4/5 → 5/5.
  - The same results with and without the fix: `NativeTennisSetupTests` 5/6, `TennisPolishPlayTests` 18/22 (capture tests in batch
    mode), `TennisTimingBalancePlayTests` + `TennisSpatialContactPlayTests` 3/3, `TennisGameplayTests` 3/6. Same failures; nothing
    that passed before fails.

**For the device test and later:**
- On a slow TV (≥ 0.4 s, e.g. a TV without Game Mode), the toss now visibly floats down after its top. Does that read as fine, or
  should a slow TV get a "use Game Mode or a cable" nudge as well?
- **Versus:** done, see below.

**Versus: the other phone draws a slow-TV server's toss (2026-10-25, built and tested off-device, not committed).**
- **Change:** the "toss" message carries the fall (`VersusMessage.fall` = the server's `tossFall`). The other phone draws the
  fall from the top at that gravity (`RemoteToss`, the same rule as `PlayerToss`). Its fallback catch, used if "catch" is lost,
  waits as long as the slower fall takes (`RemoteCatchAt` + 1 s).
- **Older phones:** an older phone sends no fall, read as 0, and `VersusWire.TossFall` turns that into 9.81. A broken value is
  also 9.81. An older phone ignores the new field and draws full gravity, as it did before. The pose format and the ready/score
  checksum are unchanged. The server's own toss is unchanged.
- **Tests** (heavy.sh, GOLF_MUTE=1, APFS clones `~/toss-fall-UnityClone/{U,U2}`; tools in `work/tennis-serve-lag/versus`; runs in
  `work/tennis-online-resilience/runs/tossfall-*`):
  - **EditMode 709 / 709.** Two new `VersusWireTests`: a missing or broken fall reads as full gravity, and every fall
    `ServeFallGravity` can give comes through unchanged.
  - **Versus harness, seat 1's TV 0.7 s behind** (`MP_LAG_SEAT=1 MP_LAG=0.7`, 3 games). The harness gets a toss track on both
    phones, and `vtoss.py` compares the other phone's toss with the server's on the shared clock.
    - **Before** (receiver ignores the fall): 17 of seat 1's tosses are 1.3–2.5 m off on the other phone by the time the hit
      arrives. FAIL.
    - **After:** 8 tosses at fall 4.23 m/s², worst gap 0.048 m. PASS. vcheck PASS, same score.
  - **Plain baseline harness:** PASS, 12 tosses within 0.11 m.
  - Even at full gravity, the other phone draws the toss about one frame (15–20 ms) behind, which is up to ~0.11 m near the hand.
    This was already the case.
  - The slow server's racket-to-ball distance when the hit arrives is now in line with normal serves (1.1–1.3 m vs 1.2–1.5 m).
    Before the fix it reached 1.8 m. Every serve has this distance: it is the racket's follow-through during the ~80 ms delivery.
- **Device check:** two phones, one TV without Game Mode. The rival's toss should float down the same way on both TVs.
