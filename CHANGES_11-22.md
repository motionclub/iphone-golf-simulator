# Changes, 11-22 (branch `11/22-combined`)

All the work done on 11-22. Every chat worked in the main folder on top of `main` d5c338d3e (the 11/21 combine, build 0.1.6 (26)), so nothing needed merging: this is that folder's uncommitted work in one commit. The build number was not changed.

| Work | Chat | Details |
|---|---|---|
| Smooth play on a TV (1080p60) + phone frame rate by device | Perf + size audit | `work/perf-size-audit-1122/SMOOTH_CHANGES.md` |
| App size 2.6 GB → about 1.1 GB | Perf + size audit | `work/perf-size-audit-1122/SIZE_CHANGES.md` |
| Tennis setup: point at the TV + fill the circle | Tennis setup | `docs/PLAN_Tennis_PointAndFill_1122.md` |
| Bowling: waiting spots, ball-return pickup, emotes | Bowling expressiveness | `work/bowling/proof/pickup-1122/`, `waitspots-1122/` |
| Daily Hole in One: shots get longer, cup 2.5× | Daily Hole in One | `work/daily-hole-in-one/proof/1122/` |

---

## Smooth play (TV)
- TV is always 1080p at 60 fps. The phone screen follows Settings → Phone frame rate: Auto (120 on ProMotion A17 Pro and newer, else 60), 60 or 120, plus Picture Smooth / Sharp.
- The 120 Hz swing input is now off by default.
- New `Unity/Assets/Scripts/Game/FramePace.cs` (FrameWindow, PacePolicy, PhoneRate) sits behind both frame governors. TV drawables are back to 3. Frame Timing Stats on.
- Bug fixed: `SportsBridge.mm` dropped events over 4096 bytes, so the golf phone map picture never arrived. The cap is now 512 KB.
- New `RenderWarmup.cs`.

## App size
- Rig exporter (`MatchHeroLockerExport.cs`) cuts at 8 mm / 2° and clips with the same id share samples: rig files 846 → 269 MB, re-exported.
- Unity animation compression Optimal 0.1°; build uses LZ4HC; environment textures 6x6.
- KTX textures deduplicated (`tools/dedupe_ktx.py` → `GolfArcade/Unity/CharacterAssets/KtxAliases.json`; the 14 deleted `.ktx` files are now aliases). Re-run the tool after regenerating KTX.
- Locker mesh packed (`tools/pack_club_room.py` → `GolfArcade/Unity/ClubEnvironments/Club_locker.lzfse`).
- `Editor/MeshCompressionRules.cs`: Low mesh compression on scenery only. Never on golf ground, bowling pins/balls, the Majestic kit, characters, or meshes with blend shapes.
- iOS build fix: the game asmdef allows unsafe code (`ShotClips.cs` did not compile for iOS).
- `work/hero-sync/look_sources.txt` no longer lists deleted belt files.

## Tennis: point and fill
- New `GolfArcade/Unity/SportsGlow.swift`: the TV draws a glow wave behind its card; the phone camera finds it and the TV's delay.
- The circle fills in about 2.6 s while every phone sharing the TV is pointed at it, and drains otherwise.
- After the circle, play starts. No flashes, no swing timing drill, no Ready tap; TennisLagLearner refines the timing during play.
- Swift only; Unity untouched.

## Bowling
- Waiting players stand along both lane edges (left, right, left), never all on one side (`BowlingGame.WaitLayouts`, default LaneSide).
- After every ball the bowler walks to the ball return and picks the ball up (`Bowl_PickupLow` + hand IK). The ball rolls out of the hood first. Tap to skip.
- Walks use the tennis run (`HubHeroAnimator.Attach(go, tennisRun:true)`, opt-in, so plaza and menus are unchanged). Players steer around each other.
- Emotes whenever it is not your turn (`BowlingGame.Emotes.cs`, `BowlingController.swift`). Pass-the-phone has no emote UI.

## Daily Hole in One
- Shot 1 is a chip (2–12 yd off the green), shot 2 is 90–110 yd, shot 3 is 150–175 yd (`DailyHoleInOne.Bands`).
- The cup is 2.5× on all three daily shots (`Hole.CupBoost`), 1× everywhere else. Scoring curve unchanged.

---

## Tests (last runs, after the final edits)
- Xcode simulator tests: passed at 19:29 and 19:32 on 11-22 (after the last Swift edit). Known earlier failures: MenuBetaTests (2), testTennisNeedsAnExternalScreen.
- Unity EditMode: bowling 98/98 (19:31), Daily Hole in One 24/24 (19:22). The perf pass ran 800/805; the 5 failures predate it (stale clearance tracks, golf 4-player totals, 3 tennis aim tests).

## Not done
- No device run of any of this.
- No Unity export, Xcode archive or upload.
- Clearance-track fingerprints are stale after the animation compression (re-bake pending).

## Left out on purpose (not 11-22 work, still untracked)
`.claude/launch.json`, `ARCHIVE_VERIFICATION.json`, `ArtDir/style/alive/…` and `ArtDir/style/experience-implementation/proof/` (10-14/15 captures), `UI overhaul.zip`, `changesdonerecently.zip`, `flowglad-briefs-3-4-scripts-v2.txt`.
Clone-only tools stay in `work/`: `work/daily-hole-in-one/tools/CupSizeCapture.cs`.
