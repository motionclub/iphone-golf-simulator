# Menu backdrop: random course behind the menu (2026-10-28)

Adnan's spec:
- Keep the plaza menu hero, standing straight and facing the camera, but swap the background for a random course each time the menu opens.
- Centre the hero, with the feet on the floor.
- The approved mock is the artifact "MotionSports Menus Before/After".

## How it works
- **`Scripts/Hub/Menu/MenuBackdrop.cs`**:
  - Attached by `HubWorld` in menu mode.
  - Picks one of 10 venues, never the same as last time (PlayerPrefs `menu.backdrop.last`; `MENU_BACKDROP=<venue>` or `MenuBackdrop.Pin` pins one).
  - Hides the plaza: the scenery root goes inactive, renderers under the hub get `forceRenderingOff` except the heroes, and the Majestic dressing root is turned off.
  - Draws the plate full screen, behind everything (`Resources/Menu/MenuBackdrop.shader`).
  - Re-applies the venue's sun and ambient every frame, at execution order 10010, after DreamEnvironment (10000) and MajesticVenue (10002), which drive the same light.
  - Puts a shadow catcher on the floor (`MenuShadowCatcher.shader`): main-light shadows plus a contact darkening per line-up slot.
- **`MenuShots.Centred` / `CentreShot`**: every screen holds one pose, because the plate's perspective is only right for that pose.
  - Camera 4.7 m in front of slot 0, eye 0.95 m, looking at 1.0 m, fov 32.
  - `MenuStage.PrepareArrival` skips the swoop.
- **`Resources/Menu/Backdrops/<venue>.jpg` + `<venue>_light.json`**, baked as follows:
  1. `tools/MenuVenueStand.cs` (a PlayMode test, run in a clone) launches each venue through `NativeSportsSession`.
  2. It deactivates the gameplay hero and hides the props near it (held ball, aim guide, contact shadows).
  3. It stands the plaza hero (`TennisCustomization.HeroBase`, `HubHeroAnimator`, stance 3) on the baked soles of the gameplay hero.
  4. It renders from `CentreShot`'s pose: `_raw.png` is the plate (no post), `_light.json` holds the sun direction relative to the camera, plus colour, intensity and ambient.
  5. `bake_plates.py` blurs the plate except the floor around the feet.
- **Why a plate and not the venue scene:** the plaza plus a map is what the 10-26 phone memory kill was made of. A plate is one texture (about 150 KB jpg each).

## Proof
- `proof/sheet_home_all_venues.jpg` and `proof/<venue>_home|locker.jpg`: the real menu in Unity (`tools/MenuBackdropCapture.cs`) on every venue. These captures used the committed menu UI; the new screen layouts are separate work.
- `proof/hero_light_per_venue.jpg`: the live hero lit by each venue's light.

## Re-bake
1. Run the `MenuVenueStand` test in a clone through `heavy.sh`, windowed, with `MV_OUT=<dir>`.
2. Run `python3 bake_plates.py <dir> Unity/Assets/Resources/Menu/Backdrops`.

## Pitfalls
- Hide heroes with `forceRenderingOff`, never by switching `renderer.enabled` off and on (Unity 6000.3 skin-streak bug).
- `timeScale` 0 makes `HubHeroAnimator` skip its pose and show the Ready crouch.
- An unparented menu hero gets its feet pinned to the world origin.
- Renderer bounds sit about 13 cm below the soles: use baked meshes.

## Not done / not verified
- No phone run (frame time, memory).
- The plaza is still built under the backdrop, just hidden: skipping its build would save load time and memory.
- The golf venues still have the ball on the tee near the feet, by design.
