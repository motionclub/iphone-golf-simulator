# Majestic weather (chat W, 2026-10-17)

The weather track "W" of `work/majestic-all-maps/PLAN.md` (§3 M3–M4, §4.4), toward the targets in
`work/majestic-all-maps/refs/weather/` (W01–W16). Gates: `GATE_RESULTS.md`. Proof: `proof/`.

## What it is
One self-attaching layer (Tennis / Golf scenes), new files only:

| File | Does |
|---|---|
| `Scripts/Majestic/MajesticWeather.cs` | the driver: one state (weather + biome family + phase + level) → shader globals, light, fog cap, wind, audio beds; takes over WeatherView's drawing; tennis play window |
| `Scripts/Majestic/MajesticWeatherRules.cs` | pure rules: the look per weather × family (13 looks + tennis variants), deterministic gusts, the tennis "around play" rule, fog cap maths |
| `Scripts/Majestic/MajesticWeatherFx.cs` | what it draws itself: camera fall layer, ≤ 400 near drops outside the ball corridor, gusty petals/embers, storm wall, rainbow, sunbeams, lava bombs |
| `Resources/Majestic/MajesticWeather.hlsl` | weather inside the world materials (included by `EnvironmentSurface.hlsl`): wet + puddles + ripples + glints, snow/ash cover, frost, grass waves, cloud shadows, whitecaps, flash light, height + distance fog toward the rendered sky (gameplay fog rule kept) |
| `Resources/Majestic/MajesticWeatherFall.shader` | the fall layer (procedural rain / snow / ash in 3 depth layers, corridor cut out on screen) |
| `Resources/Majestic/MajesticWeatherDrop.shader` | near drops / flakes / petals |
| `Resources/Majestic/MajesticWeatherSky.shader` | rainbow, sunbeams, storm wall, lava bombs |
| `Scripts/Majestic/MajesticWeatherGlow.cs` + `Resources/Majestic/MajesticWeatherGlow.shader` | readability: a soft weather-driven self-light on the ball (golf + tennis) and the flag, on their own meshes; nothing in clear weather |
| `Resources/Majestic/MajesticWeatherReflect.shader` | tennis only: the wet court's screen-space mirror (depth + opaque colour; the colour copy is requested only while the court is wet) |

### How it hooks in (no edit to WeatherView)
- `WeatherView` keeps its job: weather state, timing, strikes, thunder, rules. While the layer is on, its three
  full-screen volumes (`Cloud dome`, `Ground fog`, `Wet ground`) get `forceRenderingOff` and its five particle
  systems are paused + hidden, found by child name. Off = put back exactly (paused particles resume).
- Light: after DreamEnvironment and chat 9's signature light (`DreamEnvironment.AfterApply`, re-ordered to run last).
- Sky: raises the rendered sky's `_Cloud`, scales chat 2's `_RSkyAerial` (distant scenery hazes with the weather),
  URP fog capped so the ball, flag and players get ≤ 15 %.
- Wind: publishes `_WindDir/_WindStrength/_Gust` and scales `_GolfWind` (grass, palms, trees, flags, bunting, sails)
  after MajesticVenue writes it (execution order 10003). Gusts are a deterministic function of the session seed
  and the shared environment clock.
- Audio: drives the game's ambience beds (`EventSounds.SetAmbience`) from the same state; `MajesticWeather.Beds`
  and the `MajesticWeather.AudioCue` event are the hooks for chat 8's future Ambience bus.
- Dormant until the shader hook is installed (`Resources/Majestic/MajesticWeatherHook.txt`, written by the patch).
  `MAJESTIC=0` or `MAJESTIC_WEATHER=0` switch it off for a run; `MajesticWeather.SetEnabled(false)` at runtime.

### Adnan's decisions (10-17)
1. Holes 10 and 16 draw the ash family → `Weathers.SkyOf` patch (gameplay: wet-weather roll/bounce on those two
   holes changes from the sea values 1.6/1.3/.7 to the ash values 1.2/1.12/.85, as on 21–23).
2. Tennis weather wraps around play: on arrival, between games, after the match. During a rally nothing falls,
   flashes or blows (rain stops, lightning holds, fog thins to a haze); the court stays wet. WeatherView's strike
   clock is held during play so no thunder lands mid-rally.
3. Signature hour: chat 9's, unchanged; the weather dims and tints it.

## Shared-file edits (chat 6)
`tools/patch_shared.py apply|remove|check <Unity dir>` (idempotent, exact rollback; diffs in `patches/`):
- `Resources/Environment/Shaders/EnvironmentSurface.hlsl`: one `#include` + four guarded early-outs
  (`if(_MajWeatherOn>.5h) …`). With the layer off the original code runs.
  Puddles, lava pools (ash) and ice pools (snow) live here too (Adnan 10-17: "realistic puddles, lava puddles").
- `Course/Shaders/GolfRock.shader`, `GolfBotanical.shader`, `Environment/LuminousCoast/CoastalPine.shader`: a lite include
  (`MAJESTIC_WEATHER_LITE`, no extra texture) + `MixFog` → `MajesticWeatherMixFog` (== MixFog when off): wet rocks, snow on pines.
- `Course/Shaders/GolfOcean.shader`: `MajesticWeatherWater(...)` marks water pixels, so whitecaps never land on low ground.
- `Scripts/Course/RoundEvents.cs` `Weathers.SkyOf`: 10 and 16 → `Sky.Ash`.
- `Resources/Majestic/MajesticWeatherHook.txt` (+ .meta): wakes the layer.

## Install / rollback
```bash
work/majestic-weather/tools/install.sh            # new files only (dormant without the hook)
work/majestic-weather/tools/install.sh --patch    # + the shared-file edits (chat 6)
work/majestic-weather/tools/install.sh --remove   # rollback both
```
Tooling (clone only): `tools/sync.sh` (clone + files + patch + `tools/make_orig.py`: unpatched `__orig` shader twins for the same-frame off-path proof), `tools/run.sh <out>` (MajesticWeatherShots through
heavy.sh; env `MW_SLOTS`, `MW_JOBS`), `tools/sheets.py <run>` (ref sheets), `tools/gates.py <runs…>`.

## Proof
`GATE_RESULTS.md` (round 3; rounds 1–2 in `proof/`); final stills + sheets `proof/final2/`; muted videos `proof/videos/`; off-path tables `proof/offpath_final.md`.

## Round 3 additions (10-18)
- **Global keyword `MAJESTIC_WEATHER_ON`** (`multi_compile_fragment`, added to 11 world shaders by the patch). `MajesticWeather.hlsl` is wrapped in it with pass-through macros, so with the layer off the shaders are the original code. `MajesticWeather` sets the keyword only while active.
- **`MajesticWeatherGlow.cs` + `MajesticWeatherGlow.shader`:** additive self-light shells on the ball (golf `Ball`, tennis `Tennis ball`) and the flag, scaled by how much light the weather takes.
- **`MajesticWeatherHalo.shader`:** a soft dark disc behind the ball facing the camera (rim) plus a flat one under it (contact shade).
- **Off-path proof:** `tools/make_orig.py <Unity> <clone>` writes `__orig` twins (unpatched sources) and `__pat` twins (patched sources, the control); `Editor/MajesticWeatherShots.cs` job `offpath` swaps them in one frozen frame (`MW_OFFPATH_NOAO=1` turns SSAO off, which otherwise adds swap speckle).

