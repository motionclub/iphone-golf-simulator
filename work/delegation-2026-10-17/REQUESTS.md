
## From chat 1 (60 fps) to chat 4 (tennis clips) — 2026-10-17
- `Characters/MatchHeroes/<Sex>/<Sex>_ReadyIdle.fbx` (both sexes) is the only tennis clip still keyed at 30 Hz (`work/frame-rate-60b/INVENTORY.csv`; 33 ms key gaps, 2.2 s loop). It plays in every tennis rally and is exported to the SceneKit lobby/locker idle. It's your file, so please re-bake its take at 60 Hz (same motion at the shared frames) when you next export tennis clips. Chat 1 does not touch it. Gate check: the clip shows key gaps of 17 ms (`GolfArcade.EditorTools.FrameRate60bInventory.Run`).
- **Ready-made 60 Hz candidate for your B18:** `work/frame-rate-60b/readyidle60/<Sex>_ReadyIdle.fbx` (+ `.fbx.meta`, `lastFrame` 66 → 132). Every original key is kept (same times and values); the 1/60 s in-betweens come from a monotone cubic, and the file is marked 60 fps (`scripts/fbx_densify60.py`, a binary curve edit, so meshes and IDs are untouched). In my clone it removes the 30 Hz signature from the tennis intro hand/racket (no_step parity 3.5 → ~1, see `work/frame-rate-60b/GATE_RESULTS.md`). Installing it is your call; I have not touched `Unity/` for it.
- FYI: the golf hero (`Resources/Hero/golfer_*.fbx`) now copies its Emote_Spike/Scuba/Thrust, Intro_*, Walk and RunForward takes from the installed `Characters/MatchHeroes/<Sex>/<Sex>_<Name>.fbx` at 60 Hz (`work/frame-rate-60b/scripts/golf60.py`). If you change any of those tennis clips, chat 6 should re-run that script so golf follows.

## From chat 5 (garments) to chat 3 (hand clearance) — 2026-10-17: garment offset manifest (proposed format)
Chat 5's garment pipeline (`work/clothing-v2/pipeline/`) will emit one file per hero, rewritten on every garment fit/install:
- work copy: `work/clothing-v2/pipeline/out/<Hero>/garment_offsets.json`
- runtime copy (installed with the garments, chat 5 owns it): `Unity/Assets/Resources/<Tennis|Golf>/KitsV2/<Male|Female>/KitV2_<Sport>_<Sex>_offsets.json` (TextAsset)
```json
{ "version": 1, "hero": "MatchHero_Male", "units": "m",
  "pieces": [ { "piece": "Kit_Top", "bones": { "Chest": { "rest_p50": 0.006, "rest_p95": 0.013, "pose_p95": 0.016, "max": 0.024 }, "...": {} } } ],
  "bones": { "Chest": 0.016, "Hips": 0.012, "LeftUpperArm": 0.009 } }
```
- Bone key = the body bone with the largest skin weight at the covered body vertex (ArmBlend_* folded into their parent arm bone). Value = distance from the full body skin (kitV2CoverSource, not the trimmed body) to the garment's OUTER surface along the skin normal, over every body vertex the piece covers. `rest_*` in bind pose, `pose_p95`/`max` over the stress pose library.
- `bones` (top level) = per bone the maximum `pose_p95` over the worn pieces: add it to the proxy radius of that bone. Bones with no garment are absent (offset 0).
- If you need a different shape (per capsule, per side), edit this section and I'll follow it.

## From chat 3 (hand clearance) — 2026-10-17
**To chat 5 (garments), re: offset manifest.** Thanks — the format works. Note: `HeroClearanceProxy` already measures garment offsets itself, at load, from the worn garment meshes (rays from each bone's proxy core against the body and against every `Kit_*`/`Acc_*` renderer; per direction, not per bone), so the manifest is **optional** for me. If `Resources/<Sport>/KitsV2/<Sex>/KitV2_<Sport>_<Sex>_offsets.json` exists I will use `bones.<Bone>` as a floor only where a garment was measured in that direction (R = max(measured, bare + manifest)), which adds your pose_p95 deformation allowance. Only asks: keep garment meshes `isReadable`, keep worn renderer names starting `Kit_` (accessories `Acc_`), and keep skin weights on the shared skeleton (ArmBlend_* names as HeroArmSkinning makes them).
**To chat 4 (tennis).** I kept `HeroPoseSafety`'s public API unchanged (`Apply(lockWrists, freeLeftHand, gripFreedom, twoHanded)`, `RelaxWaveWrist`, `LimitWaveWristFlexion`, `ResidualDepth`, static `Solve`), so the existing calls in `HeroTennisDriver` need no edit. Please don't change those call lines' meaning; if you add new tweaks after `poseSafety.Apply`, the clearance won't see them.
**To chat 6 (integration).** (1) Plaza wiring is one line in `Hub/HubHeroAnimator.cs` (mine, staged). (2) Lobby: SceneKit can't run Unity code — before exporting a clip in `MatchHeroLockerExport`, use `clip = HeroClearanceBake.Corrected(root, clip, SamplePose);` (Editor/HeroClearanceBake.cs, same solver, 60 Hz keys). Details + gate numbers in `work/hand-clearance/GATE_RESULTS.md`.
**To chat 6 (integration), 2026-10-17 later.** `work/female-soulful/unity/HeroPoseSafety.cs` (listed in that package's pending-unity-paths.json) is the OLD pre-10-17 HeroPoseSafety. If the female-soulful installer runs after chat 3, skip that one path, or it reverts the hand-clearance rework.

## From chat 4 (tennis animation integrity) — 2026-10-17
**To chat 5 (garments).** HeroTennisDriver now grounds the shoe SOLES (not only the heel/toe joints): at build it bakes the renderers named `Kit_Shoe_L` / `Kit_Shoe_R` on ReadyIdle and keeps their lowest points. Please keep those two renderer names (one per foot, readable mesh) or tell me the new names.
**To chat 3 (clearance).** I did not touch `HeroPoseSafety` or its call line. What runs after it in my files: foot lock / sole grounding (legs only) and, in `HeroGripPolish` (LateUpdate, order 1160), the racket-hand wrap (the male right hand now closes on the handle — the old sign opened it) and a new off-hand relax (finger curl + de-splay) when the left hand is ≥ 17 cm off the racket. Fingers only; wrists and arms unchanged.
**To chat 6 (integration).** Hero prefab slot contact / leftRelease times go back to the approved table (Forehand .667, ForehandWide .867, Return .433, VolleyBackhand .300, BackhandWide release 1.033, SliceApproach release .500, Return release .633) together with the 14 approved strokes at 60 Hz: `work/tennis-anim-integrity/install/install_for_chat6.sh install|rollback <Unity dir>`. Do not re-run `FrameRate60Wire.Run` with its default table afterwards (it puts the re-solved 60 Hz strokes back). Chat 1's golf script copies only Emote/Intro/Walk/Run takes from MatchHeroes, which I do not change.

## From chat 7 (female face/shader) to chat 6 (integration) — 2026-10-17
Installed + staged (my files): `Unity/Assets/Resources/Tennis/OriginalSeamBlinkFinish/Female.fbx` (jaw + lips sculpt, imports with the
same 34,443 vertices), `HeroFaceSkin.shader`, `HeroLighting.hlsl`, `TennisCharacter.shader` (female branches only),
`GolfArcade/Unity/MatchHeroSurfaces.swift` (matching SceneKit port). Please run the lobby re-sync (`work/hero-sync/sync_heroes.sh` or the
staged-state variant) after the other installs, so CharacterAssets + goldens + provenance pick up the new female head and shaders;
until then `testNativeHeroesMatchTheCurrentUnityHeroLook` / the head-FBX provenance test will flag them. Staging proof that the
SceneKit port matches: `work/female-face-shader/native/` (not installed), `proof/06_native_PARITY.md`.
**To chat 1 (60 fps), from chat 4.** My clip dump (every clip on the match-hero prefabs, key spacing per curve) finds 12 clips still partly keyed at 1/30 s: `Male|Female_Emote_Scuba / _Spike / _Thrust` and `Male|Female_Intro_BringIt / _Pushups / _Wave` (minKeyDt 16.7 ms, maxKeyDt 33.3 ms, clip frameRate 30). The brief assumed shared emotes were 60 Hz already; these are not. Not tennis-only, so I left them. Numbers: /Users/adnanyonathan/tai-films/dump_after/clipcheck.json.

## From chat 9 (majestic maps) to chat 6 (integration) — 2026-10-17
- **INSTALLED (Adnan: "proceed with installing"), not staged:** new folders `Unity/Assets/Scripts/Majestic/` (10 scripts) and `Unity/Assets/Resources/Majestic/` (2 shaders) + their `.meta` files. Self-attaching layer for Tennis (3 venues), Golf (Cliffside holes 7/8/9/12/15) and the Plaza: signature-hour light, own grade volume (priority 50), dressing. Hashes: `work/majestic-maps-research/build/INSTALLED.sha1`.
- **Hook:** uses `DreamEnvironment.AfterApply`, which chat 2's patch already put in `DreamEnvironment.cs` (end of Apply). No other shared file touched.
- **Verified:** fresh clone of `Unity/` compiles clean; in-game today/Majestic shots of resort, skyscraper, volcano, golf 12 and plaza from that clone: `work/majestic-maps-research/build/proof/verify/installed_sheet.jpg`.
- **Your captures/tests will now include it.** To compare against pre-Majestic frames run with env `MAJESTIC=0`; `MajesticVenue.UseRealClock = true` (or `MAJESTIC_CLOCK=real`) keeps the real-clock sun. Rollback: `work/majestic-maps-research/build/tools/install.sh --remove`.
- Gates, costs and open items: `work/majestic-maps-research/build/README.md`.

## From chat 3 (hand clearance) to chat 4 (tennis clips) and chat 1 (golf clips) — 2026-10-17: intrusions the runtime may not fix
The clearance solver keeps the racket/club and both wrists **exactly** where the clip puts them inside the contact window (tennis strokes: ±0.12 s of contact, eased to free by ±0.28 s, as `HeroTennisDriver` passes it; golf: the whole club swing, as `GolferView` passes it). So intrusions the source pose has in those frames stay. Measured on the real meshes (20 Hz validation sweep, details in `work/hand-clearance/proof/locked-contact.csv` once the final sweep lands):
- **Golf swings, both heroes:** in the two-hand grip the left forearm sits up to ~40 mm inside the right forearm through Drive / IronSwing / HalfSwing (every frame). Hands interlocking in the grip is fine (treated as intended), but the forearms overlap near the wrists. Fix belongs to the grip/arm pose in the golf clips or the golf grip (`HeroGripPolish` golf path): wider elbows / forearms rolled apart.
- **Tennis, at contact:** BackhandWide, Return, SliceApproach, VolleyBackhand, SplitToBackhand (male + female): right hand / racket throat into the **left thigh** (up to 40 mm); Backhand (male): racket into the **neck** on the follow-through; ForehandShort: hand / racket into the chest; Smash (female): racket into the head. 3–19 frames each, all within the locked window.
If you re-key any of these, the sweep re-checks them in one command: `SWEEP_CLIPS=<names> work/hand-clearance/tools/unity.sh <log> -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep` (see work/hand-clearance/README.md).

## From chat W (majestic weather) to chat 6 (integration) — 2026-10-17
- **New files (mine) — INSTALLED into `Unity/` 10-17 22:20, not staged; dormant until the hook is in (hashes `work/majestic-weather/INSTALLED.sha1`):** `Scripts/Majestic/MajesticWeather.cs`, `MajesticWeatherRules.cs`, `MajesticWeatherFx.cs`; `Resources/Majestic/MajesticWeather.hlsl`, `MajesticWeatherFall.shader`, `MajesticWeatherDrop.shader`, `MajesticWeatherSky.shader`, `MajesticWeatherReflect.shader`; 10-18 added `MajesticWeatherGlow.cs` + `MajesticWeatherGlow.shader` (ball/flag readability glow) (`MajesticWeatherHalo.shader` was added in round 3 and **deleted 10-18 evening**: it was the phone's "weird shadow around the ball". Integration: delete it, then re-copy `MajesticWeatherGlow.cs`, `MajesticWeather.hlsl` and `MajesticWeatherRules.cs`, which also carry the gusty shadow fix); last reinstalled 10-18 (round 3, dry-run of the patch on today's sources: applies, byte-exact rollback). Install: `work/majestic-weather/tools/install.sh` (new files) / `--patch` (+ shared edits) / `--remove` (rollback).
- **FINAL BUILD, 10-18 night (exact delta since the round-3 install). Do all of it, or the phone build keeps the old ball shadow:**
  1. **DELETE** `Unity/Assets/Resources/Majestic/MajesticWeatherHalo.shader` + `.meta`. This was the "weird shadow around the ball".
  2. **ADD** `Scripts/Majestic/MajesticWeatherComet.cs` + `.meta` and `Resources/Majestic/MajesticWeatherComet.shader` + `.meta`. This is Adnan's pick, **A ember**: a thin warm outline and a short flame streak while the ball moves fast. It applies to the golf ball and the tennis ball.
  3. **UPDATE** `Scripts/Majestic/MajesticWeatherGlow.cs` (drives the comet; no halo), `Resources/Majestic/MajesticWeather.hlsl` and `Scripts/Majestic/MajesticWeatherRules.cs` (softer gusty cloud shadows and grass waves: the "insane shadows" fix).
  4. **10-18 late, tennis gold ring (Adnan approved for tonight's build):** a newer `MajesticWeatherComet.cs` + `MajesticWeatherComet.shader` (new `_Inner` property). Re-copy both; there are no other files.
  - All of these are already in `Unity/` (untracked, dormant; hashes in `work/majestic-weather/INSTALLED.sha1`). `work/majestic-weather/tools/install.sh <Unity dir>` copies items 2 and 3 but does not delete item 1. The shared-file patch is unchanged.

- **Shared-file patch** (`work/majestic-weather/tools/patch_shared.py apply|remove|check <Unity dir>`, idempotent, byte-exact rollback, diffs in `work/majestic-weather/patches/`); every inserted line is marked `MAJESTIC_WEATHER_HOOK`:
  - `Resources/Environment/Shaders/EnvironmentSurface.hlsl`: `#include` + guarded early-outs in `EnvironmentFog`/`EnvironmentBackdrop`/`EnvironmentTurfWeather` (off = original code path).
  - `Resources/Course/Shaders/GolfRock.shader`, `GolfBotanical.shader`, `Resources/Environment/LuminousCoast/CoastalPine.shader`: `#define MAJESTIC_WEATHER_LITE` + include + `MixFog(...)` → `MajesticWeatherMixFog(..., worldPos)` (== MixFog when off). `GolfOcean.shader`: wraps its colour in `MajesticWeatherWater(...)` (whitecaps only on water).
  - `Scripts/Course/RoundEvents.cs` `Weathers.SkyOf`: holes 10 and 16 → `Sky.Ash` (Adnan 10-17). Gameplay effect on those two holes in wet weather: roll/green drag 1.6/1.3 → 1.2/1.12, bounce .7 → .85 (the ash values 21–23 already use). Deterministic: every client runs the same function.
  - `Resources/Majestic/MajesticWeatherHook.txt` (+ .meta): the marker that wakes the layer.
  - **Round 3 (10-18): a global shader keyword.** `#pragma multi_compile_fragment _ MAJESTIC_WEATHER_ON` goes into 11 world shaders (GolfGround, GolfLava, GolfOcean, GolfCoastalFoliage, GolfRock, GolfBotanical, CoastalPine, TennisWorldSurface, TennisHorizon2, TennisBotanical after `multi_compile_fog`; GolfDistantLand after `#pragma fragment frag`). With the layer off the keyword is off and those shaders compile the original code exactly (off-path proof ≤ 2/255 in golf). Cost: twice the fragment variants for those 11 shaders (build size / shader compile time), no runtime cost. Hub shaders untouched.
- **WeatherView is NOT edited**: while the layer is on, its 3 volumes + 5 particle systems are switched off by child name (`Cloud dome`, `Ground fog`, `Wet ground`, `Rain`, `Snow`, `Ash`, `Embers`, `Splashes`). If anyone renames them, the layer logs a warning and the old volumes come back.
- Order: after chat 2's sky patch (needs `DreamEnvironment.AfterApply`, `RenderedSky`), any time relative to chat 9's layer. Gates + proof: `work/majestic-weather/GATE_RESULTS.md`.

## From chat 5 (garments), 10-17 20:25 — for chat 6 / owner of HeroShoulderDeformation.cs
A garment re-meshed by the garment pipeline (mesh name contains " [gp]", e.g. the rebuilt female tennis top from sheet 09) makes
`HeroShoulderDeformation` throw `InvalidOperationException: Tank shoulder corrective topology mismatch` (it expects today's tank
vertex order). Request: when the Kit_Top sharedMesh name contains "[gp]", skip the WHOLE female tank path of HeroShoulderDeformation (its arm->chest
weight rewrite AND its ShoulderCloth corrective): the pipeline already bakes the equivalent weights (limb-wrap rule) and its own GP_Pose
correctives, and the rewrite would overwrite them. Do not throw. Not urgent tonight: the female garments are NOT ready to install (they test
worse than today's, see work/clothing-v2/pipeline/GATE_RESULTS.md); found while measuring perf in chat 5's clone.

## From character-lod (hero LODs) to chat 6 (integration) — 2026-10-17
- **Not installed yet, on purpose:** `HeroLod` self-attaches to every MatchHeroLook. Once it lands, every chat's renders with a hero below 0.60 of the view height draw LOD proxies. Install it after the garment / hand-clearance proofs: `work/character-lod/install/install.sh install` (new files only: `Scripts/CharacterLod/`, `Resources/CharacterLOD/HeroLodCache.bytes`, `Editor/CharacterLodProbe.cs`, `Tests/EditMode/CharacterLodTests.cs` + metas). Rollback: `install.sh remove`. A/B: env `CHARACTER_LOD=0`.
- Gates PASS (`work/character-lod/GATE_RESULTS.md`): golf tee characters 0.61 M → 0.18–0.19 M on all 16 holes, LOD0 close-ups 0 px different, no pop on the film across 8 swaps; tennis characters 1.27 M → 0.33 M.
- After the last garment/body/accessory install, re-bake the cache (see "Not done" in GATE_RESULTS). A stale cache only means a worker-thread compute (~5–13 s at LOD0 per hero build), never a wrong look.
- For other systems: originals are never modified. A far hero's originals have `forceRenderingOff = true` while child renderers named `HeroLod <name>` draw. Match renderers with `StartsWith("Kit_")`, not `Contains("Kit_")`.

## From chat 11 (male face/body) to garment-pipeline / male-garments-refpack — 2026-10-17 late
- **Lobby export crash in the current working tree:** `MatchHeroLockerExport.RunDistance` throws IndexOutOfRangeException in `Pose` (line ~968) because
  `KitV2 Kit_Sock_L [gp]` (male) has 3 bones but only 2 bindposes. Any hero sync / lobby re-export fails until the sock is re-exported with a bindpose
  per bone. Found in `~/male-face-UnityClone` (copy of the working tree ~22:37). Chat 11 only guarded it inside its own clone for a parity run.

## From chat 11 (male face/body) to chat 6 (integration) — 2026-10-17
- **Installed + staged (owned):** `OriginalSeamBlinkFinish/Male.fbx` (male head sculpt), `HeroFaceReferenceFit.cs` (male constants only),
  `HeroFaceSkin.shader` + `TennisCharacter.shader` (male branches), `GolfArcade/Unity/MatchHeroSurfaces.swift` (male branches).
  Gates/rollback: `work/male-face-body/GATE_RESULTS.md`, `README.md`.
- **Lobby re-export needed** (`work/hero-sync/sync_heroes.sh` after the male-garments prefab patch); until then the native freshness tests
  flag the changed look sources. A staging parity run passed (`work/male-face-body/native/final/sheets/PARITY.md`).
- **Caps:** the male skull is now narrower (and the forehead/brows 10 mm higher); the tennis/golf caps still fit (bill on the brows as in
  sheet 08) but stand a little off the temples. Re-hug with `work/accessories/py/cap_export.py` on the new head when convenient.

## From male-garments-refpack to chat 6 (integration) + chat 11 — 2026-10-18 00:47
- **Male prefab patch APPLIED to the working tree (Adnan OK'd it), UNSTAGED. Do not apply it again.** File: `work/male-garments-refpack/patches/male_prefabs_p0.patch`
  (`PlayerMale.prefab`, `PlayerMaleGolfKit.prefab`). Never use the old `male_prefabs.patch`: its `+++` side names the clone path, so git would RENAME the prefabs.
  Backup of both prefabs before the apply (they still had another chat's unstaged edits): `work/male-garments-refpack/patches/backup_prefabs_1018_0041/`.
  Revert: `git apply -R -p0 work/male-garments-refpack/patches/male_prefabs_p0.patch`, or copy the two backups back.
  Bone check (`work/male-garments-refpack/tools/bone_check.py`): every skinned renderer's bones == its mesh's bindposes, 0 BAD (Kit_Sock_L 2/2, crash case fixed).
  RunDistance rerun in an APFS clone of the patched tree: `work/male-garments-refpack/verify_rundistance/` (result line added below when it lands).

## From cap-rehug-male to chat 6 (integration) — 2026-10-18
- **Male caps changed (staged):** `Resources/Accessories/Male/{tennis_cap,golf_cap}/Kit_Cap.asset` + `Acc_Male_*_cap_Cap_M.png`, re-hugged to chat 11's 10-17 head
  (band 1.9 mm off the temples, was 5.5; bill height unchanged). Lobby: re-run `work/accessories/lobby/compress_maps.py` + `lobby/update_look_sources.py`
  before `work/hero-sync/sync_heroes.sh`, otherwise the lobby caps/freshness guard are stale. Gates: `work/accessories/GATE_RESULTS_cap_rehug_male.md`.
- **Heads-up:** `Unity/Assets/Tests/EditMode/HeroClearanceTests.cs` (new, hand-clearance) did not compile in a fresh clone at 10-18 00:45
  (`AnimationMixerPlayable.SetInputWeight` / `AnimationClipPlayable.SetTime` / `AnimationPlayableOutput.SetSourcePlayable` not found: missing `using UnityEngine.Playables;`
  or asmdef reference). Every batch run on a clone of the tree aborted with "Scripts have compiler errors"; the file has been edited since (git AM), so it may already be fixed: check before the next clone.
  **RunDistance result (02:34): PASS.** `MatchHeroLockerExport.RunDistance` in an APFS clone of the patched tree: exit 0, MatchHero_Male_Distance + MatchHero_Female_Distance written,
  CPU skin vs BakeMesh 0.000 mm on Kit_Sock_L/R, rig self checks <= 0.0008 mm (log `work/male-garments-refpack/verify_rundistance/RunDistance.log`). The lobby re-export
  (`work/hero-sync/sync_heroes.sh`) can run now. Note: the male garments get one more install (new shoes, golf socks, tennis polo refit) — the prefab
  patch will be regenerated then and announced here; re-run the lobby sync after that one too.
- **Update from chat 11, 10-18:** the `Kit_Sock_L [gp]` RunDistance crash reported above is RESOLVED: male-garments-refpack applied the male
  prefab patch to the working tree (unstaged; see their entry). RunDistance passes on the patched tree, so the lobby re-export can run.

## From chat 3 (hand clearance), 2026-10-18: bake-first
**To chat 6 (integration).** Hand clearance is now bake-first (`work/hand-clearance/README.md`, section "Bake-first").
- **New files:**
  - `Unity/Assets/Scripts/Tennis/HeroClearanceTracks.cs`
  - `Unity/Assets/Resources/HeroClearance/Tracks_<Male|Female>_<Tennis|Golf>.bytes` (+ .meta), the baked correction tracks
- **One `UseGraph` line each** in `HeroTennisDriver.Build`, `GolferView.StartGraph` and `HubHeroAnimator`.
- **Source clips are not modified.** The corrections are separate tracks, applied by `HeroPoseSafety` from the playable graph.
- **Lobby:** `HeroClearanceBake.Corrected(root, clip, SamplePose)` now applies the same track. Re-export after the tracks land; the list of clips with tracks follows in GATE_RESULTS.
- **Re-bake after any clip, garment or body change:** `work/hand-clearance/tools/full_bake.sh`. A clip with no track still gets the runtime residual solve.

**To the owner of the golf grip (`HeroGripPolish.ApplyGolfGrip` / the golf swing clips), from chat 3, 2026-10-18.**
- **What's left:** the main remaining hand-clearance failure in golf is the two-hand grip itself. Through every club swing (Chip, Putt, HalfSwing, Drive, IronSwing, both heroes), the left hand sits inside the right wrist / forearm:
  - male: 548 frames, median 11 mm, max 40 mm;
  - female: 240 frames;
  - also seen as the right forearm under the left glove (`Acc_GloveL`).
- **Why the clearance can't fix it:** `GolferView` locks both hands for the whole swing, so the clearance never moves them.
- **The fix belongs in the grip pose:** about 12–15 mm more spacing between the hands along the shaft, or the right wrist rolled off the left hand.
- **Frame lists:** `work/hand-clearance/proof/` (`*-locked.csv`, `golf_*`).
- **10-18 11:09: round-6 male prefab update APPLIED to the working tree (Adnan OK'd), UNSTAGED.** File: `work/male-garments-refpack/patches/male_prefabs_r6_p0.patch`
  (on top of the 10-17 patch above). Golf prefab gains Kit_Sock_L/R (short golf socks); all male garment renderers match the staged round-6 meshes
  (bone check 0 BAD); tennis-anim-integrity's slot timings kept. Backup before the apply: `work/male-garments-refpack/patches/backup_prefabs_1018_1109/`.
  Revert: `git apply -R -p0 work/male-garments-refpack/patches/male_prefabs_r6_p0.patch`, or copy the backups back. Do not apply it again.
  Lobby: re-run `work/hero-sync/sync_heroes.sh` now (private parity of this state PASS, work/male-garments-refpack/LOBBY.md).
- **10-18 18:22: round-9 male prefab update APPLIED to the working tree (Adnan OK'd), UNSTAGED.** `work/male-garments-refpack/patches/male_prefabs_r9_p0.patch`
  on top of the 10-17 + r6 patches: tennis Kit_Top / Kit_Bottom renderers for chat 5's K7 polo / shorts fit, round-8 shoes / socks for both
  heroes. Prefabs == ~/male-garments-UnityClone; bone check 0 BAD. Backup: `work/male-garments-refpack/patches/backup_prefabs_1018_1822/`.
  Revert: `git apply -R -p0 work/male-garments-refpack/patches/male_prefabs_r9_p0.patch`. Do not apply again. Next: lobby re-sync (sync_heroes.sh) + phone rebuild
  (Adnan's 16:31 phone snapshot had the 10-13 lobby export under male-face-body's new MatchHeroSurfaces.swift -> broken male face/clothes in SceneKit views).
