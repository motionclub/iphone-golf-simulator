# GATE_RESULTS — MALE_PELVIS_FORM3 (candidate FORM3, staged, not installed)

GATE: MALE_PELVIS_FORM3 PASS  (visual lines = author reading; Adnan's sign-off pending)

| gate | result | evidence |
|---|---|---|
| ZONE_OUTSIDE = 0 | PASS | `export/audit_FORM3.json`: 0 moved outside PELVIS z .77–1.07 / LEG_TOP z .705–.77 (\|x\| <= .22) |
| TOPOLOGY_IDENTICAL | PASS | 66,158 tris unchanged, positions only |
| SIL bald front/back <= 5 % | PASS | 4.289 / 4.952 (`data/sil_FORM3.json`) |
| NO_SELF_INTERSECT / NaN | PASS | 0 new self-intersections (6 pre-existing), NaN 0, flipped 0, degenerate 0 |
| FRONT_SMOOTH_MOUND | PASS | front reach -0.24 mm (>= -1.0), front dihedral max 21.0° (<= 35), front lip 18.4 mm above roof min (>= 0); `proof/P01`, `P03`, `P08`, `P10`, `P20` |
| BUTT_ROUND_PEACH | PASS | rear dihedral max 30.4° (<= 35), lobe turn 13.7°/4 mm (<= 20), slot arch radius 12.1 mm (>= 9), fold V-ness -0.13 (< .35), rear lip 9.3 mm above roof min; `proof/P02`, `P05`, `P09`, `P12`, `P16`, `P20` |

Details, SHAs, caveats: `MALE_PELVIS_FORM3_RESULTS.md`. Numbers: `checks.json`, `proof/P18_gate_table.png`. Staged merge: `export/merged_fd04bc28.{blend,fbx}`, verify PASS.
