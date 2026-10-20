"""write FEMALE_TORSO_FORM5_RESULTS.md from checks.json + export/*.json + export/honest_notes.md  (python3 tools/write_results5.py)"""
import sys, json, hashlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
from torso4 import WD
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
ROOT = WD.parent.parent
ck = json.load(open(WD / 'checks.json'))
fc = json.load(open(WD / 'export/form5_checks.json'))
honest = open(WD / 'export/honest_notes.md').read() if (WD / 'export/honest_notes.md').exists() else '(missing)'
blend = WD / 'export/HeroBase_Female_torso_form5_candidate.blend'; delta = WD / 'export/torso_form5_delta.npz'
start = WD / 'START_form4_candidate.blend'
art = ROOT / 'ArtDir/hero/base_lock/blender/HeroBase_Female.blend'
rows = []
for l in ck['lines']:
    v = l['value']
    if isinstance(v, (dict, list)):
        v = json.dumps(v, default=str)[:170]
    rows.append(f"| {l['group']} | {l['line'].replace('|', '/')}{' *(eye check)*' if l.get('eye_check_required') else ''} | {str(v).replace('|', '/')} | {str(l['limit']).replace('|', '/')} | {l['result']} |")
md = f"""# FEMALE TORSO FORM5 - bust soft-plastic + continuous underbutt (Sonnet 5.5)

**GATE: FEMALE_TORSO_FORM5 {ck['overall']}**  (group results: {ck['group_results']})

{honest}

## Provenance
* Start: `work/female-torso-form4/export/HeroBase_Female_torso_form4_candidate.blend` SHA `{sha(start)[:16]}...{sha(start)[-8:]}` (verified aa3e1e44...; byte copy `START_form4_candidate.blend`). ArtDir `HeroBase_Female.blend` = `{sha(art)[:16]}...` (unchanged; 200dc3b9... expected) -> **nothing installed**.
* Staged result: `export/HeroBase_Female_torso_form5_candidate.blend` SHA `{sha(blend)[:16]}...{sha(blend)[-8:]}`.
* Drop-in delta relative to the ORIGINAL 200dc3b9 (supersedes FORM4, FORM3, FORM2 and chat-7 deltas): `export/torso_form5_delta.npz` SHA `{sha(delta)[:16]}...`, {fc['delta_moved_vertices']:,} vertices (documented zone5 mask: chat-7 zone 3,320 + LEG-TOP extension {fc['legtop_extension_vertices']:,}). `export/README_MERGE.md`, `export/merge_torso_delta.py` (verified: ArtDir copy + delta == candidate, bit-identical vertices; no overlap with the limbs chat's moved/removed vertices).
* Parameters: `export/form5_params_chest.json` (chest / upper zone as run), `export/form5_params_glute.json` (glute zone: FORM4's own), `export/form5_params_pelvis.json` (underbutt ramp + LEG-TOP), `export/form5_wall_corrections.npy`. Reproduce everything: `bash finalize5.sh data/P5_final.json data/P_glute4.json data/PP5_final.json`.

## Method (what was built)
Positions only; topology, UVs, materials, custom-normal raw codes, Hair, plates, lights identical; the {fc['border5_vertices']} zone5 border vertices bit-identical to the original; {fc['delta_moved_vertices']:,} vertices move (max {fc['max_vertex_move_mm_vs_original']:.1f} mm vs the original).
* **Bust (`tools/torso5.py`, on FORM4's `torso4.build3` ring/wall machinery)**: FORM4's closed bell domes were replaced by open **arc-foot mounds** (the lower contour is the shallow smile arc of the under-bust crescent; the upper half declines into the tilted chest plane, so there is no closed rim); lateral weight with a medial window (sternal valley), a soft sternal groove with a long lower taper (no pad below the cleavage), a lateral upper-chest tilt, a **soft wall corner** (smoothstep5 slope ramp instead of a max()-corner), the front wall iterated to the sub-pixel plate side contour (`fit_front5`), and a final **smooth-landing upper-chest profile** (`conc_post`): one concave sweep from the plate diagonal to the pinned neck-base ring (FORM5-v1 stalled at 5 deg and steepened again: the clay clavicle-level groove).
* **Underbutt + LEG-TOP (`tools/pelvis5.py`)**: documented extension of the zone down the thigh tops (flood-fill of the thigh tubes z .62-.795, floor ring of {fc['legtop_floor_ring_vertices']} vertices pinned) - y only: the thigh back is recessed by a depth-proportional amount (R0 in `form5_params_pelvis.json`; the original thigh back sits ~10-13 mm deeper than the plate's) (the original thigh back sits ~10-13 mm deeper than the plate's) and the lobe underside is a smooth **Beta-CDF sigmoid ramp** from that thigh to FORM4's own lobe (tangent-line continuation), with the ramp start/end varying laterally (`dshift`, `rza_x`, `cdz`, see params) so the fold is a **smile** (lowest at the cleft, rising toward the hips) instead of one horizontal band; thigh recess fades out on the hip flank; Taubin fairing of the fold band. Glute lobes above z ~.88 are FORM4's own (drift <= 0.05 mm).
* **Round 5 additions**: (1) the neck-base landing of the chest profile was relaxed (`conc_post` pw 0.25) to remove the dark band under the neck ring that the round-4 critics saw; (2) the under-butt ramp parameters were searched in the RENDER domain (`tools/rampfit8.py` + `blbatch6.py`: the soft Blender panel of proof/06z is rendered for dozens of candidates per Blender session and the fold line is traced with a robust fixed-window trace; the first version of that trace was exploited by the search - an outlier column faked a smile - and was replaced, see honest notes); (3) **custom-normal offset rescale (deviation from positions-only, disclosed)**: the authored per-corner normal offsets were baked on the ORIGINAL mesh and flatten the new fold shading in every render, so the offset (raw code0) is scaled by (1-w) on the corners of the moved / tapered vertices (`cn_vertex_weight` in the delta, applied by `merge_torso_delta.py`, `tools/cnweight5.py`).
* Chest parameters were tuned with a small constrained hill-climb (`tools/opt5.py`: plate-lit band-pass NCC at the plate-matched gain + amplitude + guard rails on silhouette, seams, dihedral) and then **chosen/adjusted by eye** (cleavage depth, valley taper, arm-seam margin); the underbutt ramp parameters were chosen from the plate's fold-onset/envelope measurements and by eye.

## Gate results (`checks.json`; evaluated by `tools/gates5.py`)
| group | line | value | limit | result |
|---|---|---|---|---|
""" + "\n".join(rows) + f"""

## Proof (`proof/`)
`04_plate_vs_form4_vs_form5_3q.png` - `05_bust_closeups_soft.png` / `_clay.png` - `05z_bust_zoom_soft.png` / `_clay.png` (tight crops) - `05s_bust_zoom_stripe.png` (mirror-stripe surface test, chest) - `06_glute_closeups_soft.png` / `_clay.png` (back, 3/4 back L/R, side) - `06z_underbutt_zoom_soft_clay.png` (tight crops: plate | F4 soft/clay | F5 soft/clay) - `07_mirror_stripe_test.png` - `01_torso_before_after_soft.png` / `_clay.png` - `02_side_profile_overlay.png` - `03_front_back_silhouette_overlay.png` - `08_bust_bandpass_vs_plate.png` (2-D shading structure) - `checks.json`. 'Soft' = lighting fitted to the plate, 'clay' = clay-studio matcap (stress test), stripes = mirror matcap; panels of one image share cameras and processing.

## Install / merge
See `export/README_MERGE.md`. Default: STAGE ONLY; install only after Adnan's eye PASS. Not done: Unity import / prefab / FBX refresh; no clothes, no hair change, no rig.
"""
open(WD / 'FEMALE_TORSO_FORM5_RESULTS.md', 'w').write(md)
print('written', len(md), 'chars')
