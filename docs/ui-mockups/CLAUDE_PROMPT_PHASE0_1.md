
You are working in the Unity project at
`/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity` (Unity 6000.3.24f1, URP, landscape iPhone).

**Read first:** `docs/ui-mockups/UI_IMPLEMENTATION_PLAN.md`, then look at the mockup images in `docs/ui-mockups/`.
- **The target look** is `M_golf_aim.jpg` (and `M_final_sheet.jpg` for the whole set): E "aero glass" panels in Emerald & Gold, Inter type.
- **Exact positions, sizes and font sizes** are in `lib.js` (`holePanel`, `lieChip`, `shotMap`, `powerMeter`, `clubSelect`, `pinPill`) and `s1.js` (the golf aim scene). The units are pixels on a 1920×1080 reference. Convert them to your canvas reference and safe-area anchors.

## Rules (important)
- **Do not commit.** Stage nothing, or stage only. At the end, show `git status` and `git diff --stat`.
- **Change only UI code and assets.** Don't touch gameplay logic, cameras, 3D assets or scene layouts. Keep your changes additive and easy to revert.
- **Only one heavy job at a time.** That means one Unity batch run, build or big import at a time. Never run them in parallel.
- **Make the change bold and clearly visible at phone size.** Use real game data only, never the sample values in the mockups.
- **Keep tests light.** Add a few EditMode tests for the theme service, and keep them fast.

## How the UI works today (so you don't hunt)
- **All uGUI, built in code. There are no prefabs.** Text is legacy `UnityEngine.UI.Text`. TextMeshPro ships inside `com.unity.ugui` 2.0, but the TMP Essentials are not imported.
- **The shared kit is `Assets/Scripts/UI/UiKit.cs`:** static colors, Rubik fonts, rounded sprites and the `Label`/`Panel`/`Card`/`Pill`/`Button` builders.
- **The golf HUD:**
  - `Assets/Scripts/UI/Hud.cs`: the whole layer, including the power meter, club and aim buttons, the minimap and safe areas.
  - `Assets/Scripts/UI/GolfShotHud.cs`: distance, club, wind and the lie chip.
  - `Assets/Scripts/UI/PinHud.cs`: the pin marker.
- **Maps (just for context; the theme does NOT depend on the map):** golf courses are in `Assets/Scripts/Course/Hole.cs` (`Course.All()`: cliffside / wildisles / magma / meadow). The current one is `GameSetup.CourseId` (`Assets/Scripts/Game/GameSetup.cs`). Tennis uses `TennisVenue.Current` (`Assets/Scripts/Tennis/TennisVenue.cs`).
- **Scenes:** `Assets/Scenes/Golf.unity`, `Tennis.unity` and `Hub.unity`. They load through `Assets/Scripts/Game/NativeSportsSession.Hub.cs`.

## Phase 0: theme system (no visible change yet)
1. **Create `Assets/Scripts/UI/Theme/`** with:
   - `ThemeRole` enum: Panel, PanelStroke, PanelText, PanelTextMuted, Accent, Button, ButtonText, Rule, MeterRail, MeterFill, SweetSpot, Pearl, Dot, Shadow.
   - `UITheme : ScriptableObject`: a color per role, a 3-stop panel gradient with opacity, stroke width, shadow (color, alpha, blur, offset) and a minimum text opacity.
   - `UIThemeLibrary : ScriptableObject`: a default theme, and sport → theme ("golf", "tennis"). **No per-map or per-venue themes.**
   - `ThemeService` (static): `Current`, an `event Changed`, and `Apply(sport)`. It hooks `SceneManager.sceneLoaded`: `Golf.unity` uses "golf", `Tennis.unity` uses "tennis", and the Hub and menus use the default (golf).
   - `ThemedGraphic : MonoBehaviour`, with a role and an alpha multiplier. It recolors its `Image` or `Text` (and `TMP_Text` if present) on enable and whenever the theme changes.
2. **Create the assets in `Assets/Resources/UI/Themes/`:**
   - `Theme_Golf_EmeraldGold`:
     - panel gradient #10936B → #0B7556 → #075B44 at 95%;
     - stroke #3FBF94 2px; text #FFFFFF (minimum opacity 0.85);
     - accent, sweet spot, button, meter fill and pearl #F5C542;
     - button text #063D2D; rule #5FC7A3;
     - meter rail white at 13%; shadow #02261B at about 27%, blur 32, y +12.
   - `Theme_Tennis_RoyalBlue` (picked):
     - panel gradient #3478EC → #1F62D6 → #1950BC at 95%;
     - stroke #7DA6F6 2px; text #FFFFFF (minimum opacity 0.86);
     - accent, sweet spot, points cell, button, meter fill and pearl #FFD166;
     - button text and the numbers in the points cell #0D2C66;
     - rule #86AEF5; shadow #071E4D.
   - `UIThemeLibrary`, wiring those two together.
3. **Fonts.** Add Inter (OFL) Regular, Medium, SemiBold and Bold under `Assets/Resources/Fonts/Inter/`.
   - Preferred: import the TMP Essentials and make Inter SDF assets.
   - If that turns into a blocker, use the Inter TTFs with legacy `Text` for now and note it.
4. **The glass shape.** Make a free procedural rounded-rect `Graphic` or shader: SDF box, radius, inside stroke, 3-stop vertical gradient. Put a soft 9-slice shadow sprite under it. **No real background blur** (it's too costly on iPhone). Default radius is 24 at the 1920×1080 reference.
5. **UiKit hook.** Add an optional `ThemeRole? role` parameter to the `UiKit` panel, label and button builders. When a role is passed, add a `ThemedGraphic`. Existing calls must stay unchanged.
6. **Tests.** Write 2–4 EditMode tests:
   - `Apply("golf")` returns the emerald theme and `Apply("tennis")` returns the royal blue one;
   - an unknown sport falls back to the default theme;
   - `ThemedGraphic` recolors when `Changed` fires.

## Phase 1: golf aim HUD (bold and visible)
**Rules from Adnan:**
- **No scenery or map art** on the hole card or the scoreboard. Panels keep their normal size.
- **No-pill callouts:** feedback words (PERFECT / GREAT / NICE …) never get a pill or outline. They are just big Inter Bold white words with a soft drop shadow (see `M_golf_perfect.jpg` and `M_tennis_point_scored.jpg`). This is Phase 2 work, but don't add any new pills in Phase 1.

**Rebuild these with the glass shape, the theme roles and Inter.** Keep them at the **same screen spots as today and as the mockup**:
- **Hole card, top left (320×156):**
  - "HOLE 01 · PAR 4": SemiBold 19, caps, muted;
  - the distance: Inter Regular 60, followed by "yd to pin" at 21;
  - "Driver · 240" and the wind: 20.
- **Lie chip under it (320×70):** a ball dot, "Tee" at 26, and "CLEAN LIE" in SemiBold 15 caps.
- **Vertical power meter on the left (80×304):**
  - "POWER" label;
  - a rail (white at 13%) with a **gold sweet-spot block** near the top;
  - a gold fill with a pearl;
  - the yards value at the bottom.
  - It must still fill with the real backswing from `Hud.cs`.
- **Club picker at the bottom left (340×114):** "SELECT CLUB", then PT / DR / HY tiles. The **selected tile is a solid gold button with dark-green text**; the others are subtle.
- **Shot map, top right (268×372):** the "Shot map" title, the existing minimap image with rounded corners, and the yardage tags as small glass pills.
- **Pin pill:** "PIN 416 yd" as a glass pill, with a thin white stem down to the pin.
- **Clean-up:**
  - Remove the old navy/lime styling, chunky outlines and heavy text shadows from these elements.
  - Text must be readable on bright grass and sky.

## Check before you stop
1. Run the Golf scene, or a quick capture, and take a screenshot at the tee from the normal camera.
2. Put it next to `docs/ui-mockups/M_golf_aim.jpg`. Check that the positions and sizes match and the colors are Emerald & Gold.
3. Look at it at about 25% size: every label must still read, nothing clipped, nothing covering the ball or the player.
4. Load Tennis once, to confirm the theme switches (log the active theme) and nothing errors.
5. Report:
   - the files you changed and added;
   - before/after screenshots;
   - `git status` and `git diff --stat` (no commit);
   - anything you couldn't match.
