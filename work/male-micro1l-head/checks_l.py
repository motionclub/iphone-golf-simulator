"""Numeric gate checks for MALE_HEAD_Micro1l (numpy only, run with Blender's python3.13 + PYTHONPATH=pylib).
python3.13 checks_l.py <tag> <audit_final.json> <audit_start.json> <selfint_json_or_-> <out.json>"""
import sys, json, hashlib, os, glob
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from l_edit import *
import l_cheek as C, l_jaw as J, l_lips as LP
sys.path.insert(0, str(I1)); import contours as CT
tag = sys.argv[1]; af = json.load(open(sys.argv[2])); a0 = json.load(open(sys.argv[3])); outp = sys.argv[5]
ctx = LCtx(); V0 = ctx.V0; E = ctx.E; n0 = len(V0)
V1 = np.load(W / f'data/V_{tag}.npy'); Vs2 = np.load(W / f'data/V_{tag}_s2_deflate.npy'); Vs3 = np.load(W / f'data/V_{tag}_s3_jaw.npy'); Vs3b = np.load(W / f'data/V_{tag}_s3b_trim.npy'); Vpre = np.load(W / 'data/V_precrest.npy')
D = V1 - V0; d = np.linalg.norm(D, axis=1); mv = d > 0; x, y, z = V0[:, 0], V0[:, 1], V0[:, 2]
res = dict(created='2026-10-02', brief='01c_MALE_HEAD_Micro1l.txt (+ lips / stubble example added by Adnan mid-run)', start_blend_sha='9bfd788a1a2a10bb6c982820e9b2c65889ef7280448f3d65ed39dcd8634d91ba', tag=tag,
           delta_D_sha256=hashlib.sha256(np.ascontiguousarray(D).tobytes()).hexdigest())
gates = {}
# ---------------- ZONE ----------------
Vk = np.load(W / 'data/V_k11_micro1k_installed.npy'); chat9 = np.any(V0[:n0 if len(Vk) > n0 else len(Vk)] != Vk[:n0], axis=1) if False else None
dk = np.zeros(len(V0), bool); dk[:len(Vk)] = np.linalg.norm(V0[:len(Vk)] - Vk, axis=1) > 1e-6          # vertices later moved by the nape/pelvis chat (relative to the installed Micro1k head)
res['zone_audit'] = dict(zone='start z >= 1.40 (head + neck zone); exact mask = vertices with start z >= 1.40 and referenced by a face (73 isolated eye-hole leftovers never move)', moved_total=int(mv.sum()), moved_below_z_1_40=int((mv & ~ctx.zone).sum()),
                         min_z_of_moved=float(z[mv].min()), max_z_of_moved=float(z[mv].max()), max_abs_x_moved_mm=float(np.abs(x[mv]).max() * 1000), y_range_of_moved_mm=[float(y[mv].min() * 1000), float(y[mv].max() * 1000)], max_move_mm=float(d.max() * 1000),
                         hands_moved=int((mv & (np.abs(x) > 0.44) & (z < 1.06)).sum()), arms_moved=int((mv & (np.abs(x) > 0.14) & (z >= 1.06)).sum()), torso_pelvis_legs_feet_moved=int((mv & (z < 1.40)).sum()),
                         nape_border_moved_verts_y_gt_0=int((mv & (y > 0.0)).sum()), moved_overlapping_chat9_nape_set=int((mv & dk).sum()), chat9_nape_set_size=int(dk.sum()),
                         weld_ring_moved=af['weld_ring_moved'], topology_identical=af['topology_identical'], vertex_groups_identical=af['vertex_groups_identical'], tris=af['tris'])
gates['ZONE_OUTSIDE'] = bool(res['zone_audit']['moved_below_z_1_40'] == 0 and res['zone_audit']['hands_moved'] == 0 and res['zone_audit']['arms_moved'] == 0 and res['zone_audit']['torso_pelvis_legs_feet_moved'] == 0)
gates['TOPOLOGY_IDENTICAL'] = bool(af['topology_identical'] and af['vertex_groups_identical'] and af['tris'] == a0['tris'])
# ---------------- LOOP drift ----------------
ld = {}
for nm, ids in ctx.loops.items():
    ids = np.array(ids); ld[nm] = dict(max_mm=float(d[ids].max() * 1000), mean_mm=float(d[ids].mean() * 1000))
res['loop_drift_mm'] = ld
res['loop_drift_summary'] = dict(mouth_loops_max_mm=float(max(ld[k]['max_mm'] for k in ld if 'mouth' in k)), nose_ala_nostril_max_mm=float(max(ld[k]['max_mm'] for k in ld if 'ala' in k or 'nostril' in k)),
                                 eye_lid_max_mm=float(max(ld[k]['max_mm'] for k in ld if 'lid' in k)), ear_helix_concha_attach_max_mm=float(max(ld[k]['max_mm'] for k in ld if ('ear_attach' in k or 'helix' in k or 'concha' in k))),
                                 jaw_ear_loops_max_mm=float(max(ld[k]['max_mm'] for k in ld if 'jaw_ear' in k)))
# ---------------- KILL_NECK_JAW_CREASE (Micro1k definition) ----------------
DJ = np.zeros((len(V0), 3)); DJ[:len(np.load(W / 'data/Djaw_j1.npy'))] = np.load(W / 'data/Djaw_j1.npy'); Va = V0.copy(); Va[:len(np.load(W / 'data/V_a_only.npy'))] = np.load(W / 'data/V_a_only.npy')
fp = np.linalg.norm(DJ, axis=1) > 0.3e-3; lat = fp & (np.abs(x) > 0.04) & (z > 1.455); Na = vertex_normals(Va, ctx.F)
big = feather(ctx, fp.astype(float), 6); big[~ctx.zone] = 0
rel = {}
for nm, V in (('pre_relief_micro1i_state', Va), ('start_now_micro1k', V0), (tag, V1)):
    N = vertex_normals(V, ctx.F); Vlp = ctx.M.taubin(V, big, iters=25, lam=0.5, mu=-0.53); r = ((V - Vlp) * N).sum(1) * 1000
    rel[nm] = dict(min_mm=float(r[lat].min()), p05_mm=float(np.percentile(r[lat], 5)), rms_mm=float(np.sqrt((r[lat] ** 2).mean())))
r1 = ((V1 - Va) * Na).sum(1) * 1000; r0 = ((V0 - Va) * Na).sum(1) * 1000
res['kill_neck_jaw_crease'] = dict(lateral_footprint_verts=int(lat.sum()), now_micro1k_vs_pre_relief_normal_mm=dict(min=float(r0[lat].min()), max=float(r0[lat].max())), micro1l_vs_pre_relief_normal_mm=dict(min=float(r1[lat].min()), max=float(r1[lat].max())),
                                   lowpass_residual_on_lateral_footprint=rel, pass_rule='recess on the old lateral footprint >= -1.5 mm vs the pre-relief surface AND low-pass groove residual not worse than the pre-relief surface by > 0.3 mm (Micro1k definition)')
gates['KILL_NECK_JAW_CREASE'] = bool(r1[lat].min() >= -1.5 and rel[tag]['min_mm'] >= rel['pre_relief_micro1i_state']['min_mm'] - 0.3)
# neck below the jaw untouched: vertices more than 6 mm below the mandible arc on the under-jaw / neck plane move?
Ng = vertex_normals(V0, ctx.F); Nd = J.smooth_normals(ctx, Ng, 8); neck_moved = 0; neck_max = 0.0
sm = np.full(ctx.n, np.inf)
for side in (1, -1):
    s, t, _ = J.euclid_field(ctx, V0, Nd, side, band=0.06, xmin=-0.03)
    sm = np.where(np.isfinite(s) & (np.abs(s) < np.abs(sm)), s, sm)
below = np.isfinite(sm) & (sm < -0.008) & (z > 1.40)
res['neck_below_jaw'] = dict(verts_more_than_8mm_below_arc=int(below.sum()), moved=int((mv & below).sum()), max_move_mm=float(d[below].max() * 1000) if below.any() else 0.0)
# ---------------- JAW crest (geometric + shading) ----------------
Nref = vertex_normals(Vs2, ctx.F); Hc = ((Vs3b - Vs2) * Nref).sum(1) * 1000        # jaw crest + silhouette trim normal displacement (mm)
bins = {}
arc_len = {}
for side in (1, -1):
    s, t, (Parc, jn, Bj) = J.euclid_field(ctx, Vs2, J.smooth_normals(ctx, Nref, 8), side, ctrl=(J.ARC_R2 if os.environ.get('ARC', 'l') == 'r2' else None))
    arcl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(Parc, axis=0), axis=1))]) * 1000; arc_len[side] = float(arcl[-1])
    near = np.where(np.isfinite(s) & (np.abs(s) < 0.004) & (V0[:, 0] * side > -0.004))[0]
    for v in near:
        k = int(arcl[min(jn[v], len(arcl) - 1)] // 10) * 10; bins.setdefault(k, []).append(float(Hc[v]))
tab = [dict(arc_mm_from_chin_midline=k, crest_height_mm_max=float(np.max(v)), crest_height_mm_p50=float(np.median(v))) for k, v in sorted(bins.items())]
res['jaw_crest'] = dict(arc_length_mm_per_side=arc_len, crest_height_along_arc=tab, max_geometric_crest_mm=float(Hc.max()), verts_gt_0_3mm=int((Hc > 0.3).sum()),
                        params='B 3.2 mm (peak, jaw body), B_ang 1.6 at the gonial angle/ramus, chin sides x0.5 (silhouette-safe), sigma up 5 mm (11 mm at the angle/ramus: no pocket), sigma down 4.5 mm, no recess, along 8x-smoothed normals, field smoothed 2x; shading: analytic crest-slope tilt of the custom normals (nboost 0.8 on the full-height crest) - positions untouched',
                        placement='crest on the mesh natural jaw border (n_z = -0.5 iso-line + plate angle/ramus points) extended round the chin; plate tone-edge is stubble pigment 6-12 mm lower (Micro1k note, unchanged)')
Nb = np.load(W / f'data/N_{tag}.npy'); Nrot = updated_normals(ctx, V1)
tilt = np.degrees(np.arccos(np.clip((Nb * Nrot).sum(1), -1, 1))); tilt[ctx.iso] = 0
res['jaw_shading_boost'] = dict(max_extra_tilt_deg=float(tilt.max()), p99_deg=float(np.percentile(tilt[tilt > 0.05], 99)), verts_gt_1deg=int((tilt > 1).sum()))
# front-view jaw line edge contrast (needs preview renders): filled by the caller (jawline json)
# ---------------- front / profile / 3-4 contour vs plate ----------------
pa = CT.report_profile(V0, E, rows=range(200, 270, 4), verbose=False); pb = CT.report_profile(V1, E, rows=range(200, 270, 4), verbose=False)
jr = {str(r): dict(start=[float(v) for v in pa[r][:3]], now=[float(v) for v in pb[r][:3]]) for r in pa if 228 <= r <= 264}
res['jaw_rows_vs_plate_mm_(front_y,back_y,half_width)'] = jr
hw0 = max(abs(pa[r][2]) for r in pa if 228 <= r <= 264); hw1 = max(abs(pb[r][2]) for r in pb if 228 <= r <= 264)
res['jaw_rows_half_width_max_abs_err_mm'] = dict(start=float(hw0), now=float(hw1))
fy = lambda P: max(abs(P[r][0]) for r in P if 228 <= r <= 264); by = lambda P: max(abs(P[r][1]) for r in P if 228 <= r <= 264)
res['profile_jaw_rows_max_abs_err_mm'] = dict(front_y=dict(start=float(fy(pa)), now=float(fy(pb))), back_y=dict(start=float(by(pa)), now=float(by(pb))))
rows = list(range(470, 596, 6)); qa = CT.report_q3(V0, E, rows=rows, verbose=False); qb = CT.report_q3(V1, E, rows=rows, verbose=False)
jaw_rows = [r for r in rows if 494 <= r <= 578 and r in qa['q3L']]
def cnt(Q, lim): return sum(1 for k in ('q3L', 'q3R') for r in jaw_rows for v_ in Q[k][r] if abs(v_) <= lim)
def mabs(Q, rr): return float(np.mean([abs(v_) for k in ('q3L', 'q3R') for r in jaw_rows if r in rr for v_ in Q[k][r]]))
res['q3_contour_jaw_cheek_rows'] = dict(within_3mm=dict(start=cnt(qa, 3.0), now=cnt(qb, 3.0), of=2 * 2 * len(jaw_rows)), mean_abs_err_mm=dict(start=mabs(qa, jaw_rows), now=mabs(qb, jaw_rows)),
                                        cheek_rows_500_560_mean_abs_mm=dict(start=mabs(qa, [r for r in jaw_rows if 500 <= r <= 560]), now=mabs(qb, [r for r in jaw_rows if 500 <= r <= 560])),
                                        jaw_bottom_rows_566_578_mean_abs_mm=dict(start=mabs(qa, [r for r in jaw_rows if 566 <= r <= 578]), now=mabs(qb, [r for r in jaw_rows if 566 <= r <= 578])))
res['q3_contour_vs_plate_mm_rows470-590'] = {f'{k}_{r}': dict(start=[float(v_) for v_ in qa[k][r]], now=[float(v_) for v_ in qb[k][r]]) for k in ('q3L', 'q3R') for r in rows if r in qa[k] and r in qb[k]}
# ---------------- CHEEK ----------------
kcw = dict(z_lo=(1.478, 1.498), z_hi=(1.566, 1.582), x_in=(0.012, 0.026), x_out=(0.074, 0.090), y_max=(-0.020, -0.044), d_mouth=(7.0, 18.0), d_nose=(5.0, 15.0), d_eye=(9.0, 22.0), d_ear=(14.0, 30.0))   # Micro1k's cheek footprint (same region => comparable)
w = C.cheek_weight(ctx, V0, **kcw); reg = w > 0.5; Vh0 = vh0(ctx); Nh = vertex_normals(Vh0, ctx.F); ch = {}
for nm, V in (('start_now_micro1k', V0), (tag, V1)):
    r = ((V - Vh0) * Nh).sum(1)[reg] * 1000
    ch[nm] = dict(rms_mm=float(np.sqrt((r ** 2).mean())), p95_abs_mm=float(np.percentile(np.abs(r), 95)), max_ridge_mm=float(r.max()), max_hollow_mm=float(r.min()))
Nn0 = vertex_normals(V0, ctx.F); disp = ((V1 - V0) * Nn0).sum(1) * 1000
# vertex areas for a volume estimate
Fq = ctx.F; area = np.zeros(ctx.n)
for f in Fq:
    p = V0[f]; a_ = np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0])) / 2 + (np.linalg.norm(np.cross(p[2] - p[0], p[3] - p[0])) / 2 if len(f) == 4 else 0.0)
    for i in f: area[i] += a_ / len(f)
regs = (w > 0.02) & ctx.zone
res['cheek_defat'] = dict(region='face-lateral cheek (Micro1k footprint, weight>0.5 for the deviation metric, >0.02 for displacement stats)', verts_w_gt_0_5=int(reg.sum()), verts_w_gt_0_02=int(regs.sum()),
                          deviation_from_micro1h_smooth_cheek=ch, normal_displacement_vs_now_mm=dict(mean=float(disp[regs].mean()), p05=float(np.percentile(disp[regs], 5)), min=float(disp[regs].min()), max=float(disp[regs].max()),
                          mean_on_core_w_gt_0_5=float(disp[reg].mean())), removed_volume_cm3_both_cheeks=float(-(disp[regs] * 1e-3 * area[regs]).sum() * 1e6), cheek_area_cm2=float(area[regs].sum() * 1e4),
                          method='Taubin low-pass blend (220 its) on the cheek footprint + broad smooth deflation 4.0 mm + buccal hollow 2.5 mm along smoothed normals; protection ramps 8-34 mm mouth / 6-30 nose / 10-30 eye / 14-36 ear / 3-16 mm above the mandible arc; silhouette guard never below 0.35 (no creases)')
# pad prominence = height of the cheek surface above the harmonic membrane spanning its own footprint border (3 rings pinned outside); same footprint/collar before and after
def _dome(V):
    reg_ = (C.cheek_weight(ctx, V0, **kcw) > 1e-3).astype(float); ext = feather(ctx, reg_, 3); pinned = (ext > 0) & (reg_ == 0)
    Vm = C.laplace_membrane(ctx, V, ext, pinned, iters=400); N_ = vertex_normals(V, ctx.F); return ((V - Vm) * N_).sum(1) * 1000
h0_, h1_ = _dome(V0), _dome(V1)
stt = lambda h: dict(mean=float(h[reg].mean()), median=float(np.median(h[reg])), p95=float(np.percentile(h[reg], 95)), max=float(h[reg].max()))
res['cheek_defat']['pad_prominence_over_membrane_mm'] = dict(before=stt(h0_), after=stt(h1_), mean_reduction_pct=float(100 * (1 - h1_[reg].mean() / h0_[reg].mean())), median_reduction_pct=float(100 * (1 - np.median(h1_[reg]) / np.median(h0_[reg]))),
                                                             p95_reduction_pct=float(100 * (1 - np.percentile(h1_[reg], 95) / np.percentile(h0_[reg], 95))), note='proxy for CHEEK_DEFAT_EYE: how far the cheek pad bulges above the surface spanning its own border (smaller = less padded). The Micro1h-deviation metric of Micro1k is NOT used: it rewards staying close to a surface with its own volume, Micro1l deliberately removes volume.')
gates['CHEEK_DEFAT_proxy'] = bool(res['cheek_defat']['pad_prominence_over_membrane_mm']['mean_reduction_pct'] >= 15.0 and res['q3_contour_jaw_cheek_rows']['cheek_rows_500_560_mean_abs_mm']['now'] <= res['q3_contour_jaw_cheek_rows']['cheek_rows_500_560_mean_abs_mm']['start'] + 0.3)
# ---------------- LIPS ----------------
plan = json.load(open(W / f'data/lipplan_{tag}.json')); xs = np.array(plan['x'])
Lm = ctx.loops
def lc(V, nm): return LP.loop_curve(V, Lm[nm])
XP = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
_ci = lambda k: [float(np.interp(x, [q[0] for q in LP.CURVES_R2[k]], [q[1] for q in LP.CURVES_R2[k]])) for x in XP]
lip = dict(plate_front_mm={'x': XP, 'seam': _ci('seam'), 'upper_border': _ci('up'), 'lower_border': _ci('lo')},
           note='plate: curves traced on the front plate with a gridded overlay (r2_analysis/lip_overlay.py): seam = centre of the dark mouth line, upper/lower = visible vermilion borders; 1 plate row = 1.30 mm')
for nm_, V in (('start', V0), (tag, V1)):
    lip[nm_] = {'seam': [float(lc(V, 'LOOP_mouth_seam')[i]) for i in lip['plate_front_mm']['x']], 'upper_loop': [float(lc(V, 'LOOP_mouth_lip_upper')[i]) for i in lip['plate_front_mm']['x']], 'lower_loop': [float(lc(V, 'LOOP_mouth_lip_lower')[i]) for i in lip['plate_front_mm']['x']]}
head = (V0[:, 2] > 1.40) & (np.abs(V0[:, 0]) < 0.12) & (ctx.M.deg > 0); prof = []
for zz in np.arange(1.480, 1.526, 0.002):
    r = rowz(zz); k = int(r); pL = plate_sil_rows('left', [r]); pR = plate_sil_rows('right', [r])
    yl = prof_y(pL[k][0], 'left') * 1000; yr = prof_y(pR[k][0], 'right') * 1000
    a_ = plane_section(V0, E, 2, zz, head)[:, 1].min() * 1000; b_ = plane_section(V1, E, 2, zz, head)[:, 1].min() * 1000
    prof.append((zz * 1000, yl, yr, a_, b_))
Pf = np.array(prof)
lip['profile_silhouette_z1480_1524_mm'] = dict(mean_abs_err_L_R_start=[float(np.abs(Pf[:, 3] - Pf[:, 1]).mean()), float(np.abs(Pf[:, 3] - Pf[:, 2]).mean())], mean_abs_err_L_R_now=[float(np.abs(Pf[:, 4] - Pf[:, 1]).mean()), float(np.abs(Pf[:, 4] - Pf[:, 2]).mean())],
                                               max_abs_err_L_R_start=[float(np.abs(Pf[:, 3] - Pf[:, 1]).max()), float(np.abs(Pf[:, 3] - Pf[:, 2]).max())], max_abs_err_L_R_now=[float(np.abs(Pf[:, 4] - Pf[:, 1]).max()), float(np.abs(Pf[:, 4] - Pf[:, 2]).max())],
                                               upper_lip_rows_1514_1520_mean_err_L_R_start=[float((Pf[(Pf[:, 0] >= 1514) & (Pf[:, 0] <= 1520), 3] - Pf[(Pf[:, 0] >= 1514) & (Pf[:, 0] <= 1520), 1]).mean()), float((Pf[(Pf[:, 0] >= 1514) & (Pf[:, 0] <= 1520), 3] - Pf[(Pf[:, 0] >= 1514) & (Pf[:, 0] <= 1520), 2]).mean())],
                                               upper_lip_rows_1514_1520_mean_err_L_R_now=[float((Pf[(Pf[:, 0] >= 1514) & (Pf[:, 0] <= 1520), 4] - Pf[(Pf[:, 0] >= 1514) & (Pf[:, 0] <= 1520), 1]).mean()), float((Pf[(Pf[:, 0] >= 1514) & (Pf[:, 0] <= 1520), 4] - Pf[(Pf[:, 0] >= 1514) & (Pf[:, 0] <= 1520), 2]).mean())])
lip['plan_curves_mm'] = {k: [round(float(v), 2) for v in np.array(plan[k])[[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]]] for k in ('seam_old', 'seam', 'up_old', 'up', 'lo_old', 'lo')}
lip['vermilion_height_at_center_mm'] = dict(start=dict(upper=float(lip['start']['upper_loop'][0] - lip['start']['seam'][0]), lower=float(lip['start']['seam'][0] - lip['start']['lower_loop'][0])), now=dict(upper=float(lip[tag]['upper_loop'][0] - lip[tag]['seam'][0]), lower=float(lip[tag]['seam'][0] - lip[tag]['lower_loop'][0])), plate=dict(upper=_ci('up')[0] - _ci('seam')[0], lower=_ci('seam')[0] - _ci('lo')[0]))
res['lips'] = lip
# ---------------- Face_M ----------------
res['face_m'] = dict(per_slot=af['face_m_per_slot'], verts=af['face_m_verts'], nonlip_slots_bit_identical=af['face_m_nonlip_slots_identical'], rebuilt_slots=['Face_Lip', 'Face_LipUp', 'Face_Seam'],
                     note='only the lip + mouth-seam paint strips were rebuilt (they must follow the new lip surface); eyes, brows, lids, nostril paint are face-for-face identical; no stubble, no sticker volume (strip lift 0.34 mm + poke-through control)')
# ---------------- SIL / selfint / normals ----------------
res['silhouette_pct'] = {k: round(v['pct'], 4) for k, v in af['silhouette'].items()}; res['silhouette_pct_start'] = {k: round(v['pct'], 4) for k, v in a0['silhouette'].items()}
gates['SIL_PCT_LE_5'] = bool(max(v['pct'] for v in af['silhouette'].values()) <= 5.0)
if sys.argv[4] != '-':
    si = json.load(open(sys.argv[4])); res['self_intersections'] = si; gates['NO_SELF_INTERSECT'] = bool(si['now'] <= si['start'])
res['normals'] = dict(far_from_edit=af['normals_far_from_edit'], edit_region=af['normals_edit_region'], custom_normals_present=af['custom_normals_present'])
gates['NO_NAN'] = bool(not af['nan_or_inf'])
gates['FACE_M_PAINT_ONLY_NONLIP_IDENTICAL'] = bool(af['face_m_nonlip_slots_identical'])

# ---------------- front-view jaw line (visible tonal edge) ----------------
try:
    jl = json.load(open(W / 'proof/jawline_front_edge.json')); xs_ = np.array(jl['x_mm']); selx = (np.abs(xs_) <= 60)
    zp = np.array(jl['rows']['PLATE']['jaw_line_z_mm']); out_ = {}
    for k in ('Micro1k', 'Micro1l_r1', 'Micro1l'):
        zk = np.array(jl['rows'][k]['jaw_line_z_mm']); ck = np.array(jl['rows'][k]['edge_contrast_lum']); cp_ = np.array(jl['rows']['PLATE']['edge_contrast_lum'])
        out_[k] = dict(jaw_line_z_err_vs_plate_mean_mm=float(np.abs(zk[selx] - zp[selx]).mean()), jaw_line_z_err_vs_plate_max_mm=float(np.abs(zk[selx] - zp[selx]).max()), edge_contrast_mean_lum=float(ck[selx].mean()), plate_edge_contrast_mean_lum=float(cp_[selx].mean()),
                       edge_contrast_at_x_0_10_20_30_40_50_60=[round(float(ck[list(xs_).index(v)]), 1) for v in (0, 10, 20, 30, 40, 50, 60)])
    # underside outline (geometry) vs the plate jaw line
    und = {}
    Nn0 = vertex_normals(V0, ctx.F); Nn1 = vertex_normals(V1, ctx.F)
    for nm_, V_, N_ in (('Micro1k', V0, Nn0), ('Micro1l', V1, Nn1)):
        row = []
        for xm in (20, 30, 40, 50, 60):
            m = ctx.zone & (np.abs(np.abs(V_[:, 0]) - xm / 1000) < 0.0025) & (V_[:, 2] > 1.40) & (V_[:, 2] < 1.52) & (V_[:, 1] < -0.02) & (N_[:, 2] < -0.6)
            row.append(round(float(V_[m, 2].min() * 1000), 1) if m.any() else None)
        und[nm_] = row
    res['front_jaw_line'] = dict(per_x=jl, summary_x20_60=out_, underside_outline_min_z_mm_at_x_20_30_40_50_60=und, plate_jaw_line_z_mm_at_x_20_30_40_50_60=[1454.2, 1458.1, 1466.0, 1472.5, 1481.6],
                                 note='visible jaw line = strongest light->dark luminance step per column in the front view (Unity-like soft studio, 4 camera-relative suns). The plate step is stubble pigment (6-12 mm below the natural mandible border); Micro1l keeps the crest ON the jaw (Micro1k rule), so the shading step sits above the plate step at the chin sides (x 20-30: +9..+10 mm) while the underside OUTLINE geometry is within ~3 mm of the plate jaw line. Edge contrast is above the plate (shading boost).')
except Exception as e:
    res['front_jaw_line'] = dict(error=str(e))
# ---------------- install / unity ----------------
try:
    ch_ = json.load(open(W / 'export/install_chain.json'))['chain']
    res['install'] = dict(chain=ch_, installed_over_blend_sha=ch_[-2]['blend_sha256'], new_blend_sha=ch_[-1]['blend_sha256'], installed_over_fbx_sha=ch_[-2]['fbx_sha256'], new_fbx_sha=ch_[-1]['fbx_sha256'],
                          fbx_export_report=json.load(open(os.environ.get('FBX_REPORT', W / 'export/merged_p6g_8a9ad64b.json'))),
                          rollback=dict(r2_body_and_paint='work/male-micro1l-head/baseline/pre_install_p6g_8a9ad64b.blend + pre_install_p6g_4f041bec.fbx (= the r2 install before the paint-only update)', first_micro1l_install='work/male-micro1l-head/baseline/pre_install_p6_0f742186.blend + pre_install_p6_5d2cd893.fbx', pre_micro1l='work/male-micro1l-head/baseline/pre_install_l_9bfd788a.blend + pre_install_l_69428fc8.fbx',
                                        unity_r2_before_paint_update='work/male-micro1l-head/unity_captures_l2r/', unity_first_install='work/male-micro1l-head/baseline/unity_captures_l2/', unity_pre_micro1l='work/male-micro1l-head/baseline/unity_captures_before/'))
    ua = open(os.environ.get('UNITY_AUDIT', W / 'proof/male-form-unity-audit.l.txt')).read().splitlines()
    res['unity'] = dict(saved_prefab_verify=ua[0], mesh_line=ua[1], fbx_sha256=[l for l in ua if l.startswith('FBX_SHA256')][0], source_fbx_sha256=[l for l in ua if l.startswith('SOURCE_FBX_SHA256')][0], prefab_sha256=[l for l in ua if l.startswith('PREFAB_SHA256')][0], import_line=[l for l in ua if l.startswith('globalScale')][0],
                        captures=len([l for l in ua if l.startswith('CAPTURE=')]), lipup_tint_change='HeroBaseMaleFormProof.cs FaceSlots LipUp (.60,.38,.31) -> (.72,.48,.37) (Male_Face_LipUp.mat _BaseColor rewritten by the harness)')
except Exception as e:
    res['install'] = dict(error=str(e))
res['user_additions_mid_run'] = dict(lips='fuller more natural lips from the plate measurements (vermilion heights / cupid bow / upper-lip pad / lower lip) - Body_M mouth loops + rebuilt Face_M lip/seam paint strips',
                                     stubble_example='preview-only light stubble (procedural object-space speckle masked by a per-vertex weight, data/W_stubble_l2.npy); NOT in the mesh/FBX/Unity assets (Body_M has no UVs)')
res['gates'] = gates
json.dump(res, open(outp, 'w'), indent=1, default=float)
print('CHECKS', json.dumps(gates)); print('jawline', json.dumps(res.get('front_jaw_line', {}).get('summary_x20_60')), json.dumps(res.get('front_jaw_line', {}).get('underside_outline_min_z_mm_at_x_20_30_40_50_60'))); print('loops', json.dumps(res['loop_drift_summary'])); print('kill', json.dumps({k: res['kill_neck_jaw_crease'][k] for k in ('micro1l_vs_pre_relief_normal_mm', 'lateral_footprint_verts')}), json.dumps(rel))
print('crest', json.dumps({k: res['jaw_crest'][k] for k in ('max_geometric_crest_mm', 'verts_gt_0_3mm')}), 'tilt', json.dumps(res['jaw_shading_boost']))
print('cheek', json.dumps(res['cheek_defat']['deviation_from_micro1h_smooth_cheek']), json.dumps(res['cheek_defat']['normal_displacement_vs_now_mm']), 'vol_cm3', res['cheek_defat']['removed_volume_cm3_both_cheeks'])
print('q3', json.dumps(res['q3_contour_jaw_cheek_rows'])); print('hw', json.dumps(res['jaw_rows_half_width_max_abs_err_mm']), 'prof', json.dumps(res['profile_jaw_rows_max_abs_err_mm']))
print('lip', json.dumps(lip['vermilion_height_at_center_mm']), json.dumps(lip['profile_silhouette_z1480_1524_mm']))
print('neck', json.dumps(res['neck_below_jaw']), 'zone', json.dumps({k: res['zone_audit'][k] for k in ('moved_total', 'min_z_of_moved', 'nape_border_moved_verts_y_gt_0', 'moved_overlapping_chat9_nape_set')}))
