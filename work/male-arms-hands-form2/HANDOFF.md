# HANDOFF - male arms+hands FORM2 - DONE and installed (2026-10-02 06:5x)

`GATE: MALE_ARMS_HANDS_FORM PASS` - see `MALE_ARMS_HANDS_FORM_RESULTS.md` (copy of `ArtDir/hero/base_lock/proof/MALE_ARMS_HANDS_FORM_RESULTS.md`) and `data/male-arms-hands-form-checks.json`.

- Installed: ArtDir blend `1fe4d53b...` -> `4287ba523218e89ae5a822483c322dc4cfa163c7af143ebcac11abbacea2db21`; FBX `73582af6...` -> `2d052746eb2ff26403080df24131abecd83564cf04528e77c46a9c2af245c483`.
- Rollback: `baseline_cur/pre_install/`.
- Not done: Unity project copy of the FBX (set `ExpectedTriangles` to 63022 in `Unity/Assets/Editor/HeroBaseMaleFormProof.cs` first; the proof run overwrites `proof/male_form_d/unity/*`).
- Rebuild on a newer ArtDir blend: dump it with `dump_mesh.py` to `data/mesh_cur.npz`, `./py.sh run_metrics.py G1 '{}' data/m.json '{}'`, `write_blend.py` on a copy of that blend (args: cand npz, out blend, `data/removed_both.npy`), `verify_blend.py`, `export_fbx.py`, then `install_form2.sh` with the new START SHAs.
- Tunables: hand params = `hand3.py` `P0`; arm params = `arms3.py` `ARM0`; silhouette fit = `opt3.py`.
