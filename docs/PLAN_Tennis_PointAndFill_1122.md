# Tennis setup: point and fill (2026-11-22)

Adnan wanted something friendlier than the flashing TV, and the swing timing drill gone ("too much friction"). With two phones on one TV, both must point at the TV at the same time. Mock: https://claude.ai/artifact/6JUqPwq2YVuf81GC5AJ9Q8

**Status:** built, Swift only, uncommitted. Unit tests pass in the simulator. Not run on a phone or a real TV yet.

## The flow now

1. The court loads. The TV shows the card "Point at the TV" (or "Point at the TV together") with a circle.
2. Behind the card, the picture slowly dims and brightens. That's a black veil following `SportsGlow.wave`, set for every TV frame from the TV screen's own display link.
3. Each phone's rear camera reads its last 2 s:
   - the patch that follows the wave is the TV, which gives the direction through it;
   - how far it trails the wave is the TV's delay.
4. The circle fills in about 2.6 s while every phone sharing the TV sees it. It drains if one points away. Readings that wander fill it slowly.
5. When it's full, the phone with the TV keeps the delay and sends it to Unity as the lag prior. Every phone locks its direction, and the match starts. There's no flash step, no timing drill and no Ready tap. TennisLagLearner (Unity, unchanged) fine-tunes the timing from the first swings.

**Fallback:** after 8 s without seeing the TV, or with the camera off, the phone offers "Use where I'm pointing". That's the existing `useCurrentDirection`, and it uses the TV's saved timing.

## Where

| What | File |
|---|---|
| Wave, reader (finds the TV and its delay), circle, lobby steps | `GolfArcade/Unity/SportsGlow.swift` (new) |
| Camera frames → reader, 10 Hz; exposure locked once the TV is seen | `SportsMotion.swift`, `// MARK: - Point and fill` |
| Circle state, sharing, finish, flow without flashes or drill | `SportsSession.swift`: `beginGlow`, `receiveGlow`, `finishGlow`, `advanceCalibration` |
| TV card, circle, glow veil, chips | `TennisCalibrationTV.swift`: `.scan`, `TVFillRing`, `TVGlowVeil` |
| Phone card (viewfinder, corners, circle) | `TennisPlayViews.swift`: `GlowRingPanel` |
| Tests | `GolfArcadeTests/SportsGlowTests.swift` (synthetic camera frames, circle, steps, proof stills); rewritten flow tests in `MenuFlowRegressionTests`, `TennisQuickStartTests`, `SportsDelayProbeTests` |
| Proof stills | `work/glow-setup-1122/proof/` |

**Lobby steps** while the circle is up: `glow:on` / `glow:off`. The TV phone adds its percentage, as in `glow:on:40`, then sends `glowDone`. The glow clock is the multiplayer network clock when phones share a TV, so every phone reads the wave the TV phone draws.

**Unity:** nothing changed, so there's nothing to re-export. The old `flash` command and the timing drill code are still there, just no longer called.

## Tuning on a device

| Constant | Now | Watch for |
|---|---|---|
| `SportsGlow.dimmest` / `lightest` | 0.46 / 0.04 | The glow is too faint to read on some TVs (auto brightness or dynamic contrast), or too obvious |
| `SportsGlow.gameFrameLead` | 1/60 s | The glow is timed at frame presentation, while the old flash was timed at Unity's frame stamp. Compare one TV both ways. |
| `SportsGlowReader.minimumMatch` / `cellMatch` | 0.8 / 0.6 | False "TV found" from a lamp or window, or a TV that's never found |
| `SportsGlowFill.seconds` | 2.6 s | How long holding feels |
| `SportsSession.glowHelpAfter` | 8 s | When the fallback button appears |

`SportsDiagnostics` logs these lines:
- `glow begin …`
- `glow read begin offset=…`
- `glow done delay=… lag=… readings=… spread=…`
- `glow locked tvHeading=…`

## Device checklist

1. Solo, AirPlay to Apple TV:
   - the circle fills in about 3 s;
   - `glow done delay` is within ~30 ms of the old flash reading for the same TV;
   - the first serves feel on time.
2. Point away halfway: the circle drains. Point back: it refills.
3. A bright room with a lamp in view: it doesn't fill until the TV is in the corners.
4. Two phones, one TV:
   - the circle stays at 0 % until both point at the TV;
   - it drains when either one points away;
   - both phones go to the match together.
5. Camera permission off: the fallback button shows, and the match starts with the saved timing.
6. Rematch on the same TV: no circle (the direction is still held). Settings → TV timing check: the circle runs again.

## Trade-offs

- **Pointing under the loading screen (T4) is off** (`SportsSession.pointUnderLoading`), because the circle needs the court on the TV to glow behind it. It could come back if the circle is drawn over the loading cover.
- **A known TV now takes about 2.6 s of pointing instead of a 1 s hold.** A rematch is still instant.

## Unrelated failures in the simulator

These were already failing and aren't caused by this change:
- `MenuBetaTests.testPlayRoutesAndBackPaths` and `testCalibrationIsOnThePlayListAndLaunchesTheAimPracticeCourt`: the Calibration row was removed on 11-16, and cast rows were added since;
- `MenuFlowRegressionTests.testTennisNeedsAnExternalScreenButGolfDoesNot`: map → connect.
