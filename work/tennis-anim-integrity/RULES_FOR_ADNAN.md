# Two gameplay timing rules that cap how good the swings can look (for Adnan to decide)

Animation fixes can't fully fix these two; they're game-rule timing. Numbers come from the chat-4 match films (`/Users/adnanyonathan/tai-films`, BUGS.md B05/B06).

## 1. The player's swing starts ~50 ms before the ball is hit
In AutoPlay matches, the player's swing starts at a time-to-contact of 0.156 game-s, and `PaceToContact` then speeds the
swing up 2–3× (`swingPace` 2.3–3.1). On screen, the whole forward swing therefore has **3 frames** (50 ms). In real play the
forward swing lasts about 0.12 s (REFERENCES.md: YAAUOoMbrfM 12.73 → 12.84, racket blurred at contact).
The driver now holds the take-back fully loaded and plays only the forward swing, blending in from the pose on screen, so
nothing teleports. But the racket can't show a 0.12 s acceleration in 50 ms. That's why most player hits still fail the
CONTACT gate (the speed peaks a few frames early, at the blend).
**Options:** (a) start the visual swing when the ball is ~0.15 s from the hitting zone, before the phone swing is confirmed,
and turn it into a whiff if no swing comes; or (b) let a late swing land its contact a few frames later than now, a gameplay
change to the hit window. Both are rule changes.

## 2. The prepared wing can switch at the last moment
The rival (and sometimes the player) prepares a forehand, then the game picks a backhand ~0.18 s before contact (and vice versa).
The arm then has to cross the body in ~0.1 s, peaking at 40–50 m/s before the ball (film after_male, rival t 1152–1163).
**Option:** pick the wing earlier (from the ball's predicted side once it crosses the net), so the prepare and the swing use the same clip.
