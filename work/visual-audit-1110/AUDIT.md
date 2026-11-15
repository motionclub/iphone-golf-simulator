# Visual audit — 2026-11-10

What the game looks like today, from fresh captures of the working tree (FN7 installed, uncommitted), compared with the approved targets. Nothing in `Unity/` was changed: every capture ran in a throwaway copy of the project.

**Captured:** tennis (3 venues, a 50 s autoplayed rally with every hit, HUD), golf (16 holes: tee, aerial, green, golfer close-ups, strike and splash, result screens), bowling (4 venues, a 3-ball film), all 15 menu screens, the plaza and locker room, and studio turnarounds of the six heroes. About 1,100 frames in `shots/`; contact sheets in `review/`.

**Compared against:** the tennis concept video, `ArtDir/hero/targets-2026-10-12` (clothing-v2, tier1), and `work/bowling-look/refs/targets`.

Each finding names the roadmap item it belongs to: 2 hit and ball VFX, 3 characters sitting in the world, 4 bowling venue, 5 clipping sweep, 6 glass UI, 7 faces, 8 phone sharpness.

## A. Looks broken

### 1. The menu hero is bright yellow with a washed-out face — item 3
![menu hero](evidence/01_menu_hero.jpg)

- **(1)** Skin renders saturated yellow and the eyes read as closed at menu size. The same hero under neutral studio light (middle panels) has brown skin and clear eyes, so the model is fine and the menu light and grade are the cause.
- **(2)** The shirt is a flat red shape with almost no shading.
- **(3)** On the sport picker the hero's head pokes out above the cards.
- This is the first thing every player sees, on all 15 menu screens.

### 2. Golf fog weather floods the hole with one flat colour
![golf fog](evidence/02_golf_fog.jpg)

- **(1)** With SEA FOG or VOLCANIC SMOKE the fairway, green and sky turn solid yellow, orange or white. On hole 20 the green itself is yellow.
- **(2)** The shot map is an empty dark box on exactly those holes (07, 10, 13, 20).
- Seen on 4 of 16 holes in this run, through the game's own weather roll. I have not checked how often it rolls in a real round.
- The fog volume is built in `Unity/Assets/Scripts/Game/WeatherView.cs`. This is a bug outside the eight items; I would fix it alongside item 3.

### 3. Characters ignore the venue's light — item 3
![character lighting](evidence/03_character_lighting.jpg)

- **(1)** Volcano court, rear camera: the rival is blown out to solid orange.
- **(2)** Volcano court and the lava golf holes: the player is lit as if in daylight and reads as pasted on. The night skyscraper court has the same problem.
- **(3)** In sunlight the skin goes flat orange with no form shading. The tier1 target calls this out as the "before" state.
- **(4)** Tennis ground shadows are faint on the resort court and not visible in the skyscraper and volcano frames, so players float. White socks and shoes render cream.

### 4. Bowling: Club Lanes is mostly black, and the pin camera is blown out — item 4
![bowling](evidence/05_bowling.jpg)

- **(1)** Walls and ceiling are a black void; the target is a warm, fully dressed lounge.
- **(2)** The scoreboard permanently covers the top quarter of the screen with empty boxes.
- **(3)** Pins on the pin camera are overexposed white with no detail. Neon Nights does the same. There is no visible effect when the ball hits the pins.
- **(4)** Crowd skin renders grey-white in all four venues.
- **(5)** The bowler's shirt shows dark vertical streaks down the front. **(6)** Empty hands rest in a claw curl.
- Tiki Shores is the strongest venue; Magma and Neon are dark but dressed.

## B. Far from the approved target

### 5. Tennis hit feedback is much weaker than the target — item 2
![tennis vs target](evidence/04_tennis_vs_target.jpg)

- **(1)** A PERFECT hit is a small white burst and pale rings on a blue court. The target has a large pink-orange ring, sparks and a tall glowing ball trail. The game shows no ball trail in rally frames and no dust at the feet.
- **(6)** A won point cuts to an empty piece of court with "YOU SCORED". The target has a WINNER popup, confetti and the player celebrating to camera (also item 7).
- **(5)** The net breaks into black vertical bars at 720p (item 8).
- Golf is in better shape here: the strike has a starburst, ring and turf, and the water splash reads well.

### 6. Tennis framing and palette have drifted from the target — your call
- The player fills about 23 % of the frame height; in the target about 35 %.
- The court is saturated royal blue on deep green. The target is powder blue on terracotta with a softer, warmer grade.
- Your earlier instruction was to preserve gameplay-camera framing, so I am listing this, not proposing it.

## C. UI — item 6

![ui](evidence/06_ui.jpg)

### 7. HUD elements sit on top of the action
- **(6)** The tennis timing bar is drawn across the player's feet, and it stays up during the intro card.
- **(4)** In handheld golf the hole title card overlaps the club selector and the "next shot" text. This came from a test that jumps between states, so it needs one check in a real round.
- In landscape golf the second player stands behind the power meter.
- **(7)** The serve power meter is the largest object on screen.

### 8. Result screens and controls do not match the glass HUD
- **(1)** The round card is unbacked text over trees, with the golfer standing in the table.
- **(2)** Three button styles appear across the result screens. **(3)** The shot result shows an empty blue pill.
- **(5)** The handheld controls are flat navy squares.
- Tennis grade text ("PERFECT · BACKHAND · 63 km/h") is too small to read at TV distance.

## D. Character detail

![hands and cloth](evidence/07_hands_cloth.jpg)

### 9. Hands — item 5
- **(1)** The female racket hand is thin tubes wrapped round the grip with gaps between them.
- **(4)** The male lead hand at golf address reads as a mitten.
- This is mesh work, the slow kind for me. A grip-pose fix may hide most of it at gameplay distance.

### 10. Cloth in direct sun — your call
- **(2)** The FN7 gloss you liked reads as vinyl in golf close-ups under full sun.
- **(3)** The trouser crease map looks crumpled at the knee.

### 11. Faces — item 7
- No reaction close-up exists at a won point, so there is nothing to judge yet. Studio faces are good on both heroes.

## E. Minor
- Rain is hard white lines, and white slash streaks cross the tennis sky.
- The golf courses mix faceted low-poly pines with smooth characters; the white domes are untextured; the lava ground is a fine speckle that may shimmer on a phone.
- A black disc beside the golf ball at address reads as a hole.
- The plaza signs still say MOTION CLUB (`HubArt.cs:657`, `:724`) and the plaza locker mirror is a blank panel. These matter only if the plaza still ships.

## Not covered
- **Phone sharpness and frame rate (item 8):** needs a device run.
- **Cloth and hand clipping across all clips (item 5):** that sweep is its own job.
- Online and party screens, onboarding and lessons, emotes, the female menu hero, and the female golfer in game light.
- PlayMode film tests (`BrollCaptureTests`, `MenuSetupCapture`) hang in batch mode because they wait for end-of-frame; the menu walkthrough ran windowed and muted instead.

## Capture-tool quirks I left out
- One resort venue angle sits inside a palm frond.
- Bowling heroes hold a racket in the studio turnaround.
- The App Store golf shot labels hole 7 as hole 1.
- The tennis HUD capture sets its own "MOTION CLUB · TENNIS" label.

## Suggested order for items 2–8
1. **Item 3 first, with the fog bug.** One lighting and shader pass covers findings 1, 2, 3 and the skin part of 10.
2. **Item 2:** tennis hit ring, ball trail, step dust, point-won beat.
3. **Item 4:** Club Lanes room, pin-camera exposure, crowd skin.
4. **Item 6:** move the timing bar, back the result screens, restyle handheld controls.
5. **Items 5 and 7:** clipping sweep, grip poses, reaction close-ups.
6. **Item 8** on a device.

## Files
- `evidence/` — the seven marked boards (`boards.py` rebuilds them).
- `review/` — unmarked contact sheets per area.
- `shots/` — every capture, by job.
- `run_stream.sh`, `jobs_a.txt`, `jobs_b.txt`, `run_menus.sh` — the capture runner; `tools/VisualAuditFilm.cs` is the rally film script (copy into a clone's `Assets/Editor`).
