"""What if chat 7's 123 border-ring vertices had been LEFT at chat 7's positions (the --force route FORM5's README suggests for an arms-candidate base)?  ./py.sh tools/verify_force_variant.py"""
import numpy as np, collections, json
L = lambda n: np.load(f'data/{n}.npz', allow_pickle=True)
FIN, A, B = L('final_body'), L('artdir_body'), L('base_body'); D = np.load('export/full_merge_delta.npz'); vmz = np.load('data/vmap_artdir_to_base.npz'); vm = vmz['base_to_final'].astype(np.int64); f2a = vmz['final_to_base'].astype(np.int64)
dz = np.load('start/torso_form5_delta.npz'); c7 = np.load('start/chat7_torso_delta.npz'); arms = np.load('start/arms_delta.npz'); lv = np.load('start/limbs_vertex_map.npz'); R = np.load('data/rings_final.npz')
VF = FIN['V'].astype(np.float64).copy(); VA = A['V'].astype(np.float64); VB = B['V'].astype(np.float64); nb = 23247
old = D['old_head_idx'].astype(np.int64); keep_v = np.ones(nb, bool); keep_v[old] = False; newidx = np.cumsum(keep_v) - 1; nkeep = int(keep_v.sum())
art_of_final = np.full(len(VF), -1, np.int64); art_of_final[:nkeep] = f2a[np.nonzero(keep_v)[0]]
border = dz['border_mask'].astype(bool); inD = np.zeros(len(VA), bool); inD[dz['moved_idx']] = True
res_art = [a for a in c7['moved_idx'] if border[a] and not inD[a]]            # the 123 chat-7-moved border vertices NOT in the FORM5 delta
fi = newidx[vm[np.array(res_art)]]
VF_force = VF.copy(); VF_force[fi] = VB[vm[np.array(res_art)]]                 # base (= chat 7) positions
nbr = collections.defaultdict(set); ls, lt, cv = FIN['loop_start'], FIN['loop_total'], FIN['corner_verts']
for s, t in zip(ls, lt):
    vs = cv[s:s + t]
    for i in range(t): a, b = int(vs[i]), int(vs[(i + 1) % t]); nbr[a].add(b); nbr[b].add(a)
has = art_of_final >= 0; ref = np.zeros_like(VF); ref[has] = VA[art_of_final[has]]
def step(ring, V):
    Rr = set(int(x) for x in ring); best = 0
    for r in Rr:
        for w in nbr[r]:
            if w not in Rr and has[r] and has[w]: best = max(best, np.linalg.norm((V[w] - V[r]) - (ref[w] - ref[r])))
    return best * 1000
out = {}
for k, nm in (('neck', 'neck/shoulder ring'), ('armpit', 'armpit ring'), ('floor', 'leg-top floor ring')):
    out[nm] = dict(delivered_mm=float(step(R[k], VF)), if_chat7_border_residue_kept_mm=float(step(R[k], VF_force)))
out['border_residue_vertices'] = len(res_art); out['max_residue_displacement_mm'] = float(np.linalg.norm(VB[vm[np.array(res_art)]] - VA[np.array(res_art)], axis=1).max() * 1000)
out['FORM5_budget_mm'] = {'neck': 1.0, 'armpit': 10.0, 'floor': 8.0}
print(json.dumps(out, indent=1)); json.dump(out, open('data/force_variant.json', 'w'), indent=1)
