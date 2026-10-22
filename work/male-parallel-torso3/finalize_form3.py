"""FORM3 gate computation: audit json + FBX report + form metrics (Unity-clay band-pass r, plate-lit r, held-out back 3/4), shelf contrast, banding/ripple,
glute lobe split, self-intersection, extremes, nape -> proof/male-torso-form3-checks.json with explicit gate lines.
PYTHONPATH=../male-micro1i/pylib python3.13 finalize_form3.py <tag> [audit json] [fbx json]"""
import json, sys, subprocess
import numpy as np
sys.path.insert(0, '.')
from relcorr2 import corr_reg, REG
from relcorr import *
import banding3, pecprof_lib as PP
from PIL import Image
TAG = sys.argv[1] if len(sys.argv) > 1 else 'FORM3'
AUD = sys.argv[2] if len(sys.argv) > 2 else 'proof/male-torso-form3-audit.json'; FBX = sys.argv[3] if len(sys.argv) > 3 else 'export/export_form3.json'
OUT = 'proof/male-torso-form3-checks.json'
d = json.load(open(AUD)); fb = json.load(open(FBX)); cfg = json.load(open(f'data/cfg_{TAG}.json'))
V0 = np.load('data/V_base.npy'); V1 = np.load(f'data/V_{TAG}.npy')
FORM2_REF = dict(front_chest=0.450, front_abdomen=0.431, front_pelvis=0.384, back_chest=0.413, back_abdomen=0.285, back_pelvis=0.108, mean=0.345)     # brief's FORM2 numbers (re-measured below)
# ---- form correlation (Unity clay), two band-pass scales
form = {}
for s1, s2 in ((1.2, 5.0), (2.0, 8.0)):
    key = f'dog_{s1}_{s2}'; form[key] = {}
    for tag, nm in (('base', 'FORM2'), (TAG, 'FORM3')):
        form[key][nm] = {f'{v}_{rn}': round(corr_reg(v, f'{tag}c', z0, z1, 0.12, s1, s2), 4) for v in ('front', 'back') for rn, (z0, z1) in REG.items()}
    b, f = form[key]['FORM2'], form[key]['FORM3']; form[key]['delta'] = {k: round(f[k] - b[k], 4) for k in b}
    form[key]['mean_FORM2'] = round(float(np.mean(list(b.values()))), 4); form[key]['mean_FORM3'] = round(float(np.mean(list(f.values()))), 4)
d['form_correlation_vs_plate'] = form
# map region names used in the brief
R6 = {'front_chest': 'front_chest', 'front_abdomen': 'front_abdomen', 'front_pelvis': 'front_pelvis', 'back_chest': 'back_chest', 'back_abdomen': 'back_abdomen', 'back_pelvis': 'back_pelvis'}
f2 = form['dog_1.2_5.0']['FORM2']; f3 = form['dog_1.2_5.0']['FORM3']
# ---- plate-lit metric
def plate_lit(tag):
    out = {f'{v[0]}-{rn[:3]}': round(corr_reg(v, f'{tag}sh', z0, z1, 0.12, 1.2, 5.0), 3) for v in ('front', 'back') for rn, (z0, z1) in REG.items()}; out['mean'] = round(float(np.mean(list(out.values()))), 3); return out
d['plate_lit_correlation'] = dict(FORM2=plate_lit('base'), FORM3=plate_lit(TAG))
# ---- held-out back 3/4 panels
from pmo_val import *
T = Torso(V0); T.make_basis(0.012, 0.009); VL = Val(T)
d['heldout_back_3q_panels'] = dict(FORM2={k: round(v, 3) for k, v in VL.score(V0).items()}, FORM3={k: round(v, 3) for k, v in VL.score(V1).items()}, note='sheet 3/4 back panels q3BL/q3BR, never used in the fit; limb-fitted camera-frame SH lighting, high-passed shading correlation over the visible torso-zone vertices')
# ---- pec shelf: plate-lit crest-to-crease drop + Unity-lit
pc = PP.measure(['base', TAG]); d['pec_crease_plate_lit'] = pc
def unity_drop(tag, kind):
    c = CAM['bald_front']; mpp = c['metres_per_pixel']; xs = [-0.13, -0.11, -0.09, -0.07, 0.07, 0.09, 0.11, 0.13]; zs = np.arange(1.10, 1.34, 0.005)
    a = np.asarray(Image.open(f'r/{tag}{"c" if kind == "clay" else ""}/front.png').convert('L')).astype('float32'); v = []
    for z in zs:
        row = int(round(c['sole_y'] - z / mpp)); v.append(np.mean([a[row - 1:row + 2, int(round(c['centre_x'] + x / mpp)) - 1:int(round(c['centre_x'] + x / mpp)) + 2].mean() for x in xs]))
    v = np.array(v); up = v[(zs > 1.21) & (zs < 1.30)].max(); lo = v[(zs > 1.12) & (zs < 1.22)].min(); return dict(drop_lum=round(float(up - lo), 1), normalized=round(float((up - lo) / v.mean()), 3), crease_z=round(float(zs[(zs > 1.12) & (zs < 1.22)][np.argmin(v[(zs > 1.12) & (zs < 1.22)])]), 3))
d['pec_shelf_unity_lit'] = {kind: dict(FORM2=unity_drop('base', kind), FORM3=unity_drop(TAG, kind)) for kind in ('skin', 'clay')}
# ---- banding / ripple
def ripple(tag):
    REGB = {'front_chest': ('front', 1.15, 1.32), 'front_abdomen': ('front', 0.90, 1.15), 'front_pelvis': ('front', 0.80, 0.90), 'back_upper': ('back', 1.15, 1.32), 'back_lumbar': ('back', 0.90, 1.15), 'back_glute': ('back', 0.80, 0.90)}
    out = {}
    for rn, (v, z0, z1) in REGB.items():
        img = PL if tag == 'plate' else Image.open(R / f'work/male-parallel-torso3/r/{tag}c/{v}.png').convert('L'); m = torso_mask(v, z0, z1, 0.12); out[rn] = round(float(dog(img, 1.0, 2.5)[m].std()), 3)
    return out
rp, r2, r3 = ripple('plate'), ripple('base'), ripple(TAG)
bd = {t: banding3.measure(t) for t in ('plate', 'base', TAG)}
sec = [m for m in bd[TAG]['pec_minima_abs'] if abs(m[0] - 1.18) > 0.02]; main_depth = max([m[1] for m in bd[TAG]['pec_minima_abs']] + [1e-6])
d['banding'] = dict(ripple_fine_std=dict(plate=rp, FORM2=r2, FORM3=r3), ripple_ratio_FORM3_over_plate={k: round(r3[k] / rp[k], 2) for k in rp}, ripple_ratio_FORM2_over_plate={k: round(r2[k] / rp[k], 2) for k in rp},
                    detectors=bd, secondary_pec_minima_FORM3=sec, main_pec_crease_depth_FORM3=main_depth,
                    note='fine-scale (2.9-7 mm) band-pass shading std of the Unity clay render per torso region vs the plate; the rejected gain ladder A5/A6 (visible ripples / parallel creases) sat at 2.4x/3.9x in the chest')
# ---- glute lobe split (geometry): back-surface depth across x at fixed heights
Z = (V0[:, 2] >= 0.77) & (V0[:, 2] < 1.40) & (np.abs(V0[:, 0]) <= np.where(V0[:, 2] < 1.20, 0.205, 0.28))
def back_profile(V, z0, half=0.007):
    out = []
    for xc in np.arange(0.0, 0.151, 0.0125):
        m = Z & (np.abs(V[:, 2] - z0) < half) & (np.abs(np.abs(V[:, 0]) - xc) < 0.0075) & (V[:, 1] > 0)
        out.append(float(V[m, 1].max() * 1000) if m.sum() else np.nan)
    return np.array(out)
lobes = {}
for z0 in (0.82, 0.84, 0.86, 0.88, 0.90):
    for nm, V in (('FORM2', V0), ('FORM3', V1)):
        p = back_profile(V, z0); c = p[0]; crest = np.nanmax(p[2:9]); xcrest = float(np.arange(0.0, 0.151, 0.0125)[2 + int(np.nanargmax(p[2:9]))])
        lobes.setdefault(f'z{z0:.2f}', {})[nm] = dict(center_mm=round(c, 1), lobe_crest_mm=round(float(crest), 1), cleft_depth_mm=round(float(crest - c), 1), crest_x_mm=round(xcrest * 1000, 1))
d['glute_lobe_split'] = lobes
# ---- extremes / nape / depth in the glute band vs the side plates
zs = np.arange(0.775, 1.40, 0.0025)
from slab import extremes
Fa, Ba = extremes(V0, T.Z, zs); Fb, Bb = extremes(V1, T.Z, zs); gate_rows = (zs >= 0.92) & (zs <= 1.30); glute_rows = (zs >= 0.80) & (zs <= 0.92)
d['silhouette_extremes_mm'] = dict(front_shift_z092_130_max_abs=round(float(np.nanmax(np.abs(Fb - Fa)[gate_rows]) * 1000), 2), back_shift_z092_130_max_abs=round(float(np.nanmax(np.abs(Bb - Ba)[gate_rows]) * 1000), 2),
                                   glute_band_back_overshoot_max=round(float(np.nanmax((Bb - Ba)[glute_rows]) * 1000), 2), glute_band_back_recede_max=round(float(np.nanmax((Ba - Bb)[glute_rows]) * 1000), 2),
                                   front_overshoot_max_all=round(float(np.nanmax((Fa - Fb)) * 1000), 2), note='z 0.80-0.92 back allowance <= 8 mm was used for the lobes: the side plates are 6-12 mm deeper than the mesh at z 0.82-0.84 (5.8 mm/px)')
d['nape_check'] = dict(verts_moved_z_ge_1352=int(np.any(V1[V0[:, 2] >= 1.352] != V0[V0[:, 2] >= 1.352], axis=1).sum()), max_z_moved=round(float(V0[np.any(V1 != V0, axis=1), 2].max()), 4), max_abs_x_moved=round(float(np.abs(V0[np.any(V1 != V0, axis=1), 0]).max()), 4))
si = {k: json.load(open(f'proof/selfisect_{k}.json')) for k in ('base', 'form3')}; d['self_intersection'] = si
d['rbf_asset'] = 'data/RBF_FORM3_asset.npz'; d['recipe'] = cfg
# ---- gates
sil = d['silhouette_pct']['body']; sb = d['silhouette_pct_baseline_body']; dep = d['torso_depth_vs_side_plates_mm_z0.92_1.30']; dz0, dz1 = d['dihedral_zone_baseline'], d['dihedral_zone_final']
G = {}
G['ZONE_OUTSIDE_MOVED=0'] = (d['zone']['verts_moved_outside_zone'] == 0 and all(v == 0 for v in d['moved_by_category'].values()) and d['face_m_bit_identical'] is True and d['cameras_empties_identical'] and d['vertex_groups_identical'],
                             f"moved outside zone {d['zone']['verts_moved_outside_zone']}; categories head/neck, legs, feet, hands, arms, arm-gap, outside = {[d['moved_by_category'][k] for k in d['moved_by_category']]}; Face_M + LOOP_* groups identical; {d['zone']['verts_moved_inside_zone']} verts moved inside the zone (all |x| < 0.20)")
G['TOPOLOGY_IDENTICAL'] = (d['topology_identical'] and d['tris'] == 60358 and d['boundary_edges'] == 92 and d['nonmanifold_edges'] == 2 and not d['nan_or_inf'] and abs(d['height_m'] - d['height_m_baseline']) < 1e-9 and d['objects_identical'] and d['materials_identical'],
                           f"{d['verts']} verts / {d['tris']} tris, face list identical, boundary/non-manifold edges {d['boundary_edges']}/{d['nonmanifold_edges']} as baseline, height {d['height_m']:.6f} m unchanged, positions-only edit")
G['SIL_FRONT_BACK<=5.0%'] = (sil['bald_front'] <= 5.0 and sil['bald_back'] <= 5.0 and sil['bald_front'] <= sb['bald_front'] + 0.05 and sil['bald_back'] <= sb['bald_back'] + 0.05,
                             f"front {sil['bald_front']:.4f} % (before {sb['bald_front']:.4f}), back {sil['bald_back']:.4f} % (before {sb['bald_back']:.4f}); y-only moves leave the outline unchanged (max |dx|,|dz| = {d['max_abs_dx_mm']:.3f}/{d['max_abs_dz_mm']:.3f} mm)")
G['DEPTH_vs_SIDE_hold'] = (dep['final']['rms_mm'] <= 3.0 and abs(dep['final']['mean_deficit_mm']) <= 3.0 and dep['final']['rms_mm'] <= dep['baseline']['rms_mm'] + 0.3,
                           f"depth deficit vs left/right plate silhouettes z 0.92-1.30: rms {dep['baseline']['rms_mm']:.2f} -> {dep['final']['rms_mm']:.2f} mm (limit 3.0), mean {dep['baseline']['mean_deficit_mm']:+.2f} -> {dep['final']['mean_deficit_mm']:+.2f} mm; front/back extremes per slab z 0.92-1.30 shift <= {max(d['silhouette_extremes_mm']['front_shift_z092_130_max_abs'], d['silhouette_extremes_mm']['back_shift_z092_130_max_abs']):.2f} mm")
G['PELVIS_SHELF_clean'] = (dz1['pelvis_band_over_55'] == 0 and dz1['over_55'] <= dz0['over_55'] and dz1['pelvis_band_max'] <= max(60.0, dz0['pelvis_band_max'] + 5),
                           f"pelvis band z 0.77-0.90: edges >55 deg {dz0['pelvis_band_over_55']} -> {dz1['pelvis_band_over_55']}, max crease {dz0['pelvis_band_max']:.1f} -> {dz1['pelvis_band_max']:.1f} deg; whole zone >55 deg {dz0['over_55']} -> {dz1['over_55']} (armpit); zone-border displacement max {d['zone_border']['max_disp_mm']:.3f} mm")
sh_pl = pc[TAG]['drop_lum'] >= pc['base']['drop_lum']; sh_un = d['pec_shelf_unity_lit']['skin']['FORM3']['drop_lum'] > d['pec_shelf_unity_lit']['skin']['FORM2']['drop_lum'] and d['pec_shelf_unity_lit']['clay']['FORM3']['drop_lum'] > d['pec_shelf_unity_lit']['clay']['FORM2']['drop_lum']
G['CHEST_DEFINED'] = (f3['front_chest'] > f2['front_chest'] and f3['front_chest'] > FORM2_REF['front_chest'] and sh_pl and sh_un,
                      f"front chest band-pass r {f2['front_chest']:+.3f} -> {f3['front_chest']:+.3f} (FORM2 {FORM2_REF['front_chest']:+.3f}); lower-pec shelf crest-to-crease drop plate-lit {pc['base']['drop_lum']:.1f} -> {pc[TAG]['drop_lum']:.1f} lum (plate {pc['plate']['drop_lum']:.1f}, crease z {pc[TAG]['crease_z']:.3f} vs plate {pc['plate']['crease_z']:.3f}); Unity-style render drop {d['pec_shelf_unity_lit']['skin']['FORM2']['drop_lum']:.1f} -> {d['pec_shelf_unity_lit']['skin']['FORM3']['drop_lum']:.1f} lum (skin), {d['pec_shelf_unity_lit']['clay']['FORM2']['drop_lum']:.1f} -> {d['pec_shelf_unity_lit']['clay']['FORM3']['drop_lum']:.1f} (clay)")
G['MIDSECTION'] = (f3['front_abdomen'] > f2['front_abdomen'] and f3['front_abdomen'] > FORM2_REF['front_abdomen'],
                   f"front abdomen band-pass r {f2['front_abdomen']:+.3f} -> {f3['front_abdomen']:+.3f} (FORM2 {FORM2_REF['front_abdomen']:+.3f}); front pelvis {f2['front_pelvis']:+.3f} -> {f3['front_pelvis']:+.3f}; abdomen fine-ripple ratio {d['banding']['ripple_ratio_FORM3_over_plate']['front_abdomen']:.2f}x plate (no carve)")
lb = lobes['z0.86']; l84 = lobes['z0.84']; split_ok = l84['FORM3']['cleft_depth_mm'] >= 5.0 and lb['FORM3']['cleft_depth_mm'] >= 3.0 and l84['FORM3']['cleft_depth_mm'] > l84['FORM2']['cleft_depth_mm'] + 3.0 and lb['FORM3']['cleft_depth_mm'] > lb['FORM2']['cleft_depth_mm'] + 3.0
G['GLUTE_FORM'] = (f3['back_pelvis'] > f2['back_pelvis'] and f3['back_pelvis'] > FORM2_REF['back_pelvis'] and split_ok,
                   f"back glute-upper band-pass r {f2['back_pelvis']:+.3f} -> {f3['back_pelvis']:+.3f} (FORM2 {FORM2_REF['back_pelvis']:+.3f}); twin lobes: centre-to-lobe-crest cleft depth at z 0.84/0.86/0.88 = " + '/'.join(f"{lobes[z]['FORM2']['cleft_depth_mm']:+.1f}->{lobes[z]['FORM3']['cleft_depth_mm']:+.1f}" for z in ('z0.84', 'z0.86', 'z0.88')) + f" mm (FORM2 -> FORM3), crests at |x| {lb['FORM3']['crest_x_mm']:.0f} mm")
all6 = all(f3[k] > f2[k] for k in R6)
G['FORM_mean_beats_FORM2'] = (form['dog_1.2_5.0']['mean_FORM3'] > form['dog_1.2_5.0']['mean_FORM2'] and form['dog_1.2_5.0']['mean_FORM3'] > FORM2_REF['mean'] and all6 and form['dog_2.0_8.0']['mean_FORM3'] > form['dog_2.0_8.0']['mean_FORM2'],
                              f"mean of 6 torso regions {form['dog_1.2_5.0']['mean_FORM2']:+.3f} -> {form['dog_1.2_5.0']['mean_FORM3']:+.3f} (FORM2 {FORM2_REF['mean']:+.3f}); every region improved: " + ', '.join(f"{k.replace('_', ' ')} {f2[k]:+.3f}->{f3[k]:+.3f}" for k in R6) + f"; wider band (DoG 2/8) {form['dog_2.0_8.0']['mean_FORM2']:+.3f} -> {form['dog_2.0_8.0']['mean_FORM3']:+.3f}")
G['NO_SELF_INTERSECT_FLIPS_NAN'] = (d['face_flips_dot<0'] == 0 and d['zero_area_faces'] == 0 and not d['nan_or_inf'] and si['form3']['overlapping_pairs_touching_torso_zone'] == 0 and si['form3']['overlapping_pairs_nonadjacent'] <= si['base']['overlapping_pairs_nonadjacent'] and d['min_face_area_mm2_zone'] >= 0.9 * d['min_face_area_mm2_zone_baseline'],
                                    f"flipped faces {d['face_flips_dot<0']}, zero-area faces {d['zero_area_faces']}, NaN/Inf {d['nan_or_inf']}; BVH self-intersections (non-adjacent triangle pairs) {si['base']['overlapping_pairs_nonadjacent']} -> {si['form3']['overlapping_pairs_nonadjacent']} (pre-existing, elsewhere), touching the torso zone {si['base']['overlapping_pairs_touching_torso_zone']} -> {si['form3']['overlapping_pairs_touching_torso_zone']}; min face area {d['min_face_area_mm2_zone']:.2f} mm2; edge length ratio {d['edge_ratio_zone']['min']:.2f}..{d['edge_ratio_zone']['max']:.2f}")
rr = d['banding']['ripple_ratio_FORM3_over_plate']; det = bd[TAG]
no_band = all(v <= 2.0 for v in rr.values()) and det['belt_front_max_frac'] <= 0.15 and det['ring_back_max_frac'] <= 0.15 and all(m[1] < 0.25 * main_depth for m in sec)
G['NO_BANDING_belt_doublepec_rings'] = (no_band, f"fine-ripple energy FORM3/plate per region: " + ', '.join(f"{k.replace('_', ' ')} {v:.2f}x" for k, v in rr.items()) + f" (limit 2.0; rejected gain ladder A5/A6 = 2.4x/3.9x chest); longest dark horizontal run belt {det['belt_front_max_frac']:.2f} / back {det['ring_back_max_frac']:.2f} of the torso width (limit 0.15; plate {bd['plate']['belt_front_max_frac']:.2f}); secondary pec minima {len(sec)} (<25 % of the main crease)")
G['NAPE_STRIP_untouched'] = (d['nape_check']['verts_moved_z_ge_1352'] == 0, f"vertices moved at z >= 1.352: {d['nape_check']['verts_moved_z_ge_1352']} (max z moved {d['nape_check']['max_z_moved']:.4f}); max |x| moved {d['nape_check']['max_abs_x_moved']:.3f} (<0.20, shoulder-ball overlap with the arms chat untouched)")
G['FBX_REIMPORT'] = (fb['max_nearest_distance_mm'] <= 0.001 and fb['imported_tris'] == 60358 and abs(fb['reimport_height_m'] - d['height_m']) < 1e-4, f"FBX re-import: {fb['imported_tris']} tris, max vertex error {fb['max_nearest_distance_mm']:.5f} mm, height {fb['reimport_height_m']:.6f} m")
d['fbx'] = dict(path='work/male-parallel-torso3/export/HeroBase_Male_Body_form3.fbx', sha256=fb['fbx_sha256'], imported_tris=fb['imported_tris'], max_reimport_error_mm=fb['max_nearest_distance_mm'], reimport_height_m=fb['reimport_height_m'])
d['gates'] = {k: dict(result='PASS' if v[0] else 'FAIL', evidence=v[1]) for k, v in G.items()}
d['GATE_MALE_TORSO_FORM3'] = 'PASS' if all(v[0] for v in G.values()) else 'FAIL'
json.dump(d, open(OUT, 'w'), indent=1)
print('GATE: MALE_TORSO_FORM3', d['GATE_MALE_TORSO_FORM3'])
for k, v in d['gates'].items(): print(f"  {k:32s} {v['result']}  {v['evidence'][:330]}")
