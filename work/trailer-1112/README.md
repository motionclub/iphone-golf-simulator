# MotionSports trailer — "Settle It"

**The film:** `MotionSports_Trailer.mp4` (2:18, 1920x1080, 24 fps, 2.39:1 bars, stereo sound, no voice).

## Change a caption

Open `captions.json`. Each caption has `text`, `duration` (seconds on screen), `style` and `at`.

- `at` is a named moment in the film (`round1`, `score1`, `round2`, `score2`, `round3`, `title`, `tagline`, `end`). `offset` moves it by seconds. A caption with `"start": 12.5` instead of `at` appears at that second.
- Styles: `chapter` (spaced capitals with a rule), `score` (big numerals), `title` (the logo), `line` (small, lower centre), `end` (end card; `\n` starts the second line).
- The font is Kanit, the game's menu font (`"font"` at the top).

Then rebuild (about 5 minutes; nothing is re-filmed):

```bash
./build.sh
```

A quick half-size check first: `./build.sh --half`.

## Change the cut

`make_edl.py` is the cut list, one line per shot: take, camera, first frame, seconds on screen, speed (1 = real time, .2 = five times slower, or a ramp). Run `python3 make_edl.py`, then `./build.sh`. Music follows the `marks` in that file; game sounds follow each shot's `snd` list.

## What is where

| File | What it does |
|---|---|
| `SCRIPT.md` | the approved script (draft 2) |
| `make_edl.py` → `edit.json` | the cut |
| `captions.json` | every caption |
| `edit.py` | cuts the takes, speed ramps with real frame blending, grade, bars, captions |
| `score.py`, `synth.py` | the music and sound, generated in code, plus the game's own effects |
| `render.py`, `build.sh` | render in four pieces and join with the sound |
| `stage/takes/` | the filmed frames (about 10 GB; needed for any rebuild) |
| `TrailerFilm.cs` | the Unity film server (lives in the private clone `~/unity-clones/trailer`, not in the game project) |
| `film.py`, `golf.py`, `s*.py`, `g*.py`, `b1.py` | the scripts that filmed each take |

## Re-filming a shot

Start the film server (`./server.sh Tennis skyscraper`, `./server.sh Golf neon`; bowling is reached with `{"op":"scene","scene":"Bowling"}`), run the take script with `f` (for example `python3 s5.py f`), then stop the server with `echo '{"op":"quit"}' | python3 send.py -`.
