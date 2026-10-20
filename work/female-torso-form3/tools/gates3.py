"""FEMALE_TORSO_FORM3 gate evaluator -> checks.json (+ printed GATE lines).

Hard / objective lines (zone, topology, silhouettes, seams, self-intersection, NaN, flips) are measured by make_final3.py + the chat-7 gate scripts.
LIKENESS lines have two parts:
  (a) objective plate-agreement + anti-box measurements defined BEFORE looking at the final result (below), and
  (b) the visual plate B/A + clay + mirror-stripe check (proof/04..07) - flagged `eye_check_required`: the verdict on (b) is the author's reading, Adnan's eye is the real test.
"""
import sys, json, hashlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form3/tools')
import numpy as np
from torso3 import *
import torso2 as t2
import seam
from photo3 import *
from footprint import grid_surface
from opt3 import cleft_depth_ratio

ck = json.load(open(WD / 'export/form3_checks.json'))
g7 = json.load(open(WD / 'export/form3_gate_scripts_checks.json'))
co = np.load(WD / 'data/co_FORM3_final.npy').astype(np.float64)
f2 = np.load(WD / 'data/co_start_f2.npy')
c7 = np.load(WD / 'data/co_chat7.npy')
lines = []


def L(group, name, value, cond, limit, basis, eye=False):
    lines.append(dict(group=group, line=name, value=value, limit=limit, result='PASS' if cond else 'FAIL', basis=basis, **({'eye_check_required': True} if eye else {})))


# ------------------------------------------------------------------------------------------------------------------- zone / topology
L('ZONE_OUTSIDE', 'moved outside zone vs FORM2 start (6859d958)', ck['moved_outside_zone_vs_form2_start'], ck['moved_outside_zone_vs_form2_start'] == 0, '== 0', 'float32 exact, audit dumps')
L('ZONE_OUTSIDE', 'moved outside zone vs ORIGINAL ArtDir 200dc3b9', ck['moved_outside_zone_vs_artdir_200dc3b9'], ck['moved_outside_zone_vs_artdir_200dc3b9'] == 0, '== 0', 'float32 exact')
L('ZONE_OUTSIDE', 'zone border vertices moved (238; neck / arm junction / leg tops) vs ArtDir', ck['border_vertices_moved_vs_artdir'], ck['border_vertices_moved_vs_artdir'] == 0, '== 0', 'bit-identical to the original ring the arms/legs/neck seams rely on')
L('ZONE_OUTSIDE', 'zone border vertices moved vs FORM2 start', ck['border_vertices_moved_vs_form2_start'], ck['border_vertices_moved_vs_form2_start'] == 0, '== 0', '')
topo = ck['topology']
tp = all(v for k, v in topo.items() if isinstance(v, bool))
L('TOPOLOGY', 'poly/loop/edge/material/smooth/UV/custom-normal raw codes/Hair/other objects identical (vs FORM2 start AND vs ArtDir)', tp, tp, 'all True', 'audit dumps')
L('TOPOLOGY', 'triangles (budget 35-50k)', topo['tris_form2_start_vs_new'][1], topo['tris_form2_start_vs_new'][1] == topo['tris_form2_start_vs_new'][0] and topo['tris_form2_start_vs_new'][1] <= 50000, 'unchanged, <=50k', 'no densify')
L('TOPOLOGY', 'flipped zone triangles vs original', ck['flipped_zone_tris_vs_original'], ck['flipped_zone_tris_vs_original'] == 0, '== 0', 'face-normal dot < 0')
L('TOPOLOGY', 'zone triangles turned >60 deg vs original', ck['zone_tris_turned_gt60deg'], ck['zone_tris_turned_gt60deg'] <= 2, '<= 2', '')
# ------------------------------------------------------------------------------------------------------------------- silhouettes
sx = g7['side_profile_torso_band_xor_z0.82_1.30']['after']
L('SIDE_SIL', 'side-profile torso-band XOR vs plate (z .82-1.30)', round(sx, 4), sx <= 0.05, '<= 0.05', 'chat-7 gate script metrics_side.py')
fb = g7['torso_visible_edge_run_xor_rows_z0.82_1.165']['after']
L('FRONT_BACK_TORSO_EDGE', 'front torso visible-edge XOR vs bald plate', round(fb['front'], 4), fb['front'] <= 0.05, '<= 0.05', 'chat-7 gate script metrics_fb.py')
L('FRONT_BACK_TORSO_EDGE', 'back torso visible-edge XOR vs bald plate', round(fb['back'], 4), fb['back'] <= 0.05, '<= 0.05', '')
# ------------------------------------------------------------------------------------------------------------------- seams (hold FORM2 limits)
bs = ck['border_steps_mm']['form3']
L('SEAM_CLEAN', 'displacement step at a pinned border edge, legs (mm)', round(bs['legs']['max_mm'], 2), bs['legs']['max_mm'] <= 8.0, '<= 8 (FORM2 limit)', '|d(v)-d(border)| over one edge (~12 mm)')
L('SEAM_CLEAN', '... arm junction (mm)', round(bs['arm']['max_mm'], 2), bs['arm']['max_mm'] <= 10.0, '<= 10 (FORM2 limit)', '')
L('SEAM_CLEAN', '... neck/shoulder top (mm)', round(bs['top']['max_mm'], 2), bs['top']['max_mm'] <= 1.0, '<= 1 (FORM2 limit)', '')
dh = ck['dihedral']
L('SEAM_CLEAN', 'zone edges with dihedral >40 deg (count)', dh['form3']['n_gt40'], dh['form3']['n_gt40'] <= dh['original']['n_gt40'], f"<= original ({dh['original']['n_gt40']})", 'inherited mesh creases are not increased')
L('SEAM_CLEAN', 'worst zone dihedral (deg)', round(dh['form3']['max_deg'], 1), dh['form3']['max_deg'] <= dh['original']['max_deg'] + 0.5, f"<= original ({dh['original']['max_deg']:.1f})", '')
rg = ck['bi_laplacian_roughness_mm_zone_interior']
L('SEAM_CLEAN', 'bi-Laplacian roughness mean (mm), zone interior', round(rg['form3']['mean'], 3), rg['form3']['mean'] <= rg['form2']['mean'] * 1.15 + 1e-9, f"<= 1.15 x FORM2 ({rg['form2']['mean']:.3f})", 'smoothness not worse than FORM2')
L('SEAM_CLEAN', 'bi-Laplacian roughness p95 (mm)', round(rg['form3']['p95'], 3), rg['form3']['p95'] <= rg['form2']['p95'] * 1.15 + 1e-9, f"<= 1.15 x FORM2 ({rg['form2']['p95']:.3f})", '')
# ------------------------------------------------------------------------------------------------------------------- no self-intersect / NaN
si = ck['self_intersection_pairs']
L('NO_SELF_INTERSECT', 'no NaN/inf coordinates', ck['nan_or_inf'], ck['nan_or_inf'] == 0, '== 0', '')
L('NO_SELF_INTERSECT', 'exact triangle-triangle intersecting pairs touching the torso zone (original / FORM2 / FORM3)', [si['original']['touching_torso_zone'], si['form2']['touching_torso_zone'], si['form3']['touching_torso_zone']], si['form3']['touching_torso_zone'] <= si['original']['touching_torso_zone'], '<= original (0)', 'mathutils BVHTree.overlap = exact tri-tri test; the 4,444 whole-mesh pairs (identical in all three files) are eyes/teeth/ears/hands, none in the torso zone')
L('NO_SELF_INTERSECT', 'whole-mesh intersecting pairs unchanged vs original', [si['original']['whole_mesh'], si['form3']['whole_mesh']], si['form3']['whole_mesh'] <= si['original']['whole_mesh'], '<= original', '')
nf = ck['custom_normals_vs_geometry_deg_zone']
L('NO_SELF_INTERSECT', 'decoded custom normals still follow the geometry in the zone (median / p95 deg, FORM3 vs original)', [round(nf['form3']['median_deg'], 2), round(nf['form3']['p95_deg'], 2), round(nf['original']['median_deg'], 2), round(nf['original']['p95_deg'], 2)], nf['form3']['median_deg'] <= nf['original']['median_deg'] + 0.5 and nf['form3']['p95_deg'] <= nf['original']['p95_deg'] + 1.0, 'within 0.5 / 1.0 deg of the original', 'shading in Unity/Blender is faithful to the new surface (raw codes untouched)')
# ------------------------------------------------------------------------------------------------------------------- likeness : objective parts
P = json.load(open(WD / 'export/form3_params.json'))
N0 = vertex_normals(co, TRI); N2 = vertex_normals(f2, TRI)
lt = np.array(LIGHT)
pb_front = roi_box('front', -0.115, 0.115, 1.14, 1.30); pb_back = roi_box('back', -0.14, 0.14, 0.80, 0.97)
lf = lt.copy(); lf[1:] *= 2.5; lb = lt.copy(); lb[1:] *= 2.0
rb3 = compare(co, 'front', pb_front, light=lf, normals=N0); rb2 = compare(f2, 'front', pb_front, light=lf, normals=N2)
rg3 = compare(co, 'back', pb_back, light=lb, normals=N0); rg2 = compare(f2, 'back', pb_back, light=lb, normals=N2)
unedited = {}
for nm, (view, x0, x1, z0, z1) in {'abdomen front': ('front', -0.10, 0.10, 0.95, 1.12), 'thighs front': ('front', -0.17, 0.17, 0.25, 0.70), 'thighs back': ('back', -0.17, 0.17, 0.25, 0.70), 'upper arm L front': ('front', -0.26, -0.14, 1.05, 1.30)}.items():
    r = compare(co, view, roi_box(view, x0, x1, z0, z1), light=(lf if view == 'front' else lb), normals=N0); unedited[nm] = round(r['ncc'], 3)
base_ncc = float(np.mean(list(unedited.values())))
ho = {}
for tag_, c_ in (('form3', co), ('form2', f2)):
    ho[tag_] = dict(bust=compare_sheet(c_, 'front', -0.115, 0.115, 1.14, 1.30, light=lf), glute=compare_sheet(c_, 'back', -0.14, 0.14, 0.80, 0.97, light=lb))
L('BUST_LIKENESS', 'plate-lit band-pass NCC in the bust ROI (front, |x|<.115, z 1.14-1.30) vs plate', round(rb3['ncc'], 3), rb3['ncc'] >= max(rb2['ncc'] + 0.10, base_ncc), f"FORM2 {rb2['ncc']:.3f} + 0.10 and >= mean NCC of unedited regions ({base_ncc:.2f}: {unedited})", 'lighting fitted on unedited regions of the plate; photo3.py')
L('GLUTE_LIKENESS', 'plate-lit band-pass NCC in the glute ROI (back, |x|<.14, z .80-.97) vs plate', round(rg3['ncc'], 3), rg3['ncc'] >= max(rg2['ncc'] + 0.10, base_ncc), f"FORM2 {rg2['ncc']:.3f} + 0.10 and >= {base_ncc:.2f}", 'same pipeline')
L('BUST_LIKENESS', 'held-out check on the multi-angle SHEET front panel (different render/scale): NCC not worse than FORM2 by > 0.05', [round(ho['form3']['bust']['ncc'], 3), round(ho['form2']['bust']['ncc'], 3)], ho['form3']['bust']['ncc'] >= ho['form2']['bust']['ncc'] - 0.05, 'form3 >= form2 - 0.05', 'guards against over-fitting the bald plate (sheet figure has bigger hips, thinner arms; 5.9 mm/px)')
L('GLUTE_LIKENESS', 'held-out check on the multi-angle SHEET back panel: NCC not worse than FORM2 by > 0.05', [round(ho['form3']['glute']['ncc'], 3), round(ho['form2']['glute']['ncc'], 3)], ho['form3']['glute']['ncc'] >= ho['form2']['glute']['ncc'] - 0.05, 'form3 >= form2 - 0.05', 'same')
# ---- anti-box measurements (bust)
xs = np.arange(-0.14, 0.1401, 0.002); zs = np.arange(1.10, 1.34, 0.002)
Gf = grid_surface(co, 'front', xs, zs)
base_wall = grid_surface(build3({**P, 'bm_list': [dict(c, H=0.0) for c in P['bm_list']], 'bp_H': 0.0, 'st_R3': 0.0, 'mo_R': 0.0, 'fl_k': 0.0, 'gm_R': 0.0}, *[np.array(x) for x in np.load(WD / 'export/form3_wall_corrections.npy')]), 'front', xs, zs)
hgt = (base_wall - Gf)                      # + forward growth relative to the wall without bust features (m)
ix = lambda x: int(round((x - xs[0]) / 0.002)); iz = lambda z: int(round((z - zs[0]) / 0.002))
res_b = {}
for side, sg in (('R', 1), ('L', -1)):
    cols = np.where((sg * xs >= 0.04) & (sg * xs <= 0.125))[0]; rows = np.where((zs >= 1.17) & (zs <= 1.29))[0]
    sub = Gf[np.ix_(rows, cols)]; i, j = np.unravel_index(np.argmin(sub), sub.shape)
    xa, za = xs[cols[j]], zs[rows[i]]
    # curvature radii at the apex (parabola fits over +-2.5 cm)
    ph = np.polyfit(xs[(np.abs(xs - xa) < 0.025)] - xa, Gf[iz(za), (np.abs(xs - xa) < 0.025)], 2)
    pv = np.polyfit(zs[(np.abs(zs - za) < 0.025)] - za, Gf[(np.abs(zs - za) < 0.025), ix(xa)], 2)
    res_b[side] = dict(apex_x=float(xa), apex_z=float(za), r_h_cm=float(abs(1 / (2 * ph[0])) * 100 if abs(ph[0]) > 1e-9 else 999), r_v_cm=float(abs(1 / (2 * pv[0])) * 100 if abs(pv[0]) > 1e-9 else 999))
rh = 0.5 * (res_b['R']['r_h_cm'] + res_b['L']['r_h_cm']); rv = 0.5 * (res_b['R']['r_v_cm'] + res_b['L']['r_v_cm'])
L('BUST_LIKENESS', 'mound apex curvature radius, horizontal / vertical (cm): round, not flat or pointed', [round(rh, 1), round(rv, 1)], 3.0 <= rh <= 20.0 and 3.0 <= rv <= 20.0, 'both 3..20', 'FORM2 boxes had flat fronts (large radius) and hard shelves')
ar = np.load(WD / 'data/dihedral_bust_region.npy') if (WD / 'data/dihedral_bust_region.npy').exists() else None
a1 = seam.dihedral(co); a0 = seam.dihedral(CO0); a2 = seam.dihedral(f2)
mid = 0.5 * (co[seam.PAIR_E[:, 0]] + co[seam.PAIR_E[:, 1]])
nb_ = ~(BORDER[seam.PAIR_E[:, 0]] | BORDER[seam.PAIR_E[:, 1]]) & (a0 <= 15.0)      # border-adjacent edges are governed by the SEAM_CLEAN step gates
bust_reg = seam.ZPAIR & nb_ & (mid[:, 2] >= 1.14) & (mid[:, 2] <= 1.32) & (np.abs(mid[:, 0]) <= 0.115) & (mid[:, 1] < 0)
glu_reg = seam.ZPAIR & nb_ & (mid[:, 2] >= 0.80) & (mid[:, 2] <= 1.02) & (np.abs(mid[:, 0]) <= 0.15) & (mid[:, 1] > 0)
L('BUST_LIKENESS', 'no hard shelf / crease: worst dihedral on the front surface, bust region (deg)', round(float(a1[bust_reg].max()), 1), a1[bust_reg].max() <= 30.0, '<= 30 (interior edges that were smooth, <=15 deg, in the original)', 'a new hard line = high dihedral between adjacent triangles; border-adjacent edges (seam-step gate) and inherited creases excluded')
L('BUST_LIKENESS', 'no hard shelf / crease: dihedral increase vs original, bust region (deg)', round(float((a1 - a0)[bust_reg].max()), 1), (a1 - a0)[bust_reg].max() <= 25.0, '<= 25', '')
L('BUST_LIKENESS', 'mound height above the local wall at the apex (mm): real mounds, not a flat pancake', round(float(0.5 * (hgt[iz(res_b['R']['apex_z']), ix(res_b['R']['apex_x'])] + hgt[iz(res_b['L']['apex_z']), ix(res_b['L']['apex_x'])]) * 1000), 1), 0.5 * (hgt[iz(res_b['R']['apex_z']), ix(res_b['R']['apex_x'])] + hgt[iz(res_b['L']['apex_z']), ix(res_b['L']['apex_x'])]) * 1000 >= 8.0, '>= 8', 'bust prominence is bounded by the plate side profile (~12 mm over the belly line)')
L('BUST_LIKENESS', 'two separate mounds with a sternal valley: front surface at the sternum strip is behind the apex (mm)', round(float(1000 * (Gf[iz(0.5 * (res_b['R']['apex_z'] + res_b['L']['apex_z'])), np.abs(xs) < 0.006].mean() - 0.5 * (Gf[iz(res_b['R']['apex_z']), ix(res_b['R']['apex_x'])] + Gf[iz(res_b['L']['apex_z']), ix(res_b['L']['apex_x'])]))), 1), 1000 * (Gf[iz(0.5 * (res_b['R']['apex_z'] + res_b['L']['apex_z'])), np.abs(xs) < 0.006].mean() - 0.5 * (Gf[iz(res_b['R']['apex_z']), ix(res_b['R']['apex_x'])] + Gf[iz(res_b['L']['apex_z']), ix(res_b['L']['apex_x'])])) >= 3.0, '>= 3', 'separation without a knife crease (crease line above)')
# ---- anti-box measurements (glute)
xs2 = np.arange(-0.19, 0.1901, 0.002); zs2 = np.arange(0.78, 1.06, 0.002)
Gb = grid_surface(co, 'back', xs2, zs2)
i2z = lambda z: int(round((z - 0.78) / 0.002)); i2x = lambda x: int(round((x - xs2[0]) / 0.002))
gl = {}
for side, sg in (('R', 1), ('L', -1)):
    cols = np.where((sg * xs2 >= 0.02) & (sg * xs2 <= 0.15))[0]; rows = np.where((zs2 >= 0.84) & (zs2 <= 0.96))[0]
    sub = Gb[np.ix_(rows, cols)]; i, j = np.unravel_index(np.argmax(sub), sub.shape)
    gl[side] = (float(xs2[cols[j]]), float(zs2[rows[i]]), float(sub[i, j]))
apx = 0.5 * (abs(gl['R'][0]) + abs(gl['L'][0]))
L('GLUTE_LIKENESS', 'two distinct round lobes: apex |x| (m) / z (m)', [round(apx, 3), round(0.5 * (gl['R'][1] + gl['L'][1]), 3)], 0.045 <= apx <= 0.095 and 0.84 <= 0.5 * (gl['R'][1] + gl['L'][1]) <= 0.90, '|x| .045..095, z .84..90', 'plate lobe centres ~ +-0.05..0.08, apex z ~0.86')
# lobe plan-view curvature radius
rcs = []
for side in ('R', 'L'):
    xa, za, _ = gl[side]; sel = np.abs(xs2 - xa) < 0.03
    pp = np.polyfit(xs2[sel] - xa, Gb[i2z(za), sel], 2); rcs.append(abs(1 / (2 * pp[0])) * 100 if abs(pp[0]) > 1e-9 else 999)
rc = float(np.mean(rcs))
L('GLUTE_LIKENESS', 'lobe horizontal curvature radius at the apex (cm): round cheeks, not flat pads', round(rc, 1), 4.0 <= rc <= 14.0, '4..14', '')
# cleft: V-ness and monotone depth
cl = {}
for z in (0.86, 0.88, 0.90, 0.92, 0.94):
    d_, r_ = cleft_depth_ratio(co, z)
    cl[z] = dict(depth_mm=round(float(d_), 1), ratio=(round(float(r_), 2) if d_ >= 4.0 else None))
ratios = [v['ratio'] for v in cl.values() if v['ratio'] is not None]
depth_seq = [cl[z]['depth_mm'] for z in (0.86, 0.88, 0.90, 0.92, 0.94)]
L('GLUTE_LIKENESS', 'cleft is a soft V (not a box/pit): width(50% depth)/width(10% depth), worst over z', cl, (max(ratios) <= 0.80 if ratios else False), '<= 0.80 (vertical-walled pit ~1.0)', 'FORM2 cleft was a square cavity')
L('GLUTE_LIKENESS', 'cleft depth monotone, deepening downward (mm at z .86 .88 .90 .92 .94)', depth_seq, all(depth_seq[i] >= depth_seq[i + 1] - 0.6 for i in range(4)) and depth_seq[0] >= 12 and depth_seq[-1] <= 12, 'monotone, >=12 at z .86, <=12 at z .94', 'plate: faint line starting ~.945 deepening toward the crotch')
L('GLUTE_LIKENESS', 'no hard rim / flat-top ledge: worst dihedral on the upper glute region z .80-1.02 (deg)', round(float(a1[glu_reg].max()), 1), a1[glu_reg].max() <= 30.0, '<= 30 (interior edges smooth in the original)', 'border-adjacent edges (seam-step gate) and inherited creases excluded')
L('GLUTE_LIKENESS', 'no hard rim: dihedral increase vs original, glute region (deg)', round(float((a1 - a0)[glu_reg].max()), 1), (a1 - a0)[glu_reg].max() <= 25.0, '<= 25', '')
# upper shelf (lumbar -> lobes) blend: plate rise vs model
sh = 1000 * (Gb[i2z(0.94), np.abs(xs2) < 0.16].max() - Gb[i2z(1.0), np.abs(xs2) < 0.16].max()); shp = 1000 * (plate_back(0.94) - plate_back(1.0))
L('GLUTE_LIKENESS', 'upper shelf rise z1.00->0.94 (mm) vs plate table', round(float(sh), 1), abs(sh - shp) <= 8.0, f'plate {shp:.1f} +- 8', '')
# ------------------------------------------------------------------------------------------------------------------- visual (author's reading; eye check required)
vis = json.load(open(WD / 'export/visual_verdict.json')) if (WD / 'export/visual_verdict.json').exists() else {'bust': 'PENDING', 'glute': 'PENDING', 'notes': ''}
L('BUST_LIKENESS', 'VISUAL plate B/A (proof/05 soft+clay, proof/04): soft rounded mounds, underbust blend, no box/cylinder/flat front', vis['bust'], vis['bust'] == 'PASS', 'author reading of the proofs', 'author verdict; Adnan eye is the real test', eye=True)
L('GLUTE_LIKENESS', 'VISUAL plate B/A (proof/06 soft+clay, proof/04): twin round lobes, soft V cleft, no box/square cavity/hard ledge', vis['glute'], vis['glute'] == 'PASS', 'author reading of the proofs', 'author verdict; Adnan eye is the real test', eye=True)
L('MIRROR_SOFT', 'mirror-stripe test (proof/07): bust/glute rings organic, stripe breaks no worse than FORM2', vis.get('mirror', 'PENDING'), vis.get('mirror') == 'PASS', 'author reading of proof/07', '', eye=True)
res = {'gate': 'FEMALE_TORSO_FORM3', 'lines': lines, 'photometric': dict(heldout_sheet=ho, bust_form3=rb3, bust_form2=rb2, glute_form3=rg3, glute_form2=rg2, unedited_ncc=unedited, unedited_mean=base_ncc),
       'measurements': dict(bust_apex=res_b, glute_apex=gl, cleft=cl)}
groups = {}
for l in lines:
    groups.setdefault(l['group'], []).append(l['result'] == 'PASS')
res['group_results'] = {k: ('PASS' if all(v) else 'FAIL') for k, v in groups.items()}
res['overall'] = 'PASS' if all(r == 'PASS' for r in res['group_results'].values()) else 'FAIL'
res['failed_lines'] = [l for l in lines if l['result'] != 'PASS']
json.dump(res, open(WD / 'checks.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
json.dump(res, open(WD / 'proof/checks.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
for l in lines:
    print(f"{l['group']:22s} {l['result']}  {l['line']}: {l['value']}  (limit {l['limit']})")
print('GROUPS', res['group_results'], 'OVERALL', res['overall'])
