# Local Body-correspondent weight transfer — rejected

GATE: reusable tennis underarm closure FAIL. Neither weight profile is approved for Assets or runtime adoption. Preserve mask2 and the existing original Top weights. The independently verified Forehand1 `local-cloth-frontcull/UnderarmTrace_Female.json` remains only a single-pose checkpoint, not a whole-motion clothing pass.

## Scope and evidence

Both candidates replay the exact 165 female motion samples (33 clips × 5) from `proof/reference-rebuild/character-motion-matrices17/matrices`, each front and rear: 330 views. `raster-front.dylib` uses the corrected Unity front-facing triangle winding. Body mask2 and the original 10 SleeveFit anchor arrays are retained. Top rest positions, normals, UVs, triangle indices, bone names, and bind matrices are unchanged. This is a source gate; these rejected profiles were not copied to Assets or captured in Unity.

| Source candidate | Regional skin pixels before → after | Views with new interior holes | Largest new hole | Maximum new background | Largest posed vertex movement |
|---|---:|---:|---:|---:|---:|
| Cuff-protected transfer | 30,864 → 30,748 | 0 | 0 px | 44 px | 114.3 mm |
| Coherent inner cuff + adjacent panel | 30,864 → 42,832 | 16 | 5 px | 970 px | 273.3 mm |

Regional counts localize exposed Body pixels; they are not all automatically cloth penetration. External silhouette shrink is not rejected by itself. The gate fails from persistent target stripes and visibly displaced cuffs, with new interior holes in the coherent candidate.

## Exact weight mismatch and its limit

The Body surface closest to the inner sleeve in the rest pose belongs mostly to the torso. For traced Top vertex 10671, the original LeftUpperArm weight is 0.974409; exact barycentric Body correspondence supplies LeftUpperArm 0.294741 and Chest 0.614991. Vertex 8185 changes from arm 0.971351 toward 0.279918. Those points are only 4.84 mm and 4.46 mm from a cuff component. Adjacent torso panel vertices 7883/7848 carry original arm weights 0.064580/0.024931. Thus the source facets bridge a sharp sleeve-to-torso binding transition.

The first transfer protected the near-cuff endpoint, leaving Forehand1 front regional exposure at 452 → 452 pixels. The coherent transfer synchronizes coincident aliases and changes 1,250 cuff vertices plus the adjoining panel. Forehand1 front falls only to 329 pixels, while EmoteSpike1 front rises from 324 to 1,318 and the cuff slides toward the torso. The maximum posed movement reaches 273.3 mm. Rest geometry preservation does not preserve a sleeve’s posed anatomical attachment.

This rejects nearest-rest-surface Body transfer as the correspondence rule for this region. It does not prove that no local weight solution exists. The measured 97% versus 28% mismatch is evidence of different surface roles, not proof that the sleeve endpoint should inherit the torso’s 28% weight.

## Representation limit and next source direction

The proven Forehand1 field closes the 20–25 mm depth deficit, but the same displacement direction and six-mode extension do not hold across crossed-arm and overhead poses. The current sparse fields cannot safely represent the range of local deformations. Full all-pose results are in `reusable-underarm/ACTIVATION_GATE.json` and `underarm-basis/source-fit-report.json`; neither is a reusable passing model.

A structural next check should preserve arm-bound cuff endpoints and torso-bound panel endpoints, then add local underarm surface degrees of freedom between them (a small tessellated gusset with pose-aware clearance against the Body). Rest-surface barycentric subdivision can preserve the original silhouette and UVs. Intermediate bindings must be selected by sleeve/torso role and evaluated on all motion samples rather than copied from the nearest rest Body point. This is a proposed direction, not an authored or proven solution. No additional weight sweep is justified by the present evidence.

## Provenance

- `author_body_weights.py` and `audit_body_weights.py`: cuff-protected candidate and complete source replay.
- `author_body_coherent_weights.py` and `audit_body_coherent_weights.py`: continuous local cuff/panel candidate and complete source replay.
- Each candidate folder has `author-report.json`, `source-motion-report.json`, `source.npz`, `UnderarmWeights_Female.json`, and selected paired source PNGs.
- `body-coherent-weights/female_EmoteSpike_1_front.png`: visible cuff slide and increased exposed skin.
- `body-coherent-weights/female_Forehand_1_front.png`: target remains despite partial reduction.

- Rejected `body-correspondent-weights/UnderarmWeights_Female.json` SHA256: `fb80af3a89980fccf74080a97e27cbbea22a06d19f71431e2c28503067cf0713`.
- Rejected `body-coherent-weights/UnderarmWeights_Female.json` SHA256: `e4f97191e9e2c459132ebe670bd5a0b6cf9f8da81dffeda768a82a149782055e`.
