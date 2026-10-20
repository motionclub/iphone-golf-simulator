"""Merge audit + FBX report + form correlation -> proof/male-torso-checks.json with computed gates. python3.13 finalize_checks.py (PYTHONPATH=pylib)"""
import json, sys
import numpy as np
sys.path.insert(0, '.')
from relcorr2 import corr_reg, REG
W = 'proof/male-torso-checks.json'
d = json.load(open(W)); fb = json.load(open('export/export_torso.json'))
# ---- form correlation (clay renders at plate framing, band-passed, interior |x|<0.12)
form = {}
for s1, s2 in ((1.2, 5.0), (2.0, 8.0)):
    key = f'dog_{s1}_{s2}'; form[key] = {}
    for tag, nm in (('P_basec', 'baseline'), ('P_finalc', 'final')):
        form[key][nm] = {f'{v}_{rn}': round(corr_reg(v, tag, z0, z1, 0.12, s1, s2), 4) for v in ('front', 'back') for rn, (z0, z1) in REG.items()}
    b, f = form[key]['baseline'], form[key]['final']
    form[key]['delta'] = {k: round(f[k] - b[k], 4) for k in b}
    form[key]['mean_baseline'] = round(float(np.mean(list(b.values()))), 4); form[key]['mean_final'] = round(float(np.mean(list(f.values()))), 4)
    form[key]['mean_delta'] = round(form[key]['mean_final'] - form[key]['mean_baseline'], 4)
d['form_correlation_vs_plate'] = form
d['fbx'] = dict(path='work/male-parallel-torso/export/HeroBase_Male_Body_torso.fbx', sha256=fb['fbx_sha256'], imported_tris=fb['imported_tris'], max_reimport_error_mm=fb['max_nearest_distance_mm'], reimport_height_m=fb['reimport_height_m'])
# ---- gates
sil = d['silhouette_pct']['body']; sb = d['silhouette_pct_baseline_body']
outl = d['torso_outline_vs_plate_mm']; dep = d['torso_depth_vs_side_plates_mm_z0.92_1.30']['final']
dz0, dz1 = d['dihedral_zone_baseline'], d['dihedral_zone_final']; fk = form['dog_1.2_5.0']
G = {}
G['ZONE_OUTSIDE_MOVED=0'] = (d['zone']['verts_moved_outside_zone'] == 0 and all(v == 0 for v in d['moved_by_category'].values()) and d['face_m_bit_identical'] is True and d['cameras_empties_identical'],
                             f"moved outside zone {d['zone']['verts_moved_outside_zone']}; head/neck, legs, feet, hands, arms = {[d['moved_by_category'][k] for k in d['moved_by_category']]}; Face_M identical")
G['TOPOLOGY_IDENTICAL'] = (d['topology_identical'] and d['tris'] == 60358 and d['vertex_groups_identical'] and d['boundary_edges'] == 92 and d['nonmanifold_edges'] == 2 and not d['nan_or_inf'] and abs(d['height_m'] - d['height_m_baseline']) < 1e-9 and d['objects_identical'] and d['materials_identical'],
                           f"{d['verts']} verts / {d['tris']} tris unchanged, vertex groups identical, boundary/non-manifold edges 92/2 as baseline, height {d['height_m']:.6f} m unchanged")
G['MESH_QUALITY'] = (d['face_flips_dot<0'] == 0 and d['zero_area_faces'] == 0 and d['min_face_area_mm2_zone'] >= 0.9 * d['min_face_area_mm2_zone_baseline'] and dz1['over_55'] <= dz0['over_55'] and d['zone_border']['max_disp_mm'] <= 1.0 and d['edge_len_mm_zone']['final_max'] <= d['edge_len_mm_zone']['base_max'],
                     f"flipped faces {d['face_flips_dot<0']}; zone edges >55 deg {dz0['over_55']} -> {dz1['over_55']}; border displacement max {d['zone_border']['max_disp_mm']:.2f} mm; max edge {d['edge_len_mm_zone']['base_max']:.1f} -> {d['edge_len_mm_zone']['final_max']:.1f} mm")
G['SIL_FRONT_BACK<=5.0%'] = (sil['bald_front'] <= 5.0 and sil['bald_back'] <= 5.0 and sil['bald_front'] <= sb['bald_front'] + 0.05 and sil['bald_back'] <= sb['bald_back'] + 0.05,
                             f"front {sil['bald_front']:.4f} % (baseline {sb['bald_front']:.4f}), back {sil['bald_back']:.4f} % (baseline {sb['bald_back']:.4f})")
oF, oB = outl['final'], outl['baseline']
G['TORSO_OUTLINE_NOT_WORSE'] = (oF['bald_front']['rows_over_1px'] <= oB['bald_front']['rows_over_1px'] and oF['bald_back']['rows_over_1px'] <= oB['bald_back']['rows_over_1px'] and oF['bald_front']['max_abs_mm'] <= oB['bald_front']['max_abs_mm'] + 0.1 and oF['bald_back']['max_abs_mm'] <= oB['bald_back']['max_abs_mm'] + 0.1,
                                f"half-width rows >1 px off plate (z 0.80-1.36): front {oB['bald_front']['rows_over_1px']} -> {oF['bald_front']['rows_over_1px']}, back {oB['bald_back']['rows_over_1px']} -> {oF['bald_back']['rows_over_1px']}")
bdep = d['torso_depth_vs_side_plates_mm_z0.92_1.30']['baseline']
G['TORSO_DEPTH_vs_SIDE_PLATES'] = (dep['rms_mm'] <= 6.0 and abs(dep['mean_deficit_mm']) <= 3.0,
                                   f"front-to-back depth deficit vs left/right plate silhouettes, z 0.92-1.30: rms {bdep['rms_mm']:.1f} -> {dep['rms_mm']:.1f} mm, mean {bdep['mean_deficit_mm']:+.1f} -> {dep['mean_deficit_mm']:+.1f} mm (1 plate px = 5.8 mm)")
G['PELVIS_SHELF_REMOVED'] = (dz1['pelvis_band_over_55'] == 0 and dz1['pelvis_band_max'] <= 0.5 * dz0['pelvis_band_max'],
                             f"pelvis band z 0.77-0.90: edges >55 deg {dz0['pelvis_band_over_55']} -> {dz1['pelvis_band_over_55']}, max dihedral {dz0['pelvis_band_max']:.0f} -> {dz1['pelvis_band_max']:.0f} deg")
fr = [fk['delta'][k] for k in fk['delta'] if k.startswith('front')]
G['FORM_vs_PLATE_RELIEF'] = (fk['mean_delta'] >= 0.05 and all(x > 0 for x in fr),
                             f"band-passed shading correlation with plate, 6 torso regions: mean {fk['mean_baseline']:+.3f} -> {fk['mean_final']:+.3f}; front chest/abdomen/pelvis {fk['baseline']['front_chest']:+.2f}/{fk['baseline']['front_abdomen']:+.2f}/{fk['baseline']['front_pelvis']:+.2f} -> {fk['final']['front_chest']:+.2f}/{fk['final']['front_abdomen']:+.2f}/{fk['final']['front_pelvis']:+.2f}")
G['FBX_REIMPORT'] = (fb['max_nearest_distance_mm'] <= 0.001 and fb['imported_tris'] == 60358 and abs(fb['reimport_height_m'] - d['height_m']) < 1e-4,
                     f"FBX re-import: {fb['imported_tris']} tris, max vertex error {fb['max_nearest_distance_mm']:.5f} mm, height {fb['reimport_height_m']:.6f} m")
d['gates'] = {k: dict(result='PASS' if v[0] else 'FAIL', evidence=v[1]) for k, v in G.items()}
d['GATE_MALE_TORSO'] = 'PASS' if all(v[0] for v in G.values()) else 'FAIL'
json.dump(d, open(W, 'w'), indent=1)
print('GATE: MALE_TORSO', d['GATE_MALE_TORSO'])
for k, v in d['gates'].items(): print(f"  {k:30s} {v['result']}  {v['evidence']}")
print(json.dumps({k: form[k]['baseline'] for k in form}, indent=0)[:600]); print(json.dumps({k: form[k]['final'] for k in form}, indent=0)[:600])
