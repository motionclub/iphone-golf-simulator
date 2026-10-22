# Golf swing speed: the phone paces the golfer's downswing (2026-10-18)

Adnan, after playing the phone build: "Swing needs to be faster and smoother."

## What was wrong (measured in-game, phone motion path, 60 fps)
On the phone, `GolfGame.NativeMotion` feeds 100 Hz phone samples to `MotionSwingDetector`.
- The detector recognises the downswing only once the phone has turned 0.15 rad back from its top, at speed: **0.05–0.10 s after the phone's top**. Only then does `GolferView.Strike()` start the golfer's downswing, and on its own fixed clock (0.25 s).
- The shot is struck when the **phone** crosses the ball (`Strike(atImpact)`). That call **snapped** the club to the impact pose, wherever the clock had got to:
  - For a phone downswing quicker than about 0.3 s, the club jumped forward. A 0.25 s swing went from 80 % down to impact: the club head moved **2.66 m in one frame** (neighbouring frames 0.77 m). A 0.20 s swing moved 3.14 m.
  - For a slower phone downswing, the club reached the ball first, then was sent back to it.
- So the swing trailed the player's hands and then lurched: slow and jerky. All clubs, both heroes (`logs/measure_before.txt`).
- **Not the cause:**
  - **Hand-clearance baked tracks:** a take with them off measures the same.
  - **Clip keys / 60 Hz:** the touch / replay path, which plays the same clips on the clock, has no pops.

## The fix (no clip, rig or track changes)
- `MotionSwingDetector.DownswingProgress`: how far the phone has turned from its top back to the ball, along the swing's own arc (0 at the top, 1 at the ball).
- `GolfGame.NativeMotion` passes each downswing sample to `GolferView.PaceDownswing(progress, sampleTime)`.
- `GolferView`:
  - **Paced downswing:** the club is as far along its own downswing path as the phone is through its turn. `DownArc` measures the clip's club-head path once per clip, so the clip's authored speed profile is kept. The club reaches the ball on the very sample the phone does, which is the shot's impact and the ball's launch.
  - **Even steps, applied in `LateUpdate`:** samples come at 100 Hz into 60 fps frames, so the newest sample is carried on to the frame's moment on the phone's clock. Without this, alternate frames stepped short.
  - **Impact:** the phone's impact never rewinds the club. A club a moment ahead carries on into the follow-through from where it is.
  - **Follow-through:** it leaves the ball at the pace the club actually came down.
  - **Full backswing:** a full phone backswing counts as full even when the pose trails it.
  - **Fallback:** if the phone goes quiet mid-downswing for more than 0.2 s, the old clock carries the swing on.
- **Unchanged:**
  - **Touch, replays, other players and practice swings** stay on the clock (touch: 0.25 s downswing, as accepted 10-12).
  - **The touch "tap" swing** stays exactly as before (see follow-ups).

## Files
| file | what |
|---|---|
| `install.sh` | install = patch the working tree + stage only these edits (index copies patched the same way); `--rollback` = exact reverse; `--check` |
| `scripts/pace_patch.py` | the exact-line patch (`--revert`, `--check`, single-file mode for the index) |
| `src/Tests/EditMode/GolfSwingPaceTests.cs` (+ .meta) | DownswingProgress runs 0→1 without going back, at the ball when struck (driver fast/slow, iron, putter) |
| `scripts/GolfSwingSpeedFilm.cs`, `scripts/GSSPhoneFeed.cs` | in-game film harness (APFS clone only): streams a synthetic 100 Hz phone swing through `NativeMotion` in the frame's Update, films TV game camera + face-on + down-the-line at 60 fps, writes trace.csv/events.txt |
| `scripts/film.sh` | runs it in `~/golf-swing-speed-UnityClone` through heavy.sh, muted |
| `scripts/measure.py` | downswing time, phone-vs-screen impact frame, ball frame, pops (SwingSmoothnessTests rule: step > 2.5 × neighbours + 30 mm; putter + 10 mm), rewinds, smoothness |
| `scripts/compose.py` | before / after film (synced on the phone reaching the ball, real speed then 0.25×) |
| `scripts/cscheck.sh`, `scripts/offline/` | compile-check / run EditMode tests without launching Unity (Unity's bundled Roslyn + .NET) |
| `GATE_RESULTS.md` | gates |
| `film/` | before/after films |

Frames are in `~/golf-swing-speed-frames/{before,before-tt,final}` (not in the repo).

## Rebuild / re-measure
```
work/golf-swing-speed/scripts/film.sh <label> [fresh] GSS_VIEWS=game,faceon,dtl     # takes from ~/golf-swing-speed-frames/<label>/swings.txt
python3 work/golf-swing-speed/scripts/measure.py ~/golf-swing-speed-frames/<label>
python3 work/golf-swing-speed/scripts/compose.py <before_root> <after_root> work/golf-swing-speed/film/<name>.mp4 <tag...>
```
Take spec: `sex:Club:motion:<phone downswing s>[:notracks]`, `sex:Club:touch` (OnLoad + StrikeToward), `sex:Club:tap` (touch-mode NativeSwing).

## Pitfalls
- **Batch-mode clocks:** in batch mode with `captureFramerate`, the unscaled clock is wall time, so it runs slower than the game clock. Pace on `Time.timeAsDouble`.
- **Editor sample feeding:** an Editor update callback runs outside the frame. Feeding the phone from it put samples a frame out of step, so the film feeds in a MonoBehaviour Update instead (`GSSPhoneFeed`).
- **Synthetic source:** in the Editor, `SwingController.Update` feeds its synthetic source into the same detector unless `NativeSportsSession.Active`. The harness gives it a silent source.
- **Shaft turn vs head path:** the shaft barely turns during the authored lag, and a putter rocks rather than turns. So `DownArc` uses the club head's path, not the shaft's turn.
- **pgrep:** `pgrep -f` in an until-loop matches its own command line.

## Follow-ups (not done here)
- **Putter backswing jump:** at clip 0.70 s the putter head jumps 44 mm in one frame (neighbours 2 mm), before and after this change, with or without the clearance tracks. It comes from the Putt clip or a grip/clearance layer.
- **Touch "tap" swing:** in touch mode `NativeSwing` strikes with no backswing at all. The golfer crossfades from address to just before impact, and the club head peaks at 12.9 m/s. A real touch swing needs an automatic backswing, which delays the ball, so that is a gameplay decision.
