# FEMALE TORSO FORM5 — WORK IN PROGRESS (stopped on usage limit, 2026-10-02 ~15:10 local, ~45 min of work)

**Status: NOT DONE. No candidate blend, no delta npz, no RESULTS.md, no proof set exist yet. Nothing installed.**
Honest gate if asked now: `GATE: FEMALE_TORSO_FORM5 FAIL` (BUST_EYE_PASS / UNDERBUTT_EYE_PASS / deliverables not produced).

Workspace `work/female-torso-form5/` = FORM4 tools/data/gate7 copied + paths patched. `START_form4_candidate.blend` SHA `aa3e1e44…` verified; ArtDir female still `200dc3b9…`.
`python3` (system, numpy+Pillow, no scipy) runs all tools; Blender: `/Applications/Blender.app/Contents/MacOS/Blender -b`. Use absolute paths (a `cd` in Bash moves the session cwd). `tri5.py` can exceed 120 s under load -> run_in_background.

## BUST — what the plate says (measured)
* Only the LOWER half of each mound is delineated: a smile-shaped crescent = lower arc of a circle R≈9.3 cm centred (x .09, z 1.273); crescent z at x=.03/.06/.085/.11 = **1.202/1.188/1.180/1.186**, dip (plate-fit light x2.5) −14/−21/−19 grey. The upper half merges into the tilted upper-chest plane (no upper rim). FORM4's closed bell domes = closed rim ring = "targets"; its crescent dips were −35 (too steep/compact).
* Plate side contour (sub-pixel): wall −123 mm to z 1.18, apex −133 @1.22, then 29–39° diagonal. The plate's relief is subtle; luminance-amplitude metrics are gain-ambiguous (FORM4 matches the plate at gain ~1.1, my J at 2.5) -> use eye + crescent position, not NCC.
* Plate has stronger lateral flatness (side fill): model chest rounds off to the arm too early (dark side band wider than plate).

## BUST — tools added (tools/)
`torso5.py` (monkeypatches `torso4.bust_amp`; `mound5` Gaussian teardrop + medial wall window; `mound_arc` arc-foot mound, `"b5.mode":"arc"`; `fit_front5` iterates the FRONT wall to the sub-pixel plate contour over `fit_front_zr`), `variants5.py` (variant boards + crescent/silhouette report), `tri5.py` (plate | soft | clay | mirror-stripe boards, chest|pelvis), `big5.py`, `bp5.py`, `cres5.py`, `lprof5.py`/`hprof5.py`/`lpv5.py` (luminance profiles), `data/P5_base.json`.
Variant example: `python3 tools/variants5.py out.png data/P5_base.json soft J3:'{...}'` (params saved as `data/P5_<name>.json`, coords `data/co5_<name>.npy`).

## BUST — best so far
`data/co5_J2.npy`, `co5_J3.npy` (params `data/P5_J3.json`): wl_y −0.115…−0.118, fit_front on zr [1.12,**1.265**], arc mode xarc .09 zlow 1.178 Rarc .095 Ll .05 Lu .045 xcr .075 sxm .032–.035 sxl .05 H .017–.021 xw .035 sv .003–.004.
Silhouette vs plate within 1 mm (z 1.16–1.30), apex −132.9, seams legs 7.6 / arm 7.1 / neck 0.5 mm, side view clean, 3/4 soft = two soft integrated mounds with crescent. Images: `scratch/v5_f_soft.png`, `scratch/tri_J3.png`.
Still wrong: front view reads as one broad band (mounds not distinct enough); no side-fill yet; clay shows a diagonal bright crease at the upper chest (slope-ramp start); mirror stripes = nested vertical ovals (not polygonal, but still ring-like).
Pitfalls: `fit_front_zr` up to 1.31 makes a neck kink + top seam 1.18 mm (>1.0); `pf_A` fill pushes the whole silhouette 7 mm forward (needs a z-limited lateral fill); Gaussian lower flank puts the crescent ~1.5 cm too high (variant G) — the foot arc fixes it.
Next: smaller sxm / stronger sternal groove or partial wall recess for distinct mounds; lateral fill limited to z<1.26 and |x| .09–.12 under the arm seam budget (≤10 mm); crescent dips toward −14/−21/−19; soften the upper-chest crease; then 3 looks + side + zoom proofs.

## UNDERBUTT — diagnosis (measured)
* FORM4 back profile at x=.065: thigh +92.5 mm for z .76–.81 (original thigh), lobe starts at z .82 and climbs +98 @.82, +110 @.83, +118 @.865 = 17 mm in 2 cm (~40°) right above the pinned zone-floor ring (z≈.795), full width -> the horizontal groove/"cut".
* Plate back silhouette (torso-chat anchor): +83 @.78, +90 @.80, +104 @.82, +113 @.84, +118 @.86; apex-minus-thigh overhang plate ≈35 mm vs model ≈23 mm. (Limbs-chat anchor puts the plate thigh ~11 mm deeper, so the absolute thigh excess is uncertain; the overhang deficit is anchor-independent.)
* Plate vertical luminance in the back view: the fold dip sits at z ≈ .795 (x .03), .80 (.06), .81 (.09), .82 (.12) = a curved "smile" rising ~2.5 cm laterally, with a long soft recovery over z .80→.93. FORM4 has a narrow cliff-like notch at the same z for every column.
* Back/front silhouette half-widths for z .60–1.0 already match the plate within ~1 cm: leave x untouched.
* Female limbs chat moved only z ≤ 0.579 (`leg_verts_moved` 2491) -> a LEG-TOP extension z ∈ [≈0.64, 0.795) does NOT overlap its vertices (its mesh has 22,419 verts: merge via `HeroBase_Female_limbs_vertex_map.npz`). Hands hang at z .78–.87, |x|≈.16–.27: select the extension by flood fill DOWN from the old leg-top border ring through the thigh tubes, not by z/x window.

## UNDERBUTT — plan (not started)
1. Documented mask T5 = old zone T ∪ flood-filled thigh tubes with z ≥ z_floor (≈0.64–0.66); new floor ring pinned bit-identical; old ring (z .795) becomes interior.
2. y-only field on the back half: recess thigh back ≤≈10 mm over z .70–.79 tapering to 0 at the floor; reshape the lobe underside as a curved fold (lowest near the cleft ≈.80, rising laterally to ≈.83), long soft recovery, no straight band; keep twin lobes + soft V cleft (FORM4 glute params P_glute4.json).
3. Gates: `gates4.py` / `make_final4.py` / `torso2.py` are hard-wired to `zone_chat7.npz` T -> write FORM5 versions with the extended mask; recompute SIDE_SIL / FRONT_BACK (incl. leg-top), seam ≤8 mm at the new border (or disclose), ZONE_OUTSIDE=0 vs FORM4 start AND vs 200dc3b9 for the documented mask.
4. Deliver: `FEMALE_TORSO_FORM5_RESULTS.md` (honest notes + LEG-TOP doc), proofs 04/05/05z/06 (soft+clay+side) + before/after + checks.json, `export/` candidate blend + `torso_form5_delta.npz` + merge script + README_MERGE.md (stage only; no ArtDir install). Send plate-vs-now progress images to Adnan every ~15–20 min.
