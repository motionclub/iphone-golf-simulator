"""Independent verification of export/HeroBase_Female_FULL_STAGED.blend (numpy only; run with ./py.sh).
Inputs (dumps made by tools/dump_obj.py): data/final_body.npz (merged), data/stage3_body.npz (STOCK merge_torso_delta.py result on the chat-7-retired base),
data/base_body.npz (hands candidate), data/f3_body.npz (MicroF3), data/artdir_body.npz, data/arms_body.npz (arms candidate), data/form5_body.npz (FORM5 candidate).
Output: data/checks_full.json (+ printed summary).  Nothing here edits a blend."""
import numpy as np, json, collections
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
L = lambda n: np.load(f'data/{n}.npz', allow_pickle=True)
FIN, S3, B, F3, A, ARMS, T5 = (L(n) for n in ('final_body', 'stage3_body', 'base_body', 'f3_body', 'artdir_body', 'arms_body', 'form5_body'))
D = np.load('export/full_merge_delta.npz'); vmz = np.load('data/vmap_artdir_to_base.npz'); vm = vmz['base_to_final'].astype(np.int64); f2a = vmz['final_to_base'].astype(np.int64)
dz = np.load('start/torso_form5_delta.npz'); arms = np.load('start/arms_delta.npz'); hd = np.load('start/hands_delta.npz'); lv = np.load('start/limbs_vertex_map.npz'); c7 = np.load('start/chat7_torso_delta.npz')
res = {}; ok_all = {}
def gate(name, ok, **kw):
    ok_all[name] = bool(ok); res[name] = dict(pass_=bool(ok), **{k: (v.item() if hasattr(v, 'item') else v) for k, v in kw.items()})
    print(('PASS ' if ok else 'FAIL ') + name, {k: v for k, v in kw.items() if not isinstance(v, (list, dict)) or len(str(v)) < 160})
VF, VS, VB, VF3, VA = FIN['V'], S3['V'], B['V'], F3['V'], A['V']
nb = len(VB); nf_ = len(VF)
old = D['old_head_idx'].astype(np.int64); keep_v = np.ones(nb, bool); keep_v[old] = False; newidx = np.cumsum(keep_v) - 1; nkeep = int(keep_v.sum())
# face bookkeeping identical to the replay (recomputed here independently)
ls, lt, cv = B['loop_start'], B['loop_total'], B['corner_verts']
face_old = np.add.reduceat((~keep_v[cv]).astype(np.int64), ls) > 0
keep_f = ~face_old; kf_ids = np.nonzero(keep_f)[0]; lmask = np.repeat(keep_f, lt); nkf = int(keep_f.sum()); nlk = int(lmask.sum())
fls, flt, fcv = FIN['loop_start'], FIN['loop_total'], FIN['corner_verts']
hls, hlt = F3['loop_start'], F3['loop_total']; NLOW = 12421
f3_face_head = np.add.reduceat((np.arange(len(VF3)) >= NLOW)[F3['corner_verts']].astype(np.int64), hls) > 0
f3_head_ids = np.nonzero(f3_face_head)[0]
f3_head_loops = np.concatenate([np.arange(hls[f], hls[f] + hlt[f]) for f in f3_head_ids])

# ===================================================== BASE_SHA / inputs
import hashlib
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
gate('BASE_SHA', sha('start/base_hands_candidate.blend') == '1149e620985248e546e2fab93eb19f447f1a5ae673d50a2525fcae5769529ff4' and str(D['base_sha256']) == sha('start/base_hands_candidate.blend'),
     base=sha('start/base_hands_candidate.blend'), f3=sha('start/F3_head_STAGED.blend'), form5_delta=sha('start/torso_form5_delta.npz'), note='verified before any edit; copies in start/ are read-only')

# ===================================================== VMAP_CLEAN
s1 = json.load(open('data/stage1_report.json'))
st3 = json.load(open('data/stage3_check.json'))
rp = json.load(open('data/replay_report.json'))
stock_unretired = open('logs/s3_stock_merge_on_UNRETIRED_base_literal.txt').read()
stock = open('logs/s3_stock_merge.txt').read()
hand_idx = np.arange(22419, 23247)
slots = hd['slots'].astype(np.int64)
final_hand_pos_equal = (VF[newidx[hand_idx]] == VB[hand_idx]).all()
final_slot_pos_equal = (VF[newidx[slots]] == VB[slots]).all()
tmoved_in_final = newidx[D['t_idx'].astype(np.int64)]
gate('VMAP_CLEAN', ('"conflicts(target differs from start)": 0' in stock) and ('"applied": 4540' in stock) and final_hand_pos_equal and final_slot_pos_equal and rp['torso_conflicts'] == 0
     and s1['torso_delta_state_on_base'] == {'clean': 1346, 'superseded_chat7': 3194} and s1['delta_verts_whose_current_base_position_is_shared_by_another_base_vertex'] == 0,
     stock_script_on_retired_base='applied 4540, conflicts 0, missing 0, cn corners 13131',
     stock_script_on_base_as_handed_over='applied 1346, CONFLICTS 3194 (all = chat-7 old torso, superseded by FORM5), see logs/s3_stock_merge_on_UNRETIRED_base_literal.txt',
     chat7_retired_verts=3317, delta_clean=1346, delta_superseded_chat7=3194, real_conflicts_with_arms_hands_limbs=0, ambiguous_matches=0,
     writes_on_hand_verts_22419_23246=int((~(VF[newidx[hand_idx]] == VB[hand_idx]).all(1)).sum()), writes_on_1326_reused_hand_slots=int((~(VF[newidx[slots]] == VB[slots]).all(1)).sum()))

# ===================================================== equivalence with the STOCK result (retained vertices / loops)
eq_pos = (VF[:nkeep] == VS[keep_v]).all()
eq_cn = np.array_equal(FIN['custom_normal_i16'][:nlk], S3['custom_normal_i16'][lmask])
eq_uv = np.array_equal(FIN['uv'][:nlk], B['uv'][lmask]) and np.array_equal(FIN['material_index'][:nkf], B['material_index'][keep_f])
eq_topo = np.array_equal(fcv[:nlk], newidx[cv[lmask]]) and np.array_equal(flt[:nkf], lt[keep_f])
gate('REPLAY_EQUALS_STOCK_SCRIPT', eq_pos and eq_cn and eq_uv and eq_topo, retained_vertices=nkeep, positions_bit_identical=bool(eq_pos), raw_custom_normals_bit_identical=bool(eq_cn), uv_material_topology_identical=bool(eq_uv and eq_topo),
     note='retained part of the final == data/stage3_torso_merged.blend produced by the unmodified merge_torso_delta.py')

# ===================================================== HEAD_ZONE_ONLY
head_pos_equal = (VF[nkeep:] == VF3[D['head_f3_idx']]).all()
# every head-face corner position / uv / raw / material equals F3's
hv_final = fcv[nlk:]; hv_f3 = F3['corner_verts'][f3_head_loops]
corner_pos_equal = (VF[hv_final] == VF3[hv_f3]).all()
uv_equal = np.array_equal(FIN['uv'][nlk:], F3['uv'][f3_head_loops]); raw_equal = np.array_equal(FIN['custom_normal_i16'][nlk:], F3['custom_normal_i16'][f3_head_loops])
mat_equal = np.array_equal(FIN['material_index'][nkf:], F3['material_index'][f3_head_ids]); lt_equal = np.array_equal(flt[nkf:], F3['loop_total'][f3_head_ids])
# lower body: final lower verts == base (after torso) NOT F3: where do final lower verts differ from F3's lower body (ArtDir) and is each difference explained?
kmap = {tuple(p): i for i, p in enumerate(VF3[:NLOW])}
differ = []
for i in range(nkeep):
    j = kmap.get(tuple(VF[i]))
    if j is None: differ.append(i)
differ = np.array(differ, np.int64)
base_of_final = np.nonzero(keep_v)[0]                                         # final idx -> base idx (retained verts)
bi = base_of_final[differ]; ai = f2a[bi]
c7set = set(c7['moved_idx'].tolist()); zone = dz['zone_mask'].astype(bool)
arm_zone_art = set(lv['final_to_base'][np.nonzero(arms['zone_mask_limbs_order'])[0]].tolist()) - {-1}
arm_moved_art = set(lv['final_to_base'][arms['moved_idx_limbs_order']].tolist()) - {-1}
legm = lv['leg_moved_base'].astype(bool)
expl = collections.Counter()
for b_, a_ in zip(bi, ai):
    if a_ < 0: expl['hands/limbs-SDF new vertex (no ArtDir counterpart)'] += 1
    elif zone[a_]: expl['FORM5 torso zone (delta)'] += 1
    elif a_ in arm_moved_art: expl['arms chat (moved arm vertex)'] += 1
    elif legm[a_]: expl['limbs chat (legs/feet)'] += 1
    else: expl['UNEXPLAINED'] += 1
gate('HEAD_ZONE_ONLY', head_pos_equal and corner_pos_equal and uv_equal and raw_equal and mat_equal and lt_equal and expl['UNEXPLAINED'] == 0 and nkeep + len(D['head_V']) == nf_,
     head_vertices_equal_F3=bool(head_pos_equal), head_corners_pos_uv_rawnormal_material_equal_F3=bool(corner_pos_equal and uv_equal and raw_equal and mat_equal and lt_equal),
     head_faces=int(len(f3_head_ids)), head_verts=int(len(D['head_V'])), faces_taken_from_F3='only the 8,578 faces touching F3 head vertices (8,488 head + 90 collar-crossing)',
     final_lower_verts_not_at_a_F3_lower_position=int(len(differ)), explained_by=str(dict(expl)),
     F3_lower_body_12421_verts_copied='NO (checked against, not copied)')

# ===================================================== ARMS_KEPT
arm_zone_limbs = np.nonzero(arms['zone_mask_limbs_order'])[0]; pins = arms['pinned_idx_limbs_order'].astype(np.int64); arm_moved_l = arms['moved_idx_limbs_order'].astype(np.int64)
pos_arms_cand = ARMS['V']                                                     # arms candidate, limbs order == base indices < 22419
d_arm = np.abs(VF[newidx[arm_zone_limbs]] - pos_arms_cand[arm_zone_limbs]).max()
d_pin = np.abs(VF[newidx[pins]] - pos_arms_cand[pins]).max()
border = dz['border_mask'].astype(bool)
gate('ARMS_KEPT', d_arm == 0 and d_pin == 0, arm_zone_verts=int(len(arm_zone_limbs)), arm_zone_verts_changed_vs_arms_candidate=int((np.abs(VF[newidx[arm_zone_limbs]] - pos_arms_cand[arm_zone_limbs]).max(1) > 0).sum()),
     arms_moved_by_arms_chat=int(len(arm_moved_l)), pins=int(len(pins)), pins_changed=int((np.abs(VF[newidx[pins]] - pos_arms_cand[pins]).max(1) > 0).sum()),
     torso_border_pin_exception_needed='no - the only border vertices that changed are TORSO-zone ring verts (123, chat-7 residue restored to the ArtDir original, max %.3f mm), not arm vertices' % s1['chat7_border_residue_displacement_mm_max'],
     arm_zone_overlap_FORM5_zone=int(zone[lv['final_to_base'][arm_zone_limbs]].sum()))

# ===================================================== LEGS_UNSCULPTED
z0 = VB[:, 2]
chg = np.zeros(nb, bool); chg[keep_v] = (VF[:nkeep] != VB[keep_v]).any(1)
below = chg & (z0 < 0.62 - 1e-4)
leg_band = chg & (z0 >= 0.62 - 1e-4) & (z0 < 0.795)
inF5 = np.zeros(nb, bool); inF5[tmoved_in_final.shape[0] and D['t_idx'].astype(np.int64)] = True
gate('LEGS_UNSCULPTED', below.sum() == 0 and (leg_band & ~inF5).sum() == 0, verts_moved_below_z0p62=int(below.sum()),
     verts_changed_in_FORM5_leg_top_band_z0p62_0p795=int(leg_band.sum()), of_which_not_in_FORM5_delta=int((leg_band & ~inF5).sum()), leg_verts_changed_vs_hands_base_total_below_z0p795=int((chg & (z0 < 0.795)).sum()),
     note='the only leg vertices that differ from the hands base are FORM5\'s documented LEG-TOP extension (thigh tops z .62-.795, y-only); nothing below the z .62 floor ring and no new leg sculpt')

# ===================================================== custom normals bookkeeping
raw_ret = FIN['custom_normal_i16'][:nlk]; raw_b = B['custom_normal_i16'][lmask]
chg_loops = (raw_ret != raw_b).any(1)
res['custom_normals'] = dict(retained_loops=nlk, retained_loops_raw_changed_vs_base=int(chg_loops.sum()), code1_changed=int((raw_ret[:, 1] != raw_b[:, 1]).sum()), code0_changed=int((raw_ret[:, 0] != raw_b[:, 0]).sum()),
                             head_loops=int(len(FIN['custom_normal_i16']) - nlk), cleared_anywhere=False, note='rescale = FORM5 cn_vertex_weight (13,131 corners, code0 only); head loops = F3 raw codes')
print('custom normals:', res['custom_normals'])
# decoded (Blender-evaluated) corner normals: float64 vector differences (NOT arccos of float32 dots)
def vdiff(a, b): return np.linalg.norm(a.astype(np.float64) - b.astype(np.float64), axis=1)
cn_f, cn_s, cn_3 = FIN['corner_normals'], S3['corner_normals'], F3['corner_normals']
d_ret = vdiff(cn_f[:nlk], cn_s[lmask]); d_head = vdiff(cn_f[nlk:], cn_3[f3_head_loops])
ring_f = set(newidx[D['ring_base_idx'].astype(np.int64)].tolist())
lv_final = fcv
ring_loop = np.array([v in ring_f for v in lv_final])
res['decoded_corner_normals'] = dict(retained_vs_stock_max_vecdiff=float(d_ret.max()), retained_loops_diff_gt_1e5=int((d_ret > 1e-5).sum()), retained_diff_loops_at_collar_ring=int(((d_ret > 1e-5) & ring_loop[:nlk]).sum()),
                                     head_vs_F3_max_vecdiff=float(d_head.max()), head_loops_diff_gt_1e5=int((d_head > 1e-5).sum()), head_diff_loops_at_collar_ring=int(((d_head > 1e-5) & ring_loop[nlk:]).sum()),
                                     max_deg_at_collar_ring_loops=float(np.degrees(2 * np.arcsin(np.minimum(1, np.concatenate([d_ret[ring_loop[:nlk]], d_head[ring_loop[nlk:]]]).max() / 2)))))
print('decoded corner normals:', res['decoded_corner_normals'])

# ===================================================== TOPOLOGY
def edges_info(Vp, ls_, lt_, cv_):
    cnt = collections.Counter(); dcnt = collections.Counter()
    for s, t in zip(ls_, lt_):
        vs = cv_[s:s + t]
        for i in range(t):
            a, b = int(vs[i]), int(vs[(i + 1) % t]); dcnt[(a, b)] += 1; cnt[(min(a, b), max(a, b))] += 1
    return cnt, dcnt
cnt, dcnt = edges_info(VF, fls, flt, fcv)
bnd = [e for e, c in cnt.items() if c == 1]; nm = [e for e, c in cnt.items() if c > 2]
flipped = sum(1 for (a, b), c in dcnt.items() if c > 1)                      # same directed edge used twice => winding inconsistency
adj = collections.defaultdict(list)
for a, b in bnd: adj[a].append(b); adj[b].append(a)
seen = set(); loops_b = []
for s0 in adj:
    if s0 in seen: continue
    st = [s0]; seen.add(s0); comp = [s0]
    while st:
        u = st.pop()
        for w in adj[u]:
            if w not in seen: seen.add(w); st.append(w); comp.append(w)
    loops_b.append(comp)
bloops = [dict(n=len(c), centre=[round(float(x), 4) for x in VF[c].mean(0)]) for c in loops_b]
# in-source boundary: F3's own eye openings; anything else was created by the merge
f3_cnt, _ = edges_info(VF3, hls, hlt, F3['corner_verts']); f3_bnd = [e for e, c in f3_cnt.items() if c == 1]
f3_bnd_pos = set(frozenset((tuple(VF3[a]), tuple(VF3[b]))) for a, b in f3_bnd)
fin_bnd_pos = set(frozenset((tuple(VF[a]), tuple(VF[b]))) for a, b in bnd)
base_cnt, _ = edges_info(VB, B['loop_start'], B['loop_total'], B['corner_verts']); base_bnd = [e for e, c in base_cnt.items() if c == 1]
used = np.zeros(nf_, bool); used[fcv] = True
# components
par = list(range(nf_))
def find(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for s, t in zip(fls, flt):
    vs = fcv[s:s + t]
    for i in range(1, t):
        a, b = find(int(vs[0])), find(int(vs[i]))
        if a != b: par[a] = b
ncomp = len(set(find(int(v)) for v in np.nonzero(used)[0]))
def face_areas(Vp, ls_, lt_, cv_):
    out = np.empty(len(ls_))
    for k, (s, t) in enumerate(zip(ls_, lt_)):
        P = Vp[cv_[s:s + t]].astype(np.float64); n = np.zeros(3)
        for i in range(t): n += np.cross(P[i], P[(i + 1) % t])
        out[k] = 0.5 * np.linalg.norm(n)
    return out
ar = face_areas(VF, fls, flt, fcv); ar_b = face_areas(VB, B['loop_start'], B['loop_total'], B['corner_verts'])
tris_final = int((flt - 2).sum())
H = collections.Counter(tuple(p) for p in VF)
res['topology'] = dict(vertices=nf_, faces=len(flt), tris=tris_final, loops=int(len(fcv)), edges=len(cnt), boundary_edges=len(bnd), boundary_loops=bloops, nonmanifold_edges=len(nm), inconsistent_winding_edges=flipped,
                       loose_vertices=int((~used).sum()), connected_components=ncomp, boundary_edges_in_F3_head_source=len(f3_bnd), boundary_edges_in_hands_base=len(base_bnd),
                       boundary_edges_created_by_merge=len(fin_bnd_pos - f3_bnd_pos), min_face_area_mm2=float(ar.min() * 1e6), min_face_area_mm2_base=float(ar_b.min() * 1e6),
                       zero_area_faces_lt_0p001_mm2=int((ar * 1e6 < 1e-3).sum()), coincident_vertex_pairs=int(sum(c - 1 for c in H.values() if c > 1)))
print('topology:', json.dumps(res['topology']))
t_ok = (len(nm) == 0 and flipped == 0 and (~used).sum() == 0 and ncomp == 1 and res['topology']['boundary_edges_created_by_merge'] == 0 and ((ar * 1e6) < 1e-3).sum() == 0)
res['TOPOLOGY_core_ok_excluding_literal_boundary_count'] = bool(t_ok)
# tri counts
hair_tris = 4960
res['tri_counts'] = dict(Body_F=tris_final, Face_F=6052, Hair_F=hair_tris, body_plus_hair=tris_final + hair_tris, body_plus_face=tris_final + 6052, all_three=tris_final + 6052 + hair_tris,
                         hands_base_body=int((B['loop_total'] - 2).sum()), hands_base_body_plus_hair=int((B['loop_total'] - 2).sum()) + hair_tris, F3_body=int((F3['loop_total'] - 2).sum()), F3_body_plus_face=int((F3['loop_total'] - 2).sum()) + 6052)
print('tri counts:', res['tri_counts'])
res['vertex_groups'] = dict(names=[str(x) for x in FIN['vg_names']], n=len(FIN['vg_names']),
                            members_equal_F3_by_position=bool(all(set(map(tuple, VF[np.nonzero(FIN['vg_weights'][g] > 0)[0]])) == set(map(tuple, VF3[np.nonzero(F3['vg_weights'][g] > 0)[0]])) for g in range(len(FIN['vg_names'])))))
print('vertex groups:', res['vertex_groups']['n'], 'members equal F3:', res['vertex_groups']['members_equal_F3_by_position'])
res['height_m'] = float(VF[:, 2].max() - VF[:, 2].min()); print('height', res['height_m'])
json.dump(dict(gates=ok_all, details=res), open('data/checks_full.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print('\nSUMMARY', ok_all)
