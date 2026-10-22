# NEW_MENUS — Island menus, item-first locker, click-to-move controller (2026-10-03)

Product direction (Adnan, 2026-10-03): a locker that works like a cosmetics locker — customise skin tone / hair / clothes colour, and equip per-sport gear
(racket, shoes, skin/costume) — **with no gear items shipped yet**; simpler so people equip things; a controller that is **click to move, never swipe**;
menus audited and improved; characters must be the newest models and **wearing clothes** (see DRESS_MATCH_HEROES in `work/hero-dressed/`).

## What is in the app now
| area | what | where |
|---|---|---|
| Locker | **Gear** tab (sport toggle, slots Skin / Racket-or-Club / Shoes, a shelf of tiles, item colour row) and **Customize** tab (Player, Plays, Skin, Shirt, Shorts as swatch rows, "Custom" gradient panel). Camera reframes per slot. Revert, Shuffle, Done. Phone = touch, TV = same screen on the click remote. | `GolfArcade/Unity/LockerStudio.swift` (`IslandLockerScreen`), state + focus grid in `TennisMenu.swift` (`lockerRows()`, `lk-*` ids) |
| Equipment model | `LockerSlot / LockerItem / LockerCatalog` — one **Standard** item per slot, nothing else. `Player.loadout` (optional, backward compatible), `loadoutPayload(sport:)` in the launch message. | `GolfArcade/Unity/LockerCatalog.swift`, `GolfArcade/Domain/Player.swift`, `SportsSession.swift` |
| Home | Continue card first (next match in one click), Store row removed, level ring profile pill | `MotionClubMenus.swift`, `IslandScreens.swift` |
| Hub / Campaign | Lock states with reasons, rival preview, no system alert (a remote cannot answer it), New tournament behind "More" with an in-screen confirm | `IslandScreens.swift` |
| Settings | switches / segments / buttons, full-width labels, TV explainer card, Developer tab hidden in release | `IslandScreens.swift`, `TennisMenu.swift` |
| After a match | **Change court** (phone + TV), same match on another court | `TennisMenu.swift`, `TennisPlayViews.swift`, `ClubScreens.swift` |
| Remote | four arrow buttons (one step per click, hold to repeat), A / B / Home, strip showing what the TV is on | `TennisPlayViews.swift` |
| Controller | dark Island racket screen: score pill, radar, stamina, one big Dive zone, hold-to-pause, tap-to-aim serve | `TennisPlayViews.swift` |
| Safety | an unreadable `players.v1` is kept under `players.v1.unreadable.<ts>` instead of being overwritten; menu haptics honour the Haptics setting | `Domain/Player.swift`, `TennisMenu.swift` |

## Tests and proofs
* Unit: `GolfArcadeTests/LockerTests.swift` (catalog, saves, focus grid, revert, shuffle), updated `TennisCampaignTests.swift` (Home / campaign / change-court behaviour).
* Snapshots: `GolfArcadeTests/NewMenuSnapshotTests.swift` + `TennisMenuSnapshotTests/testLockerStates` write phone (402x874) and TV (1280x720) PNGs to `$MENU_SNAP_DIR`
  (`TEST_RUNNER_MENU_SNAP_DIR=<dir> xcodebuild test ...`).
* Whole `GolfArcadeTests` bundle: 351 tests (1 skipped, opt-in), 0 failures, run 2026-10-03 ~16:45 against the dressed heroes.
* Proof sheets: `proof/*.jpg` (locker and Home on phone, play flow on phone, TV screens, controller, rival portraits).

## Not done / decisions pending
* Heroes: the match heroes now wear the White kit (DRESS_MATCH_HEROES, `work/hero-dressed/`). Open there: shoe soles sit ~28 mm below the court until `HeroTennisDriver.PostProcess` adds a sole lift (one line; another session was editing that file), small skin-poke patches at the armpits / shoe toe boxes, and the poke/float gate numbers above its pre-registered thresholds.
* The Skin (costume) slot holds only Standard; colours for shirt / shorts / shoes recolour the kit live.
* No hair UI: the new bodies have no hair meshes.
* Rival portraits on the hub are now rendered from the match heroes in the roster colours (`RivalLooks.swift`); the old illustrations (`MenuArt/menu-hero-*.png`) remain on the story / ladder screens that still use them.
* Dead code (about 3.4k lines in `Unity/*.swift`, ~100 MB of unused menu assets) is not deleted.
* The phone menus show dark navy bands under the status bar and home indicator (pre-existing `TennisPhoneMenu` background).
* Golf's phone controller is still a plain Form; the first-time setup panels were restyled, not merged into one stepper.
