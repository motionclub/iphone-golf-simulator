"""MicroF3 verification: F3 vs the staged F1 blend (the build base) and F2 (previous delivery).  python3 verify_f3.py -> data/verify_f3.json + printed gate lines
needs data/dump/F1.npz, F2.npz, F3.npz (tools/dump_full.py) and the *_Body_F.json dumps."""
import sys, json, collections
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np
import fl, meshlib as ml
D = fl.W / 'data/dump'
a = np.load(D / 'F1.npz'); b = np.load(D / 'F3.npz'); c2 = np.load(D / 'F2.npz')
res = {}; ok = True


def gate(name, passed, detail=''):
    global ok
    ok &= bool(passed); res[name] = dict(passed=bool(passed), detail=detail)
    print(('GATE %-36s %s  %s' % (name, 'PASS' if passed else 'FAIL', detail)).rstrip())


# ------------------------------------------------------------------------------------------------ topology / structure
nm = 'Body_F'
same_f = np.array_equal(a[nm + '_F'], b[nm + '_F']) and np.array_equal(a[nm + '_Foff'], b[nm + '_Foff'])
same_m = np.array_equal(a[nm + '_MI'], b[nm + '_MI']); same_s = np.array_equal(a[nm + '_smooth'], b[nm + '_smooth'])
uvk = [k for k in a.files if k.startswith(nm + '_uv_')]
same_uv = all(np.array_equal(a[k], b[k]) for k in uvk)
gate('TOPOLOGY Body_F', same_f and same_m and same_s and same_uv, f'faces+offsets {same_f}, material idx {same_m}, smooth flags {same_s}, UVs {same_uv} ({len(uvk)} layers): positions + shading normals only')
ja = json.load(open(D / 'F1_Body_F.json')); jb = json.load(open(D / 'F3_Body_F.json'))
gate('VERTEX_GROUPS (21 LOOP_*)', ja['groups'] == jb['groups'] and len(jb['groups']) == 21, f"{len(jb['groups'])} groups, membership+weights identical: {ja['groups'] == jb['groups']}")
gate('MATERIALS/OBJECTS', ja['materials'] == jb['materials'] and json.load(open(D / 'F1_objects.json')) == json.load(open(D / 'F3_objects.json')) and ja['n_edges'] == jb['n_edges'],
     f"slots {jb['materials']}, edges {jb['n_edges']}; Body_F custom normals F1 {ja['has_custom_normals']} -> F3 {jb['has_custom_normals']} (intended: analytic jaw normals)")
# Face_F: non-lip faces identical (geometry matched by centroid, vertex order is not kept by the bmesh rebuild); lip faces replaced
fa, fb = json.load(open(D / 'F1_Face_F.json')), json.load(open(D / 'F3_Face_F.json'))
gate('MATERIALS Face_F', fa['materials'] == fb['materials'], f"{len(fb['materials'])} slots unchanged")
LIP = ('Face_Lip', 'Face_LipUp', 'Face_Seam')
def face_centroids(npz, mats):
    V = npz['Face_F_V']; F = npz['Face_F_F']; off = npz['Face_F_Foff']; mi = npz['Face_F_MI']
    out = {}
    for k, m in enumerate(mats):
        cs = np.array([V[F[off[i]:off[i + 1]]].mean(0) for i in np.where(mi == k)[0]]) if (mi == k).any() else np.zeros((0, 3))
        out[m] = cs
    return out
ca, cb = face_centroids(a, fa['materials']), face_centroids(b, fb['materials'])
worst = 0.0; cnt_ok = True
for m in fa['materials']:
    if m in LIP: continue
    if len(ca[m]) != len(cb[m]): cnt_ok = False; continue
    sa = ca[m][np.lexsort(ca[m].T[::-1])]; sb = cb[m][np.lexsort(cb[m].T[::-1])]
    worst = max(worst, float(np.abs(sa - sb).max()) if len(sa) else 0.0)
gate('TOPOLOGY Face_F (non-lip)', cnt_ok and worst < 5e-5, f'face counts per non-lip material identical, max centroid shift {worst*1000:.3f} mm (paint follows the skin)')
cnt = lambda npz, js: {m: int((npz['Face_F_MI'] == k).sum()) for k, m in enumerate(js['materials']) if m in LIP}
res['lip_faces'] = dict(F1=cnt(a, fa), F3=cnt(b, fb)); print('   lip paint faces (quads): F1', res['lip_faces']['F1'], '-> F3', res['lip_faces']['F3'])
nf = len(b['Body_F_Foff']) - 1
tris_b = int(sum(int(b['Body_F_Foff'][i + 1] - b['Body_F_Foff'][i]) - 2 for i in range(nf)))
nff = len(b['Face_F_Foff']) - 1; tris_f = int(sum(int(b['Face_F_Foff'][i + 1] - b['Face_F_Foff'][i]) - 2 for i in range(nff)))
gate('TRI_BUDGET (<= 50k, Body_F unchanged)', tris_b == 42296 and tris_f + tris_b <= 50000, f'Body_F {tris_b} (F1 42,296) + Face_F {tris_f} (F1 5,364: the rebuilt lip strips add {tris_f - 5364}) = {tris_b + tris_f} tris')


def edge_counts(npz, nm):
    F = npz[nm + '_F']; off = npz[nm + '_Foff']; cnt = collections.Counter()
    for i in range(len(off) - 1):
        f = F[off[i]:off[i + 1]]; n = len(f)
        for k in range(n):
            u, v = int(f[k]), int(f[(k + 1) % n]); cnt[(min(u, v), max(u, v))] += 1
    return sum(1 for cc in cnt.values() if cc == 1), sum(1 for cc in cnt.values() if cc > 2)
bnd, nonman = edge_counts(b, 'Body_F'); bnd1, nonman1 = edge_counts(a, 'Body_F')
gate('MANIFOLD Body_F', (bnd, nonman) == (bnd1, nonman1) == (256, 0), f'boundary edges {bnd} (= the two 128-vertex eye apertures), non-manifold {nonman} (F1: {bnd1}, {nonman1})')
# ------------------------------------------------------------------------------------------------ zone / what moved
Va, Vb = a['Body_F_V'], b['Body_F_V']
dv = np.linalg.norm(Vb - Va, axis=1); moved = dv > 0; z = Va[:, 2]
below = z < 1.4225
gate('BODY_BELOW_NECK (vs F1)', int(moved[below].sum()) == 0, f'{int(below.sum())} verts with z < 1.4225 (collar ring + everything below): moved {int(moved[below].sum())}, max diff {dv[below].max():.1e} m')
gate('ZONE (head only, lower face)', float(Va[moved, 2].min()) > 1.4225 and float(Va[moved, 2].max()) < 1.575,
     f'moved {int(moved.sum())} Body_F verts (max {dv.max()*1000:.2f} mm), z {Va[moved, 2].min()*1000:.1f}..{Va[moved, 2].max()*1000:.1f} mm; y {Va[moved, 1].min()*1000:.0f}..{Va[moved, 1].max()*1000:.0f} mm; |x| max {np.abs(Va[moved, 0]).max()*1000:.0f} mm')
core = (np.abs(Va[:, 0]) < 0.020) & (Va[:, 2] > 1.4575); upper = Va[:, 2] > 1.575
gate('HOLD mouth/nose core + cranial', int(moved[core].sum()) == 0 and int(moved[upper].sum()) == 0, f'mouth/nose core |x|<20 mm, z>1.4575: {int(core.sum())} verts, moved {int(moved[core].sum())}; z>1.575: {int(upper.sum())} verts, moved {int(moved[upper].sum())}')
groups = jb['groups']; res['loops_moved'] = {}
for g in ('LOOP_eyeL', 'LOOP_eyeR', 'LOOP_lid_up_L', 'LOOP_lid_up_R', 'LOOP_lid_low_L', 'LOOP_lid_low_R', 'LOOP_ear_attach_L', 'LOOP_ear_attach_R', 'LOOP_helix_L', 'LOOP_helix_R', 'LOOP_concha_L', 'LOOP_concha_R',
          'LOOP_nostril_L', 'LOOP_nostril_R', 'LOOP_ala_L', 'LOOP_ala_R', 'LOOP_seam', 'LOOP_lip_up', 'LOOP_lip_lo'):
    ids = np.array([i for i, w in groups[g]]); res['loops_moved'][g] = float(dv[ids].max() * 1000)
mv = {k: v for k, v in res['loops_moved'].items() if v > 0}
gate('LOOPS hold (eye/ear/nose/mouth)', not mv or max(mv.values()) < 0.2, 'loops that moved (mm): ' + (str({k: round(v, 3) for k, v in mv.items()}) if mv else 'none (19 loops bit-identical)'))
for g in ('LOOP_jaw_ear_L', 'LOOP_jaw_ear_R'):
    ids = np.array([i for i, w in groups[g]]); res.setdefault('jaw_loops', {})[g] = dict(n=int(len(ids)), moved_mean_mm=float(dv[ids].mean() * 1000), moved_max_mm=float(dv[ids].max() * 1000))
print('   jaw_ear loops (same vertex ids, ride with the surface):', res['jaw_loops'])
# ------------------------------------------------------------------------------------------------ mesh sanity
Fa = [a['Body_F_F'][a['Body_F_Foff'][i]:a['Body_F_Foff'][i + 1]] for i in range(nf)]
fnA = ml.face_normals(Va, Fa); fnB = ml.face_normals(Vb, Fa)
touch = np.array([moved[f].any() for f in Fa])
angd = np.degrees(np.arccos(np.clip((fnA * fnB).sum(1), -1, 1)))
area = lambda V: np.array([0.5 * np.linalg.norm(sum(np.cross(V[f[j]] - V[f[0]], V[f[j + 1]] - V[f[0]]) for j in range(1, len(f) - 1))) for f in Fa])
arB = area(Vb); arA = area(Va)
gate('NO_FOLDS / inversions', float(angd[touch].max()) < 60.0 and int((angd[touch] > 90).sum()) == 0 and float(arB[touch].min()) > 1e-8,
     f'faces touching moved verts {int(touch.sum())}: max face-normal change {angd[touch].max():.1f} deg, >30deg {int((angd[touch] > 30).sum())}, inverted(>90) {int((angd[touch] > 90).sum())}, min area {arB[touch].min()*1e6:.2f} mm2 (F1 min {arA[touch].min()*1e6:.2f})')
e, L1 = ml.edge_stats(Va, Fa); _, L2 = ml.edge_stats(Vb, Fa)
em = moved[e[:, 0]] | moved[e[:, 1]]
print('   edges touching moved verts: %d; length mm F1 min %.2f mean %.2f max %.2f | F3 min %.2f mean %.2f max %.2f' % (int(em.sum()), L1[em].min() * 1000, L1[em].mean() * 1000, L1[em].max() * 1000, L2[em].min() * 1000, L2[em].mean() * 1000, L2[em].max() * 1000))
res['edge_len_mm'] = dict(F1=[float(L1[em].min() * 1000), float(L1[em].mean() * 1000), float(L1[em].max() * 1000)], F3=[float(L2[em].min() * 1000), float(L2[em].mean() * 1000), float(L2[em].max() * 1000)])
print('   height Body_F: %.4f m (F1 %.4f)' % (Vb[:, 2].max() - Vb[:, 2].min(), Va[:, 2].max() - Va[:, 2].min()))
# compare to F2: where F3 differs
V2 = c2['Body_F_V']; d32 = np.linalg.norm(Vb - V2, axis=1)
print('   F3 vs F2 (previous delivery): %d verts differ, max %.2f mm, mean(differing) %.2f mm' % (int((d32 > 1e-9).sum()), d32.max() * 1000, d32[d32 > 1e-9].mean() * 1000))
res['f3_vs_f2'] = dict(n=int((d32 > 1e-9).sum()), max_mm=float(d32.max() * 1000))
json.dump(res, open(fl.W / 'data/verify_f3.json', 'w'), indent=1)
print('ALL STRUCTURAL GATES', 'PASS' if ok else 'FAIL')
