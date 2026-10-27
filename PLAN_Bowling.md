# PLAN — Bowling, the third sport (2026-10-24)

Status: **plan, decisions answered 10-24** (see §13). Nothing is built yet.

Ask (Adnan, 10-24): bowling is the third and final sport. Gameplay is simple:
1. Move your character left/right with the controller.
2. Press **Ready** on the bowling ball. The character starts the approach.
3. **Hold on** to the ball, and time it with the character on screen to (a) **release** the ball and (b) **swing** it to make power. A badly timed release makes the ball harder to control.
4. **Flick the wrist** a real-life way to add spin.

Plan it from how Wii Sports did it and from real bowling rules. Cover the ball, how characters hold it, animations, the alley and everything else.

---

## 1. What already exists (code + assets read 10-24)

| Thing | Where | State |
|---|---|---|
| `Sport.bowling` | `GolfArcade/Unity/SportProgress.swift` | Case exists ("Neon lanes, perfect strikes", `figure.bowling`, violet). `playable` is false, so menus show "coming soon". |
| Club art | `ClubDesign.swift`, `MenuArt/club-bowling.png` | Bowling uses the shared "pavilion" scene. |
| Alley | `SportsLibrary/Arenas/Bowling/coastal-bowling-resort-v1.blend/.fbx` | 9 regulation lanes (18.288 m foul line → head pin, 1.067 m bed), 90 separate pins, gutters, dots, arrows, pinsetter facades, palms. No colliders, physics or LODs. The wood shader is Blender-procedural, so it must be baked. |
| Ball + pin | `SportsLibrary/Equipment/Bowling_Ball.fbx`, `Bowling_Pin.fbx` | Blockout only. Both are easy to make new (the pin is a lathed profile, the ball a sphere with drilled holes), so **we build new ones** (§5.1, §7). The old files are fallback only. |
| Animations | `SportsLibrary/Animations/V4/Bowling/` | 44 actions on the **old standard characters, not the MatchHero rig**. **Not used** (Adnan 10-24: only the alley, ball and pin may come from SportsLibrary). New clips are keyed from real-life bowling footage and bowling-game gameplay (§5.3). |
| Crowd | `SportsLibrary/Crowds/bowling-familiar-crowd.blend` | **Not used**, same rule. The room is livened with the game's own plaza NPC/ambient systems or left out. |
| Rules from earlier | `SportsLibrary/CHARACTER-STANDARD.md` | The ball must detach **at the gameplay release event**, not when a preview trajectory starts. RH/LH is a player setting. |
| Tests | `Tests/EditMode/StandardArmSportTests.cs` | Already has a `("male","bowling")` case. |

How a sport is wired today (reuse, do not re-invent):
- **Runtime-built scenes.** `Golf.unity` and `Tennis.unity` each hold one component that builds everything. Bowling gets `Scenes/Bowling.unity` with one `BowlingGame`.
- **Phone → Unity.** `SportsMotion.swift` reads CoreMotion at 100 Hz into the 120-byte `SportsSample` ring buffer (`SportsBridge.mm`). Unity reads it in `NativeSportsSession.Update()`. Commands go through `SportsSession.command` → `NativeSportsSession.Receive`. Events come back via `SportsEmit`/`pollEvent`.
- **Swing model to copy:** golf `MotionSwingDetector` (load, then downswing) plus `GolferView.PaceDownswing`, which keeps the on-screen club moving with the phone.
- **TV-delay model to copy:** tennis `DisplayLatency` (flash probe) plus `TennisLagLearner`.
- **Turns:** golf `Course/Match.cs` (`Players`, `TurnIndex`), `GameSetup` (Solo / LocalVersus / Tournament / Online), `SharedPhoneTransport` pass-and-play, and `NetworkGolfRound` host authority.
- **Characters:** Generic-rig FBX clips from `work/match-anim-set`, played with Playables (no Animator state machines). Hand sockets hang on `RightHand` (`Hand_Racket`), and `HeroAccessories` handles items. **Finger bones exist** (`HeroAuthoredHandPose`, `HeroGripPolish`: Thumb/Index/Middle/Ring proximal → distal), so a real three-hole grip is possible.
- **Physics:** there are **no Rigidbodies anywhere** in the game. Golf and tennis use custom integrators (`BallFlight` at 1/240 s, `TennisBall` at 1/120 s). Pin collisions would be the project's first real physics (§6).

---

## 2. How Nintendo did it (what we take, what we change)

**Wii Sports (2006):**
- **Setup:** D-pad moves the Mii left/right. Holding A plus the D-pad **rotates the throw angle**.
- **Throw:** hold **B**, swing the arm back, swing it forward, and **let go of B** to release.
- **Release timing sets spin and loft.** An early release (arm low, near the floor) gives more spin. A late release (arm already rising) gives a straighter ball with little spin.
- **Wrist twist at release sets spin direction**, and the swing direction steers the ball. Speed comes from swing speed.
- **Known gags:** letting go on the backswing throws the ball **behind you** and scares the crowd. A late, high "pop" release sends a fast, nearly straight ball.
- **Training:** Power Throws (pins grow each stage to 91, with a secret rail button), Spin Control (walls you must curve around), Picking Up Spares (20 set-ups).
- **Multiplayer:** pass the remote, one lane, turns.

**Wii Sports Resort / Club:** same controls with MotionPlus precision. Adds 100-pin bowling and Spin Control as a mode.

**Switch Sports (2022):**
- Hold **ZR** to hold the ball. Move with the stick and aim with a red dotted throw line.
- **Twist your wrist just before the top of the forward swing.** How far you twist sets how much it hooks.
- **Online, everyone bowls at the same time on their own lane** (no waiting). Survival Bowling: 16 players, the bottom half is cut after frame 3, and so on.
- Special lanes have moving barriers, ramps and gaps.

**What we take:**
- Hold-button-to-hold-ball. A real arm swing. Thumb-lift release. Wrist twist for hook.
- The comedic drop-behind.
- The three training games, which double as the tutorial.
- Simultaneous lanes online (later; online is one at a time for now).
- 100-pin and special lanes later.

**What we change (Adnan's design):** in Wii Sports the Mii's walk simply follows your arm. **Here the character walks a fixed 4-step approach on its own,** and the skill is matching it:
- **Your swing makes power.**
- **Your release timing, against the character's slide step, makes control.**

This gives bowling a rhythm skill that tennis (reaction) and golf (static swing) do not have. Each sport plays differently.

---

## 3. Real bowling — rules and numbers we implement

### 3.1 Scoring (USBC tenpin)
- **10 frames,** up to two balls per frame. Pins count one point each.
- **Strike (X):** all 10 on the first ball. Scores 10 plus the next **two** balls.
- **Spare (/):** all 10 with two balls. Scores 10 plus the next **one** ball.
- **Open frame:** the pin count only. A miss is written **–**.
- **10th frame:** a strike earns two bonus balls, and a spare earns one. A full reset happens after each strike in the 10th, and after a spare. Maximum 3 balls in the 10th.
- **Perfect game 300** = 12 strikes in a row.
- **Gutter ball:** the ball enters the channel and is out of play. Pins it knocks later (for example in the pit) **do not count**.
- **Foul:** any body part touches or crosses the foul line on delivery. The ball counts, the **pinfall counts 0**, and pins are reset (first ball) or stay as they were (second ball).
- **Legal pinfall:**
  - Pins knocked by the ball, by other pins, by pins bouncing off the side partitions (kickbacks) or off the rear cushion **count**.
  - A pin that wobbles but stays standing does **not** count. A pin that moves off its spot but stays standing is left standing.
  - Pins knocked by the pinsetter sweep or by a ball bouncing back from the rear cushion **do not count**.
- **Dead ball:** for example, a pin was missing from the set. Re-roll it (this matters only for bugs and network desyncs).
- **Split:** the head pin is down and two or more pins are left with a gap. Either a pin between them is down (7-10, 4-6), or the pin in front of and between them is down (baby splits 2-7, 3-10). The scoreboard circles splits.
  - Named leaves feed the announcer: 7-10 "bedposts", 4-6-7-10 "big four", 4-6-7-9-10 "Greek church", 2-4-5-8 "bucket" (not a split), 1-2-10 / 1-2-4-10 "washout" (not a split).
- **Streak names** for the announcer: 2 = double, 3 = **turkey**, 4 = hambone/four-bagger, 6 = six-pack, 9 = golden turkey, 12 = perfect game.

All of this is a pure C# `BowlingScore` with EditMode tests (§10, gate S1).

### 3.2 Dimensions (metres in Unity; values from USBC specs, re-check against the official spec PDF in phase 0)

| Item | Value |
|---|---|
| Foul line → centre of head pin | 18.288 m (60 ft) |
| Lane (bed) width | 1.054–1.067 m (41–42 in), **39 boards** of ~2.7 cm, board 20 = centre |
| Gutters | about 0.235 m each (9¼ in), concave. Lane + gutters = 1.524 m (60 in) |
| Approach | at least 4.57 m (15 ft) behind the foul line. Approach dots at 2 m and 3.66–4.57 m |
| Lane markings | dots at 2.13 m (7 ft); **7 target arrows at 3.66–4.88 m (12–16 ft)** on boards 5-10-15-20-25-30-35; range finders around 10.4–12.2 m (34–40 ft) |
| Pin deck → pit | lane end ~0.86 m past the head pin; kickback side plates; rear cushion; pit |
| Pin | 0.381 m tall (15 in), max diameter 0.121 m, **1.47–1.64 kg**, centre of mass ~0.145 m above the base. Two red neck stripes |
| Pin spacing | 0.3048 m (12 in) centre to centre, equilateral triangle, numbered 1 (front) to 7-8-9-10 (back row, 7 at the left) |
| Ball | diameter 0.216–0.218 m (8.5–8.6 in), max 7.26 kg (16 lb). House balls 6–16 lb. Three-hole grip: thumb plus middle and ring fingers |

### 3.3 Ball motion (the physics must produce this, not fake it)
- **Skid → hook → roll.** The ball leaves the hand sliding: forward speed is much higher than its rolling speed, and it spins on a tilted axis.
  - On the **oil** (friction μ ≈ 0.04) it skids nearly straight.
  - When it reaches **dry back end** (μ ≈ 0.2) friction turns the side spin into sideways motion, so it hooks.
  - Once the surface speed matches the travel speed it **rolls** and stops hooking.
- **Typical numbers:**
  - Release speed 7–8.5 m/s (16–19 mph). Recreational throws are 5.5–7 m/s.
  - Travel time to the pins 2.3–3.0 s.
  - Rev rate 150–250 rpm (recreational) to 300–450 rpm (strong).
  - Axis rotation 30–60°. The breakpoint is about 12 m down the lane.
- **House oil pattern:** about 12 m (40 ft), with more oil in the middle and drier boards outside. That forgiving "wall" pushes a missed ball back toward the pocket, which is why rec bowlers strike at all. We ship this as the default.
- **Strike pocket** (right-hander): between pins 1 and 3, the ball centre on board ~17.5, entering at **4–6°**. Without hook, the entry angle is ~1–2°, and carry drops sharply ("straight balls leave 10-pins and splits"). A hook really matters, and the game should reward it the way real bowling does.

---

## 4. Controls and feel (phone = controller, TV = game)

The phone is held **like the ball:** upright in the bowling hand, screen facing the player's leg, thumb on the screen. One **phone screen per phase**, and the phone never shows the game (10-10 UI rule).

### 4.1 Setup — "Find your spot"
- **Move:** drag left/right on a lane strip, or use big ◀ ▶ buttons. The character side-shuffles across the approach in **half-board steps** (1.35 cm). The TV shows the approach dots plus the board number ("Board 23").
- **Position only (decided).** There is no angle turn. The ball always launches straight down the lane from the chosen board, and the hook (§4.5) is the only thing that bends it. The TV shows a straight dotted line from the bowler's board through the arrows, plus a faint ghost of where the line hooks if you flick. An angle turn can come later.
- **Ball:** everyone uses the same club ball (decided). There is no choice here or in the Locker.

### 4.2 Ready → hold → approach
1. A **giant ball** on the phone: **press and hold** = "Ready". This also captures the **ready attitude** (the forward reference for aim, like golf's ready grip).
2. The character settles into **stance**: ball at the chest, with the off hand under it.
3. After **0.4 s held**, the approach starts. It is a **fixed-tempo 4-step approach**: pushaway (step 1) → downswing (step 2) → top of backswing (step 3) → slide + release (step 4). Total ~1.9 s; tempo is set per venue/difficulty.
4. **Haptic footsteps.** The phone ticks on each step (the 4th step gets a heavier tick), and the slide gives a "tension" buzz that peaks at the ideal release. **Haptics have no TV delay**, so they are the honest timing cue. The TV shows the same rhythm.
5. **Arm = phone.** The character's legs follow the clip, and the **bowling arm is scrubbed by the phone's swing angle** (pitch about the shoulder axis). This is the golf `PaceDownswing` trick:
   - The arm blends 70/30 toward the clip's ideal arc so it never looks broken.
   - A player who barely swings gets a short, weak swing on screen.

### 4.3 Swing → power
- **Backswing height** (phone pitch at the top) sets the **potential** (golf `Load`). Shoulder height = 100 %. Higher than that adds nothing and costs control (+scatter), which mirrors "muscling" the ball.
- **Forward-swing speed** sets the **delivered** speed. Peak gyro rate about the swing axis × ~0.65 m effective arm gives the phone hand speed. Map it into ball speed **5.0–9.5 m/s**, with a soft cap above 8.5. The HUD shows mph ("17.4 mph"), like a real alley monitor.
- **Swing direction does not steer** (position only, decided). A forward swing that wanders badly sideways (yaw drift > 15° against the ready reference) only adds to the release scatter below, so a wild flail still costs control.

### 4.4 Release → control (timing)
The **release window** is centred on the character's **slide-foot plant at the foul line**, when the ball passes the ankle at the bottom of the arc. It is judged **against what the player sees**: the window shifts by the measured `DisplayLatency` and a `BowlingLagLearner` (a copy of `TennisLagLearner`).

| Thumb lift vs ideal | Grade | Effect |
|---|---|---|
| ±45 ms | **PERFECT** | Full speed and spin transfer, no scatter, slight speed bonus. "Clean release" sparkle on the ball. |
| ±100 ms | GOOD | 95 % speed, small direction scatter (±0.4°). |
| −100 to −250 ms (early) | EARLY | The ball is "dumped" from behind the slide: 80 % speed, ±1.2° scatter, the ball **lands short and bounces** (visible thud), extra skid. |
| < −250 ms, during the backswing | **DROP** | The ball slips out behind the bowler (Wii gag). It rolls back to the approach, the crowd yelps, and it **counts as a 0-pin ball**. **Before the backswing** (steps 1–2), a lift **cancels** the approach instead: `AbortApproach`, no ball used. This keeps a slip of the thumb from being punished. |
| +100 to +250 ms (late) | LATE | **Lofted.** The ball flies about 1–2 m and lands with a boom, 90 % speed, ±1° scatter, pulled inward. It skids longer, so it hooks less. |
| > +250 ms / never | **FOUL** (fouls are on, decided) | Holding past the slide carries the character over the foul line: the slide foot crosses it, a buzzer sounds, and the red foul light flashes on the line. The ball still goes out as a big loft (auto-release at the top of the follow-through), so the pins really fall, but the **pinfall counts 0** (§3.1): on ball 1 the pins are reset and ball 2 is bowled at a full rack; on ball 2 the frame ends with ball 1's count. The TV says "FOUL" and shows the foot over the line in a 1-second replay, so the player sees why. |

The fixed approach always stops the slide just short of the line, so a foul can only come from holding too long. That makes fouls a fair, readable punishment for late timing. The window edge (+250 ms) is tuned in playtest (gate I4).

So **power and control are separate skills,** as Adnan asked: you can swing hard but release late (fast, sloppy), or swing soft with a perfect release (accurate, little carry).

### 4.5 Wrist flick → spin (hook)
The flick is read over the **last ~180 ms before the thumb lifts:** roll rotation about the phone's long axis.
- **Turning toward the "handshake" position** (RH bowler: counter-clockwise from behind, fingers coming up the side of the ball) = normal **hook**. **Rotation amount** sets the **axis rotation** (0–75°). **Roll rate** sets the **rev rate** (100–450 rpm).
- **No flick** = a straight ball (axis ~0°, low revs: forward roll only).
- **Opposite flick** = **backup ball** (reverse hook). Wii allows it, it is a real thing, and it is fun.
- **Late flick** (after the lift) is ignored. The timing ties the flick to the release, as in real life and Switch Sports ("twist just before the peak").
- The phone shows a small spin gauge after each shot ("Hook: 38° · 290 rpm"). This is how players learn the flick without a tutorial wall.

### 4.6 Second ball, between shots, and touch fallback
- **Second ball / spares:** same flow. Pins left standing are highlighted on the TV, and the phone suggests "Move: 4 boards left" for common spares (on by default, off in Pro).
- **Between shots:** emote buttons on the phone (existing emote slots) while waiting for the ball return.
- **Touch fallback (no-motion / accessibility):** a vertical flick on the screen for the swing, with the thumb lift = release. The flick's curve sets the spin. Like golf touch mode, it gets **its own** grading so it is not secretly perfect (the golf touch bug noted 10-24).

---

## 5. The ball, how characters hold it, animations

### 5.1 Ball model
- **Real size:** 0.217 m diameter. About 1.5k tris at LOD0, 300 at LOD2.
- **Three holes** in a conventional grip: thumb plus middle and ring fingers, about 11.5 cm span. The holes are modelled (bevelled, dark inside) so **the spin is readable from the TV**. The holes and a logo are the tracking marks, like a real ball on TV.
- **One club ball for everyone (decided).** No colour, finish or weight choice for now.
  - **Look:** a pearl **reactive-resin swirl** in the club colours (deep teal into cream, with a small brass club crest by the thumb hole), high clear-coat gloss and environment reflection. URP, new `BowlingBall.shader`, mobile. The swirl and holes have to read clearly against the maple lane so the spin is visible.
  - **Weight:** 14 lb (6.35 kg), the most common adult house ball. Physics mass 6.35 kg.
  - **Why one ball:** in turn-based play everyone shares one lane and one ball return, so one ball is also what real friends at an alley do. Player-coloured balls can come later as a Locker item.

### 5.2 How characters hold it (the hard visual problem)
- A new socket, **`Hand_Ball`**, under `RightHand` (`LeftHand` for LH). The ball's centre sits in the palm with the **thumb and two fingers inside the holes**. Fingers go in to the second knuckle and the thumb all the way, as in a real conventional grip.
- **Hand pose:** a `HeroAuthoredHandPose` preset, `BallGrip`. Thumb straight into the thumb hole; middle and ring curled into the finger holes; index and pinky spread flat on the ball surface. Built per sex on the real finger bones.
  - The ball's hole positions are **fitted to each hero's hand**: the ball rotates in the socket so the holes meet the fingers, which beats bending fingers into fixed holes.
  - Golf/tennis glove/grip polish (`HeroGripPolish`) must be **off** while holding the ball (lesson from 10-24 idle hands).
- **Stance:** both hands. The off hand cradles the ball from below at chest height (`Hand_Ball_Support` IK target).
- **The weight must show.** In stance the elbows are tucked. In the swing the arm hangs **straight, like a pendulum** (no bent-elbow lifting). The shoulder drops slightly on the ball side, and the torso tilts forward.
- **Release:** at the release event the ball detaches from the socket and becomes the physics ball, with the **same world position and velocity** (no pop). The thumb leaves first and the fingers lift ~30 ms later. This lift is what makes revs in real life, and we show it as the finger-snap pose.
- **Clearance:** add the ball as a `HeroClearance` proxy so it never sinks into the thigh/hip on the backswing. Expect the shorts/skirt hems to need a clearance check (garment tear history 10-18).

### 5.3 Clip list (MatchHero rig, both sexes, right-handed; left-handed later)
Built in `work/bowling-anim/` with the `match-anim-set` pipeline (Blender at 30 fps, Generic FBX, `MatchHeroImport`). Clips with ⚙ are layered with the phone-driven arm.

**References come first (decided: real-life bowling footage or bowling-game gameplay, not the old V4 actions):**
- **Real life:** slow-motion PBA four-step and five-step approaches (side and behind views), rec-league bowlers (a relaxed, less athletic swing that suits our heroes better than pros), the ball pick-up at the ball return, and real strike/split/gutter reactions.
- **Games:** Wii Sports and Switch Sports bowling gameplay (body english, reactions, the walk back, how they stage the throw for a TV camera), plus PBA Pro Bowling for a more realistic approach.
- **Method:** the YouTube frame-stepping recipe in the Browser pane, contact sheets per clip. Watch only the listed clips (a non-bowling frame is a mistake). Record clips **by id + timestamps only** in `work/bowling-anim/REFERENCES.md`, with what each clip is used for.
- **What the references must answer before keying:** foot timing of each step against the arm swing, slide length, where the ball sits at the ankle at release, the shoulder and spine tilt, how high the follow-through ends, and how the off arm balances.
- **Gate A0:** every clip below names at least one reference id, and the approach clip's step/arm timing matches the reference within 2 frames at 30 fps.

| Clip | Notes |
|---|---|
| `Bowl_Pickup` | Lift the ball from the ball return with **both hands** (real etiquette, and it reads as heavy). |
| `Bowl_Idle` | Ball held at the chest, small breathing and look-at-pins. |
| `Bowl_ShuffleL/R` | Side-step on the approach while holding the ball (setup moves). |
| `Bowl_Stance` | Ready pose. Knees soft, ball at the chest, eyes on the arrows. |
| `Bowl_Approach4` ⚙ | Legs + torso, fixed tempo. **Events:** step1..4, `slidePlant`, `releaseIdeal`. Arm channels are overridden by the swing layer. |
| `Bowl_SwingArc` ⚙ | A 1-D pose track for the arm from pushaway → top of backswing → bottom → follow-through, **scrubbed by phone pitch**. |
| `Bowl_Release_Straight` / `_Hook` / `_Backup` ⚙ | Hand/forearm finish layered at release. Hook = handshake rotation; backup = the forearm turns the other way. |
| `Bowl_Release_Early` / `_Late` / `_Drop` | Distinct body reactions: the late loft has a stiff arm, the drop is a "whoops" look back. |
| `Bowl_FollowThrough` | High finish, held balance on the slide foot with the off leg swept behind. **Hold time ends when the ball passes the arrows.** |
| `Bowl_BodyEnglish` | Additive lean L/R driven by the ball's lateral error in real time (everyone does this). |
| `Bowl_Abort` | Stop mid-approach and walk back. |
| `Bowl_Foul` | The slide foot crosses the line, the bowler stumbles one half-step and looks down at the line. |
| `Bowl_WalkBack` | Return to the ball return. |
| Reactions | Strike (fist pump + 2 variants), Turkey (bigger), Spare, Gutter (head in hands), Split (stare), 7-10 (disbelief), Converted split (big), Foul (protest). These **reuse the Emote Standard Kit** where possible, plus 4 bowling-specific clips. |

- **Timing truth:** `releaseIdeal` is the authority for the release window (§4.4). The approach clip is authored so the ball reaches the ankle exactly at `releaseIdeal`. A gate checks this on the baked clip (B3).
- **Frame rate:** bake at 60 Hz (the 10-16 frame-rate rule). Bowling is all about feel at the release.

### 5.4 Clothes
No new garments needed: the tennis/golf kits work for launch. A **bowling shirt** (camp collar, contrast panels) is a natural Locker item later. It is out of scope for this pass, by the clothes-scope rule.

---

## 6. Physics (lane, ball, pins)

### 6.1 Ball on the lane: a custom deterministic integrator (like `TennisBall`)
- **State:** position, velocity, angular velocity (3-D), radius, mass, moment of inertia (I = k·m·r², with k from the ball's RG, about 0.4). Fixed step **1/240 s**.
- **Contact:** slip velocity `u = v + ω × (−r·ŷ)`. While |u| > ε: friction force `−μ(x,z)·m·g·û` plus an equal torque. Once |u| ≤ ε: pure roll with small rolling resistance. **This one rule produces skid → hook → roll by itself.** It is the standard published model (Frohlich, Am. J. Phys. 2004), and no "hook curve" is faked.
- **Oil map:** `OilPattern` = μ(board, distance), a 39 × 60 grid.
  - House 40 ft: μ 0.04 inside, 0.06 at the edges, 0.18–0.22 dry back end.
  - Optional **lane transition:** the dry track breaks down over frames, so the line moves a little. Pro mode only; off for party.
- **Loft:** a short ballistic phase with a bounce (restitution 0.15) when the ball is released above the lane.
- **Gutters:** past the lane edge, the ball drops into a gutter channel modelled as a half-pipe constraint and rolls to the pit. **Ball state = out of play** (§3.1).
- **Determinism:** pure C# floats, no PhysX until the pin deck. That keeps replays exact and multiplayer able to re-simulate from the throw inputs.

### 6.2 Pins: PhysX, script-stepped, only during pin action
- When the ball crosses the pin-deck line (head pin − 0.5 m), the ball hands off to a PhysX **Rigidbody** with an identical state. The 10 pins become dynamic Rigidbodies.
- **Pin collider:** a compound of 3 capsules + 1 sphere matching the profile. Mass 1.53 kg, CoM 0.145 m. **CCD on** for the ball and pins.
- **Stepping:** `Physics.simulationMode = Script` and `Physics.Simulate(1/240)` for **up to 4.5 s**, or until all pins sleep. Gameplay time is decoupled from frame time, so the TV plays it back interpolated at 60 Hz.
- **Deck objects:** kickback plates, pit, rear cushion, the gutters' inner walls, and the deck plane. Their friction and bounce are tuned to measured pin-action reference (the pins must "mix" off the kickbacks).
- **Pinfall rule:** after pins sleep, a pin counts as down if its tilt > 30° **or** it left the deck. A pin that slid off its spot but is standing stays standing (§3.1). Pins knocked by the rear-cushion rebound do not count: track `ballReturnedFromCushion`.
- **Pin feel (decided): standard pins, lively and fun, but strikes are not easy.** There is one setting for everyone, with no assist dice and no "friendly pins" option.
  - **Lively:** pins fly and spin. They bounce hard off the kickback side plates back into the deck, ride the rear cushion, and knock each other ("messenger" pins crossing the deck). Pin-to-pin restitution sits at the top of the real range, the kickbacks are bouncy, and the pin's spin damping is low. Each pin crash should look a little different, which keeps watching every throw fun.
  - **Not easy:** liveliness must not turn into free strikes. Only a good pocket hit with hook should carry often. The Monte Carlo targets (gate P3) stay close to real carry:
    - Pocket at 4–6° entry: ~75–85 % strike.
    - Pocket at 1–2° (straight ball): ~40–50 %.
    - Light pocket: ~35 % (classic 10-pin left).
    - Brooklyn: ~25 %.
    - Head-on: ~10 % (many splits).
    - A gutter-side edge hit (1–2 pins): never a strike.
  - **Fun check (gate P5):** at least 30 % of non-strike pocket hits must show a "near miss" (a pin wobbling, or a messenger crossing the deck) so a miss still looks dramatic.
- **Determinism note:** PhysX is not bit-exact across devices. So **multiplayer uses host authority for pin action** (§8): the host's pinfall is the truth, and others receive the pin keyframes.

### 6.3 Pinsetter and ball return (visible machinery = charm)
- **After ball 1:** the rake/sweep bar drops, the deck lifts the standing pins, the sweep clears the fallen ones, the deck sets the standing pins back down. About 3.5 s; **skippable** by tapping on the phone (Wii is slow here).
- **After ball 2 / strike:** full reset of 10 pins.
- **Ball return:** the ball reappears in the return hood with a "thunk" and air-blower sound about 4 s after the throw. The next bowler (or you) does the `Bowl_Pickup`.
- The machinery is animated by code (transform tweens) on separate meshes from the facade. No physics.

---

## 7. The alley (venue art)

### 7.1 The one venue for now: "Club Lanes" (decided; from the existing coastal resort)
Assets: the **alley** comes from SportsLibrary. The **ball and pins are new** (easy to build: the pin is lathed from the regulation profile with the two red neck stripes, and the ball is a sphere with drilled holes). The pinsetter machinery and ball return are new too, because the SportsLibrary ones are flat facade only.
- **Start** from `SportsLibrary/Arenas/Bowling/coastal-bowling-resort-v1.blend`: regulation, 9 lanes, palms, sea. Restyle it to the **country-club look** of the plaza and tennis/golf hubs (10-12 restyle): warm maple, teal pinsetter masking, brass, cream.
- **Primary lane** = centre lane. The neighbour lanes are populated by **ambient CPU bowlers** (a background loop with simple pin-action clips, no physics) so the room feels alive, as in Switch Sports.
- **Lane surface** (the hero surface, seen for 3 s every throw):
  - Maple board texture **baked from the Blender procedural grain** (2K, tiling along the length, 39 visible boards). Pine boards in the middle section, maple at the approach/heads and pin deck (real lanes).
  - A **dark wood stripe at the arrows**. Markings: inlaid arrows, dots, foul line, approach dots.
  - **The lane must be glossy:** a mirror-like reflection of pins and the ball on the oil. On mobile, use a **planar reflection only on the primary lane** (half-res, every other frame) plus a reflection probe elsewhere. The oil area reads glossier than the dry back end, which is a subtle way to *see* the pattern.
- **Masking unit** above the pins:
  - A **large score monitor** showing the classic 10-frame sheet. The same data drives the HUD.
  - Big strike/turkey animations on the monitor (a nod to classic alleys, and it makes great TV moments).
- **Scorer area:** a horseshoe bench, ball rack with house balls, the ball return (§6.3), a scoring console and a shoe cubby. This is where waiting players stand/sit and emote.
- **Crowd:** a few of the game's own plaza-style NPCs at low LOD behind the scorer area, reacting to strikes, drops and fouls. The SportsLibrary crowd file is not used.
- **Lighting:** bright, even lane lighting with warm practicals. This is a **readability first** sport: pins must read on a phone-mirrored TV from 3 m away. Use `MajesticVenue` for grade.

### 7.2 Later venues (not in this pass; like tennis's 3 venues)
- **Cosmic / Neon** ("Neon lanes, perfect strikes" is already the tagline): blacklight, glowing pins and balls, a moving light show after strikes. Cheap to make as a lighting variant of Club Lanes.
- **Volcano or Skyscraper lanes:** reuse the tennis venue themes for brand coherence, a rooftop lane at sunset. Uses the special-lane obstacles (§9).

### 7.3 Budgets
- **Primary lane** (lane + gutters + deck + pinsetter + 10 pins + ball): ~60k tris.
- **Whole venue:** ≤ 350k tris on screen with LOD.
- **Pins:** 1.2k tris at LOD0 and 200 at LOD2, GPU-instanced.
- **Draw calls:** ≤ 150 with the hero on screen.
- **Target:** 60 fps on device during pin action (gate DV1).

---

## 8. Players, turns, modes, multiplayer

| Mode | How | Reuse |
|---|---|---|
| **Solo 10 frames** | You vs your best. Optional CPU rival on the next lane, from `TennisOpponentProfile`-style skill profiles. | `GameSetup.Solo` |
| **Pass-and-play (1–4)** | One lane, turns in frame order, as in real bowling and Wii Sports. The phone passes between people. A "Your turn: Sam" card on the TV. | `SharedPhoneTransport` + `Match.cs` turns |
| **Local multi-phone (2–4)** | Each phone is its own controller. Turns on one lane on the TV. | `LocalMultiplayerTransport`, host authority like `NetworkGolfRound` |
| **Online friends** | **One at a time for now (decided).** One shared lane, the same turn order as pass-and-play. Everyone watches the current bowler's throw on their own TV/phone. Host authority as below. | `NetworkGolfRound` host authority, Club Hub invites |
| **Quick game** | 3 frames (or 5) for parties. | |
| **Later: simultaneous online / Survival (8–16)** | Switch-style, everyone bowls their own lane at once and the bottom half is cut every 3 frames. Not in this pass. | `TennisGame.Versus` pattern |

**Same TV: one lane, turns (decided).** No split-screen lanes.

- **Turn order:** the real rule. Each player bowls a complete frame (both balls), then the next player.
- **Away policy:** `AwayPolicy.swift` (a player who leaves has their frames auto-bowled by CPU after 180 s).
- **Skip votes** for the pinsetter / replay.
- **Host-authority detail (local multi-phone and online):**
  - The guest phone computes **throw parameters** (start board, speed, axis, revs, release grade, loft, foul) and sends them.
  - The host simulates the lane (deterministic) and the pin action (PhysX), then broadcasts the pinfall plus 30 Hz pin keyframes (10 pins × pos+rot × ~120 frames ≈ 30 KB).
  - Everyone's TV plays the host's result. This matches golf's model.

---

## 9. Training / tutorial / extras (Wii's three, re-done)

1. **Bowling Lesson** (first play; ties into `PLAN_Onboarding_GolfLesson.md`). Three short steps:
   - (a) Hold + release on the slide foot, with haptic steps to feel the rhythm.
   - (b) Swing for power, with a speed readout.
   - (c) Flick for hook, with a ghost line showing the breakpoint.
   - Each step needs 2 successes to pass. This replaces any text wall.
2. **Power Throws:** pins grow each stage (10 → 15 → 21 → … → 91). Points per pin, double for clearing. Includes a secret-rail easter egg as an homage.
3. **Spin Control:** walls block a straight line, so you must hook around them. This teaches the flick.
4. **Spare Pickup:** 20 set-ups (10-pin, 7-pin, baby splits, bucket, washout). It teaches cross-lane spare shooting ("stand left for the 10-pin").
5. **Later:** 100-pin game, special lanes (moving bumpers, ramps, gap jumps), bumpers for kids/first timers (an **option**, as in real alleys).

---

## 10. Presentation (camera, HUD, audio, haptics, replays)

### Cameras (`BowlingCamera.cs`)
1. **Setup:** behind and above the bowler (Wii's view). The lane runs up the middle of the TV, and the pins are visible.
2. **Approach:** a slow push-in on the same line.
3. **Release → travel:** the camera **chases the ball low behind it** down the lane, speeds matched. On a hook, it slightly leads the hook direction.
4. **Pin action:** at 2 m before the head pin, cut to a **pin cam** (low, 3/4 front). A slight slow-mo 0.75× on impact frames only, then normal speed.
5. **Result:** a pause on the standing pins with a sticker graphic (X / spare / "7-10 SPLIT" / GUTTER). Then cut back to the bowler's reaction clip.
6. **Strike replay:** for turkeys, converted splits and the 10th frame, use the `TennisReplay` system (pin cam, slow-mo, skippable).

### HUD
- The classic **score sheet strip** at the top of the TV: player rows, 10 frames, X / – marks, split circles, running totals. It also feeds the monitor in the venue.
- Current player + frame + ball number.
- Speed (mph) after release.
- A release-grade sticker (PERFECT / GOOD / EARLY / LATE), using the golf `StrikeHud` style.
- A spin readout on the phone only.
- **Glass theme:** `ThemeService` for the colours.

### Audio (`BowlingAudio` on the existing buses)
- **The single most important sound is pin crash.** Layered by the number and speed of pin impacts: wood clacks per impact, a sustain rumble, and a "crisp strike" sweetener when all 10 fall. Add 6+ variants each. Real recordings or high-quality synthesis go through the `work/audio-pass` gates.
- **Ball roll:** a rumble loop pitched by speed. Louder on the dry back end (real lanes do this). A loft thud, gutter rattle, ball-return thunk + air blower, and pinsetter sweep clank.
- **Room:** neighbour-lane crashes (randomized, quiet), crowd murmur, crowd "ooh" on near misses.
- **Announcer** (Kokoro voice pipeline): Strike / Spare / Double / Turkey / Hambone / Split / 7-10 / Gutter / Perfect game, plus player names.

**As built (10-25, `BowlingSynth.cs` + `BowlingAudio.cs`):**
- **Pin crash:** rendered from the pin action's own impacts. `BowlingPinDeck.Listen` records each body's velocity jump per physics step as ball-pin, pin-pin, pin-kickback, pin-deck or pit. The crash is rendered on a worker thread while the ball rolls and starts on the first pin frame. Each impact is a modal model (pin clack 1–7.6 kHz, ball thump, deck knock, kickback thunk, pit thud). On top: a rumble that follows the hit density, a strike sweetener, and a venue reverb (club hall / neon hall / open beach / cave).
- **Ball and machine:**
  - Release whoosh by speed, landing (a loft is a deeper drop).
  - Roll rumble pitched by speed, louder past the oil; gutter rattle; foul buzzer.
  - Pinsetter sweep (clank, motor, clank), ball-return blower and knock.
- **Room:**
  - The crowd murmur hushes from Ready to the release.
  - Synthetic neighbour-lane crashes every 7–17 s.
  - Tiki surf / Magma cave ambience, music per venue (`bowl_<venue>` when made, else `game_light`; none in Magma).
- **Crowd:** reactions reuse the tennis/golf crowd files.
- **Announcer:** `GameVoice` keys `bowl_*` (strike, double, turkey, hambone, six_pack, golden_turkey, spare, split, seven_ten, split_converted, gutter, foul, welcome_<venue>). Silent until the lines exist.
- **Gates** (`Editor/BowlingAudioProof.cs` → `work/bowling/audio/proof/GATE_RESULTS.md`):
  - A1: crash loudness ranks with the pins.
  - A2: ≥ 6 distinct crashes.
  - A3: every pinfall is audible.
- **In-game recordings:** `BOWL_FILM_AUDIO=1` in the film (real time; the output is silenced while recording).

### Haptics (`GolfHitFeel.h` styles)
- New styles:
  - `BowlStep` (light tick per approach step).
  - `BowlReleaseWindow` (tension rising into the ideal moment).
  - `BowlRelease` (thunk, stronger on PERFECT).
  - `BowlPinCrash` (rumble scaled by pins down; the strike burst is distinct).
- **Timed to TV delay:** pin haptics fire on the TV's moment (as golf/tennis hit feel does), but step haptics fire in **phone time** because they *are* the timing cue (§4.2).

### Emotes and intros
- **Emotes:** the existing emote slots work in bowling. The plaza gets a bowling room.
- **Intro:** a venue flyover (`PresentationDirector`, skip votes), then each player picks up their ball.

---

## 11. Code layout (new files, following tennis/golf naming)

**Unity: `Scripts/Bowling/`**

| File | Role |
|---|---|
| `BowlingGame.cs` (+ `.Native.cs`, `.Network.cs`, `.Presentation.cs`, `.Results.cs`) | Builds the scene, state machine (Setup → Approach → Roll → PinAction → Reset → NextTurn). |
| `BowlingLane.cs` | All dimensions from §3.2 as constants, board ↔ metre helpers, pin spots. |
| `OilPattern.cs` | μ grid, house/sport/short patterns, optional transition. |
| `BowlingBall.cs` | Deterministic integrator (§6.1), step 1/240. Also used for the setup preview line. |
| `BowlingPinDeck.cs` | PhysX handoff, script stepping, pinfall rules, keyframe recording. |
| `BowlingPinsetter.cs` | Sweep/deck/ball-return animation. |
| `BowlingScore.cs` | Pure rules (§3.1), split/leave naming. |
| `BowlingThrow.cs` | Throw parameters struct (the network unit). |
| `BowlingSwingDetector.cs` | Phone samples → load, forward speed, yaw, roll flick, lift timing. Copies the `MotionSwingDetector` structure. |
| `BowlingLagLearner.cs` | Release-window latency learning. |
| `HeroBowlerDriver.cs` | Playables: approach legs + phone-scrubbed arm layer + release layers + body english; ball socket attach/detach. |
| `BowlingCamera.cs`, `BowlingHud.cs`, `BowlingAudio.cs`, `BowlingVenue.cs` (venue selection like `TennisVenue`) | Presentation. |

**Unity, existing files touched:**
- `NativeSportsSession` (`BeginSceneLoad` + `Load` + `Receive` bowling actions: `bowlMove`, `bowlTurn`, `bowlHold`, `bowlRelease`, `bowlSkip`).
- `ThemeService.SportOf`, `HubLayout` (bowling room + bays), build settings.
- `SportsMultiplayer` (sport string), `HeroAssets` (no new hero; ball/pin names registered), `HeroAccessories` (`Hand_Ball` socket).

**Swift:**
- `Sport.bowling.playable = true` (last step, behind a flag until gates pass).
- `SportsSession.startBowling`, a `SportsMotion` bowling mode (CoreMotion only, no ARKit).
- `BowlingController.swift` (setup strip, giant hold-ball, spin gauge, emotes).
- `MultiplayerSport.bowling`, `GuideDeck.bowling` + `HowTo` cards, `HubSession`/`HubControllerView` bay lists, `Progression` (ball unlocks).
- SceneKit lobby export of the held club ball (`MatchHeroLockerExport` + `MatchHeroData`). No Locker ball item for now (one ball for everyone).

**Art jobs:**
- `work/bowling-venue/` (Blender → FBX, baked lane textures, colliders as separate `UCX_` meshes).
- `work/bowling-ball-pin/`.
- `work/bowling-anim/`.
- All heavy jobs through `heavy.sh` (16 GB Mac rule).

---

## 12. Phases and binary gates

Every phase ends with `GATE_RESULTS.md` plus proof in `proof/bowling/<phase>/`. No proof = FAIL.

**P0 — Greybox and rules (Unity editor, keyboard input)**
- **S1:** `BowlingScore` EditMode tests pass. Cases: 300, 0, all 9-spares + 9 = 190, alternating X / spare = 200, all spares with 5s = 150, 10th-frame X-X-X, X-/-, 9/-X, open 10th, foul in each ball, gutter, split/washout detection on the 12 named leaves.
- **P1:** At 7.6 m/s, travel time to the head pin is 2.4–2.8 s.
- **P2:** On the house pattern, max-rev ball hook ≥ 8 boards with breakpoint 10–13 m. A no-rev ball hooks ≤ 1 board.
- **P3:** Monte Carlo of 2,000 throws per bucket. The strike rates in §6.2 fall within ±7 %.
- **P4:** 0 pin tunnel / explode events in 10k throws. Pins sleep in ≤ 4.5 s. The pinfall rule agrees with a human read on 50 recorded edge cases (wobblers, moved-standing, pit kick-ups).

**P1 — Phone input**
- **I1:** Recorded IMU sessions (20 swings across 3 people: soft/hard/hook/backup/straight/early/late/drop) replay through `BowlingSwingDetector` to the expected labels at ≥ 90 %.
- **I2:** The release window is latency-compensated. With a simulated 150 ms TV delay, a player releasing on the TV slide-plant grades PERFECT.
- **I3:** A thumb lift in steps 1–2 cancels and does not consume a ball.
- **I4:** A hold past the window always fouls: the slide foot is over the line in the replay, the buzzer sounds, the pinfall scores 0, and ball 2 after a ball-1 foul gets a full rack. A release inside LATE never fouls.

**P2 — Character + ball**
- **B1:** `BallGrip` pose with fingers in the holes at the face camera and gameplay camera; ≤ 3 mm finger/hole penetration.
- **B2:** No ball/thigh/garment intersection across the full approach for both sexes (`HeroClearance` sweep).
- **B3:** The ball reaches the ankle at `releaseIdeal` ± 1 frame on the baked clip.
- **B4:** No position or velocity pop at detach (≤ 1 cm, ≤ 5 %).
- **B5:** Lobby (SceneKit) holds the ball the same as Unity (hero-sync sheet).

**P3 — Alley art:** lane reads glossy with a pin reflection on the TV capture; board texture shows 39 boards; arrows/dots at correct metres (overlay vs §3.2); pinsetter cycle ≤ 3.5 s and skippable; ≤ 350k tris, ≤ 150 draw calls.

**P4 — Presentation:** the camera never loses the ball; strike replay plays and skips; pin crash audio has ≥ 6 variants and scales with pins; announcer covers the full list in §10; haptic step ticks are in phone time.

**P5 — Integration:** bowling launches from the menu, plaza and onboarding picker; pass-and-play 4 players complete 10 frames; local 2-phone host authority shows the same pinfall on both phones; online 2 players one at a time complete 10 frames with the same pinfall on both; away policy auto-bowls; the near-miss fun check from §6.2 passes.

**P6 — Training:** the Lesson passes for a first-time tester without verbal help; Power Throws / Spin Control / Spare Pickup are playable start to finish.

**DV — Device:**
- **DV1:** 60 fps on the phone + AirPlay during pin action (Instruments capture).
- **DV2:** Thermal ok over a 3-player 10-frame game.
- **DV3:** Release feel tested by Adnan on the real TV. This one is his call.

**Order:** P0 → P1 run in parallel with the art jobs (ball/pin, venue, animation are independent) → P2 → P3/P4 → P5 → P6 → DV. P0 is the riskiest (pin physics feel), so it goes first and is shown to Adnan as a capture before any art lands.

---

## 13. Decisions (Adnan, 10-24)

- **D1 Fouls: ON.** Holding past the release window carries you over the line: buzzer, 0 pins (§4.4).
- **D2 Aim: position only** for now. No angle turn, and the swing does not steer (§4.1, §4.3).
- **D3 Ball: the same ball for everyone.** One 14 lb club ball, no choices (§5.1).
- **D4 Play: one lane, one at a time.** Same TV, pass-and-play, local multi-phone and **online all take turns** for now. Simultaneous online / Survival is later (§8).
- **D5 Venue: Club Lanes** only (§7.1).
- **D6 Left-handed bowlers: later.**
- **D7 Pins: standard, lively and fun, but not easy to strike.** One tuning for everyone, no assist option (§6.2).
- **D8 Sources:** only the **alley** comes from SportsLibrary. The **ball and pins are new**, because they are easy to make. No V4 animations and no SportsLibrary crowd.
- **Animations:** keyed from **real-life bowling footage or bowling-game gameplay**, recorded by clip id in `work/bowling-anim/REFERENCES.md` (§5.3, gate A0).

---

## Sources
- Wii Sports bowling controls and release-timing behaviour: [Wikibooks — Wii Sports/Bowling](https://en.wikibooks.org/wiki/Wii_Sports/Bowling), [Wii Sports Wiki](https://wiisports.fandom.com/wiki/Bowling_(sport)), [StrategyWiki — Wii Sports Club controls](https://strategywiki.org/wiki/Wii_Sports_Club/Controls)
- Wii training games: [StrategyWiki — Bowling Training](https://StrategyWiki.org/wiki/Wii_Sports/Bowling_Training), [Nintendo — Bowling Training Tips](https://www.nintendo.com/en-gb/Support/Legacy-system/Bowling-Training-Tips-613258.html), [Giant Bomb — Wii Sports](https://giantbomb.com/wiki/Games/Wii_Sports)
- Switch Sports bowling: [Nintendo — Switch Sports Bowling](https://www.nintendo.com/sg/switch/as8s/bowling/), [GGRecon bowling tips](https://ggrecon.com/guides/nintendo-switch-sports-bowling-tips), [Nintendo developer tips (scoring, Survival)](https://www.nintendo.com/us/whatsnew/developer-tips-part-ii-bowling-chambara-and-a-secret-code/), [Pro Game Guides — Survival Bowling](https://progameguides.com/nintendo-switch-sports/what-is-survival-bowling-in-nintendo-switch-sports/)
- Lane and ball specs: [Top End Sports — tenpin dimensions](https://www.topendsports.com/sport/tenpin/dimensions.htm), [USBC ball spec summary](https://images.bowl.com/bowl/media/legacy/internap/bowl/associations/pdfs/BallSpecSummary.pdf), [Wikipedia — Tenpin bowling](https://en.wikipedia.org/wiki/Tenpin_bowling), [Wikipedia — Bowling ball](https://en.wikipedia.org/wiki/Bowling_ball)
- Ball motion and entry angle: [Storm — skid/hook/roll](https://www.stormbowling.com/read/bowling-ball-reactions-skid-hook-roll), [USBC — adjusting entry angle](https://bowl.com/adjusting-entry-angle), [USBC ball-motion study](https://images.bowl.com/bowl/media/legacy/internap/bowl/equipandspecs/pdfs/ASQBallMotionPresentation.pdf), [Wikipedia — Hook (bowling)](https://en.wikipedia.org/wiki/Hook_(bowling))

## 14. Status 10-26 (branch `bowling/ship-2026-10-26`, worktree 2026-10-26/bowling)
- **In the menus:** pointer menu Bowling card + modes (Play, Exhibition, Pass the phone, Online); TennisMenu game select / venue picker (4 venues, `map-bowling-<venue>.jpg`); HubSession routes `bay-bowling-*`; `Sport.bowling.playable`.
- **Exhibition vs the computer:** `BowlingCpu` (plans lines on the real lane integrator, skill-scaled misses). Opponents measured over 16 games (`BowlingGameHarness`): Rookie Ray 112, Steady Sam 148, Lucky Lou 174, Pro Pia 202.
- **Scoring counts:** Unity `bowlingGame` summary → `BowlingGameStats` → `Progression.awardBowling` (XP lines), `SportProgress.recordMatch`, the post-match screen (phone Finish button).
- **Pin carry:** tuned (carry r5/r6, 250 throws a bucket): pocket ~80 %, straight 45-50 %, light ~35 %, Brooklyn ~23 %, nose ~10 % (all in range).
- **Phone only (V2, self-timed):** the release is judged against the player's own arm passing the bottom (`BowlingSwingDetector.SinceBottom`, bottom angle measured on the backswing); the walk is time-warped to the swing (`HubHeroAnimator.ActionRate`); tick/buzz haptics from `bowlCue`. No TV: the lane plays on the phone in portrait under a see-through overlay controller (`SportsDisplays.phonePlayWindow`). Gate G6 tests pass at 3 tempos.
- **Multiplayer (local + online):** `MultiplayerSport.bowling`; every phone runs the game, the bowler's phone sends its throw + pinfall (`BowlingGame.Network`), the host bowls for dropped players. Proof `BowlingNetProof`: two phones, identical score sheets (G7 PASS).
- **Polish:** strike / Turkey / converted-split slow-motion replay (tap to skip), pin-crash rumble on the phone, how-to tips rewritten.
- **Combined 10-26 evening (clothes):** Clothing V3 (yarn atlas + fibre shine, Unity + lobby), the male polo tear fix, the female tennis tank R3 and both bowling kits (male camp-collar shirt + slacks + saddle shoes; female sleeveless camp-collar blouse BF_SL6 + skirt: `PlayerFemaleBowlingKit`, `BowlingKitHero_Female`, `Resources/Bowling/KitsV2/Female`) copied from the main checkout, lobby hero assets + goldens re-synced. `MatchHeroSurfaces.swift` 3-way merged (main's nil-safe `garment` + V3 surface). Unity EditMode 727/730 (3 = clone has no sibling GolfArcade/ folder), iOS build-for-testing SUCCEEDED.
- **Not done:** device run (2-phone, phone-only feel, thermal), TV-loss mid-round prompt (PhonePlay §3), plaza walkable bowling bays, onboarding bowling lesson + drills (P6), announcer lines (ElevenLabs credits not approved).
