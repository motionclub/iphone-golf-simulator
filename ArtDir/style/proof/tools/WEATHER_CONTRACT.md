# Presentation weather ownership

**Current update:** Adnan reversed character lighting on 2026-10-15. The hero-specific integration described below is historical and removed; world weather behavior is retained.

`WeatherView` remains the only transition owner. It supplies already-blended wetness, settled precipitation, precipitation, darkness and mist to `WeatherDirector.Publish`. Atmosphere blends over 4 seconds, precipitation 3, fog 5; wetting uses 8 seconds and drying 30; snow/ash settling 14 and clearing 40. These code paths are unchanged.

The adapter clamps globals to 0–1: `_EnvironmentWetness` for chroma-only turf desaturation; `_EnvironmentSnow` only for the snow biome; `_EnvironmentStorm` for normalized storm amount; `_EnvironmentWeatherEnabled` for opt-in stage ≥5. Existing WeatherGround still owns wet darkening/gloss and ash/snow deposition. No duplicate darkening layer is introduced. Snow's existing 0.6 darkness scale is reversed only to identify storm strength, not to change its world lighting.

Hero settings use the same amounts: ambient ceiling .60→.46 in mist/storm, mist rim strength →.25, precipitation shifts rim cool; skin light exposure is 1 + .28 × min(precipitation/.62, 1) + .17 × storm. The face-only bounce uses max(min(precipitation/.62, 1), mist) as its weather activation, because softened overcast shadows no longer reliably trigger cap occlusion; the same luminance mask and 0.20 maximum remain. Hero ambient floor remains .12 and fill .35. No independent weather timer or wind writer was added.

`Restore`, disable and new-hole setup reset all adapter globals. The transition test exercises Clear→each state→Clear and Rain→Storm→Fog on holes 7,17,22, then scene exit. It accelerates scratch time ×4 and asserts the original scaled-time blending; these stills are not real-time clip or multiplayer/network verification. Existing RoundEvents tests remain the rules authority.

Hub scenery uses layered haze without linear fog, preserving the painted Unlit sky dome. The shared fog helper treats URP’s no-fog variant as zero venue veil (URP returns zero from ComputeFogIntensity there); it does not interpret disabled fog as full opacity.
