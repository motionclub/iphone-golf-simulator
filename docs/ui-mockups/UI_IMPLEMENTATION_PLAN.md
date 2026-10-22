# Party Sports UI: implementation plan (E aero-glass, color by sport)

## 1. Goal
Rebuild the in-game UI in the **E aero-glass style** (the H mockups), using **one shared set of shapes and fonts** for everything. The **colors change by sport only**. There are no per-map or per-venue themes and no scenery art:
- **Golf:** Emerald & Gold (J variant 4, exact values below).
- **Tennis:** Royal Blue & Gold, a classic true blue (the L palette; final mockups are in `M_final/`).

Keep every element where it sits today, for example the power meter on the left and the club picker at the bottom left. Keep the 3D world, cameras and game logic exactly as they are. The changes must be bold and easy to see at phone size.

## 2. What the repo has today (checked read-only)
Repo: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`. Unity project: `Unity/`, Unity **6000.3.24f1**.

- **UI tech: uGUI, all built in code.** There are no HUD prefabs and no UI Toolkit.
  - 35 scripts use `UnityEngine.UI`; none use `TMPro`.
  - Text is legacy `UnityEngine.UI.Text`.
  - `com.unity.ugui` 2.0.0 is installed. In Unity 6 that package includes TextMeshPro, but the TMP Essentials are not imported yet (there is no `Assets/TextMesh Pro` folder).
- **Shared UI kit:** `Unity/Assets/Scripts/UI/UiKit.cs`. It holds:
  - static colors: `Surface #10243D`, `Ink #FFF9EE`, `Accent #65D1D3`, `ArcadeYellow #D7F044`, and so on;
  - fonts: Rubik `Display`, `Strong`, `Ui` and `Body`, loaded from `Resources/Fonts/Club/`;
  - sprites built in code: `Rounded`, `RoundedLarge`, `Circle`, `Ring`;
  - builders: `Label`, `Panel`, `Card`, `Pill`, `Button`, `Chunky`.
  - **This is the natural place to plug in the theme.**
- **A second palette:** `Unity/Assets/Scripts/UI/Club.cs` holds the menu/club palette (`Lagoon`, `Coral`, `Green`, `Sun`, `Cream`, `Ink #16123A`, `Sky`).
- **Golf HUD:**
  - `UI/Hud.cs` (1436 lines): the whole on-screen layer, the Wii-style power meter, aim and club buttons, the results banner, the minimap, the scorecard, and safe-area handling.
  - `UI/GolfShotHud.cs`: the distance, club, wind and lie chips, plus the club card.
  - Callouts and results: `UI/PinHud.cs`, `UI/StrikeHud.cs`, `UI/ShotResultPanel.cs`, `UI/HoleOutCard.cs`, `UI/LandingBadge.cs`, `UI/RoundEventsHud.cs`, `UI/IntroGraphics.cs`, `UI/HoleGraphics.cs`, `UI/HoleLoadingCover.cs`.
- **Tennis HUD:**
  - `Scripts/Tennis/TennisHud.cs` (738 lines) has its own colors: `Navy #10243D`, `RallyCream`, `RallyLime #D7F044`.
  - It loads its font from `Resources/Tennis/UI/Fonts/Rubik-Bold`.
  - Related files: `Tennis/TennisTossMeter.cs`, `Tennis/UiGradient.cs`, `Tennis/HudClock.cs`, `Tennis/TennisJuice.cs`.
- **Phone controller.** There are two:
  - the native SwiftUI one, `GolfArcade/Unity/GolfController.swift` (`GolfControllerStyle`, fonts via `ClubFonts`, font files in `GolfArcade/Unity/Fonts`);
  - a Unity fallback, `Unity/Assets/Scripts/UI/ControllerSheet.cs`.
  - The hub controller is `GolfArcade/Unity/HubControllerView.swift`.
- **Scenes:** `Unity/Assets/Scenes/Golf.unity`, `Tennis.unity` and `Hub.unity`. They are loaded in `Scripts/Game/NativeSportsSession.Hub.cs` with `SceneManager.LoadSceneAsync`.
- **How maps are identified** (for reference only; the theme does not depend on them):
  - **Golf courses** are code, not ScriptableObjects, in `Scripts/Course/Hole.cs`:
    - `Course.All()` returns `Cliffside()` "cliffside", `WildIsles()` "wildisles" and `Magma()` "magma"; there is also "meadow".
    - `Course.ByKey(key)` looks a course up by its key.
    - The current one comes from `GameSetup.CourseId` (`Scripts/Game/GameSetup.cs`, default "cliffside") or `golf.ActiveCourseId`.
  - **Tennis venues:** `Scripts/Tennis/TennisVenue.cs` defines `enum TennisVenueKind { Resort, Skyscraper, Volcano }`. The current one is `TennisVenue.Current`, set from `NativeSportsSession.cs`.
- **Hub and menus:** `Scripts/Hub/*` (HubWorld, HubRooms, HubKit, HubShapes …), `UI/HomeScreen.cs`, `UI/Lobby.cs`, `UI/Locker.cs`, `UI/ArcadeCards.cs`.
- **Existing ScriptableObjects:** only `Majestic/MajesticLook.cs`, `Majestic/MajesticCourseKit.cs` and `Hub/HubArt.cs`. There is no theme asset yet.
- **Your UI doc** (`userdoc/doc.txt`) has guidance worth keeping:
  - one shared token layer, with no hardcoded colors per screen;
  - explicit states: normal, pressed, selected, disabled;
  - safe areas and responsive anchors;
  - presentation kept separate from game logic;
  - build golf aim first, check it on a device, then extend;
  - no neon lime, and no meaning carried by color alone;
  - big, readable numbers.
- **Where these mockups override the doc:** use Inter (the doc says Plus Jakarta), use larger radii, and use colored glass panels.

## 3. Theme system design
**`UITheme` (a ScriptableObject).** Make one per sport: `Theme_Golf_EmeraldGold.asset` and `Theme_Tennis_RoyalBlueGold.asset`. Each theme holds:
- the colors for each role (section 4), including the 3-stop panel gradient and the panel opacity;
- the panel stroke color and width, plus the shadow color, alpha, blur and offset;
- a minimum text opacity, so small labels never fade too much on colored glass;
- an optional font override (normally none).

**`UIThemeLibrary` (a ScriptableObject, kept in `Resources/UI/Themes/`)** holds:
- `defaultTheme`;
- `sportThemes`: golf maps to one theme, tennis to another.

**`ThemeService` (a static class or a small singleton):**
- `Current` is the active theme.
- `event Action<UITheme> Changed` tells components the theme changed.
- `Apply(string sport)` picks the sport theme (or the default) and fires `Changed`.
- Call it when a scene loads, in a `SceneManager.sceneLoaded` hook: `Golf.unity` uses golf, `Tennis.unity` uses tennis, and `Hub.unity` and menus use the default (golf) theme. The course and venue don't matter.

**`ThemedGraphic` (a MonoBehaviour on any `Image` or `Text`/`TMP_Text`):**
- It has a `ThemeRole role` field and an `alpha` multiplier.
- It recolors itself when it is enabled and whenever `ThemeService.Changed` fires.
- The roles are: `Panel`, `PanelStroke`, `PanelText`, `PanelTextMuted`, `Accent`, `Button`, `ButtonText`, `Rule`, `MeterRail`, `MeterFill`, `SweetSpot`, `Pearl`, `Dot`, `Shadow`.

**Hooking it into code-built UI.** The UI is built in code, so give the `UiKit` builders an optional `ThemeRole` argument. For example, `UiKit.Panel(..., role: ThemeRole.Panel)` adds a `ThemedGraphic`. You then don't have to edit every call site by hand. Screens that pass no role keep their current colors until they are migrated.

**What stays fixed across themes:** layout, sizes, radii and fonts. Only colors and opacity change.

## 4. Token values
### Golf: Emerald & Gold (picked; J variant 4, exact)
| Role | Value |
|---|---|
| Panel gradient (top → mid → bottom) | #10936B @95% → #0B7556 @95% → #075B44 @96% |
| PanelStroke | #3FBF94, 2 px, inside |
| PanelText | #FFFFFF; muted labels no lower than 85% opacity |
| Accent / SweetSpot | #F5C542 |
| Button fill | #F5C542 |
| ButtonText | #063D2D |
| Rule | #5FC7A3 |
| MeterRail | #FFFFFF @13% |
| MeterFill / Pearl | #F5C542, with a white ring on the pearl |
| Shadow | #02261B, about 27% alpha, blur 32, y +12 |

### Tennis: Royal Blue & Gold (picked; same structure as Emerald & Gold)
| Role | Value |
|---|---|
| Panel gradient (top → mid → bottom) | #3478EC @95% → #1F62D6 @95% → #1950BC @96% |
| PanelStroke | #7DA6F6, 2 px, inside |
| PanelText | #FFFFFF; muted labels no lower than 86% opacity |
| Accent / SweetSpot / points cell | #FFD166 (soft gold) |
| Button fill | #FFD166 |
| ButtonText (and the numbers in the points cell) | #0D2C66 |
| Rule | #86AEF5 |
| MeterRail | #FFFFFF @13% |
| MeterFill / Pearl | #FFD166, with a white ring on the pearl |
| Shadow | #071E4D, about 27% alpha, blur 32, y +12 |

**Tennis notes:**
- The points cell is solid #FFD166 with #0D2C66 numbers.
- The shot-charge dots are solid gold with a 5 px white ring and a small shadow.

### Callout rule: no pills (new)
- **Feedback words have no pill, banner, background or outline.** This covers PERFECT / GREAT / NICE, "You scored", "Perfect contact" and similar. Just the words:
  - Inter **Bold**, big (about 116–132 px at 1920×1080), pure white;
  - a soft two-layer drop shadow: about 0 6 28 black at 42%, plus 0 2 6 black at 30%;
  - optional sub-line in Inter Bold caps at about 34 px with the same shadow.
- **UI hints keep their small pill** ("Aim on controller", "Pin 416 yd", tags), and so do buttons.
- In code, replace `UiKit.Chunky` and the callout glass panels with a plain themed label plus two `Shadow` components (or a TMP underlay).
- Mockups: `M_final/M_golf_perfect.jpg` and `M_final/M_tennis_point_scored.jpg`.

## 5. Fonts
- **Inter** (OFL) is the only family. Bring in `Inter-Regular`, `Medium`, `SemiBold` and `Bold`, either as separate files or from the variable font.
- **Role mapping** (matching the E frames):
  - big numbers and values (416, Par, 4, scores): **Inter Regular**, large;
  - names and titles: Inter Regular;
  - small caps labels (HOLE 01 · PAR 4, POWER, SELECT CLUB): **Inter SemiBold**, uppercase, about 6% letter spacing;
  - body: Inter Medium.
- **Target: TextMeshPro with Inter SDF.**
  1. Import the TMP Essentials.
  2. Generate one SDF atlas per weight, with Latin plus the symbols ·, –, › and °.
  3. Add a `ThemedGraphic` that supports `TMP_Text`.
- **Fallback if TMP slows Phase 1 down:** point the `UiKit.Display/Strong/Ui/Body` fonts at the Inter TTFs on legacy `Text` first, then move to TMP afterwards.
- **Remove the heavy text shadows and outlines** (`UiKit.Chunky`, `Shadow` components) on themed screens. E uses clean type.

## 6. Shapes and glass
- **Shapes.** Use rounded rectangles with radius 22–28 px at 1920×1080 reference (24 is the default), pills for chips, and circles for the round buttons. Either:
  - (a) buy **Shapes** by Freya Holmér (about $20), which gives crisp anti-aliased rounded rects, strokes and soft shadows; or
  - (b) build it free: a small procedural rounded-rect shader or `Graphic` (an SDF box with a radius, an inside stroke and a 3-stop vertical gradient), plus a 9-sliced soft-shadow sprite underneath.
  - Option (b) fits the existing code-built `UiKit` sprites and costs nothing. **Recommend (b).**
- **Glass blur.** A real background blur (grab-pass or a URP blur feature) is expensive on iPhone, especially behind many panels. Instead, fake the glass with the high-opacity tinted gradient (95%), a 2 px light stroke, a soft shadow and an optional faint top highlight. At these opacities the mockups barely depend on blur. If wanted, add one shared low-res blurred screen texture later, for the hole-out and results cards only.

## 7. Phased rollout
Each phase must be bold and visible. Stage the changes, don't commit, and show screenshots.
- **Phase 0: tokens and theme service.**
  - Add `UITheme`, `UIThemeLibrary`, `ThemeService`, `ThemeRole` and `ThemedGraphic` under `Scripts/UI/Theme/`.
  - Create the Golf Emerald & Gold and Tennis Royal Blue & Gold theme assets.
  - Add the Inter fonts and the rounded-glass sprite or shader.
  - Add the optional `role` argument to the `UiKit` builders.
  - Call `ThemeService.Apply` on scene load.
  - No visual change yet, except for a debug key or log that prints the active theme.
- **Phase 1: golf aim HUD** (`Hud.cs`, `GolfShotHud.cs`, `PinHud.cs`):
  - hole and distance card at the top left;
  - lie chip under it;
  - vertical power meter on the left: rail, Emerald sweet spot in gold, fill and pearl;
  - club picker at the bottom left (PT / DR / HY, the selected club as a gold button);
  - shot map at the top right, with yardage tags;
  - the pin pill.
  - Match the H/J mockups at the same positions.
- **Phase 2: golf callouts and results.** "Perfect!" callout (`StrikeHud`, no pill: words only), ball-flight "Perfect contact" (words only, no pill), shot result (`ShotResultPanel`), putt result, hole-out (`HoleOutCard`: stroke badge, banner, scorecard, emotes, Next hole button), and `RoundEventsHud` toasts.
- **Phase 3: tennis.** In `TennisHud.cs` and `TennisTossMeter.cs`: the scoreboard, serve timing bar, vertical serve power meter, racket swing button, shot-charge dots, the "You scored" callout (no pill). Replace the navy/lime colors with theme roles.
- **Phase 4: phone controller.**
  - SwiftUI `GolfController.swift` (`GolfControllerStyle`): header, chips, map card, club card, aim pad and the swing button states.
  - Mirror the tokens in Swift as a small `UITheme` struct. The theme is chosen by the sport sent over the existing session.
  - Also update the Unity fallback, `ControllerSheet.cs`.
- **Phase 5: hub and menus.** `HomeScreen`, `Lobby`, `Locker`, `ArcadeCards`, the `Club.cs` palette and the Hub world screens.

## 8. How to verify each phase
1. Capture real gameplay screenshots from the **same camera and moment** as the mockups (golf tee aim, perfect swing, hole-out; tennis before serve, serve power, point scored, rally).
2. Put each next to its mockup (H/J for golf, K for tennis) and check that the positions, sizes, colors and text match.
3. Check at phone size by shrinking to about 25%. Every label should be readable, and nothing should be clipped or overlap the ball, the player or the target line.
4. Switch sport (golf → tennis) and confirm the colors change on load. Changing the course or venue must not change the theme.
5. Do a device test on an iPhone in landscape: notch and home-indicator safe areas, frame rate with the HUD on screen, and the touch targets on the controller.

## 9. Rules
- **Stage only, never commit.** Leave the changes staged or unstaged and show `git status` and `git diff --stat`.
- **Only one heavy job at a time on the Mac.** That means one Unity batch build, Xcode build or large import at a time. Don't run them in parallel.
- **Don't change gameplay logic, cameras, 3D assets or scene layout.** UI changes must be additive and reversible.
- **Make bold, visible changes.** Adnan judges at phone size; subtle tweaks don't count.
- **Use real game data.** Never use mockup sample values in code.

## 10. Mockups (currently on the box, not the Mac). Copy them to the Mac, e.g. into `docs/ui-mockups/` inside the repo (not staged).
- Golf, Emerald & Gold:
  - `/workspace/figma-ui/J_colors/J_golf_aim__4_emerald_gold.jpg`
  - `/workspace/figma-ui/J_colors/J_golf_holeout_par__4_emerald_gold.jpg`
- Layout reference (pure E colors). Callouts here still have pills; for callouts, follow M_final:
  - `/workspace/figma-ui/H_golf_aim.jpg`
  - `H_golf_aim_before_after.jpg`
  - `H_golf_perfect_callout.jpg`
  - `H_golf_ball_flight.jpg`
  - `H_golf_holeout_par.jpg`
  - `H_golf_putt_result.jpg`
  - `H_tennis_*.jpg`
- **Final look (use these first):**
  - `/workspace/figma-ui/M_final/M_final_sheet.jpg`
  - `M_golf_aim.jpg`
  - `M_golf_perfect.jpg`
  - `M_tennis_before_serve.jpg`
  - `M_tennis_serve_power.jpg`
  - `M_tennis_point_scored.jpg`
  - `M_tennis_rally.jpg`
- Exact geometry and font sizes (the code that drew the mockups, 1920×1080 reference):
  - `/workspace/figma-ui/G_js/lib.js`
  - `/workspace/figma-ui/G_js/s1.js`
  - `/workspace/figma-ui/G_js/s2.js`
  - `/workspace/figma-ui/G_js/s3.js`
  - `/workspace/figma-ui/G_js/s4.js` (phone)
- Palettes as JSON:
  - `/workspace/figma-ui/J_colors/palettes.json`
  - `/workspace/figma-ui/L_tennis_palette.json` (tennis Royal Blue and golf Emerald)
