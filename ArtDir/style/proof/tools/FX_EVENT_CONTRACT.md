# Existing feedback routes — phase 6

Source inspection, 2026-10-15. Phase 6 changes the existing normal/charged contact core alpha and golf landing palette, and consumes the existing constrained-presentation flag for reduced decorative particle motion. It adds no event subscription, trigger, pool, object, timing change or camera movement. Recipe capture is separate from evidence that gameplay calls it.

| Confirmed event | Existing visual | Existing sound / haptic | Source |
|---|---|---|---|
| Tennis player serve | `TennisFx.Contact` | Hit + native serve feel | `TennisGame.cs` serve-contact resolution |
| Tennis rally hit | `TennisFx.Contact`, perfect/charged branches | Hit + graded rally feel | `TennisGame.cs` contact resolution |
| Network confirmed hit | Contact after accepted remote hit | Hit; local hitter haptic | `TennisGame.Network.cs` |
| Opponent hit | OpponentContact, optional heavy recipe | RivalHit | `TennisGame.cs` opponent contact |
| Net tape collision | NetHit | Net | `TennisGame.cs` collision branch |
| Point result | Existing point/HUD response | Applause or call; point/game/match cue | `TennisGame.cs` AwardPoint |
| Celebration confetti | `Celebrate` pool recipe exists; **no current caller found** | No channel claimed for this unused recipe | `TennisFx.cs` |
| Golf fairway/rough/green/sand landing | Touchdown chosen from confirmed surface lie | Thud; first-down Tick | `GolfGame.cs` landing resolution |
| Ice landing / skid entry | Touchdown ice recipe | IceSkid; first-down Tick | `GolfGame.cs` |
| Water / lava hazard resolution | Splash / LavaBurst | Splash / LavaHiss, gasp, Failure | `GolfGame.cs` hazard resolution |
| Cup | Cup, guarded by cupFeedback | Cup, roar, hole-out/fanfare | `GolfGame.cs` |
| Replay water / lava | Existing replay recipe | Existing replay sound | `GolfGame.cs` replay presentation |

`EnvironmentFxProofTests` directly exercises the nine recipes in fixed views and checks that the ParticleSystem object count remains constant. Its frame logs record active particles, not GPU overdraw or screen coverage. Audio and physical haptics require live-device verification. The three still frames and timestamped clip are recipe evidence, not proof of confirmed network dispatch or performance.

The native `SportsSession.reduceMotion` preference already reaches `PresentationPolicy.Constrained` (also used by Low/thermal presentation). Phase 6 now consumes that flag: multi-particle bursts emit about one third of the particles; explicit tennis decorative velocities scale to .45. Single core cues remain. Loop-based emission thinning preserves every original `UnityEngine.Random` draw, so presentation cannot shift the gameplay random sequence. `EnvironmentReducedFxProofTests` checks that sequence, live particle counts and confetti speed. This does not add weather, camera or timing writers.

The unused celebration recipe remains unbound; activating it would add a new trigger and is not claimed here. Audio, physical haptics, simultaneous-event screen coverage and sustained device cost remain unmeasured. The existing 14/30/45 ms hit holds and disabled live camera punch are unchanged.
