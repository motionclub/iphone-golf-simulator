"""write FEMALE_TORSO_FORM4_RESULTS.md from checks.json + export/*.json + export/honest_notes.md  (python3 tools/write_results4.py)"""
import sys, json, hashlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
from torso4 import WD
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
ROOT = WD.parent.parent
ck = json.load(open(WD / 'checks.json'))
fc = json.load(open(WD / 'export/form4_checks.json'))
honest = open(WD / 'export/honest_notes.md').read() if (WD / 'export/honest_notes.md').exists() else '(missing)'
blend = WD / 'export/HeroBase_Female_torso_form4_candidate.blend'; delta = WD / 'export/torso_form4_delta.npz'
start3 = WD / 'START_form4_candidate.blend'
art = ROOT / 'ArtDir/hero/base_lock/blender/HeroBase_Female.blend'
P = json.load(open(WD / 'export/form4_params.json'))
ph = ck['photometric']
rows = []
for l in ck['lines']:
    v = l['value']
    if isinstance(v, (dict, list)):
        v = json.dumps(v, default=str)[:160]
    rows.append(f"| {l['group']} | {l['line']}{' *(eye check)*' if l.get('eye_check_required') else ''} | {v} | {l['limit']} | {l['result']} |")
md = f"""# FEMALE TORSO FORM4 - bust primary + glute hold (Sonnet 5.5)

**GATE: FEMALE_TORSO_FORM4 {ck['overall']}**  (group results: {ck['group_results']})

{honest}

## Provenance
* Start: `work/female-torso-form3/export/HeroBase_Female_torso_form3_candidate.blend` SHA `{sha(start3)[:16]}...{sha(start3)[-8:]}` (verified a0f69f9d...; byte copy `START_form4_candidate.blend`). ArtDir `HeroBase_Female.blend` = `{sha(art)[:16]}...` (unchanged; 200dc3b9... expected) -> **nothing installed**.
* Staged result: `export/HeroBase_Female_torso_form4_candidate.blend` SHA `{sha(blend)[:16]}...{sha(blend)[-8:]}`.
* Drop-in delta relative to the ORIGINAL 200dc3b9 (supersedes FORM3, FORM2 and chat-7 deltas): `export/torso_form4_delta.npz` SHA `{sha(delta)[:16]}...`, {fc['delta_moved_vertices']:,} vertices. `export/README_MERGE.md`, `export/merge_torso_delta.py`.
* Parameters: `export/form4_params.json` (chest/upper zone, as run) + `export/form4_params_glute.json` (pelvis/glute, FORM3's own + back-apex target), `*_full.json` (incl. defaults of `tools/torso4.py`), `export/form4_wall_corrections.npy`. Reproduce everything: `bash finalize4.sh data/P_final4.json data/P_glute4.json`.

## Method (what was built)
Positions only; topology, UVs, materials, custom-normal raw codes, Hair, plates, lights identical; the 238 zone border vertices bit-identical to the original; {fc['delta_moved_vertices']:,} vertices move (max {fc['max_vertex_move_mm_vs_original']:.1f} mm vs the original). `tools/torso4.py` (derived from FORM3's `torso3.py`), `build_final(PC, PG)`:
* **chest / upper zone (z > ~1.06)**: FORM3's ring remap on the ORIGINAL ring shape (no flatten band, no moat, no pec fill) + a **plate-following front wall** from the new sub-pixel plate contour (`tools/plate_side4.py`) + a **sternum wall line** `wl_y` (the plate silhouette in the bust band is the dome apex line, not the sternum) + **two signed bell domes** (profile (1-rho^p)^k with separate exponents below/above, physical-space rotation, compact C2 support, `bm_signed`) + an **upper-chest slope ramp** (plate slope eased to a constant slope that lands exactly on the original neck-ring front) + wider geodesic weights (`arm_r` .07, `top_r` .10, `top_f` .07, `ksm` 12: arm step 9.3 -> 7.0 mm, neck 0.5 mm) + sternum-strip smoothing (`cs_k`).
* **pelvis / glute zone (z < ~0.99)**: FORM3's own parameters + a 3 mm back-silhouette target (`bk_amp`); blended with the chest build over z 0.99-1.06 so chest-side parameter changes cannot leak into the glutes.
* Dome parameters were tuned with a bounded evolution strategy (`tools/opt4.py`, objective `tools/score4.py`: plate-lit band-pass NCC at two scales + amplitude + guard rails on silhouette RMS, apex radius, slope, dihedral, seam budgets) and then **chosen by eye** from the candidates (`tools/variants4.py`, `zoom4.py`, `stretch4.py`, `bpmap4.py`, `side4.py`); the pure-NCC optimum was rejected (peaky, polygonal, creased).

## Gate results (`checks.json`; evaluated by `tools/gates4.py`)
| group | line | value | limit | result |
|---|---|---|---|---|
""" + "\n".join(rows) + f"""

## Proof (`proof/`)
`04_plate_vs_form3_vs_form4_3q.png` - `05_bust_closeups_soft.png` / `_clay.png` (front, 3/4 L/R, side) - `05z_bust_zoom_soft.png` / `_clay.png` (zoomed) - `06_glute_closeups_soft.png` / `_clay.png` - `02_side_profile_overlay.png` / `12_side_overlay_subpixel_zoom.png` - `03_front_back_silhouette_overlay.png` - `07_mirror_stripe_test.png` - `01_torso_before_after_soft.png` / `_clay.png` - `08_bust_sections_front.png` (horizontal sections: FORM3's trapezoid plateau vs FORM4's domes) - `11_bandpass_maps.png` (2-D shading structure, plate vs FORM3 vs FORM4) - `13_full_torso_soft.png` - `09_merged_preview_torso_limbs_arms_UNOFFICIAL.png` / `10_armpit_seam_check_merged.png` (FORM4 delta merged onto the arms chat candidate; preview only) - `checks.json`. 'Soft' = lighting fitted to the plate (matcap gain 2.2), 'clay' = clay-studio matcap, stripes = mirror matcap; panels of one image share cameras and processing.

## Install / merge
See `export/README_MERGE.md`. Default: STAGE ONLY; install only after Adnan's eye PASS. Not done: Unity import / prefab / FBX refresh; no clothes, no hair change, no rig.
"""
open(WD / 'FEMALE_TORSO_FORM4_RESULTS.md', 'w').write(md)
print('written', len(md), 'chars')
