# Codex task: MotionSports UI redesign boards: sculpted toy style, our brand colours

Repo root: /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
Make concept boards only. Do not change code, scenes, project files or production assets, and do not commit. Claude will implement from your boards.

## Goal
Redesign every screen of the game's UI in the style of the UI overhaul package, but in the MotionSports brand palette instead of each map's own colours. The UI should feel like one friendly, tactile, party-game system: Wii / Switch Sports energy, readable from the couch and at phone distance.

## Style reference (study these first)
- `UI overhaul/01 Current UI/proof/01–15*.png`: the style to match. Note the sculpted 3D plates, raised rounded cream lettering with a dark outline and a soft drop, cream pills with a darker raised lip, one big glossy action button per screen, chunky rims around panels, generous rounding, and small flourishes at panel corners.
- `UI overhaul/01 Current UI/README.md` and `REVISIONS.md`: the rules that still apply.
- Current screens for layout and function: `UI overhaul/05 Reference maps/*.jpg` and `docs/ui-mockups/`.

## Palette (keep exactly; this replaces the per-map colours)
- Navy Ink #061A4B; Deep Navy #0B2878; Royal #003EB8; Bright #1F62D6; Lift #286EE6; Glow #78BEFF.
- Gold #F5C542; Wordmark Gold #F1B120; Gold Deep #C48812; Arc Warm #EDB15D.
- Success #34C77B; Error #FF5A5F.
- Neutrals: N700 #2A3558, N500 #6B7A9E, N300 #B7C2DC, plus white and a warm cream (~#FFF4DF) for pills and plates.

How to use it:
- Panels: Royal → Deep Navy faces with a raised rim.
- The one primary action per screen is Gold with a Gold Deep lip and Navy Ink text.
- Secondary actions are cream pills with a Navy Ink label and a Deep Navy lip.
- Light and progress use Glow.
- Lettering is cream or white with a Navy Ink outline.
- No per-map palettes. A map may appear only in its scenery and its sculpted title, never as the UI colour.

## Type
- MotionSports wordmark: Kanit ExtraBold Italic, white "Motion" + gold "Sports".
- All other UI type: chunky rounded heavy lettering (Fredoka Bold feel), raised and sculpted for titles and plates, flat and readable for data.

## Rules (from the latest requirements)
- Usernames only: no YOU, no PLAYER 1, no role badges.
- Map names stand alone; no sport-category labels (TENNIS / GOLF / BOWLING) anywhere on a screen.
- No currencies, battle pass, leagues, abilities or features the game doesn't have.
- Use sample names ADNAN, MILO and JUNE.
- Power meter, wherever it appears: a small exact percentage pill and four notches at 25 / 50 / 75 / 100 %.
- Leave room for safe areas and 44 pt touch targets.

## Boards to make
Square 1254×1254 boards, the same presentation as the reference set: a small CONCEPT label, then the screens with short captions.

1. Boot loading: wordmark, full-screen action art, LOADING… bar.
2. Home / squad line-up: PLAY bottom-left, + on empty spots, logo, focus frame.
3. Play menu: Daily Challenges, Single Player, Multiplayer, Tutorial.
4. Map chooser: all 10 maps as sculpted miniatures with names, Back and Play.
5. Match loading: art, sculpted map title, ready list, slim rail, short tip.
6. Locker: Gear and Customize tabs, item grid, colour swatches, hero preview.
7. Settings and pause: Resume, Send feedback, Leave game, Leave party, sound and haptics toggles.
8. Party / friends lobby and invites: party list, invite card, join banner.
9. Onboarding and tutorial: coach-mark tips over the menu, play-safe card, Set your direction, Timing check, Ready to play.
10. Tennis: TV HUD (scoreboard, serve meter, POINT banner, ACE / OUT / FAULT / DEUCE) and the phone controller (serve court, T / WIDE, ◀ ▶, TOSS, rally radar, stamina, emotes).
11. Golf: TV HUD (hole card, club selector, power meter, minimap, PERFECT, shot result) and the phone controller (hole / yards, club pill, drag-to-aim, TAP TO SWING).
12. Bowling: TV HUD (scorecard, LAST THROW, STRIKE!) and the phone controller (Frame · Ball, ◀ Board ▶, ball, Hold to start).
13. Results and rewards: match / hole / round complete, XP and unlock toast, Rematch, Back to Plaza.
14. Handheld play (no TV): golf and bowling with the game on top and the control deck below.
15. Component sheet: plate, cream pill, gold primary button, panel, tab, toggle, chip, progress bar, power meter, nameplate, event banner, toast. Show each in default, pressed and disabled states, with colour hex labels.

## Output
- Save PNGs to `ArtDir/ui/brand-sculpted-2026-11-16/proof/NN-name.png`.
- Save the exact prompts to `PROMPTS.md`, and any corrective edits to `REVISIONS.md`, in that folder.
- Add a `gallery.html` with no external dependencies.
- Write `GATE_RESULTS.md` with binary gates:
  - PALETTE_ONLY_BRAND: every UI surface uses only the palette above.
  - NO_SPORT_LABELS.
  - USERNAMES_ONLY.
  - ALL_15_BOARDS.
  - COMPONENTS_MATCH_ACROSS_BOARDS: the same pill, button and plate everywhere.
  - POWER_METER_4_NOTCHES.
  - READABLE_AT_PHONE_SIZE: the smallest data text is legible on a 402-pt-wide phone screenshot.
- If a gate fails, regenerate the board, and say which boards needed redoing and why.