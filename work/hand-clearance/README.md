# Hand clearance (chat 3, 2026-10-17)

Hands, forearms and the held racket/club stay out of the body and the clothes, in every clip, on every hero, for any garment, with no per-clip or per-garment numbers. Brief: `work/delegation-2026-10-17/03_hand_arm_clearance.md`. Gates: `GATE_RESULTS.md`.

## How it works
1. **Proxy, fitted automatically** (`Unity/Assets/Scripts/Tennis/HeroClearanceProxy.cs`). One "radial capsule" per deforming bone (pelvis, spine, chest, upper chest, neck, head, clavicles, upper arms, forearms, hands, every finger phalanx, thighs, shins, feet). The proxy is a core segment along the bone with hemispherical caps, plus a table of surface distances along straight rays from that core. Rows run along the bone and over the caps; columns go round the bone in the cross-section's own ellipse. The table is measured by casting the rays against the rest-pose triangles skinned to that bone. Two tables: `Rb` (bare full body, including skin hidden under V2 garments, read from `kitV2CoverSource`) and `R` (the farthest surface of body + every worn `Kit_*` / `Acc_*` renderer, i.e. the outside of the clothes). **Garment offsets = R − Rb, measured from the garment meshes themselves**, so a new or bigger garment changes the proxy with no number to tune. ArmBlend_* twist helpers are folded into their two limb bones. In the game the fit runs on a worker thread (about 2 s, no main-thread hitch). Fitted tables are cached per body+garment mesh set.
2. **Solver** (`HeroClearance.cs`), after the animation and before the garment correctives, every frame:
   - grip translation: each hand (or a two-hand grip with its racket/club, as one group) moves by the smallest offset that takes the hand, the prop and the wrist half of the forearm outside `R` + 4 mm. Iterative push first, then a straight-line search over a few directions if the pushes fight (thigh vs hip). The target is kept on the arm's reach sphere, so a straight arm swings out instead of losing the push. Two-bone IK keeps segment lengths and the elbow side, and the hand keeps its world rotation, so fingers and grip are unchanged. How far each hand may travel comes from the caller: 0 at racket/club contact, so contact position and time can't change.
   - elbow swivel about the shoulder–wrist line (wrist fixed, elbow angle fixed, so no flip) for the forearm and outer upper arm. The upper arm is tested against the bare body only, so sleeve and shirt may touch.
   - prop turn about the wrist for a single-hand racket still inside, and a second hand sliding along the handle when two hands overlap.
   - corrections appear when needed and fade out (0.14 s / 0.18 s), and the swivel prefers last frame's angle.
3. **Callers**: `HeroPoseSafety` (same public API as before, now an adapter) is already called by `HeroTennisDriver` (tennis) and `GolferView` (golf). Plaza: one line in `Hub/HubHeroAnimator.cs`.
4. **Offline bake** for the SceneKit lobby: `Editor/HeroClearanceBake.cs` runs the same Solve frame by frame at 60 Hz and writes every moved transform back as keys. Chat 6 uses `clip = HeroClearanceBake.Corrected(root, clip, SamplePose);` in `MatchHeroLockerExport`.
5. **Sweep / audit**: `Editor/AnimationSafetyAuditSweep.cs` (`AnimationSafetyAudit.Sweep`) poses every clip × hero × kit at 60 Hz three times (RAW / BEFORE = `AnimationSafetyAuditLegacy.cs`, the 10-15 solver / AFTER = this one) through the game's own pipeline. BEFORE and AFTER are measured on the **real baked meshes**:
   - BODY: hand / finger / forearm skin points and the held prop inside the full body, own arm excluded.
   - CLOTH: the same points behind a garment's outer wall, with the own sleeve or glove excluded.
   - Per clip: contact drift, elbow/shoulder angular-velocity spikes and elbow flips against RAW, and solver cost. It also renders the worst frames before and after at 1920×1080.

## Bake-first (2026-10-18)
Every authored clip is known ahead of time, so the expensive, high-quality work runs **offline** and the game only plays the result:
1. **Offline bake** (`AnimationSafetyAudit.Sweep` with `SWEEP_TRACKS=bake`), per clip x hero x kit, through the game's own pose pipeline:
   - pass 1: the full solver plays the clip forward (with its look-ahead). Where a **locked** hand or the held prop is still inside (tennis contact, golf swing), the **body step** moves the body instead: chest turn and knee swivel, with both hands and both feet held exactly. Then the **truth push** measures the real body and garment meshes, which the proxy only approximates (flared hems, skirts), and moves a free hand or forearm that is still inside out along the surface normal. A two-hand grip moves as one. Golf hands may move up to 1 cm away from impact.
   - rounds 2–3: the correction (each bone's local rotation, game pose -> cleared pose) is **smoothed in time** with a zero-phase Gaussian (0.042 s, then smaller), applied again, with locked hands put back exactly, feet kept planted and elbows never on the other side; then the residual solve and the truth push run again. Every push is followed by a smoothing and every smoothing by a push.
   - the result is stored as a **correction track**: for the bones that moved (clavicles, arm chains, chest, legs), the local rotation delta at the bake rate. One file per hero and kit: `Unity/Assets/Resources/HeroClearance/Tracks_<Male|Female>_<Tennis|Golf>.bytes` (a few KB per clip; the clips themselves are untouched).
2. **Runtime** (`HeroClearanceTracks.Player`, called first in `HeroPoseSafety.Apply`): it reads which clips the hero's playable graph plays (weights, times, the tennis upper-body layer mask) and applies their blended tracks. Consumers hand over their graph once: `HeroTennisDriver.Build`, `GolferView.StartGraph`, `HubHeroAnimator`. Then `HeroClearance` runs as a cheap **residual** pass (`Residual`: no look-ahead, tighter pairing) for blends and transitions. A pure clip is already clear, so it exits early.
3. **Lobby**: `HeroClearanceBake.Corrected(root, clip, SamplePose)` now applies the same track (+ residual) and writes keys, so the SceneKit lobby matches the game.
4. **Round 3 (2026-10-18):**
   - **Grip parting:** in a locked two-hand grip (golf swing, two-hand backhand), when one hand lies inside the other arm or under the other glove on the real meshes, both hands part along the contact normal. Each moves at most 1 cm, and not at all at the contact instant.
   - **Hand offsets in the track:** a per-frame offset channel stores where each locked hand is meant to be relative to the game's hand. The game's re-lock keeps those offsets and nothing else, between keys too.
   - **Elbow side:** every IK keeps the elbow on the game's side, and the elbow can swivel at most 80 deg from the game's own elbow plane. It's a continuous clamp, never a switch, so there are no flips.
   - **Residual skip:** a pure baked clip (coverage 1) skips the residual solve. The result is then a function of time alone (cost about 0.02 ms per hero, and the lobby can match it).
   - **Lobby keys:** the lobby bake writes keys at 120 Hz (`HeroClearanceBake.LobbyHz`).
5. Re-bake after any clip, garment or body change: `CTXS="tennis_male tennis_female golf_male golf_female" work/hand-clearance/tools/full_bake.sh` (a copy of the run script). A missing track only means that clip runs the residual solver alone, as before.

## Run
```
work/hand-clearance/tools/sync_to_clone.sh                 # repo -> ~/hand-clearance-work/UnityClone (only this job's files)
SWEEP_OUT=~/hand-clearance-work/sweep/full SWEEP_HZ=60 work/hand-clearance/tools/unity.sh ~/hand-clearance-work/logs/full.log -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep
python3 work/hand-clearance/tools/sheet.py out.jpg ~/hand-clearance-work/sweep/full    # worst-20 before/after sheet
```
Env: `SWEEP_CONTEXTS`, `SWEEP_CLIPS`, `SWEEP_HZ`, `SWEEP_WORST`, `SWEEP_RENDER`, `SWEEP_GROW` (NEW_GARMENT: Kit_Top pushed out), `SWEEP_DIAG` / `SWEEP_TRACE` / `SWEEP_PROXYVIS` (diagnostics), `SWEEP_FREE`. Every run is muted (`GOLF_MUTE=1` + `EditorUtility.audioMasterMute`).
The clone and outputs live in `~/hand-clearance-work`, because `/private/tmp` is wiped on restart.

## Ownership / integration notes
- Mine: the files above, `HeroClearanceTracks.cs`, the track files and `HeroClearanceTests.cs`. Since the bake-first round, I also own one `UseGraph` line each in `HeroTennisDriver.Build`, `GolferView.StartGraph` and `HubHeroAnimator`. Not touched: source clips, garment meshes and bindings, `HeroGripPolish`.
- `work/female-soulful/unity/HeroPoseSafety.cs` is the OLD pre-10-17 solver. If that package is installed later, skip that path.
