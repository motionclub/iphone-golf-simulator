# Serve walk / ball arm — GATE FAIL

2026-10-05. Requested prompt read in full and executed in the golf simulator project.

Project: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`. Work: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm`.

**No production carry fix was installed.** The new editor proof tool is the production change. The rejected runtime candidate is preserved as `report/CANDIDATE_GATES_FAIL.patch` and in the isolated `CandidateClone`; applying it would retain known failures. No commit was made.

## Reproduction and candidate

BEFORE male RH deuce walking-left: **105.208 mm** at frame **129**, **23.782%** of ARM vertices inside TRUNK, dominant bone **LeftUpperArm**. Female RH deuce: **78.701 mm** at frame **143**. Exact front/left stills are saved even though those odd frames are between the regular 30 fps image samples.

The Serve-derived hold target and inherited elbow pole do not fit the Walk pose; the IK pulls the upper arm through the trunk. Match forces serveYaw to zero, so an extra serveYaw rotation is not the cause, and walking right also penetrates. The game asks for the target before the driver updates the visual yaw/root, adding a one-frame mismatch.

The candidate samples the Walk hand, places the ball outside and in front of the thigh, guards the target with torso/thigh capsules, and chooses an outward elbow pole. It blends back in 0.25 s and changes only the Match carry branch. All eight player walking cases reach 0 mm / 0% penetration, but the complete acceptance gates remain FAIL.

## Binary gates

| Gate | Result | Actual result |
|---|---|---|
| G1 NO_ARM_IN_BODY | FAIL | Player walking: 0 mm / 0% in 8/8. Player planting: up to 30.215 mm; complete player/opponent transitions: 128.704 mm, 30.287% max inside share. |
| G2 BALL_IN_HAND | FAIL | Player walking maximum 4.208 cm; unchanged free bounce reaches 74.673 cm. Some opponent/reset frames also exceed this, and ball centre can be inside the body/hand mesh. Limit: 3.5 cm, zero inside frames. |
| G3 BALL_VISIBLE | FAIL | Per-run walking percentages below. Player game view can be below 95%; front view is below 100%. |
| G4 FULL_ARM | FAIL | Same-frame BEFORE/AFTER limb lengths differ at most 0.001 mm. Walking elbow range and belt height fail; lateral and exact mesh clearance are tabulated below. No bone scaling occurs. |
| G5 SMOOTH | FAIL | Worst measured non-fixture hand step 15.581 cm and speed change 18.381 m/s/frame. Limits: 3 cm and 0.6. Carry-to-hold duration is 0.250 s. |
| G6 NO_REGRESSION | FAIL | Stationary control and subsequent player serve positions: 0.000 cm difference; arm angle numerical roundoff at most 0.00000342 deg. Walking-right continuity/visibility or ball clearance worsens in some cases. |
| G7 MATRIX | FAIL | 16 requested player/opponent cases recorded BEFORE and AFTER. No case passes all G1–G6. Current Match driver always solves Left arm; left-handed player visuals are not mirrored. Opponent requested LH remains actual RH in ConfigureMatch. |
| G8 GAME_PATH | FAIL | Visible Editor Play capture attempted through the real A/D input path, but native UI control could not activate reliably. Captured keyboard runs contain no walking input, so they cannot establish this gate. |
| G9 EYE | FAIL | Eight paired films and eight paired contact sheets delivered. Adnan eye approval has not been supplied. |

## Per-run G1 and visibility

G1 covers the input walking/turning/planting sequence, including the planted bounce. Opponent rows cover the real OpponentServe flow before release, excluding its separate stationary control segment and the explicit fixture-placement frames 0 and 300. Walking is |speed| > 0.2 m/s with PrepareAmount <= 0.001. The opponent speed is in the server’s local frame; its two fixture segments move to the legal serve spot from each side.

| Case | BEFORE left mm @ frame / bone | AFTER walking mm / max inside % | AFTER G1 mm @ frame / max inside % | Game visible % | Front visible % |
|---|---|---|---|---|---|
| female-lh-ad | 78.604 @ 48 / LeftUpperArm | 0.000 / 0.000 | 5.300 @ 547 / 1.053 | 90.940 | 98.993 |
| female-lh-deuce | 78.701 @ 143 / LeftUpperArm | 0.000 / 0.000 | 5.300 @ 547 / 1.053 | 94.633 | 97.458 |
| female-rh-ad | 78.604 @ 48 / LeftUpperArm | 0.000 / 0.000 | 5.300 @ 547 / 1.053 | 93.960 | 98.993 |
| female-rh-deuce | 78.701 @ 143 / LeftUpperArm | 0.000 / 0.000 | 5.300 @ 547 / 1.053 | 96.328 | 97.458 |
| male-lh-ad | 104.100 @ 59 / LeftUpperArm | 0.000 / 0.000 | 30.215 @ 547 / 7.065 | 68.121 | 96.980 |
| male-lh-deuce | 105.208 @ 129 / LeftUpperArm | 0.000 / 0.000 | 30.213 @ 547 / 4.407 | 84.746 | 97.175 |
| male-rh-ad | 104.100 @ 59 / LeftUpperArm | 0.000 / 0.000 | 30.215 @ 547 / 7.065 | 90.604 | 96.980 |
| male-rh-deuce | 105.208 @ 129 / LeftUpperArm | 0.000 / 0.000 | 30.213 @ 547 / 4.407 | 92.938 | 97.175 |
| opponent-female-lh-ad | 92.806 @ 325 / LeftLowerArm | 91.473 / 19.872 | 91.473 @ 308 / 19.872 | 100.000 | 100.000 |
| opponent-female-lh-deuce | 92.806 @ 325 / LeftLowerArm | 91.455 / 19.872 | 91.455 @ 308 / 19.872 | 100.000 | 100.000 |
| opponent-female-rh-ad | 92.806 @ 325 / LeftLowerArm | 91.473 / 19.872 | 91.473 @ 308 / 19.872 | 100.000 | 100.000 |
| opponent-female-rh-deuce | 92.806 @ 325 / LeftLowerArm | 91.455 / 19.872 | 91.455 @ 308 / 19.872 | 98.718 | 100.000 |
| opponent-male-lh-ad | 139.344 @ 310 / LeftUpperArm | 128.704 / 30.287 | 128.704 @ 307 / 30.287 | 100.000 | 100.000 |
| opponent-male-lh-deuce | 139.304 @ 310 / LeftUpperArm | 128.604 / 29.401 | 128.604 @ 307 / 29.401 | 97.297 | 100.000 |
| opponent-male-rh-ad | 139.344 @ 310 / LeftUpperArm | 128.704 / 30.287 | 128.704 @ 307 / 30.287 | 100.000 | 100.000 |
| opponent-male-rh-deuce | 139.304 @ 310 / LeftUpperArm | 128.604 / 29.401 | 128.604 @ 307 / 29.401 | 95.946 | 100.000 |

## Per-run hand, full-arm and smoothness

G2 maxima below use the complete pre-toss trace, including reset transients. The independently useful player walking/planting bounce maximum is 74.673 cm; the larger complete-trace figures include stale ball positions immediately after Refeed. These transients are visible in the CSV and are not presented as carry-target defects. G5 excludes frames 0/1 after each explicit opponent fixture placement (0, 300, 600), because a fixture teleport and its acceleration derivative are not a hand-motion test.

| Case | G2 pre-toss max cm / inside frames | Walk elbow min–max deg | Hip lateral min–max cm | Mesh clearance min cm | Wrist above hips max cm | Step cm / speed change m/s |
|---|---|---|---|---|---|---|
| female-lh-ad | 336.493 / 14 | 23.179–60.831 | 0.884–30.088 | 19.288 | 10.747 | 9.223 / 2.772 |
| female-lh-deuce | 369.754 / 13 | 22.760–60.831 | 0.735–29.251 | 19.283 | 13.401 | 9.223 / 2.697 |
| female-rh-ad | 248.664 / 15 | 23.179–60.831 | 0.884–30.088 | 19.288 | 10.747 | 9.223 / 2.772 |
| female-rh-deuce | 315.285 / 13 | 22.760–60.831 | 0.735–29.251 | 19.283 | 13.401 | 9.223 / 2.697 |
| male-lh-ad | 323.487 / 18 | 22.833–61.986 | 0.786–35.976 | 17.837 | 6.105 | 10.897 / 3.302 |
| male-lh-deuce | 314.675 / 13 | 22.380–61.986 | 0.629–35.082 | 17.868 | 8.818 | 10.897 / 3.192 |
| male-rh-ad | 237.622 / 17 | 22.833–61.986 | 0.786–35.976 | 17.837 | 6.105 | 10.897 / 3.302 |
| male-rh-deuce | 233.072 / 14 | 22.380–61.986 | 0.629–35.082 | 17.868 | 8.818 | 10.897 / 3.192 |
| opponent-female-lh-ad | 291.475 / 21 | 7.557–91.939 | 0.752–29.613 | 4.766 | 35.408 | 13.879 / 17.726 |
| opponent-female-lh-deuce | 461.034 / 21 | 7.557–91.939 | 0.751–29.613 | 4.773 | 35.404 | 13.879 / 17.726 |
| opponent-female-rh-ad | 291.475 / 21 | 7.557–91.939 | 0.752–29.613 | 4.766 | 35.408 | 13.879 / 17.726 |
| opponent-female-rh-deuce | 461.034 / 21 | 7.557–91.939 | 0.751–29.613 | 4.773 | 35.404 | 13.879 / 17.726 |
| opponent-male-lh-ad | 286.026 / 15 | 7.204–92.424 | 1.061–35.505 | 2.884 | 39.067 | 15.581 / 18.381 |
| opponent-male-lh-deuce | 462.193 / 16 | 7.204–92.342 | 1.036–35.510 | 3.012 | 39.020 | 15.557 / 18.381 |
| opponent-male-rh-ad | 286.026 / 15 | 7.204–92.424 | 1.061–35.505 | 2.884 | 39.067 | 15.581 / 18.381 |
| opponent-male-rh-deuce | 462.193 / 16 | 7.204–92.342 | 1.036–35.510 | 3.012 | 39.020 | 15.557 / 18.381 |

## G6 control evidence

The player controls contain plain hold, two bounces, wind-up, toss, trophy and contact. The opponent control segment starts at frame 600 at the legal service mark, then lets its real routine complete. Every matching control frame is compared, rather than selecting only six favorable stills. Player post-walk serve segment frames 552–767 is also compared. Phase transitions, release and contact in these identical trajectories occur on the same frames.

| Case | Control frames | Palm / ball / strings delta cm | Arm delta deg | Subsequent player serve delta cm | Walking right no worse |
|---|---|---|---|---|---|
| female-lh-ad | 432 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| female-lh-deuce | 432 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| female-rh-ad | 432 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| female-rh-deuce | 432 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| male-lh-ad | 432 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| male-lh-deuce | 432 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| male-rh-ad | 432 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| male-rh-deuce | 432 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| opponent-female-lh-ad | 300 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| opponent-female-lh-deuce | 300 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| opponent-female-rh-ad | 300 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| opponent-female-rh-deuce | 300 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| opponent-male-lh-ad | 300 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| opponent-male-lh-deuce | 300 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| opponent-male-rh-ad | 300 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |
| opponent-male-rh-deuce | 300 | 0.000 / 0.000 / 0.000 | 0.00000342 | 0.000 | FAIL |

## Constraint requiring a decision

G2 literally requires the ball to remain within 3.5 cm on every pre-toss frame, while the prompt also requires preserving the bouncing ritual and the BEFORE palm/ball path within 1 cm. The BEFORE free bounce separates ball and palm by about 74 cm. Keeping both ball and palm within 1 cm of those positions cannot reduce that separation to 3.5 cm. The earlier clarification request about applying G2 only to held/caught frames remains unanswered; the gate has not been silently narrowed. Other candidate failures remain independent of this conflict.

## Method and scope

Unity 6000.3.24f1, real Tennis.unity scene, campaign match, actual MatchHeroLook body, real TennisGame.Step/serve routine. Player input uses only ServeNudge. NativeControlled prevents the keyboard auto-toss in scripted runs; AutoPlay and ManualSimulation are false. Both halves and sex/hand settings are recorded in input.json. Opponent uses its production UpdateOpponent path without simulated player nudge.

Each rendered frame is measured at a 60 Hz capture clock. The actual SkinnedMeshRenderer is baked into world space. ARM uses summed bone weights > 0.5 to Left upper/lower arm, hand and fingers; TRUNK uses hips/spine/chest/upper chest and both thighs. Trunk triangles require three trunk vertices. Coincident bind vertices are welded to 1 micrometre, and partition boundary loops are capped for parity containment. Three oblique rays vote inside; depth is nearest ORIGINAL trunk triangle, excluding caps. The male split closes three loops from 248 boundary edges, with zero unresolved/nonmanifold edges. This is a bone-region mesh measurement, not garment occlusion or a capsule substitute.

Visibility is a ray against the full baked body plus game-camera frustum test, starting outside the 10 cm ball radius. Ball-centre containment uses the full body mesh; ball mesh overlap volume and cloth/racket occlusion are not measured. Camera views are fixed in the actor frame during turns. Game camera includes HUD. PNG every second frame is encoded at 30 fps; numeric trace remains 60 fps.

BEFORE and candidate assets are frozen in separate APFS clones so concurrent project work cannot change the comparison. source-audit.json confirms identical Serve FBXs, TennisGame, TennisRules, TennisActor, TennisServeRoutine and QualitySettings between both clones and production. A recursive binary comparison of all clone Assets reports only HeroTennisDriver.cs differing; all ProjectSettings match. Production HeroTennisDriver.cs still matches this task’s initial backup.

## Exact film and sheet paths

- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/male-game-before-after.mp4`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/male-game-comparison-sheet.jpg`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/male-front-before-after.mp4`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/male-front-comparison-sheet.jpg`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/male-left-before-after.mp4`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/male-left-comparison-sheet.jpg`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/male-top-before-after.mp4`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/male-top-comparison-sheet.jpg`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/female-game-before-after.mp4`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/female-game-comparison-sheet.jpg`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/female-front-before-after.mp4`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/female-front-comparison-sheet.jpg`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/female-left-before-after.mp4`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/female-left-comparison-sheet.jpg`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/female-top-before-after.mp4`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/film/female-top-comparison-sheet.jpg`

Raw per-run views and 12-frame sheets: `before/<case>/` and `after/<case>/`, with `game.mp4`, `front.mp4`, `left.mp4`, `top.mp4`, and `worst-<view>-sheet.jpg`. Every run also has trace.csv, input.json, completed.json, summary.json and measurement.txt.

## Changed files and rollback

- New `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Editor/ServeWalkFilm.cs` and its `.meta`. Rollback absence markers: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/rollback/Unity/Assets/Editor/ServeWalkFilm.cs.ABSENT` and `.meta.ABSENT`.
- Rejected candidate only: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/CandidateClone/Assets/Scripts/Tennis/HeroTennisDriver.cs`. Original backup: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/rollback/Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs`. Review patch: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/report/CANDIDATE_GATES_FAIL.patch`.
- Backups also preserve original TennisActor.cs and TennisServeRoutine.cs; neither was edited. Tool iterations and analysis-script revisions are in rollback/. No FBX, mesh, rig, socket, golf code, timing, URP or quality setting was edited by this task.
- Only this task’s editor source/meta, text report, review patch and proof scripts are staged. Existing unrelated dirty/staged work is preserved. No commit.

## Remaining work

Correct the carry transition to meet continuity/visibility/full-arm limits, support the real opponent movement path, mirror left-handed Match visuals within the allowed scope, resolve the bounce/G2 contract, and complete a successful keyboard-driven Editor proof. The candidate should remain unapplied until these measurements pass, then Adnan can judge the paired film.
