"""FEMALE_TORSO_FORM4 gate evaluator -> checks.json (+ printed GATE lines).

Objective lines (zone, topology, silhouettes, seams, self-intersection, NaN, flips) are measured by make_final4.py + the chat-7 gate scripts.
BUST_LIKENESS has (a) objective support measured against the plate (sub-pixel side contour, plate-lit band-pass NCC/amplitude, curvature, slopes, creases)
and (b) the visual plate B/A (proof/04, 05, 06, 07) which is the AUTHOR'S reading and flagged `eye_check_required`: Adnan's eye overrides every number here
(FORM3's agent-measured NCC 'soft-passed' a chest Adnan called flat).
"""
import sys, json, hashlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools')
import numpy as np
from torso4 import *
import torso4 as t4
import seam
from photo3 import *
from footprint import grid_surface
from opt3 import cleft_depth_ratio
import score4

ck = json.load(open(WD / 'export/form4_checks.json'))
g7 = json.load(open(WD / 'export/form4_gate_scripts_checks.json'))
g73 = json.load(open(WD.parent / 'female-torso-form3/export/form3_gate_scripts_checks.json'))
co = np.load(WD / 'data/co_FORM4_final.npy').astype(np.float64)
f3 = np.load(WD / 'data/co_FORM3_final.npy').astype(np.float64)
lines = []


def L(group, name, value, cond, limit, basis, eye=False):
    lines.append(dict(group=group, line=name, value=value, limit=limit, result='PASS' if cond else 'FAIL', basis=basis, **({'eye_check_required': True} if eye else {})))


# ------------------------------------------------------------------------------------------------------------------- zone / topology
L('ZONE_OUTSIDE', 'moved outside zone vs FORM3 start (a0f69f9d)', ck['moved_outside_zone_vs_form3_start'], ck['moved_outside_zone_vs_form3_start'] == 0, '== 0', 'float32 exact, audit dumps')
L('ZONE_OUTSIDE', 'moved outside zone vs ORIGINAL ArtDir 200dc3b9', ck['moved_outside_zone_vs_artdir_200dc3b9'], ck['moved_outside_zone_vs_artdir_200dc3b9'] == 0, '== 0', 'float32 exact')
L('ZONE_OUTSIDE', 'zone border vertices moved (238; neck / arm junction / leg tops) vs ArtDir', ck['border_vertices_moved_vs_artdir'], ck['border_vertices_moved_vs_artdir'] == 0, '== 0', 'bit-identical to the original ring the arms/legs/neck seams rely on')
L('ZONE_OUTSIDE', 'zone border vertices moved vs FORM3 start', ck['border_vertices_moved_vs_form3_start'], ck['border_vertices_moved_vs_form3_start'] == 0, '== 0', '')
topo = ck['topology']
tp = all(v for k, v in topo.items() if isinstance(v, bool))
L('TOPOLOGY', 'poly/loop/edge/material/smooth/UV/custom-normal raw codes/Hair/other objects identical (vs FORM3 start AND vs ArtDir)', tp, tp, 'all True', 'audit dumps')
L('TOPOLOGY', 'triangles (budget 35-50k; NO densify)', topo['tris_form3_start_vs_new'][1], topo['tris_form3_start_vs_new'][1] == topo['tris_form3_start_vs_new'][0] and topo['tris_form3_start_vs_new'][1] <= 50000, 'unchanged, <=50k', 'positions only')
L('TOPOLOGY', 'flipped zone triangles vs original', ck['flipped_zone_tris_vs_original'], ck['flipped_zone_tris_vs_original'] == 0, '== 0', 'face-normal dot < 0')
L('TOPOLOGY', 'zone triangles turned >60 deg vs original', ck['zone_tris_turned_gt60deg'], ck['zone_tris_turned_gt60deg'] <= 2, '<= 2', '')
# ------------------------------------------------------------------------------------------------------------------- silhouettes
sx = g7['side_profile_torso_band_xor_z0.82_1.30']['after']; sx3 = g73['side_profile_torso_band_xor_z0.82_1.30']['after']
L('SIDE_SIL', 'side-profile torso-band XOR vs plate (z .82-1.30)', round(sx, 4), sx <= 0.05, f'<= 0.05 (FORM3 {sx3:.4f})', 'chat-7 gate script metrics_side.py')
fb = g7['torso_visible_edge_run_xor_rows_z0.82_1.165']['after']
L('FRONT_BACK_TORSO_EDGE', 'front torso visible-edge XOR vs bald plate', round(fb['front'], 4), fb['front'] <= 0.05, '<= 0.05', 'chat-7 gate script metrics_fb.py')
L('FRONT_BACK_TORSO_EDGE', 'back torso visible-edge XOR vs bald plate', round(fb['back'], 4), fb['back'] <= 0.05, '<= 0.05', '')
# ------------------------------------------------------------------------------------------------------------------- seams
bs = ck['border_steps_mm']['form4']; bs3 = ck['border_steps_mm']['form3']
L('SEAM_CLEAN', 'displacement step at a pinned border edge, legs (mm)', round(bs['legs']['max_mm'], 2), bs['legs']['max_mm'] <= 8.0, f"<= 8 (FORM3 {bs3['legs']['max_mm']:.2f})", '|d(v)-d(border)| over one edge (~12 mm)')
L('SEAM_CLEAN', '... arm junction (mm)', round(bs['arm']['max_mm'], 2), bs['arm']['max_mm'] <= 10.0, f"<= 10 (FORM3 {bs3['arm']['max_mm']:.2f})", '')
L('SEAM_CLEAN', '... neck/shoulder top (mm)', round(bs['top']['max_mm'], 2), bs['top']['max_mm'] <= 1.0, f"<= 1 (FORM3 {bs3['top']['max_mm']:.2f})", '')
dh = ck['dihedral']
L('SEAM_CLEAN', 'zone edges with dihedral >40 deg (count)', dh['form4']['n_gt40'], dh['form4']['n_gt40'] <= dh['original']['n_gt40'], f"<= original ({dh['original']['n_gt40']})", 'inherited mesh creases are not increased')
L('SEAM_CLEAN', 'worst zone dihedral (deg)', round(dh['form4']['max_deg'], 1), dh['form4']['max_deg'] <= dh['original']['max_deg'] + 0.5, f"<= original ({dh['original']['max_deg']:.1f})", '')
rg = ck['bi_laplacian_roughness_mm_zone_interior']
L('SEAM_CLEAN', 'bi-Laplacian roughness mean (mm), zone interior', round(rg['form4']['mean'], 3), rg['form4']['mean'] <= rg['form3']['mean'] * 1.15 + 1e-9, f"<= 1.15 x FORM3 ({rg['form3']['mean']:.3f})", 'smoothness not worse than FORM3')
L('SEAM_CLEAN', 'bi-Laplacian roughness p95 (mm)', round(rg['form4']['p95'], 3), rg['form4']['p95'] <= rg['form3']['p95'] * 1.15 + 1e-9, f"<= 1.15 x FORM3 ({rg['form3']['p95']:.3f})", '')
# ------------------------------------------------------------------------------------------------------------------- no self-intersect / NaN
si = ck['self_intersection_pairs']
L('NO_SELF_INTERSECT', 'no NaN/inf coordinates', ck['nan_or_inf'], ck['nan_or_inf'] == 0, '== 0', '')
L('NO_SELF_INTERSECT', 'exact triangle-triangle intersecting pairs touching the torso zone (original / FORM3 / FORM4)', [si['original']['touching_torso_zone'], si['form3']['touching_torso_zone'], si['form4']['touching_torso_zone']], si['form4']['touching_torso_zone'] <= si['original']['touching_torso_zone'], '<= original (0)', 'mathutils BVHTree.overlap = exact tri-tri test; the 4,444 whole-mesh pairs (identical in all files) are eyes/teeth/ears/hands, none in the torso zone')
L('NO_SELF_INTERSECT', 'whole-mesh intersecting pairs unchanged vs original', [si['original']['whole_mesh'], si['form4']['whole_mesh']], si['form4']['whole_mesh'] <= si['original']['whole_mesh'], '<= original', '')
nf = ck['custom_normals_vs_geometry_deg_zone']
L('NO_SELF_INTERSECT', 'decoded custom normals still follow the geometry in the zone (median / p95 deg, FORM4 vs original)', [round(nf['form4']['median_deg'], 2), round(nf['form4']['p95_deg'], 2), round(nf['original']['median_deg'], 2), round(nf['original']['p95_deg'], 2)], nf['form4']['median_deg'] <= nf['original']['median_deg'] + 0.5 and nf['form4']['p95_deg'] <= nf['original']['p95_deg'] + 1.0, 'within 0.5 / 1.0 deg of the original', 'shading in Unity/Blender is faithful to the new surface (raw codes untouched)')
# ------------------------------------------------------------------------------------------------------------------- BUST: objective support
FF = np.load(WD / 'data/plate_front_fine4.npy'); FB = np.load(WD / 'data/plate_back_fine4.npy')
def env(c, zs, back=False):
    fe, be = section_extents(c); fe, be = fillnan(fe), fillnan(be)
    return np.interp(zs, ZG, be if back else fe)
zb = np.arange(1.15, 1.2701, 0.005)
e4 = env(co, zb) - np.interp(zb, FF[0], FF[1]); e3 = env(f3, zb) - np.interp(zb, FF[0], FF[1])
r4 = float(np.sqrt((e4 ** 2).mean()) * 1000); r3 = float(np.sqrt((e3 ** 2).mean()) * 1000)
L('BUST_LIKENESS', 'side-envelope bump band z 1.15-1.27: RMS vs SUB-PIXEL plate contour (mm)', [round(r4, 2), round(r3, 2)], r4 <= 3.0 and r4 <= r3 + 0.3, '<= 3.0 and not worse than FORM3 (value = [FORM4, FORM3])', 'plate_side4.py: sub-pixel gradient edge, calibrated on z .95-1.15 to the old table (-4.75 mm)')
zd = np.array([1.28, 1.30, 1.32])
d4 = 1000 * (env(co, zd) - np.interp(zd, FF[0], FF[1])); d3 = 1000 * (env(f3, zd) - np.interp(zd, FF[0], FF[1]))
L('BUST_LIKENESS', 'upper-chest diagonal: front line vs plate at z 1.28/1.30/1.32 (mm, negative = model further forward; FORM3 in 2nd list)', [[round(float(v), 1) for v in d4], [round(float(v), 1) for v in d3]], bool((np.abs(d4) < np.abs(d3)).all()), '|FORM4| < |FORM3| at all three heights', 'residual above z~1.30 is the pinned neck-base ring (hand-off); STRETCH target |FORM4| <= 0.75 |FORM3| is met at z 1.28 (%.2f) and 1.30 (%.2f) but NOT at 1.32 (%.2f) - see honest notes' % tuple(np.abs(d4) / np.abs(d3)))
sc4 = score4.evaluate(co); sc3 = score4.evaluate(f3)
L('BUST_LIKENESS', 'mound apex curvature radius of the side envelope (cm): round, not flat (FORM3 8.6) nor pointed; plate 5.6', [round(sc4['rc'], 1), round(sc3['rc'], 1)], 4.0 <= sc4['rc'] <= 8.0, '4..8 (plate 5.6)', 'parabola fit of the front envelope over +-2 cm around the apex')
L('BUST_LIKENESS', 'dome surface slope (98th pct |dy/dz| angle along the dome column, deg): soft, not conical', [round(sc4['slope98'], 1), round(sc3['slope98'], 1)], sc4['slope98'] <= 38.0, '<= 38 (plate profile max ~39 on the diagonal)', '')
a1 = seam.dihedral(co); a0 = seam.dihedral(CO0); a3 = seam.dihedral(f3)
mid = 0.5 * (co[seam.PAIR_E[:, 0]] + co[seam.PAIR_E[:, 1]])
nb_ = ~(BORDER[seam.PAIR_E[:, 0]] | BORDER[seam.PAIR_E[:, 1]]) & (a0 <= 15.0)
bust_reg = seam.ZPAIR & nb_ & (mid[:, 2] >= 1.14) & (mid[:, 2] <= 1.32) & (np.abs(mid[:, 0]) <= 0.115) & (mid[:, 1] < 0)
glu_reg = seam.ZPAIR & nb_ & (mid[:, 2] >= 0.80) & (mid[:, 2] <= 1.02) & (np.abs(mid[:, 0]) <= 0.15) & (mid[:, 1] > 0)
cen_reg = seam.ZPAIR & (mid[:, 2] >= 1.15) & (mid[:, 2] <= 1.30) & (np.abs(mid[:, 0]) < 0.022) & (mid[:, 1] < 0)
L('BUST_LIKENESS', 'no hard shelf / crease: worst dihedral on the front bust region (deg; FORM3 %.1f)' % a3[bust_reg].max(), round(float(a1[bust_reg].max()), 1), a1[bust_reg].max() <= 31.0, '<= 31 (11 mm mesh: 31 deg = 2 cm radius, soft; interior edges that were smooth, <=15 deg, in the original)', 'a new hard line = high dihedral between adjacent triangles; border-adjacent edges (seam-step gate) and inherited creases excluded')
L('BUST_LIKENESS', 'no hard shelf / crease: dihedral increase vs original, bust region (deg)', round(float((a1 - a0)[bust_reg].max()), 1), (a1 - a0)[bust_reg].max() <= 25.0, '<= 25', '')
L('BUST_LIKENESS', 'sternal valley without a knife crease: worst dihedral on the sternum strip |x|<2.2 cm, z 1.15-1.30 (deg; FORM3 %.1f)' % a3[cen_reg].max(), round(float(a1[cen_reg].max()), 1), a1[cen_reg].max() <= 20.0, '<= 20 (smooth valley: >=2.5 cm radius at 11 mm spacing)', 'two signed domes summed (no |x| kink) + sternum-strip smoothing')
# photometric agreement (plate-lit, plate's own pixel grid; lighting fitted on unedited regions of the plate)
N4 = vertex_normals(co, TRI); N3 = vertex_normals(f3, TRI)
lt = np.array(LIGHT); lf = lt.copy(); lf[1:] *= 2.5; lb = lt.copy(); lb[1:] *= 2.0
core = roi_box('front', -0.085, 0.085, 1.15, 1.28); wide = roi_box('front', -0.115, 0.115, 1.14, 1.30)
rc4 = compare(co, 'front', core, light=lf, normals=N4); rc3 = compare(f3, 'front', core, light=lf, normals=N3)
rw4 = compare(co, 'front', wide, light=lf, normals=N4); rw3 = compare(f3, 'front', wide, light=lf, normals=N3)
L('BUST_LIKENESS', 'relief amplitude in the bust CORE ROI (|x|<.085, z 1.15-1.28; band-pass std ratio model/plate, plate-fit light x2.5): FORM4 not weaker than FORM3', [round(rc4['amp_ratio'], 2), round(rc3['amp_ratio'], 2)], rc4['amp_ratio'] >= rc3['amp_ratio'], '>= FORM3 (value = [FORM4, FORM3])', 'INFORMATIONAL about the absolute level: the ratio to the plate depends on the photometric gain (at the raw regression gain 1.0 the core ratios are about 0.89 / 0.59; at the calibrated x2.5 they are above 1 for both) - the visual proofs, not this ratio, are the reference')
L('BUST_LIKENESS', 'plate-lit band-pass NCC, bust WIDE ROI (front, |x|<.115, z 1.14-1.30)', [round(rw4['ncc'], 3), round(rw3['ncc'], 3)], rw4['ncc'] >= rw3['ncc'] - 0.02, '>= FORM3 - 0.02 (value = [FORM4, FORM3])', 'FORM3 scored 0.644 here and was still called flat by eye: NCC alone is not evidence')
L('BUST_LIKENESS', 'plate-lit band-pass NCC, bust CORE ROI', [round(rc4['ncc'], 3), round(rc3['ncc'], 3)], rc4['ncc'] >= 0.70, '>= 0.70 (value = [FORM4, FORM3])', 'FORM4 trades a little pattern correlation for 1.5x the relief amplitude')
ho = {t: dict(bust=compare_sheet(c_, 'front', -0.115, 0.115, 1.14, 1.30, light=lf), glute=compare_sheet(c_, 'back', -0.14, 0.14, 0.80, 0.97, light=lb)) for t, c_ in (('form4', co), ('form3', f3))}
L('BUST_LIKENESS', 'held-out check on the multi-angle SHEET front panel (different render/scale): NCC not worse than FORM3 by > 0.05', [round(ho['form4']['bust']['ncc'], 3), round(ho['form3']['bust']['ncc'], 3)], ho['form4']['bust']['ncc'] >= ho['form3']['bust']['ncc'] - 0.05, 'form4 >= form3 - 0.05', 'guards against over-fitting the bald plate')
# mound height above the local wall / sternal valley (grid surfaces)
P = json.load(open(WD / 'export/form4_params.json'))
dF, dB = [np.array(x) for x in np.load(WD / 'export/form4_wall_corrections.npy')[:2]]          # chest build's wall corrections
xs = np.arange(-0.14, 0.1401, 0.002); zs = np.arange(1.10, 1.34, 0.002)
Gf = grid_surface(co, 'front', xs, zs)
Pb = {**DEFAULT3, **P}; Pb['bm_list'] = [dict(c, H=0.0) for c in P['bm_list']]; Pb.update(bp_H=0.0, st_R3=0.0, mo_R=0.0, rd_R=0.0)
base_wall = grid_surface(t4.build3(Pb, dF, dB), 'front', xs, zs)
hgt = base_wall - Gf
ix = lambda x: int(round((x - xs[0]) / 0.002)); iz = lambda z: int(round((z - zs[0]) / 0.002))
res_b = {}
for side, sg in (('R', 1), ('L', -1)):
    cols = np.where((sg * xs >= 0.03) & (sg * xs <= 0.125))[0]; rows = np.where((zs >= 1.17) & (zs <= 1.29))[0]
    sub = Gf[np.ix_(rows, cols)]; i, j = np.unravel_index(np.argmin(sub), sub.shape)
    res_b[side] = dict(apex_x=float(xs[cols[j]]), apex_z=float(zs[rows[i]]))
hap = 0.5 * sum(hgt[iz(res_b[s]['apex_z']), ix(res_b[s]['apex_x'])] for s in 'RL') * 1000
L('BUST_LIKENESS', 'mound height above the local wall without the domes, at the apex (mm): real mounds, not a flat pancake', round(float(hap), 1), hap >= 12.0, '>= 12 (FORM3 12.4 incl. the flatten band; FORM4 domes sit on the un-flattened ring)', '')
zc_ = 0.5 * (res_b['R']['apex_z'] + res_b['L']['apex_z']); apx_y = 0.5 * sum(Gf[iz(res_b[s]['apex_z']), ix(res_b[s]['apex_x'])] for s in 'RL')
valley = 1000 * (Gf[iz(zc_), np.abs(xs) < 0.006].mean() - apx_y)
L('BUST_LIKENESS', 'two separate mounds with a sternal valley: front surface at the sternum strip is behind the apex (mm)', round(float(valley), 1), valley >= 3.0, '>= 3', '')
# ------------------------------------------------------------------------------------------------------------------- GLUTE: hold or better
BKf = np.interp(np.array([0.85, 0.86, 0.87, 0.88]), FB[0], FB[1])
b4 = 1000 * (env(co, np.array([0.85, 0.86, 0.87, 0.88]), back=True) - BKf); b3 = 1000 * (env(f3, np.array([0.85, 0.86, 0.87, 0.88]), back=True) - BKf)
L('GLUTE_HOLD_OR_BETTER', 'back-envelope apex vs SUB-PIXEL plate contour at z .85/.86/.87/.88 (mm; FORM3 in 2nd list)', [[round(float(v), 1) for v in b4], [round(float(v), 1) for v in b3]], float(np.abs(b4).max()) <= float(np.abs(b3).max()), '|FORM4| max <= |FORM3| max', 'sub-pixel plate back contour peaks ~3 mm further back than the old table (plate_back4.py)')
xs2 = np.arange(-0.19, 0.1901, 0.002); zs2 = np.arange(0.78, 1.06, 0.002)
def glute_meas(c):
    Gb = grid_surface(c, 'back', xs2, zs2)
    i2z = lambda z: int(round((z - 0.78) / 0.002))
    gl = {}
    for side, sg in (('R', 1), ('L', -1)):
        cols = np.where((sg * xs2 >= 0.02) & (sg * xs2 <= 0.15))[0]; rows = np.where((zs2 >= 0.84) & (zs2 <= 0.96))[0]
        sub = Gb[np.ix_(rows, cols)]; i, j = np.unravel_index(np.argmax(sub), sub.shape)
        gl[side] = (float(xs2[cols[j]]), float(zs2[rows[i]]), float(sub[i, j]))
    rcs = []
    for side in ('R', 'L'):
        xa, za, _ = gl[side]; sel = np.abs(xs2 - xa) < 0.03
        pp = np.polyfit(xs2[sel] - xa, Gb[i2z(za), sel], 2); rcs.append(abs(1 / (2 * pp[0])) * 100 if abs(pp[0]) > 1e-9 else 999)
    return Gb, gl, float(np.mean(rcs))
Gb4, gl4, rcg4 = glute_meas(co); Gb3, gl3, rcg3 = glute_meas(f3)
apx = 0.5 * (abs(gl4['R'][0]) + abs(gl4['L'][0]))
L('GLUTE_HOLD_OR_BETTER', 'two distinct round lobes: apex |x| (m) / z (m)', [round(apx, 3), round(0.5 * (gl4['R'][1] + gl4['L'][1]), 3)], 0.045 <= apx <= 0.095 and 0.84 <= 0.5 * (gl4['R'][1] + gl4['L'][1]) <= 0.90, '|x| .045..095, z .84..90', 'plate lobe centres ~ +-0.05..0.08, apex z ~0.86')
L('GLUTE_HOLD_OR_BETTER', 'lobe horizontal curvature radius at the apex (cm): round cheeks, not flat pads (FORM3 %.1f)' % rcg3, round(rcg4, 1), 4.0 <= rcg4 <= 14.0, '4..14', '')
cl = {}
for z in (0.86, 0.88, 0.90, 0.92, 0.94):
    d_, r_ = cleft_depth_ratio(co, z); cl[z] = dict(depth_mm=round(float(d_), 1), ratio=(round(float(r_), 2) if d_ >= 4.0 else None))
ratios = [v['ratio'] for v in cl.values() if v['ratio'] is not None]
depth_seq = [cl[z]['depth_mm'] for z in (0.86, 0.88, 0.90, 0.92, 0.94)]
L('GLUTE_HOLD_OR_BETTER', 'cleft is a soft V (not a box/pit): width(50% depth)/width(10% depth), worst over z', cl, (max(ratios) <= 0.80 if ratios else False), '<= 0.80 (vertical-walled pit ~1.0)', 'FORM2 cleft was a square cavity')
L('GLUTE_HOLD_OR_BETTER', 'cleft depth monotone, deepening downward (mm at z .86 .88 .90 .92 .94)', depth_seq, all(depth_seq[i] >= depth_seq[i + 1] - 0.6 for i in range(4)) and depth_seq[0] >= 12 and depth_seq[-1] <= 12, 'monotone, >=12 at z .86, <=12 at z .94', '')
L('GLUTE_HOLD_OR_BETTER', 'no hard rim / flat-top ledge: worst dihedral on the glute region z .80-1.02 (deg; FORM3 %.1f)' % a3[glu_reg].max(), round(float(a1[glu_reg].max()), 1), a1[glu_reg].max() <= 30.0, '<= 30', 'border-adjacent edges (seam-step gate) and inherited creases excluded')
L('GLUTE_HOLD_OR_BETTER', 'no hard rim: dihedral increase vs original, glute region (deg)', round(float((a1 - a0)[glu_reg].max()), 1), (a1 - a0)[glu_reg].max() <= 25.0, '<= 25', '')
sh = 1000 * (Gb4[int(round((0.94 - 0.78) / 0.002)), np.abs(xs2) < 0.16].max() - Gb4[int(round((1.0 - 0.78) / 0.002)), np.abs(xs2) < 0.16].max()); shp = 1000 * (plate_back(0.94) - plate_back(1.0))
L('GLUTE_HOLD_OR_BETTER', 'upper shelf rise z1.00->0.94 (mm) vs plate table', round(float(sh), 1), abs(sh - shp) <= 8.0, f'plate {shp:.1f} +- 8', '')
drift = np.linalg.norm(co - f3, axis=1); gsel = (CO0[:, 2] < 1.0) & (drift > 1e-9)
L('GLUTE_HOLD_OR_BETTER', 'glute-ROI drift vs FORM3 (mm: max / mean over moved vertices): light polish only', [round(float(1000 * drift[CO0[:, 2] < 1.0].max()), 2), round(float(1000 * drift[gsel].mean()), 2)], drift[CO0[:, 2] < 1.0].max() <= 0.004 and drift[gsel].mean() <= 0.002, 'max <= 4, mean <= 2 (brief: avg <= 2-4 mm)', 'bk_amp 3.5 mm back-silhouette target + lobe reshaped (H .020->.024, lower reach .073->.054 to stay inside the legs seam budget)')
rg4 = compare(co, 'back', roi_box('back', -0.14, 0.14, 0.80, 0.97), light=lb, normals=N4); rg3 = compare(f3, 'back', roi_box('back', -0.14, 0.14, 0.80, 0.97), light=lb, normals=N3)
L('GLUTE_HOLD_OR_BETTER', 'plate-lit band-pass NCC in the glute ROI (back, |x|<.14, z .80-.97): not worse than FORM3', [round(rg4['ncc'], 3), round(rg3['ncc'], 3)], rg4['ncc'] >= rg3['ncc'] - 0.03, '>= FORM3 - 0.03 (value = [FORM4, FORM3])', '')
L('GLUTE_HOLD_OR_BETTER', 'held-out SHEET back panel NCC not worse than FORM3 by > 0.05', [round(ho['form4']['glute']['ncc'], 3), round(ho['form3']['glute']['ncc'], 3)], ho['form4']['glute']['ncc'] >= ho['form3']['glute']['ncc'] - 0.05, 'form4 >= form3 - 0.05', '')
# ------------------------------------------------------------------------------------------------------------------- visual (author's reading; Adnan's eye overrides)
vis = json.load(open(WD / 'export/visual_verdict.json')) if (WD / 'export/visual_verdict.json').exists() else {'bust': 'PENDING', 'glute': 'PENDING', 'mirror': 'PENDING', 'notes': ''}
L('BUST_EYE_PASS', 'VISUAL plate | FORM3 | FORM4 (proof/05 soft + clay + side, proof/04): soft rounded projected mounds, soft matcap still shows volume, no flat wall, no pointy shelves', vis['bust'], vis['bust'] == 'PASS', 'author reading of the proofs', 'AUTHOR verdict; Adnan eye overrides (FORM3 soft-passed and was rejected)', eye=True)
L('GLUTE_HOLD_OR_BETTER', 'VISUAL plate | FORM3 | FORM4 (proof/06 soft + clay, proof/04): twin lobes + soft V cleft held, no box/pit/ledge regression', vis['glute'], vis['glute'] == 'PASS', 'author reading of the proofs', 'AUTHOR verdict; Adnan eye overrides', eye=True)
L('MIRROR_SOFT', 'mirror-stripe test (proof/07): bust/glute rings organic (no square rings / V creases); polygonal innermost bust ring disclosed', vis.get('mirror', 'PENDING'), vis.get('mirror') == 'PASS', 'author reading of proof/07', '', eye=True)
res = {'gate': 'FEMALE_TORSO_FORM4', 'lines': lines, 'photometric': dict(heldout_sheet=ho, bust_core=dict(form4=rc4, form3=rc3), bust_wide=dict(form4=rw4, form3=rw3), glute=dict(form4=rg4, form3=rg3)),
       'measurements': dict(bust_apex=res_b, glute_apex=gl4, cleft=cl, score4_form4={k: v for k, v in sc4.items()}, score4_form3={k: v for k, v in sc3.items()})}
groups = {}
for l in lines:
    groups.setdefault(l['group'], []).append(l['result'] == 'PASS')
res['group_results'] = {k: ('PASS' if all(v) else 'FAIL') for k, v in groups.items()}
res['overall'] = 'PASS' if all(r == 'PASS' for r in res['group_results'].values()) else 'FAIL'
res['failed_lines'] = [l for l in lines if l['result'] != 'PASS']
dumper = lambda o: o.item() if hasattr(o, 'item') else str(o)
json.dump(res, open(WD / 'checks.json', 'w'), indent=1, default=dumper)
json.dump(res, open(WD / 'proof/checks.json', 'w'), indent=1, default=dumper)
for l in lines:
    print(f"{l['group']:22s} {l['result']}  {l['line']}: {l['value']}  (limit {l['limit']})")
print('GROUPS', res['group_results'], 'OVERALL', res['overall'])
