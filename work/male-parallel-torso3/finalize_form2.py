"""Merge audit + FBX report + form metrics -> proof/male-torso-form2-checks.json with computed gates.  python3.13 finalize_form2.py (PYTHONPATH=pylib)"""
import json, sys, subprocess
import numpy as np
sys.path.insert(0, '.')
from relcorr2 import corr_reg, REG
W = 'proof/male-torso-form2-checks.json'
d = json.load(open(W)); fb = json.load(open('export/export_form2.json'))
PASS1 = json.load(open('../male-parallel-torso/proof/male-torso-checks.json'))['form_correlation_vs_plate']       # the torso-1 PASS numbers (reference of this task)
# ---- form correlation on the staged blend's own clay renders (P2_basec = PASS state on the current snapshot, P2_finalc = FORM2)
form = {}
for s1, s2 in ((1.2, 5.0), (2.0, 8.0)):
    key = f'dog_{s1}_{s2}'; form[key] = {}
    for tag, nm in (('P2_basec', 'baseline'), ('P2_finalc', 'final')):
        form[key][nm] = {f'{v}_{rn}': round(corr_reg(v, tag, z0, z1, 0.12, s1, s2), 4) for v in ('front', 'back') for rn, (z0, z1) in REG.items()}
    b, f = form[key]['baseline'], form[key]['final']; form[key]['delta'] = {k: round(f[k] - b[k], 4) for k in b}
    form[key]['mean_baseline'] = round(float(np.mean(list(b.values()))), 4); form[key]['mean_final'] = round(float(np.mean(list(f.values()))), 4); form[key]['mean_delta'] = round(form[key]['mean_final'] - form[key]['mean_baseline'], 4)
form['torso1_PASS_reference_dog_1.2_5.0'] = PASS1['dog_1.2_5.0']['final']; form['torso1_PASS_reference_mean'] = PASS1['dog_1.2_5.0']['mean_final']
d['form_correlation_vs_plate'] = form
# ---- plate-lit (physical) metric, held-out back 3/4 panels, pec crease
def plate_lit(tag):
    out = {f'{v[0]}-{rn[:3]}': round(corr_reg(v, f'{tag}sh', z0, z1, 0.12, 1.2, 5.0), 3) for v in ('front', 'back') for rn, (z0, z1) in REG.items()}; out['mean'] = round(float(np.mean(list(out.values()))), 3); return out
d['plate_lit_correlation'] = dict(baseline=plate_lit('base'), final=plate_lit('final'))
from pmo_val import *
V = np.load('data/V_base.npy'); Pf = np.load('data/V_final.npy'); T = Torso(V); T.make_basis(0.012, 0.009); VL = Val(T)
d['heldout_back_3q_panels'] = dict(baseline={k: round(v, 3) for k, v in VL.score(V).items()}, final={k: round(v, 3) for k, v in VL.score(Pf).items()}, note='sheet 3/4 back panels q3BL/q3BR: never used in the fit; limb-fitted camera-frame SH lighting, high-passed shading correlation over the visible torso-zone vertices')
import pecprof_lib as PP
d['pec_crease'] = PP.measure(['base', 'final'])
# ---- fit description
d['fit'] = json.load(open('data/params_FORM2.json'))
# ---- gates
sil = d['silhouette_pct']['body']; sb = d['silhouette_pct_baseline_body']; dep = d['torso_depth_vs_side_plates_mm_z0.92_1.30']
dz0, dz1 = d['dihedral_zone_baseline'], d['dihedral_zone_final']; fk = form['dog_1.2_5.0']; ref = PASS1['dog_1.2_5.0']['final']
G = {}
G['ZONE_OUTSIDE_MOVED=0'] = (d['zone']['verts_moved_outside_zone'] == 0 and all(v == 0 for v in d['moved_by_category'].values()) and d['face_m_bit_identical'] is True and d['cameras_empties_identical'] and d['vertex_groups_identical'],
                             f"moved outside zone {d['zone']['verts_moved_outside_zone']}; head/neck, legs, feet, hands, arms categories = {[d['moved_by_category'][k] for k in d['moved_by_category']]}; Face_M + LOOP_* groups identical; {d['zone']['verts_moved_inside_zone']} verts moved inside the zone")
G['TOPOLOGY_IDENTICAL'] = (d['topology_identical'] and d['tris'] == 60358 and d['boundary_edges'] == 92 and d['nonmanifold_edges'] == 2 and not d['nan_or_inf'] and abs(d['height_m'] - d['height_m_baseline']) < 1e-9 and d['objects_identical'] and d['materials_identical'],
                           f"{d['verts']} verts / {d['tris']} tris, face list identical, boundary/non-manifold edges 92/2 as baseline, height {d['height_m']:.6f} m unchanged")
G['SIL_FRONT_BACK<=5.0%'] = (sil['bald_front'] <= 5.0 and sil['bald_back'] <= 5.0 and sil['bald_front'] <= sb['bald_front'] + 0.05 and sil['bald_back'] <= sb['bald_back'] + 0.05,
                             f"front {sil['bald_front']:.4f} % (before {sb['bald_front']:.4f}), back {sil['bald_back']:.4f} % (before {sb['bald_back']:.4f}); pure front/back vertex moves leave the outline unchanged")
G['DEPTH_vs_SIDE_hold'] = (dep['final']['rms_mm'] <= 3.0 and abs(dep['final']['mean_deficit_mm']) <= 3.0,
                           f"depth deficit vs left/right plate silhouettes z 0.92-1.30: rms {dep['baseline']['rms_mm']:.2f} -> {dep['final']['rms_mm']:.2f} mm (limit 3.0), mean {dep['baseline']['mean_deficit_mm']:+.2f} -> {dep['final']['mean_deficit_mm']:+.2f} mm")
reg6 = ['front_chest', 'front_abdomen', 'front_pelvis', 'back_chest', 'back_abdomen', 'back_pelvis']
G['FORM_mean_beats_+0.146'] = (fk['mean_final'] > PASS1['dog_1.2_5.0']['mean_final'] and all(fk['final'][k] > ref[k] for k in reg6) and fk['final']['front_chest'] > ref['front_chest'] and fk['final']['back_chest'] > ref['back_chest'],
                               f"mean of 6 torso regions {PASS1['dog_1.2_5.0']['mean_final']:+.3f} (PASS) -> {fk['mean_final']:+.3f} (target >= +0.25: {'met' if fk['mean_final'] >= 0.25 else 'NOT met'}); front chest {ref['front_chest']:+.3f} -> {fk['final']['front_chest']:+.3f}, back upper {ref['back_chest']:+.3f} -> {fk['final']['back_chest']:+.3f}; every one of the 6 regions above its PASS value")
G['PELVIS_SHELF_clean'] = (dz1['pelvis_band_over_55'] == 0 and dz1['pelvis_band_over_55'] <= dz0['pelvis_band_over_55'] and dz1['over_55'] <= dz0['over_55'] and dz1['pelvis_band_max'] <= max(60.0, dz0['pelvis_band_max'] + 5),
                           f"pelvis band z 0.77-0.90: edges >55 deg {dz0['pelvis_band_over_55']} -> {dz1['pelvis_band_over_55']}, max crease {dz0['pelvis_band_max']:.0f} -> {dz1['pelvis_band_max']:.0f} deg; whole zone >55 deg: {dz0['over_55']} -> {dz1['over_55']}")
G['MESH_QUALITY'] = (d['face_flips_dot<0'] == 0 and d['zero_area_faces'] == 0 and d['zone_border']['max_disp_mm'] <= 1.0 and d['min_face_area_mm2_zone'] >= 0.9 * d['min_face_area_mm2_zone_baseline'],
                     f"flipped faces {d['face_flips_dot<0']}; zone-border displacement max {d['zone_border']['max_disp_mm']:.3f} mm; min face area {d['min_face_area_mm2_zone']:.2f} mm2 (before {d['min_face_area_mm2_zone_baseline']:.2f}); zone dihedral p99 {dz0['p99']:.1f} -> {dz1['p99']:.1f} deg")
G['FBX_REIMPORT'] = (fb['max_nearest_distance_mm'] <= 0.001 and fb['imported_tris'] == 60358 and abs(fb['reimport_height_m'] - d['height_m']) < 1e-4,
                     f"FBX re-import: {fb['imported_tris']} tris, max vertex error {fb['max_nearest_distance_mm']:.5f} mm, height {fb['reimport_height_m']:.6f} m")
d['fbx'] = dict(path='work/male-parallel-torso3/export/HeroBase_Male_Body_form2.fbx', sha256=fb['fbx_sha256'], imported_tris=fb['imported_tris'], max_reimport_error_mm=fb['max_nearest_distance_mm'], reimport_height_m=fb['reimport_height_m'])
d['gates'] = {k: dict(result='PASS' if v[0] else 'FAIL', evidence=v[1]) for k, v in G.items()}
d['GATE_MALE_TORSO_FORM2'] = 'PASS' if all(v[0] for v in G.values()) else 'FAIL'
json.dump(d, open(W, 'w'), indent=1)
print('GATE: MALE_TORSO_FORM2', d['GATE_MALE_TORSO_FORM2'])
for k, v in d['gates'].items(): print(f"  {k:26s} {v['result']}  {v['evidence']}")
print('plate-lit', d['plate_lit_correlation']); print('heldout', d['heldout_back_3q_panels']['baseline'], d['heldout_back_3q_panels']['final']); print('pec', d['pec_crease'])
