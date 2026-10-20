# HERO_MAINSTAY — the new heroes replace the old ones

2026-10-03. The male and female HeroBase bodies from `work/match-anim-set` are now the only character the game draws: the match (player and rival),
every campaign opponent, the Unity locker view and the phone's locker mirror (`CharacterModelPreview.swift`). They are bald grey mannequins with the
painted face, skin-tinted by the locker / roster, holding the classic racket. The 32 exported FBX clips play, each on its own skeleton.
Gate results: `GATE_RESULTS.md`. Proof: `proof/` (index at the bottom).

## What the game does now

| thing | before | now |
|---|---|---|
| `TennisHeroSetup` | loaded `Tennis/Hero/Hero_01_Tennis`, named it Hero01 for player and rival | loads `TennisCustomization.HeroBase(actor.Female)` = `Resources/Tennis/Customization/PlayerMale` or `PlayerFemale` (new prefabs), names it "Match hero Male/Female (player/rival visual)" |
| player sex | locker | locker (`SelectCharacter(female)`) — unchanged |
| rival sex | `TennisRoster.Female` | `TennisRoster.Female` — unchanged (Milo, Tama, Dex, Bruno, Jax, Viktor male; Suki, Lina, Rosa, Nadia female) |
| body | Hero V4 chibi + HeroKit hair / visor / cap / sweatband + worn kit | `Body_M` (33,196 verts, source SHA d6c4dcfb…) / `Body_F` (23,683 verts, source SHA a1d73a33…) + `Face_M` / `Face_F` (painted, 13 / 14 flat-colour slots) — mesh and skeleton used as exported, nothing edited |
| racket | the old sculpt | `Racket_Classic` (frame / strings / grip / butt cap) on `Hand_Racket`; the roster / locker racket colour tints the frame only |
| clips | `Hero_*` (humanoid, retargeted) | `Male_*` / `Female_*` FBX, byte-identical copies of `work/match-anim-set/export/fbx/`, played as the transform curves Blender baked on that skeleton (Generic rig, no retargeting). Unity pose vs Blender: max 0.010 mm over 52 bones × 7 clips × 2 sexes (`data/blender_compare_*.json`) |
| skin | HeroKit palette on the atlas | `MatchHeroLook.SetSkin` tints the body material (locker `skinHex`, else the palette index); roster `HeroSkin` index for rivals |
| `TennisCustomization` | loaded `PlayerMale/Female.fbx` (Higgsfield bases) | the same resource names now hold the match-hero prefabs; the old FBXs moved (with their .meta) to `Assets/Characters/Archive/OldPlayerBase/` |
| `CharacterModelPreview.swift` | baked Hero V4 export (HeroMenu / HeroV4 / HeroLounge / HeroSwing_* + atlas, hat and hair parts) | `MatchHero_Male/Female.json + .lzfse` + 12 forehand frames each, exported from the same prefabs by `MatchHeroLockerExport` |

## Swing → clip map (existing game markers only; no new classifier)

The clip is chosen once, when the swing starts (`HeroTennisDriver.ClipFor`), and played contact-locked by the driver's existing `StrokeTime`.

| game state | clip | contact (s, male = female) |
|---|---|---|
| ready, idle, walking, running, between points | ReadyIdle (held, looped) | – |
| normal forehand (Drive / Topspin / Slice / Lob / LowPickup / Dive, forehand side) | Forehand | 0.667 |
| `Stroke.Running` forehand (the actor's own "wide" marker: `TennisRules.StrokeFor`, lateral gap > 1.1 m) | ForehandWide | 0.867 |
| backhand side | Backhand | 0.633 |
| `Stroke.Running` backhand | BackhandWide | 0.767 |
| backhand while the ball in flight is the serve (`Flow == Rally && RallyShots == 1`) | Return | 0.433 |
| serve | Serve (stance → toss arm → trophy read off the clip itself) | 0.900 |
| `Stroke.Volley`, forehand / backhand | VolleyForehand / VolleyBackhand | 0.300 / 0.300 |
| `Stroke.Smash` / overhead | Overhead | 0.733 |

Imported, on the prefab, **not** mapped (the brief says "only if the actor already marks it"; the game has no such marker):
ForehandShort (no short-ball flag), ForehandOpen (no open-stance flag), SliceApproach (the game's Slice is forehand-only and there is no net-approach state),
SplitToForehand / SplitToBackhand (no split step), RecoverCenter (no recover state). Each is one line in `ClipFor` when the game grows the state.

## MISSING (no clip exists; ReadyIdle is held, no old `Hero_*` clip plays)

RunForward, RunRight, RunLeft, Walk, HitPerfect, CelebratePoint, SadPointLost, MatchWin, MatchLose, MissWhiff, the signature intro emote (Idle),
and in the phone locker the seated lounge pose (the club "settings" tile now shows the hero standing in front of the deck chair).
`HeroTennisDriver.MissingFromMatchSet` lists them; a request for one is counted in `MissingReactions` and nothing plays. A miss ("whiff") keeps swinging.
A hero on the move therefore slides in ReadyIdle (the driver re-plants the feet as before); that is the limit of the clip set, not a bug.

## What was found and fixed on the way (driver, `Match` heroes only)

1. **Frozen follow-through while moving.** With no run / walk clip the driver's base layer dropped the run share and then re-normalised the remainder onto
   whichever stroke slot still held weight, so a hero that was moving kept the last follow-through pose (30.2 % of Run / Ready frames had ReadyIdle < 0.9 in the
   first full trace; the pose then popped into the next swing). The share of absent clips now goes to ReadyIdle (5.8 % left = the intended 0.2 s blend-out).
2. **Snap at the end of a stroke.** The upper-body layer weight went to 0 in one frame. It now eases out over 0.16 s, and two strokes in a row cross-fade over 0.09 s.
3. Racket drawn at the game's `HeroRacketScale` (1.3×, the arcade string bed is wider than a real one) — in the match and, since the export, in the locker mirror.

Both changes are inside `if (Match)` branches; the old-look path of the driver is untouched.

## Old look: what still references it

Runtime code (`Assets/Scripts`, `GolfArcade/`): **no live reference** to `Hero_01_Tennis`, `Hero01` or `Resources/Tennis/Opponents`. Remaining strings are comments (`TennisGame.cs` — untouched, ball/scoring file),
the profiler name "Hero01 tennis" in `ModularHeroLook.cs`, and doc comments.

Still on disk, not loaded by the game (left in place as asked):
- `Unity/Assets/Resources/Tennis/Hero/` (Hero_01_Tennis.prefab + kit masks, 316 KB) and `Unity/Assets/Resources/Tennis/Opponents/*.fbx` (11 MB). They sit in `Resources`, so a player build still packs them. Delete in a later pass.
- `GolfArcade/Unity/CharacterAssets/{HeroMenu,HeroV4*,HeroLounge,HeroSwing_*,Player*}` — excluded from the app bundle in `project.yml` (`excludes: Hero*`, `Player*`); not deleted.
- `GolfArcade/Unity/MenuArt/menu-hero-*.png` — 2D illustrated portraits (clothed, with hair) used on the campaign map / story / ladder screens. They are pictures, not Hero01 or Opponents meshes, and were not touched; they no longer look like the in-match heroes. Decision needed (re-render from the new meshes?).
- Editor-only tools that load the old prefab on purpose: `HeroGameplayBuild`, `HeroLockerExport`, `HeroV5Rebind`, `HeroIntegrityAudit`, `HeroV6Polish*`, `MatchHeroAB` (via `LegacyHero01.PrefabPath`), and the PlayMode test `HeroV6RetargetTests` (literal path).
- `Unity/Assets/Scenes/Hero01*.unity` — editor review scenes of the old hero; only `Golf.unity` and `Tennis.unity` are in the build settings.
- `HeroV4` in `CharacterModelPreview.swift` is now only the name tables the menus list (haircuts, headwear, `offered`); it loads and draws nothing.
- Not characters of this job and unchanged: the umpire, the stands / resort crowd and ball kids (`Resources/Tennis/Umpire`, `Crowd`, `StandardCharacters`); none of their assets carries a Hero01 name (audit: no marker among live renderers).
- `[Explicit]` PlayMode audits of the old hero's hair / wardrobe / clips (`HairFitAuditTests`, `Score80HairABTests`, `Score80WardrobeAuditTests`, `Score80ClipProbeTests`, …) read `driver.look`, which is null on the match heroes; they would throw if run by name.

## Things Adnan should know

- In play the heroes read as bare mannequins in the picked skin tone — that is the brief (bald, no kit, no shoes). Hair, headwear, shirt / shorts / shoes colour, height, build and face-shape pickers now change nothing on the 3D meshes (Unity and Swift); the style-card thumbnails for hair and headwear are identical heads. The skin and racket picks work.
- Left-handed setting: as before, the visuals stay right-handed (the actor mirrors the logic, not the model).
- Quick mapping check: the rival bodies for all ten roster keys were verified in Play mode (`proof/audit.txt`, "roster").
- A/B of the same scripted self-play (4 matches of 150 s, same seed; the old Hero01 put back on the actors by hand vs the new heroes; `logs/ab_*.txt`): strings-to-ball gap at the player's contact, mean 0.116 m (old) vs 0.103 m (new); contacts that visibly miss the ball (> 12 cm) 84 / 156 (old) vs 32 / 138 (new); player honest misses 6 vs 7; rival whiffs 23 vs 29; hits in the 600 s 134 vs 113. Ball, scoring and rules code are byte-identical to before; the differences come from the body and clip timings feeding the existing contact planning.
- Locomotion: with ReadyIdle held, a hero on the move slides its feet. In the traced rallies (18,000 player frames) the player moved faster than 1 m/s in 9,006 and the toes dragged over 0.15 m/s in 87 % of those (median 2.8 m/s at a median ground speed of 3.3 m/s); standing, 8 %. A run clip is the fix.
- Swing speeds: the contact lock plays a clip's pre-contact part in whatever time the actor has left, so a late swing is fast; the racket hand covers up to ~0.6 m in one frame at the strike in the traces. That is the existing `StrokeTime` behaviour, not a pop (the pop film `proof/raw/pop_*` shows the frames).

## Checks run

- Swift (iPhone 17 Pro simulator): `MatchHeroLockerTests` 10, `TennisCampaignTests` 31, `SportsIntegrationTests` 24 and the three existing tests adapted to the new mirror — 68 pass. Removed: the old-hero hair / lounge / style proofs in `TennisMenuSnapshotTests` (`testHeroV5*`, `testHairFitAudit`) — they asserted Hero V5 hair nodes.
- Unity PlayMode `MatchHeroClipMapTests` (new): the stroke → clip map and the contact-time table, both sexes — passes.
- Unity PlayMode `NativeLaunchHeroTests` (updated: match heroes survive the phone launch path, body follows locker sex and `TennisRoster.Female` for every key, no old look / cosmetics) — 2 / 2 pass; its lineup now writes to `proof/lineup` instead of `ArtDir/score80/lineup`.
- Unity EditMode: 159 / 160 pass. The one failure, `TennisTutorialTests.KitColoursParseFromTheLaunchMessage`, is in committed code this job did not touch (`TennisLook.Kit.From` always sets `HasSkin`, so `Any` is true for an empty kit).

## Rebuild / re-prove

```
# prefabs from the staged FBXs (hash-guarded, writes logs/build_report.txt)
Unity -batchmode -nographics -quit -projectPath Unity -executeMethod GolfArcade.EditorTools.MatchHeroBuild.Run
# locker assets for the Swift mirror
Unity -batchmode -nographics -quit -projectPath Unity -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.Run
# Play-mode proof (locker, roster, two campaign matches, rally, dive, replay, pop film) -> proof/
MH_PROOF_OUT=$PWD/work/hero-mainstay/proof Unity -batchmode -projectPath Unity -executeMethod GolfArcade.EditorTools.MatchHeroProof.Run
python3 work/hero-mainstay/tools/contact_lands.py && python3 work/hero-mainstay/tools/clip_usage.py && python3 work/hero-mainstay/tools/label_sheets.py
# Swift
xcodegen generate --spec project.yml
xcodebuild test -project GolfArcade.xcodeproj -scheme GolfArcade -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -only-testing:GolfArcadeTests/MatchHeroLockerTests
```

Rollback: `work/hero-mainstay/baseline/` holds the pre-change copies of every file edited (`*.orig`, `SHA256_before.txt`, `git_status_before.txt`, both `.pbxproj`).

## Proof index (`work/hero-mainstay/proof/`)

| file | shows |
|---|---|
| `LOCKER_male.png`, `LOCKER_female.png` | Play mode, game camera moved onto the hero: front 3/4, back 3/4, head — locker look applied as the phone applies it |
| `LOCKER_SWIFT_male.png`, `LOCKER_SWIFT_female.png`, `swift_locker/` | the phone's locker mirror (`CharacterModelPreview`): full body, head, practice swing (match Forehand), club "settings" tile, the real SwiftUI view read back from its SCNView |
| `LOCKER_SCREENS_phone.png`, `LOCKER_SCREENS_tv.png`, `locker_screens/` | the whole locker screens (`ClubCharacterScreen`, `LockerStudio` tabs) with the new mirror |
| `CAMPAIGN_vs_Nadia.png` | campaign match vs Nadia (female rival), player male: wide game camera, rival close-up, player |
| `CAMPAIGN_vs_Viktor.png` | campaign match vs Viktor (male rival), player female |
| `LINEUP_player_and_ten_rivals.png`, `lineup/` | the player and all ten roster rivals in the phone-launch path (NativeLaunchHeroTests) |
| `RALLY_serve_forehand_backhand.png` | one rally (vs Nadia): serve, forehand, backhand at the gameplay contact, clip name + clip time + contact time in the corner |
| `RALLY_vs_*_closeups.png`, `RALLY_vs_*_game_camera.png`, `rally/` | every stroke captured in both rallies (serve, forehand, backhand, return, volleys, overhead, wide strokes), labelled |
| `audit.txt` | what was in the scene / in memory at each stage; slot → FBX asset per hero; roster check; actor renderers; gameplay contact log |
| `contact_lands.txt`, `clip_usage.txt` | contact frame vs clip contact for 156 swings; which clips played |
| `trace.csv` | one row per hero per frame: state, clip, clip time, mixer weights, key points |
| `raw/` | the raw frames, incl. serve ritual (`*_serve_hold_*`, `*_serve_toss_*`), slide, run (`*_run_*`), dive (`*_dive_*`), instant replay (`*_replay_*`), pop film (`pop_NN_*`) |
