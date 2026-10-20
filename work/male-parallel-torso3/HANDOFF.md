# HANDOFF - male torso FORM3 - DONE and installed (2026-10-02 08:19)

`GATE: MALE_TORSO_FORM3 PASS` - see `proof/MALE_TORSO_FORM3_RESULTS.md` and `proof/male-torso-form3-checks.json`.

- Installed (guarded vertex-index patch): ArtDir blend `2e8f973b...` -> `548a83f4bf3f8624e452955bfef84e3f5bf84a3088f8cd9ae5325dc20d426495`; FBX `d40e9b55...` -> `2e0740d7127556fc2176e4d35d7f8d916180e856187de3de71b46ef16f5e5bfc` (66,158 tris).
- Rollback: `baseline/pre_install_form3_2e8f973b.blend` / `pre_install_form3_d40e9b55.fbx`.
- Not done: Unity project copy of the FBX (set `ExpectedTriangles` to 66158 in `Unity/Assets/Editor/HeroBaseMaleFormProof.cs` first).
- Re-apply on a newer ArtDir blend: `blender -b --factory-startup --python apply_form3.py -- <current.blend> <out.blend>` (5,587 vertices, aborts if a torso vertex is neither at FORM2 nor FORM3), or `./install_form3.sh` (lock + guard + FBX re-export + atomic move).
- Rebuild the edit from scratch: `./run_form3.sh FORM3` (recipe `base_FORM3.json`, frozen solver asset `data/RBF_FORM3_asset.npz`).
- Open items for a possible FORM4 / other zones: buttock fold arcs + thigh overhang + crotch slot (legs zone); held-out back 3/4 panels are slightly lower than FORM2 (see results); Unity-style shelf contrast 24 lum vs plate's own ~38 under frontal light (rig is flatter) - judge in the rig, not plate-lit.
