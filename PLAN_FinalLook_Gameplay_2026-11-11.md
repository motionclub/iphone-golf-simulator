# Master plan — final look, gameplay and animation (2026-11-11)

One plan for everything discussed on 11-10 and 11-11: the visual audit, the character work, customisation, ball physics, game speed and animation. Nothing in this plan has started except what is listed under "Where things stand". Sizes are rough estimates in working days, not commitments.

## The direction

**Arcade that looks real but goofy.** The ball, the body and the light behave believably; the fun comes from exaggerated reactions around them.

| Kept real | Made goofy |
|---|---|
| Ball flight, bounce and roll | Wind-ups, overshoot and follow-through |
| Feet planted, weight shifting, hands that grip | Reactions to a win, a miss, a strike, a shank |
| Light, shadow and cloth that suit the venue | Hit effects, trails, confetti, camera kicks |
| Muscles and proportions that read as athletes | Faces: effort, focus, joy, despair |

Three constraints hold through every phase:

- **No lag,** especially on the TV: 60 frames a second with even pacing.
- **Gameplay feels smooth:** no hitches, pops or sliding.
- **Customisation matters:** what a player picks shows up in play, not just in the locker.

## Where things stand

*Updated 2026-11-11 23:15. Gates, numbers and proof: `work/final-plan-1111/GATE_RESULTS.md`.*

- **Go given 2026-11-11** ("proceed with this plan"). Decisions 1 and 2 are taken as accepted with it. Decision 9 is still open.
- **Phase 0, partly done.** The project compiles with everything installed; EditMode is green (758 of 758 after one fix: the arm-shaping pass was denting her skirt and his shorts). PlayMode runs in seven batches (a single run used 16 GB and was stopped): 209 tests, 165 passed, 41 failed, 3 skipped at the start. Two failures have a cause; 39 do not yet. Frame times on the Mac editor are in (tennis intro 51 fps, tennis match 56–58, golf and plaza 60); **none on a phone or TV.**
- **Phase 1, built and in `Unity/`, uncommitted:**
  - Tennis: flatter, faster ball. Rally balls peak about a third lower in the real game (yours 2.5 m to 1.6 m, the rival's 2.65 m to 1.9 m); rally length and winner counts are unchanged in self-play. One rival (Tama, the moonballer) still peaks at 2.3 m.
  - Golf: new landing. Drive skips low and runs 19 yd, 7 iron 6 yd, wedge stops by its pitch mark, lob wedge draws back, bunker and rough as the table asks, slope counts, each hop lands on its own ground.
  - Waits: tennis intro 6 s with a one-player skip, pre-serve 1.2 s, golf flyover 4 s, hole-out 3 s, bowling sweep 1.5 s and replay 4 s.
  - EditMode with all of it: 778 of 778. `work/final-plan-1111/ROLLBACK.sh` undoes Phase 0 and 1.
- **Phase 1, checked in the game on the Mac:** PlayMode on the changed code is 164 / 42 / 3: no test that passed before fails because of it (one hub test is unsteady on both copies; one replay test's set-up was tied to the old run-out and was changed). Mac frame times are unchanged. Golf landings filmed in still air (`work/final-plan-1111/phase1/proof_golf_landing_film.jpg`): wedge hops fell from 1.1–1.3 m to under 0.2 m and stop within 1.2 yd.
- **Phase 1, not verified:** the one filmed drive ran 12.9 yd against a 15–30 yd target (tests hold 19 on flat ground; not explained); no 7 iron filmed onto fairway; the shortened waits have not been watched in game; nothing has run on a phone or TV.
- **Phase 2, installed in the game project on 11-12 at your word, uncommitted:** his whole-body rebuild with fitted tennis, golf and bowling tops and rounded shoe toes; her refitted tops, tapered wrist, lighter forearm, and her walk (arms no longer flared, elbow and wrist matched to his). EditMode 778 of 778 on a synced copy; the installed game is shown in `work/final-plan-1111/look/installed_1112.jpg`. Switches and rollback are listed in `work/final-plan-1111/GATE_RESULTS.md`. The menu, locker and lobby heroes were re-exported from the installed game the same day (`work/final-plan-1111/look/menu_characters_1112.jpg`; undo with `ROLLBACK_MENUS.sh`), so they match the game again; the app's own test of its heroes against Unity's reference passes on them (14 older tests in the same files were already failing and still are). Not done: PlayMode, a phone build, a look at the menus in the app itself, his legs, her hands' shape, and the animation rework (the wrist passes human limits in 91 of 107 animations).
- **Animation rework, step 1, INSTALLED 11-13 13:42 (uncommitted, `ARM_LIMITS=0` off):** the wrist and elbow rule below is now in the game and in the menu export. EditMode 778 of 778. Films of every animation: `work/final-plan-1111/anim/films_1113/`.
- **Animation rework, step 1, built in the project copy only (11-12):** one wrist and elbow rule for every sport (`work/final-plan-1111/anim/HeroArmLimits.cs.txt`). In real play her tennis ready-stance wrist goes from 60 degrees off the forearm's line to 13, the golf address hand from 54 to 24, bowling's empty hands stay under 42 (they reached 97); no jumps; EditMode 778 of 778 on the copy. Not solved: the hand that carries the racket or club in a stroke (still up to 82 in tennis, 106 putting), the serve's ball hand, the menu heroes. Not in the shared project: another chat is editing hand code there. Proof `work/final-plan-1111/anim/proof_wrist_limits_v1.jpg`.
- **Installed in `Unity/` before this plan, uncommitted:** the men's muscular build, her arm shape, forearm twist bones, the shoe reshape, hero lighting on by default, the calmer menu grade, the menu head turn, and the 10-30 cloth shine pass. Each has an off switch; `work/hero-build-1111/ROLLBACK.sh` restores the 11-11 install.
- **Your verdict on the build:** the arms look fat, not defined, and the forearms grew as much as the upper arms. That method (thickening everything evenly) is finished; Phase 2 replaces it.
- **Abandoned:** the code-built replacement model and the generated reference images.
- **Audits behind this plan:**
  - `work/visual-audit-1110/AUDIT.md` — whole-game look
  - `work/hero-look-1111/CHARACTER_AUDIT.md` — hero look, weight, customisation
  - `work/hero-depth-1111/HERO_DEPTH_AUDIT.md` — her arms, shoes, her clothes
  - `work/hero-build-1111/HERO_BUILD.md` — what was installed
  - `work/gameplay-audit-1111/GAMEPLAY_AUDIT.md` — ball physics, pacing, animation

## Rules for every phase

- **One component at a time.** Each is judged in game light as played, shown to you as real game renders, then the next begins.
- **Pass or fail gates.** Each phase lists numbers that must hold. "Looks better" is not a pass.
- **Fix the asset, not the load.** New character work is built in Blender and exported finished. No new fixes that rebuild meshes when a match loads.
- **Budget rules for anything added:** pooled effects only, one hero light setup, a fixed post-processing cost, quality tiers for older phones.
- **Physics changes replace their tests.** A changed ball model ships with tests that pin the new behaviour.
- **Same result on every phone.** Any randomness in a shot is seeded and shared, so party and online play stay identical.
- **Safe working:** every Unity and Blender run goes through a copy of the project; every install has a switch and a rollback; staged only, no commits unless you say so.

## Order at a glance

| Phase | What | Size | Why here |
|---|---|---|---|
| 0 | Baseline and budget | 1 | Nothing else can be judged without it |
| 1 | Ball and pace | 3–4 | Your three gameplay complaints; code only, fast to feel |
| 2 | Bodies: arms as muscles | 3–4 | Your open complaint on the installed build |
| 3 | Her clothes, both shoes | 4–5 | Largest remaining character gap |
| 4 | Hero weight and load-time fixes | 3–5 | Pays for everything after it on the TV |
| 5 | Animation | 6–8 | Bowling first, then tennis, golf, the goofy layer |
| 6 | Hit feedback and celebrations | 3–4 | Biggest "over the top" gain per day |
| 7 | Lighting and venues | 3–4 | |
| 8 | Customisation | 4–6 | |
| 9 | Interface | 3–4 | |
| 10 | Final check on phone and TV | 1–2 | |

Roughly 35–45 working days in total. Phases 1, 2 and 6 give the most visible change earliest.

---

## Phase 0 — Baseline and budget

**Work**
- Open the real project with the installed changes, run the test suites, and fix what breaks.
- Measure frame time on a phone and on the TV output in each sport, with four players where the sport allows.
- Record load times and any hitch at match start.
- Write the budget down: frame time, triangles and renderers per hero, effect counts.

**Gates**
- Test suites green, or each failure listed with its cause.
- A table of measured frame times per sport and device exists.

**Needs from you:** which phone and which TV count as the minimum.

## Phase 1 — Ball and pace

### Tennis: a flatter, faster ball
The ball is slow (10–17.5 m/s), so it has to arc high to cross the court. Ordinary shots peak at 2.6–3.8 m against about 1.6 m in real tennis.

**Work**
- Raise shot speed and lower net clearance until ordinary shots stay near head height.
- Take pace off the ball at the bounce, so the player keeps reaction time without the ball hanging in the air.
- Lower the bounce (it keeps 75 % of its height today) and re-check the smash threshold.
- Cut CPU lobs: lower peak, far fewer of them.
- Re-check timing windows, swing lanes and CPU positioning against the new flight times.

**Gates** (starting targets, tuned by your feel)

| Measure | Today | Target |
|---|---|---|
| Perfect drive peak | 2.6 m | 1.8 m or less |
| Average shot peak | 3.8 m | 2.2 m or less |
| CPU drive peak | 3.7 m | 2.2 m or less |
| Second arc after the bounce | 1.7–2.3 m | 1.3 m or less |
| CPU lob | 4.4 m, up to 1 in 5 | 3.5 m or less, at most 1 in 12 |
| Time from opponent's hit to your contact | — | no shorter than today's fastest rally ball |

A new test pins rally peak height; none exists today.

### Golf: a landing that depends on the shot
The flight is good. Every full shot is forced to hop 1–2.4 m and skip two or three times, whatever the club.

**Work**
- Rebound from descent angle, speed and surface firmness.
- Backspin that checks the ball, and draws it back for a well-struck wedge on a green.
- Bounce off the real ground slope at the landing point.
- A distinct table per surface: tee, fairway, fringe, green, rough, bunker, out of bounds.
- Judge the surface again on every hop.
- A small seeded spread, so identical swings are not pixel-identical.
- Keep the aim preview and the shot map consistent with the new model.
- Roll and putting stay as they are.

**Gates**

| Shot | Target |
|---|---|
| Full wedge onto a green | First hop 0.5 m or less; stops within 3 yd of its pitch mark, or spins back |
| 7 iron onto fairway | One or two hops; 5–10 yd of run |
| Driver onto fairway | Skips forward; 15–30 yd of run |
| Any shot into a bunker | No hop |
| Any shot into rough | One dead hop |
| Same shot, upslope against downslope | Upslope finishes clearly shorter |

The test that requires 2–3 hops for every club is replaced by these.

### Pace: cut the waits

| Wait | Today | Target |
|---|---|---|
| Tennis intro | 12.9 s | 6 s or less; any one player can skip |
| Tennis pre-serve routine | 2.2 s | 1.2 s |
| Golf hole flyover | 7.9 s | 4 s, skippable |
| Golf after holing out | about 5.5 s | 3 s |
| Bowling pin sweep | 3.1 s, cannot be skipped | 1.5 s or skippable |
| Bowling strike replay | up to 8 s | 4 s |
| Bowling walk back | about 3 s | covered by the next player's setup |

Golf players hitting at the same time is a bigger change and is listed under decisions.

## Phase 2 — Bodies: arms as muscles

**Work, in this order**
1. **Male arm, rebuilt as separate muscles** in Blender by code: three deltoid heads, biceps, triceps, the forearm masses. Transferred onto the current mesh.
2. **Definition baked into the skin:** a normal map and a crease map from that sculpt, so it reads at gameplay distance.
3. **Light that shows form:** hero fill moved to the side, creases darkened. The current camera-side fill flattens muscle.
4. **Flex:** biceps peaks as the elbow bends, triceps tightens as it straightens.
5. **Chest, back and legs** the same way.
6. **Her arms** at lower intensity, plus the hard edge behind her shoulder and matching shoulder support.

**Gates**
- Upper arm clearly thicker than forearm; narrow elbow and wrist; arm oval in cross-section, not round.
- Biceps and triceps separation visible in a rally frame at gameplay distance, not just in the studio.
- No skin through any garment across the tennis, golf and bowling kits.
- You approve the male arm before anything else in this phase starts.

**Target:** `ArtDir/hero/targets-2026-10-12/tier1/01_male_body_turnaround.jpg`, if that is still the build you want.

## Phase 3 — Her clothes, both shoes

**Work**
- **Her tank and skirt** rebuilt to the standard of his polo: clean armholes and hem with thickness, a waistband, baked folds, a matching finish, tidy undershorts.
- **Both shoes remodelled** as low sneakers on a real last. The foot is already hidden under the shoe, so the box shape is no longer needed.
- **Cloth in full sun:** the shine reads as vinyl in golf close-ups; the trouser crease looks crumpled at the knee.
- **All clothing colours stay customisable.** Checked on light, dark and saturated picks.

**Gates**
- No ragged edge on her tank or skirt in any rally frame.
- Shoe width to length about 0.38 (0.49 today); toe lower and narrower than the heel.
- No poke-through or tearing in the rally films for either sex.

## Phase 4 — Hero weight and load-time fixes

Done after Phases 2 and 3 so the new meshes are reduced once.

**Work**
- Cut each hero from 206–228 thousand triangles to about 60 thousand, part by part.
- Merge renderers (13 today) by pairing socks, shoes and face layers.
- Bake the roughly 40 fixes that rebuild each hero at load into the assets.
- Re-export the phone locker's copies so the locker matches the game.

**Gates**
- 60 thousand triangles or fewer and 7 renderers or fewer per hero at full detail.
- No visible difference at menu and close-up size, shown side by side.
- Match load time and frame time no worse than the Phase 0 baseline, and measurably better with four players.
- The locker hero matches the game hero.

## Phase 5 — Animation

### 5a. Finish the audit
- Run the all-clips check overnight on the old bodies and the new ones, so real clipping can be told apart from the tool misreading the new build.
- Film the golf swings and the bowling delivery the way the tennis rally was filmed.

### 5b. Bowling
- Body tempo follows the player's swing instead of one fixed-speed clip.
- Play the clips that already exist and are never used: pickup from the ball return, walk back, watching the pins, sitting, cheering, the intros, win and lose.
- Blend at release; no 3.5 m jump when the delivery ends; feet planted during the slide.
- A reaction to a gutter ball and to a strike.

### 5c. Tennis
- Serve at full speed with the racket moving at contact.
- No pop when a swing starts; feet that do not slide.
- Her elbows brought in during runs and recoveries.
- Free hands relaxed, not clawed.

### 5d. Golf
- A natural address pose with some variation between holes.
- Fixes from the swing films in 5a.

### 5e. Hands and clothes
- Re-bake the hand-clearance tracks for the new bodies, so low hands stop sinking into shorts, thighs and hips.

### 5f. The goofy layer
- Wind-up before big swings and overshoot after them.
- Faces: eyes that follow the ball, plus effort, focus, win and lose expressions.
- Big reactions: a won point, a double fault, a strike, a gutter ball, a holed putt, a shot in the water.

**Gates**
- The audit report exists for every clip on both sexes, with a baseline.
- Bowling: every authored clip is reachable in a normal game; delivery length tracks swing length.
- Tennis: feet slide on 20 % of moving frames or fewer, the project's existing limit (41.6 % when last measured on 10-03); racket moving at serve contact.
- Each sport has at least one win and one lose reaction that shows the face.

## Phase 6 — Hit feedback and celebrations

**Work**
- **Tennis:** a coloured hit ring and sparks by timing grade, a ball trail, dust at the feet, and a point-won beat with a slow-motion last hit, confetti and a winner close-up.
- **Golf:** a ball trail, a landing puff per surface, a hole-out moment. The strike burst and splash are already good.
- **Bowling:** a flash on pin impact and a strike explosion.
- **Camera:** a small kick on perfect hits.
- Effect and trail colour come from the player's accent pick.

**Gates**
- Every effect is pooled; frame time stays inside the Phase 0 budget on the TV with four players.
- A perfect tennis hit is readable from across a room, compared with the target video.

## Phase 7 — Lighting and venues

**Work**
- **Golf fog bug:** fog weather floods 4 of 16 holes with one flat colour and blanks the shot map.
- **Bowling:** Club Lanes is a black room; the pin camera is blown out white; the crowd's skin is grey; the scoreboard covers the top quarter of the screen.
- **Heroes in each venue:** a side key and rim light per venue, visible ground shadows on the rooftop and volcano courts, white kit that stays white.
- **One colour grade per venue,** including the menu.
- **Tennis net** breaks into bars at 720p.
- **Small items:** hard white rain lines, a black disc beside the golf ball at address, old "MOTION CLUB" signs in the plaza.

**Gates**
- No golf hole renders as a single flat colour under any weather.
- Club Lanes walls and ceiling visible; pins show shading on the pin camera.
- A ground shadow under every player in all three tennis venues.

## Phase 8 — Customisation

| Today | Added |
|---|---|
| Sex, skin, shirt, shorts or skirt, shoes, racket colour | Accent colour as its own pick |
| Cap forced on, fixed colour | Cap colour, cap on or off |
| One finish, hard-coded | Matte, satin or gloss |
| No patterns | Stripes, halves, a chest number, a crest |
| One garment per slot | At least two styles per slot |
| Bald under the cap | Hair styles and colours, once one is fitted to the current head |
| Picks show on the hero only | Hit effects, ball trail and celebration follow the player's picks |

**Gates**
- Every new pick saves, reloads, and shows the same in the locker and in all three sports.
- Existing saved selections still load unchanged.
- New zones are material values only: no extra draw cost per hero.

## Phase 9 — Interface

**Work**
- The glass style on the tennis and bowling displays, result screens and handheld controls.
- Nothing drawn over the player: the tennis timing bar currently sits on the feet.
- Result screens with a backing panel and one button style.
- Text sized to read from across a room; score pops and screen transitions.

**Gates**
- No display element overlaps a player in any sport, in TV and handheld layouts.
- Grade and score text readable at TV distance, checked on the TV.

## Phase 10 — Final check on phone and TV

- Frame time, pacing and load re-measured against Phase 0.
- Render sharpness, shadow resolution and edge smoothing tuned per quality tier.
- Pops when character detail levels switch.
- A full party session in each sport.

**Gate:** 60 frames a second on the TV output in every sport, with no hitch at load or match start.

---

## Decisions for you

| # | Decision | Why it is yours |
|---|---|---|
| 1 | Tennis: accept a flatter, faster ball | It reverses the "hang time" change you asked for on 10-26 |
| 2 | Golf: wedges that stop instead of bouncing | It reverses the "not bouncy enough" change from 10-28 |
| 3 | The muscle target | Whether the tier1 turnaround is still the build you want |
| 4 | The uncommitted work in `Unity/` | Commit it as the base for this plan, or keep staging |
| 5 | Tennis camera and court colours | The game has drifted from the target video; you earlier said to keep the framing |
| 6 | Hair and the male face | Fit the existing hair or stay with caps; restyle his face or leave it |
| 7 | Golf turns | Whether players may hit at the same time to cut waiting |
| 8 | The plaza | Whether it still ships; it decides if its signs and mirror get fixed |
| 9 | Minimum phone and TV | Sets the budget in Phase 0 |

Decisions 1, 2 and 9 block Phases 0 and 1. The rest can wait until their phase.

## Risks

- **Freehand shape work is slow.** Arms, shoes and her clothes are the phases most likely to overrun; each is gated on your eye.
- **Ball changes ripple.** Tennis timing, CPU play and golf aim previews all depend on the flight model and need re-tuning with it.
- **Nothing has been measured on a device.** Phase 0 may reorder this plan, most likely by pulling Phase 4 forward.
- **The animation audit is unfinished.** Phase 5 sizes assume the earlier findings still hold on the new bodies.
