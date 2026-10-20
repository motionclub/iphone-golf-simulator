# Merging the female torso FORM5 zone (bust soft-plastic + continuous underbutt + documented LEG-TOP extension)

Delta is relative to the ORIGINAL start `HeroBase_Female.blend` SHA `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` (22,444 verts).
It **supersedes** FORM4's `torso_form4_delta.npz`, FORM3's `torso_form3_delta.npz`, FORM2's `torso_form2_delta.npz` and chat 7's `torso_delta.npz` - apply exactly ONE of them (never stack).

`torso_form5_delta.npz` (SHA `f8dd0a57bbddd3c4...`): `moved_idx`, `start_co` (original float32), `new_co`, `zone_mask` (the DOCUMENTED FORM5 zone5 mask: chat 7's 3,320-vertex torso mask + the 1,442-vertex LEG-TOP extension z .62-.795, 4,762 vertices), `border_mask` (222), `vertex_count`.
The 222 zone5 border vertices (neck / arm junction / the NEW leg-top floor ring at z .62; the old class-1 border ring at z .795 is now interior) are NOT in the delta: they stay bit-identical to the original, which the arms/legs/neck seams rely on.
**LEG-TOP extension:** unlike FORM4 the delta also moves vertices of the thigh tops z .62-.795 (y-only recess of the thigh back, tapering to 0 at the floor ring z .62; exact numbers in proof/checks.json LEG-TOP lines - they changed in round 5). The female limbs chat moved only z <= 0.579, so there is no overlap with its vertices; merge into its order with `--vmap` below.

**Custom-normal offsets (ROUND 5 DEVIATION from 'positions only', disclosed):** the delta also carries `cn_vertex_weight` (float32 per ORIGINAL vertex). `merge_torso_delta.py` scales the authored custom-normal OFFSET (raw code0 of the `custom_normal` attribute) by (1-w) on the corners of those vertices (code0 == 0 means 'use the computed loop normal'; code1 and every other loop stay bit-identical; the scaling is not idempotent: apply once; skip with `--no-normals` to get the positions-only result). Reason: the offsets were baked on the ORIGINAL mesh; where the zone moved by millimetres they flatten the new under-butt fold in every render (same geometry: rendered smile +1.7 px with them, +6.5 px without; plate +14). Weights = smoothstep of the vertex displacement (2-10 mm) + 2 diffusion passes, border / floor-ring vertices 0 (`tools/cnweight5.py`).

Staged candidate: `HeroBase_Female_torso_form5_candidate.blend` SHA `7aa351d56427d037...` (= ArtDir blend + this delta, vertex arrays bit-identical - verified).
ArtDir `HeroBase_Female.blend` is still `200dc3b93e65491a...` : NOTHING was installed. Install only after Adnan's eye PASS.

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
# same vertex order as ArtDir (22,444): tested on a copy of the ArtDir blend -> the whole delta applied, 0 conflicts, vertex arrays bit-identical to the staged candidate (audit/merge_verify.json)
$B -b <target.blend> --python export/merge_torso_delta.py -- export/torso_form5_delta.npz <out>.blend
# limbs-chat vertex order (22,419):
$B -b <limbs-order.blend> --python export/merge_torso_delta.py -- export/torso_form5_delta.npz <out>.blend \
   --vmap work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz
# verified: merging into the limbs chat blend (`work/female-parallel-limbs/HeroBase_Female_limbs.blend`, 22,419 verts) with --vmap -> all 4,540 delta vertices applied, 0 conflicts, 0 missing (audit/merge_report_limbs_order.txt)
# a target that already carries chat 7's / FORM2's / FORM3's / FORM4's torso (e.g. the arms candidate) needs --force (its torso verts are not at the original positions)
```
* Each delta vertex must still be at its original position in the target (float32 exact); otherwise the vertex is reported and skipped (`--force` overwrites).
* Never run "clear custom split normals" on `Body_F` (that changes the shading of the whole body); the only normal edit is the weighted offset rescale above.
* Install rule: only one chat writes ArtDir at a time. After installing re-run the other chats' outside-zone audits; re-check the armpit seam against the arms candidate. NOT done in this chat: no merged torso + limbs + arms preview was built; the arm seam is verified only against the ArtDir arm junction (step 9.4 mm <= 10 mm per border edge).
* Rebuild from scratch: `bash finalize5.sh data/P5_final.json data/P_glute4.json data/PP5_final.json` (chest params + glute params + pelvis/underbutt params; builds the blend, delta, audits, merge check, proofs, gates, results; needs `START_form4_candidate.blend` = FORM4 candidate SHA `aa3e1e44...`).
* Also exported: `form5_params_chest.json`, `form5_params_glute.json`, `form5_params_pelvis.json`, `form5_wall_corrections.npy` (rows: chest dF,dB, glute dF,dB), `form5_checks.json` + `form5_gate_scripts_checks.json` (numeric gate record), `honest_notes.md` (what still differs from the plate).
