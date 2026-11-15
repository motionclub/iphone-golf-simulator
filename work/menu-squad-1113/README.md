# Menu squad, midday lighting, focus and one-press start (2026-11-13)

Adnan, 11-13: "just do bright mid-day and make the changes. make sure the characters don't get covered by UI. also make the MotionSports logo
bigger. ... you can't really tell where you are hovering because of colours, and it's not simple to start a game".

Installed in `Unity/` (uncommitted). Undo: `./ROLLBACK.sh` (restores a file only if it is still exactly as this install left it).
Originals and new copies: `src/orig`, `src/new`. Proof boards: `proof_before_after.jpg`, `proof_focus_and_home.jpg`.

## What changed
- **Squad formation** (`MenuShots.SquadSlots`, `MenuStage.FriendsShown`): with a venue plate, you stand front and centre, friends a step back on
  each side, the fourth further back on the left. Friends stand on Home only; every screen with lists or cards shows just your hero.
- **Bright midday light** (`MenuBackdrop`, `MENU_MIDDAY=0` turns it off): one high, near-white sun from the camera's left on every venue; the
  venue's sky and ground kept, with a brightness floor; the heroes' own front fill raised for the menu (1.1, play is 0.5) and restored on leaving;
  a gentler grade (saturation 8, contrast 4, temperature 1). Tunables: `MENU_MIDDAY_SUN`, `MENU_MIDDAY_FILL`, `MENU_HERO_FILL`, `MENU_HERO_SKIN`.
- **Home** (revised 11-13 evening, Adnan: "play button on the left, bottom left ... just have the + signs in each spot"): PLAY is one gold button bottom left, lit when Home opens (Home hides the SELECT hint: PLAY carries its own A); a + INVITE floats on every empty spot (3 alone, none with a full party); down from any + is PLAY; no side scrims over the squad. Proof: proof_home_v2.jpg.
- **Sport screen**: a word list (Tennis / Golf / Bowling) left of the hero and the sport's card right of it (the full-width lanes covered the hero).
- **Logo** 46 -> 72.
- **Focus**: every lit item that is not a word (buttons, tabs, the +, segments, cards, swatches) gets a thick white frame with a breathing gold glow.
- **Start**: Home opens on PLAY, the setup on START, the loader on START MATCH as soon as the match is built. Right/down from + INVITE goes to PLAY.

## Measured (tools/MenuSquadCapture.cs, tennis-resort plate, arrow steps + Select like the phone)
| | before | after |
|---|---|---|
| presses, Home -> exhibition started | 9 | 5 |
| lit when the setup opens | PLAZA tab (Select left the setup) | START |
| lit when the match is built | Settings | START MATCH |
| hero body covered by UI (party Home) | 0-89 % | 0-1.4 % |
| hero body covered by UI (Sport) | 91-100 % | 0 % |
| leader face / arm / legs brightness | 122 / 126 / ~117 | 142 / 159 / 136 |

Light strengths filmed: shots/light2 (A-D); C picked. Neon bowling checked: shots/after5_neon.

Tests (clone ~/unity-clones/menu-squad, windowed, muted): MenuArrowFocusTests 2/2 (new: SelectAloneStartsAMatch), MenuPointerTests 5/5 (+1 skipped
proof film), MenuPhoneFillCapture 1/1 (upright + sideways phone). Not run: full EditMode/PlayMode suites, a phone/TV device run.
Capture pitfall: run MenuPhoneFillCapture in a separate launch from MenuSquadCapture (it leaves the editor window phone-shaped, which narrows the menu camera).
