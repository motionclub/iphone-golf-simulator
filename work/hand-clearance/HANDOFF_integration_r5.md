# Hand clearance: hand-off to integration (chat 3, 2026-10-18 20:15)

Integration re-bakes the clearance tracks on the combined clone, and those are the tracks that ship. These are the code changes that combined bake needs.

## 1. Files (all in this working tree; staging state as of this note)
Round 2/3 code, already staged:
- `Unity/Assets/Scripts/Tennis/HeroClearance.cs`, `HeroClearanceProxy.cs`, `HeroClearanceTracks.cs` (+ `.meta`): the solver, the proxy, and track playback.
  - Tracks are HCT2: a locked-hand slip channel.
  - Locked hands are re-locked with the game's elbow side.
  - The swivel clamp is continuous (80 deg).
  - Coverage is measured, and a fully covered clip skips the residual solve.
- `Unity/Assets/Scripts/Tennis/HeroPoseSafety.cs`: the pass the game calls.
  - Plays the tracks via `UseGraph`, times the whole pass in `LastMs`, and has `ClampSwivel` / `Solve(…, hinge)`.
  - **Not staged yet:** a 2-line `Disabled` static (diagnostic A/B only).
- `HeroTennisDriver.cs`, `GolferView.cs`, `HubHeroAnimator.cs`: one `UseGraph` line each.
- `Unity/Assets/Editor/HeroClearanceBake.cs`: lobby bake at 120 Hz + adaptive keys.
- `Unity/Assets/Editor/AnimationSafetyAudit.cs`, `AnimationSafetyAuditLegacy.cs`, `AnimationSafetyAuditSweep.cs`: the bake and the gate sweep.
- `Unity/Assets/Tests/EditMode/HeroClearanceTests.cs`.
- `Unity/Assets/Resources/HeroClearance/Tracks_*.bytes` (+ `.meta`): the round 3 tracks, which integration's bake replaces.

**New since round 3, NOT staged yet** (the first-drive "body angled weird" fix and tooling):
- `Unity/Assets/Editor/AnimationSafetyAuditSweep.cs`:
  - **BodyStep is now truth-gated.** A chest turn or knee swivel is kept only if the real-mesh worst depth drops by >= 2 mm; otherwise the pose is restored exactly. The cost per degree is 10x higher (2e-4 chest, 5e-5 knee). Without this, golf tracks turned the male upper chest about 6.6 deg at address, which was Adnan's bug.
  - **`SWEEP_BAKE_ONLY=<ctx,...>`:** bake only those contexts and play the installed tracks for the rest, in one launch.
- `Unity/Assets/Editor/HeroClearanceFilm.cs`: `HeroClearanceFilm.GolfFirstShot` (the first-tee-shot repro; `FILM_BODY=male|female`, `FILM_TRACKS=0`, `FILM_CLEARANCE=0`). Note: `FILM_BODY` writes the shared Editor PlayerPrefs `golfer.look.v1`. Save it and restore it after, as `work/hand-clearance/tools/proof_run.sh` shows.
- `Unity/Assets/Scripts/Tennis/HeroPoseSafety.cs`: `public static bool Disabled` (used only by that repro).

## 2. Install and bake (on the combined clone, after chat 4's strokes and the new garments are in)
1. Copy the files above into the clone.
2. Bake and gate in one launch, through heavy.sh, muted:
```
SWEEP_TRACKS=bake SWEEP_TRACKS_FRESH=1 SWEEP_TRACK_HZ=30 SWEEP_ROUNDS=2 SWEEP_BAKE_DIAG=0 \
SWEEP_BEFORE=1 SWEEP_RENDER=1 SWEEP_WORST=6 SWEEP_FREE=1 SWEEP_BAKE=1 SWEEP_HZ=60 \
SWEEP_CONTEXTS=tennis_male,tennis_female,golf_male,golf_female SWEEP_OUT=<dir> \
Unity -batchmode -projectPath <clone> -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep
```
   This writes `Assets/Resources/HeroClearance/Tracks_<Male|Female>_<Tennis|Golf>.bytes` in the clone; copy all four, plus any new `.meta`, to the repo. `SWEEP_BAKE=1` runs the lobby BAKE check at the end (`<dir>/bake/bake-check.json`).
3. Gate numbers: `python3 work/hand-clearance/tools/summarize.py <dir> <proofdir> --label integration` and `tools/sheet.py` for the worst-20 sheet.
4. Lobby: re-export with `HeroClearanceBake.Corrected(root, clip, SamplePose)` (120 Hz + adaptive keys), after the tracks are in.

## 3. Gate thresholds (unchanged)
- **BODY / CLOTH:** frames with a hand, forearm or prop > 3 mm into the full body / under a garment's outer wall (real meshes).
- **CONTACT:** racket or club head drift at contact <= 10 mm, contact time unchanged (round 3: 0.32 mm).
- **NO_POP:** elbow/shoulder speed <= max(2x the clip's own peak, 60 deg/s); flips = elbow hinge > 90 deg from RAW while bent > 20 deg.
- **COST:** <= 0.3 ms per hero, the whole pass (`HeroPoseSafety.LastMs`), live rally at 1080p (round 3: 0.066 / 0.049 ms; golf 0.055).
- **BAKE:** lobby clip vs game within 2 mm between keys (round 3: <= 1.41 mm).
- **Posture check (new, from the first-drive bug):** male golf first tee shot, UpperChest yaw relative to the root at address within ~2 deg of clearance-off (`GolfFirstShot`, compare `pose.csv` with `FILM_CLEARANCE=0`). Round 3 failed this at 6.6 deg.

## 4. What chat 3 still runs
One small validation launch only, on its own clone: re-bake the 5 male golf swings with the truth-gated body step (`SWEEP_BAKE_ONLY=golf_male`, clips `golf:Drive,Chip,IronSwing,HalfSwing,Putt`), then the male first tee shot. This checks that the fix compiles and removes the 6.6 deg chest turn before you depend on it. The full 4-context r5all was cancelled, so the Unity slot is yours.
