"""Numeric checks for MALE_HEAD_RESULTS / male-micro1j-checks.json (numpy only).  python3.13 checks_j.py <D.npy> <audit_merged.json> <audit_on_start.json> <out.json>"""
import sys, json, hashlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head')
from j_edit import *
import contours as C
D = np.load(sys.argv[1]); am = json.load(open(sys.argv[2])); a0 = json.load(open(sys.argv[3])); outp = sys.argv[4]
ctx = Ctx(); V0 = ctx.V0; V1 = V0 + D; E = ctx.E
res = dict(created='2026-10-01', brief='01_MALE_HEAD_Micro1j.txt', scope='male head+neck zone z>=1.40 only (position-only edits on the Micro1i topology)')
res['hashes'] = dict(start_blend_68de53ca='68de53ca729ff04d366377e6df302952082abfb8e5621c524d39468c39f630cf', artdir_base_at_install_0dd37baf='0dd37baf20fcc3524ee1d8557b88b87ce0d2d3782d13c5eb15a8df9fe38802b7',
                      artdir_base_fbx_614cccf3='614cccf33f8401632b78605c5f81abc911077dfd9d0c68d5b6e4d66a0722cd6d', delta_D_sha256=hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest())
mv = np.linalg.norm(D, axis=1) > 0; d = np.linalg.norm(D, axis=1)
res['zone_audit'] = dict(zone='start z >= 1.40', moved_total_numeric=int(mv.sum()), moved_outside_zone=int((mv & ~ctx.zone).sum()), moved_below_z_1_40=int((mv & (V0[:, 2] < 1.40)).sum()),
                         min_z_of_moved=float(V0[mv, 2].min()), max_move_mm=float(d.max() * 1000), hands_moved=int((mv & (np.abs(V0[:, 0]) > 0.44) & (V0[:, 2] < 1.06)).sum()))
res['audit_vs_artdir_base_0dd37baf'] = {k: am[k] for k in ('moved_total', 'moved_outside_zone_z_lt_1_40', 'min_z_of_moved_verts', 'hands_moved', 'arms_moved', 'torso_pelvis_legs_feet_moved', 'topology_identical', 'tris', 'vertex_groups_identical', 'face_m_identical', 'boundary_edges', 'nonmanifold_edges', 'normals_far_from_edit', 'normals_edit_region', 'silhouette')}
res['audit_vs_start_68de53ca_(my_edit_alone)'] = {k: a0[k] for k in ('moved_total', 'moved_outside_zone_z_lt_1_40', 'min_z_of_moved_verts', 'hands_moved', 'tris', 'silhouette', 'height_m')}
# regions of the edit
x, y, z = V0[:, 0], V0[:, 1], V0[:, 2]
reg = {'front_neck_apple_throat (y<-0.02, z<1.4545)': mv & (y < -0.02) & (z < 1.4545) & (np.abs(x) < 0.06),
       'nape (y>0)': mv & (y > 0.0), 'jaw/ramus (|x|>0.01, z 1.43..1.545, y -0.16..0.03)': mv & (np.abs(x) > 0.01) & (z > 1.43) & (z < 1.545) & (y > -0.16) & (y < 0.03)}
res['regions'] = {k: dict(verts=int(m.sum()), max_mm=float(d[m].max() * 1000) if m.any() else 0, mean_mm=float(d[m].mean() * 1000) if m.any() else 0) for k, m in reg.items()}
# loops
lp = {}
for nm, ids in ctx.loops.items():
    ids = np.array(ids); lp[nm] = dict(verts=int(len(ids)), max_move_mm=float(d[ids].max() * 1000))
res['loops_move'] = lp
# symmetry of the edit
mate = np.load(W / 'data/mirror_mate.npy'); asym = []
for i in np.where(mv)[0]:
    j = mate[i]
    if j >= 0: asym.append(np.linalg.norm(D[i] * np.array([-1, 1, 1]) - D[j]))
res['mirror_asymmetry_mm'] = dict(mean=float(np.mean(asym) * 1000), p95=float(np.percentile(asym, 95) * 1000), max=float(np.max(asym) * 1000))
# topology density in the face zone (unchanged topology, new positions)
n = len(V1); head = (V1[:, 2] > 1.43) & (np.abs(V1[:, 0]) < 0.14); sel = head[E[:, 0]] & head[E[:, 1]]
el = np.linalg.norm(V1[E[sel, 0]] - V1[E[sel, 1]], axis=1) * 1000; zc = 0.5 * (V1[E[sel, 0], 2] + V1[E[sel, 1], 2]); yc = 0.5 * (V1[E[sel, 0], 1] + V1[E[sel, 1], 1]); fz = (zc > 1.47) & (zc < 1.63) & (yc < -0.02)
res['head_edge_mm'] = dict(mean=float(el.mean()), median=float(np.median(el)), n=int(len(el))); res['face_zone_edge_mm'] = dict(mean=float(el[fz].mean()), median=float(np.median(el[fz])), n=int(fz.sum()))
# plate fits: neck front contour (profile plates avg), nape contour (silhouette incl. shirt), jaw rows
m = (V0[:, 2] > 1.30) & (np.abs(V0[:, 0]) < 0.12)
PLF = {1.4033: (-77.2, -78.5), 1.4112: (-78.5, -79.8), 1.4190: (-81.1, -82.4), 1.4229: (-82.4, -83.7), 1.4307: (-87.6, -88.9), 1.4347: (-88.9, -90.2), 1.4386: (-88.9, -91.5), 1.4425: (-90.2, -91.5), 1.4464: (-88.9, -91.5), 1.4503: (-87.6, -88.9)}
tab = []
for zz, (pl, pr) in PLF.items():
    a = plane_section(V0, E, 2, zz, m)[:, 1].min() * 1000; b = plane_section(V1, E, 2, zz, m)[:, 1].min() * 1000; tab.append(dict(z=zz, plate_avg=(pl + pr) / 2, start=float(a), now=float(b), err_start=float(a - (pl + pr) / 2), err_now=float(b - (pl + pr) / 2)))
res['apple_throat_front_contour_mm'] = tab
PLB = {1.4033: (83.95), 1.4112: (78.05), 1.4190: (71.5), 1.4268: (65.65), 1.4347: (59.15), 1.4425: (53.95), 1.4503: (46.7), 1.4581: (44.1), 1.4660: (41.5), 1.4777: (38.9), 1.4933: (37.6), 1.5012: (38.25)}
tb = []
for zz, pl in PLB.items():
    a = plane_section(V0, E, 2, zz, m)[:, 1].max() * 1000; b = plane_section(V1, E, 2, zz, m)[:, 1].max() * 1000; tb.append(dict(z=zz, plate_avg=pl, start=float(a), now=float(b), err_start=float(a - pl), err_now=float(b - pl)))
res['nape_back_contour_mm'] = tb
rows = list(range(500, 600, 6)); qa = C.report_q3(V0, E, rows=rows, verbose=False); qb = C.report_q3(V1, E, rows=rows, verbose=False)
res['q3_contour_max_change_mm'] = float(max(abs(qb[k][r][i] - qa[k][r][i]) for k in ('q3L', 'q3R') for r in qa[k] if r in qb[k] for i in (0, 1)))
pa = C.report_profile(V0, E, rows=range(200, 266, 4), verbose=False); pb = C.report_profile(V1, E, rows=range(200, 266, 4), verbose=False)
res['profile_front_y_max_change_mm'] = float(max(abs(pb[r][0] - pa[r][0]) for r in pa)); res['front_half_width_jaw_rows_err_mm'] = {str(r): [float(pa[r][2]), float(pb[r][2])] for r in pa if 232 <= r <= 264}
res['profile_back_y_jaw_rows_err_mm'] = {str(r): [float(pa[r][1]), float(pb[r][1])] for r in pa if 232 <= r <= 264}
# knee/hump numbers: back midline slope before/after (zone rows) and the locked rows
cols = np.where((np.abs(V0[:, 0]) < 0.0075) & (V0[:, 1] > 0) & (V0[:, 2] > 1.34) & (V0[:, 2] < 1.52))[0]; cols = cols[np.argsort(V0[cols, 2])]
res['nape_midline_rows'] = [dict(z_mm=float(V0[i, 2] * 1000), y_start_mm=float(V0[i, 1] * 1000), y_now_mm=float(V1[i, 1] * 1000)) for i in cols[::2]]
json.dump(res, open(outp, 'w'), indent=1); print('saved', outp)
for k in ('zone_audit', 'regions', 'mirror_asymmetry_mm', 'head_edge_mm', 'face_zone_edge_mm', 'q3_contour_max_change_mm', 'profile_front_y_max_change_mm'): print(k, json.dumps(res[k])[:400])
