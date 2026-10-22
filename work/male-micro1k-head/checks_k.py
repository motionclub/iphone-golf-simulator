"""Numeric gate checks for MALE_HEAD_RESULTS (Micro1k) / male-micro1k-checks.json (numpy only).
python3.13 checks_k.py <tag> <audit_vs_micro1j.json> <audit_merged.json> <out.json>
V = data/V_<tag>.npy (edit on the installed Micro1j blend 72fc6465), data/V_<tag>nc.npy = same without the mandible crest / trim."""
import sys, json, hashlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head')
from k_edit import *
import k_mand as KM
import contours as C
tag = sys.argv[1]; a0 = json.load(open(sys.argv[2])); am = json.load(open(sys.argv[3])); outp = sys.argv[4]
ctx = KCtx(); V0 = ctx.V0; E = ctx.E
V1 = np.load(W / f'data/V_{tag}.npy'); Vnc = np.load(W / f'data/V_{tag}nc.npy'); Va = np.load(W / 'data/V_a_only.npy'); Vh0 = np.load(I1 / 'data/V_h0.npy')
D = V1 - V0; d = np.linalg.norm(D, axis=1); mv = d > 0
x, y, z = V0[:, 0], V0[:, 1], V0[:, 2]
res = dict(created='2026-10-01', brief='01b_MALE_HEAD_Micro1k.txt', scope='male head+neck zone z>=1.40 plus the Adnan-approved nape strip (z 1.352-1.40); position-only on the installed Micro1j topology')
res['hashes'] = dict(start_blend_micro1j='72fc6465f0623a3c963ca3af58a5358c0a498265c7b9da059a941b58050c1059', artdir_blend_at_install_start='59a74b8573a089198207a6155ad815625d55f4c670531d6530bc698c1b78ac28',
                     artdir_fbx_at_install_start='0454f6c36cdc2199d3a4e7885a7087821ea2642a764e90edda203920e89072a1', delta_D_sha256=hashlib.sha256(np.ascontiguousarray(D).tobytes()).hexdigest())
gates = {}
# ---------------- ZONE ----------------
strip = mv & ~ctx.zone
zone = dict(zone='start z >= 1.40 (+ nape strip z 1.352-1.40)', moved_total_numeric=int(mv.sum()), moved_below_z_1_40=int(strip.sum()),
            nape_strip_z_range=[float(z[strip].min()), float(z[strip].max())], nape_strip_max_abs_x_mm=float(np.abs(x[strip]).max() * 1000), nape_strip_max_move_mm=float(d[strip].max() * 1000),
            hands_moved=int((mv & (np.abs(x) > 0.44) & (z < 1.06)).sum()), arms_moved=int((mv & (np.abs(x) > 0.14) & (z >= 1.06)).sum()),
            torso_legs_feet_moved_excluding_nape_strip=int((mv & (z < 1.40) & ~((z >= 1.35) & (z < 1.40) & (np.abs(x) < 0.0255) & (y > 0))).sum()),
            max_move_mm_total=float(d.max() * 1000))
res['zone_audit'] = zone
res['audit_micro1k_alone_on_micro1j_72fc6465'] = {k: a0[k] for k in ('moved_total', 'moved_outside_zone_z_lt_1_40', 'min_z_of_moved_verts', 'hands_moved', 'arms_moved', 'torso_pelvis_legs_feet_moved', 'topology_identical', 'tris', 'vertex_groups_identical', 'face_m_identical', 'boundary_edges', 'nonmanifold_edges', 'normals_far_from_edit', 'normals_edit_region', 'silhouette')}
res['audit_merged_on_artdir_59a74b85'] = {k: am[k] for k in ('moved_total', 'moved_outside_zone_z_lt_1_40', 'min_z_of_moved_verts', 'hands_moved', 'arms_moved', 'topology_identical', 'tris', 'vertex_groups_identical', 'face_m_identical', 'silhouette')}
gates['ZONE_OUTSIDE'] = bool(zone['moved_below_z_1_40'] <= 40 and zone['nape_strip_max_move_mm'] <= 2.0 and zone['nape_strip_max_abs_x_mm'] <= 25.6 and zone['hands_moved'] == 0 and zone['arms_moved'] == 0
                             and zone['torso_legs_feet_moved_excluding_nape_strip'] == 0 and am['face_m_identical'] and am['topology_identical'] and am['vertex_groups_identical'])
# ---------------- 1 KILL_NECK_JAW_CREASE ----------------
DJ = np.load(W / 'data/Djaw_j1.npy'); fp = np.linalg.norm(DJ, axis=1) > 0.3e-3; Na = vertex_normals(Va, ctx.F)
lat = fp & (np.abs(x) > 0.04) & (z > 1.455)                       # lateral jaw/neck footprint of the rejected relief (the midline under-chin junction is natural geometry, excluded)
rs = ((V0 - Va) * Na).sum(1) * 1000; r1 = ((V1 - Va) * Na).sum(1) * 1000
big = feather(ctx, fp.astype(float), 6); big[~ctx.zone] = 0
rel = {}
for nm, V in (('START_micro1j', V0), ('pre_relief_micro1i_state', Va), (tag, V1)):
    N = vertex_normals(V, ctx.F); Vlp = ctx.M.taubin(V, big, iters=25, lam=0.5, mu=-0.53); r = ((V - Vlp) * N).sum(1) * 1000
    rel[nm] = dict(min_mm=float(r[lat].min()), p05_mm=float(np.percentile(r[lat], 5)), rms_mm=float(np.sqrt((r[lat] ** 2).mean())))
res['kill_neck_jaw_crease'] = dict(lateral_footprint_verts=int(lat.sum()), micro1j_relief_vs_pre_relief_normal_mm=dict(min=float(rs[lat].min()), max=float(rs[lat].max())),
                                   now_vs_pre_relief_normal_mm=dict(min=float(r1[lat].min()), max=float(r1[lat].max())), lowpass_residual_on_lateral_footprint=rel,
                                   pass_rule='recess on the old lateral footprint: now min >= -1.5 mm vs the pre-relief surface (Micro1j -5.98) AND low-pass residual min not worse than the pre-relief surface by > 0.3 mm')
gates['KILL_NECK_JAW_CREASE'] = bool(r1[lat].min() >= -1.5 and rel[tag]['min_mm'] >= rel['pre_relief_micro1i_state']['min_mm'] - 0.3)
# ---------------- 2 REAL_MANDIBLE_PROFILE ----------------
Nnc = vertex_normals(Vnc, ctx.F); H = ((V1 - Vnc) * Nnc).sum(1) * 1000        # crest + trim normal displacement (mm), + = out
bins = []; bodyok = []
for side in (1, -1):
    s, t, arc = KM.arc_field(ctx, Vnc, Nnc, side, ctrl=KM.ARC_NAT, passes=12)
    arcl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(arc, axis=0), axis=1))]) * 1000       # mm along the arc
    near = np.where(np.isfinite(s) & (np.abs(s) < 0.0035) & (V0[:, 0] * side > 0.004))[0]
    L = arcl[-1]
    for lo in np.arange(0, L, 10.0):
        sel = [v for v in near if lo <= arcl[min(int(round(t[v] * (len(arc) - 1))), len(arc) - 1)] < lo + 10.0]
        if sel: bins.append((side, float(lo), float(L), float(np.max(H[sel]))))
tb = {}
for side, lo, L, h in bins: tb.setdefault(int(lo), []).append(h)
tab = [dict(arc_mm_from_chin_end=k, crest_height_mm_L_R_max=float(np.max(v)), crest_height_mm_L_R_min=float(np.min(v))) for k, v in sorted(tb.items())]
body = [r for r in tab if 20 <= r['arc_mm_from_chin_end'] <= 80]                # chin-fade-in .. gonial angle: the jaw BODY
res['real_mandible'] = dict(crest_height_along_arc=tab, arc_length_mm=float(bins[0][2]), jaw_body_bins_20_80mm_min_of_sides_mm=float(min(r['crest_height_mm_L_R_min'] for r in body)),
                            max_crest_height_mm=float(H.max()), crest_verts_gt_0_3mm=int((H > 0.3).sum()),
                            placement_note='crest follows the mesh natural jaw border (n_z = -0.5 iso-line + plate angle/ramus); the plate-derived border (profile-plate tone edge) is 6-12 mm lower along the jaw body and coincides at the angle (see proof/arc_overlay)')
# plate contours at the jaw rows
pa = C.report_profile(V0, E, rows=range(200, 266, 4), verbose=False); pb = C.report_profile(V1, E, rows=range(200, 266, 4), verbose=False)
jr = {str(r): dict(start=[float(v) for v in pa[r][:3]], now=[float(v) for v in pb[r][:3]]) for r in pa if 228 <= r <= 264}
res['jaw_rows_vs_plate_mm_(front_y,back_y,half_width)'] = jr
hw_now = max(abs(pb[r][2]) for r in pb if 228 <= r <= 264); hw_start = max(abs(pa[r][2]) for r in pa if 228 <= r <= 264)
res['jaw_rows_half_width_max_abs_err_mm'] = dict(start=float(hw_start), now=float(hw_now))
gates['REAL_MANDIBLE_PROFILE'] = bool(res['real_mandible']['jaw_body_bins_20_80mm_min_of_sides_mm'] >= 1.2 and r1[lat].min() >= -1.5 and hw_now <= 3.0)
# ---------------- 3 CHEEK_SOFTEN ----------------
w = cheek_weight(ctx, V0); reg = w > 0.5; Nh = vertex_normals(Vh0, ctx.F); ch = {}
for nm, V in (('START_micro1j', V0), (tag, V1)):
    r = ((V - Vh0) * Nh).sum(1)[reg] * 1000
    ch[nm] = dict(rms_mm=float(np.sqrt((r ** 2).mean())), p95_abs_mm=float(np.percentile(np.abs(r), 95)), max_ridge_mm=float(r.max()), max_hollow_mm=float(r.min()))
res['cheek_soften'] = dict(region='face-lateral cheek, weight>0.5', verts=int(reg.sum()), deviation_from_micro1h_smooth_cheek=ch, malar_ridge_reduction_pct=float(100 * (1 - ch[tag]['max_ridge_mm'] / ch['START_micro1j']['max_ridge_mm'])),
                           hollow_reduction_pct=float(100 * (1 - ch[tag]['max_hollow_mm'] / ch['START_micro1j']['max_hollow_mm'])),
                           pass_rule='deviation RMS from the smooth Micro1h cheek reduced by >= 35 % but not below 25 % of start (still defined, not a blank cheek)')
red = 1 - ch[tag]['rms_mm'] / ch['START_micro1j']['rms_mm']
gates['CHEEK_SOFTEN'] = bool(red >= 0.35 and ch[tag]['rms_mm'] >= 0.25 * ch['START_micro1j']['rms_mm'])
# ---------------- 4 NAPE_LUMP ----------------
m = (np.abs(x) < 0.0075) & (y > 0) & (z > 1.345) & (z < 1.41); idx = np.where(m)[0]; idx = idx[np.argsort(z[idx])]; idx = idx[::2]
zz = z[idx] * 1000; ys, yn = V0[idx, 1] * 1000, V1[idx, 1] * 1000
anchor = [i for i in range(len(idx)) if abs(zz[i] - 1370.6) < 0.3 or abs(zz[i] - 1401.6) < 0.3]
a_, b_ = anchor[0], anchor[-1]
line = lambda Y: Y[a_] + (zz - zz[a_]) / (zz[b_] - zz[a_]) * (Y[b_] - Y[a_])
rs_, rn_ = ys - line(ys), yn - line(yn)
inz = (zz >= zz[a_]) & (zz <= zz[b_])
res['nape_lump'] = dict(midline_rows=[dict(z_mm=float(a), y_start_mm=float(b), y_now_mm=float(c)) for a, b, c in zip(zz, ys, yn)], chord_anchors_z_mm=[float(zz[a_]), float(zz[b_])],
                        bump_over_chord_mm=dict(start=float(rs_[inz].max()), now=float(rn_[inz].max())), crease_under_chord_mm=dict(start=float(rs_[inz].min()), now=float(rn_[inz].min())),
                        strip_vertices=int(strip.sum()), strip_max_move_mm=float(d[strip].max() * 1000), pass_rule='bump over the chord reduced >= 50 %, <= 2 mm moves, <= 40 verts below z 1.40')
gates['NAPE_LUMP'] = bool(rn_[inz].max() <= 0.5 * rs_[inz].max() and d[strip].max() * 1000 <= 2.0 and strip.sum() <= 40)
# ---------------- 5 ADAMS_APPLE_ROUND ----------------
mm_ = (V0[:, 2] > 1.30) & (np.abs(V0[:, 0]) < 0.12)
PLF = {1.4033: (-77.2, -78.5), 1.4112: (-78.5, -79.8), 1.4190: (-81.1, -82.4), 1.4229: (-82.4, -83.7), 1.4307: (-87.6, -88.9), 1.4347: (-88.9, -90.2), 1.4386: (-88.9, -91.5), 1.4425: (-90.2, -91.5), 1.4464: (-88.9, -91.5), 1.4503: (-87.6, -88.9)}
tab = []
for zz_, (pl_, pr_) in PLF.items():
    p_ = (pl_ + pr_) / 2; a_y = plane_section(V0, E, 2, zz_, mm_)[:, 1].min() * 1000; b_y = plane_section(V1, E, 2, zz_, mm_)[:, 1].min() * 1000
    tab.append(dict(z=zz_, plate_avg=p_, start=float(a_y), now=float(b_y), err_start=float(a_y - p_), err_now=float(b_y - p_)))
reg_a = (y < -0.02) & (z < 1.445) & (np.abs(x) < 0.03) & (z > 1.40)
ap = [t for t in tab if t['z'] <= 1.4464]
res['adams_apple'] = dict(front_contour_rows_mm=tab, apple_rows_max_change_mm=float(max(abs(t['now'] - t['start']) for t in ap)), apple_rows_max_err_now_mm=float(max(abs(t['err_now']) for t in ap)), apple_rows_max_err_start_mm=float(max(abs(t['err_start']) for t in ap)),
                          top_row_z1_4503_err_start_now_mm=[tab[-1]['err_start'], tab[-1]['err_now']], lateral_throat_verts_moved_by_the_crease_undo=int((mv & reg_a).sum()), lateral_throat_max_move_mm=float(d[reg_a].max() * 1000),
                          pass_rule='midline front contour at the apple rows z 1.4033-1.4464 within 0.35 mm of Micro1j and not worse vs plate by > 0.3 mm')
gates['ADAMS_APPLE_ROUND'] = bool(res['adams_apple']['apple_rows_max_change_mm'] <= 0.35 and all(abs(t['err_now']) <= abs(t['err_start']) + 0.3 for t in ap))
# ---------------- SIL ----------------
sil = a0['silhouette']; res['silhouette_pct'] = {k: round(v['pct'], 4) for k, v in sil.items()}
gates['SIL_PCT_LE_5'] = bool(max(v['pct'] for v in sil.values()) <= 5.0)
# ---------------- NO_STICKER_VOLUME ----------------
dh = H.copy(); g = np.abs(dh[E[:, 0]] - dh[E[:, 1]]) / np.maximum(np.linalg.norm(V0[E[:, 0]] - V0[E[:, 1]], axis=1) * 1000, 1e-6)
res['no_sticker_volume'] = dict(crest_height_max_mm=float(H.max()), crest_edge_slope_max=float(g.max()), crest_edges_slope_gt_0_5=int((g > 0.5).sum()), topology_identical=bool(am['topology_identical']), new_geometry=0,
                                pass_rule='position-only surface displacement, edge slope of the crest field <= 0.5 mm/mm, max crest <= 3 mm')
gates['NO_STICKER_VOLUME'] = bool(H.max() <= 3.0 and g.max() <= 0.5 and am['topology_identical'])
# ---------------- contours (3/4, profile) ----------------
rows = list(range(470, 596, 6)); qa = C.report_q3(V0, E, rows=rows, verbose=False); qb = C.report_q3(V1, E, rows=rows, verbose=False)
q = {}
for k in ('q3L', 'q3R'):
    for r in rows:
        if r in qa[k] and r in qb[k]: q[f'{k}_{r}'] = dict(start=[float(v) for v in qa[k][r]], now=[float(v) for v in qb[k][r]])
res['q3_contour_vs_plate_mm_rows470-590'] = q
jaw_rows = [r for r in rows if 494 <= r <= 578]
def cnt(Q, lim): return sum(1 for k in ('q3L', 'q3R') for r in jaw_rows if r in Q[k] for v in Q[k][r] if abs(v) <= lim)
res['q3_contour_rows_within_3mm_jaw_cheek_rows'] = dict(start=cnt(qa, 3.0), now=cnt(qb, 3.0), of=2 * 2 * len([r for r in jaw_rows if r in qa['q3L']]))
res['q3_contour_max_change_mm'] = float(max(abs(qb[k][r][i] - qa[k][r][i]) for k in ('q3L', 'q3R') for r in qa[k] if r in qb[k] and r >= 494 and r <= 584 for i in (0, 1)))
res['q3_contour_max_abs_error_jaw_cheek_rows_mm'] = dict(start=float(max(abs(v) for k in ('q3L', 'q3R') for r in jaw_rows if r in qa[k] for v in qa[k][r])), now=float(max(abs(v) for k in ('q3L', 'q3R') for r in jaw_rows if r in qb[k] for v in qb[k][r])))
pa2 = C.report_profile(V0, E, rows=range(96, 262, 6), verbose=False); pb2 = C.report_profile(V1, E, rows=range(96, 262, 6), verbose=False)
res['profile_front_y_max_change_mm'] = float(max(abs(pb2[r][0] - pa2[r][0]) for r in pa2)); res['profile_back_y_max_change_mm'] = float(max(abs(pb2[r][1] - pa2[r][1]) for r in pa2))
# ---------------- OVERALL_LIKENESS (closer) ----------------
better = []; worse = []
better.append(f"neck jaw crease removed (recess vs pre-relief {rs[lat].min():.1f} mm -> {r1[lat].min():.2f} mm)")
better.append(f"jaw edge on the mandible (crest {H.max():.1f} mm)"); better.append(f"cheek relief pulled to the smooth plate-like cheek (RMS {ch['START_micro1j']['rms_mm']:.2f} -> {ch[tag]['rms_mm']:.2f} mm from Micro1h)")
better.append(f"nape C7 bump over chord {rs_[inz].max():.2f} -> {rn_[inz].max():.2f} mm")
c0, c1 = res['q3_contour_rows_within_3mm_jaw_cheek_rows']['start'], res['q3_contour_rows_within_3mm_jaw_cheek_rows']['now']
res['overall_likeness_basis'] = dict(improved=better, silhouette_pct_start=[4.3337, 4.3908], silhouette_pct_now=[round(sil['body_bald_front']['pct'], 4), round(sil['body_bald_back']['pct'], 4)],
                                     q3_rows_within_3mm=[c0, c1], jaw_half_width_err_start_now=[float(hw_start), float(hw_now)])
gates['OVERALL_LIKENESS_closer'] = bool(c1 >= c0 - 1 and hw_now <= hw_start + 0.3 and max(v['pct'] for v in sil.values()) <= 4.3908 and all(gates[k] for k in ('KILL_NECK_JAW_CREASE', 'REAL_MANDIBLE_PROFILE', 'CHEEK_SOFTEN', 'NAPE_LUMP')))
# ---------------- mirror asymmetry, loops, topology density ----------------
mate = np.load(W / 'data/mirror_mate.npy'); asym = []
for i in np.where(mv)[0]:
    j = mate[i]
    if j >= 0: asym.append(np.linalg.norm(D[i] * np.array([-1, 1, 1]) - D[j]))
res['mirror_asymmetry_of_edit_mm'] = dict(mean=float(np.mean(asym) * 1000), p95=float(np.percentile(asym, 95) * 1000), max=float(np.max(asym) * 1000))
res['loops_move'] = {nm: dict(verts=len(ids), max_move_mm=float(d[np.array(ids)].max() * 1000)) for nm, ids in ctx.loops.items()}
regs = {'front_neck_apple_throat': mv & reg_a, 'nape strip (y>0, z<1.40)': strip, 'jaw/ramus/cheek (|x|>0.01, 1.43<z<1.58, y -0.16..0.03)': mv & (np.abs(x) > 0.01) & (z > 1.43) & (z < 1.58) & (y > -0.16) & (y < 0.03)}
res['regions'] = {k: dict(verts=int(v.sum()), max_mm=float(d[v].max() * 1000) if v.any() else 0.0, mean_mm=float(d[v].mean() * 1000) if v.any() else 0.0) for k, v in regs.items()}
res['gates'] = {k: ('PASS' if v else 'FAIL') for k, v in gates.items()}
json.dump(res, open(outp, 'w'), indent=1); print('saved', outp)
print(json.dumps(res['gates'], indent=1))
for k in ('kill_neck_jaw_crease', 'cheek_soften', 'nape_lump'): print(k, json.dumps({a: b for a, b in res[k].items() if a != 'midline_rows'})[:900])
print('real_mandible', json.dumps({a: b for a, b in res['real_mandible'].items() if a not in ('placement_note',)})[:900])
print('jaw half-width err', res['jaw_rows_half_width_max_abs_err_mm'], '| q3 within 3mm', res['q3_contour_rows_within_3mm_jaw_cheek_rows'], '| q3 max err', res['q3_contour_max_abs_error_jaw_cheek_rows_mm'])
