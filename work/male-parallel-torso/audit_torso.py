"""Zone + integrity + gate audit of a Body_M torso edit.
blender -b --factory-startup --python audit_torso.py -- <final.blend> <out.json> [outdir] [baseline.blend]
PYTHONPATH must contain work/male-micro1i/pylib (Pillow).  Zone/independent categories are defined HERE, not taken from the sculpt script's weights."""
import sys, json, hashlib, pickle
from pathlib import Path
from collections import defaultdict
import numpy as np
import bpy
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); W = R / 'work/male-parallel-torso'
sys.path.insert(0, str(W)); sys.path.insert(0, str(R / 'work/male-micro1i/pylib'))
argv = sys.argv[sys.argv.index('--') + 1:]
final = Path(argv[0]); outj = Path(argv[1]); outdir = Path(argv[2]) if len(argv) > 2 else W / 'r/audit'; outdir.mkdir(parents=True, exist_ok=True)
basebl = Path(argv[3]) if len(argv) > 3 else W / 'baseline/HeroBase_Male_Silhouette.blend'
BASE = np.load(W / 'baseline/mesh.npz')['co']; FB = pickle.load(open(W / 'baseline/faces.pkl', 'rb'))
N0 = len(BASE)
# ---- declared zone (torso): z in [0.77, 1.40), |x| <= xlim(z)
Z_LO, Z_HI = 0.77, 1.40
def xlim(z): return np.where(z < 1.20, 0.205, np.where(z < 1.24, 0.205 + (z - 1.20) / 0.04 * 0.075, 0.28))
def zone(V): return (V[:, 2] >= Z_LO) & (V[:, 2] < Z_HI) & (np.abs(V[:, 0]) <= xlim(V[:, 2]))
def read_scene(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    b = bpy.data.objects['Body_M']; me = b.data
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    polys = [list(p.vertices) for p in me.polygons]
    vg = {g.name: np.zeros(len(V)) for g in b.vertex_groups}
    names = {g.index: g.name for g in b.vertex_groups}
    for v in me.vertices:
        for g in v.groups: vg[names[g.group]][v.index] = g.weight
    fm = bpy.data.objects.get('Face_M'); F_ = None
    if fm:
        fv = np.empty(len(fm.data.vertices) * 3); fm.data.vertices.foreach_get('co', fv); F_ = fv.reshape(-1, 3)
    cams = {o.name: [list(map(float, r)) for r in o.matrix_world] for o in bpy.data.objects if o.type in ('CAMERA', 'EMPTY')}
    return dict(V=V, polys=polys, vg=vg, face=F_, cams=cams, mats=[m.name for m in me.materials], shape_keys=me.shape_keys is not None, mods=[m.type for m in b.modifiers],
                objs=sorted(o.name for o in bpy.data.objects), uv=[u.name for u in me.uv_layers])
B0 = read_scene(basebl); S = read_scene(final)
V1 = S['V']; res = dict(final_blend=str(final), final_blend_sha256=hashlib.sha256(final.read_bytes()).hexdigest(), baseline_blend_sha256=hashlib.sha256(basebl.read_bytes()).hexdigest())
assert len(V1) == N0, (len(V1), N0)
# ---- bit identity / zone containment (independent categories)
same = np.all(V1 == BASE, axis=1); moved = ~same; Z = zone(BASE)
x, y, z = BASE[:, 0], BASE[:, 1], BASE[:, 2]; ax = np.abs(x)
cats = {'head_neck(z>=1.40)': z >= 1.40, 'legs(z<0.77)': z < 0.77, 'feet(z<0.25)': z < 0.25, 'hands_forearms(|x|>0.44,z<1.10)': (ax > 0.44) & (z < 1.10),
        'arms_beyond_shoulder_ball(|x|>0.28)': ax > 0.28, 'arm_gap_side(|x|>0.205,z<1.20)': (ax > 0.205) & (z < 1.20), 'outside_declared_zone': ~Z}
res['zone'] = dict(definition='z in [0.77,1.40) and |x| <= xlim(z): 0.205 below z=1.20, ramps to 0.28 at z=1.24 (shoulder ball), 0.28 above', verts_in_zone=int(Z.sum()), verts_total=N0,
                   verts_moved=int(moved.sum()), verts_moved_inside_zone=int((moved & Z).sum()), verts_moved_outside_zone=int((moved & ~Z).sum()))
res['moved_by_category'] = {k: int((moved & m).sum()) for k, m in cats.items()}
res['category_vertex_counts'] = {k: int(m.sum()) for k, m in cats.items()}
d = np.linalg.norm(V1 - BASE, axis=1); res['max_displacement_mm'] = float(d.max() * 1000); res['mean_displacement_moved_mm'] = float(d[moved].mean() * 1000)
res['max_displacement_xz_mm'] = float(np.linalg.norm((V1 - BASE)[:, [0, 2]], axis=1).max() * 1000)
res['max_abs_dx_mm'] = float(np.abs(V1[:, 0] - BASE[:, 0]).max() * 1000); res['max_abs_dz_mm'] = float(np.abs(V1[:, 2] - BASE[:, 2]).max() * 1000)
# ---- other data identical
res['topology_identical'] = bool(S['polys'] == FB == B0['polys'])
res['tris'] = int(sum(len(p) - 2 for p in S['polys'])); res['tris_baseline'] = int(sum(len(p) - 2 for p in FB)); res['verts'] = len(V1)
res['vertex_groups_identical'] = bool(set(S['vg']) == set(B0['vg']) and all(np.array_equal(S['vg'][k], B0['vg'][k]) for k in S['vg']))
res['face_m_bit_identical'] = bool(np.array_equal(S['face'], B0['face'])) if S['face'] is not None else None
res['cameras_empties_identical'] = bool(S['cams'] == B0['cams']); res['objects'] = S['objs']; res['objects_identical'] = bool(S['objs'] == B0['objs'])
res['materials'] = S['mats']; res['materials_identical'] = bool(S['mats'] == B0['mats']); res['shape_keys'] = S['shape_keys']; res['modifiers'] = S['mods']
res['height_m'] = float(V1[:, 2].max() - V1[:, 2].min()); res['height_m_baseline'] = float(BASE[:, 2].max() - BASE[:, 2].min())
res['nan_or_inf'] = bool(~np.isfinite(V1).all()); res['bounds_min'] = V1.min(0).tolist(); res['bounds_max'] = V1.max(0).tolist()
# ---- mesh integrity
ec = defaultdict(list)
for i, f in enumerate(FB):
    for k in range(len(f)):
        a, b = f[k], f[(k + 1) % len(f)]; ec[(min(a, b), max(a, b))].append(i)
res['boundary_edges'] = sum(1 for v in ec.values() if len(v) == 1); res['nonmanifold_edges'] = sum(1 for v in ec.values() if len(v) > 2); res['boundary_edges_baseline'] = res['boundary_edges']
def fnorm(V):
    n = np.zeros((len(FB), 3)); a = np.zeros(len(FB))
    for i, f in enumerate(FB):
        p = V[f]; c = np.zeros(3)
        for k in range(1, len(f) - 1): c += np.cross(p[k] - p[0], p[k + 1] - p[0])
        a[i] = 0.5 * np.linalg.norm(c); n[i] = c / max(np.linalg.norm(c), 1e-18)
    return n, a
n0, a0 = fnorm(BASE); n1, a1 = fnorm(V1)
fz = np.array([Z[f].any() for f in FB]); dot = (n0 * n1).sum(1)
res['face_flips_dot<0'] = int((dot < 0).sum()); res['faces_turned_over_60deg'] = int((dot < 0.5).sum()); res['min_face_dot_vs_baseline'] = float(dot.min())
res['zero_area_faces'] = int((a1 < 1e-9).sum()); res['min_face_area_mm2_zone'] = float(a1[fz].min() * 1e6); res['min_face_area_mm2_zone_baseline'] = float(a0[fz].min() * 1e6)
E = np.array(sorted(ec.keys())); L0 = np.linalg.norm(BASE[E[:, 0]] - BASE[E[:, 1]], axis=1); L1 = np.linalg.norm(V1[E[:, 0]] - V1[E[:, 1]], axis=1)
ez = Z[E[:, 0]] | Z[E[:, 1]]; ratio = L1[ez] / np.maximum(L0[ez], 1e-9)
res['edge_ratio_zone'] = dict(min=float(ratio.min()), p1=float(np.percentile(ratio, 1)), p99=float(np.percentile(ratio, 99)), max=float(ratio.max()), over_1p6=int((ratio > 1.6).sum()), under_0p6=int((ratio < 0.6).sum()), n=int(ez.sum()))
res['edge_len_mm_zone'] = dict(base_mean=float(L0[ez].mean() * 1000), base_max=float(L0[ez].max() * 1000), final_mean=float(L1[ez].mean() * 1000), final_max=float(L1[ez].max() * 1000))
def dihedrals(V, nrm):
    out = []
    for e, fs in ec.items():
        if len(fs) == 2: out.append((float(np.degrees(np.arccos(np.clip(nrm[fs[0]] @ nrm[fs[1]], -1, 1)))), e))
    return out
D0 = dihedrals(BASE, n0); D1 = dihedrals(V1, n1)
def dstat(D):
    zz = np.array([a for a, e in D if Z[e[0]] and Z[e[1]]]); pel = np.array([a for a, e in D if Z[e[0]] and Z[e[1]] and 0.77 <= 0.5 * (BASE[e[0], 2] + BASE[e[1], 2]) <= 0.90])
    return dict(zone_edges=int(len(zz)), over_40=int((zz > 40).sum()), over_55=int((zz > 55).sum()), over_80=int((zz > 80).sum()), max=float(zz.max()), p99=float(np.percentile(zz, 99)), pelvis_band_over_55=int((pel > 55).sum()), pelvis_band_max=float(pel.max()), pelvis_band_p99=float(np.percentile(pel, 99)))
res['dihedral_zone_baseline'] = dstat(D0); res['dihedral_zone_final'] = dstat(D1)
# vertex-normal deviation (area-weighted from faces)
def vnorm(V, nrm, ar):
    n = np.zeros_like(V)
    for i, f in enumerate(FB):
        w = nrm[i] * ar[i]
        for v in f: n[v] += w
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)
vn0 = vnorm(BASE, n0, a0); vn1 = vnorm(V1, n1, a1); ang = np.degrees(np.arccos(np.clip((vn0 * vn1).sum(1), -1, 1)))
res['vertex_normal_change_deg_zone'] = dict(mean=float(ang[Z].mean()), p99=float(np.percentile(ang[Z], 99)), max=float(ang[Z].max()))
# border continuity: zone verts adjacent to non-zone verts
nbr = defaultdict(set)
for a, b in ec: nbr[a].add(b); nbr[b].add(a)
border = [i for i in np.where(Z)[0] if any(not Z[j] for j in nbr[i])]
bd_d = np.array([d[i] for i in border]) * 1000 if border else np.zeros(1)
res['zone_border'] = dict(border_verts=len(border), max_disp_mm=float(bd_d.max()), p95_disp_mm=float(np.percentile(bd_d, 95)))
# split by border segment
seg = defaultdict(float)
for i in border:
    nm = 'bottom_legs' if z[i] < 0.80 else ('top_neck' if z[i] > 1.37 else 'side_arm')
    seg[nm] = max(seg[nm], float(d[i] * 1000))
res['zone_border_max_disp_mm_by_segment'] = dict(seg)
vol = 0.0
for p in S['polys']:
    for k in range(1, len(p) - 1): vol += float(np.dot(V1[p[0]], np.cross(V1[p[k]], V1[p[k + 1]]))) / 6.0
vol0 = 0.0
for p in FB:
    for k in range(1, len(p) - 1): vol0 += float(np.dot(BASE[p[0]], np.cross(BASE[p[k]], BASE[p[k + 1]]))) / 6.0
res['signed_volume_m3'] = vol; res['signed_volume_m3_baseline'] = vol0; res['volume_change_L'] = (vol - vol0) * 1000
# ---- silhouette gate + plate profile (renders from the blend's own locked cameras)
sc = bpy.context.scene
sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x = 1280; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
fm = bpy.data.objects.get('Face_M')
import silgate, prof
sil = {}
for tag, showf in (('body', False), ('withface', True)):
    if fm: fm.hide_render = not showf
    d_ = outdir / f'sil_{tag}'; d_.mkdir(exist_ok=True)
    for v in ('bald_front', 'bald_back', 'left', 'right'):
        sc.camera = bpy.data.objects['Locked_' + v]; sc.render.filepath = str((d_ / f'{v}.png').resolve()); bpy.ops.render.render(write_still=True)
    sil[tag] = {k: round(v_['pct'], 4) for k, v_ in silgate.run(d_).items()}
res['silhouette_pct'] = sil
res['silhouette_pct_baseline_body'] = {k: round(v_['pct'], 4) for k, v_ in silgate.run(W / 'r/sil_base').items()}
P1 = prof.profile(str(outdir / 'sil_body')); P0 = prof.profile(str(W / 'r/sil_base'))
def outline(P):
    out = {}
    for v in ('bald_front', 'bald_back'):
        dl = []; dr = []
        for zk in sorted(P[v]['plate'], key=float):
            zf = float(zk)
            if zf < 0.80 or zf > 1.36: continue
            a, b = P[v]['plate'][zk], P[v]['mesh'][zk]
            if a and b and abs(b[0] - a[0]) < 40 and abs(b[1] - a[1]) < 40: dl.append(b[0] - a[0]); dr.append(b[1] - a[1])
        dl, dr = np.array(dl), np.array(dr)
        out[v] = dict(rows=len(dl), max_abs_mm=float(max(np.abs(dl).max(), np.abs(dr).max())), mean_abs_mm=float(np.mean(np.abs(np.concatenate([dl, dr])))), rows_over_1px=int((np.abs(dl) > 3.0).sum() + (np.abs(dr) > 3.0).sum()))
    return out
res['torso_outline_vs_plate_mm'] = dict(baseline=outline(P0), final=outline(P1))
def depth(P):
    zs, ds = [], []
    for zk in sorted(P['left']['plate'], key=float):
        zf = float(zk)
        if zf < 0.92 or zf > 1.30: continue
        dl = []
        for v in ('left', 'right'):
            a, b = P[v]['plate'][zk], P[v]['mesh'][zk]
            if a and b: dl.append((a[1] - a[0]) - (b[1] - b[0]))
        zs.append(zf); ds.append(float(np.mean(dl)))
    ds = np.array(ds); return dict(rows=len(ds), mean_deficit_mm=float(ds.mean()), rms_mm=float(np.sqrt((ds ** 2).mean())), max_abs_mm=float(np.abs(ds).max()))
res['torso_depth_vs_side_plates_mm_z0.92_1.30'] = dict(baseline=depth(P0), final=depth(P1))
outj.write_text(json.dumps(res, indent=1))
print('AUDIT_TORSO_DONE')
for k in ('zone', 'moved_by_category', 'topology_identical', 'tris', 'vertex_groups_identical', 'face_m_bit_identical', 'face_flips_dot<0', 'silhouette_pct', 'torso_depth_vs_side_plates_mm_z0.92_1.30'): print(k, json.dumps(res[k]))
