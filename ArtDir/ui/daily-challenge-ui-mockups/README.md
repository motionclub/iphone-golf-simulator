# Daily challenge UI mockups

## Selected design

Adnan selected **The Friend Challenge** as the Daily Hole in One share design. It pairs the player’s score with a dated play link and shows how the invitation appears in a friend’s messages. [Mockup PNG](concepts/proof/03-friend-challenge.png) · [Editable HTML](concepts/03-friend-challenge.html) · [Review results](concepts/GATE_RESULTS.md)

## Earlier share-flow exploration

Keywords: daily challenge ui mockups, Daily Hole in One, share, one-tap share, brag text, Wordle-style, share sheet, share clip, can you beat my score.

UI mockups for **sharing a Daily Hole in One result** (golf daily challenge, PLAY → DAILY CHALLENGES). Made 2026-11-21 for Adnan; he asked for one-tap sharing like Wordle.

| File | What it is |
|---|---|
| `daily-share-mockups.html` | The mockup board (self-contained, screenshots embedded). Open it in a browser. |
| `template.html` | The same page with `{{IMG_*}}` placeholders, before the images were embedded. |
| `*.jpg` | Game screenshots used in the board (from `work/daily-hole-in-one/proof/`, resized). |

Published copy (private to Adnan): https://claude.ai/artifact/82sAb3pPHYRUEu5nuicW3f

## What the board shows
1. **Round done (phone):** total out of 3,000, one tile per shot, world rank, a big yellow **SHARE MY SCORE** button as the first focus. The TV's last card gets the same button.
2. **Share sheet:** the clip and message are ready when it opens. Wide / Tall switch, message preview, then Save video · Messages · Instagram · TikTok · X · More.
3. **A friend's Messages view:** video, brag text, link card to play today's 3 shots.
4. **The clip storyboard (about 18 s):** title plate → each shot with a points stamp → end card "2,402 · Can you beat it?".
5. **Tall 9:16 version** for TikTok and Reels: the game picture is uncropped in the middle, with the score above and the challenge below.
6. **Brag text,** one square per shot: ⛳ holed, 🟩 inside 10 ft, 🟨 10–30 ft, 🟧 over 30 ft, 🟥 water/lava/OB. It names no hole or pin position.

## Open choices shown on the board (with the recommendation)
- The clip spoils the day's line to the pin. Recommendation: share it anyway.
- Shape: Wide for Save and Messages; Tall automatically for TikTok and Instagram.
- Link target: placeholder `motionsports.app/d/<day>`. Adnan has to give the real domain or App Store link.
- Face cam: game footage only.

Instagram and TikTok don't accept a caption from apps, so the brag text is copied to the clipboard on every share.

Related: `work/daily-hole-in-one/README.md` (the challenge's rules and code).
