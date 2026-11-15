# Gameplay, ball physics, pacing and animation — what is lacking (2026-11-11)

Read from the code and from today's films. Nothing was changed. Direction from Adnan: arcade in the sense of *looking real but goofy* — believable ball and body first, exaggeration in the reactions.

## Golf: landing and bounce

The flight is a proper stepped simulation (drag, lift, wind, spin per club). The problems are all in the landing.

| What happens | Where | Real behaviour |
|---|---|---|
| Every full shot hops 1–2.4 m and skips 2–3 times, wedges included | `Shot/BallFlight.cs:99-100` (rebound factor 0.30–0.46); pinned by test `AFullShotKicksUpThenSkipsAndRuns` | A wedge lands and stops or takes one small hop; a driver skips and runs |
| Rebound ignores how steeply the ball comes down | `BallFlight.cs:186` | Steep landings stop, shallow ones skip |
| Spin only trims forward speed once, then is discarded | `BallFlight.cs:189-194` | Backspin checks the ball or pulls it back |
| The bounce is computed on a flat plane | `BallFlight.cs:180`, `Course/CourseShot.cs:840-851` | An upslope kills the ball, a side slope kicks it |
| Fairway, tee, fringe and out-of-bounds bounce identically; the green is almost as lively | `Course/Hole.cs:80-89` | Each surface differs |
| The lie is judged once, at the first touchdown | `CourseShot.cs:712-719` | Each hop lands on its own surface |
| No variation: the same launch always lands the same | — | Small natural spread |

The rebound was raised on 10-28 after "not bouncy enough" (from 0.12–0.26 to 0.30–0.46). The roll after the hops is sound: it respects slope and surface.

## Tennis: the ball is too high on ordinary shots

It is not the lob stroke. Ball speeds are 10 / 13 / 17.5 m/s (mistimed / middle / perfect; `Tennis/TennisRules.cs:966-973`) and about 13–14.5 m/s for the CPU, under real gravity with no air drag. To cross a real-size court at that speed the solver has to throw the ball high.

| Shot | Flight (real s) | Peak height |
|---|---|---|
| Perfect drive | 1.12 | 2.6 m |
| Middle-quality shot | 1.43 | 3.8 m |
| CPU drive | 1.41 | 3.7 m |
| CPU lob | — | 4.4 m, fixed |
| A real rally ball (about 25 m/s) | 0.86 | about 1.6 m |

- The 10-26 "hang time" change made it higher: slower pace, and net clearance raised from 0.7 to 1.1 m (CPU 0.45 to 0.9).
- The bounce keeps 75 % of the vertical speed, so the second arc peaks at 1.7–2.3 m, and anything above 1.75 m is classed as a smash.
- CPU lobs can be 18–24 % of rally balls.
- No test checks rally peak height. The one that checks a peak under 3.3 m covers serve returns only, with an outdated clearance.

## Pacing

| Sport | Longest waits |
|---|---|
| Tennis | 12.9 s intro (both players must vote to skip in versus); 2.2 s pre-serve routine; 4 s set beat. Game speed is 1.1× |
| Golf | 7.9 s hole flyover; at least 3 s + 2.5 s on hole-out; no simultaneous or ready-golf play; replay code exists but nothing calls it |
| Bowling | Strike replay up to 8 s; 3.1 s pin sweep that cannot be skipped; about 3 s walk back |

Frame rate is floored at 60 on every scene, with quality tiers by phone. There is no dynamic resolution.

## Animation

### Bowling
- The bowler's body is a fixed-tempo clip, not the player's swing. The code comment says the walk is time-warped to the swing; `ActionRate` is only ever 1 (`Bowling/BowlingHero.cs:157`, `BowlingGame.cs:443`).
- About twenty authored clips are never played: pickup, walk with ball, walk back, watch pins, the seated set, cheer and clap, both intros, all idles, win and lose.
- The ball snaps into the hand at setup; there is no pickup from the return.
- No foot planting, and the body jumps 3.55 m forward when the delivery clip ends.
- The clip swaps at release with no blend.
- Faces are never driven; the crowd is a procedural bob.

### Tennis
- Her elbows flare in the run and recover clips (today's films).
- Found on 10-17 and not re-checked today: the serve plays at half speed with the racket still at contact, swing starts pop when the prepared clip differs from the swung one, and feet slide.
- Free hands rest as claws.

### Golf
- The address pose is stiff, with straight arms held away from the body, and identical on every hole.
- I did not film a golf swing today.

### All sports
- No facial animation beyond blinking.
- The 10-12 frame-by-frame review of 138 clips circled 9,271 problems, mostly hands sinking into clothes and thighs whenever the hands are low.
- Nothing is exaggerated: no anticipation, squash or oversized reactions, which is where the goofy half of the brief would live.

### The fresh all-clips audit did not complete
I started the project's all-clips audit on the current heroes and stopped it: it processed 6 clips in 10 minutes, so the full set would take hours. All six flagged hands or forearms inside the shirt at a depth that looks like the tool's cap (49.8 mm). Without a baseline run on the old bodies I cannot say whether that is the tool misreading the new build or the new build really intersecting.

## Order I would take

1. Tennis arc, with a test that pins rally peak height.
2. Golf landing model.
3. Bowling: play the clips that already exist, then match the tempo to the swing.
4. Pacing cuts.
5. Run the all-clips animation audit overnight, with a baseline.
