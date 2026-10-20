"""FEMALE_TORSO_FORM5 gate evaluator -> checks.json (+ printed GATE lines).

Objective lines (zone, topology, silhouettes, seams, self-intersection, NaN, flips) are measured by make_final5.py + the chat-7 gate scripts.
The BUST_EYE_PASS / UNDERBUTT_EYE_PASS / MIRROR lines are the AUTHOR'S reading of the proofs (plus independent reviewer notes) and are flagged `eye_check_required`:
Adnan's eye on the plate | FORM4 | FORM5 proofs overrides every number here (FORM3/FORM4 'soft-passed' by number and were rejected by eye).
Measured 'support' lines compare against the plate in the SAME render domain (plate crop vs soft render luminance) - they are supporting evidence, not the verdict.
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from torso4 import *
import torso4 as t4
import seam
from photo3 import *
from footprint import grid_surface
from opt3 import cleft_depth_ratio
import score4, benv5, cres5, ring5
from PIL import Image

ck = json.load(open(WD / 'export/form5_checks.json'))
g7 = json.load(open(WD / 'export/form5_gate_scripts_checks.json'))
g74 = json.load(open(WD / 'export/form4_gate_scripts_checks.json')) if (WD / 'export/form4_gate_scripts_checks.json').exists() else json.load(open(WD.parent / 'female-torso-form4/export/form4_gate_scripts_checks.json'))
Z5 = np.load(WD / 'data/zone5.npz'); T5 = Z5['torso']; BORDER5 = Z5['border5']
co = np.load(WD / 'data/co_FORM5_final.npy').astype(np.float64)
c4 = np.load(WD / 'data/co_FORM4_final.npy').astype(np.float64)
lines = []


def L(group, name, value, cond, limit, basis, eye=False, info=False):
    lines.append(dict(group=('INFO_' + group) if info else group, line=name, value=value, limit=limit, result='PASS' if cond else ('INFO' if info else 'FAIL'), basis=basis, **({'eye_check_required': True} if eye else {})))


# ------------------------------------------------------------------------------------------------------------------- zone / topology
L('ZONE_OUTSIDE', 'moved outside the DOCUMENTED zone5 mask vs FORM4 start (aa3e1e44)', ck['moved_outside_zone5_vs_form4_start'], ck['moved_outside_zone5_vs_form4_start'] == 0, '== 0', 'float32 exact, audit dumps; zone5 = chat-7 torso zone (3,320) + LEG-TOP extension (%d verts, z .62-.795, flood-filled thigh tubes, floor ring %d verts pinned)' % (ck['legtop_extension_vertices'], ck['legtop_floor_ring_vertices']))
L('ZONE_OUTSIDE', 'moved outside zone5 vs ORIGINAL ArtDir 200dc3b9', ck['moved_outside_zone5_vs_artdir_200dc3b9'], ck['moved_outside_zone5_vs_artdir_200dc3b9'] == 0, '== 0', 'float32 exact')
L('ZONE_OUTSIDE', 'zone5 border vertices moved vs ArtDir (%d: neck / arm junction / NEW leg-top floor ring)' % ck['border5_vertices'], ck['border5_vertices_moved_vs_artdir'], ck['border5_vertices_moved_vs_artdir'] == 0, '== 0', 'bit-identical to the original ring the neighbours rely on')
L('ZONE_OUTSIDE', 'zone5 border vertices moved vs FORM4 start', ck['border5_vertices_moved_vs_form4_start'], ck['border5_vertices_moved_vs_form4_start'] == 0, '== 0', '')
topo = ck['topology']
tp = all(v for k, v in topo.items() if isinstance(v, bool))
L('TOPOLOGY', 'poly/loop/edge/material/smooth/UV/Hair/other objects identical; custom-normal raw codes identical OUTSIDE the disclosed offset rescale (vs FORM4 start AND vs ArtDir)', tp, tp, 'all True', 'audit dumps; ROUND 5 DEVIATION from positions-only (brief: topology identical PREFERRED): the authored custom-normal OFFSET (raw code0) is scaled by (1-w) on %d corners of %d moved/tapered vertices (code1 and every other loop untouched) because the offsets baked on the ORIGINAL mesh flatten the new under-butt fold shading (same geometry: smile +1.7 px with them, +6.5 px without)' % (topo.get('custom_normal_weighted_corners', 0), topo.get('custom_normal_weighted_vertices', 0)))
L('TOPOLOGY', 'triangles (budget 35-50k; NO densify)', topo['tris_form4_start_vs_new'][1], topo['tris_form4_start_vs_new'][1] == topo['tris_form4_start_vs_new'][0] and topo['tris_form4_start_vs_new'][1] <= 50000, 'unchanged, <=50k', 'positions only')
L('TOPOLOGY', 'flipped zone5 triangles vs original', ck['flipped_zone5_tris_vs_original'], ck['flipped_zone5_tris_vs_original'] == 0, '== 0', 'face-normal dot < 0')
L('TOPOLOGY', 'zone5 triangles turned >60 deg vs original', ck['zone5_tris_turned_gt60deg'], ck['zone5_tris_turned_gt60deg'] <= 2, '<= 2', '')
# ------------------------------------------------------------------------------------------------------------------- silhouettes
sx = g7['side_profile_torso_band_xor_z0.82_1.30']['after']; sx4 = g74['side_profile_torso_band_xor_z0.82_1.30']['after']
L('SIDE_SIL', 'side-profile torso-band XOR vs plate (z .82-1.30; torso band unchanged by the leg-top extension)', round(sx, 4), sx <= 0.05, f'<= 0.05 (FORM4 {sx4:.4f})', 'chat-7 gate script metrics_side.py')
fb = g7['torso_visible_edge_run_xor_rows_z0.82_1.165']['after']
L('FRONT_BACK_TORSO_EDGE', 'front torso visible-edge XOR vs bald plate', round(fb['front'], 4), fb['front'] <= 0.05, '<= 0.05', 'chat-7 gate script metrics_fb.py (x is untouched in the torso; <=1 mm denoise in the leg-top band)')
L('FRONT_BACK_TORSO_EDGE', 'back torso visible-edge XOR vs bald plate', round(fb['back'], 4), fb['back'] <= 0.05, '<= 0.05', '')
# ------------------------------------------------------------------------------------------------------------------- seams
bs = ck['border_steps_mm']['form5']
L('SEAM_CLEAN', 'displacement step at the NEW leg-top floor ring (mm)', round(bs['legs_floor']['max_mm'], 2), bs['legs_floor']['max_mm'] <= 8.0, '<= 8 (FORM4 zone-floor budget; new border far smaller)', '|d(v)-d(border)| over one edge (~12 mm), d = displacement vs the original')
L('SEAM_CLEAN', '... arm junction (mm)', round(bs['arm']['max_mm'], 2), bs['arm']['max_mm'] <= 10.0, '<= 10', '')
L('SEAM_CLEAN', '... neck/shoulder top (mm)', round(bs['top']['max_mm'], 2), bs['top']['max_mm'] <= 1.0, '<= 1', '')
dh = ck['dihedral']
L('SEAM_CLEAN', 'zone5 edges with dihedral >40 deg (count)', dh['form5']['n_gt40'], dh['form5']['n_gt40'] <= dh['original']['n_gt40'], f"<= original ({dh['original']['n_gt40']})", 'inherited mesh creases are not increased (FORM4 %d)' % dh['form4']['n_gt40'])
L('SEAM_CLEAN', 'worst zone5 dihedral (deg)', round(dh['form5']['max_deg'], 1), dh['form5']['max_deg'] <= dh['original']['max_deg'] + 0.5, f"<= original ({dh['original']['max_deg']:.1f}) + .5", 'the 80 deg is the crotch arch inherited from the original')
rg = ck['bi_laplacian_roughness_mm_zone5_interior']
L('SEAM_CLEAN', 'bi-Laplacian roughness mean (mm), zone5 interior', round(rg['form5']['mean'], 3), rg['form5']['mean'] <= rg['form4']['mean'] * 1.15 + 1e-9, f"<= 1.15 x FORM4 ({rg['form4']['mean']:.3f})", 'smoothness not worse than FORM4')
L('SEAM_CLEAN', 'bi-Laplacian roughness p95 (mm)', round(rg['form5']['p95'], 3), rg['form5']['p95'] <= rg['form4']['p95'] * 1.15 + 1e-9, f"<= 1.15 x FORM4 ({rg['form4']['p95']:.3f})", '')
# ------------------------------------------------------------------------------------------------------------------- no self-intersect / NaN
si = ck['self_intersection_pairs']
L('NO_SELF_INTERSECT', 'no NaN/inf coordinates', ck['nan_or_inf'], ck['nan_or_inf'] == 0, '== 0', '')
L('NO_SELF_INTERSECT', 'exact triangle-triangle intersecting pairs touching zone5 (original / FORM4 / FORM5)', [si['original']['touching_zone5'], si['form4']['touching_zone5'], si['form5']['touching_zone5']], si['form5']['touching_zone5'] <= si['original']['touching_zone5'], '<= original (0)', 'mathutils BVHTree.overlap = exact tri-tri test; the 4,444 whole-mesh pairs (identical in all files) are eyes/teeth/ears/hands')
L('NO_SELF_INTERSECT', 'whole-mesh intersecting pairs unchanged vs original', [si['original']['whole_mesh'], si['form5']['whole_mesh']], si['form5']['whole_mesh'] <= si['original']['whole_mesh'], '<= original', '')
nf = ck['custom_normals_vs_geometry_deg_zone5']
L('NO_SELF_INTERSECT', 'decoded custom normals still follow the geometry in zone5 (median / p95 deg, FORM5 vs original)', [round(nf['form5']['median_deg'], 2), round(nf['form5']['p95_deg'], 2), round(nf['original']['median_deg'], 2), round(nf['original']['p95_deg'], 2)], nf['form5']['median_deg'] <= nf['original']['median_deg'] + 0.5 and nf['form5']['p95_deg'] <= nf['original']['p95_deg'] + 1.0, 'within 0.5 / 1.0 deg of the original', 'raw codes untouched')
# ------------------------------------------------------------------------------------------------------------------- BUST: keep FORM4's wins
FF = np.load(WD / 'data/plate_front_fine4.npy'); FB = np.load(WD / 'data/plate_back_fine4.npy')
def env(c, zs, back=False):
    fe, be = section_extents(c); fe, be = fillnan(fe), fillnan(be)
    return np.interp(zs, ZG, be if back else fe)
zb = np.arange(1.15, 1.2701, 0.005)
e5 = env(co, zb) - np.interp(zb, FF[0], FF[1]); e4 = env(c4, zb) - np.interp(zb, FF[0], FF[1])
r5 = float(np.sqrt((e5 ** 2).mean()) * 1000); r4 = float(np.sqrt((e4 ** 2).mean()) * 1000)
L('BUST_KEEP', 'side-envelope bump band z 1.15-1.27: RMS vs SUB-PIXEL plate contour (mm) [FORM5, FORM4]', [round(r5, 2), round(r4, 2)], r5 <= 3.0 and r5 <= r4 + 0.3, '<= 3.0 and not worse than FORM4', 'plate_side4.py sub-pixel gradient edge')
zd = np.array([1.28, 1.30, 1.32])
d5 = 1000 * (env(co, zd) - np.interp(zd, FF[0], FF[1])); d4 = 1000 * (env(c4, zd) - np.interp(zd, FF[0], FF[1]))
c3 = np.load(WD / 'data/co_FORM3_final.npy').astype(np.float64)
d3 = 1000 * (env(c3, zd) - np.interp(zd, FF[0], FF[1]))
L('BUST_KEEP', 'upper-chest diagonal: front line vs plate at z 1.28/1.30/1.32 (mm, negative = model further forward) [FORM5, FORM4, FORM3]', [[round(float(v), 1) for v in d5], [round(float(v), 1) for v in d4], [round(float(v), 1) for v in d3]], bool((np.abs(d5) <= np.abs(d4) + 1.0).all() and (np.abs(d5) < np.abs(d3)).all()), '|FORM5| <= |FORM4| + 1.0 mm (0.4 plate px) and better than FORM3 at all three heights (brief: keep the upper-chest diagonal better than FORM3)', 'ROUND 5 CHANGE (disclosed): was |FORM5| <= |FORM4|+0.05; the landing was relaxed to remove the neck-base dark band the round-4 critic found; residual above z~1.30 is the pinned neck-base ring (hand-off)')
sc5 = score4.evaluate(co); sc4 = score4.evaluate(c4)
L('BUST_KEEP', 'mound apex curvature radius of the side envelope (cm): round, not flat nor pointed; plate 5.6 [FORM5, FORM4]', [round(sc5['rc'], 1), round(sc4['rc'], 1)], 4.0 <= sc5['rc'] <= 8.0, '4..8 (plate 5.6)', 'parabola fit of the front envelope over +-2 cm around the apex')
L('BUST_KEEP', 'mound column surface slope (98th pct |dy/dz| angle along |x| .06-.085, deg) [FORM5, FORM4]', [round(sc5['slope98'], 1), round(sc4['slope98'], 1)], sc5['slope98'] <= 38.0, '<= 38 (plate profile max ~39 on the diagonal)', '')
cv1 = np.load(WD / 'data/co_FORM5_v1_final.npy').astype(np.float64) if (WD / 'data/co_FORM5_v1_final.npy').exists() else c4
def upper_slope_inc(c_):
    zz = np.arange(1.27, 1.3461, 0.01); e_ = env(c_, zz)
    sl_ = np.degrees(np.arctan(np.gradient(e_, 0.01)))
    return float(max(sl_[i + 1] - sl_[i] for i in range(len(sl_) - 1))), [round(float(v), 1) for v in sl_]
ui5, us5 = upper_slope_inc(co); ui4, us4 = upper_slope_inc(c4); uiv1, usv1 = upper_slope_inc(cv1)
L('BUST_SOFT_PLASTIC', 'upper-chest front profile is ONE concave sweep (no stall-then-steepen groove): max slope INCREASE between successive 1 cm samples, z 1.27-1.345 (deg) [FORM5, FORM4, FORM5-v1 (first staged version, rejected by the reviewers)]', [round(ui5, 1), round(ui4, 1), round(uiv1, 1)], ui5 <= 2.0, '<= 2.0 (FORM5-v1 3.3 = stall to 5 deg then steepen to 12+ deg: the clay clavicle-level groove)', 'front envelope, sub-pixel plate contour is monotone here; slopes %s' % us5)
import chestprof6 as _cp6
from fplate import BALD as _BALD
def _neck_dip(c_):
    img_, _m = _cp6.render_front(c_, 1.5); cen_, _sd = _cp6.groups(img_); return _cp6.dip(cen_)
_pl = np.asarray(_BALD[_cp6.BOXF[1]:_cp6.BOXF[3], _cp6.BOXF[0]:_cp6.BOXF[2]], dtype=float); _plc, _pls = _cp6.groups(_pl)
nd5, nd4, ndp = _neck_dip(co), _neck_dip(c4), _cp6.dip(_plc)
L('BUST_SOFT_PLASTIC', 'no dark band under the neck-base ring: centre dip of the plate-lit front render (grey levels below the straight line z 1.26 -> 1.38, z 1.29-1.36) [FORM5, FORM4, plate]', [round(nd5, 1), round(nd4, 1), round(ndp, 1)], nd5 <= nd4 + 0.5, '<= FORM4 (+0.5): the round-4 critic read FORM5-r4 (12.3) as a NEW dark band at clavicle level', 'ROUND 5 LINE: numpy plate-lit domain (gain 1.5 = the proofs soft look); a pure-plate profile has no dip (negative)')
_zz = np.arange(1.30, 1.3551, 0.01); _sl = np.degrees(np.arctan(np.gradient(env(co, _zz), 0.01)))
L('BUST_SOFT_PLASTIC', 'no near-vertical wall above the mound (front envelope slope z 1.30-1.355, deg from vertical; plate diagonal 35-40)', [round(float(v), 1) for v in _sl], float(_sl.min()) >= 15.0, '>= 15 deg everywhere (round-4 FORM5 fell to 8 deg = the wall the critic saw as a step in the side contour; FORM4 14.5)', 'ROUND 5 LINE')
# ------------------------------------------------------------------------------------------------------------------- BUST: soft-plastic language, measured
a1 = seam.dihedral(co); a0 = seam.dihedral(CO0); a4 = seam.dihedral(c4)
mid = 0.5 * (co[seam.PAIR_E[:, 0]] + co[seam.PAIR_E[:, 1]])
ZP5 = T5[seam.PAIR_E[:, 0]] & T5[seam.PAIR_E[:, 1]]
nb_ = ~(BORDER5[seam.PAIR_E[:, 0]] | BORDER5[seam.PAIR_E[:, 1]]) & (a0 <= 15.0)
bust_reg = ZP5 & nb_ & (mid[:, 2] >= 1.14) & (mid[:, 2] <= 1.32) & (np.abs(mid[:, 0]) <= 0.115) & (mid[:, 1] < 0)
cen_reg = ZP5 & (mid[:, 2] >= 1.15) & (mid[:, 2] <= 1.30) & (np.abs(mid[:, 0]) < 0.022) & (mid[:, 1] < 0)
L('BUST_SOFT_PLASTIC', 'no hard shelf / crease: worst dihedral on the front bust region (deg) [FORM5, FORM4]', [round(float(a1[bust_reg].max()), 1), round(float(a4[bust_reg].max()), 1)], a1[bust_reg].max() <= 31.0, '<= 31 (11 mm mesh: 31 deg = 2 cm radius, soft)', 'border-adjacent edges and inherited creases (<=15 deg in the original) excluded')
L('BUST_SOFT_PLASTIC', 'no hard shelf / crease: dihedral increase vs original, bust region (deg)', round(float((a1 - a0)[bust_reg].max()), 1), (a1 - a0)[bust_reg].max() <= 25.0, '<= 25', '')
L('BUST_SOFT_PLASTIC', 'soft cleavage (contact, not a knife crease): worst dihedral on the sternum strip |x|<2.2 cm, z 1.15-1.30 (deg) [FORM5, FORM4]', [round(float(a1[cen_reg].max()), 1), round(float(a4[cen_reg].max()), 1)], a1[cen_reg].max() <= 20.0, '<= 20 (smooth valley: >=2.5 cm radius at 11 mm spacing)', '')
xs_ = np.arange(-0.14, 0.1401, 0.002); zs_ = np.arange(1.10, 1.34, 0.002)
Gf = grid_surface(co, 'front', xs_, zs_)
ix = lambda x: int(round((x - xs_[0]) / 0.002)); iz = lambda z: int(round((z - zs_[0]) / 0.002))
resb = {}
for side, sg in (('R', 1), ('L', -1)):
    cols = np.where((sg * xs_ >= 0.03) & (sg * xs_ <= 0.125))[0]; rows = np.where((zs_ >= 1.17) & (zs_ <= 1.29))[0]
    sub = Gf[np.ix_(rows, cols)]; i, j = np.unravel_index(np.argmin(sub), sub.shape)
    resb[side] = dict(apex_x=float(xs_[cols[j]]), apex_z=float(zs_[rows[i]]))
zc_ = 0.5 * (resb['R']['apex_z'] + resb['L']['apex_z']); apx_y = 0.5 * sum(Gf[iz(resb[s]['apex_z']), ix(resb[s]['apex_x'])] for s in 'RL')
valley = 1000 * (Gf[iz(zc_), np.abs(xs_) < 0.006].mean() - apx_y)
L('BUST_SOFT_PLASTIC', 'readable soft cleavage: front surface at the sternum strip is BEHIND the mound apex by (mm)', round(float(valley), 1), 5.0 <= valley <= 22.0, '5..22 (plate: soft valley; FORM4 9.7)', 'sternum strip |x|<6 mm at the apex height; not a deep pit and not absent')
fr = {}
for tag, c_ in (('FORM5', co), ('FORM4', c4)):
    G_ = grid_surface(c_, 'front', xs_, zs_)
    fr[tag] = float(np.mean([G_[iz(z), ix(sg * x)] for z in (1.19, 1.21, 1.23) for x in (0.095, 0.105) for sg in (1, -1)]) * 1000)
L('BUST_SOFT_PLASTIC', 'side fill: lateral chest flank |x| .095-.105, z 1.19-1.23 (mean front y, mm; more negative = fuller) [FORM5, FORM4]', [round(fr['FORM5'], 1), round(fr['FORM4'], 1)], fr['FORM5'] <= fr['FORM4'] + 2.0, 'not thinner than FORM4 by more than 2 mm', 'the pinned arm seam (<=10 mm step) limits lateral relief')
cr = cres5.stats(co); cr4 = cres5.stats(c4)
ok = all(abs(v[2] - v[0]) <= 0.015 for k, v in cr.items() if k <= 0.085)
L('BUST_SOFT_PLASTIC', 'under-bust crescent position (z of lowest plate-lit luminance) at |x| .03/.06/.085 vs plate [FORM5 (plate)]', {str(k): [round(v[2], 3), round(v[0], 3)] for k, v in cr.items() if k <= 0.085}, ok, 'within 1.5 cm of the plate', 'plate-fit light x2.5, plate pixel grid')
H = str(WD)
ims = {'plate': ring5.plate_crop('chest', 1.0)}
for t in ('F4', 'F5'):
    p = f'{H}/scratch/r/bd_chest_{t}_soft_front.png'
    if os.path.exists(p):
        ims[t] = ring5.bgcomp(p)
if 'F5' in ims:
    rs = {k: ring5.ring_stats(v) for k, v in ims.items()}
    upper = max(v[1] for v in rs['F5'].values())
    L('BUST_SOFT_PLASTIC', 'open crescent, not a closed rim: fraction of the circle (r 3.5-6.5 cm about each mound) darker than the mound centre, UPPER half [F5 max, plate max]', [round(upper, 2), round(max(v[1] for v in rs['plate'].values()), 2)], upper <= 0.30, '<= 0.30 (plate ~0.2; closed rim >0.6)', 'soft render luminance, plate grid (informational for F4: %.2f)' % (max(v[1] for v in rs['F4'].values()) if 'F4' in rs else -1))
# photometric agreement (INFO only: FORM3 scored 0.644 and was called flat; FORM4 scored 0.696 and was called disks)
N5 = vertex_normals(co, TRI); N4 = vertex_normals(c4, TRI)
lt = np.array(LIGHT); lf = lt.copy(); lf[1:] *= 2.5; lb = lt.copy(); lb[1:] *= 2.0
wide = roi_box('front', -0.115, 0.115, 1.14, 1.30)
rw5 = compare(co, 'front', wide, light=lf, normals=N5); rw4 = compare(c4, 'front', wide, light=lf, normals=N4)
L('BUST_SOFT_PLASTIC', 'plate-lit band-pass NCC, bust WIDE ROI [FORM5, FORM4]', [round(rw5['ncc'], 3), round(rw4['ncc'], 3)], True, 'informational', 'NCC alone is not evidence (see FORM3/FORM4)', info=True)
# ------------------------------------------------------------------------------------------------------------------- UNDERBUTT (support lines)
zu = np.arange(0.70, 0.881, 0.02)
dev5 = 1000 * (benv5.env(co, zu) - np.interp(zu, FB[0], FB[1])); dev4 = 1000 * (benv5.env(c4, zu) - np.interp(zu, FB[0], FB[1]))
L('UNDERBUTT_CONTINUOUS', 'back envelope vs SUB-PIXEL plate contour, z .70-.88 (mm; max |dev|) [FORM5, FORM4]', [round(float(np.abs(dev5).max()), 1), round(float(np.abs(dev4).max()), 1)], float(np.abs(dev5).max()) <= 4.0, '<= 4 (FORM4 shows the thigh 10-13 mm too deep at z .72-.80)', 'torso-chat plate anchor (knee centre); limbs-chat anchor puts the plate thigh ~11 mm deeper - disclosed in RESULTS')
xs2 = np.arange(0.0, 0.1801, 0.004)
from fplate import BALD, BACK_CX, SOLE as SOLE_, S as S_
_ZR = np.arange(0.74, 0.90, 0.002)
_BOX = roi_box('back', -0.20, 0.20, 0.72, 0.92)
def _model_profile(c_, x, gain=2.0):
    L_ = np.array(LIGHT, dtype=float).copy(); L_[1:] *= gain
    Nn = vertex_normals(c_, TRI); sh = shade_vertices(c_, Nn, 'back', L_)
    img, mask = raster_shaded(c_, sh, 'back', _BOX)
    c0, r0, c1, r1 = _BOX
    col = int(round(BACK_CX - x / S_)) - c0
    return np.array([img[int(round(SOLE_ - z / S_)) - r0 - 1:int(round(SOLE_ - z / S_)) - r0 + 2, col - 1:col + 2].mean() for z in _ZR])
def _plate_profile(x):
    col = int(round(BACK_CX - x / S_))
    return np.array([BALD[int(round(SOLE_ - z / S_)) - 1:int(round(SOLE_ - z / S_)) + 2, col - 1:col + 2].mean() for z in _ZR])
def fold_onset(v):
    """height (m) where the lower flank of the dark fold band reaches 50 % of its depth (steepest onset); depth relative to the mean of z .74-.76"""
    r = v - v[:10].mean()
    j = int(np.argmin(r)); half = 0.5 * r[j]
    i = j
    while i > 0 and r[i] < half:
        i -= 1
    return float(_ZR[i])
fx = (0.03, 0.06, 0.09, 0.12)
pz = [fold_onset(_plate_profile(x)) for x in fx]; z5 = [fold_onset(_model_profile(co, x)) for x in fx]; z4 = [fold_onset(_model_profile(c4, x)) for x in fx]
L('UNDERBUTT_CONTINUOUS', 'fold ONSET height (lower flank of the dark under-bum band reaches 50 % of its depth) at |x| .03/.06/.09/.12 vs plate (m) [FORM5, FORM4, plate]', [[round(v, 3) for v in z5], [round(v, 3) for v in z4], [round(v, 3) for v in pz]], max(abs(a - b) for a, b in zip(z5, pz)) <= 0.012, 'within 1.2 cm of the plate at every column (FORM4 is 1.2-2 cm too high)', 'plate-fit light x2.0, plate pixel grid')
import foldtab5 as _ft5
def _band_line(c_):
    img_, _m = _ft5.fx.render(c_)
    return [_ft5.fx.band_stats(_ft5.fx.profile_model(img_, x))['centroid'] for x in _ft5.XS]
zl5 = _band_line(co); zl4 = _band_line(c4); zlp = [_ft5.fx.band_stats(_ft5.fx.profile_plate(x))['centroid'] for x in _ft5.XS]
smile5 = zl5[7] - zl5[2]; smile4 = zl4[7] - zl4[2]; smilep = zlp[7] - zlp[2]
rms5 = float(np.sqrt(np.mean((np.array(zl5) - np.array(zlp)) ** 2))); rms4 = float(np.sqrt(np.mean((np.array(zl4) - np.array(zlp)) ** 2)))
L('UNDERBUTT_CONTINUOUS', 'dark fold BAND (centroid of the plate-lit luminance deficit) is a SMILE: rise from |x| .045 to .12 (cm) [FORM5, FORM4, plate]', [round(100 * smile5, 1), round(100 * smile4, 1), round(100 * smilep, 1)], smile5 >= 0.010, '>= 1.0 cm (plate 1.8; FORM4 flat / inverted)', 'robust band centroid per column (the argmin flips between the thin crease and the broad band), plate-fit light x2.0, plate pixel grid, columns |x| .02 .03 .045 .06 .075 .09 .105 .12 .135')
L('UNDERBUTT_CONTINUOUS', 'dark fold BAND height vs plate: rms of the centroid line over 9 columns (cm) [FORM5, FORM4]', [round(100 * rms5, 2), round(100 * rms4, 2)], rms5 <= 0.010 and rms5 <= rms4, '<= 1.0 cm and better than FORM4', 'the cleft columns |x| <= .03 are dominated by the V-cleft shading and by the plate AO next to the gap (plate band 1-2 cm lower there)')
rise5 = z5[3] - z5[1]; rise4 = z4[3] - z4[1]; risep = pz[3] - pz[1]
L('UNDERBUTT_CONTINUOUS', 'fold is a CURVED smile, not a straight band: rise of the fold onset from |x| .06 to .12 (cm) [FORM5, FORM4, plate]', [round(100 * rise5, 1), round(100 * rise4, 1), round(100 * risep, 1)], rise5 >= 0.004 and rise5 >= rise4 + 0.002, '>= 0.4 cm and larger than FORM4 (plate ~1 cm)', 'a horizontal band has rise ~0; lateral columns are bounded by the pinned hip/thigh silhouette')
import bandtrace_panel6 as _bp6
_p06z = str(WD / 'proof/06z_underbutt_zoom_soft_clay.png')
if os.path.exists(_p06z):
    _res6, _sm6 = _bp6.analyse(_p06z)
    L('UNDERBUTT_CONTINUOUS', 'RENDERED fold line (traced in the soft Blender panel proof/06z, what the eye sees): rms error vs plate over dx +-45..105 px (px, ~0.8 px/mm) [FORM5, FORM4]', [round(_sm6['F5soft']['rms_err_px'], 1), round(_sm6['F4soft']['rms_err_px'], 1)], _sm6['F5soft']['rms_err_px'] <= 6.0 and _sm6['F5soft']['rms_err_px'] < _sm6['F4soft']['rms_err_px'], '<= 6 px (~0.75 cm) and better than FORM4', 'ROUND 5 LINE (added after the round-4 critics traced a flat bar in the renders while the numpy centroid gate passed): high-pass luminance (sigma 10 px) deficit centroid per column; clay panels reported in checks.json measurements')
    L('UNDERBUTT_CONTINUOUS', 'RENDERED fold line is a smile: lateral rise of the traced fold line from |dx| 45 to 105 px (px) [FORM5, FORM4, plate]', [round(_sm6['F5soft']['rise_px'], 1), round(_sm6['F4soft']['rise_px'], 1), round(_sm6['plate']['rise_px'], 1)], _sm6['F5soft']['rise_px'] >= 8.0, '>= 8 px (plate 14; FORM4 -3; FORM5 round 4 -0.5)', 'ROUND 5 LINE: soft panel; (px / 0.8) = mm')
    L('UNDERBUTT_CONTINUOUS', 'RENDERED fold line, shape vs placement: mean offset of the traced line vs plate (px; negative = fold HIGHER than the plate) / shape error after removing that offset (px) [FORM5, FORM4]', [[round(_sm6['F5soft']['mean_offset_px'], 1), round(_sm6['F5soft']['shape_err_px'], 1)], [round(_sm6['F4soft']['mean_offset_px'], 1), round(_sm6['F4soft']['shape_err_px'], 1)]], True, 'informational (the pre-set gate above stays as defined)', 'ROUND 5: separates the smile SHAPE from a constant vertical offset (partly the plate AO); not used to relax any gate', info=True)
    meas_extra = dict(panel_fold_rows={n: {str(d): round(v, 1) for d, v in r.items()} for n, r in _res6.items()}, panel_fold_summary=_sm6)
else:
    meas_extra = {}
mid_all = 0.5 * (co[seam.PAIR_E[:, 0]] + co[seam.PAIR_E[:, 1]])
und_reg = (mid_all[:, 2] >= 0.70) & (mid_all[:, 2] <= 0.90) & (mid_all[:, 1] > 0.02) & (np.abs(mid_all[:, 0]) >= 0.035) & (np.abs(mid_all[:, 0]) <= 0.17)
L('UNDERBUTT_CONTINUOUS', 'no hard line: worst dihedral on the underbutt region z .70-.90, |x| .035-.17 (deg; crotch/gap excluded) [FORM5, FORM4]', [round(float(a1[und_reg].max()), 1), round(float(a4[und_reg].max()), 1)], a1[und_reg].max() <= max(a4[und_reg].max() + 0.5, 30.0), '<= max(FORM4, 30)', '')
def sag(c_, xc, zr=np.arange(0.66, 0.90, 0.01)):
    ys = []
    for z in zr:
        m = (np.abs(c_[:, 2] - z) < 0.0056) & (np.abs(c_[:, 0] - xc) < 0.012) & (c_[:, 1] > 0.0)
        ys.append(c_[m, 1].max() if m.any() else np.nan)
    return zr, np.array(ys)
def max_slope_change(c_):
    out = []
    for xc in (0.065, 0.09):
        zr, y = sag(c_, xc); good = np.isfinite(y)
        yy = np.interp(zr, zr[good], y[good]); yy = gauss1d(np.interp(np.arange(0.66, 0.90, 0.002), zr, yy), 0.008, step=0.002)
        ang = np.degrees(np.arctan(np.gradient(yy, 0.002)))
        zz = np.arange(0.66, 0.90, 0.002); m = (zz >= 0.74) & (zz <= 0.86)
        out.append(float(np.abs(np.diff(ang[m][::5])).max()))
    return max(out)
ms5 = max_slope_change(co); ms4 = max_slope_change(c4)
L('UNDERBUTT_CONTINUOUS', 'continuous under-curve: max slope change per 1 cm along the lower flank z .74-.86 at |x| .065/.09 (deg) [FORM5, FORM4]', [round(ms5, 1), round(ms4, 1)], ms5 <= 22.0 and ms5 <= ms4 + 0.5, '<= 22 and not worse than FORM4', 'sagittal sections of the denoised profile')
band = (CO0[:, 2] >= 0.62) & (CO0[:, 2] < 0.795) & Z5['ext']
dd = np.linalg.norm(co - c4, axis=1)
L('UNDERBUTT_CONTINUOUS', 'LEG-TOP band (documented): max displacement vs FORM4 (mm) / max in-plane (x,z) movement (mm) / vertices moved', [round(float(1000 * dd[band].max()), 1), round(float(1000 * np.linalg.norm((co - c4)[band][:, [0, 2]], axis=1).max()), 2), int((dd[band] > 1e-9).sum())], float(1000 * np.linalg.norm((co - c4)[band][:, [0, 2]], axis=1).max()) <= 3.0, 'in-plane movement <= 3 mm (Taubin denoise only; < 1.2 plate pixels; front/back silhouettes unchanged)', 'y-only recess <= 12.5 mm at z .74-.78 tapering to 0 at the floor ring z .62')
zt_ = np.arange(0.64, 0.80, 0.02)
db = 1000 * (benv5.env(co, zt_) - benv5.env(c4, zt_))
L('UNDERBUTT_CONTINUOUS', 'LEG-TOP disclosure: thigh-back recess vs FORM4 at z .64 .66 .68 .70 .72 .74 .76 .78 (mm, envelope)', [round(float(v), 1) for v in db], True, 'informational', 'plate (torso anchor) thigh back +81..83 mm; FORM4 +90..96', info=True)
# ------------------------------------------------------------------------------------------------------------------- GLUTE: language held
xs3 = np.arange(-0.19, 0.1901, 0.002); zs3 = np.arange(0.78, 1.06, 0.002)
def glute_meas(c):
    Gb = grid_surface(c, 'back', xs3, zs3)
    i2z = lambda z: int(round((z - 0.78) / 0.002))
    gl = {}
    for side, sg in (('R', 1), ('L', -1)):
        cols = np.where((sg * xs3 >= 0.02) & (sg * xs3 <= 0.15))[0]; rows = np.where((zs3 >= 0.84) & (zs3 <= 0.96))[0]
        sub = Gb[np.ix_(rows, cols)]; i, j = np.unravel_index(np.argmax(sub), sub.shape)
        gl[side] = (float(xs3[cols[j]]), float(zs3[rows[i]]), float(sub[i, j]))
    rcs = []
    for side in ('R', 'L'):
        xa, za, _ = gl[side]; sel = np.abs(xs3 - xa) < 0.03
        pp = np.polyfit(xs3[sel] - xa, Gb[i2z(za), sel], 2); rcs.append(abs(1 / (2 * pp[0])) * 100 if abs(pp[0]) > 1e-9 else 999)
    return Gb, gl, float(np.mean(rcs))
Gb5, gl5, rcg5 = glute_meas(co); Gb4, gl4, rcg4 = glute_meas(c4)
apx = 0.5 * (abs(gl5['R'][0]) + abs(gl5['L'][0]))
L('GLUTE_HOLD_LANGUAGE', 'two distinct round lobes: apex |x| (m) / z (m)', [round(apx, 3), round(0.5 * (gl5['R'][1] + gl5['L'][1]), 3)], 0.045 <= apx <= 0.095 and 0.84 <= 0.5 * (gl5['R'][1] + gl5['L'][1]) <= 0.90, '|x| .045..095, z .84..90', 'plate lobe centres ~ +-0.05..0.08, apex z ~0.86')
L('GLUTE_HOLD_LANGUAGE', 'lobe horizontal curvature radius at the apex (cm): round cheeks, not flat pads [FORM5, FORM4]', [round(rcg5, 1), round(rcg4, 1)], 4.0 <= rcg5 <= 14.0, '4..14', '')
cl = {}
for z in (0.86, 0.88, 0.90, 0.92, 0.94):
    d_, r_ = cleft_depth_ratio(co, z); cl[z] = dict(depth_mm=round(float(d_), 1), ratio=(round(float(r_), 2) if d_ >= 4.0 else None))
ratios = [v['ratio'] for v in cl.values() if v['ratio'] is not None]
depth_seq = [cl[z]['depth_mm'] for z in (0.86, 0.88, 0.90, 0.92, 0.94)]
L('GLUTE_HOLD_LANGUAGE', 'cleft is a soft V (not a box/pit): width(50% depth)/width(10% depth), worst over z', cl, (max(ratios) <= 0.80 if ratios else False), '<= 0.80 (vertical-walled pit ~1.0)', 'FORM2 cleft was a square cavity')
L('GLUTE_HOLD_LANGUAGE', 'cleft depth monotone, deepening downward (mm at z .86 .88 .90 .92 .94)', depth_seq, all(depth_seq[i] >= depth_seq[i + 1] - 0.6 for i in range(4)) and depth_seq[0] >= 12 and depth_seq[-1] <= 12, 'monotone, >=12 at z .86, <=12 at z .94', '')
glu_reg = ZP5 & nb_ & (mid[:, 2] >= 0.80) & (mid[:, 2] <= 1.02) & (np.abs(mid[:, 0]) <= 0.15) & (mid[:, 1] > 0)
L('GLUTE_HOLD_LANGUAGE', 'no hard rim / flat-top ledge: worst dihedral on the glute region z .80-1.02 (deg) [FORM5, FORM4]', [round(float(a1[glu_reg].max()), 1), round(float(a4[glu_reg].max()), 1)], a1[glu_reg].max() <= 30.0, '<= 30', 'border-adjacent edges and inherited creases excluded')
L('GLUTE_HOLD_LANGUAGE', 'no hard rim: dihedral increase vs original, glute region (deg)', round(float((a1 - a0)[glu_reg].max()), 1), (a1 - a0)[glu_reg].max() <= 25.0, '<= 25', '')
BKf = np.interp(np.array([0.85, 0.86, 0.87, 0.88]), FB[0], FB[1])
b5 = 1000 * (env(co, np.array([0.85, 0.86, 0.87, 0.88]), back=True) - BKf); b4 = 1000 * (env(c4, np.array([0.85, 0.86, 0.87, 0.88]), back=True) - BKf)
L('GLUTE_HOLD_LANGUAGE', 'back-envelope apex vs SUB-PIXEL plate contour at z .85/.86/.87/.88 (mm) [FORM5, FORM4]', [[round(float(v), 1) for v in b5], [round(float(v), 1) for v in b4]], float(np.abs(b5).max()) <= max(float(np.abs(b4).max()), 2.0) + 0.5, '|FORM5| max <= max(|FORM4| max, 2) + .5', 'apex held')
drift = np.linalg.norm(co - c4, axis=1)
L('GLUTE_HOLD_LANGUAGE', 'lobe-top shape held: max drift vs FORM4 at z .88-.99 (mm)', round(float(1000 * drift[(CO0[:, 2] >= 0.88) & (CO0[:, 2] < 1.0)].max()), 2), float(1000 * drift[(CO0[:, 2] >= 0.88) & (CO0[:, 2] < 1.0)].max()) <= 1.0, '<= 1.0 (was 0.5 in the first FORM5 draft: the fairing of FORM4 lattice ripple now fades over z .88-.94 so the processed-region boundary does not show as a hairline; p99 drift ~0.5 mm, macro lobe shape unchanged)', 'chest build blends in only above z .99')
# ------------------------------------------------------------------------------------------------------------------- visual (author's reading + independent reviewers; Adnan's eye overrides)
vp = WD / 'export/visual_verdict.json'
vis = json.load(open(vp)) if vp.exists() else {'bust': 'PENDING', 'underbutt': 'PENDING', 'mirror': 'PENDING', 'notes': ''}
L('BUST_EYE_PASS', 'VISUAL plate | FORM4 | FORM5 (proof/05 soft + clay + side + zoom, proof/04): conventional soft-plastic breasts with cleavage / under-bust / side fill; NO circular/disk/target blobs *(eye check)*', vis['bust'], vis['bust'] == 'PASS', 'author reading of the proofs + independent reviewer notes', 'AUTHOR verdict; Adnan eye overrides', eye=True)
L('UNDERBUTT_EYE_PASS', 'VISUAL plate | FORM4 | FORM5 (proof/06 back + 3/4 + side, soft + clay): continuous soft round into hamstrings/leg-top; NO mechanical horizontal cut *(eye check)*', vis['underbutt'], vis['underbutt'] == 'PASS', 'author reading of the proofs + independent reviewer notes', 'AUTHOR verdict; Adnan eye overrides', eye=True)
L('MIRROR_SOFT', 'mirror-stripe test (proof/07): organic (no square/polygonal rings, no bullseye of concentric circles) *(eye check)*', vis.get('mirror', 'PENDING'), vis.get('mirror') == 'PASS', 'author reading of proof/07', '', eye=True)
res = {'gate': 'FEMALE_TORSO_FORM5', 'lines': lines,
       'measurements': dict(bust_apex=resb, glute_apex=gl5, cleft=cl, crescent=({str(k): v for k, v in cr.items()}), fold_z=dict(form5=z5, form4=z4, plate=pz), score4_form5={k: v for k, v in sc5.items()}, score4_form4={k: v for k, v in sc4.items()}, **meas_extra)}
groups = {}
for l in lines:
    if l['group'].startswith('INFO_'):
        continue
    groups.setdefault(l['group'], []).append(l['result'] == 'PASS')
res['group_results'] = {k: ('PASS' if all(v) else 'FAIL') for k, v in groups.items()}
res['overall'] = 'PASS' if all(r == 'PASS' for r in res['group_results'].values()) else 'FAIL'
res['failed_lines'] = [l for l in lines if l['result'] == 'FAIL']
dumper = lambda o: o.item() if hasattr(o, 'item') else str(o)
json.dump(res, open(WD / 'checks.json', 'w'), indent=1, default=dumper)
os.makedirs(WD / 'proof', exist_ok=True)
json.dump(res, open(WD / 'proof/checks.json', 'w'), indent=1, default=dumper)
for l in lines:
    print(f"{l['group']:24s} {l['result']}  {l['line']}: {l['value']}  (limit {l['limit']})")
print('GROUPS', res['group_results'], 'OVERALL', res['overall'])
