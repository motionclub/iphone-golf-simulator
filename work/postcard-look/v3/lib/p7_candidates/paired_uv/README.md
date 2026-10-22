# Single finite paired-chart trial — overall FAIL

One UV variant was tested on the same three compact tiles, with the immutable actual `bounded_v6_source` C/N/E maps. Exact source texture and inherited BASALT_PRISMS checks remain in the frozen parent handoff. No production source, shared library, installed PNG, stage or Unity state was changed. No second chart variant was run.

`paired_columns.py` exposes `author_paired_columns(ob, seed=0, uf=.38, vf=.32)`. Input is a real compact-column mesh with original `lk_v3_columns` per-shaft vertex/face metadata. It authors original plain-zone UVs first, then replaces one pair of physically adjacent front side planes per column with one continuous perimeter chart. u follows the real counterclockwise footprint distance; both planes share one world-z phase. The corner uses an unchanged GLOW_U entry, with a whole bounded tree fitted across the actual two face widths. All six original glow lines are used overall. It creates no geometry and does not change material slots, normals or texture data.

Shared-edge UV delta is exactly0 on all45column pairs. All564vertices,372polygons and948triangles compare hash-identical before/after. Ten actual frozen Phase4 scoring meshes were loaded as hidden read-only UV controls; their mesh geometry, polygons, material indices and UV hashes also remain identical. Controls were not used to pad the scenery object-presence requirement.

| Check | Independent-face control | Paired variant1 |
|---|---:|---:|
| Side faces with decoded glow |79/282=28.0142%, PASS15–45% |90/282=31.9149%, PASS15–45% |
| Plain caps |90/90PASS |90/90PASS |
| UV_DENSITY, original full function with scoring controls |PASS |PASS; basalt0.35..0.92×contract |
| GROUND_UV_LOCAL_SMEAR, original full function |PASS |PASS; largest affected ground total5.2m²≤15, largest triangle≤10m² |
| H_GLOW top coverage |0%, PASS≤0.5% |0%, PASS≤0.5% |
| H_GLOW side coverage |2.25165%, PASS1.01240–2.42975% |**2.73695%, FAIL>2.42975%** |
| H_GLOW side area with any glow |29.3639%, PASS10–50% |35.9289%, PASS10–50% |
| Original world dash estimate |2.33333m, FAIL<2.5 |2.625m, PASS≥2.5 |
| Whole-hole H_GLOW presence |3objects, FAIL<200 |3objects, FAIL<200 |
| View0 vertical share |90.4%, FAIL>80 |48.9%, PASS |
| View+35 vertical share |84.9%, FAIL>80 |69.3%, PASS |
| View−35 vertical share |92.8%, FAIL>80 |38.5%, PASS |
| All three per-shot BASALT_JOINTS pixel predicates |AllFAIL |AllPASS |
| Aggregate junctions/100skeleton pixels |8.5864PASS |10.1380PASS |
| Geometry/scoring-control preservation |Baseline |PASS exact hashes |

Paired per-view coverage is6.50%,5.20%,7.02% (pixel limit20%); rungs0% in all views; base median26.1,23.4,28.7≤55; mean saturation.085,.062,.092≤.25. Original whole-hole H_UV_WINDOWS mesh-presence count is not present in this three-tile fixture; only its unchanged top/plain and15–45%side predicates are evaluated locally. The original H_GLOW_JOINTS function runs unchanged and reports FAIL; its exact local variables are captured without altering its predicates. Do not rename a local numerical check as a complete hole PASS.

All six before/after views, original strict gate text, exact counters, chart records and hashes are in `attempt1/result.json`, `attempt1.log` and `attempt1/*.png`. The initial runner import failed because the local helper directory was not on sys.path; that log is preserved in `runner_import_FAIL.log`. The repair changed only the import path before any fixture was built.

Visual review remains FAIL: larger complete hot graphs cross actual corners and reduce the vertical streak classification, but the source's dense central branch knots still resemble bright star shapes rather than naturally distributed geological joints. Native Game-view results remain UNVERIFIED. Numeric three-view PASS does not override this review or the side-coverage FAIL.

If a later authorized full-stage test retains the side-coverage failure, reduce the proportion of whole columns receiving a hot paired chart and keep the other whole columns in genuine plain-zone charts. Do not crop individual forks, dim pixels to game a mask or change texture/gate thresholds. For example38/45hot pairs is a planning distribution: simple proportional projection gives2.3112%side coverage and26.9504%glowing side faces, but these are not measured PASSes. Actual object area, chart placement, all three images and every original full-stage gate must decide. The single measured variant is frozen here; there are no extra parameter retries.
