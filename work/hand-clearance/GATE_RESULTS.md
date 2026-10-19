# Hand clearance: gate results

## Round 3 fix: "body angled weird" on the first drive (2026-10-18 evening)
Adnan's phone build: the round-3 golf tracks turned the male upper chest about **6.6 deg** open at address. Cause: the bake's body step turned the chest to lower the proxy cost of the two-hand grip overlap, which it cannot clear.
- **Fix (staged):** the body step is kept only when the real meshes get better (deepest point -2 mm), and the cost per degree is 10x higher.
- **Repro:** `HeroClearanceFilm.GolfFirstShot`, male first tee shot, chest yaw at address relative to the root: clearance off 79.5 / round 3 72.9 / **fixed 79.5**. Proof: `proof/round3/golf_first_shot_male_on_vs_off.jpg`.
- **Cost of the fix:** male tennis body+cloth fail frames 262 -> 327 (female unchanged). A looser v2 rule was tried and rejected (369).
- **New guard:** tracks carry their clip's fingerprint (HCT3); the EditMode test `InstalledTracksMatchTheClipsTheyWereBakedFrom` fails on stale tracks.
- **Integration:** re-bakes all four contexts on the combined clone with these files; those tracks ship.

## Round 3 (2026-10-18 afternoon), current
Changes since round 2 (`README.md`, "Round 3"):
- **Grip parting:** in a locked two-hand grip, the hands part by up to 1 cm, never at the contact instant.
- **Hand offsets in the track:** locked hands keep their baked offset and nothing else, between keys too.
- **Elbow side:** every IK keeps the game's elbow side, and a continuous 80 deg swivel clamp replaces the flip switch.
- **Residual skip:** pure baked clips skip the residual solve, so they're a function of time alone.
- **Lobby keys:** 120 Hz plus adaptive keys.

**Same measurement as round 2:**
- Real meshes; 138 clip runs, 17,454 frames at 60 Hz.
- BEFORE = the 10-15 solver.
- Numbers: `proof/round3/round3-summary.json`, `round3-clips.csv`, `round3-locked.csv`.

| Gate | Result | 10-15 solver -> round 2 -> **round 3** |
|---|---|---|
| **BODY** (0 frames > 3 mm into the body) | **FAIL** | 3,378 -> 1,186 -> **526**. With free hands: 100 -> 126. Golf male 556 -> **98**, golf female 408 -> **184** (grip parting). |
| **CLOTH** (0 frames > 3 mm under a garment's outer wall) | **FAIL** | 6,496 -> 1,268 -> **800**. With free hands: 176 -> 209. Golf male 513 -> **170**, golf female 492 -> **325**. |
| **CONTACT** (<= 1 cm at contact, time unchanged) | **PASS** | max **0.32 mm** over 34 contact clips. The grip parting and hand offsets fade to 0 between 0.10 and 0.04 s from the contact instant. |
| **NO_POP** (no speed above max(2x clip peak, 60 deg/s); no flips) | **FAIL** | pops 547 -> 309 -> **247** frames (21 clips; **0** of them near-still clips). Flips 0 (round 1) -> 66 -> **14** (male ForehandShort 6, a few at female two-hand contact). |
| **COST** (<= 0.3 ms per hero) | **PASS** | Live AI rally, 1920x1080, **whole pass (track + residual)**: player **0.066 ms** (p95 0.11), opponent **0.049 ms** (p95 0.08). Golf: **0.055 ms**. Note: the round 2 film timed only the residual solve, not the track, so its 0.17 / 0.13 ms figures were incomplete. All sweep frames: mean 0.033, p95 0.068 ms. Not measured on a device. |
| **BAKE** (lobby = game within 2 mm, 3 clips) | **PASS** | At keys: <= 0.001 mm. **Between keys: <= 1.41 mm** (Ready 0.006 / 0.012, IntroWave 1.38 / 0.97, EmoteSlump 1.16 / 1.41 mm, male / female) against the game's pass at the in-between times. The lobby keys are 120 Hz plus adaptive keys (11–16 k keys per clip). `proof/round3/bake-check.json`. |
| **NEW_GARMENT** | not re-run | As round 2: the proxy refits itself; a new garment needs a re-bake for truth-checked tracks. |
| **VISUAL** | done | `proof/round3/worst_before_after.jpg`: **16 of the 20 worst frames go from 40 mm to clear** (one ends at 2.3 mm, under the 3 mm line). The 4 left are tennis contact windows (SliceApproach x2, VolleyBackhand, BackhandWide) plus golf Drive (9 mm). |
| Tests | **15/15 pass** | `proof/edit-tests.xml` |

| context | frames | BODY (10-15 -> r3) | CLOTH | pops | flips |
|---|---|---|---|---|---|
| tennis male | 4,884 | 1,048 -> **125** | 1,533 -> **145** | 46 | 8 |
| tennis female | 4,884 | 671 -> **119** | 2,091 -> **160** | 97 | 6 |
| golf male | 3,843 | 1,044 -> **98** | 1,589 -> **170** | 30 | 0 |
| golf female | 3,843 | 615 -> **184** | 1,283 -> **325** | 74 | 0 |

**What is left:**
- **Tennis contact windows** (most tennis BODY): the hand or racket against the thigh, chest or neck within +-0.1 s of the hit (SliceApproach, VolleyBackhand, BackhandWide, Return, ForehandShort). The rule keeps the racket fixed there, and the body step (chest turn, knee swivel) clears only part of it. The rest needs the stroke clips changed.
- **Golf female grip + swing forearms:** golf female keeps 184 BODY and 325 CLOTH frames. The grip overlap is mostly beyond what a 1 cm part per hand can clear; also the forearm against the shirt.
- **Free-hand residue rose a little** (BODY 100 -> 126, CLOTH 176 -> 209). Pure baked clips no longer run the residual solve, which used to clean up a few proxy-visible frames. That trade buys the time-only result (BAKE pass, lower cost).
- **Clips are not rewritten:** the corrections ship as per-clip tracks (`Resources/HeroClearance`, 134 tracks, about 520 KB), not as 60 Hz clip copies. The coordinator asked for 60 Hz clips through the import path, but those copies would be about 3 MB of `.anim` each, about 300 MB in total. The lobby gets baked clips through `HeroClearanceBake.Corrected`.

---

## Round 2, bake-first (2026-10-18 morning)
Design: `README.md`, section "Bake-first". Every clip, hero and kit is solved **offline** and stored as a correction track (`Unity/Assets/Resources/HeroClearance/Tracks_*.bytes`: 134 tracks, 520 KB in total). The game applies the track from its playable graph, with locked hands held where the game put them, then runs a cheap residual solve.

**Measurement:**
- Truth = the real baked meshes, as in round 1.
- BEFORE = the 10-15 solver.
- AFTER = track + residual, exactly as the game runs it.
- Every clip of every context: 4 contexts + the plaza set on both kits, **138 clip runs, 17,454 frames at 60 Hz**.
- Numbers: `proof/bake-first/bakefirst-summary.json`; per clip `bakefirst-clips.csv`; locked frames `bakefirst-locked.csv`.

| Gate | Result | Numbers (10-15 solver -> round 1 -> **bake-first**) |
|---|---|---|
| **BODY**: 0 frames > 3 mm into the full body | **FAIL** | 3,378 -> 1,658 -> **1,186** frames. **With free hands: 100.** The rest are locked-hand frames: 1,234 frames fail while locked, out of 2,176 locked frames. Golf: the two-hand grip itself, left hand inside the right wrist, 548 + 240 frames, median 11 mm (see below). Tennis: contact windows, racket or hand against the thigh in SliceApproach, VolleyBackhand and Backhand. |
| **CLOTH**: 0 frames > 3 mm under a garment's outer wall | **FAIL** | 6,506 -> 4,815 -> **1,268** frames. **With free hands: 176.** Golf: the right forearm under the left glove, the same grip overlap (459 + 405 frames). Tennis female: forearms under the tank top, median 8 mm. In a two-hand grip the other hand's glove now counts as intended contact (hand on hand), like the other hand's skin. |
| **CONTACT**: racket/club within 1 cm at contact, time unchanged | **PASS** | max **0.27 mm** over 34 contact clips. A hand the caller locks is put back exactly where the game's pose has it after the track. That holds between track keys too: without it the 30 Hz track moved a locked racket up to 556 mm between keys. That was found and fixed in this round. |
| **NO_POP**: no elbow/shoulder speed above max(2x clip peak, **60 deg/s**); no flips | **FAIL** | The 60 deg/s floor is the coordinator's rule (10-18), so near-still clips are judged fairly. **309 pop frames in 31 clips** (round 1: 547 in 40). **66 flip frames** (round 1: 0): two-hand backhands, 2–12 frames per clip at contact. |
| **NEW_GARMENT** | not re-run | The proxy still refits itself from any garment with no tuning (round 1 test passes). A new garment needs a re-bake (`tools/full_bake.sh`) to get the truth-checked tracks. Until then the residual solver alone covers it. |
| **COST**: <= 0.3 ms per hero | **PASS** | Live AI rally + 3 emotes, Tennis scene at **1920x1080** (Editor, Mono, Apple M5): **player 0.17 ms** mean (p95 0.27), **opponent 0.13 ms** (p95 0.20). Golf tee shot: **0.13 ms** (p95 0.15). Round 1: 0.83 / 0.54 ms. All sweep frames: mean 0.14, p95 0.24 ms. Device estimate: about the same or lower (IL2CPP ~2x faster than Editor Mono; an A17/A18 core ~0.75x an M5 core). **Not measured on a device.** `proof/bake-first/film/*-cost.json`. |
| **BAKE**: baked = runtime within 2 mm on 3 clips | **FAIL (between frames)** | At every 60 Hz frame: **0.000–0.001 mm** (Ready, IntroWave, EmoteSlump, both heroes). Between frames against a 120 Hz runtime: Ready 0.02 / 9.5 mm, IntroWave 32 / 30 mm, Slump 237 / 100 mm. The gap is at the elbow probe. Likely cause: the residual solver and the "no elbow flip" guard switch differently at 120 Hz than at 60 Hz. The lobby plays the 60 Hz keys, so between keys it can differ from the game. `proof/bake-first/film/bake-check.json`. |
| **VISUAL** | done | `proof/bake-first/worst_before_after.jpg`: the 20 worst frames over all heroes and kits, old solver vs bake-first at 1920x1080. **16 of 20 go from 40 mm to clear.** The 4 left are contact moments. Films (game camera, 1080p): `proof/bake-first/film/tennis-film-overview.jpg`, `tennis-film-emotes.jpg`, `golf-film.jpg`. |
| Tests | **15/15 pass** | `HeroClearanceTests` 7/7 (new: the track round trip + playback by the graph's weights), `AnimationSafetyTests` 4/4, `FemaleDeformationTests` 4/4. `proof/edit-tests.xml`. |

### Per context (10-15 solver -> bake-first, fail frames > 3 mm)
| context | frames | BODY | CLOTH | pops | flips |
|---|---|---|---|---|---|
| tennis male | 4,884 | 1,048 -> **111** | 1,542 -> **102** | 79 | 28 |
| tennis female | 4,884 | 671 -> **111** | 2,092 -> **161** | 95 | 30 |
| golf male | 3,843 | 1,044 -> **556** | 1,589 -> **513** | 43 | 3 |
| golf female | 3,843 | 615 -> **408** | 1,283 -> **492** | 92 | 5 |

### What is left, and whose it is
- **Golf two-hand grip** (most of what is left): the left hand sits inside the right wrist/forearm through every club swing. Male: 548 frames, median 11 mm. Female: 240. `GolferView` locks both hands for the whole swing, so this is the grip pose's job (`HeroGripPolish.ApplyGolfGrip` / the golf clips): about 12–15 mm more spacing along the shaft. Request filed in `work/delegation-2026-10-17/REQUESTS.md`.
- **Tennis contact windows:** racket or hand against the thigh at the hit (SliceApproach, VolleyBackhand, BackhandWide, Return), and the right hand in the left forearm in the two-hand backhand grip. The body step (chest turn, knee swivel) clears some of it; the rest needs the source strokes changed.
- **Flips at two-hand backhand contact (66 frames) and between-key lobby differences:** the next solver work. Make the elbow-side guard continuous (no hard switch), and bake the lobby keys at the game's rate with the residual included.

### How the bake works (offline, `AnimationSafetyAudit.Sweep`, `SWEEP_TRACKS=bake`)
1. **Pass 1:** the full solver plays the clip forward.
   - Where a locked hand or the held prop is still inside, the **body step** turns the chest (up to 12/8/8 deg) and swivels the knees (up to 25 deg), with hands and feet held exactly.
   - The **truth push** measures the real meshes and moves a free hand or forearm out along the surface normal. A forearm hit is scaled by its lever; a two-hand grip moves as one.
2. **Two smoothing rounds:** each smooths the correction (zero phase; round the seam for looping clips; 0.2–0.6 s for near-still clips), applies it again (locked hands exact, feet planted, elbow never on the other side), then runs the residual solve and the truth push.
3. **Track:** the final local-rotation delta at 30 Hz, for the bones that moved.

---

## Round 1 (2026-10-17), history

Brief: `work/delegation-2026-10-17/03_hand_arm_clearance.md`. Design, commands, ownership: `README.md`.

**Measurements** are taken on the **real baked meshes**, not on the solver's proxy:
- the full body, including the skin hidden under V2 garments;
- each garment's outer wall;
- the held racket or club.

**Compared solvers:**
- BEFORE = the 2026-10-15 `HeroPoseSafety` (kept unchanged as `Editor/AnimationSafetyAuditLegacy.cs`);
- AFTER = the new `HeroClearance`;
- RAW = the clip with no clearance (the NO_POP reference).

**Sweep:** every clip of every context (tennis male/female in the tennis kit, golf male/female in the golf kit, and the empty-handed plaza set on both kits), 60 Hz, **138 clip runs, 16,800 frames**. Numbers: `proof/final-summary.json`, per clip `proof/final-clips.csv`, locked-contact frames `proof/final-locked.csv`.

| Gate | Result | Numbers |
|---|---|---|
| **BODY**: 0 frames with hand / forearm / prop > 3 mm into the full body | **FAIL** | 3,446 → **1,658** frames (−52%). In frames where the hands may move: 2,480 → **371** (−85%). The rest (1,287) are frames where the wrists are **locked**: tennis contact windows and the whole golf swing (see "What is left"). |
| **CLOTH**: 0 frames > 3 mm under a garment's outer wall | **FAIL** | 8,188 → **4,815** frames (−41%); free frames 6,547 → 3,056. Left: forearms under the shirt hem in emotes (Defeat, Victory, Shock), hands under the female skirts in Slump, locked strokes. |
| **CONTACT**: racket/club position at contact within 1 cm, contact time unchanged | **PASS** | max drift **0.001 mm** over 34 contact clips. The wrists are locked at contact by design, so time is unchanged. EditMode `FemaleDeformationTests.BackhandAndServeContactTransformsStayExact` and `HeroClearanceTests.LockedHandsAtContactDoNotMove` pass. |
| **NO_POP**: no elbow/shoulder angular-velocity spike > 2× the clip's own peak introduced by the solver; no elbow flips | **FAIL** (flips **PASS**) | elbow flips **0** (was 90 in an earlier build; the IK now takes the bend side from the joint's hinge). Spikes: 547 frames in 40 clips. Five are near-still clips (Ready, Idle: clip peak < 30°/s, so any correction change exceeds 2×). The large ones are Slump and Walk onsets when a deep correction appears or switches. Rate caps fixed the pops but let hands sink (tested twice, rejected). |
| **NEW_GARMENT**: Kit_Top pushed out 1 cm, no code or number changes | **FAIL** (as worded); adapts | the proxy grows with the garment automatically (EditMode `ABiggerShirtGrowsTheTorsoProxyWithNoTuning`: median +6–14 mm where the shirt is; the bare-body table unchanged). Sweep with the grown top (30 Hz): body fail rate 9.9% → 10.2% (unchanged), cloth 28.7% → 35.0%. CLOTH does not pass for the normal kit either, so it cannot "still pass". |
| **COST**: runtime pass ≤ 0.3 ms per hero | **FAIL** | live AI rally + 3 emotes in the Tennis scene at 1920×1080 (Editor, Mono, Apple M5, final code): **player 0.83 ms mean** (p50 0.68, p95 1.88), **opponent 0.54 ms** (p50 0.43, p95 1.21). These are per rendered frame: the driver skips the clearance on the 120 Hz physics substeps (the film saved an image every second frame, 873 images over 1,746 frames). Both heroes together take ≈ 1.4 ms of the 8 ms main-thread budget in `work/frame-rate-60b/BUDGET.md`: it fits 60 fps, but it is not 0.3. Device estimate: IL2CPP is roughly 2× faster than Editor Mono on this kind of math and an A17/A18 core is ~0.75× an M5 core, so ≈ 0.4–0.6 ms per hero on the phone. **Not measured on a device.** Where the time goes: translate 0.66 ms (≈ 22 proxy evaluations and ≈ 530 table lookups per solve); the swivel takes 0.12 ms. Halving the pair rebuilds (8.6 → 4.8 per solve) did not lower the time. Golf (live tee shot, Golf scene, 1080p): **golfer 0.22 ms mean** (p95 0.28), which is within the gate. `proof/film/tennis-cost.json`, `proof/film/golf-cost.json`. |
| **BAKE**: baked clip = runtime within 2 mm on 3 sample clips | **FAIL** | at every 60 Hz frame (what the game plays), final code: **0.000–0.001 mm** on Ready, IntroWave and EmoteSlump for the female hero and on Ready and IntroWave for the male; **male EmoteSlump 33.8 mm** at the last frame (t = 2.567 s): the runtime run ends on a different tracker branch. Between frames (the lobby interpolates its keys): 7.6–198 mm against a 120 Hz runtime pass, because the tracker is path-dependent where a correction switches sides (Slump, Wave). `proof/film/bake-check.json`. |
| **VISUAL** | done | `proof/worst20_before_after.jpg` (1920×1080 renders, centre crops): 14 of the 20 worst frames go from 40 mm to clear. Films (1920×1080, the game camera): `proof/film/tennis-film-overview.jpg` (AI rally + Defeat/Shock/FistPump), `proof/film/tennis-film-emotes.jpg` (emotes cropped round the player), `proof/film/golf-film.jpg` (live tee box in rain at night: address and waggle with the club in both hands; the swing itself is covered by the sweep). |

## Late changes (after the 60 Hz sweep above)
Three changes, measured on subsets rather than a new full 60 Hz sweep, because machine time was short after the 20:55 out-of-memory stop:
1. **Clavicle step, locked arms only:** the shoulder joint moves up to 4.5 cm; the wrist stays exactly where it is.
2. **Elbow-swivel rate cap = 150°/s + 2× the arm's own angular speed in the clip** (was a flat 150°/s).
3. **One pairing per solve that covers the look-ahead.**

Effect of 1 + 2 (30 Hz, golf swings):
- female HalfSwing body fail rate .82 → .70; Drive .29 → .25; Chip .95 → .85.
- male Drive .60 → .45; IronSwing .46 → .39.
- female tennis Ready cloth .36 → .21.

`MaxSwivel` 100° was tried and rejected: it caused 31 elbow flips on HalfSwing.

Tennis male subset at 60 Hz, final vs late (`proof/late-tennis-subset-*.csv`):
- body fail frames: Backhand 50 → 46, Forehand 22 → 19, ForehandShort 11 → 9;
- cloth fail frames: Backhand 48 → 29, ForehandShort 38 → 28, Slump 48 → 43;
- the looser swivel cap gives a new NO_POP spike on Walk: left shoulder 293°/s against a clip peak of 81°/s (ratio 1.86 → 3.61).

The old solver is still better on two female golf swings: Chip (.46) and IronSwing (.08).

## What is left, and whose it is
- **Locked contact (tennis strokes), source clips, chat 4:** the right hand or racket goes into the left thigh at the hit (BackhandWide, Return, SliceApproach, VolleyBackhand, SplitToBackhand), the racket into the neck on the male Backhand follow-through, and the hand/racket into the chest in ForehandShort. The solver may not move the racket inside the contact window. Frame list: `proof/final-locked.csv`. Request: `work/delegation-2026-10-17/REQUESTS.md`.
- **Golf swings, source clips / golf grip (chat 1, chat 4's `HeroGripPolish`):** in the two-hand grip the left forearm sits up to 40 mm inside the right forearm through the whole swing. The interlocking hands are treated as intended contact; the forearms are not.
- **Emote forearms under the shirt hem** (Defeat, Victory, JumpJoy, Shock) and **female hands under the skirt in Slump:** solver residuals. A two-hand Ready hold also moves both hands up to 14 cm forward on the female hero to get the forearm out of the tank top (visible, but no clipping).

## How each gate is measured
- **BODY:** hand and finger skin points (one per 8 mm, rest pose), forearm points (one per 10 mm) and about 300 racket/club points. Each point's nearest full-body triangle comes from a per-frame grid, with the point's own arm excluded; in a two-hand grip the other hand is excluded too (intended). A point is inside when it lies behind the triangle's geometric face normal (oriented by its vertex normals) and not past an edge. Depth is reported up to 40 mm.
- **CLOTH:** a point is under a garment when the garment's outer wall lies between the point and the outside: a 40 mm ray from the point along the skin's outward normal (at the nearest body point) hits the outer wall. The own sleeve or glove is excluded. This holds up for pleats and flared skirts, where a nearest-face sign gave false 35 mm readings.
- **Intended contact:** the second hand on a racket or club (two-hand grip, a cradle at the throat or head) touches the prop and the other hand by design.
- **Locked:** the frame's smaller hand travel is < 5%. Wrists are locked as `HeroTennisDriver.PostProcess` passes them (strokes only, eased in by ±0.12–0.28 s around contact) and as `GolferView` passes them (club swings).
- **Pipeline = the game's:** tennis driver tweaks (open-forehand swivel, serve wrist), golf swing clearance + grip + hand separation, grip polish, and every garment corrective. Sampled through a playable graph per clip; the solver settles on frame 0.
- **NO_POP:** local-rotation angular velocity of the upper arm (shoulder) and forearm (elbow), AFTER vs the RAW clip's peak. A flip is the elbow hinge turning > 90° from RAW while bent > 20°.

## Tests (EditMode, clone)
**14/14 pass** with the final code (clone, 2026-10-17 21:11): `HeroClearanceTests` 6/6 (proxy fitted for both heroes, buried hands come out at 60 Hz with lengths kept for both heroes, locked contacts do not move, a bigger shirt grows the proxy with no tuning), `AnimationSafetyTests` 4/4, `FemaleDeformationTests` 4/4. `proof/edit-tests.xml`.
