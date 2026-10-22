# Emote overhaul - Spike / Scuba / Thrust (2026-10-05)

Adnan's three complaints about the taunts (Spike used two arms, Scuba was not the dance, Thrust was not a Waluigi-style thrust) were researched (`REFERENCE_STUDY.md`, `pose_preview.html`, `check_poses.js`) and the three clips were re-keyed for both match heroes.  His answers to the open questions: Scuba - drop the racket and pick it up again; Thrust - the racket stays in the right hand; Spike - one big slam plus one smaller, racket kept; clips not capped in length; crossed forearms; facing the net.

## What is installed (all byte-identical to what was tested in an APFS clone of the Unity project)
* 6 FBX + their .meta (only `lastFrame` changed): `Unity/Assets/Characters/MatchHeroes/{Male,Female}/{Male,Female}_Emote_{Scuba,Thrust,Spike}.fbx`.  Lengths: Spike 3.2 s, Thrust 3.5 s, Scuba 4.7 s (were 2.0 s).  Prefabs, slots and the other 3 intro clips are untouched.
* `TennisGame.cs`: `HoldNextPoint(seconds)` + `ApplyTauntHold()` (+2 lines in `AwardPoint` / `BeginPoint`).  `HeroTennisDriver.cs`: ONE line in `PlayEmote`.  Reason: the game's timers run at `GameSpeed` = 1.2x real time and the serve timer after a won game is 2.4 game seconds = exactly the old 2.0 s clips; longer taunts would have been cut by the next serve.  A taunt now holds the serve for (clip length + 0.4 s) x GameSpeed; the timer only ever grows; match results, live points and plain points are untouched.
* `Unity/Assets/Editor/EmoteHoldCheck.cs`: editor tool that plays each taunt through the real `AwardPoint` flow (`proof/hold/`).
* `INSTALLED_SHA256SUMS.txt` lists every installed file.

## What the clips do
* **Spike**: set, racket overhead and dropped behind the head, one-arm chop that drives the racket head into the court beside the right foot (trunk folded ~60 deg), rebound, smaller second lift and second chop, stand up with a head shake.  The free (left) hand only hangs / clenches.
* **Scuba**: racket dropped at the start (lands, bounces once, lies on the court), left thumb+index pinch the nose, right arm held out and the hand sweeps side to side like a fish on the 163 BPM beat (4 sweeps = 22 frames each) while the knees open and close; then both hands drop, the hero squats, picks the racket up (left hand on the knee) and stands up in READY.
* **Thrust**: wide bowlegged stance, hips go BACK then drive 0.36 / 0.40 / 0.42 m FORWARD three times; on the same frame the forearms cross in front of the body (racket in the right hand across the left side), head thrown back, third hit held with a head / shoulder shake; then a strut with the fists on the hips.

## Why the arms do not go through the body now
The IK knows nothing about the body.  `scripts/emo_clear.py` adds a body-clearance pass: the dressed hero's skin, shirt and shorts are posed with the game's own skinning, the clothes are modelled as an outward offset of the skin (they are thick double shells whose inner / outer faces fool a normal test), and a damped Gauss-Newton step moves each arm's wrist (grip) target and elbow swing out of anything it would penetrate.  Per-frame candidate fixes are joined into ONE smooth path per arm by dynamic programming (no pops), READY at both ends is left exactly READY, a hand that must be on a contact (the nose pad, the grasp on the racket) is pinned.  Independent check (`scripts/collide3.py`, Blender-evaluated skin, every frame): the deepest forearm / hand / racket vertex behind the body skin is <= 12 mm in every frame (the READY pose itself has 18.0 mm at the right forearm, so the first / last 0.25 s may reach 20 mm).

## Rebuild / measure
`scripts/run_all2.sh` = solve the 3 clips x 2 heroes -> bake -> export the FBX (`work/emotes/export/fbx`) -> re-import and trace -> penetration run -> all gates (about 9 minutes, needs Blender).  Unity side (in an APFS clone only): `scripts/unity_run2.sh GolfArcade.EditorTools.EmoteWire.Run <log>` / `EmoteFilm.Run` / `EmoteHoldCheck.Run`, `scripts/make_film2.py` for the videos.  `GATE_DEFS_preregistered.md` + `GATE_RESULTS.md` hold the gate definitions (with three disclosed amendments) and the 82 / 82 results.

## Rollback
1. FBX + metas: copy `rollback/fbx/*.fbx` and `rollback/unity_meta/*.meta` back to `Unity/Assets/Characters/MatchHeroes/<Sex>/` (SHA256SUMS lists the old hashes); also copy `rollback/fbx/*` to `work/emotes/export/fbx/` and `rollback/data/*` to `work/emotes/data/` if the old build is wanted for EmoteWire again.
2. C#: `python3 work/emote-overhaul/scripts/unpatch_cs.py Unity` removes exactly the lines added (tested: the result equals the files saved before the job, `rollback/code/*.before`); delete `Unity/Assets/Editor/EmoteHoldCheck.cs(.meta)`.

## Known limits / notes
* The clothes are not tested by a second independent method (the numeric check is against the skin; the solver models the clothes as an offset).  Look at the films in `film/` when judging cloth against the forearms.
* The pelvic-thrust gesture is cartoon-level and clothed, but it is a suggestive gesture: worth a look for the App Store age-rating questionnaire (Adnan has not answered this question yet).
* `TennisTutorialTests.KitColoursParseFromTheLaunchMessage` fails in the Unity EditMode suite (232 / 233 pass); it fails identically without this job's C# changes (checked), it is about kit colours.
* The game camera sees the hero from behind-right, so the Thrust is mostly seen from behind: the hips-forward / backward motion and the head shake are what read there; the crossed forearms and the racket across the body read from the front and side (the opponent's view).
