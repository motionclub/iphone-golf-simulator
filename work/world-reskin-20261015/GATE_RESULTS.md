> Current golf implementation: **Dream Coast revision 2**, following the user’s rejection of this first pass. Read [revision2/GATE_RESULTS.md](revision2/GATE_RESULTS.md). The results below describe the historical first pass; its screenshots and native build do not represent the latest golf source. Tennis remains on that first pass.

# Luminous Coast pilot — gate results

Scope: Resort tennis and authored golf hole 12 only. Both pilots are enabled by default in the working game; `LUMINOUS_COAST=0` restores the baseline for comparison. The user explicitly accepts 30 fps when 60 cannot be maintained and asked to skip physical-device testing. No commits or production deployment.

## Gates

- **GATE: Unity render/compile PASS.** Final real scene captures completed without C# or shader errors. See `final.json.results.json` and `default-on.json.results.json`; the latter confirms default-on behavior without an opt-in flag. These are actual Unity renders; generated images are source textures, never substituted for proof.
- **GATE: Before/after evidence PASS.** Same gameplay/reveal cameras, matched image dimensions. Final golf comparisons use the same 8 mph / 45° wind. Animated water and NPC phase can vary. Full-resolution originals are in `proof/before-final` and `proof/after`; portrait tennis is in `proof/portrait-before` / `proof/portrait-after`.
- **GATE: Golf collision and rules data PASS.** All 161 obstacles, obstacle hash `f66789056e9c646408c10b9f2651f6dfd3b88935e43fb061480a4caa95139eaf`, 14 collision meshes and their transformed vertices/indices are exactly equal before/after. Sources: paired `golf/hole12_audit.json`.
- **GATE: Tennis court geometry PASS.** Court mesh hash `67b8b0a42e70bcafb48e3394b683789adec0c4ed068888995cb3986b50a6eea1` and rendered court height `0.0499998815` are equal before/after. Tennis uses analytic gameplay rules; its zero MeshCollider count is not itself a collision proof.
- **GATE: Scope isolation PASS.** After loading pilot golf12 and transitioning to golf7, no pilot root/material remains, the original GolfResortSky is restored, and collision hash matches baseline. Skyscraper tennis has zero pilot roots/materials and retains TennisRooftopSky. The final default-on golf12 → golf7 audit matches the earlier after audit exactly. See `proof/default-on/golf/exit-to-hole7-audit.json` and `proof/portrait-*/skyscraper/audit.json`.
- **GATE: Existing regression suite PASS.** 63/63 tests, including the new frame-budget policy and input-rate checks: environment look, Cliffside, course catalog, surfaces, obstacles, tennis rules and chase camera. See `proof/regression-30fps.xml` (original art suite: `proof/regression.xml`).
- **GATE: Native art build/install PASS (before the final fallback change).** Unity 6000.3.24f1 export and Release iPhone Xcode build succeeded. Bundle `com.aloniewski.GolfArcade.CoastReview` installed on paired iPhone17 Pro Max. See `device/xcode-final.log` and `device/install-final.json`.
- **GATE: 30 fps fallback policy PASS.** Three consecutive two-second windows with at least 10% late drawn frames lower the target from 120 to 60, then 60 to 30. An eight-second initial grace excludes loading; four-second settling follows a target change. The policy does not raise the rate again during the pilot. Further existing quality reductions are available if 30 fps is still late. No simulation time-scale changes. EditMode policy tests pass; runtime behavior has not been measured on a phone.
- **GATE: Physical-device performance NOT MEASURED — waived by user.** User: “if it cant run 60 it can be 30” and “skip this” in response to the unlock/testing request. No stable 30 or 60 fps claim is made. The earlier locked-phone attempts are historical evidence, not measured FPS failures.

## Actual automatic-frame workload

| Pilot view | Before draws | After draws | Before triangles | After triangles | Before / after SetPass |
| --- | ---: | ---: | ---: | ---: | ---: |
| Resort tennis, 960×540, crowd instancing on | 400 | 399 | 2,855,451 | 2,847,905 | 73 / 72 |
| Golf12 tee, 900×1600 | 133 | 114 | 3,475,428 | 3,447,974 | 46 / 39 |

Counters come from three consecutive completed sole-camera automatic Metal frames and agree with UnityStats. These include render passes, so they are not unique mesh counts. Golf's final turf scale/normal tuning came after this measurement; it changes uniforms only, not draw submissions or mesh counts. Native GPU cost still needs measurement.

## Delivered visual changes

- Shared coastal panorama with detailed limestone islands and cloud layers; bounded sky shader with derivative-safe wrap.
- Warm key/cool ambient balance, local water palette, quieter ocean surface and removal of the visible golf water overlay seam.
- Sapphire tennis acrylic and coordinated teal runoff, preserving the explicit player court-colour override.
- Muted golf turf palette, shorter physical cut grass, finer ground atlas, limestone detail, four Blender-authored opaque pine variants at existing tree positions. Instanced trees retain the original gameplay obstacle data.
- No additional realtime lights, reflection cameras, transparent foliage layers or new colliders.

## Limits and verification status

This is a scoped mobile art pilot, not a claim of console AAA parity. Distant islands are a panorama and have no translation parallax. Existing weather logic is retained. Device frame pacing, GPU timing and thermal behavior remain unmeasured by the user's instruction; neither stable 30 nor stable 60 fps is certified.

The installed CoastReview build contains the completed art and timing recorder, but predates the final 30 fps fallback. The working Unity source includes the fallback for the next build. No further phone connection, unlock or testing is required for this task.

Historical optional tooling remains in `device/`: the 180-second collector saves timing JSON after 150 seconds, outside its 120-second active-play window. `analyze_performance.py` is a strict 60 fps evaluator, not the current acceptance gate now that 30 fps is acceptable. Its synthetic unit tests do not constitute device evidence. Lock-state files and the earlier missing-data FAIL report are retained as history.
