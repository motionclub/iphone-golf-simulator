# Menu UI to the approved mock (ba_template2), 2026-10-28

Real Unity captures (clone `~/unity-clones/menu-ui`, windowed PlayMode, `MenuAllCapture.cs` in this folder, MS_OUT), 3D + UI alpha-composited. Contact sheet: `proof/contact_sheet.jpg`.
Preview VideoPlayers render grey or see-through in captures (a known capture artifact). The hero/camera framing comes from the clone's copy of MenuStage/MenuShots, which is not the centred-hero version (another agent owns that).

| Gate | Result | Proof |
|---|---|---|
| Kanit only, nothing heavier than ExtraBold; headlines = BrandUi.Headline (white + gold, ink underlay) | PASS | all |
| Lists/headings left (x 64–~730), pop-ups right (x ≥ 1190), hero column 800–1120 clear of UI | PASS (modes, setup, players, locker, clubhouse, loading). Sport lanes cover the full width, as the mock does | 03–12, 14 |
| Menu items are words; hover = gold skewed slash, nudge right 15 px, ink text, siblings dim | PASS | 01b, 03, 04 |
| Home: PLAY 138 px + gold TENNIS · GOLF · BOWLING, then INVITE FRIENDS | PASS | 01, 01b |
| Sport: flat navy field removed; dim + three skewed lanes with venue art; the hovered lane widens and shows its modes | PASS | 02, 02b |
| Modes ×3: word list left + skewed preview card right; bowling now has a preview (its venue stills) | PASS | 03, 04, 07, 10 |
| Setup: skewed segments, stepper, gold START MATCH / TEE OFF bottom-left, court card + skewed strip right | PASS | 05, 06, 09 |
| Players: huge skewed 2/3/4 cards right; the hovered one gold and lifted; tip line left | PASS | 08 |
| Locker: word rail left with ↗ PHONE tags, big skewed swatches right, gold ring + lift on the hovered/picked one | PASS | 11 |
| Clubhouse: 4 entries with sublines | PASS | 12 |
| Phone modal: full dim, big phone glyph, title, gold caption | PASS | 13 |
| Loading: mixed-case mode title (not the mode id), readable subline, skewed gold bar, venue card right; Ready: huge gold READY! + START MATCH | PASS | 14, 15 |
| Chrome: text tabs + gold skewed underline, skewed name/settings chips, Ⓐ SELECT Ⓑ BACK hint (back still hit-testable), side scrims | PASS | all |
| Skew via a reusable mesh effect (`MotionSports.Brand.Skew`), not rotated rects | PASS | BrandEffects.cs |
| MenuPointerTests | 4 pass, 1 skip (FilmEveryScreen, ML_OUT unset), 1 FAIL `PlayNowThenTennisThenExhibitionOpensItOnThePhone`. It fails identically on the original code (it expects menuOpen; Exhibition has set up on the TV since 10-26) | Logs |
| MenuSetupCapture (MS_OUT set) | FAIL `no item sport-tennis on home`. It fails identically on the original code: its Press reads TryCentre once, straight after a Shot, so the centre is stale | Logs |
| MenuAllCapture | PASS | proof/ |
| EditMode "Menu" filter (MenuFocusTests ×3, OnlineRoomTests ×1) | 4/4 PASS | Logs |
