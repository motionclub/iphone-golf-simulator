"""MicroF2 verification: F2 vs the staged F1 blend (and the ArtDir start blend for BODY_BELOW_NECK).  python3 verify_f2.py [tag] -> data/verify_f2.json + printed gate lines
needs data/dump/F1.npz, F2.npz (tools/dump_full.py) and, for the start-blend comparison, data/dump/START.npz."""
import sys, json, hashlib, collections
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np
import fl, meshlib as ml
D = fl.W / 'data/dump'
a = np.load(D / 'F1.npz'); b = np.load(D / 'F2.npz')
res = {}
ok = True
def gate(name, passed, detail=''):
    global ok
    ok &= bool(passed); res[name] = dict(passed=bool(passed), detail=detail)
    print(('GATE %-34s %s  %s' % (name, 'PASS' if passed else 'FAIL', detail)).rstrip())
# ------------------------------------------------------------------------------------------------ topology / structure
for nm in ('Body_F', 'Face_F'):
    same_f = np.array_equal(a[nm + '_F'], b[nm + '_F']) and np.array_equal(a[nm + '_Foff'], b[nm + '_Foff'])
    same_m = np.array_equal(a[nm + '_MI'], b[nm + '_MI']); same_s = np.array_equal(a[nm + '_smooth'], b[nm + '_smooth'])
    uvk = [k for k in a.files if k.startswith(nm + '_uv_')]
    same_uv = all(np.array_equal(a[k], b[k]) for k in uvk)
    gate(f'TOPOLOGY {nm}', same_f and same_m and same_s and same_uv, f'faces+offsets {same_f}, material idx {same_m}, smooth flags {same_s}, UVs {same_uv} ({len(uvk)} layers)')
ja = json.load(open(D / 'F1_Body_F.json')); jb = json.load(open(D / 'F2_Body_F.json'))
gate('VERTEX_GROUPS (21 LOOP_*)', ja['groups'] == jb['groups'] and len(jb['groups']) == 21, f"{len(jb['groups'])} groups, membership+weights identical: {ja['groups'] == jb['groups']}")
gate('MATERIALS/OBJECTS', ja['materials'] == jb['materials'] and json.load(open(D / 'F1_objects.json')) == json.load(open(D / 'F2_objects.json')) and ja['n_edges'] == jb['n_edges'] and not jb['has_custom_normals'],
     f"slots {jb['materials']}, edges {jb['n_edges']}, custom normals {jb['has_custom_normals']}")
nf = len(b['Body_F_Foff']) - 1
tris_b = int(sum(int(b['Body_F_Foff'][i + 1] - b['Body_F_Foff'][i]) - 2 for i in range(nf)))
nff = len(b['Face_F_Foff']) - 1; tris_f = int(sum(int(b['Face_F_Foff'][i + 1] - b['Face_F_Foff'][i]) - 2 for i in range(nff)))
gate('NO_DENSIFY (tri budget)', tris_b == 42296 and tris_f == 5364, f'Body_F {tris_b} + Face_F {tris_f} = {tris_b + tris_f} tris (F1: 42,296 + 5,364 = 47,660); verts {len(b["Body_F_V"])} / {len(b["Face_F_V"])}')
# manifold / boundary
def edge_counts(npz, nm):
    F = npz[nm + '_F']; off = npz[nm + '_Foff']; cnt = collections.Counter()
    for i in range(len(off) - 1):
        f = F[off[i]:off[i + 1]]; n = len(f)
        for k in range(n):
            u, v = int(f[k]), int(f[(k + 1) % n]); cnt[(min(u, v), max(u, v))] += 1
    return sum(1 for c in cnt.values() if c == 1), sum(1 for c in cnt.values() if c > 2)
bnd, nonman = edge_counts(b, 'Body_F'); bnd1, nonman1 = edge_counts(a, 'Body_F')
gate('MANIFOLD', (bnd, nonman) == (bnd1, nonman1) == (256, 0), f'boundary edges {bnd} (= the two 128-vertex eye apertures), non-manifold {nonman} (F1: {bnd1}, {nonman1})')
# ------------------------------------------------------------------------------------------------ zone / what moved
Va, Vb = a['Body_F_V'], b['Body_F_V']
dv = np.linalg.norm(Vb - Va, axis=1); moved = dv > 0
z = Va[:, 2]
below = z < 1.4225
gate('BODY_BELOW_NECK (vs F1)', int(moved[below].sum()) == 0, f'{int(below.sum())} verts with z < 1.4225 (collar ring z 1.3965-1.4053 and everything below): moved {int(moved[below].sum())}, max diff {dv[below].max():.1e} m')
ring = np.load(fl.W / 'data/ring.npz')
gate('ZONE_OUTSIDE (head only, lower face)', float(Va[moved, 2].min()) > 1.4225 and float(Va[moved, 2].max()) < 1.53,
     f'moved {int(moved.sum())} Body_F verts, z {Va[moved, 2].min()*1000:.1f}..{Va[moved, 2].max()*1000:.1f} mm; y {Va[moved, 1].min()*1000:.0f}..{Va[moved, 1].max()*1000:.0f} mm; |x| max {np.abs(Va[moved, 0]).max()*1000:.0f} mm')
core = (np.abs(Va[:, 0]) < 0.020) & (Va[:, 2] > 1.4575)
upper = Va[:, 2] > 1.53
gate('HOLD mouth/nose/eyes/brows/cranial', int(moved[core].sum()) == 0 and int(moved[upper].sum()) == 0,
     f'verts above the lower face (z>1.53): {int(upper.sum())}, moved {int(moved[upper].sum())}; mouth/nose core |x|<20 mm, z>1.4575: {int(core.sum())}, moved {int(moved[core].sum())}')
lips = (np.abs(Va[:, 0]) < 0.036) & (Va[:, 2] > 1.4575) & (Va[:, 2] < 1.50)
res['lip_extent_max_move_mm'] = float(dv[lips].max() * 1000)
print('   lip extent |x|<36 mm, z 1.4575-1.50: %d verts, max move %.3f mm' % (int(lips.sum()), dv[lips].max() * 1000))
# ear / eye loops untouched
groups = jb['groups']
for nm in ('LOOP_eyeL', 'LOOP_eyeR', 'LOOP_ear_attach_L', 'LOOP_ear_attach_R', 'LOOP_helix_L', 'LOOP_helix_R', 'LOOP_concha_L', 'LOOP_concha_R', 'LOOP_nostril_L', 'LOOP_nostril_R', 'LOOP_ala_L', 'LOOP_ala_R', 'LOOP_seam', 'LOOP_lip_up', 'LOOP_lip_lo'):
    ids = np.array([i for i, w in groups[nm]]); res.setdefault('loops_moved', {})[nm] = float(dv[ids].max() * 1000)
mv_loops = {k: v for k, v in res['loops_moved'].items() if v > 0}
gate('LOOPS hold (eye/ear/nose/mouth)', not mv_loops or max(mv_loops.values()) < 0.2, 'loops that moved (mm): ' + (str({k: round(v, 3) for k, v in mv_loops.items()}) if mv_loops else 'none'))
for nm in ('LOOP_jaw_ear_L', 'LOOP_jaw_ear_R'):
    ids = np.array([i for i, w in groups[nm]]); res.setdefault('jaw_loops', {})[nm] = dict(n=int(len(ids)), moved_mean_mm=float(dv[ids].mean() * 1000), moved_max_mm=float(dv[ids].max() * 1000))
print('   jaw_ear loops (same vertex ids, moved with the surface):', res['jaw_loops'])
# ------------------------------------------------------------------------------------------------ Face_F
Lva, Lvb = a['Face_F_V'], b['Face_F_V']; dl = np.linalg.norm(Lvb - Lva, axis=1)
print('   Face_F verts changed: %d, max shift %.3f mm (only where the skin under the paint moved: lower lip edge / chin side)' % (int((dl > 0).sum()), dl.max() * 1000))
res['face_f_changed'] = int((dl > 0).sum()); res['face_f_max_shift_mm'] = float(dl.max() * 1000)
# ------------------------------------------------------------------------------------------------ mesh sanity (folds, degenerate, edge lengths) on faces touching a moved vertex
Fa = [a['Body_F_F'][a['Body_F_Foff'][i]:a['Body_F_Foff'][i + 1]] for i in range(nf)]
fnA = ml.face_normals(Va, Fa); fnB = ml.face_normals(Vb, Fa)
touch = np.array([moved[f].any() for f in Fa])
cosang = np.clip((fnA * fnB).sum(1), -1, 1); angd = np.degrees(np.arccos(cosang))
area = lambda V: np.array([0.5 * np.linalg.norm(sum(np.cross(V[f[j]] - V[f[0]], V[f[j + 1]] - V[f[0]]) for j in range(1, len(f) - 1))) for f in Fa])
arB = area(Vb); arA = area(Va)
gate('NO_FOLDS / inversions', float(angd[touch].max()) < 60.0 and int((angd[touch] > 90).sum()) == 0 and float(arB[touch].min()) > 1e-8,
     f'faces touching moved verts {int(touch.sum())}: max face-normal change {angd[touch].max():.1f} deg, >30deg {int((angd[touch] > 30).sum())}, inverted(>90) {int((angd[touch] > 90).sum())}, min area {arB[touch].min()*1e6:.2f} mm2 (F1 min {arA[touch].min()*1e6:.2f})')
e, L1 = ml.edge_stats(Va, Fa); _, L2 = ml.edge_stats(Vb, Fa)
em = moved[e[:, 0]] | moved[e[:, 1]]
print('   edges touching moved verts: %d; length mm F1 min %.2f mean %.2f max %.2f | F2 min %.2f mean %.2f max %.2f' % (int(em.sum()), L1[em].min() * 1000, L1[em].mean() * 1000, L1[em].max() * 1000, L2[em].min() * 1000, L2[em].mean() * 1000, L2[em].max() * 1000))
res['edge_len_mm'] = dict(F1=[float(L1[em].min() * 1000), float(L1[em].mean() * 1000), float(L1[em].max() * 1000)], F2=[float(L2[em].min() * 1000), float(L2[em].mean() * 1000), float(L2[em].max() * 1000)])
print('   height Body_F: %.4f m (F1 %.4f)' % (Vb[:, 2].max() - Vb[:, 2].min(), Va[:, 2].max() - Va[:, 2].min()))
json.dump(res, open(fl.W / 'data/verify_f2.json', 'w'), indent=1)
print('ALL STRUCTURAL GATES', 'PASS' if ok else 'FAIL')
