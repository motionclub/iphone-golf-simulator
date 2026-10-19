# Phase 7 — full reachable roster and final review

GATE: CAPTURE COVERAGE PASS — 111 world views and 344 hero views,  plus two above-ground hole 14 diagnostics. All seven capture test methods passed. Three tennis venues, hub and all sixteen selectable golf holes are represented; golf heroes cover all five weather states. Eight fixed-pose views place all four heroes in Resort and hole 7.

GATE: HERO VISUAL ACCEPTANCE FAIL.

| Check | Final result | Required |
|---|---:|---:|
| Face L | 216/268 measurable views | L 45–65 in every measurable view |
| Gameplay silhouette | 52/168 | dL≥15 everywhere; initial FIX target at least 110/168 |
| Lobby face parity | 19/268 | within 8 L of recorded lobby reference |
| Darkest 5% | 13/168 | mean L 3–12 per gameplay hero |
| Saturation | mean 0.6823; 114/168 individual views | at least 0.62 |
| Detail | mean 12.223; 168/168 | at least 6.8, estimator provisional |

Sixty-eight normal-grid faces are hidden or too small to measure and are not counted as passes. Face chroma additionally passes 126/268 under the bible's a/b ranges. Measurements use unlit ID masks and native PNGs; review JPEGs are not measurement inputs. The supplied detail threshold did not specify an estimator; the documented Lab-L Laplacian RMS is a comparison aid, not an independently established acceptance method. Per-shot failures are in combined-gates.json.

GATE: WORLD ART ACCEPTANCE FAIL — contrast increases in the measured Resort close scene (Lab P 90–P 10: 47.88→50.60) and golf07 tee (55.96→59.43), and distance haze is now layered by preset. These changes do not establish a match to r1–r5. Dense fog still reads too much as a veil; silhouette separation, near-black clothing and reference-level scene finish remain unresolved. No visual or shipping acceptance is claimed.

GATE: HOLE 14 DIAGNOSIS PASS — original approach/green audit cameras are 3.58/5.66 yards below sampled terrain. Supplemental fixed diagnostic cameras sit 3/6 yards above local ground and show the supporting land. Original comparisons are retained; no production camera, terrain, collider or hole layout was changed. See hole14/sheets and hole14/results.xml.

Meadow Run is not selectable in the current Unity roster: Course.All contains Cliffside, Wild Isles and Magma; Course.ByKey has no meadow entry and GameSetup falls back to Cliffside. Its legacy builder exists, but adding a gameplay entry is outside this rendering pass. No JumpToHole(1–3) coverage is claimed.

GATE: DEVICE PERFORMANCE UNTESTED — explicitly deferred by Adnan. High/Low editor checks verify ACES, bloom/DOF policy and no-fog near-surface parity; they do not prove 60 fps, thermal endurance, complete Low material parity or GPU cost. Target remains 60 fps on all tiers.

The full capture XML contains two obsolete hero-only activation assertions that expected off even with environment stage7 enabled. Capture methods themselves all passed. The replacement suite tests both opt-ins, stage disable/enable and initializer ordering separately; see ../final-activation-order-results.xml. The original failing XML is retained rather than relabeled.

Proof: sheets/ (111 BEFORE | AFTER | REF); heroes/ (phase 6→7); heroes/expanded/ (full roster against the initial hero correction in the original world); heroes/review/ (same-frame hero-isolation comparisons, masks and individual frames); modern_detail_board.jpg; capture-provenance.json. The experiment remains opt-in while the visual gates fail.
