# TENNIS_SHOES_FIT - tennis shoes (and the socks they sit on) fitted to the current hero feet

Staged only. Nothing under `ArtDir` is written, the two body blends are read-only (SHA verified before and after), polo / shorts / skort are untouched, no racket.
Verdict and evidence: `GATE_RESULTS.md`; every number: `checks.json` (flat summary under `summary`); gate definitions written before the final measurement run: `GATE_DEFS_preregistered.md`.

## Bodies the fit was measured on
| hero | file | SHA-256 |
|---|---|---|
| male | `work/male-pelvis-form3/export/merged_fd04bc28.blend` | `d6c4dcfb1150853a8802a8dc7501aa64066adb8b2734c14a4d6ed8e82dada781` |
| female | `work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend` | `a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1` |

## Deliverables (`export/`)
`StandardKit_Male.blend`, `StandardKit_Female.blend` = copies of the start kit blends (`start/`, SHA ad07a7b9... / f19a9c03...) in which ONLY these changed:
* `Kit_Shoe_L/R` and `Kit_Sock_L/R` (both colourways) rebuilt on these feet; same object names, collections, material slots (Std_White_Lit / Std_Black_Lit), custom props; each parented to `Foot_L_Shoe_<colour>` / `Foot_R_Shoe_<colour>`, identity world transform.
* the four foot sockets set to an identity transform; `FitRef_Body_*` is now a copy of the body above; every `*_ArmsCandFit_*` object / mesh / collection and the arms-candidate reference body are deleted.
`Kit_Top_Polo_*` and `Kit_Bottom_*` are bit-identical (mesh hash compared in `checks.json`).

## Proofs (`proof/`)
`FEET_<Hero>_<White|Black>.png` close-ups of both feet (side / front / heel / low 3/4), `CUTAWAY_<Hero>.png` capped sections (skin / sock / shoe), `BEFORE_AFTER_<Hero>.png` (start kit on the new body vs new), `CONTEXT_<Hero>.png` full body, raw cells in `proof/raw/`, per-hero measurements in `proof/raw/checks_<g>.json`.

## Design
Same sneaker as the start kit (low-top, chunky cupsole, padded collar roll, tongue, five lace rows as ridges on the shell, toe cap / heel counter seams, heel tab, herringbone tread; no logos) but:
* built once around the UNION of the right foot and the mirrored left foot -> the left shoe is the exact mirror of the right (same length, same sole height, same ground plane z = -sole height);
* per-slice convex hull "last" of the real feet + offset, toe box rounded by a heavy blur, upper clears the real socks by >= 2.5 mm and the skin by >= 4.6 mm;
* collar line raised to the ankle, rim path smoothed, round 10-sided padded roll (no kinks), roll and tongue pushed off the sock so no triangle of sock and shoe intersect;
* sole + tread use the piping slot (white on both kits: contrasts on the black kit);
* socks: same crew sock (2 mm knit wall, ribbed cuff stands 1.4 mm proud, cuff ring), whole mesh rebuilt on each leg (female start sock stood up to 63 mm off the new leg; male sock came out vertex-identical).

## Rebuild
`scripts/run_all.sh` (~3 min, headless Blender 5.2, numpy only inside Blender's python, Pillow in the system python): SHA guard -> `dump_body.py` / `measure_feet.py` -> `sock.py` -> `shoe.py` -> `assemble_fit.py` -> `final_checks.py` -> start-kit control (`fitcheck.py old`) -> proof renders (`view_blend.py`, `render_cutaway.py`) -> `compose_proofs.py` -> `final_report.py`.
Code map: `kitlib.py` numpy/BVH helpers, `sdf.py` SDF grid + surface nets + clip, `kit_common.py` closed shells / ribbons / enforcement, `fitbody.py` body registry (only the two bodies above), `shell.py` sock shell, `checklib.py` winding number / enclosure rays / camera-ray skin visibility, `slicer.py` plane slicer.
