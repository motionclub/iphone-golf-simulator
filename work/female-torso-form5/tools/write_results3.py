"""write FEMALE_TORSO_FORM3_RESULTS.md from checks.json + export/*.json + export/honest_notes.md  (python3 tools/write_results3.py)"""
import sys, json, hashlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
from torso3 import WD
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
ROOT = WD.parent.parent
ck = json.load(open(WD / 'checks.json'))
fc = json.load(open(WD / 'export/form3_checks.json'))
honest = open(WD / 'export/honest_notes.md').read() if (WD / 'export/honest_notes.md').exists() else '(missing)'
blend = WD / 'export/HeroBase_Female_torso_form3_candidate.blend'; delta = WD / 'export/torso_form3_delta.npz'
art = ROOT / 'ArtDir/hero/base_lock/blender/HeroBase_Female.blend'
P = json.load(open(WD / 'export/form3_params.json'))
ph = ck['photometric']
rows = []
for l in ck['lines']:
    v = l['value']
    if isinstance(v, (dict, list)):
        v = json.dumps(v, default=str)[:160]
    rows.append(f"| {l['group']} | {l['line']}{' *(eye check)*' if l.get('eye_check_required') else ''} | {v} | {l['limit']} | {l['result']} |")
md = f"""# FEMALE TORSO FORM3 - bust + glute likeness (Sonnet 5.5)

**GATE: FEMALE_TORSO_FORM3 {ck['overall']}**  (group results: {ck['group_results']})

{honest}

## Provenance
* Start: `work/female-torso-form2/export/HeroBase_Female_torso_form2_candidate.blend` SHA `6859d958...66a65f27` (verified; byte copy `START_form2_candidate.blend`). ArtDir `HeroBase_Female.blend` = `{sha(art)[:16]}...` (unchanged; 200dc3b9... expected) -> **nothing installed**.
* Staged result: `export/HeroBase_Female_torso_form3_candidate.blend` SHA `{sha(blend)[:16]}...{sha(blend)[-8:]}`.
* Drop-in delta relative to the ORIGINAL 200dc3b9 (supersedes FORM2 and chat-7 deltas): `export/torso_form3_delta.npz` SHA `{sha(delta)[:16]}...`, {fc['delta_moved_vertices']:,} vertices. `export/README_MERGE.md`, `export/merge_torso_delta.py`.
* Parameters: `export/form3_params.json` (as run) / `export/form3_params_full.json` (incl. defaults of `tools/torso3.py`) + `export/form3_wall_corrections.npy`. Reproduce everything: `bash finalize3.sh data/P_final.json` (blend, delta, audits, gates, proofs, integration preview, this file).

## Why FORM2 failed (root causes this pass removed)
1. **Bust = ellipsoid caps on a cylinder.** Hard footprints (compact support) + a constant-height cap left flat fronts, a shelf at the underbust and a second shelf at the upper edge; two eggs on a tube.
2. **Glutes = lobe union + recessed base.** The cleft was the recessed base (a pit with vertical walls), the lobes had a lateral window / upper rim -> a rectangular slab with a square cavity and a ledge.
3. **My own proof lighting was wrong.** The plate-like matcap inherited from FORM2 is lit from the viewer's LEFT; a regression of the plate's luminance on the model normals (unedited regions, front and back views) says the plate is lit from above and the viewer's RIGHT, with low contrast (`data/plate_light_fit.json`: I = 181.8 + 18.2 n_right + 28.5 n_up + 11 n_toward, contrast under-estimated by regression dilution -> calibrated gain 2.5 front / 2.0 back on the unedited regions). All proofs here use the fitted light (`tools/matcap_platefit_g22.png`) plus clay studio and mirror-stripe matcaps. The sheet's 3/4 panels are NOT 25 deg: front panels look ~15-20 deg, back panels ~30 deg; proofs use +-20 (front) / +-30 (back).

## What changed (zone = chat 7's 3,320-vertex torso mask, z 0.795-1.37, arms excluded)
Positions only; topology, UVs, materials, custom-normal raw codes, Hair, plates, lights identical; the 238 zone border vertices bit-identical to the original; 3,082 vertices move (max 42 mm).
* All features are smooth Gaussian-type fields on chat 7's depth remap (no compact-support footprints, no hard windows). `tools/torso3.py` (`build3`):
  * **bust** = one asymmetric Gaussian-type mound per side (steeper below, long gentle slope above) with an underbust groove, a localized wall dip behind it (`b_rec`) and a mound-centred moat (`mo_*`) so the 12 mm relief fits inside the plate's side envelope, a light flatten band (`fl_k`), and a smooth Hermite ramp of the front wall from the mound's upper edge to the original neck (`ramp_*`; removes the slope-kink shelf of chat 7 / FORM2);
  * **glutes** = Gaussian lobes + lobe moat (strong medially/below, none above) + a separately carved soft V cleft (`cl_*`, widening/fading into the lumbar) + a +4 mm underbutt bump from the floor ring (`ub_*`).
* Parameters were fitted against the plate with a photometric optimiser (`tools/opt3.py`, CMA-ES: 1 - NCC of band-passed plate vs model luminance + amplitude term + penalties for silhouette envelope, seam steps, creases, minimum mound height, cleft depth/V-shape), then hand-tuned against the proofs; `tools/photo3.py` rasterises the model at the plate's pixel grid with the fitted light.
* Front/back wall tables are re-fitted so the side-silhouette envelope tracks the plate table (`fit_walls`), as in chat 7.

## Gate results (`checks.json`; evaluated by `tools/gates3.py`)
| group | line | value | limit | result |
|---|---|---|---|---|
""" + "\n".join(rows) + f"""

Photometric agreement (band-pass NCC, plate-lit): bust FORM3 {ph['bust_form3']['ncc']:.3f} (FORM2 {ph['bust_form2']['ncc']:.3f}), glute FORM3 {ph['glute_form3']['ncc']:.3f} (FORM2 {ph['glute_form2']['ncc']:.3f}); unedited regions of the same model score {ph['unedited_ncc']} (mean {ph['unedited_mean']:.2f}) - i.e. the metric tops out around 0.4-0.7 for 'same shape, not pixel-exact'.

## Proof (`proof/`)
`04_plate_vs_form2_vs_form3_3q.png` - `05_bust_closeups_soft.png` / `_clay.png` - `06_glute_closeups_soft.png` / `_clay.png` - `07_mirror_stripe_test.png` - `02_side_profile_overlay.png` - `03_front_back_silhouette_overlay.png` - `01_torso_before_after_soft.png` / `_clay.png` - `08_relief_profiles.png` (brightness profiles through mounds/lobes/cleft, plate vs FORM2 vs FORM3) - `09_merged_preview_torso_limbs_arms_UNOFFICIAL.png` / `10_armpit_seam_check_merged.png` (FORM3 delta merged onto the arms chat candidate; preview only) - `checks.json`. 'Soft' = lighting fitted to the plate, 'clay' = clay-studio matcap, stripes = mirror matcap; panels of one image share cameras and processing.

## Install / merge
See `export/README_MERGE.md`. Default: STAGE ONLY; install only after Adnan's eye PASS. Not done: Unity import / prefab / FBX refresh; no clothes, no hair change, no rig.
"""
open(WD / 'FEMALE_TORSO_FORM3_RESULTS.md', 'w').write(md)
print('written', len(md), 'chars')
