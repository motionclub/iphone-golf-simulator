"""Seam / weld measurements on the merged Body_F (numpy; ./py.sh tools/verify_seams.py).  Definitions are the PRE-REGISTERED ones in GATE_DEFS_preregistered.md.
POSITION_STEP      = max |final position - position the other piece(s) expect|  (pins stay pins => 0)
DISPLACEMENT_STEP  = max over ring-crossing edges (r in ring, w not in ring) of |(P_w - P_r)_final - (P_w - P_r)_before|   (FORM5 SEAM_CLEAN convention), before = ArtDir original / hands base
COLLAR_OFFSET      = computed in tools/verify_bvh.py (Blender): head vertices on the collar ring's neighbours vs the ORIGINAL ArtDir surface they replaced.
Output: data/seams.json"""
import numpy as np, json, collections
L = lambda n: np.load(f'data/{n}.npz', allow_pickle=True)
FIN, B, F3, A, ARMS, T5, S3 = (L(n) for n in ('final_body', 'base_body', 'f3_body', 'artdir_body', 'arms_body', 'form5_body', 'stage3_body'))
D = np.load('export/full_merge_delta.npz'); vmz = np.load('data/vmap_artdir_to_base.npz'); vm = vmz['base_to_final'].astype(np.int64); f2a = vmz['final_to_base'].astype(np.int64)
dz = np.load('start/torso_form5_delta.npz'); arms = np.load('start/arms_delta.npz'); hd = np.load('start/hands_delta.npz'); lv = np.load('start/limbs_vertex_map.npz')
VF, VB, VA = FIN['V'].astype(np.float64), B['V'].astype(np.float64), A['V'].astype(np.float64)
nb = len(VB); old = D['old_head_idx'].astype(np.int64); keep_v = np.ones(nb, bool); keep_v[old] = False; newidx = np.cumsum(keep_v) - 1; nkeep = int(keep_v.sum())
base_of_final = np.full(len(VF), -1, np.int64); base_of_final[:nkeep] = np.nonzero(keep_v)[0]
art_of_final = np.full(len(VF), -1, np.int64); art_of_final[:nkeep] = f2a[base_of_final[:nkeep]]
def fin_of_base(i): return newidx[np.asarray(i, np.int64)]
def fin_of_art(a):
    a = np.asarray(a, np.int64); b = vm[a]; assert (b >= 0).all(); return newidx[b]
zone = dz['zone_mask'].astype(bool); border = dz['border_mask'].astype(bool)
za = np.nonzero(zone)[0]
# --------------------------------------------------------------- rings in ArtDir index space
arm_zone_l = np.nonzero(arms['zone_mask_limbs_order'])[0]; pins_l = arms['pinned_idx_limbs_order'].astype(np.int64)
arm_zone_art = lv['final_to_base'][arm_zone_l]; arm_zone_art = arm_zone_art[arm_zone_art >= 0]
# adjacency in the final mesh
ls, lt, cv = FIN['loop_start'], FIN['loop_total'], FIN['corner_verts']
nbr = collections.defaultdict(set)
for s, t in zip(ls, lt):
    vs = cv[s:s + t]
    for i in range(t):
        a, b = int(vs[i]), int(vs[(i + 1) % t]); nbr[a].add(b); nbr[b].add(a)
bidx = np.nonzero(border)[0]
zb = VA[bidx, 2]
floor_a = bidx[np.abs(zb - 0.62) < 0.01]
arm_set_f = set(fin_of_art(arm_zone_art).tolist())
bfin = fin_of_art(bidx)
touch_arm = np.array([any(w in arm_set_f for w in nbr[int(f)]) for f in bfin])
arm_junction_a = bidx[touch_arm]
neck_a = bidx[(~touch_arm) & (zb > 1.3)]
others = bidx[~np.isin(bidx, np.concatenate([floor_a, arm_junction_a, neck_a]))]
rings = {'neck_shoulder_FORM5_border': neck_a, 'armpit_FORM5_border': arm_junction_a, 'leg_top_floor_FORM5_border': floor_a}
print('FORM5 border classes: neck', len(neck_a), ' armpit(adjacent to arm zone)', len(arm_junction_a), ' floor', len(floor_a), ' unclassified', len(others))
print('   z-based classes for comparison: neck(z>1.3) %d floor %d rest %d' % ((zb > 1.3).sum(), (np.abs(zb - 0.62) < 0.01).sum(), ((zb <= 1.3) & (np.abs(zb - 0.62) >= 0.01)).sum()))
# --------------------------------------------------------------- helpers
def disp_vs(ref_pos_of_final, mask_has_ref):
    # displacement of each final vertex vs reference (nan where no reference)
    d = np.full(len(VF), np.nan); m = mask_has_ref; d[m] = np.linalg.norm(VF[m] - ref_pos_of_final[m], axis=1); return d
ref_art = np.zeros_like(VF); has_art = art_of_final >= 0; ref_art[has_art] = VA[art_of_final[has_art]]
ref_base = np.zeros_like(VF); has_base = base_of_final >= 0; ref_base[has_base] = VB[base_of_final[has_base]]
disp_art = disp_vs(ref_art, has_art); disp_base = disp_vs(ref_base, has_base)
def crossing(ring_f):
    R = set(int(x) for x in ring_f); E = []
    for r in R:
        for w in nbr[r]:
            if w not in R: E.append((r, w))
    return E
def step(E, ref, has):
    best = 0.0; arg = None; vals = []
    for r, w in E:
        if not (has[r] and has[w]): continue
        d = np.linalg.norm((VF[w] - VF[r]) - (ref[w] - ref[r])); vals.append(d)
        if d > best: best = d; arg = (r, w)
    return best * 1000, arg, (np.mean(vals) * 1000 if vals else 0.0), len(vals)
def side_label(w):
    a = art_of_final[w]
    if w >= nkeep: return 'head(new F3 vertex)'
    if a < 0: return 'new limbs/hands vertex'
    if zone[a]: return 'torso FORM5 zone'
    if a in arm_zone_set: return 'arm zone'
    return 'other (unchanged body)'
arm_zone_set = set(arm_zone_art.tolist())
res = {}
print('\n--- DISPLACEMENT_STEP per ring (mm); FORM5 reported: neck 0.57, armpit 9.42, floor 1.35')
for name, ring_a in rings.items():
    ring_f = fin_of_art(ring_a); E = crossing(ring_f)
    sa, arga, ma, na = step(E, ref_art, has_art); sb, argb, mb, nbse = step(E, ref_base, has_base)
    # per side (neighbour category) vs ArtDir
    per_side = collections.defaultdict(float)
    for r, w in E:
        if not (has_art[r] and has_art[w]): continue
        d = np.linalg.norm((VF[w] - VF[r]) - (ref_art[w] - ref_art[r])) * 1000; sl = side_label(w); per_side[sl] = max(per_side[sl], d)
    # FORM5-convention: displacement of ZONE-interior neighbours only (ring itself unmoved)
    zi = max([disp_art[w] * 1000 for r, w in E if has_art[w] and zone[art_of_final[w]] and not border[art_of_final[w]]] or [0])
    res[name] = dict(ring_verts=int(len(ring_f)), crossing_edges=len(E), DISPLACEMENT_STEP_vs_ArtDir_mm=float(sa), DISPLACEMENT_STEP_vs_hands_base_mm=float(sb), mean_vs_ArtDir_mm=float(ma),
                     FORM5_convention_interior_neighbour_displacement_mm=float(zi), per_neighbour_side_vs_ArtDir_mm={k: float(v) for k, v in per_side.items()},
                     at_vertex_z_x_of_max=[float(VF[arga[1], 2]), float(VF[arga[1], 0])] if arga else None)
    print(f'{name:30s} ring {len(ring_f):3d} edges {len(E):4d}  step vs ArtDir {sa:7.3f}  vs hands base {sb:7.3f}  FORM5-convention {zi:7.3f}  sides {dict((k, round(v, 3)) for k, v in per_side.items())}')
# --------------------------------------------------------------- armpit across the 2-ring band (torso border | arm pins)
pins_f = fin_of_base(pins_l); pin_set = set(pins_f.tolist()); ring_arm_f = fin_of_art(arm_junction_a); ring_arm_set = set(ring_arm_f.tolist())
rel = []; adj_pairs = 0
dispv = lambda w: VF[w] - ref_art[w]
for r in ring_arm_f:
    for p in nbr[int(r)]:
        if p in pin_set:
            adj_pairs += 1
            us = [u for u in nbr[int(r)] if u != p and u not in ring_arm_set and u not in pin_set and has_art[u]]
            vs_ = [v for v in nbr[p] if v != r and v not in ring_arm_set and v not in pin_set and has_art[v]]
            for u in us:
                for v in vs_:
                    rel.append(np.linalg.norm(dispv(v) - dispv(u)) * 1000)
res['armpit_relative_step_across_border_and_pins'] = dict(ring_pin_adjacent_pairs=adj_pairs, paths=len(rel), max_mm=float(max(rel)) if rel else None, mean_mm=float(np.mean(rel)) if rel else None)
print('armpit relative step across (torso border | arm pins):', res['armpit_relative_step_across_border_and_pins'])
pin_disp = max(float(np.linalg.norm(VF[p] - ref_art[p]) * 1000) for p in pins_f if has_art[p])
res['armpit_pins_displacement_vs_ArtDir_mm_max'] = pin_disp; print('arm pins displacement vs ArtDir (must be 0):', pin_disp)
# --------------------------------------------------------------- wrist rings (hands chat's 36 ring verts)
wr_f = fin_of_base(hd['ring'].astype(np.int64)); E = crossing(wr_f)
sa, _, _, _ = step(E, ref_art, has_art); sb, _, _, nbse = step(E, ref_base, has_base)
side = collections.defaultdict(float)
for r, w in E:
    if has_art[r] and has_art[w]:
        side[side_label(w)] = max(side[side_label(w)], np.linalg.norm((VF[w] - VF[r]) - (ref_art[w] - ref_art[r])) * 1000)
res['wrist_rings'] = dict(ring_verts=int(len(wr_f)), crossing_edges=len(E), DISPLACEMENT_STEP_vs_hands_base_mm=float(sb), DISPLACEMENT_STEP_vs_ArtDir_forearm_side_only_mm=float(sa), per_side_vs_ArtDir={k: float(v) for k, v in side.items()},
                          note='merge-induced step is the change vs the hands base: the merge touches neither side of the wrist ring (hand side has no ArtDir counterpart: info only)')
print('wrist rings:', res['wrist_rings'])
# --------------------------------------------------------------- POSITION_STEP: do pins stay pins?
def posd(final_idx, other_pos): return float(np.abs(VF[final_idx] - other_pos).max() * 1000)
T5V = T5['V'].astype(np.float64); ARV = ARMS['V'].astype(np.float64); F3V = F3['V'].astype(np.float64)
from collections import defaultdict
h3 = defaultdict(list)
for i, p in enumerate(F3V[:12421]): h3[tuple(np.float32(p))].append(i)
def vs_F3_lower(final_idx):
    worst = 0.0
    for i in final_idx:
        k = tuple(np.float32(VF[i]))
        if k in h3: continue
        worst = max(worst, float(np.linalg.norm(F3V[:12421] - VF[i], axis=1).min()))
    return worst * 1000
pos = {}
neck_f = fin_of_art(neck_a); arm_f = fin_of_art(arm_junction_a); floor_f = fin_of_art(floor_a)
collar_f = newidx[D['ring_base_idx'].astype(np.int64)]
pos['neck_shoulder_ring'] = dict(vs_FORM5_candidate_mm=posd(neck_f, T5V[neck_a]), vs_F3_lower_body_mm=vs_F3_lower(neck_f), vs_ArtDir_original_mm=posd(neck_f, VA[neck_a]))
pos['collar_ring_30'] = dict(vs_F3_ring_mm=posd(collar_f, D['ring_pos'].astype(np.float64)), vs_ArtDir_original_mm=posd(collar_f, VA[f2a[D['ring_base_idx'].astype(np.int64)]]), vs_hands_base_mm=posd(collar_f, VB[D['ring_base_idx'].astype(np.int64)]))
pos['armpit_border_ring'] = dict(vs_FORM5_candidate_mm=posd(arm_f, T5V[arm_junction_a]), vs_ArtDir_original_mm=posd(arm_f, VA[arm_junction_a]), vs_F3_lower_body_mm=vs_F3_lower(arm_f))
pos['arm_pins_107'] = dict(vs_arms_candidate_mm=posd(pins_f, ARV[pins_l]), vs_ArtDir_original_mm=posd(pins_f, VA[lv['final_to_base'][pins_l]]))
pos['wrist_rings_36'] = dict(vs_arms_candidate_mm=posd(wr_f, ARV[hd['ring'].astype(np.int64)]), vs_hands_candidate_mm=posd(wr_f, VB[hd['ring'].astype(np.int64)]))
pos['leg_top_floor_ring'] = dict(vs_FORM5_candidate_mm=posd(floor_f, T5V[floor_a]), vs_ArtDir_original_mm=posd(floor_f, VA[floor_a]), vs_hands_base_mm=posd(floor_f, VB[vm[floor_a]]))
res['POSITION_STEP'] = pos
print('\n--- POSITION_STEP (mm):'); [print(f'  {k:22s}', {a: round(b, 6) for a, b in v.items()}) for k, v in pos.items()]
# --------------------------------------------------------------- neck-region geometry context (not a gate): FORM5 border vs collar ring heights, band between them
zn = VF[neck_f, 2]; zc = VF[collar_f, 2]
res['neck_geometry'] = dict(FORM5_neck_ring_z_range=[float(zn.min()), float(zn.max())], collar_ring_z_range=[float(zc.min()), float(zc.max())],
                            original_untouched_band_between_m=float(zc.min() - zn.max()), verts_in_band=int(((VF[:, 2] > zn.max()) & (VF[:, 2] < zc.min())).sum()))
print('neck geometry:', res['neck_geometry'])
json.dump(res, open('data/seams.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))

# --------------------------------------------------------------- save rings + provenance labels for the proof renderer
prov = np.zeros(len(VF), np.int8)                       # 0 original ArtDir, 1 FORM5 zone interior, 2 arms zone, 3 hand shells, 4 limbs legs/feet moved, 5 head (F3), 6 FORM5 border ring, 7 other limbs-new
hand_b = np.zeros(nb, bool); hand_b[hd['slots'].astype(np.int64)] = True; hand_b[22419:] = True
legm = lv['leg_moved_base'].astype(bool)
for i in range(len(VF)):
    if i >= nkeep: prov[i] = 5; continue
    b = base_of_final[i]; a = f2a[b]
    if hand_b[b]: prov[i] = 3
    elif a < 0: prov[i] = 7
    elif border[a]: prov[i] = 6
    elif zone[a]: prov[i] = 1
    elif a in arm_zone_set: prov[i] = 2
    elif legm[a]: prov[i] = 4
np.savez('data/rings_final.npz', neck=neck_f, armpit=arm_f, floor=floor_f, collar=collar_f, pins=pins_f, wrist=wr_f, prov=prov)
print('saved rings_final.npz; provenance counts', dict(collections.Counter(prov.tolist())))
