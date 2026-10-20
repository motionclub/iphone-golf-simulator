# GATE RESULTS — SERVE_AND_FEET (2026-10-03)

**GATE: SERVE_AND_FEET FAIL** — three of the ten pre-registered lines fail (`GATE_DEFS_preregistered.md`, thresholds not changed after a result was seen). One is a real miss of this job (NO_SLIDE_SUBSTITUTE); two are literal failures caused by other sessions writing into the shared repo while the job ran (FROM_WATCH media rule, BALL_UNCHANGED hash list). `scripts/check_gates.py` recomputes the table from files → `checks.json`.

| # | gate | result | one-line reason |
|---|------|--------|-----------------|
| 1 | FROM_WATCH | **FAIL (not by this job)** | everything of this job passes (only `JJEDwXeDjBc` and `rxo1uEdLouY` appear; no media under work/serve-and-feet; every Serve key carries an S3 token; walk / run carry S1 / S2 tokens). The "no media added anywhere in the repo during the job" rule sees 4 files written by other sessions: `ArtDir/ui/motion-club-radial-v1/runtime/Motion_Club_{Menus_and_Transitions,Living_Backgrounds,Hinge_Transitions}.mp4`, `ArtDir/screenshots/golf_flyover/cliffside_flyover.mp4` |
| 2 | SERVE_BOUNCE | PASS | thin, no bounce time; tossing palm 1.5 mm (m) / 1.5 mm (f) below frame 0, min 0.881 / 0.893 m; FBX object list identical to the other clips (8 objects) |
| 3 | SERVE_HIPS | PASS | Blender: +70° from frame 0, +40° from the stance, unwind 66° (both sexes). Play mode (Hips transform): load 40.1–42.2°, unwind 64.2–66.2°, four cases (player + rival, both sexes) |
| 4 | SERVE_CONTACT | PASS | contact 1.700 s = frame 51, `Contact` marker there, sweet spot highest on that frame, prefab slot 1.700 s (both). Play mode: 59 player + 16 rival serves, both sexes, every contact within 1 frame (−13.7…+3.3 ms); strings-to-ball at the contact instant ≤ 12 cm for 100 % (max 8.2 cm) |
| 5 | WALK_STEPS | PASS | 1.10 s loop, closed to 0.0; each foot planted 64 %, clear ≥ 40 mm 27 % / 24 %, peak 94.9 / 94.0 mm; one foot planted on every frame; planted foot 1.2500 m/s = design. Play mode: Walk weight 1.00, `FootSkate` median 0.027 m/s (m) / 0.027 (f) |
| 6 | RUN_BOTH_LEGS | PASS | 0.567 s loops, closed; each foot planted 41 %, clear ≥ 60 mm 47–53 %, peaks 199.5 / 200.0 mm (ratio 0.997); planted speed = design 3.2508 m/s; RunRight hips +70°, RunLeft −70° (own clip, racket socket unmoved < 2e-7); toe-bone slide at design speed: 0 frames (walk), 1 per foot (run). Play mode: 101 / 101 run windows show ≥ 60 mm clearance for both feet in every cycle (RunForward 50, RunLeft 23, RunRight 28; 70 male, 31 female) |
| 7 | NO_SLIDE_SUBSTITUTE | **FAIL** | legs differ from ReadyIdle by 19.8° (walk) / 33.6–34.3° (runs) ✓; Walk ≥ 0.9 / Ready < 0.1 on every walking frame ✓; run frames on the Run clips 100 % ✓; **share of moving frames whose planted toe slides > 0.15 m/s = 41.6 % (limit 20 %; HERO_MAINSTAY 87 %)** ✗ |
| 8 | OTHER_CLIPS_UNCHANGED | PASS | 96 hashed files: only `{Male,Female}_Serve.fbx` + `.meta` differ, 8 new FBX + 8 new `.meta` (Walk, RunForward, RunLeft, RunRight); the 15 other actions have the same F-curve hashes as the source blends; body / face mesh hashes equal; source hero blends = the two SHAs of the brief |
| 9 | NO_OLD_HERO | PASS | every slot asset is under `Assets/Characters/MatchHeroes/`; `look` null, `matchLook` set (4 of 4 heroes); played clip names all `Male_` / `Female_`; no added line anywhere refers to Hero01 / Resources/Tennis/Hero / Opponents / Hero_Run / Hero_Walk; prefab diffs are only the slot list, the three serve times and the speed fields |
| 10 | BALL_UNCHANGED | **FAIL (not by this job)** | TennisGame, TennisBall, TennisRules, TennisMatch, TennisActor, TennisServeRoutine, TennisOpponent, TennisUmpire byte-identical; the driver diff (11 hunks, `data/HeroTennisDriver.diff`) touches no ball / score / rules member. Literal hash list: `Tennis/HeroKit.cs` differs from the job-start hash — written 15:29:48 by another session (worn-kit work), not edited here; `MatchHeroLook.cs` also differs (allowed by the line) |

## Why NO_SLIDE_SUBSTITUTE fails, with the numbers (`proof_metrics.json → no_slide_unity.by_what_plays`)

Player frames moving faster than 1 m/s (20,406 of them), by what is playing (final Play-mode proof, real project):

| playing | share of moving frames | frames with planted-toe slide > 0.15 m/s | median |
|---|---|---|---|
| Walk ≥ 0.9 | 28 % | **17.5 %** | 0.027 m/s |
| Run clips ≥ 0.9 | 37 % | 39.7 % | 0.111 m/s |
| action layer (the other 15 clips + Serve) | 32 % | 61.5 % | 0.43 m/s |
| blending, no clip ≥ 0.9 | 4 % | 73.7 % | 1.2 m/s |

* The action layer is the 15 untouched stroke clips (gate 8 forbids changing them) and is a third of the moving frames at 61 %: with every other frame perfect the share would still be ~20 %.
* Run frames: the clip itself has zero toe slide at design speed except one frame per foot per cycle (toe leaving / landing, 0.5 and 2.0 m/s, `data/toe_slide_Rig_*.json`); the rest is the heel-to-toe roll counted by the 15 mm rule, accelerations, turns and cross-fades between clips.
* The walk is under 20 % on its own (17.5 %); before this job's driver work the same frames were at 0.35 m/s median (see below).

## What the Play-mode proof found, and what was changed in `HeroTennisDriver.cs` (all visual-only, 11 hunks)

1. **The game runs at its own pace** (0.75 on the serve walk-in, 1.2 in a rally) while `actor.Speed` is in game seconds, so the hero really moves `Speed × pace` m/s. The driver set walk / run clip rates from the unscaled speed: planted feet slid by about 25 % (walk) and 15 % (run) of the speed. The driver now measures the pace (real displacement / commanded, smoothed 0.15 s) and uses it for the clip rates. Walk planted-toe median 0.352 → 0.027 m/s.
2. **The actor moves in 1/120 s game steps**, so a 60 fps frame covers 1, 2 or 3 steps and the hero's position judders by up to a step (11 mm walking, 40 mm running) while its planted feet are still. The hero is now drawn at the actor position carried forward at the real velocity and eased back onto the actor (visual only; the actor, ball, contact are untouched).
3. **Diagonal runs**: the blend of RunForward with RunRight / RunLeft is slide-free only when both play the same way round (`data/run_blend_model_*.json`: speed 0.985 V, angle = 90° × weight). Backing away played RunForward in reverse against forward lateral clips, which cancels the leg swing (0.18 V at 50 %). Now: toward the net, F + R / L with weight angle/90; away from the net, F reversed + the opposite lateral clip reversed (shared run phase, reverse pivot 0.2167 s from the stance windows), family change past 100° / back before 80°. Mixed-direction medians 0.75–2.4 → 0.1–0.4 m/s.
4. Run clip rate cap 1.6 → 2.0 (match heroes only; real speeds reach 7 m/s). The ankle lock does not run while Walk / Run clips carry ≥ 0.9 of the legs.
* `MatchHeroImport.cs` / `MatchHeroBuild.cs` (Editor): one line each so a rebuild of the prefabs keeps the SERVE_AND_FEET clips (otherwise the old Serve would come back).

## Numbers the gates do not ask for

* Serve contact: the previous Serve (HERO_MAINSTAY, `contact_lands.txt`): male 11 swings mean 2.1 ms max 3.3 ms; female 10 swings mean 2.0 ms max 3.3 ms. New: −13.7…+3.3 ms. The strings-to-ball gap read on the frame the log fires on (not at the instant of contact) is 64 % ≤ 12 cm, max 0.37 m, because that frame can come after the game has launched the ball; the gate value uses the instant the time-to-contact reaches 0 (ball taken back along its own pre-launch path, strings between the last two frames). Both are in `proof_metrics.json`; the closest approach of the strings to the ball is ≤ 5 mm for the perfect-toss serves.
* The first Serve build failed SERVE_BOUNCE by the written definition (palm 99 mm below frame 0 while settling from ReadyIdle into the stance) — fixed by holding the ball in the fist from frame 0; the check in `verify_blend.py` was changed to the pre-registered "from frame 0" definition at the same time.
* Racket socket moves < 2.3e-7 (constant) over every new clip; lowest foot vertex ≥ −1 mm; Play-mode foot peaks equal Blender's (walk 94.9 mm, run ≈ 200 mm).
* Arm / forearm into the body (verify_clear): new Serve male 84 mm (right hand, follow-through), female 28 mm; the accepted old Serve was 127 mm, Forehand 100 mm, ForehandWide 120 mm; racket into body ≤ 1.2 mm.
* Prefab: Serve contact 0.9 → 1.7 s, serve times 0.200 / 0.700 / 1.333 s, `walkClipSpeed` 1.25, `runClipSpeed` 3.2508, `runReversePivot` 0.2167 (both prefabs); skin / mesh / materials / the other 15 slots untouched.
* THIN (WATCH.md): the serve bounce is not in frame; the hip angle in degrees, the ball on the strings and the slow-motion factor are not readable. The Serve is paced by the game (stance → release 0.5 s, release → trophy 0.62 s); the swing from the trophy to the contact is re-timed by the driver as before.

## Proof (Play mode, game camera, both sexes) — `proof/`

`PROOF_serve_{male,female}.jpg` (stance, toss, trophy, deepest bend, push-off, contact, landing; behind and high views; hips yaw printed), `PROOF_walk_{male,female}.jpg` (12 steps 0.1 s apart, foot heights printed), `PROOF_run_{male,female}.jpg` (side-on, frames flagged BOTH FEET OFF THE COURT), `audit.txt`, `shots.json`, `trace.csv.gz` (every frame: weights, foot heights, FootSkate). Blender review sheets: `blender_sheets/`.
