# WATCH — match-animation reference clips (MATCH ANIMS 1/2)

Written 2026-10-03; second search pass the same day (see "How I watched"). Nothing here is animated. No hero, rig or Unity file was touched. **No video was downloaded or saved anywhere** (not in the repo, not in /tmp). Frames were only viewed in the browser; the only copies are the screenshot cache the Claude app keeps for this session, outside the repo.

**GATE: MATCH_ANIM_WATCH_GAPS PASS** (1b/2 gap re-watch, 2026-10-03; it replaces the first-pass `GATE: MATCH_ANIM_WATCH FAIL`, whose only failing lines were the next two)
- `SliceApproach`: **seen, THIN on contact.** A one-handed backhand slice with the player moving forward (feet visible; a run-in, a split-step landing and a first volley follow) is in `https://www.youtube.com/watch?v=ebS3Lf25hZ0` t=3.40–18.70. His body hides the contact in that back view. Section 17, at the bottom. The earlier "not found" verdict is withdrawn.
- `ForehandShort`: **seen.** A forehand hit on the move while stepping in on a short ball, feet and contact in frame, is in `https://www.youtube.com/watch?v=WBfw9nFojHc` t=64.50–68.00 (the take-back is hidden). Section 18, at the bottom. Section 8 stays the mini-tennis forehand it always was. The earlier "partial only" verdict is withdrawn.
- Everything else was seen; each section says what was only partly visible.

## How I watched

- Claude desktop built-in browser, YouTube player, 1080p (a few close-ups at 1440p). The 2160p / 120 fps streams would not load in this browser, so slow-motion detail is limited to 1080p.
- I paused the player and stepped it to exact media times (0.04–0.5 s apart; 0.025–0.033 s steps for the return), drew those frames side by side, and read them by eye. Every time below is a media time you can reopen at `https://www.youtube.com/watch?v=<id>&t=<seconds>s`.
- When the pane was hidden the player sometimes handed back a stale frame. Any sheet whose neighbouring cells were identical was thrown away and re-taken (for example my first attempt at `DGIkkdxMrWc` t=865.2–866.9).
- **Second pass (after you asked me to search the unwatched stretches).** I sampled every stretch I had skipped: `DGIkkdxMrWc` 9:26–10:31 and 18:16–19:28; `HI0bvG0pw4w` 9:23–13:55; `-Eu80hGbgVA` 6:00–6:52; `bvVXmtHt0DM` 3:57–7:01; `0a_DL1I4q38` 2:46–4:23; `rxo1uEdLouY` 1:35–2:58; `sH3iK7Wm5EY` 0:00–6:36 and 11:33–16:12; `vD0wO3tq6BM` the whole clip. Steps were 1–4 s for most, 12.5 s for the Colton serves. **A step of 2–4 s can step over a whole 1–1.5 s swing in a real-time clip, so "not found" below means "not found at that sampling", not "proved absent".**
- One autoplay recommendation (not in your list) flashed in the pane early on; none of its frames were used. After that every sheet was stamped with the video id and refused to draw on an ad or a different video.

## How to read the numbers

- **Left / right.** "his/her R/L" = the player's own side. "viewer's left/right" = left/right in the frame. In a back view the player's R is the viewer's right; in a front view it is the viewer's left. All players I read as right-handed (Djokovic, Alcaraz, Zverev; the others from their racket arm).
- **Swing window.** `t_start` = first visible take-back movement of racket or shoulders (not the ready stance). `t_end` = racket reaches the peak of its follow-through. **Contact fraction = (t_contact − t_start) / (t_end − t_start).** Where the ball is visible on the strings I trust it to about ±0.05; where I inferred contact from the arm and racket I say so and trust it to about ±0.1.
- **Slow motion.** Slow-mo clips have an unknown slow-down factor, so their seconds are video seconds. Use the fractions, not the seconds. Djokovic's DGIkkdxMrWc clip is real time at 60 fps; its seconds are real seconds.
- **Stroke direction, not style.** Several clips are practice, so shot depth and pace are not known.

## Clip index (what each URL actually is)

| id | what it is | notes from watching |
|---|---|---|
| `DGIkkdxMrWc` | Djokovic court-level practice 2023, 19:28, real time 60 fps, phone camera | chapters verified: 0:00 groundstrokes, 4:22 serves, 10:31 returns, 13:49 volleys/overheads, 15:35 warm-up. **The warm-up starts as mini-tennis (t≈935.6–990)** a few metres behind the net, then moves back to full groundstrokes (close camera behind him from ~16:40). After the 18:36 "thanks" there is bonus footage and a freeze frame (t≈1117–1167). |
| `yAM1j_B6yQs` | "2026 Forehand Compilation" — **a 21.8 s vertical Short** | **the stamps 0:24 (Alcaraz) and 1:03 (Djokovic) do not exist in it.** Alcaraz is t=0.0–1.37, Djokovic t=1.37–2.47, then Sinner, Zverev, Musetti and others about 1 s each. Frames are doubled (about 15 distinct frames/s). Every clip starts mid-swing, so there is no take-back in it |
| `HI0bvG0pw4w` | "Explosive Forehands Up Close", 14:08, slow motion from behind | stamps match: Djokovic from t≈16.5, Alcaraz from t≈115.5 |
| `-Eu80hGbgVA` | Alcaraz forehand and backhand, slow motion, 6:55 | many camera cuts and zooms; tracking him is unreliable |
| `bvVXmtHt0DM` | Alcaraz + Tiafoe practice, real time, 8:12 | baseline rallies from a far camera (t≈238–384); net feed drill from t≈385: front view of Alcaraz at the net with the net behind him (t≈398–421, not analysed in detail), then a camera behind him for the overheads (t≈436–463) |
| `0a_DL1I4q38` | Zverev two-handed backhand, slow motion, 720p only | front-left view, very clear |
| `s8BvHWqlodI` | Sasnovich serve, 16.9 s vertical slow-mo | female serve reference |
| `rxo1uEdLouY` | Alcaraz serve/forehand/backhand, slow motion, 3:45 | serve at t=178–182; matches the chapter list (serve 2:58) |
| `sH3iK7Wm5EY` | Colton Smith / Tseng Chun-hsin practice, 16:31 | t≈3–390: baseline rallies from a high camera far behind the baseline; net-level front view at t≈402–410; serve at t≈635; Colton's serves from t≈818 |
| `vD0wO3tq6BM` | Eala practice, 8:15 | **mapped at 1–4 s steps, not analysed stroke by stroke; no section relies on it.** Content: t≈8–157 coach-fed baseline forehands/backhands (close front/side views); 160–217 more of the same with the net at the bottom of the frame; 256–277 volleys and overheads at the net (front 3/4 view); 280–347 close front views of groundstrokes (feet mostly cropped); 385–478 serves (front view first, then side). Female cross-check material for groundstroke, volley/overhead and serve lives there. |

## Coverage

| # | section | seen? |
|---|---|---|
| 1 | ReadyIdle | yes (static stance only; no idle loop in any clip) |
| 2 | SplitToForehand | yes, **but no airborne split-step hop seen anywhere** |
| 3 | SplitToBackhand | yes, same caveat |
| 4 | RecoverCenter | yes |
| 5 | Forehand | yes |
| 6 | ForehandOpen | yes (clip starts after the take-back) |
| 7 | ForehandWide | yes |
| 8 | ForehandShort | yes — the step-in on a short ball is **section 18**; section 8 is the mini-tennis version |
| 9 | Backhand | yes |
| 10 | BackhandWide | yes |
| 11 | SliceApproach | yes — **section 17**, THIN on contact (the back view hides the ball behind his body) |
| 12 | Serve | yes |
| 13 | Return | yes (contact frame hard to see) |
| 14 | VolleyForehand | yes |
| 15 | VolleyBackhand | yes |
| 16 | Overhead | yes |

---

## 1. ReadyIdle

**Used:** `HI0bvG0pw4w` t=21.5–22.9 (Djokovic, back view, slow motion). Cross-checks: `DGIkkdxMrWc` t=635.48–636.38 (returner, front view, 1440p, real time); `sH3iK7Wm5EY` t=402.55–403.31 (net-level front view).

**Feet, in order**
1. Stance wide (visual estimates): about 1.7× shoulder width in the Djokovic back view, about 2× in the front-view return, about 1.5× in the net-level view. Both feet flat on the ground, toes forward or slightly out.
2. Knees slightly flexed (the front view reads about 25–30°), hips a little lowered, torso upright and leaning slightly forward.
3. Across t=21.5–22.75 the feet do not move. In the 0.025–0.033 s steps of the return (t=635.5–636.38) both feet stay on the ground. Only weight sway of a few centimetres is visible.
4. In the net-level view (t=402.55–403.31) the feet shift slightly side to side as the weight sways; I did not measure it.

**Shoulders and racket**
- Shoulders square to the net and relaxed.
- Hands together at the belt or belly with the racket held in front (return view: racket head up and slightly forward; net-level view: arms hang low in front of the thighs, racket hanging at the side until t≈403.35).
- No cyclic bob. The only motion before the first move is small sway.

**Contact:** none.

**What is different:** this is the baseline pose the other three movement clips start from.

**Could not see:** an idle longer than about 1.4 s (every clip moves on); heel micro-lifts at 1080p; racket orientation in the back views (hands hidden by the body).

---

## 2. SplitToForehand

**Used:** `DGIkkdxMrWc` t=1015.90–1016.40 (Djokovic, close camera behind him, real time). Cross-checks: `sH3iK7Wm5EY` t=409.10–409.97 (net-level front view, lunge to his R); `HI0bvG0pw4w` t=22.90–23.90 (Djokovic, slow-mo, back view).

**Feet, in order (DGIkk t=1015.9–1016.4)**
1. t=1015.90–1015.98: compact stance, feet close (about 0.6–1.0× shoulder width), knees deeply bent, both feet on the ground, racket in front.
2. t=1016.05: first move — his R leg strides wide toward his R while the L leg pushes off.
3. t=1016.13: stance about 2× shoulder width (visual estimate; it widened from ≈0.6–1.0× in about 0.15 s); R foot planted flat on the outside; weight loads onto it.
4. t=1016.20–1016.27: L leg trails behind on its toe (not stepped through); knees bent; R knee takes the load.
5. t≈1016.37: contact with the R foot still planted (see Forehand for the stroke).

**Shoulders and racket**
- t=1015.90–1016.05: racket in front, then his L arm swings out to the side at shoulder height (t=1016.05–1016.27) for balance.
- t=1016.13: racket goes back on the R side in the R hand, shoulders turned about 70–90° toward his R.
- t=1016.20–1016.27: racket back and slightly low, head up; the ball is visible to his R (viewer's right in this back view) at t=1016.05–1016.27.

**Contact:** ≈1016.37 (ball not seen on the strings; inferred from the arm at full extension at hip height). From the first stride (1016.05) to contact is about 0.3 s.

**Seen in the cross-checks**
- `sH3iK` (front view): from a ready stance (t=409.10–409.17) the first move at t=409.22 is his R foot stepping out wide while the racket goes back at the same time; the L leg then trails and drags on its inside edge (t=409.37–409.53); deep lunge bottoms out at t=409.70–409.97 with the racket near his R foot. This is a low net reach, not a baseline stroke.
- `HI0bv` (slow motion): from the ready stance (t=22.9) he turns and loads the racket back (t=23.1–23.5), then lunges forward and hits at t≈23.90.

**What is different from the neutral forehand:** the neutral forehand (section 5) has no lateral travel; here the stance widens roughly 2–3× in about 0.15 s and the L leg trails.

**Could not see:** **a split-step hop.** In every clip the feet stay on the ground until the first stride. No frame shows both feet airborne before the lunge. I looked specifically for one in the second pass: Zverev's feet at 0.04 s steps (`0a_DL1I4q38` t=16.92–17.88, slow motion) show alternating walking/jog steps and a stance that widens, with no two-footed hop; Eala's close camera (`vD0wO3tq6BM` t=303–309) crops her feet. Also not seen: which foot is airborne during the first stride (feet are small and the camera is behind).

---

## 3. SplitToBackhand

**Used:** `DGIkkdxMrWc` t=10.19–12.16 (Djokovic, behind, real time). Cross-checks: `sH3iK7Wm5EY` t=403.30–404.00 (net-level front view); `0a_DL1I4q38` t=17.40–19.60 (Zverev, slow-mo).

**Feet, in order (DGIkk; re-read at 0.05 s steps, t=10.20–11.35)**
1. t=10.20–10.45: ready stance, about 1.7× shoulder width, both feet flat, hands together at the belt.
2. t=10.50–10.60: his L foot steps out wide to the left (stance widens to about 2×); the R foot stays put.
3. t=10.65–10.75: L foot planted wide, L knee bent, weight on the L leg; the R leg extends behind and trails on its toes.
4. t=10.80–10.90: the R foot is lifted off the ground behind the L leg (toe down).
5. t=10.95–11.05: the R foot swings forward and arrives next to the L foot.
6. t=11.10–11.20: feet close together at about hip width, flat.
7. t=11.25–11.39: both heels up (feet on the toes) as the racket drops low.

**Shoulders and racket**
- t=10.35–10.45: racket head hangs at his L hip, hands together at the belt.
- t=10.50–10.75: shoulders rotate left (about 60° then about 90°); racket tip up at the L hip, hands low.
- t=10.80–11.20: racket held back and vertical at the L hip, shoulders about 90–100° turned (about 0.4 s).
- t=11.30–11.39: racket drops low at his L, near ankle height (the bottom of the drop).
- t=11.44–11.56: racket rises fast (about 0.15 s) from low to above the L shoulder; it is then wrapped behind the head by t≈11.75 (peak) and comes down by t≈12.1.

**Contact:** none. The ball on the court stays fixed in the frame and no live ball reaches him, so this is a **shadow swing**; the clip is good for the first move and the racket path, not for contact timing.

**Seen in the cross-checks**
- `sH3iK` (front view): from ready (t=403.30) the racket rises to his L side at t=403.35 and he lunges to his L; his L foot out wide with the knee bent; racket head up and held at chest height at t=403.52–403.88; ball visible at the top right at t=403.52.
- `0a_DL` (Zverev): racket tilts left at t=17.68; his L foot steps out wide on its toe at t=18.28–18.56; wide landing at t=18.88 (see BackhandWide).

**What is different from SplitToForehand:** the steps are mirrored, and the trailing R foot lifts off the ground and swings in to meet the L foot instead of staying behind on its toe; the racket waits at the L hip and then drops low before it rises.

**Could not see:** a split-step hop (none in any frame); the foot-by-foot order in the front-view cross-check (the feet are small).

---

## 4. RecoverCenter

**Used:** `HI0bvG0pw4w` t=150.0–156.5 (Alcaraz after a wide forehand, slow-mo, behind). Cross-check: `DGIkkdxMrWc` t=637.23–637.98 (returner after the return, front view, 1440p, real time).

**Feet, in order (Alcaraz)**
1. t=150.0–151.0: after the wide stroke he is airborne or landing off balance, drifting out of the shot, racket still extended.
2. t=151.5–152.5: three long recovery strides back toward the court centre — each a leap with the trailing leg fully extended behind and the body leaning forward.
3. t=153.0–154.0: steps shorten and slow; he turns his body back toward the net.
4. t=154.5–156.5: walking steps, racket hanging low in the R hand, standing relaxed at t=156.5.

**Shoulders and racket:** racket arm still extended after the stroke (t=150–151); during the strides the racket is carried in the R hand at hip height with the L arm swinging; by t=154.5 it hangs low.

**Contact:** none.

**Seen in the cross-checks**
- `DGIkk` (front view): after the finish, about 0.35 s of small quick steps (I could not count them) while the torso straightens (t=637.23–637.58), arriving in a narrower upright stance with the racket low at the R hip by t≈637.7–638.0, about 0.85 s after the return's contact.
- `sH3iK7Wm5EY` t=405.98–406.50 is **not** a recovery: after the low net reach he drops the racket, turns his back to the net and walks away.

**What is different:** recovery length scales with how far he was pulled; the Alcaraz example is the long version (about 2 s of video time of strides), the Djokovic return the short one (about 0.35 s of real time).

**Could not see:** the recovery from a forehand hit at the baseline in real time with the whole court visible; a recovery that ends in a clean split-step.

---

## 5. Forehand (neutral reference)

**Used:** `DGIkkdxMrWc` t=7.60–9.90 (Djokovic, camera behind and to his right, real time 60 fps). Contact: **t=8.99**, ball on the strings.

**Feet, in order**
1. t=7.59: ready, stance about 1.4× shoulder width, both feet flat, parallel to the baseline.
2. t=7.74: weight shifts onto the R foot; the L heel lifts.
3. t=7.89: the L foot re-plants a little wider.
4. t=8.04: the L heel lifts again (second small adjusting step); R foot flat.
5. t=8.19–8.34: both feet flat, wide, knees bending more, weight on the R leg.
6. t=8.49–8.74: deepest knee bend; feet roughly parallel to the baseline (semi-open; the L foot is slightly nearer the net).
7. t=8.89: the R heel starts to rise and the R knee extends as hips and shoulders rotate toward the net.
8. t=8.99 (contact): both feet on the ground, wide base; no step with the L foot; weight moves from R to L.
9. t=9.04–9.19: the R heel is up and the R foot swings in on its toe; the L foot stays planted.
10. t=9.34–9.49: feet back to about shoulder width, both flat.
11. t=9.64–9.79: wide ready stance again.

**Shoulders and racket, in order**
1. t=7.59–7.69: racket in front at the belt, shoulders square.
2. t=7.69–8.04: shoulders turn right (about 45° then about 90°); racket goes back at his R side.
3. t=8.04–8.19: his L hand takes the racket throat; racket vertical.
4. t=8.34–8.49: shoulders turned past 90° (chest toward the camera), racket tip up behind the head, the L hand lets go and the L arm extends toward the ball.
5. t=8.59–8.79: racket drops behind to the R hip, the L arm stays out for balance.
6. t=8.79–8.89: forward swing begins low to high; hips and shoulders rotate toward the net; the L arm folds in.
7. **t=8.99 contact** in front of the body at hip/waist height, arm nearly straight, shoulders about square.
8. t=9.04–9.19: racket continues up and across the body and wraps behind the neck on his L side (t=9.19).
9. t=9.34–9.49: finish with the racket around the L shoulder (peak).
10. t=9.49–9.79: racket lowers back to the belt.

**Contact fraction:** t_start = 7.70, t_end = 9.45, contact = 8.99 → **≈0.74** (0.70–0.74 depending on where the take-back is said to begin). Whole swing ≈1.75 s real time (a relaxed rally swing; the ball was not tracked); contact is about 1.3 s after the first movement and about 0.45 s before the finish.

**What defines "neutral" here:** semi-open stance, one small adjusting step before loading, two-handed prep that releases the L hand before the forward swing, contact in front at hip height, full wrap finish.

**Could not see:** racket-face angle (back view); the R foot's toe angle; the incoming ball (far and small in this camera).

---

## 6. ForehandOpen

**Used:** `yAM1j_B6yQs` t=0.00–1.37 (Alcaraz, front-side view, slow motion). Cross-check: same clip t=1.37–2.47 (Djokovic). The clip starts at the low point of the loop, so there is **no unit turn or take-back** in it.

**Feet, in order (Alcaraz, feet-only crops at t=0.0, 0.10, 0.23, 0.37, 0.50, 0.63, 0.77, 0.90)**
1. t=0.00–0.90: his R foot (viewer's left in this front view, white shoe) stays planted flat with the knee bent for the whole window.
2. t=0.00–0.90: the other foot (his L, viewer's right, shoe with the orange logo) stays **off the ground** the whole time, toe pointing down, about 10–15 cm up. All weight is on the R leg.
3. t=0.77–0.90: the R heel begins to rise.
4. Djokovic cross-check: the visible foot (his L, viewer's right) is planted at t=1.4–1.6 and rises off the ground at about t=1.8, after contact.

**Shoulders and racket**
1. t=0.00: racket head low at his R side (viewer's left), arm bent; his non-racket arm is bent in front of the face with the hand up near the chin and the thumb out. That hand stays there until about t=1.3. Chest open toward the camera, head still on the contact point.
2. t=0.10–0.23: racket rises quickly from low to high; the ball is visible to the viewer's right of the racket, close to it at t=0.23.
3. **t≈0.27 contact** (ball and strings together between t=0.23 and 0.30; the strings are blurred at 0.30), in front of the hip at thigh/hip height.
4. t=0.37–0.50: racket sweeps up and across the body.
5. t=0.50–0.93: racket high toward the L shoulder (viewer's right), elbow high.
6. t=0.93–1.37: finish above and behind the L shoulder.
- Djokovic (cross-check): the ball touches the strings at about t=1.82 (frames t=1.80 and 1.85); same L-hand-up-at-chin shape.

**Contact fraction:** t_start 0.00 (clip start, not a real take-back start), contact 0.27, t_end ≈1.2 → 0.22 **of what is visible**. Do not use 0.22 as a whole-swing fraction. For the whole swing use the neutral forehand's ≈0.74 and use this clip only for the forward-swing shape and the stance.

**What is different from the neutral forehand**
- **Open stance:** feet parallel to the baseline, chest faces the net/camera at contact (square), not the semi-open turn of section 5.
- **Weight on the outside (R) leg alone**, other foot lifted, instead of both feet down.
- **The off-hand stays up at the chin** through the swing instead of folding into the chest.
- **Higher finish:** racket above and behind the L shoulder with the elbow high.
- Rotation looks hip-driven (hips open to the net while the racket is still low).

**Could not see:** the unit turn and take-back; the L foot landing; the exact strings-contact frame (the clip has about 15 distinct frames per second).

---

## 7. ForehandWide

**Used:** `HI0bvG0pw4w` t=145.5–150.0 (Alcaraz running wide forehand, slow motion, camera behind-left; ball visible at t=149.23–149.38). Cross-checks: `HI0bvG0pw4w` t=91.0–94.6 (Djokovic, planted wide lunge); `DGIkkdxMrWc` t=1015.90–1017.50 (Djokovic, real time).

**Feet, in order (Alcaraz)**
1. t=145.5–147.0: running toward his R with alternating strides; at t=146.20 the rear foot (viewer's left) is behind and the leading foot (viewer's right) is ahead on its toe.
2. t=147.0–147.5: last steps shorten; knees bend; shoulders turn right.
3. t=147.63–148.12: deepest knee flexion; as far as I can read, the outside (R) leg is the loaded one.
4. t=148.0–149.5 (full-body frames at 0.5 s): wide, low lunging stance (knees about 110–120°), outside foot planted, trailing leg extended behind.
5. t=149.9–151.0: he leaves the ground and lands off balance (continues in RecoverCenter).
- The exact order of the last two steps could not be read; the feet are cropped or small in the sharp frames.

**Shoulders and racket**
1. t=145.5–147.0: racket carried in front at chest height in both hands, head up, body leaning forward.
2. t=147.2–147.5: racket goes back with the tip up on the R side; his L arm extends horizontally toward the ball (t=147.32–148.40).
3. t=148.27–148.75: racket drops behind and begins forward.
4. t=148.92–149.23: forward swing, racket sweeps up at arm's length to his R.
5. **t≈149.40 contact**: ball just right of the racket at t=149.23–149.38; arm extended horizontally at hip/waist height, body stretched sideways.
6. t=149.55–149.72: racket sweeps across and up the body.

**Contact fraction:** t_start 147.2 (racket goes back; the running approach is not counted), contact 149.40, t_end ≈149.95 → **≈0.80**.
- Djokovic planted lunge (slow motion; contact **inferred**, the ball is out of the crop): t_start ≈91.0, contact ≈93.65, t_end ≈94.6 → ≈0.74.
- Djokovic real time (t=1015.9–1017.5): racket already up when the lateral step starts, so the visible window is short; t_start 1015.95, contact ≈1016.37, t_end ≈1016.80 → ≈0.5.
- So the spread for wide forehands is **0.5 (reactive, racket pre-loaded) to 0.8 (slow loop)**.

**What is different from the neutral forehand**
- Contact is far from the body: arm fully extended, torso leaning sideways instead of rotating square.
- Stance is far wider (about 3× shoulder width in Djokovic's lunge at t=92.4–93.15, with his L knee bent and the R leg extended wide; by t=93.45–93.75 the R knee bends (about 110°) and the L leg trails extended behind; the L foot lifts and swings in at t=94.05–94.5). Back view, so R = viewer's right.
- The L arm stays extended for balance through the swing.
- The follow-through ends with the body still moving; he does not return to a set stance.

**Could not see:** foot-by-foot order in the last two steps; the ball on the strings in the Djokovic examples.

---

## 8. ForehandShort — the short-court mini-tennis forehand (the step-in on a short ball is section 18)

**What "short" can mean, and what I found.** (a) A **short ball**: the opponent's ball lands near the service line and the player steps in and attacks it. **Found in the 1b/2 re-watch — section 18.** (b) A **short-court, compact forehand**: the mini-tennis at the start of Djokovic's warm-up. **Everything below is (b).** Do not read a step-in or an attacking swing out of this section; take those from section 18.

**Used:** `DGIkkdxMrWc` t=939.5–941.9 (Djokovic, mini-tennis at the start of the 15:35 warm-up; camera behind him and a little to his left, real time; sheets at 1440p). He stands roughly at the service line, a little behind it, with a partner across the net hitting soft balls. Contact: **t≈941.46**, ball next to the strings in the 1440p frame (±0.05 s).

**Feet, in order**
1. t=939.49–939.89: ready, facing the net, feet about shoulder width apart and parallel, both flat; racket held low at his R side (mostly hidden).
2. t=940.09: feet widen to about 1.3× shoulder width, both flat.
3. t=940.29–940.49: the body starts to turn (about 30° then 45°); feet still flat.
4. t=940.69–940.89: turn about 60°, stance staggered (which foot is ahead is not clear at this size), weight leaning back onto the R side.
5. t=941.09–941.39: weight moves forward as the hips rotate toward the net.
6. **t≈941.46 contact:** both feet on the ground; **no step** — he pivots on the spot.
7. t=941.59–941.79: feet come level and flat again, body square to the net.

**Shoulders and racket, in order**
1. t=939.49–940.09: shoulders square to the net, racket low at the R side.
2. t=940.25–940.36: first visible take-back — the racket lifts to head height on his R side; his L arm comes up in front.
3. t=940.44–940.60: racket upright beside the R shoulder; shoulders about 45° turned; the L arm points forward at the ball.
4. t=940.69–940.99: racket vertical and high behind the R shoulder; shoulders about 60° turned; the L arm still forward. The racket is carried in the R hand alone.
5. t=941.05–941.39: forward swing — the racket head **drops below the hand** (head pointing down) and swings forward with a nearly straight arm.
6. **t≈941.46 contact** at waist/hip height, in front of the R hip, arm nearly straight, ball at the strings.
7. t=941.54–941.69: racket rises to a straight-up arm above his head and drifts to his L (peak ≈941.6–941.7).
8. t=941.71–942.01: racket drops on his L side; it is back at the L hip by about t=942.1–942.3.

**Contact fraction:** t_start 940.25, contact 941.46, t_end ≈941.67 → **≈0.85 (±0.05).** The take-back is slow (about 0.8 s from first lift to the start of the forward swing), the forward swing about 0.4 s, the finish about 0.2 s.

**What is different from the neutral forehand (section 5)**
- Hit from about the service line with **no step and no travel**, only a pivot.
- Turn of about 45–60°, not about 90°.
- **One-handed prep:** the L hand never takes the racket throat; the L arm points at the ball.
- A **low, floating swing**: the racket head drops below the hand and the arm is nearly straight at contact, rather than a compact loop with a bent elbow.
- **High finish:** straight arm up over the head, then to the L, rather than a wrap behind the neck.
- Soft pace (mini-tennis) and a late contact fraction (0.85 against 0.74).

**Could not see:** a step-in on a short ball in this clip (the footwork of running into the court; section 18 has it from another clip); the ball's flight and depth (tiny); which foot is ahead during the turn; this is **one** forehand — other strokes in the same rally (t≈935.6–990) were not analysed, and I could not reliably separate forehands, backhands and volleys among them at the size he appears.

---

## 9. Backhand (neutral two-handed)

**Used:** `-Eu80hGbgVA` t=164.0–176.0 (Alcaraz, slow motion; wide shot then zoomed behind-right; ball visible at t=169.5–170.0). Feet from `DGIkkdxMrWc` t=1009.99–1011.89 (Djokovic, low two-handed backhand from behind, real time, ball visible).

**Shoulders and racket, in order (Alcaraz, video seconds)**
1. t=164.0: ready, stance about 1.5× shoulder width, racket in both hands at the belly.
2. t=164.5–165.0: racket tilts left; hands go to his L hip; shoulders turn left.
3. t=165.5–166.5: racket back and low at his L side, upper body turned; ball first visible at t=166.5 (upper right).
4. t=167.0–168.5: knees bent, hands low at the L hip, racket head pointing down-left behind the hips.
5. **t≈170.1–170.2 contact:** ball at the strings at t=170.0, racket blurred and the ball gone by t=170.5; hands at about hip height, low at his L side, arms extended.
6. t=171.0–172.5: racket sweeps up and over his R shoulder, both arms across the chest.
7. t=172.5–173.5: racket wraps behind the head (peak ≈173.0).
8. t=174.0–176.0: racket drops back to hip level.

**Feet, in order (Djokovic, real time)**
1. t=1010.19–1010.29: wide ready stance (about 1.6×), both feet flat.
2. t=1010.39: weight shifts; the racket appears at his L side.
3. t=1010.49–1010.59: stance narrows slightly, knees bend, the R heel starts to rise.
4. t=1010.69–1010.79: deep knee bend, R heel up, both hands on the racket low at the L hip.
5. t=1010.99–1011.09: both knees bent, torso inclined over the ball.
6. **t≈1011.19 contact:** ball at the strings, racket low on his L; the legs begin to extend.
7. t=1011.29–1011.39: legs extend (up on the toes) while the racket rises up and over the R shoulder.
8. t=1011.49–1011.69: racket wraps behind the head (peak ≈1011.6).
9. t=1011.79–1011.89: racket comes down behind the R shoulder.

**Contact fraction:** Alcaraz t_start 164.5, contact 170.15, t_end 173.0 → 0.66. Djokovic t_start 1010.35, contact 1011.19, t_end 1011.6 → 0.67. **≈0.66**.

**What is different from the forehand:** both hands on the racket the whole swing (visible in every frame; the L hand is the upper one); the take-back is a held "hands low at the L hip" position; contact is low on his L side; the finish is over his **R** shoulder (the dominant-side shoulder), not the L.

**Could not see:** the feet at contact in the Alcaraz clip (cropped from t=165.5); exact hand overlap on the handle at 1080p.

---

## 10. BackhandWide

**Used:** `0a_DL1I4q38` t=17.40–22.10 (Zverev, front-left view, slow motion, 720p; ball visible from t=20.20, on the strings at t=21.08).

**Feet, in order**
1. t=17.40–17.68: feet about shoulder width and close together, knees flexed, weight light on the feet; racket vertical in front of the chest in both hands.
2. t=18.00–18.28: shoulders start turning to his L; his R foot stays flat, his L foot's toe steps out.
3. t=18.56: his L foot lands wide to the side on the ball of the foot.
4. t=18.88–19.20: stance widens to about 1.5× shoulder width (visual estimate), knees bent about 120°, L foot flat.
5. t=19.20–19.88: deep wide stance held; chest turned away to his L; racket far back and low at the L hip.
6. t=20.20–20.80: forward swing; the stance narrows to about 0.8× as he pushes up and in from the lunge, both feet flat.
7. **t=21.08 contact:** both feet flat, about hip width, torso square to the camera.
8. t=21.40: feet together with the heels slightly up (small gather).
9. t=21.68–22.08: feet back to shoulder width.

**Shoulders and racket**
1. t=17.40: racket vertical in both hands; t=17.68 it tilts toward his R.
2. t=18.00–18.28: shoulders turn left, racket head moves to the viewer's right (his L), hands at the belly.
3. t=18.56–18.88: racket tilts back and up on the L side.
4. t=19.20–19.88: racket dropped low behind his L hip, farthest back at t≈19.5–19.9.
5. t=20.20–20.80: racket sweeps low-to-high from the L hip toward the front; ball at ankle height at the far left at t=20.20, near the hands at t=20.80.
6. **t=21.08 contact:** ball at the strings in front of the body, arms extended, torso square.
7. t=21.40: arms swing across to his R.
8. t=21.68–22.08: racket wraps up over his **R** shoulder.

**Contact fraction:** t_start 17.68, contact 21.08, t_end ≈22.0 → **0.79**.

**What is different from the neutral backhand:** a large lateral step with a deep, wide, low stance held about 1 s of video time; contact is low in front of the body; the stance narrows during the swing (the push-in) instead of staying put; the L-foot step lands on the ball of the foot. Hands are still both on the racket.

**Could not see:** the ball before t=20.2 (out of frame at the left); toe angles; exact frame of the L-foot landing (between t=18.28 and 18.56).

---

## 11. SliceApproach — seen in the 1b/2 re-watch (section 17), THIN on contact

The one-handed backhand slice with the player moving forward is in **section 17**: `https://www.youtube.com/watch?v=ebS3Lf25hZ0` t=3.40–18.70 — a slice hit from the baseline line, then six or seven running steps, a split-step landing near the service line and a forehand volley. **The contact is not in frame** (the back view hides the ball behind his body), so the clip is THIN on contact, not on feet.
- The first two passes covered ten other clips and none of them had a one-handed slice approach; that part stands (the backhands there were two-handed topspin or low drives, and none of Eala's practice (`vD0wO3tq6BM`) is an approach drill).
- In the 1b/2 pass Federer's slice video (`nocXg77xfTs`) turned out to be baseline practice slices with no forward travel, and the "four ways" video (`XaLwHO60Jys`) has only a forehand-side slice insert with a walk-in; both are written up in section 17 under "Seen in the cross-checks".

---

## 12. Serve

**Used:** `rxo1uEdLouY` t=178.0–181.2 (Alcaraz, slow motion, close camera in front and slightly to the side; feet and legs clearly visible). Cross-checks: `s8BvHWqlodI` t=6.3–16.1 (Sasnovich, female, slow motion, vertical); `sH3iK7Wm5EY` t=635.4–637.5 (practice serve, real time, 1440p).

**Feet, in order (Alcaraz)**
1. t=178.2–178.9: feet about shoulder width, parallel to the baseline, flat; slow rocking.
2. t=179.27: knees start to bend, weight moves to the back foot.
3. t=179.60: knees bent about 130°, both feet flat; torso arched back.
4. t=179.78–179.90: knees bent about 110–120° and loaded.
5. t=180.00: deepest bend, both feet flat and about shoulder width.
6. **t=180.10 launch:** both feet leave the ground together.
7. t=180.20–180.28: airborne, legs extended, both feet off the ground.
8. t=180.30–180.40: one leg kicks back and up behind him to nearly horizontal while the other foot reaches down to land (the L foot lands first; the right-hander's R leg is the one kicked back).
9. t=180.50: landing leg bent and planted; kicked leg still high behind.
10. t=180.60–180.80: kicked leg swings forward and steps through into the court.
11. t=180.90–181.20: running steps into the court, knees bent.

**Shoulders and racket, in order**
1. t=178.2–178.9: torso inclined forward about 30°; racket hangs low in the R hand; the L hand holds the ball at the racket throat.
2. t≈179.05–179.10 pendulum: toss arm extends forward and up; racket arm swings back and down.
3. t=179.27: racket rises behind the shoulder.
4. t=179.45: toss arm fully up at release; racket vertical behind.
5. t=179.60–179.78: trophy — toss arm straight up, body arched.
6. t=179.90–180.00: racket drops behind the back; toss arm folds down in front of the chest.
7. t=180.10–180.20: torso rotates toward the net; racket arm swings up to full extension overhead.
8. **t≈180.24 contact** (the racket is at its highest at t=180.20 and has passed through by t=180.28; the ball is not visible on the strings).
9. t=180.30: racket swings down across the front of the body.
10. t=180.40–180.50: racket arrives at the hip as the landing leg plants.

**Contact fraction:** t_start 179.05, contact 180.24, t_end ≈180.50 (racket at the hip, landing planted) → **≈0.82**.
- Sasnovich (slow motion, contact ≈13.15; the ball is just above the racket head at t=13.00): pendulum starts ≈6.3 (from my first pass at 2.1 s steps), trophy ≈10.9, racket drop 11.5–11.8, feet off the ground by about t≈12.4–12.7 (the camera crops at her shoe level, so take-off timing is approximate), landing planted ≈14.8 → ≈0.81.
- Real-time practice serve (contact ≈636.72, ball not on the strings): start 635.5, finish ≈637.1 → ≈0.76.

**What is different:** the trophy-to-launch push is explosive (both feet together, about 0.1 s from the deepest bend to leaving the ground); contact is at full extension, off the ground; the landing is on **one** foot with the other leg kicked high and back (the female serve does the same: lands on one foot at t≈14.3–14.8, other leg kicked back at t=14.8–15.7, first step in at t≈16.1). The male serve here goes straight into running steps; the female one pauses on one leg first.

**Could not see:** which exact foot is airborne in the male launch frames (the camera angle hides left vs right); the male server's recovery after t=181.2 (the camera pans away); the ball on the strings in any of the three serves.

---

## 13. Return

**Used:** `DGIkkdxMrWc` t=635.48–637.98 (Djokovic, returner on the far side, front view, 1440p, real time; a second man in a white shirt stands beside him and does not hit). The return is a **backhand-side return**: the racket and the lunge go to the viewer's right, which in this front view is his L.

**Feet, in order**
1. t=635.48–636.20: wide static stance, about 2× shoulder width, knees bent about 30°, both feet flat. I stepped t=635.5–636.38 at 0.025–0.033 s: **no hop and no airborne frame**.
2. t=636.27–636.38: racket drops to hip height while the shoulders turn left; feet unchanged.
3. t=636.43–636.57: lunge toward his L (viewer's right): his L foot steps out wide with the knee bent; weight goes onto it.
4. t=636.64–636.78: R leg trails behind; deep lunge with the racket extended.
5. **t≈636.88 contact:** ball and racket together at t=636.83–636.90 (the ball is tiny; this is the best frame I can name).
6. t=637.02–637.16: still moving forward and to the viewer's right as the racket finishes high.
7. t=637.23–637.58: small recovery steps (see RecoverCenter).

**Shoulders and racket**
1. t=635.48–636.20: hands together at the belly, racket head up and slightly forward.
2. t=636.27–636.38: racket drops toward the L hip, shoulders turn left.
3. t=636.43–636.78: racket goes out to the L side while he lunges, arm extended toward the ball.
4. **t≈636.88 contact** (±0.05).
5. t=637.00–637.10: racket vertical high on the follow-through (peak ≈637.08).
6. t=637.23: racket lowering to the R hip.

**Contact fraction:** t_start 636.25, contact ≈636.88, t_end ≈637.08 → **≈0.75 (±0.08)**. The whole return is only about 0.8 s long, with about 0.6 s before contact and only about 0.2 s of follow-through.

**What is different from the neutral backhand:** a static wide stance instead of a travelling split; the take-back is just a drop to the hip (about 0.1 s); the lunge is compact; the follow-through is short and high. Two hands, as in the neutral backhand (assumed from the swing shape; the returner is only about 1/8 of the frame high, so I cannot see his hands on the grip).

**Could not see:** the incoming serve and the server (the camera is behind the server and crops them); the grip; the exact strings-contact frame; any split-step hop (none visible).

---

## 14. VolleyForehand

**Used:** `DGIkkdxMrWc` t=835.28–839.09 (Djokovic in a white shirt, camera behind-left, real time, a few metres behind the net; the feeder hand-feeds low balls). Two volleys: A at t=837.29–839.09 (contact **t=838.09**, ball on the strings) and B at t=835.28–837.09 (contact **t≈836.15**).

**Feet, in order (A; approximate — the shoes are small in this camera)**
1. t=837.29: ready, stance about 1.2–1.3× shoulder width, knees slightly bent, both feet flat.
2. t=837.39–837.59: small turn; knees flex; the stance staggers slightly toward the ball side (R).
3. t=837.69–837.99: he sinks into the falling ball; the R knee bends deeper (about 110°); the rear foot stays back.
4. **t=838.09 contact:** weight loaded on the R side, deep knee bend, rear foot behind.
5. t=838.19–838.99: weight returns to the middle and the feet go back to about 1.2× shoulder width, flat.

**Shoulders and racket, in order**
1. t=837.29: racket upright in front of the R shoulder, head up.
2. t=837.39: racket moves slightly to the R; shoulders turn about 20°.
3. t=837.49: racket head up beside the head.
4. t=837.59: racket head extends toward the ball at head height to his R (ball visible at the tip).
5. t=837.69–837.99: he follows the ball with the racket head, which drops from eye level to knee level; shoulders about 90° turned; torso bends forward; the L arm out for balance.
6. **t=838.09 contact** at knee height on his R, arm extended.
7. t=838.19: racket whips **up and behind the head** — the finish is a high wrap, not a stop in front.
8. t=838.29–838.59: racket behind the head and L shoulder.
9. t=838.69–838.99: racket lowers to the hip; wide ready stance again.

**Contact fraction:** A: t_start 837.35, contact 838.09, t_end 838.55 → 0.62. B: 835.35, 836.15, 836.55 → 0.67. **≈0.62–0.67.**

**What is different from the groundstroke forehand:** no loop — the racket never goes below the shoulder before the ball arrives; the take-back is a tiny turn; the stroke is a downward tracking reach with a deep knee bend, not a rotation; contact is at knee height; the racket whips up behind the head afterwards (this is how Djokovic finishes these hand-fed volleys; a normal punch-and-stop volley was not what I saw).

**Could not see:** the exact foot order in the last 0.3 s before contact (the shoes are small); the feeder; a high volley (every ball in this chapter is dropped low).

---

## 15. VolleyBackhand

**Used:** `DGIkkdxMrWc` t=865.30–866.60 (Djokovic, white shirt, 1440p, real time, same hand-feed drill). Cross-check: `sH3iK7Wm5EY` t=403.30–404.00 (net-level front view).

**Feet and body, in order (DGIkk)**
1. t=865.30: standing with the feet wide and flat; racket hangs low in front of his R thigh.
2. t=865.43–865.63: racket hand moves to his L; he sinks into a deep knee bend.
3. t=865.69–865.95: both hands on the racket (L above R), racket low at his L side at knee height; torso bent forward over the ball; the rear foot is up on its toes (heel up).
4. **t≈866.05 contact:** ball at the strings at ankle-to-knee height at the lower left; the ball is at the racket at t=866.01 and gone by t=866.08.
5. t=866.14–866.40: racket sweeps up and over his **R** shoulder with both arms rising.
6. t=866.40–866.60: racket vertical and wrapped behind the head (peak ≈866.45).

**Contact fraction:** t_start 865.45, contact 866.05, t_end 866.45 → **≈0.60**.

**Cross-check (`sH3iK`, front view, a different player):** from ready (t=403.30) the racket rises on his L side at t=403.35; he lunges to his L with the L foot out wide and the knee bent (t=403.39–403.47); the racket head stays up at chest height at t=403.52–403.88; the ball is at the top right at t=403.52; the racket then sweeps down and to the right (t=403.65–403.80); wide ready by t≈404.1–404.3.

**What is different from VolleyForehand:** two hands on the racket; contact is lower; the knee bend is deeper; the finish is over the R shoulder, not the L; the take-back is a held "racket low at the L side" rather than a racket-up-beside-the-head turn.

**Could not see:** the foot-by-foot order; whether the front-view player uses one hand or two; a backhand volley at chest height (every ball in the drill is low).

---

## 16. Overhead

**Used:** `bvVXmtHt0DM` t=447.60–449.90 (Alcaraz, net-level camera behind him looking over the net, real time). Contact at **t≈449.03**.

**Feet, in order**
1. t=447.60–447.90: standing upright, feet staggered at about shoulder width, both flat.
2. t=448.00–448.40: small adjusting shuffles (foot positions change slightly) while he turns sideways, the L shoulder toward the net.
3. t=448.50–448.80: feet flat, knees bending as the racket drops behind his back.
4. **t≈448.85 take-off:** a two-foot push — both feet are clearly off the ground by t=448.90 (shoes and shadows separated at t=448.90, 448.97 and 449.03).
5. **t≈449.03 contact** in the air near the top of the jump.
6. t=449.17–449.23: both feet land (his L slightly first), knees slightly bent.
7. t=449.30–449.90: straightens to standing and recovers.
- Take-off to landing is about 0.3 s; contact comes about 0.15–0.18 s after take-off.

**Shoulders and racket, in order**
1. t=447.60–447.80: racket up in front of the chest in the R hand.
2. t=447.90–448.00: his L arm starts to rise toward the ball.
3. t=448.00–448.30: racket cocked behind the head; the L arm points up at the ball (t=448.40–448.60).
4. t=448.60–448.80: racket drops behind the back (back-scratch); the L arm tucks in.
5. t=448.80–449.00: racket swings up and forward; the arm extends fully overhead.
6. **t≈449.03 contact:** arm straight overhead, body stretched, back arched; the ball is already away from the racket by t=449.10.
7. t=449.10–449.30: racket swings down in front of the body to hip level.
8. t=449.37–449.90: arms relax; standing.

**Contact fraction:** t_start 447.90, contact 449.03, t_end 449.35 → **≈0.78** (0.72–0.82 depending on whether the first racket-up frame at t=447.60 is counted).

**What is different from the neutral forehand:** vertical rather than rotational; a two-foot jump with contact in the air; the racket drops behind the back like the serve but the L arm points at the ball first; no recovery step is needed after the landing.

**Could not see:** the ball before contact (out of frame above); the exact strings-contact frame (the ball is hidden behind the arm at t=449.03); which foot leaves the ground first (back view).

---

## Appendix — things the 2/2 chat should not assume

- **No split-step hop was seen**, including in a dedicated second look at Zverev's feet at 0.04 s steps. In every ready and return clip the feet stay on the ground until the first stride. If the game needs a hop, it will have to be authored from general knowledge, not from these clips. The longest true idle I saw is about 1.4 s (section 1); in the mini-tennis stretch I examined (t≈936–966) there is no pause longer than about a second.
- **Contact fractions run from about 0.5 to 0.85** depending on the stroke and style (0.74 neutral forehand, 0.85 slow short-court forehand, 0.66 two-handed backhand, 0.62–0.67 low volleys, 0.60 low backhand volley, 0.75 return, 0.78 overhead, 0.8 serve, 0.5–0.8 wide forehand). One number for all strokes would be wrong.
- Slow-motion clips give fractions, not seconds. Only `DGIkkdxMrWc`, `bvVXmtHt0DM` and `sH3iK7Wm5EY` are real time.
- **`SliceApproach` and the step-in `ForehandShort` now come from the 1b/2 re-watch** (sections 17 and 18, at the bottom); section 8 is still only the short-court mini-tennis version. `SliceApproach` is THIN on contact. Both new primary clips are speed-ramped or held on single images in places (each section says where), so their seconds are not real seconds.
- `yAM1j_B6yQs` contains no take-back, so it cannot support any "whole swing" fraction.
- `vD0wO3tq6BM` (Eala) was mapped but not analysed stroke by stroke; nothing here depends on it. If the animation chat wants a female cross-check, the volley/overhead work at t≈256–277 and the front-view serves at t≈385–443 are the places to start.

---

## 17. SliceApproach — one-handed backhand slice, moving forward (1b/2 re-watch) — THIN on contact

**How I watched (this section and the next).** Claude desktop built-in browser, YouTube player at the best quality that loaded (720p for `ebS3Lf25hZ0` and `nocXg77xfTs`, 1080p for `WBfw9nFojHc` and `XQYtS5u3V6Y`, 1080p–1440p for `XaLwHO60Jys`). I paused the player, stepped it to exact media times (1/30 s up to 3 s apart), drew the frames side by side with the video id and time on each, and read them by eye. A sheet was refused if an ad or a different video showed; one early 1440p sheet came out black and was thrown away and redone. Nothing was downloaded or saved; no frame is in the repo, the only copies are the screenshot cache the Claude app keeps outside it. Times are media times: reopen at `https://www.youtube.com/watch?v=<id>&t=<seconds>s`. "his R/L" = his own side; in a back view his R is the viewer's right.

**Used:** `https://www.youtube.com/watch?v=ebS3Lf25hZ0` t=3.40–18.70 (Meike Babel Tennis, "Use the backhand slice as approach shot", a 63 s vertical Short, 720p is the best it offers). The footage is a right-handed club player in a white shirt and dark shorts (the captions call him "Andre"), filmed from behind and above the baseline under floodlights, with captions and red drawn marks. Slice swing t=4.47–9.1, run-in t=9.5–12.5, split-step landing t=12.53–16.03, first volley t=16.37–17.9. (t=0–3.3 is the coach talking to the camera; the footage cuts in at 3.40.)
Cross-checks: `https://www.youtube.com/watch?v=nocXg77xfTs` t=5.0–11.65 (Federer: a slice with the contact in frame, but no forward travel); `https://www.youtube.com/watch?v=ebS3Lf25hZ0` t=52.80–57.30 (the coach's own front-view demo); `https://www.youtube.com/watch?v=XaLwHO60Jys` t=234.95–239.4 (a slice, then a walk toward the net).

**How the used clip is timed — read this first.** It is speed-ramped, not slow motion at one speed. Counting distinct images while stepping the player at 1/30 s: about 20 per second in t=3.3–5.3 (real time); a clearly new image only every 0.2–0.7 s in t=5.3–7.6 (almost frozen); a handful of images around the contact, t=7.87–8.63; about 10 per second in t=9–12.5; then two frozen stretches, t=12.53–14.67 and t=15.0–16.03 (the red circle and the caption "split stepping right here" are drawn on them); real time again in t=16.4–18.67. Video seconds are therefore **not** real seconds, and the fractions below are video-time fractions.

**Feet, in order** (back view; the two shoes are small, so left/right is read from small offsets where I say so)
1. t=3.47–3.87: right after the cut he is a couple of metres behind the baseline and walks forward toward the net (his image shrinks). Real time.
2. t=4.00–4.40: wide ready stance, about 1.7× shoulder width (visual estimate), knees bent, both feet flat. **No hop**: both feet stay on the ground.
3. t=4.47–4.93: weight rolls forward, the feet shuffle slightly, shoulders turn to his left.
4. t=5.27–7.87: he stands on the baseline line, bent forward from the hips. The front foot is flat on the line; the rear foot is behind it on its toes with the heel up. The two shoes sit almost one behind the other; from a sideways offset of about 10 px I read the front foot as his left and the rear as his right — likely, not certain. No step in the images shown (the stretch is almost frozen, so a quick shuffle could fall between them).
5. t=7.87–8.60 (contact window): same base, both feet on the ground, rear heel still up. **He hits from a set base on the baseline; the forward travel starts only after the finish.**
6. t=8.60–9.33: weight on the front (left) foot, the right foot still behind it on its toe.
7. t=9.53–9.80: first run step — the **right** foot (the rear one) swings past the left and lands ahead, about 1.3 s of video after the contact.
8. t=10.07–12.3: alternating jog steps, left, right, left and so on, about six or seven steps counting the first. Arms stay out to the sides for the first two steps (racket arm out right, left arm out left), then come down.
9. t=12.53–16.03 (frozen): the landing — a wide athletic stance about 1.4–1.5× shoulder width, both feet flat, knees bent, just behind the service line. The red circle drawn at t=14.2 is around both feet. **No airborne frame**: the moving images before it (t=11.97, 12.11, 12.25, 12.39) are jog steps and the frozen image (12.53) is already the landing, so the hop itself is not in the clip.
10. t=16.37–17.0: still wide, small adjustments. t=17.0–17.4: the right foot steps out wide to his right. t=17.43–17.9: lunge to his right with the racket arm extended — the first volley is a forehand volley.

**Shoulders and racket, in order**
1. t=3.47–4.40: racket upright at his left side in front of the left shoulder; shoulders square to the net.
2. t=4.47–4.67: shoulders turn to his left; at t=4.67 the racket lies across the body at belly height with **both hands on it**, the left hand at the throat.
3. t=4.73–4.93: the incoming ball crosses the top of the frame, high, moving right, while the racket comes to his left side.
4. t=5.27–7.87: deep forward bend from the hips (torso inclined roughly 45–60° forward at t≈6.0–7.6, visual estimate); racket low at his left, head near the ground; the left hand is still beside the throat at t=7.57 and 7.87.
5. t=7.87–8.20: the ball is visible beside his head and left shoulder in the image (the camera is above him, so it is probably low and ahead of him, not near his head); the left hand is still beside the racket.
6. **Contact — not visible (see below).** t=8.27: the left hand is now out to his left (wristband visible) and the racket is a blur at his right shoulder; the ball is above and in front of his head.
7. t=8.50–8.63: racket arm out to his right at shoulder height with the racket head above the hand; left arm out to his left; the ball is far above and still rising.
8. t=8.77–9.10: racket tilted up, arm still out right — a T-shaped finish (peak about t=8.9–9.1).
9. t=9.2–10.4: finish held while he starts to run; the racket arm then drops and carries the racket at his right side.

**Contact:** **not in frame.** From this angle the ball is behind his body during the swing, and the speed ramp leaves one image across it. It is bracketed: the last image before it (t=7.87–8.23) has the ball beside his left shoulder and the racket low at his left; the next image (t=8.27) has the racket as a blur at his right shoulder and the ball already above his head. So contact is between t=8.20 and 8.27 (one source frame), ±0.1 s. I cannot see the strings, the racket-face angle or whether the racket cut under the ball. The coach names the shot a backhand slice; what I can see agrees (racket on his left side in the take-back, left hand on the throat at t=4.67).

**Contact fraction:** t_start 4.47 (shoulders turn, racket to his left), contact ≈8.23, t_end ≈9.0 (T finish at its peak) → **≈0.8 (0.75–0.85).** Of the used clip (3.40–18.70) the contact sits at 0.32. Both are video-time numbers from a speed-ramped clip.

**What is different from the neutral backhand (section 9)**
- One hand on the racket through the swing: the left hand lets go between t=7.87 and 8.27, within one image of the contact.
- He is bent over and hits low from a set base on the baseline line; there is no step or lunge in the stroke itself.
- A T-shaped finish (racket arm out right, left arm out left) instead of the racket wrapping over the shoulder.
- Everything after the contact is travel: first step with the rear (right) foot, a jog of six or seven steps, a wide-stance landing near the service line, then a lunge to a forehand volley.

**Seen in the cross-checks**
- **Federer, `https://www.youtube.com/watch?v=nocXg77xfTs`** (Tennis Pro TV, 257 s, 720p). I stepped the whole video at 1 s (full frame) and at 2 s (player crops). The footage is t=0–237.5 (an end card follows): slow-motion practice slices from behind and to the side, about 25 s of video per slice, with the camera position changing (dissolves) at about t=42.5, 60.5, 77, 148 and 170.5. **At that sampling, in every clip he stays at the baseline (behind the line wherever the line is visible) and moves mostly sideways. I saw no forward travel after any slice and no slice hit while stepping in** — "not seen at 1–2 s steps", not "proved absent". Slice A (t=5.0–11.65, close view from behind and a little to his left, behind the baseline line, roughly 1–2 m by eye): both hands near the throat with the racket high behind his head at t=6.05–8.15; the racket drops from behind the head at t=8.15–8.5 to horizontal and out to his left at shoulder height by t=8.85; **the ball is at the racket tip at t=9.20 (contact in frame, ±0.15 s)**; the racket continues left and down at t=9.55–9.9 and hangs low at t=10.25–11.65. Both feet stay on the ground, wide, behind the line; at most a heel lift near contact. Contact fraction ≈0.8 (t_start ≈1.0 when the racket first moves, contact 9.2, t_end ≈11.3).
- **Coach demo, `https://www.youtube.com/watch?v=ebS3Lf25hZ0` t=52.80–57.30:** the coach (right-handed) enters from the right edge and walks toward the camera (a stride or two, t=53.10–53.50); both hands on the racket above her left shoulder at t=53.37–53.43 (the backhand-side take-back); at t=53.57 the picture cuts to a close-up of racket and ball that stays frozen until t≈56.4 (face open, ball resting on the upper strings; it looks like a zoomed freeze of the contact moment, but it may not be the same instant as the frames before it); real time resumes at t=56.57 with a T-shaped finish (racket arm out to her right, left arm out) while she keeps walking toward the camera. Contact is shown as a still, not timed.
- **"Four ways", `https://www.youtube.com/watch?v=XaLwHO60Jys`** (Top Tennis Training, 489 s; chapters: Method One 0, Method Two "slice approach" 145, Method Three 285, Method Four 370). Method Two is mostly the coach talking to a static camera on a blue court. The one insert with a slice followed by travel is t=234.95–239.4: a player in a white shirt with a red stripe, blue sleeves and shorts, filmed from behind during a ball-feeding drill (balls lie on the court). Racket high behind his right shoulder and left arm out to his left at t=234.95–235.60; the racket arm sweeps out to his right at shoulder height at t=235.63–235.77 (T-shaped finish); the racket drops low at t=235.80–235.87; then he walks/jogs away from the camera toward the net, t=235.95–239.4. It reads as a **forehand-side** slice (racket in his right hand, high behind the right shoulder), not the one-handed backhand asked for; the clip starts mid-preparation after a cut and I did not identify the ball at contact. Not examined: the coach's own swings in this chapter (t≈152.1–152.6, 162.8, 172.8, 181.8, 186.6) and Method Four (t=370–489).

**Could not see**
- The ball on the strings, the racket-face angle and the cut-under path in the used clip; the real-time duration of the swing (speed ramp).
- An airborne split-step hop: the clip freezes on the landing.
- The first volley's contact (t≈17.6–17.8; the ball is not visible).
- **A one-handed backhand slice approach with the contact in frame: none of the five URLs has one.** Federer's contact is in frame but he does not travel; the Andre clip travels in frame but its contact is hidden. That is why this section is THIN on contact, not on feet.

---

## 18. ForehandShort — step-in on a short ball (1b/2 re-watch)

**Used:** `https://www.youtube.com/watch?v=WBfw9nFojHc` t=64.50–68.00 (Intuitive Tennis 247, "Dynamic Forehand Footwork on a Diagonal Short Ball", a 77 s vertical Short, 1080p). A right-handed student (pink top, teal cap) filmed from behind at court level as she runs diagonally forward into a short ball and hits a forehand; the coach in white is in other cuts. The drill is shown again from a wider camera at t=69.03–72.6 and t=73.83–76.9. The net is in view just ahead of her, so the ball is short; I did not measure the distance.
Cross-checks: the wide views above; `https://www.youtube.com/watch?v=XQYtS5u3V6Y` t=49.57–54.03, t=68.6–73.47 and t=119.7–132.1; `https://www.youtube.com/watch?v=XaLwHO60Jys` (nothing usable).

**How the used clip is timed.** Real time at t=64.50–65.17 (the clip cuts in with her already running). Then three held images: **F1** t=65.17–66.07 (a red X is drawn on the court beside her right foot), **F2a** t=66.10 (about one image) and **F2b** t=66.20–66.9 (red markers are drawn beside the racket). Real time resumes at t=67.07. How much real time passes between F1, F2a and F2b is not shown.

**Feet, in order** (back view; her R/L = the viewer's R/L)
1. t=64.50–64.77: running diagonally forward, strides alternating, body leaning forward. The clip starts mid-run.
2. t=64.83: wide base, about 1.5× shoulder width, left heel up, right foot flat.
3. t=64.97: the feet come together (a gather step), both close to the ground.
4. t=65.10: the left foot is planted and the right foot swings forward, off the ground.
5. **F1, t=65.17–66.07:** the right foot is planted flat and wide, ahead, right beside the red X, knee bent about 110–120° (visual estimate); the left leg trails far behind on its toes with the heel up. Torso leaning forward and to her right.
6. **F2a, t=66.10:** the same base — right foot flat, left foot behind on the toe with the heel high, weight on the right leg.
7. **F2b, t=66.20–66.9 (contact):** right foot flat, right knee flexed; the left foot is lifted behind her, toe down, touching or just clear of the ground — I cannot tell which.
8. t=67.07 (after the hit): both feet flat, side by side, about shoulder width.
9. t=67.2–67.9: she moves on with short running steps; the feet are partly cropped at the bottom of the frame.

**Shoulders and racket, in order**
1. t=64.50–64.77: the racket is hidden behind her body; **no take-back is visible.**
2. t=64.83–65.10: racket hand low at her right side with the racket head below the hand; the left arm is out to her left (wristband visible) as a counterweight.
3. **F1, t=65.17–66.07:** racket hand at hip height at her right; the ball is ahead of and above her hand, a racket-head length or more above the strings; her head is turned to the ball; left arm out to the left.
4. **F2a, t=66.10:** racket head still below the hand and pointing down-right; the ball is a few centimetres above its top edge.
5. **F2b, t=66.20–66.9 — contact:** racket head up and the ball in line with the string bed, at hip height, ahead of her right hip (at or within a frame of contact; the strings are seen from behind). Left arm out to her left; shoulders turned to her right.
6. t=67.07: racket vertical above her head (follow-through up), left arm bent in front of her chest; the ball is gone.
7. t=67.13–67.5: the racket goes over and down behind her head (wrap) by t≈67.4–67.5.
8. t=67.5–68.0: racket brought down to her right side as she runs on.

**Contact:** **in frame.** F2b (t=66.20–66.9, one held image) shows the ball in line with the strings; F1 and F2a show the ball approaching the low racket from above and ahead. The racket-face angle cannot be read from behind.

**Contact fraction:** the take-back is hidden and the clip starts mid-run, so this is **not a swing fraction.** Indicative only: from the first frame where the racket is visible (t=64.83) to its wrap behind the head (t≈67.5), contact at 66.2 sits at **≈0.5 (±0.15)**; of the used clip (64.50–68.00) it sits at 0.49. About 1.7 s of that video time is held images, so the real-time figure is later than the video-time one.

**What is different from the neutral forehand (section 5) and the mini-tennis forehand (section 8)**
- She hits on the move: a diagonal run-in, a gather step, then a lunge onto the outside (right) foot with the left leg trailing behind. No set stance and no recovery step before the hit. Section 8 is a pivot with no step; this is the step-in.
- Contact is low (hip height) and in front of the right hip, with the racket going low to high; the finish is a high wrap, not the compact loop of section 5.
- The left arm is out to the side as a counterweight through the whole hit (section 8 points it at the ball; section 5 folds it in).

**Seen in the cross-checks**
- **Wide view of the same drill, `https://www.youtube.com/watch?v=WBfw9nFojHc` t=69.03–72.6 and t=73.83–76.9:** she starts at the baseline and runs diagonally toward the net in about 4–5 strides over about 1 s (t=69.03–70.0, my count from a small figure); the camera then cuts to a side view (t=70.18–70.97) where she is still running. The figure is small (feet readable, racket not). White circles on her feet and on the ball/racket spot are drawn on held images of the same low lunge at t=71.14–71.78 and t=75.13–76.0, with real time again right after. The coach's own demos (t=29.8–34.5 from behind, t=50.4–55.2 from the front) are shadow swings with no ball and were not used.
- **`https://www.youtube.com/watch?v=XQYtS5u3V6Y`** (2MinuteTennis, "How To Put Away Short Balls", 255 s, 1080p; a player in a blue shirt on a court with a sponsor banner, hitting put-aways near the net, with yellow lines, red arrows and circles drawn on held images). In the real-time clips (t=49.57–50.83, t=68.6–73.47, t=119.7–123.4) he is already standing in the mid-court in a wide ready stance when the clip starts — **the step in from the baseline is not in frame.** Contact appears only on held images: t=52.73 (ball at the blurred racket, above net level and to his right), t=54.03 (just after), t=126.0–129.8 and t=131.6–132.1. The camera zooms and pans, so foot placement is unreliable. THIN; not used for numbers.
- **`https://www.youtube.com/watch?v=XaLwHO60Jys`** ("four ways", 489 s): nothing usable for a step-in short ball. Method One (t=0–145) is an intro montage of five single baseline forehands by the coach in black on a clay court (t=0–9.7), then the coach talking on a blue court with shadow swings, plus short inserts (t=25.7–28.9 a player shadow-swinging; t=65.8–72.3 a player in light blue on grass filmed from behind, baseline movement and rallies — no short-ball step-in seen). The Method Three inserts (t=291–294.8, 343.2–349, 366.7–368.95) are shadow swings (no ball seen). Sampling: every 3 s over t=0–141 and 145–286, every 1.8 s over t=284–369, finer (0.1–0.5 s) inside the inserts. Not examined: Method Four (t=370–489) and the coach's swings in Method Two listed in section 17.

**Could not see:** the take-back; the strides before the cut at t=64.50; the real time between F1, F2a and F2b; the racket-face angle at contact; where the left foot lands after the hit; the feet and racket in the wide views at any useful size.
