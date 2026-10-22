# HANDOFF - male hands FORM3 (palm scale + round tips) - DONE and installed (2026-10-02 07:5x)

`GATE: MALE_HANDS_FORM3 PASS` - see `proof/MALE_HANDS_FORM3_RESULTS.md` (copy in `ArtDir/hero/base_lock/proof/`) and `proof/male-hands-form3-checks.json`.

- Installed: ArtDir blend `4287ba52...` -> `b51cbb05d5135325b083462efc1b6e05d444a8a514c6c3b58547dad9564431ee`; FBX `2d052746...` -> `39303a777785a240ab9821107c00d9dfef6a476c29ce60d3bd369e7ad9e1038c`.
- Rollback: `baseline/pre_install/` (blend `4287ba52...`, FBX `2d052746...`).
- Not done: Unity project copy of the FBX (set `ExpectedTriangles` to 63638 in `Unity/Assets/Editor/HeroBaseMaleFormProof.cs` first; the proof run overwrites `proof/male_form_d/unity/*`).
- Generator: `hand4.py` (= FORM2 `hand3.py` + u-parametrised palm + `cap_mode='round'`); default params reproduce the FORM2 mesh bit-for-bit (`regress.py`). Final parameters: `params_final.json`.
- Rebuild on a newer ArtDir blend: `dump_mesh.py` -> `data/mesh_cur.npz`, `make_cut.py` (needs the FORM2 `data/shellv_*.npy` to define the shell), `make_zone.py`, `./pipeline_final.sh` (candidate -> staged blend -> verify -> audit -> native silhouettes -> FBX -> self-intersection -> weld check), `make_checks3.py`, proof sheets (`compose_ba.py`, `compose_tips.py`, `compose_plate.py`, `compose_prof.py` after the render steps listed in the session), `install_form3.sh` with the new START SHAs.
- Tools: `allmetrics.py` (all gates, FORM2 = '{}'), `explore.py` / `maxdih.py` / `volcmp.py` (parameter sweeps: ROI, dihedral, palm volume), `tipsheet.py` (isolated tip close-ups), `hv.py` / `cmp2.py` (hand view sheets), `profcmp.py` (plate profile cameras), `sharp.py` / `roles.py` (find / explain sharp edges), `weldcheck.py`, `audit3.py`.
