# Reproduce the combined lighting pass

Use Unity 6000.3.24f1 in a scratch copy, foreground `-batchmode` with graphics. Never open the shared project for captures. These tests intentionally preserve the supplied fixed cameras; gameplay camera source and geometry are untouched.

1. Copy `EnvCombinedCaptureTests.cs.txt` to scratch `Assets/Tests/PlayMode/EnvBriefCaptureTests.cs`. Run `character-lighting/tools/prepare_capture.py SCRATCH` for the hero fixtures and diagnostic masks.
2. With `VISUAL_HERO_LIGHTING=1`, capture stage 0 as the world baseline. `VISUAL_ENVIRONMENT_STAGE=2` enables Resort/hole7; stage 3 adds masters; 4 adds all presets; 5 enables weather presentation; 6 adds effect palettes. Stage 7 uses the same implementation with expanded coverage.
3. `ENV_ALL=1` expands world shots to 111. `CHARLIGHT_ALL=1` captures 344 hero views (including eight look-dev comparisons). Set `AUDIT_OUT` to a fresh directory and use test filter `GolfArcade.PlayTests.CharLight;GolfArcade.PlayTests.EnvBriefCaptureTests`.
4. Measure PNGs with `character-lighting/tools/measure.py RAW --before RAW/paired-before`. Build world and hero sheets with `build_phase_sheets.py` and `build_hero_phase_sheets.py`. Run `report_combined.py` against the recorded SceneKit lobby-reference metrics. JPEG sheets are unretouched review copies; all numeric measurements use the PNGs.
5. `CombinedPhaseCaptureTests.cs.txt` orchestrates phase captures in order using `PHASE_ROOT`, `PHASE_FIRST` and `PHASE_LAST`. `ENV_REPAIR_ONLY=1 CHARLIGHT_WEATHER_ONLY=1` recaptures only hub and wet/fog hero cases affected by the later sky/face corrections. Preserve the initial and repair XML results and record this mixed capture provenance.
6. The weather and FX fixtures are scratch-only. Weather uses scaled time ×4 to test the existing transitions, never as a real-time timing clip. FX records actual frame timestamps; `encode_frames.swift` encodes those timestamps into an MP4. These are recipe clips, not a frame-rate benchmark.

ACES is the selected mapper for both tiers. `VISUAL_TONEMAPPER=Neutral` exists only to reproduce the comparison. With no environment or hero flag the experiment is disabled. It has not met all visual gates, so it is not enabled by default. Device verification was deferred by Adnan after the separate signed audit app lost its install connection. The saved device build is older than the final corrections and is not final performance evidence.

7. The final activation fixture covers explicit hero flags and combined stages separately, including either initializer order. The full capture run retained two obsolete hero-only expectations; use the revised fixture in character-lighting/tools, not the historical after/ copy. `EnvironmentHole14ProofTests` adds grounded diagnostic views without changing the original comparison set.

Current state after Adnan’s character-lighting reversal: environment stage7 no longer enables or tunes hero lighting. For current captures use `VISUAL_HERO_LIGHTING=0`. The pre-existing explicit hero look-dev flag remains independent. Earlier combined capture instructions and proofs describe the rejected character candidate.
