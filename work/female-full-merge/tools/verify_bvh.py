"""BVH based checks (run inside Blender, no blend needs to be open):
    blender -b --factory-startup --python tools/verify_bvh.py
1. COLLAR_OFFSET: F3 head vertices on rows 1..4 above the collar ring vs the ORIGINAL ArtDir surface they replaced (closest point on ArtDir head+neck faces).
2. Self-intersections (non-adjacent triangle pairs, BVH overlap), hands base vs merged, classified hand-hand / hand-body / by zone (same method as work/female-hands-fingers/verify_blend_f.py).
3. Face_F alignment: distance of every Face_F vertex to the nearest Body_F surface, final vs F3 (identical head => identical distribution).
Writes data/bvh_checks.json"""
import bpy, numpy as np, json, collections, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
L = lambda n: np.load(f'data/{n}.npz', allow_pickle=True)
FIN, B, F3, A, FFIN, FF3, S3 = (L(n) for n in ('final_body', 'base_body', 'f3_body', 'artdir_body', 'final_face', 'f3_face', 'stage3_body'))
D = np.load('export/full_merge_delta.npz'); vmz = np.load('data/vmap_artdir_to_base.npz'); vm = vmz['base_to_final'].astype(np.int64); f2a = vmz['final_to_base'].astype(np.int64)
dz = np.load('start/torso_form5_delta.npz'); arms = np.load('start/arms_delta.npz'); hd = np.load('start/hands_delta.npz'); lv = np.load('start/limbs_vertex_map.npz')
nb = len(B['V']); old = D['old_head_idx'].astype(np.int64); keep_v = np.ones(nb, bool); keep_v[old] = False; newidx = np.cumsum(keep_v) - 1; nkeep = int(keep_v.sum())
res = {}
def tris_of(d):
    ls, lt, cv = d['loop_start'], d['loop_total'], d['corner_verts']; T = []; TF = []
    for fi, (s, t) in enumerate(zip(ls, lt)):
        for k in range(1, t - 1): T.append((int(cv[s]), int(cv[s + k]), int(cv[s + k + 1]))); TF.append(fi)
    return np.array(T), np.array(TF)
def bvh_of(V, T): return BVHTree.FromPolygons([tuple(map(float, v)) for v in V], [tuple(int(i) for i in t) for t in T], all_triangles=True, epsilon=0.0)

# ------------------------------------------------------------------ 1. COLLAR_OFFSET
Aq = A['V'].astype(np.float64); ls, lt, cv = A['loop_start'], A['loop_total'], A['corner_verts']
head_art = Aq[:, 2] > float(D['cut_z'])
sel = [fi for fi, (s, t) in enumerate(zip(ls, lt)) if head_art[cv[s:s + t]].any()]            # head + crossing faces = the surface F3's head replaced
Tn, Tf = [], []
for fi in sel:
    s, t = ls[fi], lt[fi]
    for k in range(1, t - 1): Tn.append((int(cv[s]), int(cv[s + k]), int(cv[s + k + 1]))); Tf.append(fi)
oldbvh = bvh_of(Aq, np.array(Tn))
Vf = FIN['V'].astype(np.float64); fls, flt, fcv = FIN['loop_start'], FIN['loop_total'], FIN['corner_verts']
nbr = collections.defaultdict(set)
for s, t in zip(fls, flt):
    vs = fcv[s:s + t]
    for i in range(t):
        a, b = int(vs[i]), int(vs[(i + 1) % t]); nbr[a].add(b); nbr[b].add(a)
collar = set(newidx[D['ring_base_idx'].astype(np.int64)].tolist())
rows = [set()]; seen = set(collar); frontier = set(collar)
for k in range(1, 7):
    nxt = set()
    for u in frontier:
        for w in nbr[u]:
            if w >= nkeep and w not in seen: nxt.add(w)
    rows.append(nxt); seen |= nxt; frontier = nxt
def offset(P):
    loc, nrm, idx, dist = oldbvh.find_nearest(Vector(P)); return dist, float(np.dot(P - np.array(loc), np.array(nrm)))
co = {}
for k in range(1, 7):
    if not rows[k]: continue
    d = [offset(Vf[w]) for w in rows[k]]; mag = np.array([x[0] for x in d]) * 1000; sg = np.array([x[1] for x in d]) * 1000
    co[f'row{k}'] = dict(verts=len(rows[k]), z_mean=float(np.mean([Vf[w, 2] for w in rows[k]])), max_dist_mm=float(mag.max()), mean_dist_mm=float(mag.mean()), max_abs_signed_normal_offset_mm=float(np.abs(sg).max()))
res['COLLAR_OFFSET'] = co; res['COLLAR_OFFSET_MM_row1_max'] = co['row1']['max_dist_mm']
print('COLLAR_OFFSET (head vertices vs the original ArtDir neck/head surface):')
for k, v in co.items(): print(' ', k, {a: round(b, 4) if isinstance(b, float) else b for a, b in v.items()})
# dihedral across collar ring edges, final vs ArtDir
def edge_dihedrals(V, ls_, lt_, cv_, ring_pairs):
    # face normals
    fn = {}
    for fi, (s, t) in enumerate(zip(ls_, lt_)):
        P = V[cv_[s:s + t]]; n = np.zeros(3)
        for i in range(t): n += np.cross(P[i], P[(i + 1) % t])
        fn[fi] = n / max(np.linalg.norm(n), 1e-30)
    e2f = collections.defaultdict(list)
    for fi, (s, t) in enumerate(zip(ls_, lt_)):
        vs = cv_[s:s + t]
        for i in range(t):
            a, b = int(vs[i]), int(vs[(i + 1) % t]); e2f[(min(a, b), max(a, b))].append(fi)
    out = []
    for e in ring_pairs:
        fs = e2f.get(e, [])
        if len(fs) == 2: out.append(float(np.degrees(np.arccos(np.clip(np.dot(fn[fs[0]], fn[fs[1]]), -1, 1)))))
    return out
# edges whose both endpoints are collar ring verts or that connect ring to the first head row
ring_edges_final = [(min(a, b), max(a, b)) for a in collar for b in nbr[a] if b in collar or b in rows[1]]
dh_final = edge_dihedrals(Vf, fls, flt, fcv, set(ring_edges_final))
# ArtDir equivalents: ring verts (ArtDir idx) and neighbours above
ring_art = f2a[D['ring_base_idx'].astype(np.int64)]
nbrA = collections.defaultdict(set)
for s, t in zip(ls, lt):
    vs = cv[s:s + t]
    for i in range(t):
        a, b = int(vs[i]), int(vs[(i + 1) % t]); nbrA[a].add(b); nbrA[b].add(a)
ra = set(int(x) for x in ring_art)
ring_edges_art = [(min(a, b), max(a, b)) for a in ra for b in nbrA[a] if (b in ra) or head_art[b]]
dh_art = edge_dihedrals(Aq, ls, lt, cv, set(ring_edges_art))
res['collar_ring_dihedral_deg'] = dict(merged_max=float(max(dh_final)), merged_mean=float(np.mean(dh_final)), ArtDir_original_max=float(max(dh_art)), ArtDir_original_mean=float(np.mean(dh_art)), n_merged=len(dh_final), n_ArtDir=len(dh_art))
print('collar ring dihedral across ring/first-row edges (deg):', res['collar_ring_dihedral_deg'])

# ------------------------------------------------------------------ 2. self-intersections, base vs merged
slots = hd['slots'].astype(np.int64)
def region_labels(n, art_idx_of):
    lab = np.array(['other'] * n, dtype=object)
    for i in range(n):
        a = art_idx_of[i]
        if a < 0: lab[i] = 'hand/limb-new'
    return lab
def run(name, d, base_idx_of_vertex, is_head_vertex, hand_mask):
    V = d['V'].astype(np.float64); T, TF = tris_of(d); bvh = bvh_of(V, T)
    pairs = [(i, j) for i, j in bvh.overlap(bvh) if i < j]
    # zone labels per vertex
    n = len(V); art = np.full(n, -1, np.int64); m = base_idx_of_vertex >= 0; art[m] = f2a[base_idx_of_vertex[m]]
    zone = dz['zone_mask'].astype(bool); armz = np.zeros(len(zone), bool); az = lv['final_to_base'][np.nonzero(arms['zone_mask_limbs_order'])[0]]; armz[az[az >= 0]] = True
    vlab = np.full(n, 'other/legs', dtype=object)
    for i in range(n):
        if hand_mask[i]: vlab[i] = 'hand'
        elif is_head_vertex[i]: vlab[i] = 'head'
        elif art[i] >= 0 and zone[art[i]]: vlab[i] = 'torso'
        elif art[i] >= 0 and armz[art[i]]: vlab[i] = 'arm'
    cnt = collections.Counter(); allp = 0; ex = []
    for i, j in pairs:
        if set(T[i].tolist()) & set(T[j].tolist()): continue
        allp += 1
        li = sorted(set(vlab[T[i]].tolist())); lj = sorted(set(vlab[T[j]].tolist()))
        hi, hj = 'hand' in li, 'hand' in lj
        if hi and hj: cnt['hand-hand'] += 1
        elif hi or hj: cnt['hand-body'] += 1
        key = '+'.join(sorted(set(li) | set(lj))); cnt['zones:' + key] += 1
        if len(ex) < 6 and (hi or hj): ex.append([float(x) for x in V[T[i]].mean(0)])
    print(name, 'tris', len(T), 'non-adjacent overlap pairs', allp, dict(cnt))
    return dict(tris=int(len(T)), nonadjacent_overlap_pairs=allp, breakdown=dict(cnt), example_hand_pair_centres=ex)
# base
hand_b = np.zeros(nb, bool); hand_b[slots] = True; hand_b[22419:] = True
head_b = np.zeros(nb, bool); head_b[old] = True
res['bvh_hands_base'] = run('hands base', B, np.arange(nb), head_b, hand_b)
# stage 3 (torso merged, old head still there) - isolates what FORM5 does to the arms/hands
res['bvh_stage3_torso_merged_old_head'] = run('stage3 (FORM5, old head)', S3, np.arange(nb), head_b, hand_b)
# merged
nf_ = len(FIN['V']); base_of_final = np.full(nf_, -1, np.int64); base_of_final[:nkeep] = np.nonzero(keep_v)[0]
hand_f = np.zeros(nf_, bool); hand_f[newidx[slots]] = True; hand_f[newidx[np.arange(22419, nb)]] = True
head_f = np.zeros(nf_, bool); head_f[nkeep:] = True
res['bvh_merged'] = run('merged', FIN, base_of_final, head_f, hand_f)
res['bvh_F3_body'] = None
# ------------------------------------------------------------------ 3. Face_F alignment
def gaps(body, face):
    V = body['V'].astype(np.float64); T, _ = tris_of(body); bv = bvh_of(V, T)
    P = face['V'].astype(np.float64); d = np.empty(len(P))
    for i, p in enumerate(P):
        loc, nrm, idx, dist = bv.find_nearest(Vector(p)); d[i] = dist
    return d
gf = gaps(FIN, FFIN); g3 = gaps(F3, FF3)
res['Face_F_alignment'] = dict(face_vertices=int(len(gf)), merged_min_gap_mm=float(gf.min() * 1000), F3_min_gap_mm=float(g3.min() * 1000), max_abs_diff_between_merged_and_F3_gaps_mm=float(np.abs(gf - g3).max() * 1000),
                               Face_F_positions_identical_to_F3=bool(np.array_equal(FFIN['V'], FF3['V'])), Face_F_topology_identical_to_F3=bool(np.array_equal(FFIN['corner_verts'], FF3['corner_verts']) and np.array_equal(FFIN['material_index'], FF3['material_index'])),
                               Face_F_custom_normals_identical_to_F3=bool(np.array_equal(FFIN['custom_normal_i16'], FF3['custom_normal_i16'])))
print('Face_F alignment:', res['Face_F_alignment'])
json.dump(res, open('data/bvh_checks.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print('BVH_DONE')
