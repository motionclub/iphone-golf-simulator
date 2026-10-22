# Six material families — implementation map

The six resources under `Unity/Assets/Resources/Environment/Materials/` establish authoring masters. Stage 3 routes representative runtime builders through `EnvironmentMaterials.Create`. Every master uses the pre-existing shader and starts at that shader's defaults; builders continue supplying textures, detail settings, instancing and vertex semantics. Exact default/pass/keyword/queue parity is tested before adoption. Missing/mismatched resources fall back to the requested original shader, never a different family.

| Master | Representative shader / builder | Retained variants |
|---|---|---|
| M_Ground | TennisWorldSurface / TennisVenueArt | GolfGround, GolfIce, sand keyword, court aggregate |
| M_Foliage | TennisBotanical / TennisVenueArt | GolfCoastalFoliage, GolfPlants, wind and coverage |
| M_Prop | HubSurface / HubClub | TennisWorldSurface stone/wood/glazing, URP metal |
| M_Water | GolfOcean / GolfLook | HubWater, TennisWater; depth, foam and reflections |
| M_Emissive | GolfLava / GolfLook | Towers/windows; existing flowing lava/cooling masks |
| M_Sky | TennisCoastalSky / TennisLook | GolfResortSky, rooftop/volcano panoramas, hub dome |

`EnvironmentSurface.hlsl` shares distance-layer behavior across ground, foliage, prop, water and emissive variants. Sky stays independently authored. Existing fog and layered haze use the stronger contribution, not two washes. Turf weather owns only chroma because WeatherGround already owns wet darkening and gloss. Hero shaders stay outside this migration; their old include in GolfGround is retained for legacy behavior but live weather uses the actual world key from stage 5.

No old shader or material asset is deleted. No new keyword variant, realtime light, shadow pass or per-frame material allocation is introduced by this migration. GPU cost still requires device measurement; the helper's distance math is not claimed to be free.
