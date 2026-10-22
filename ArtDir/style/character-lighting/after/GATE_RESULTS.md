# Character-lighting look-dev — GATE RESULTS

**GATE: visual acceptance FAIL.** This is staged as an opt-in experiment (`VISUAL_HERO_LIGHTING=1`). Normal builds keep the original look. No commit or push.

The cap-shadow problem improves substantially, but the broad fill and rim reduce separation from bright backgrounds. The close-ups also look flatter: the fill and highlight shoulder soften the nose/cheek shading too much. This is not ready for rollout.

| Requested gate | Before → after | Result |
|---|---|---|
| Face L45–65, a10–20, b18–30 together | 0/268 → **217/268** measurable shots pass | FAIL: 51 remain outside the box |
| No sampled face below L35 | 244 → **0** | PASS |
| Gameplay silhouette dL ≥15 | **116/168 → 9/168** pass | FAIL: major regression |
| Shirt hue within 12°, L≥25 | 227/335 → **335/335** measurable shots pass | PASS for measured samples; one distant hub shirt is too small to verify |
| Resort/lobby face and shirt within L8 | 0/4 → **2/4** heroes pass | FAIL: both golf faces remain too dark |
| No added realtime lights | **0 added**; inventories match in 44 independently captured before/after cases | PASS |
| Animation, rig, mesh assets and venue lighting preserved | Six production source files only; state checks pass | PASS |
| iPhone 60 FPS / +0.2 ms GPU budget | No on-device timing captured | FAIL: performance gate unverified |

The after face ranges are **L43.80–65.36, a7.63–21.92, b17.46–33.55**. Maximum measured shirt hue error improves **12.16° → 10.85°**; minimum measured shirt L improves **5.91 → 36.18**. Hidden or undersized faces (68 of 336 main shots) are marked N/A, never counted as passes.

## Four-hero checkpoints

Numbers are median **L / a / b**, from registered visible face skin.

| Hero / shot | Before | After |
|---|---|---|
| Male tennis, Resort | 44.96 / 9.35 / 26.21 | 56.58 / 11.56 / 21.53 |
| Female tennis, Resort | 56.93 / 8.47 / 27.19 | 60.28 / 10.51 / 21.48 |
| Male golf, hole 7 Clear | 16.18 / 10.15 / 18.55 | 48.19 / 16.47 / 28.26 |
| Female golf, hole 7 Clear | 11.06 / 6.78 / 13.39 | 45.99 / 15.43 / 29.56 |

Hole 7 male rain face L: **10.02 → 49.69**; storm: **7.75 → 50.91**. Both revised weather samples satisfy all three face-colour limits.

## Lobby parity

The reference uses the current SceneKit renderer, the §15 lighting rig, and the exact recorded skin/shirt picks. It is not the Unity hub. The golf lobby pose faces forward; gameplay still looks down under the cap.

| Hero | Face dL before → after | Shirt dL before → after |
|---|---|---|
| MatchHero_Male | 13.84 → 2.22 | 13.40 → 0.98 |
| MatchHero_Female | 10.04 → 6.69 | 17.44 → 1.03 |
| GolfKitHero_Male | 47.03 → 16.92 | 14.69 → 2.56 |
| GolfKitHero_Female | 56.01 → 18.22 | 18.75 → 0.65 |

Marked sample regions and reference images: [lobby-reference](lobby-reference/). The matched lobby faces measure L58.80 / 66.97 for tennis and L66.69 / 67.01 for golf; the bible’s old L42–50 estimate is not a matching-colour reference.

## Proof sheets

- [W1 — Volcano tennis: before / after / reference](W1_tennis_volcano_gameplay_before_after_ref.jpg): gameplay dL **11.04 → 41.38**.
- [W2 — Skyscraper: before / after / reference](W2_tennis_skyscraper_gameplay_before_after_ref.jpg): gameplay dL **15.01 → 31.46**.
- [W3 — Hole 16: before / after / reference](W3_golf_16_volcano_rim_gameplay_before_after_ref.jpg): gameplay dL **28.62 → 2.39**, a regression.
- [W4 — Cap shadow: before / after / reference](W4_golf_close_face_cap_shadow_before_after_ref.jpg).
- [Enlarged face comparisons](face_detail_before_after.jpg).
- [All four heroes in both environments](lookdev_four_heroes_both_environments.jpg).
- Matching original grids: [male tennis](grid_MatchHero_Male_after.jpg), [female tennis](grid_MatchHero_Female_after.jpg), [male golf](grid_GolfKitHero_Male_after.jpg), [female golf](grid_GolfKitHero_Female_after.jpg).
- [All-hole weather sheets](sheets/), [every measurement and failed line](measurements.csv), [machine-readable gates](summary.json).

## What changed and what was tested

Hero shaders now opt into a shared camera-side fill, cubic rim, bounded key/additional-light contribution, and ambient luminance clamp of 0.25–0.60 with saturation ≤0.35. A skin highlight shoulder prevents bright-key washout. Rain/storm get skin-only exposure compensation; warm dusk and cool Volcano get different fill colours. Presets reset between sports and follow the weather state. GolfAtmosphere only supplies the hole number to the hero profile.

The shared include is also used by golf terrain, so the new ambient/key response is explicitly compiled into only the three hero surface shaders. No new light objects, shadow maps, geometry, camera changes or venue/post changes are added. Existing ground shadow casting stays unchanged.

**GATE: capture execution PASS.** Foreground Unity PlayMode in an APFS scratch clone produced **344** beauty captures and masks: 320 golf (16 playable holes × 5 weather states × 2 heroes × 2 views), 12 tennis, 4 hub, and 8 frozen-production-pose look-dev comparisons. All four capture tests passed. The final smoke run passed **7 tests**, including three activation/venue-state checks. Results: [matrix XML](after-results.xml), [final smoke XML](final-smoke-results.xml).

The supplied capture harness is preserved as input. Its lit, layer-31 mask was replaced because layer 31 contains weather overlays. Unlit material/anatomical IDs on unused layer 28 prevent fog, hats, trousers or background from being sampled as skin. All diagnostic changes are scratch-only.

Before/after numbers come from the same rendered frame with the experiment off/on; original supplied screenshots and metrics remain untouched. Measurements use PNGs, D65 Lab, and circular shirt HSV error against the selected material colour. Silhouette is the absolute difference between median inner 3-pixel contour and outer 3-pixel ring, including equipped geometry. Its failures are retained, not replaced with a more favourable metric.

Reproduction and sampling details: [tools README](../tools/README.md). Raw PNGs: `/private/tmp/hero-lighting-lookdev/after`; source/capture provenance: [manifest](capture-provenance.json), [hashes](source-provenance.json).

The next correction to test is **separate head fill from garment/equipment fill**. Keep the successful cap illumination while restoring dark-kit contrast on bright turf; then address the remaining Volcano/dusk skin-colour misses and golf/lobby face parity. Do not increase whole-hero brightness again to solve the face gate.
