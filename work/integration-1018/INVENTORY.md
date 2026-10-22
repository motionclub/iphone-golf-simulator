# Integration 10-18: inventory and dry-run (chat 12)

Brief: `work/delegation-2026-10-17/12_integration_and_test.md`. Integration clone: `~/integration-UnityClone`, an APFS copy of the working
tree `Unity/` taken 10-18 16:01 (it includes the staged and unstaged work of every chat as of then, plus this chat's away/recording edits).
Baseline for the test comparison: `~/integration-UnityClone2`, the same snapshot with none of the pending installs.

## Already in the working tree (so already in the clone)
| Piece | State in `Unity/` | Check |
|---|---|---|
| 60 fps (frame-rate-60b) | staged: golfer_{m,f} 60 fps, 12 emote FBX headers, FrameProbe, SignatureShot, TennisQuality.StepDown 1080p floor; 10-16 MatchHeroes/HeroMoves re-bakes **unstaged** | in clone |
| Rendered skies (rendered-backgrounds) | staged; 6 hook files | `patch_shared.py` on a copy: "already patched" × 6 |
| Tennis anim integrity (driver/inertia/grip) | staged `.cs` | the clips/prefab times are the pending part (below) |
| Hand clearance round 3 (bake-first) | staged: HeroClearance*, HeroPoseSafety, tracks `Resources/HeroClearance/*.bytes`, UseGraph lines | tracks baked on the strokes as they were before chat 4's install → re-bake tennis after it |
| Male garments + shoes (round 6) | `male_prefabs_r6_p0.patch` applied, **unstaged**; meshes staged | round 8 still running in its own chat → second pass |
| Female face/shader, male face/shader | staged | |
| Male caps re-hug | staged | lobby maps pending (lobby step) |
| Majestic layer (6 places) | installed, untracked | `INSTALLED.sha1` 12/12 OK |
| Weather dormant files | installed, untracked | `INSTALLED.sha1` 11/11 OK; shared patch not applied (`check`: 8 × False) |

## Pending installs (dry-run against the clone)
| Order | Piece | Command | Dry-run |
|---|---|---|---|
| 1 | Tennis clips + prefab contact times | `tools/tennis_install.sh install <clone>` (= chat 4's `install_for_chat6.sh`, backups under `backup/`) | ran in the clone: 14 strokes × 2 at 60 Hz, ArmCorrected + ReadyIdle60, 6 slot times per prefab moved (prefab diff = 7 timing lines, garments untouched); its test patch has the wrong path depth: applied by hand with `-p1` |
| 2 | Female tennis top + skirt (K12_FT) | `GP_CLONE=<clone> GP_OUT_DIR=work/integration-1018/garments_out garment_install_batch MatchHero_Female:K12_FT:work/clothing-v2/out_gp` | needs the HeroShoulderDeformation `[gp]` early return (REQUESTS 10-17 20:25), applied in the clone (whole tank path: weight rewrite + ShoulderCloth corrective live in `BindTankToTorso`) |
| 3 | Lobby clips get the clearance correction | one line in `MatchHeroLockerExport` (`HeroClearanceBake.Corrected`, REQUESTS chat 3) | clone only |
| 4 | Hand-clearance re-bake (tennis) | `work/hand-clearance/tools/full_bake.sh` contexts tennis_male/female with `CLONE=<clone>` | clips changed in step 1 |
| 5 | Character LOD | `work/character-lod/install/install.sh install <clone>` then cache re-bake (`run_probe.sh`, `CLOD_STEPS=bake` + tennis probe) | new files only |
| 6 | Majestic all maps (16 holes) + landmark kit | `work/majestic-all-maps/tools/install_majestic.sh install <clone>` | dry-run: 9 scripts, 5 shaders, 34 kit FBX + impostors, 1 editor file added; 5 files backed up + patched/replaced (MajesticLook, MajesticVenue, GolfCoastalInstances, Resort BotanicalKit/CoastalBotany FBX) |
| 7 | Weather shared patch | `python3 -I work/majestic-weather/tools/patch_shared.py apply <clone>` | `check`: not applied yet (8 files) |

Not integrated: VFX + sound research (on hold, Adnan).

## Overlaps
- `Tennis/Customization/PlayerMale.prefab`, `PlayerFemale.prefab`: male garments r6 patch (renderers) + chat 4 slot times (step 1). Checked: step 1 changes only timing lines.
- Female `Kit_*` mesh assets (`Characters/KitsV2/MatchHero_Female/`): garment pipeline patches them in place (step 2); character LOD caches them (step 5, so after 2); hand clearance proxies read them (step 4, after 2).
- `Scripts/Majestic/MajesticLook.cs`, `MajesticVenue.cs`: chat 9's files, patched by chat 10 (step 6); weather reads them (step 7 after 6).
- World shaders: weather adds `MAJESTIC_WEATHER_ON` + include to 11 shaders; nobody else edits them in this round.
- `DreamEnvironment.cs`: rendered-backgrounds hook (in tree) is what Majestic and weather attach to.
- `MatchHeroLockerExport.cs`: chat 1's `forehand` RigClips line (in tree) + step 3.
- `HeroTennisDriver.cs`: chat 4 edits + chat 3's UseGraph line, both in tree.
- This chat's away edits: `TennisGame.Versus.cs`, `TennisGame.cs` (opponent gates), `TennisHud.cs`, `NetworkGolfRound.cs`, `SportsMultiplayer.cs`, `SportsSessionRecorder.mm` (+ Swift app files) — no other chat edits these this round.
