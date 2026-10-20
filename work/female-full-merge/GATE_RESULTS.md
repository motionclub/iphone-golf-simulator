# GATE_RESULTS - FEMALE_FULL_MERGE (work/female-full-merge)

**GATE: FEMALE_FULL_MERGE FAIL - NECK_WELD** (NECK_STEP_MM 7.92 > 2.0). Flagged because the literal wording is not met although nothing is broken: VMAP_CLEAN, TOPOLOGY.
Staged only: `export/HeroBase_Female_FULL_STAGED.blend` (+ fbx, delta, replay script, vmaps, README_MERGE.md). ArtDir female SHA `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` before and after. Not a form pass.

| gate | literal reading | as delivered | evidence |
|---|---|---|---|
| BASE_SHA | PASS | PASS | `1149e620...` verified before edit |
| VMAP_CLEAN | **FAIL**: stock `merge_torso_delta.py --vmap` on the base as handed over = 3,194 conflicts (chat-7 old torso), 1,346 applied | **PASS**: after exactly retiring chat 7's 3,317 verts: 4,540 applied, 0 conflicts, 0 missing, 0 writes on hand verts 22,419-23,246 (0 on the 1,326 reused slots) | `checks/s3_stock_merge*.txt`, `checks/stage1_report.json` |
| HEAD_ZONE_ONLY | PASS | PASS | F3 head zone only (8,578 faces, 8,899 verts, bit-equal); F3 lower body not copied; lower body = base | `checks/checks_full.json` |
| ARMS_KEPT | PASS | PASS | 0 of 1,699 arm-zone verts (107 pins) changed | |
| LEGS_UNSCULPTED | PASS | PASS | 0 verts below z 0.62; FORM5's documented leg-top band only | |
| SEAMS | PASS (reported) | reported | `proof/SEAMS_SHEET.png`, `checks/seams.json` |
| **NECK_WELD** | **FAIL** | **FAIL** | NECK_STEP_MM = 7.92 (collar ring, F3 head vs the original neck; FORM5 neck ring 0.57; positions 0.000) |
| OPEN_FAILS_DISCLOSED | PASS | PASS | bust side fill FAIL and underbutt crease FAIL carried, README_MERGE.md |
| TOPOLOGY | **FAIL** (Body_F has 256 boundary edges) | **PASS** on what the merge controls: boundary edges created by the merge 0; the 256 are F3's two eye openings (2 x 128), identical to F3's own Body_F, covered by Face_F; non-manifold 0; winding 0; loose 0; hand-vs-body 0 | `checks/checks_full.json`, `checks/bvh_checks.json` |
| ARTDIR_UNCHANGED | PASS | PASS | `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` before and after |
| PROOFS | PASS | PASS | `proof/FULL_FIGURE_5VIEWS.png`, `proof/CLOSEUPS_SHEET.png`, `proof/SEAMS_SHEET.png`, `proof/raw/` |
| NOT_A_FORM_PASS | PASS | PASS | no plate-fidelity claim |

Deviations I chose (each one reversible, all in README_MERGE.md): (1) retired chat 7's superseded torso before the FORM5 delta; the 123 chat-7-moved FORM5 border verts went back to the original (<= 2.455 mm); (2) head grafted as a zone replacement because F3's head has a different topology; (3) 460 orphan F3 vertices not carried; (4) Body_F material slots = Base_Grey_F, Skin_F; (5) Face_F appended from F3; (6) gate definitions fixed before measuring (`GATE_DEFS_preregistered.md`, one dated amendment about the border classification; no verdict depends on it).
