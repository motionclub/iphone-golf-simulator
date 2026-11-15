# Loading screen: full-screen random action (2026-11-13)

Adnan: remove the "Swing your phone. Play on your TV." caption and add action shots, then "full screen action, but the tennis shot is bad because
of how disfigured the animation is ... we need to cycle completely random shots, not just the same few", then "Build it".

Mockups: https://claude.ai/artifact/SWufBhNHovAbacK3Drqojd (`loading-action.html`, pool in `img/pool`, `pool.json`).

## In the app (uncommitted)
- `GolfArcade/Unity/HubControllerView.swift`: `HubLoadingScreen` (the TV boot screen; the no-TV phone shows it scaled) is a
  full-screen shot under a navy shade from the left and bottom, the wordmark, the shot's SPORT · VENUE in gold, and LOADING with the bar.
  The caption and the swing arc are gone. `LoadingShots` holds the pool and `Reel` (a fresh shuffle each boot; every shot once
  before a repeat; never the same twice in a row; a boot never opens on the shot the last boot ended on, `UserDefaults` `loading.lastShot`).
  `LoadingShotImage` fills 1280×720 and uses each shot's `anchor` (which part of a wider-than-16:9 picture shows) so the player
  sits right of the wordmark, with a 3.4 s push-in. A new shot every 3 s; Reduce Motion shows one random still.
- `GolfArcade/Assets.xcassets/LoadingShots/loadshot-00…34` (about 4.1 MB): 26 trailer frames (Sky Tower tennis, Magma Open golf,
  Neon bowling; letterbox cropped) and 9 in-game captures (Tropical Resort and Magma Crater tennis; Club, Magma and Tiki bowling, scoreboard cropped).
  The tennis dive and every frame of it are left out (its body warps); shots with motion-smeared arms, cut-off heads or a bent hand too.
- `GolfArcadeTests/HubSessionTests.swift`: `testLoadingShotsShuffleThroughTheWholePool`, `testLoadingShotSnapshots` (shots 3, 12, 20, 28, 33 at 68 %).

## Gaps
- Golf has one venue (Magma Open): the Cliffside / Wild Isles captures all carry the aim HUD. A clean film of them would add shots.
- Removing the dive move from the game is its own task (session "Remove the warped tennis dive move").

Run: `work/loading-action-1113/native_tests.sh` (own simulator `loading-action-snap`; snapshots to `snap/`).
