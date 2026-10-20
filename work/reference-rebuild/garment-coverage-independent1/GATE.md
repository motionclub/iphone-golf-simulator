# Independent garment mask coverage diagnostic

Work-only audit completed on the original approved polo profiles with the
proposed additional Body render masks. No Assets, garment source or author
data were edited. Complete Body vertex arrays/weights were used; source-proof
display crops were excluded. Exact posed Kit_Bottom was included so waist
coverage is evaluated as an outfit rather than falsely exposing omitted shorts.

## Finite source checks

- Tennis: 330 captured pose matrices, four views each, 42.63 seconds. Body
  triangle indices are identical between the mask author's cloth14 source and
  the current-matrix canonical source. Masks map all 6,284 male / 2,892 female
  physical faces. Original ten-anchor Top vertices match the canonical mesh
  within 0.3 micrometres.
- Golf: 310 evaluated poses, four views each, 33.60 seconds. New masks omit
  1,043 male / 1,065 female baseline Body faces, with the hem-safe floors
  1.095 / 1.10m. Baseline Golf Body is already culled; the comparison evaluates
  only the *additional* mask, not every legacy coverage decision.
- Raster: 900px orthographic upper-outfit framing, binary pixel-centre coverage,
  Body/Bottom CullBack, original Top CullBack and a two-sided Top control.
  Inputs are hashed in `input-manifest.json`; mask hashes are in each report.

## Interpretation and concrete findings

Lost combined silhouette is **not an automatic failure**: removing skin that
protrudes beyond a polo is intentional. The original first-pass FAIL wording
was corrected. Diagnostic face IDs preserve those edge changes for visual
review; they must not be restored indiscriminately.

Flood-filled enclosed changes also include enlarged preexisting limb gaps.
`worst-region-classification.json` compares component occupancy against the
baseline for the eight worst plates, without another full catalog run.

- Tennis MatchLose 1/2 and SadPointLost 1/2 worst changes enlarge existing
  arm–torso background openings; none creates a new isolated hole. EmoteSpike
  is an external axilla/side contraction. These require material-aware shape
  review rather than numerical rejection.
- Golf male Iron 021 rear introduces a new isolated 98px opening with Top
  CullBack. Two-sided Top restores it entirely. The three other worst Golf
  plates enlarge existing small cloth openings; those changes are also
  restored by two-sided Top.
- Across all 1,240 Golf views, two-sided Top leaves at most 7 changed pixels
  per view (8 views have tiny residual changes). The largest original Top
  culling coverage gain is 911px once Bottom is included. This supports the
  root's actual combined-mask / two-sided-material trial; it is not runtime
  acceptance.

## Recommended bounded actual gate

Use the same original meshes and the opt-in masks at the current settled
camera. Compare CullBack and two-sided original Top on Golf male Iron follow
through (sample 021), female PitchingWedge follow-through (sample 022), and
Tennis male Serve, Forehand and hands-on-hips / lowered-arm emotes. Check
checkerboard/backdrop visibility, cuff arm continuity, neck/hem anatomy and
underarm seams; separate intended skin-bulge removal from missing exposed
anatomy. Approve the candidate only after actual material-aware renders.

This audit does not certify skin bleed, fold shading, every intervening frame,
all perspective views, native performance or final art quality. No more full
catalog source audit runs are planned until the actual candidate works.

## Reproduction

From repository root:

```sh
clang++ -O3 -dynamiclib work/reference-rebuild/garment-coverage-independent1/raster.cpp -o work/reference-rebuild/garment-coverage-independent1/raster.dylib
python3 work/reference-rebuild/garment-coverage-independent1/audit.py
python3 work/reference-rebuild/garment-coverage-independent1/classify_worst.py
```

`*-diagnostic-face-indices.json` gives the source Body face indices and view
counts for silhouette changes and enclosed-background changes. These are
review flags, not proposed replacement masks.
