# Review capture 10-19: GOLF (golf agent)
Source: APFS clone ~/unity-clones/review-1019 of Unity/ (all uncommitted 10/19 work, cloned 17:33), batch mode, muted, captureFramerate 30.
Hole: cliffside hole 1 (par 4), phone flow (PrepareNativeAddress / NativeReady / TryNativePresentation), chat A broadcast camera + chat B waggle/watch.
Play: flyover (skipped by the phone continue after 12 s) -> address + waggle (3 s) -> drive -> post-shot watch -> 5-iron approach onto the green
-> putt 1 (missed on purpose) -> putt 2 holed -> FistPump hole-out -> round card (4 strokes, par). Film = 46.5 s, 1396 frames.

## Videos (golf/)
- golf/golf_gameplay.mp4: the gameplay camera with the HUD, exactly as on the TV, 1280x720
- golf/golf_side_on_wide.mp4: side-on wide, up the target line looking back at the golfer (lead-side profile), 960x540
- golf/golf_face_on_close.mp4: face-on close-up, in front of the golfer's chest, 960x540
- golf/golf_drone_ball.mp4: high drone that follows the ball in flight (else the golfer), 960x540
- golf/golf_behind_green.mp4: fixed camera behind/right of the green looking back to the tee, 960x540
- golf/golf_chase_low.mp4: low chase behind the ball (behind the ball along the line at rest), 960x540
- golf/golf_establishing.mp4: fixed high wide shot of the whole hole from the side, 960x540
- golf/golf_grid.mp4: all 7 above, labelled, 3x3 grid 1920x1080
- golf/golf_events.txt, golf/golf_trace.csv: per-stage times and per-frame state/camera/ball trace for the films

## Stills (stills/golf/, sheet stills_golf.jpg)
- stills/golf/golf_{male,female}_{address,idle}_{1_front,2_34left,3_side,4_34back,5_back,6_face,7_lowfull}.jpg: 1200x1500, on the cliffside
  hole 1 tee with game lighting and the golf kit. "address" = at the ball with the driver, "idle" = standing (Idle clip, game paused).
- stills_golf.jpg: labelled contact sheet of all 28.

## Tools (tools/)
- tools/unity/ReviewGolfFilm.cs, ReviewShared.cs, ReviewMute.cs: the harness (copied into the clone's Assets/Editor/ReviewLocal by film.sh)
- tools/film.sh golf: runs it through heavy.sh; frames land in ~/review-1019-frames/golf (the encoded films are from ~/review-1019-frames-run2/golf)
- tools/mkvid (+ mkvid.swift): JPEG sequence -> H.264 mp4 and labelled grid mp4 (AVFoundation, no ffmpeg)
- tools/sheet.py: labelled contact sheets (PIL)
