# Delegation plan — Adnan's notes of 2026-10-19

21 notes → **9 worker chats + this chat as coordinator/integrator**, run in two waves.
Grouping rule: one chat per set of files, so no two chats edit the same code. Work that touches
someone else's files goes through that chat or through the integration 3-way merge.

## Ground rules for every chat (paste into each brief)

0. **Budget: ONE good pass, then stop for Adnan's review.** Adnan has ~82 % of the weekly usage left for all 9 chats.
   The 10-17/18 runs were far too extensive. No sub-agent fan-out, no repeated re-render loops, no 40-gate suites.
   Aim for the simplest change that clearly fixes each note. If something turns out big, do the core and write it
   down as a follow-up instead of chasing it.
1. Read `AGENTS.md` and this file (skip the old HANDOFF/CHANGES history unless you need it). Commit to your OWN branch only;
   never push, never merge into `10/19`. Adnan combines the branches later.
2. **Base:** branch `10/19` (commit `3e5086a68a`+) has all work through 10-19. Each chat runs in its own git worktree cut from it.
   Unity: the worktree has no `Unity/Library`. Seed it with an APFS clone instead of a full import:
   `cp -cR <main checkout>/Unity/Library <worktree>/Unity/Library` (main checkout =
   `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`).
3. **Machine:** 16 GB Mac. Every Unity/Blender launch goes through
   `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/delegation-2026-10-17/heavy.sh unity|blender <cmd>`
   (shared slots in `~/.heavy-slots`). One heavy job per chat at a time. Quit your Editor when idle. Windowed Unity runs use `GOLF_MUTE=1`.
4. **References (video), kept light:** write `work/<job>/REFERENCES.md` with 3–4 clips (YouTube id + start–end seconds +
   the one thing to copy). Watch only those clips in the Browser pane and save ONE contact sheet per clip to `work/<job>/refs/`
   (seek+pause+canvas method, see memory "YouTube frame-stepping"). Don't wait for approval of the list. Cite clips by id.
   Never rip audio or copy copyrighted text. Emotes: no Fortnite dances.
5. **Proof, kept light:** a few actual game captures, before/after next to the reference sheet, and a short `GATE_RESULTS.md`
   (≤8 binary lines). Finish with a 5-line report: what changed, the branch name, what is NOT done.
6. Use the installed skills where they fit: `camera-systems`, `game-feel`, `audio-design`, `game-ui-ux`,
   `input-systems`, `level-design`, `unity-animation`, `unity-physics`.

## The 9 chats

| # | Chat | Adnan's notes covered | Owns (files) | Wave |
|---|------|------|------|------|
| A | **Golf shot flow + broadcast camera** | first-drive facing bug; post-swing cam; ball follow; post-putt cam; hole-out cam keeps behind-the-golfer angle; golfer hidden on putts; broadcast-style cuts; remove character intros after flyover; remove obstacle tags from course intro; no emotes after a hit | `Game/GolfGame*.cs` (flow), `Game/CameraRig.cs`, `Game/PresentationDirector.cs`, `Game/HoleIntro.cs`, `UI/IntroGraphics.cs`, `Game/IntroLens.cs` | 1 |
| B | **Golf mannerisms + hole emotes** | post-shot walk/stare at the ball, grip shuffle/waggle; fix celebration + anger emotes after a hole (broken hands/arms, arms through clothes) | golf clips + `Game/GolferView.cs` move hooks, `Game/GolferFootwork.cs`, `GolfGame.HoleOut.cs HoleOutReaction` clip choice, HeroClearance tracks | 2 |
| C | **Hold-to-swing + putting distance meter** | change golf to hold button and swing; on-map putt power meter (power ↔ distance) | `GolfArcade/Unity/GolfController.swift`, `SportsSession.swift` (golf swing), `SportsMotion.swift`, `GolfGame.Native.cs`, `Swing/MotionSwingDetector.cs`, `Shot/GolfClub.cs` putt curve, `UI/Hud.cs` meter | 2 |
| D | **Audio: crowd, announcer, contact, soundtrack** | crowd sounds, standard announcer, more contact sounds, a standard soundtrack (golf + tennis + menus) | `Game/GolfSounds.cs`, `Game/EventSounds.cs`, `Game/PresentationStinger.cs`, tennis hit sounds, new music/announcer director + mixer | 1 |
| E | **Course content + impact FX** | remove floating rocks; quirky obstacles (timed launchpad, moving target, more random stuff); better swing impact effects; more visible flag | `Course/*` (Obstacles, CourseMovers, CourseShot, PlayRules, HoleView flag), `Course/GolfResortDress.cs`, `Majestic/MajesticScatter.cs`, `Environment/DreamWorldArt.cs`, `Game/ShotEffects.cs`, `Game/MoverView.cs` | 2 |
| F | **Male clothes + face repair** | male clothes and face broken; smooth clothes, shaders, quality | male garment builders (`work/clothing-v2`, garment pipeline), male face (`MaleFaceFinish`), `TennisCloth`/`HeroFaceSkin` male branches | 1 |
| G | **Menu hero: parity, idle arm, zoom, racket on back** | menu character ≠ game character; right arm sticks out at idle; zoom in more; racket on the back + switch racket/club | `CharacterModelPreview.swift`, `MatchHeroMotion.swift`, `MatchHeroSurfaces.swift`, `LockerStudio.swift` racket/club slot, `Hub/HubHeroAnimator.cs`, `Tennis/HeroAccessories.cs` (new racket BackCarry), `work/hero-sync` | 2 (final sync after F) |
| H | **Custom UI kit** | create a set of custom UI | phase 1: HTML mock-ups only (`ArtDir/ui/…`); phase 2: SwiftUI component kit + Unity `UI/UiKit.cs` | 1 (mocks) → 2 (build) |
| I | **Online made simple** | lobby: everyone enters a room together; one-click invites that work; in-game notifications; in-game text chat without leaving | `GolfArcade/Social/*`, `GolfArcade/Multiplayer/*`, `GolfArcade/Party/PartyChat*`, `Hub/HubWorld.cs` doors/`GatherParty`, `Hub/HubRemotes.cs`, `club-hub/` server | 1 |

Coordinator (this chat): briefs, answers blocked chats, starts wave 2. Adnan reviews each branch, then the branches are combined
later (merge, hero sync, phone build, two-phone test).

### Waves
- **Wave 1 (now):** A, D, F, H-mocks, I. Heavy load: A = Unity, F = Blender, I = Xcode + some Unity, D and H are light.
- **Wave 2 (as slots free up):** B, C, E, G, then H-build.
  B goes after A, because A decides when the post-shot and hole-out moments happen and B fills them with clips.
  C goes after A, because both touch the shot flow. G's last step is a fresh hero sync after F installs.
- **End:** Adnan reviews; combining the branches is a later step.

## What each chat needs to know (findings from the code map)

**A — flow/camera.** State machine `GolfGame.cs` `State {Menu, Golfer, Intro, Aim, Flight, Result, HoleDone, …}`.
- *Facing bug suspect:* `MeetThePlayer` (GolfGame.cs:~1346) calls `golfer.Perform("Idle")`. That sets the yaw to `baseRot * ClipYaw`
  (+90° for Idle/Wave/Intro_/Emote_), and only `SetClub`/`Settle` reset it. The first drive comes straight after the intro.
  Also check `TeeAim()` against `AimDirection()`, and the golfBeat==2 branch in `GolfGame.Presentation.cs:90`.
- *Cameras:* `CameraRig.FollowShot` is the only flight camera. `HoleCam`, `Drone`, `BallPov` and `HoldOn` exist but are never called,
  so they are building blocks for broadcast cuts. Result framing is `GolfGame.Results.cs FrameResult()`.
- *Intro:* obstacle tags come from `FrameFlyover` → `introGraphics.ShowTag/Pin`. The character intro is `MeetThePlayer` (1.2 s over the shoulder + 3 s `IntroWindow`).
- *Emote after a hit:* `PlayResultEmote(selection)` in Results.cs.
- *References:* PGA Tour / Masters broadcast tee shot (cut from behind the golfer → tracer → landing), a broadcast putt hole-out
  seen from behind, EA PGA Tour / PGA 2K camera, Mario Golf: Super Rush, Wii Sports Resort golf.

**B — mannerisms/emotes.** There are no post-shot mannerisms today. The golfer holds the finish, then plays `Perform("Idle")`. Walk/Run clips
are loaded in GolferView (line ~365) but unused in golf. Hole-out reaction = `HoleOutReaction()` (Victory/JumpJoy/FistPump/Slump/Stomp).
Reuse the hand-clearance solver + `CLIPPING_AUDIT.md` (309 problems). Earlier decision: fit the emotes to the clothes.
*References:* pre-shot waggle/regrip routines, a pro holding the finish and watching the flight, walking off the tee, a fist-pump celebration, club-slam frustration.

**C — input/putt.** Today: tap `startSwingButton` (GolfController.swift:374) → "HOLD STILL" → "SWING NOW". The command is `golfStartSwing`, and Unity runs
`NativeStartSwing` → `NativeSwingTracking`. The new flow: press-and-hold arms the swing, the swing happens while the button is held, and letting go resets the swing (Wii Sports Resort style). That needs
a new release command. Putt distance follows meter² (`GolfClub.MeterExponent`), and the HUD shows only "N ft".
*Map meter:* draw distance rings/ticks on the green along the aim line, so the power–distance link is visible.
*References:* Wii Sports Resort golf (hold B), Mario Golf: Super Rush motion controls, Golf Clash and PGA 2K putt-distance previews.

**D — audio.** All sound is synthesised today. There are no audio files, no announcer and no music system. Choose a source: synth, CC0 libraries
or generated audio (ask Adnan before anything paid). Never ripped audio. Build a mixer with buses and ducking.
*References:* broadcast crowd roars and groans, Wii Sports / Switch Sports announcer and menu music feel, Mario Tennis Aces announcer.

**E — course/FX.** There is no general ground snap. `GolfResortDress.DressShore` places boulders at `max(-.2, center.y - r*.5)`, which can float.
`DreamWorldArt.Golf()` samples the ground at one point. Most rocks are baked in the Blender course models (`blender/scripts/phase7_rocks.py`).
New obstacles extend `CourseMovers` (`MoverKind` already has `RockGate` and `WindLift`) + `CourseShot` physics + `ObstacleTests`.
Impact = `ShotEffects.Strike()` (putts get only a small ring). Flag = `HoleView.BuildPin/DressFlag`.
*References:* Golf With Your Friends launch pads and moving parts, What the Golf?, Mario Golf: Super Rush courses and impact effects, broadcast flag readability.

**F — male.** Start from `work/male-audit-1018/AUDIT.md` (fix order), the male ref pack, and the memories male-garments-refpack and male-face-pass-1018.
Show Adnan the before images first, then fix.

**G — menu hero.** The phone menu is SwiftUI + SceneKit copies (not Unity). The TV plaza is Unity.
- *Arm:* the phone always loops `<Sex>_ReadyIdle` (the tennis ready stance holding a racket) and hides the racket, so the arm stays out.
  The plaza blends toward a hand-built relaxed pose ("arms hang… a little out").
- *Zoom:* `cameraDistance` is set per screen (MotionClubMenus 3.25/3.4, LockerStudio 2.7, IslandScreens 3.4).
- *Racket on back:* the only BackCarry item is `golf_bag`, so add a `racket_back` item and a locker toggle.
- *Parity:* drift comes from the hand-ported `MatchHeroSurfaces.swift`. Freshness test `testNativeHeroesMatchTheCurrentUnityHeroLook`.
*References:* Switch Sports / Fall Guys customise screens (idle pose, framing).

**H — UI kit.** Phone = SwiftUI; TV = uGUI built in code (`UI/UiKit.cs`). Process rule: study real game screens, mock up in HTML
(not Unity), and use the Wii Sports / Mario Kart structure without copying their look. Then pick with Adnan and build the kit.
Apply it screen by screen only after G and I land.
*References:* Switch Sports, Mario Golf: Super Rush, Fall Guys UI (Game UI Database).

**I — online (Game Center only).** Drop the club-hub relay path (`ClubHubServerURL` stays empty and must not be needed). Game Center invites
(`GameCenterTransport.invite`, `MultiplayerService.inviteGameCenterFriend`) have never been tested on two phones. Make the party, presence,
room switching and chat run over the Game Center match. `HubRoomTransport.swift` currently rides the relay, so move it onto Game Center or replace it.
- *Rooms:* `HubWorld.WalkThrough` teleports only the local player. Add party-follows-leader on doors: the leader walks through, everyone switches.
- *Notifications:* the in-game `InviteBanner` already exists.
- *Chat:* the chat is a sheet, so make it inline.
*References:* Brawl Stars / Fall Guys party invite → banner → join, party-follows-leader, quick in-game chat.

## Adnan's decisions (2026-10-19)
1. **Putt camera: confirmed.** On a putt the camera stays behind the golfer and the golfer fades out while the ball rolls.
   On a hole-out there is no cut: the golfer reappears in the same view and reacts, seen from behind.
2. **Hold-to-swing: confirmed.** Hold the button to arm and swing while holding. **Letting go resets the swing.**
3. **Online = Game Center only.** No club-hub relay or server. Invites, presence, room switching and chat all run over Game Center
   (GKMatch / invites), with our own in-game banner on top of the Game Center notification.
4. **Base:** the 10-14…10-19 work is committed as branch `10/19`. Chats branch from it, and Adnan combines the results later.
5. **One good pass per chat**, then Adnan reviews everything.
