# Pointer menu: the Plaza as the menu's backdrop (2026-10-24/25)

Adnan approved the HTML mock (https://claude.ai/artifact/WMxHCKFRozzAcZDkPL49gi) and asked for it to be built. The walkable Plaza
becomes a Wii-style pointer menu in the MotionSports brand (Brand Guide v1.0: Kanit, white and gold two-line headlines, one gold
primary per screen, Deep Navy panels with white borders, the swing arc).

## Decisions (Adnan)
- Only the party **leader** drives the menu (local or online). Guests' TVs follow the leader's screen and cursor.
- The **TV** handles the choices: tabs, PLAY NOW, sport, mode lists, Locker categories and colours. **Detail screens stay on the phone**:
  exhibition options, course picker and holes, the full locker editor, settings, invites.
- **No TV**: the same menu, tapped with a finger. It is drawn in a 16:9 band at the top of the upright phone.
- **Kanit** comes from Google Fonts (OFL), in Unity `Resources/Fonts/Kanit` and the app's `GolfArcade/Unity/Fonts`.
- No sublines under headlines and no hint text.

## Defaults (changeable)
- Online matches hand off as soon as everyone has loaded. Solo and local matches wait for START on the TV.
- `UserDefaults hub.pointerMenu = false` brings back the walkable Plaza for a comparison.

## Where it lives
| Piece | Files |
|---|---|
| Shots and slots (data) | `Unity/Assets/Scripts/Hub/Menu/MenuShots.cs` |
| Camera and line-up | `Hub/Menu/MenuStage.cs`, `HubRemotes.Override`, `HubWorld.MenuMode` (only the plaza is built in menu mode) |
| TV menu, pointer, loader | `Hub/Menu/MenuHud.cs` |
| Brand | `Scripts/Brand/BrandColors.cs` (guide appendix), `BrandUi.cs`, `ArcGraphic.cs` |
| Bridge | `Game/NativeSportsSession.Hub.cs` (menu commands, pointer samples, held load, menu session), `NativeSportsSession.cs` |
| Phone | `GolfArcade/Unity/MenuPointer.swift` (attitude → cursor), `MenuControllerView.swift`, `MotionBrand.swift`, `HubSession.swift`, `SportsSession.swift`, `SportsHome.swift` |
| Tests | `Unity/Assets/Tests/PlayMode/MenuPointerTests.cs` (+ `FilmEveryScreen` with `ML_OUT`), `GolfArcadeTests/MenuPointerMathTests.swift` |

## Protocol
### Phone → Unity
- **`start`** gains these fields:
  - `menu`: build the menu.
  - `leader`: this phone drives the menu.
  - `soloLocked`: friends are here.
  - `playerName`, `colour`.
  - `screen`: when back from a match, open this screen with no fly-in.
- **Pointer**: binary `SportsSample` with flags `Valid | MenuPointer(4)`, plus `Touch(8)` when there is no TV.
  - `target` / `aim`: cursor x / y in -1..1.
  - `power`: greater than 0 means the cursor is shown.
  - `swing`: Select is held.
  - `swingStart`: Select press counter. A dropped release still clicks once.
- **Menu commands**:
  - `menuBack`, `menuRecenter`
  - `menuGo{mode:screen}`
  - `menuPhone{mode:on|off, reason:title}`
  - `menuParty{leader, soloLocked}`
  - `menuMirror{mode:screen|hover|x|y|shown}`
  - `menuRows{mode:"name|STATE;…"}`
  - `menuTag{remote:id, mode:tag}`
- **Kept**: `hubRemote`, `hubRoster`, `hubLook`, `hubEmote`, `hubToast`, `hubArrive`, `end`.

### Match start from the menu
`SportsSession.start` sends:
- `seamless: true`
- `bay`: the route id, or `"menu"`.
- `hold`: true for solo and local.
- `menuLabel`

### Unity → phone
- `menuScreen`
- `menuHover id|label`: the phone shows it as "Pointing at" and plays a haptic tick.
- `menuOpen <route id>`: the phone runs the existing `HubSession.useStation`.
- `menuLook slot|hex`: saved with `setOutfitHex`.
- `menuStart`, `menuCancel`: Cancel calls `session.end()`, and the existing cancel and adopt path brings the menu back on its list.
- `menuState`: leader only, at most 15 Hz. It is relayed to the party as `hubEvent "menu|…"`.

### During a held load
- The match takes `session` / `token`. The menu keeps `menuSession` / `menuToken`.
- `MenuLoadingUpdate` polls the pointer samples, and `MenuDuringLoad` accepts menu commands.
- `SportsSession.poll` forwards `menu*` events to `HubSession.menuEvent`.

## Gates
**Status:** see `proof/pointer-menu/GATE_RESULTS.md`.

**Device checks still to run:**
- Cursor feel and latency over AirPlay.
- 60 fps with 4 heroes while a match loads behind the menu.
- Kanit on a real TV.
- The no-TV band on a device.
- Two phones and two TVs in a Game Center party.
- Two CMMotionManagers during a hold (the menu pointer and the match's motion).

## Not done yet (P7, after device sign-off)
Remove the walkable path:
- rooms, doors and spots;
- the stick UI, the quick menu and `HubControllerView`'s explore view;
- the walking tests.
