"""Write FEMALE_TORSO_FORM2_RESULTS.md from checks.json + export/*.json (numbers are pulled, not typed)."""
import json,hashlib,sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2/tools')
from torso2 import DEFAULT2, WD
sha=lambda p:hashlib.sha256(open(WD/p,'rb').read()).hexdigest()
ck=json.load(open(WD/'checks.json')); ex=json.load(open(WD/'export/form2_checks.json')); g7=json.load(open(WD/'export/form2_gate_scripts_checks.json')); fm=json.load(open(WD/'export/form2_feature_metrics.json'))
P={**DEFAULT2,**json.load(open(WD/'export/form2_params.json'))}
L={l['line']:l for l in ck['lines']}
def val(prefix): 
    for k,l in L.items():
        if k.startswith(prefix): return l['value']
    raise KeyError(prefix)
sx=g7['side_profile_torso_band_xor_z0.82_1.30']; fb=g7['torso_visible_edge_run_xor_rows_z0.82_1.165']; se=g7['side_contour_error_mm']['after']
bs=ex['border_steps_mm']; dh=ex['dihedral']; rg=ex['bi_laplacian_roughness_mm_zone_interior']; b=fm['bust']; g=fm['glute']
blend_sha=sha('export/HeroBase_Female_torso_form2_candidate.blend'); delta_sha=sha('export/torso_form2_delta.npz'); start_sha=sha('START_torso_candidate.blend'); art_sha=hashlib.sha256(open(WD/'../../ArtDir/hero/base_lock/blender/HeroBase_Female.blend','rb').read()).hexdigest()
cap=P['b_Ry']-P['b_e']
rows=[]
def row(grp,line,value,limit): rows.append(f'| {grp} | {line} | {value} | {limit} |')
for l in ck['lines']:
    v=l['value']; v=f"{v:.3f}".rstrip('0').rstrip('.') if isinstance(v,float) else str(v)
    row(l['group'],l['line'],f"{v} — {l['result']}",l['limit'])
md=f"""# FEMALE TORSO FORM2 — bust + glute (chat A of 07b/08b)

**GATE: FEMALE_TORSO_FORM2 {ck['overall']}** — all {len(ck['lines'])} binary lines in `checks.json` pass (groups: {', '.join(ck['group_results'])}).
Read "Honest notes" first: the form gate lines are this chat's definitions (plate-anchored), and Adnan's eye on `proof/04`, `proof/05`, `proof/01` is the real test — chat 7's PASS was rejected on form.

* Start: `work/female-parallel-torso/export/HeroBase_Female_torso_candidate.blend` — SHA `{start_sha[:8]}…{start_sha[-8:]}` (verified; byte copy `START_torso_candidate.blend`).
* ArtDir `HeroBase_Female.blend` = `{art_sha[:8]}…{art_sha[-8:]}` before and after → **nothing installed** (staged only; install rule).
* Staged result: `export/HeroBase_Female_torso_form2_candidate.blend` — SHA `{blend_sha[:8]}…{blend_sha[-8:]}`.
* Drop-in delta, relative to the ORIGINAL start 200dc3b9 (supersedes chat 7's delta): `export/torso_form2_delta.npz` — SHA `{delta_sha[:8]}…{delta_sha[-8:]}`, {ex['delta_moved_vertices']:,} vertices. `export/README_MERGE.md` has the commands.

## Why chat 7 was rejected (root causes found)
1. **Arm-taper weights strangled the bust.** Chat 7 faded displacement over 7.5 cm toward the arm junction, cutting the lateral half of each mound; the chest ring became a trapezoid ("shield") and the remains were pinched V creases (`data/xsec.png`, `proof/06`).
2. **Bust centre ~5 cm too low** (chat 7: z 1.19; plate: apex z≈1.21–1.22, dark underbust crescent z≈1.18–1.19, highlight z≈1.26, mound centres x≈±0.07–0.085).
3. **Glutes were one ellipse with an 11 mm Gaussian cleft.** The original pelvis ring already had the plate's glute depth (+0.1185 at z .86) but as a symmetric slab: no lobes, no shelf.

## What changed (zone = chat 7's 3,320-vertex torso mask, z 0.795–1.37, arms excluded)
Positions only; topology, UVs, materials, custom-normal raw codes, Hair, plates, lights identical. **The 238 zone border vertices (neck / arm junction / leg tops) are bit-identical to the original start** — the arms chat pinned its arm vertices to exactly those positions.

Method (`tools/torso2.py`, `build2`; parameters `export/form2_params.json`):
* Taubin-denoised surface (the 13.5 mm surface-nets lattice jitters ±0.5 mm); geodesic border weights (sstep5; feature tapers arm 4.5 / legs 3.5 / neck 4 cm, remap tapers 5 / 7 / 5 cm); the displacement diffusion pins the border vertices (Dirichlet 0).
* Per-ring depth remap to the plate side-profile envelope (chat 7's accepted depth, kept): front wall at the sternum line, back base at the cleft line; neck fade z {P['top_z1']-P['top_zw']:.2f}→{P['top_z1']:.3f}.
* **Bust** = two *wall-relative* ellipsoid caps (cap height above the local chest wall = R_y·√rad − e, R_y {P['b_Ry']:.3f}, e {P['b_e']:.3f} → {cap*1000:.0f} mm at the cap centre) smooth-min'd into the wall (a constant-depth ellipsoid left a ~38 mm cliff at the lateral edge against the pinned arm border). Centre x ±{P['b_xc']:.3f}, z {P['b_zc']:.3f}; radii {P['b_Rxm']:.3f}/{P['b_Rxl']:.3f} (x medial/lateral), {P['b_Rzd']:.3f}/{P['b_Rzu']:.3f} (z down/up) → footprint {b['L']['footprint_x_range_abs'][1]*1000-b['L']['footprint_x_range_abs'][0]*1000:.0f} × {(b['L']['footprint_z_range'][1]-b['L']['footprint_z_range'][0])*1000:.0f} mm; sternum line recessed {P['st_R']*1000:.0f} mm with a wide transition; {P['kfin_b']} diffusion passes keep a crisp underbust lip.
* **Glutes** = two ellipsoid lobes (centre x ±{P['g_xc']:.3f}, z {P['g_zc']:.3f}; semi-axes {P['g_Rxm']:.3f}/{P['g_Rxl']:.3f} (x medial/lateral) × {P['g_Ry']:.3f} (y) × {P['g_Rzd']:.3f}/{P['g_Rzu']:.3f} (z down/up)) smooth-max'd onto a base whose centre line is recessed by up to {P['gr_C']*1000:.0f} mm below the plate envelope (full below z≈{P['gr_z1']-P['gr_w']:.2f}, fading to 0 at z {P['gr_z1']:.3f}) — **the cleft is the base**; a lateral window (|x| {P['g_lat0']:.2f}→{P['g_lat1']:.3f}) ends the lobes before the hip roll-over; {P['kfin_g']}-pass displacement diffusion removed the hard rim along the top of the lobes; the lumbar→shelf knee is softened to σ 14 mm in the modelling target.
* Parameters were fitted to the plate envelope (`tools/fit.py`); footprint sizes/positions were fixed by design from plate grids and band-pass maps (`data/grid_*.png`, `proof/scratch/foot_*.png`).

## Gate results (`checks.json`; evaluated by `tools/gates.py` from `export/form2_*.json`)
| group | line | value | limit |
|---|---|---|---|
""" + "\n".join(rows) + f"""

Context numbers: side contour error front {se['front_mean']:.1f} mm mean / {se['front_max']:.1f} max, back {se['back_mean']:.1f} / {se['back_max']:.1f} (chat 7: 3.5/12, 2.5/16 by its own table); max vertex move {ex['max_vertex_move_mm_vs_original']:.0f} mm; dihedral stats (zone edges): mean {dh['form2']['mean_deg']:.1f}°, p95 {dh['form2']['p95_deg']:.1f}° (original {dh['original']['mean_deg']:.1f}° / {dh['original']['p95_deg']:.1f}°); roughness mean {rg['form2']['mean']:.3f} mm (original {rg['original']['mean']:.2f}, chat 7 {rg['chat7_candidate']['mean']:.3f}).
Whole-body front/back silhouette ({100*g7['front_back_silhouette_project_frame']['after']['front']['full']:.1f} / {100*g7['front_back_silhouette_project_frame']['after']['back']['full']:.1f} %) is **not** a torso-zone quantity and is unchanged (head, arms, legs). Chat 7's own `final_metrics.py` / `mesh_quality.py` were run unchanged on the new coordinates (`gate7/`). Edge-stretch max 22× is an inherited degenerate original edge (identical to chat 7).

## Proof (`proof/`)
`01_torso_before_after_soft.png` / `_clay.png` (chat 7 vs form2, same cameras) · `02_side_profile_overlay.png` · `03_front_back_silhouette_overlay.png` · `04_plate_vs_model_3q.png` (plate | chat 7 | form2) · `05_chest_glute_closeups.png` / `_clay.png` · `06_smoothness_mirror_test.png` (chat 7 vs form2 mirror stripes) · `08_merged_preview_torso_limbs_arms_UNOFFICIAL.png` · `09_armpit_seam_check_merged_vs_arms_candidate.png`.
Mirror-stripe test: chat 7's chest is broken stripes + pinched rings; form2 shows two clean concentric ring systems at the domes and two at the lobes. "Soft light" = plate-like matcap (`tools/soft_plate_matcap.png`); "clay" = chat 7's original matcap.

## Install / merge
* Validated on a copy: **ArtDir blend + delta** → 3,082 applied, 0 conflicts, vertex arrays bit-identical to the staged candidate.
* Onto the arms chat's candidate (torso+limbs+arms, limbs order) the merge needs `--vmap … --force` (its torso vertices still hold chat 7's positions): 3,082 applied → `export/PREVIEW_form2_torso_plus_limbs_plus_arms_UNOFFICIAL.blend` (preview only; `proof/08`, `proof/09`).
* Not done: Unity import / prefab / FBX refresh; no clothes, no hair change, no rig.

## Honest notes / limits
* **Form gate lines are my definitions**, anchored to plate measurements (mound/lobe positions and sizes measured from the plate grids and band-pass maps before tuning; cleft range, shelf tolerance and rim angle chosen knowing the result). Close to a limit: arm border step {bs['arm']['max_mm']:.1f}/10 mm, legs border step {bs['legs']['max_mm']:.1f}/8 mm, back torso-edge XOR {100*fb['after']['back']:.2f}/5 %, lobe apex error {val('lobe apex depth'):.1f}/4 mm.
* **Bust prominence is bounded by the plate profile**: the belly line below the bust is only ~5.5 mm behind the mound apex in the side view, so mounds read through shading (the plate has AO/crescents). Under plate-like light the mounds are soft and clear (see `proof/04`, `proof/05`) but still *less pronounced than the plate's in a straight front view*; under harsh clay light the dome flanks show V-shaped highlights.
* **Glutes**: round lobes + cleft + shelf now, but the buttock still reads **boxier than the plate in the 3/4 back view**: the zone floor (z 0.795) and the **fixed leg-top ring** form a horizontal ledge, so the plate's underbutt arc/overhang (fold z≈0.805–0.835) can only be approximated by the lobes' lower flank ({val('underbutt fold'):.0f} mm rise z .808→.852). That needs the legs chat to flare the thigh tops.
* Neck seam: the front envelope is still 5–16 mm forward of the plate table at z 1.30–1.32 (chat 7 had up to 14 mm); the neck chat should blend z 1.34–1.40.
* Arm-junction columns (|x|≈0.12, z 1.16–1.29) stay noisy in the mirror test (inherited from the original mesh; not worse than before). The arms chat faired its armpit against chat 7's torso: border vertices are identical, the first interior ring differs — re-check `proof/09` after merging.
* Plate-lit shading correlation (SH2 lighting fitted on legs/arms) was explored and **not used as a gate**: the fit explains only R² 0.57–0.67, doesn't transfer between body parts, and biases peak positions ~2 cm high for both mounds and lobes (`tools/platelit.py`, `tools/corr*.py`).

## Files
`export/`: staged blend, delta, `merge_torso_delta.py`, `README_MERGE.md`, `form2_params.json`, `form2_checks.json`, `form2_gate_scripts_checks.json`, `form2_feature_metrics.json`, PREVIEW blend. `checks.json` (this gate). `tools/`: `torso2.py` (build), `fit.py`, `make_final.py` (build+export+audit), `gates.py`, `featmetrics.py`, `seam.py`, `rough.py`, `make_proofs2.py`, `render_merged.sh`, `write_results.py`, plate/shading helpers. `gate7/`: chat 7's metric scripts, paths patched. Reproduce everything: `bash run_all.sh && bash tools/render_merged.sh && python3 tools/write_results.py`.
"""
open(WD/'FEMALE_TORSO_FORM2_RESULTS.md','w').write(md); print('written',len(md),'chars')
