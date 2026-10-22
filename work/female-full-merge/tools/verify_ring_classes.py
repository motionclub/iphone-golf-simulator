"""Sensitivity of the seam numbers to the FORM5-border classification (adjacency-based = operational, z-based = the counts quoted in GATE_DEFS_preregistered.md).  ./py.sh tools/verify_ring_classes.py"""
import numpy as np, json, collections
L = lambda n: np.load(f'data/{n}.npz', allow_pickle=True)
FIN, A = L('final_body'), L('artdir_body'); D = np.load('export/full_merge_delta.npz'); vmz = np.load('data/vmap_artdir_to_base.npz'); vm = vmz['base_to_final'].astype(np.int64); f2a = vmz['final_to_base'].astype(np.int64)
dz = np.load('start/torso_form5_delta.npz'); arms = np.load('start/arms_delta.npz'); lv = np.load('start/limbs_vertex_map.npz')
VF, VA = FIN['V'].astype(np.float64), A['V'].astype(np.float64); nb = 23247
old = D['old_head_idx'].astype(np.int64); keep_v = np.ones(nb, bool); keep_v[old] = False; newidx = np.cumsum(keep_v) - 1; nkeep = int(keep_v.sum())
art_of_final = np.full(len(VF), -1, np.int64); base_of_final = np.full(len(VF), -1, np.int64); base_of_final[:nkeep] = np.nonzero(keep_v)[0]; art_of_final[:nkeep] = f2a[base_of_final[:nkeep]]
fin_of_art = lambda a: newidx[vm[np.asarray(a, np.int64)]]
border = dz['border_mask'].astype(bool); zone = dz['zone_mask'].astype(bool); bidx = np.nonzero(border)[0]; zb = VA[bidx, 2]
nbr = collections.defaultdict(set); ls, lt, cv = FIN['loop_start'], FIN['loop_total'], FIN['corner_verts']
for s, t in zip(ls, lt):
    vs = cv[s:s + t]
    for i in range(t): a, b = int(vs[i]), int(vs[(i + 1) % t]); nbr[a].add(b); nbr[b].add(a)
arm_zone_art = lv['final_to_base'][np.nonzero(arms['zone_mask_limbs_order'])[0]]; arm_zone_art = arm_zone_art[arm_zone_art >= 0]; arm_f = set(fin_of_art(arm_zone_art).tolist())
touch = np.array([any(w in arm_f for w in nbr[int(f)]) for f in fin_of_art(bidx)])
floor = np.abs(zb - 0.62) < 0.01
classes = {'adjacency: neck (not adjacent to arm zone, z>1.3)': bidx[(~touch) & (zb > 1.3)], 'adjacency: armpit/shoulder (adjacent to arm zone)': bidx[touch], 'adjacency: other 8 border verts (z<=1.3, not adjacent to arm)': bidx[(~touch) & (zb <= 1.3) & ~floor],
           'z-based: neck (z>1.3)': bidx[zb > 1.3], 'z-based: rest (arm junction, z<=1.3, not floor)': bidx[(zb <= 1.3) & ~floor], 'floor ring (|z-.62|<.01)': bidx[floor]}
ref = np.zeros_like(VF); has = art_of_final >= 0; ref[has] = VA[art_of_final[has]]
out = {}
for name, ring_a in classes.items():
    R = set(fin_of_art(ring_a).tolist()); best = 0.0
    for r in R:
        for w in nbr[r]:
            if w not in R and has[w] and has[r]: best = max(best, np.linalg.norm((VF[w] - VF[r]) - (ref[w] - ref[r])))
    out[name] = dict(verts=len(ring_a), displacement_step_vs_ArtDir_mm=float(best * 1000)); print(f'{name:62s} n={len(ring_a):3d}  step {best*1000:7.3f} mm')
json.dump(out, open('data/ring_classes.json', 'w'), indent=1)
