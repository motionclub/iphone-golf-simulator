"""End-to-end build: graded head -> Phi -> eye carve -> assemble body -> blend with Body_M + Face_M -> previews.
blender -b --factory-startup --python run_final.py -- <tag> [save=0|1]"""
import sys, pickle, time, json, importlib, hashlib
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1e')
import h1lib as H, loft as L, proxy as PX, sculpt as S, stage2 as S2, topo as T, finalize as FZ, faceparts as FP, h1render as HR, wire
for m in (H, L, PX, S, S2, T, FZ, FP, HR): importlib.reload(m)
argv = sys.argv[sys.argv.index('--') + 1:]
tag = argv[0]; save = len(argv) > 1 and argv[1] == '1'
theta_file = argv[5] if len(argv) > 5 else None
if theta_file:
    S.apply_theta(json.load(open(theta_file)))
    print('theta applied from', theta_file)
maxlev = int(argv[2]) if len(argv) > 2 else 2
eps_mm = float(argv[3]) if len(argv) > 3 else 0.45
errlev = int(argv[4]) if len(argv) > 4 else 2
t0 = time.time()
V = np.load(H.W / 'data/V_micro1f.npy'); F = pickle.load(open(H.W / 'data/F.pkl', 'rb'))
Vcc, Fcc = PX.build_proxy(3)
phi = S2.Phi(); phi.attach_cc(Vcc, Fcc)
feat2 = float(argv[6]) * 1e-3 if len(argv) > 6 else 0.0022
ear3 = len(argv) > 7 and argv[7] == '1'
Vn, Fn, info = S2.build_final(V, F, phi, eps=eps_mm * 1e-3, max_level=maxlev, err_max_level=errlev, feat_dist=(0.0045, feat2), ear_level3=ear3, verbose=False)
P1 = phi.stage1(Vn)
P1c, loops = FZ.carve_all(P1, Fn, verbose=True)
P2, _ = S.stage2(P1c, Fn, S.PRM, phi.parts)
P3, F3, einfo = FZ.carve_eyes(P2, Fn)
loops['lid_margin_L'] = einfo[-1]['loop']; loops['lid_margin_R'] = einfo[1]['loop']


def taubin_zone(P, F, sel, iters=4, lam=0.5, mu=-0.53):
    n = len(P); adj = FZ.edge_graph(F, n)
    nb = {int(i): np.array(list(adj[i].keys()), int) for i in np.where(sel)[0]}
    P = P.copy()
    for it in range(iters):
        for step in (lam, mu):
            new = P.copy()
            for i, nn in nb.items():
                if len(nn): new[i] = P[i] + step * (P[nn].mean(axis=0) - P[i])
            P = new
    return P


ear_iters = int(argv[8]) if len(argv) > 8 else 0
if ear_iters > 0:
    P3 = taubin_zone(P3, F3, S2.ear_footprint(P3, 0.002), iters=ear_iters)
    print('ear Taubin smoothing, iterations', ear_iters)
face_iters = int(argv[9]) if len(argv) > 9 else 0
if face_iters > 0:
    zone = (np.abs(P3[:, 0]) < 0.060) & (P3[:, 2] > 1.474) & (P3[:, 2] < 1.600) & (P3[:, 1] < -0.060)
    # keep the eye margin / lid wall untouched (4 mm around the opening)
    zone &= S.poly_dist(np.abs(P3[:, 0]), P3[:, 2], S.smooth_poly(S.eye_poly())) > 0.004
    P3 = taubin_zone(P3, F3, zone, iters=face_iters)
    print('face Taubin smoothing, iterations', face_iters, 'verts', int(zone.sum()))
fidx = T.region_faces(V, F)
V_all, F_all, ring = S2.assemble(V, F, fidx, info['used'], Vn, F3, P3)
tris = sum(len(f) - 2 for f in F_all)
print('build secs %.1f  head tris %d  full tris %d' % (time.time() - t0, sum(len(f) - 2 for f in F3), tris))
np.save(H.W / f'data/Vfinal_{tag}.npy', V_all)
nu_ = len(info['used']); used_ = np.array(info['used'])
glob = lambda k: int(used_[k]) if k < nu_ else len(V) + (k - nu_)
pickle.dump({k: [glob(int(i)) for i in v] for k, v in loops.items()}, open(H.W / f'data/loops_{tag}.pkl', 'wb')); pickle.dump([list(map(int, f)) for f in F_all], open(H.W / f'data/Ffinal_{tag}.pkl', 'wb'))

# ---------------- blend: baseline scene, Body_M geometry replaced, Face_M rebuilt
bpy.ops.wm.open_mainfile(filepath=str(H.W / 'baseline/HeroBase_Male_Silhouette.blend'))
body = bpy.data.objects['Body_M']; me = body.data
old_face = bpy.data.objects.get('Face_M')
if old_face:
    bpy.data.objects.remove(old_face, do_unlink=True)
me.clear_geometry()
n = len(V_all)
me.vertices.add(n); me.vertices.foreach_set('co', V_all.astype(np.float32).ravel())
lens = np.array([len(f) for f in F_all], np.int64)
me.loops.add(int(lens.sum())); me.polygons.add(len(F_all))
me.loops.foreach_set('vertex_index', np.concatenate([np.asarray(f, np.int64) for f in F_all]))
me.polygons.foreach_set('loop_start', np.concatenate([[0], np.cumsum(lens)[:-1]]))
me.polygons.foreach_set('loop_total', lens)
me.update(calc_edges=True)
if 'sharp_face' not in me.attributes:
    me.attributes.new('sharp_face', 'BOOLEAN', 'FACE')
me.attributes['sharp_face'].data.foreach_set('value', np.zeros(len(F_all), bool))
me.update()
# ---- smoothed shading normals in the head region (geometry untouched); body keeps Blender's own normals
nrm = np.empty(n * 3, np.float64); me.vertex_normals.foreach_get('vector', nrm); nrm = nrm.reshape(-1, 3)
adjn = FZ.edge_graph(F_all, n)
headv = (V_all[:, 2] > 1.43) & (np.abs(V_all[:, 0]) < 0.14)
hv = np.where(headv)[0]
ring_set = set(int(i) for i in ring)
for it in range(3):
    new = nrm.copy()
    for v in hv:
        if v in ring_set:
            continue
        nb = list(adjn[v])
        m_ = nrm[nb].mean(axis=0)
        t = 0.5 * nrm[v] + 0.5 * m_
        new[v] = t / (np.linalg.norm(t) + 1e-12)
    nrm = new
me.normals_split_custom_set_from_vertices([tuple(x) for x in nrm])
me.update()
for name_, idxs in {k: [glob(int(i)) for i in v] for k, v in loops.items()}.items():
    vg = body.vertex_groups.new(name='LOOP_' + name_)
    vg.add(idxs, 1.0, 'REPLACE')
face_o, parts = FP.build_face_m(P3, F3, margin={-1: loops['lid_margin_L'], 1: loops['lid_margin_R']})
face_o.parent = None
print('Face_M verts', len(face_o.data.vertices), 'tris', sum(len(p.vertices) - 2 for p in face_o.data.polygons))
if save:
    out = H.W / f'final/HeroBase_Male_Silhouette_{tag}.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print('saved', out)
# ---------------- previews
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body.hide_render = False
s = bpy.context.scene
body.data.materials.clear(); body.data.materials.append(H.skin_material())
# sclera brighter in preview (emission) so the eyes read as in the plate
m_sc = bpy.data.materials.get('Face_Sclera')
if m_sc:
    b = m_sc.node_tree.nodes['Principled BSDF']
    try:
        b.inputs['Emission Color'].default_value = (0.5, 0.49, 0.47, 1); b.inputs['Emission Strength'].default_value = 0.35
    except Exception: pass
HR.setup(transparent=True)
out = HR.render_set(tag)
H.setup_eevee(res=(900, 900))
extra = {
    'head_front': ((0, -0.05, 1.58), 0, 0, 0.30, (900, 900)), 'head_q3L': ((0, -0.05, 1.58), 32.5, 0, 0.30, (900, 900)),
    'head_q3R': ((0, -0.05, 1.58), 30.0, 0, 0.30, (900, 900)), 'head_side': ((0, -0.05, 1.58), 90, 0, 0.30, (900, 900)),
    'face_front': ((0, -0.1, 1.55), 0, 0, 0.16, (900, 900)), 'face_q3L': ((0, -0.1, 1.55), 32.5, 0, 0.16, (900, 900)),
    'face_q3R': ((0, -0.1, 1.55), 30.0, 0, 0.16, (900, 900)), 'face_side': ((0, -0.1, 1.55), 90, 0, 0.16, (900, 900)),
    'eye_front': ((0.036, -0.1, 1.585), 0, 0, 0.07, (900, 900)), 'ear_side': ((0.09, -0.0115, 1.5628), 90, 0, 0.11, (900, 900)),
    'ear_back': ((0.09, -0.0115, 1.5628), 150, 8, 0.12, (900, 900)), 'ear_front': ((0.09, -0.0115, 1.5628), 0, 0, 0.11, (900, 900)),
}
for nme, (t, az, el, sc, res) in extra.items():
    H.shot(out / f'{nme}.png', t, az, el, sc, res)
print('rendered secs %.1f' % (time.time() - t0))
