# Dream worlds — gate results

**Implementation is staged. Full acceptance remains open: human balance testing is incomplete and device performance is unverified. No commit was made.**

| Gate | Result | Evidence and limits |
|---|---|---|
| COVERAGE | **PASS** | 16 golf holes and 3 tennis venues in day, sunset, night, fog and storm: **95 configurations**, 365 full-resolution PNGs and 95 landscape previews. [Coverage](proof/coverage.csv), [raw renders](proof/final-v3). |
| VISUAL | **PASS** | Matched tee/approach/aerial comparisons for every hole; near/far/wide comparisons for every tennis venue; live fog/HUD proof. [Review sheets](proof/review) use actual game renders. Tennis “before” is reconstructed with the new environment disabled and the previous stage selected. Mesa caps and affected Magma views were recaptured after their final corrections. |
| WEATHER | **PASS** | [70 repeat-shot measurements](proof/measurements/repeat-shots.csv), native/Unity forecast parity and removed public weather overrides. Identical calm-wind iron input rolls **3.752 yd dry**, **2.364 rain**, **2.053 snow**, **3.141 ash**. Carry remains unchanged in that isolation test. Crosswind gives **7.43 / 13.18 / 23.48 yd** lateral rest offsets at 8 / 14 / 24 mph. |
| FOG | **PASS** | Shared observer-relative world/map policy, [distance measurements](proof/measurements/fog-distance.csv), overhead/approach/HUD captures and live minimap verification. Cameras and quality do not move the observer. Current ball remains visible; distant exact terrain, targets and paths are obscured. |
| HAZARDS | **PASS** | Tests cover timed warning/active state, burn substeps, exactly one penalty, safe recovery, deterministic outcomes and later moving-rock collisions after a current. [Actual stage renders](proof/hazards) and [cycle measurements](proof/measurements/vent-cycle.csv) share the collision clock. All 16,000 real-terrain placement/recovery checks passed. |
| FAIRNESS | **FAIL** | **Failed line: required human playtests have not been performed.** All 16 holes pass 1,000 seeded configurations and show positive expert-model shortcut benefit. [Paired simulations](proof/balance.csv) use 48 matched errors per skill band per hole, not human scoring data. Conservative shots now use an error-envelope search rather than nominal landing alone. Estimated expert benefit is **0.06–1.05 strokes**: the ice route is modest. Par-3 targets were moved away from the cup to reward birdie positions; the four final par-3 samples separately report hole-out counts. Human balance acceptance remains required. |
| CLOCK | **PASS** | Fixed UTC−5 across winter/summer; continuous dawn/sunset/night/midnight; snapshot/replay restoration; offline resume corrections queued to safe boundaries; host-clock protection. [Clock samples](proof/measurements/clock.csv) and integration tests. Device UTC is not tamper-proof. |
| TENNIS | **PASS** | All venues from both ends in five conditions. Tests cover symmetric physics and solver landing, game-boundary changes, host/rejoin epoch parity and cosmetic crater effects only after an existing point result. Live golf→tennis verification confirms cleared golf fog and one compositor. |
| PERFORMANCE | **UNVERIFIED — device tests waived** | No phone fps or thermal claim. [Editor counters](proof/editor-counters.csv) are diagnostic scene/submission counts, not sustained main/render/GPU timings. Existing 60→30 pacing and quality fallback remain; simulation and visibility rules do not change with quality. |
| REGRESSION | **PASS — automated scope** | **595/595 EditMode tests**, **1/1 live transition test**, successful arm64 iOS Simulator native-shell build. Existing tests cover score/drop/save, tutorials, authority/wire/reconnect, timing and split-view models. Real multi-device GameKit operation is not newly certified. |

## Build boundary

- [Final EditMode XML](proof/all-editmode-release.xml): 595 passed, 0 failed.
- [Final live scene XML](proof/runtime-transition-pass.xml): 1 passed, 0 failed. Earlier failed harness runs are retained: it initially remained in the intro and inherited the repository's classic-weather fixture. The final fixture explicitly enters gameplay and enables normal conditions.
- [Native build log](proof/native-build-release.log): `BUILD SUCCEEDED`. Six native menu previews use actual game renders.
- **A fresh Unity iOS player export was not produced.** This installation has `MacStandaloneSupport` but no iOS player module. The native-shell build does not certify a newly exported Unity iPhone runtime.

## Preservation and provenance

[Geometry invariants](proof/geometry-invariants.csv) confirm identical original ground meshes, static-obstacle hashes and collider counts on all 16 holes. Added art has no landable collision. The authored ice strip and deterministic hazards/currents are intended gameplay additions. Character/clothing assets were preserved.

[Manifest](proof/manifest.csv) hashes source and raw evidence. [Provenance](proof/provenance.json) distinguishes Editor rendering, model estimates, reconstructed baselines and native-build scope. Unrelated pre-existing work remains intact; overlapping files were staged by selecting this task's change blocks. Redundant showcase frames and task caches were removed after the workspace volume filled; all required comparison views and weather captures remain.

See [implementation notes](IMPLEMENTATION.md) and the [human acceptance checklist](HUMAN_PLAYTEST.md). Concise review sheets, representative images and machine-readable reports are staged; full raw capture directories remain available in the workspace.
