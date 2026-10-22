# Female shader pass — 2026-10-16 (PROMPT_SHADER_FIXES.md)

All images are actual renders: Unity clone Editor (`/private/tmp/female-soulful-UnityClone`), the native SceneKit lobby renderer built from the app's own `MatchHeroData/MatchHeroSurfaces/MatchHeroMotion`, and Blender lookdev (Cycles + OSL port of the Unity code). No generated images are used as proof.

BEFORE = clone shaders as they were at 14:46 (backups: `../../revisions/shader-pass-blender-20261016/`). AFTER = this pass. Both sides use the same geometry, pose, skin pick, kit colours, camera, lights and exposure; only the five material files are swapped.

## Sheets
| Sheet | What |
|---|---|
| `studio-golf.jpg` | HeroTurnaround studio, golf profile: face (Cream skin = game default pick), eye macro, coral polo |
| `studio-eyes.jpg` | Eye macro, same framing |
| `studio-tones.jpg` | Fair / Tan / Deep skin picks (selectable colours preserved, relative tone maths) |
| `studio-swatches.jpg` | Light, dark, saturated garment swatches + tennis tank |
| `studio-full.jpg` | Full body, golf (cap/glove/shoes) and tennis |
| `live-tennis.jpg` | Real Tennis scene (Tropical Open), gameplay camera + wave detail, same seed/frame |
| `live-golf.jpg` | Real Golf scene, cliffside hole 12, `DREAM_WEATHER=Clear`, wind 8 mph, impact frame 62 both runs |
| `native-lobby.jpg` | Native SceneKit lobby renderer: production payload+code vs candidate payload+code |

Raw folders: `before/ after/ before-tones/ after-tones/ live-*/ native/`. Blender lookdev: `../../lookdev-blender/` (renders `r1…r5`, `lookdev.blend`, OSL ports, `build_lookdev.py`, `render_round.py`).

## Reproduce
- Studio: `Editor/FemaleShaderReview.cs` (mirror `../../unity/FemaleShaderReview.cs`), `SHADER_REVIEW_OUT=<dir> SHADER_REVIEW_SET=core|tones`, then `GolfArcade.EditorTools.FemaleShaderReview.Run()` via `unity cmd eval`.
- Tennis: `FemaleAliveCapture.Run()` with `ALIVE_MODE=tennis ALIVE_CAPTURE_STRIDE=40`.
- Golf: same with `ALIVE_MODE=golf ALIVE_DETAIL=1 ALIVE_CAPTURE_STRIDE=24 DREAM_WEATHER=Clear FILM_WIND_MPH=8 FILM_WIND_DEGREES=90` (weather is random per run otherwise; the first golf pair was rejected for that reason).
- Native: `xcrun swiftc -swift-version 6 -O -parse-as-library work/female-soulful/native_lobby_render.swift GolfArcade/Unity/MatchHeroData.swift <MatchHeroSurfaces.swift> GolfArcade/Unity/MatchHeroMotion.swift -framework SceneKit -framework AppKit -framework Metal`, `LP_SEX=Female [LP_GOLF=1] LP_FRAMINGS=head,torso,body LP_ASSETS=<assets>`. The candidate surfaces file is `../../native-shader/MatchHeroSurfaces.swift`; candidate manifests `../../native-shader/assets/*.json` (render used production CharacterAssets with only the three female JSONs swapped in).
