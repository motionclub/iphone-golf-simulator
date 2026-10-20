# Astra material review — softbox candidate

GATE: patch applicability PASS. GATE: actual material quality PENDING. Production files are owned by root; this directory is staging only.

Reference review used both user target images and all four actual broad1 front/three-quarter PNGs. Current heads still read as matte clay. The existing skin-polish lobe has a half-width near 25 degrees in normal space, so much of the forward face receives nearly the same reflection. The references have a localized soft forehead highlight with warmer side falloff and a smaller nose highlight. Widening the reflection further cannot create that separation.

`softbox.patch` redistributes reflection from the very broad wash to a moderate satin core. At smoothness 0.36, the two old lobes are approximately exponent 7.16 / amplitude .22 and exponent 69.6 / amplitude .018. The candidate keeps exponent 7.16 at .035 and uses exponent 24.48 at .40. The normal-space integrated lobe is about 27% lower while the peak is 83% higher. This gives an observable material distinction without a globally brighter face. Existing regional weighting leaves forehead/nose shinier than lips and neck. There are still two pow evaluations and no new samples or shader variants.

The exact coefficients are mirrored in Swift. Selected skin tone, relative lip/beard pigment, diffuse/wrap/subsurface, exposure, shadow values, ambient, reflection probes, rim, all geometry/normals, and the actual native lobby light recipe are untouched. The already-staged iris/sclera polish stays as it was. `VISUAL_CHARACTER_SKIN_POLISH=1` enables this candidate; default remains 0 pending actual acceptance.

Root: apply `git apply -p0 work/reference-rebuild/face-look-astra/softbox.patch`, then use `two-front-queue.json` for one matched material pair. This retains the broad1 flags and changes only output path / two-front scope. Inspect actual forehead highlight separation, nose hotspot width, lip color readability and geometry visibility. If successful, use on the final integrated geometry for gameplay/lobby proof and native export. If it makes the nose look oily or exposes ear/philtrum facets, reject rather than masking geometry with diffuse brightness.

The existing material30 native proof script can evaluate this source after fresh integrated exports; do not use old29 goldens as a geometry gate. Swift typecheck verifies host Swift source only; root's actual native render must verify Metal compilation.

## Actual composed1 review

All four front/three-quarter actuals were inspected. GATE: softbox highlight presence PASS; GATE: overall character reference quality FAIL (still in geometry integration). The forehead now has a clean identifiable highlight and the female nose has the desired small highlight. The male's camera-left cheek has an oversized warped reflection, exposing local surface waviness. This justifies the only follow-up weighting adjustment: `regional/regional.patch` reduces rough skin weight from .5 to .16, while changing the smoothness ramp so a .364 forehead keeps weight .776 vs .775. Full nose response remains 1. No light, lobe exponent, peak, diffuse or pigment changes.

GATE: regional patch applicability PASS. GATE: regional actual PENDING. Root can fold it into the next integrated capture; prior composed1 remains the visible baseline.
