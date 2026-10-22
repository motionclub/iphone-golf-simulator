# Phase 5 — existing weather drives presentation

GATE: WEATHER TRANSITION / RESTORE PASS — Clear→each state→Clear and Rain→Storm→Fog on holes 7,17,22. Precipitation, wetness, settling and global state clear correctly; sky/fog restore exactly; authoritative wind is unchanged; exiting the scene clears globals. Test runs at scaled time ×4, so these stills do not prove real-time timing or audio.
GATE: CAPTURE PASS — 57 world and 52 hero views; 12 transition stills.
GATE: VISUAL ACCEPTANCE FAIL — face L45–65 passes 29/36 measurable normal-grid faces; silhouette dL≥15 passes 12/22 gameplay views.
GATE: DEVICE / MULTIPLAYER / AUDIO UNTESTED — device testing deferred by Adnan; no claim from editor stills.

Storm turf fixed-ROI HSL saturation changes 79.52→27.38%, lightness 32.55→32.94%. Rain saturation changes 69.89→39.58%. The shader adds chroma adjustment, while existing WeatherGround owns wet darkening/gloss. Full ROI definitions and before/after values are in measurements.json.

WeatherView remains the only transition owner. See ../tools/WEATHER_CONTRACT.md. Rain's existing precipitation value .62 now represents fully overcast hero compensation; the .20 face-bounce limit, .35 fill, .15 shadow floor and .35 rim ceiling remain.

Raw: /private/tmp/combined-style-compile/rollout/phase_05; initial matrix plus targeted hub/weather-face repair. The last effective-state entry per shot is authoritative. Normalized rain face compensation was checked again in the final full matrix.
