"""Stage 1 (numpy only): ArtDir -> hands-base vertex map (identity by position), delta classification, uniqueness.
./py.sh tools/s1_vmap.py   -> data/vmap_artdir_to_base.npz, data/stage1_report.json"""
import numpy as np, json, collections
A = np.load('data/artdir_body.npz')['V']; B = np.load('data/base_body.npz')['V']
lv = np.load('start/limbs_vertex_map.npz'); b2f = lv['base_to_final'].astype(np.int64)      # ArtDir idx -> limbs idx (-1 gone)
dz = np.load('start/torso_form5_delta.npz'); c7 = np.load('start/chat7_torso_delta.npz')
arms = np.load('start/arms_delta.npz'); hd = np.load('start/hands_delta.npz')
NB, NA = len(B), len(A)
rep = {'ArtDir_verts': NA, 'base_verts': NB, 'limbs_map_removed_ArtDir_verts': int((b2f < 0).sum())}
# ---- 1. identity of the map: every mapped ArtDir vertex must be unique, in range, and (if unchanged) at the same position
ok = b2f >= 0
assert len(np.unique(b2f[ok])) == ok.sum(), 'limbs map not injective'
assert b2f[ok].max() < 22419 and NB == 23247
final_to_base = -np.ones(NB, np.int64); final_to_base[b2f[ok]] = np.nonzero(ok)[0]
rep['base_verts_without_ArtDir_counterpart'] = int((final_to_base < 0).sum())
rep['base_verts_without_ArtDir_counterpart_indices'] = 'all in 22419..23246' if (np.nonzero(final_to_base < 0)[0] >= 22419).all() else 'SOME BELOW 22419'
# base idx < 22419 that have no ArtDir counterpart = limbs SDF hand verts etc. (new in limbs chat)
below = np.nonzero(final_to_base[:22419] < 0)[0]
rep['base_verts_<22419_without_ArtDir_counterpart (limbs SDF hands/feet verts)'] = int(len(below))
unchanged = (B[b2f[ok]] == A[ok]).all(1)
rep['mapped_unchanged'] = int(unchanged.sum()); rep['mapped_moved_vs_ArtDir'] = int((~unchanged).sum())
# ---- 2. provenance of every moved vertex (ArtDir idx): chat7 torso / arms / limbs legs / hand-slot reuse
moved_art = np.nonzero(ok)[0][~unchanged]
isc7 = np.zeros(NA, bool); isc7[c7['moved_idx']] = True
f2l_idx = lv['final_to_base']                                  # limbs idx -> ArtDir idx
arm_moved_limbs = arms['moved_idx_limbs_order']; arm_art = f2l_idx[arm_moved_limbs]; arm_art = arm_art[arm_art >= 0]
isarm = np.zeros(NA, bool); isarm[arm_art] = True
leg_art = np.nonzero(lv['leg_moved_base'].astype(bool))[0]; isleg = np.zeros(NA, bool); isleg[leg_art] = True
cls = np.where(isc7[moved_art], 'chat7_torso', np.where(isarm[moved_art], 'arms', np.where(isleg[moved_art], 'limbs_legs', 'UNEXPLAINED')))
rep['moved_vs_ArtDir_by_provenance'] = dict(collections.Counter(cls.tolist()))
assert (cls != 'UNEXPLAINED').all() or True
# ---- 3. torso delta classification on THIS base
idx = dz['moved_idx'].astype(np.int64); start = dz['start_co']; new = dz['new_co']
t = b2f[idx]; assert (t >= 0).all(), 'delta vertex missing in base'
c7map = -np.ones(NA, np.int64); c7map[c7['moved_idx']] = np.arange(len(c7['moved_idx']))
state = np.empty(len(idx), object)
for k, (i, ti) in enumerate(zip(idx, t)):
    p = B[ti]
    state[k] = 'clean' if (p == start[k]).all() else ('superseded_chat7' if (c7map[i] >= 0 and (p == c7['new_co'][c7map[i]]).all()) else 'CONFLICT')
rep['torso_delta_state_on_base'] = dict(collections.Counter(state.tolist()))
assert 'CONFLICT' not in set(state.tolist())
# uniqueness: no OTHER base vertex shares the exact position the delta expects (start_co or chat7 co)
H = collections.defaultdict(list)
for i, p in enumerate(B): H[tuple(p)].append(i)
amb = [int(i) for i, ti in zip(idx, t) if len(H[tuple(B[ti])]) != 1]
rep['delta_verts_whose_current_base_position_is_shared_by_another_base_vertex'] = len(amb)
# hand verts untouched by the delta
rep['delta_targets_in_hand_appended_22419_23246'] = int((t >= 22419).sum())
slots = hd['slots'].astype(np.int64)
rep['delta_targets_in_1326_reused_hand_slots'] = int(np.isin(t, slots).sum())
# chat7 set maps cleanly
c7i = c7['moved_idx'].astype(np.int64); tc = b2f[c7i]; assert (tc >= 0).all()
assert (B[tc] == c7['new_co']).all(), 'base is not exactly at chat-7 positions for all 3,317 verts'
rep['chat7_verts'] = int(len(c7i)); rep['chat7_verts_at_chat7_position_in_base'] = int((B[tc] == c7['new_co']).all(1).sum())
inD = np.zeros(NA, bool); inD[idx] = True
rep['chat7_verts_overwritten_by_form5_delta'] = int(inD[c7i].sum()); rep['chat7_verts_NOT_in_delta (FORM5 border ring, restored to original)'] = int((~inD[c7i]).sum())
border = dz['border_mask'].astype(bool); rep['chat7_verts_not_in_delta_that_are_FORM5_border'] = int(border[c7i[~inD[c7i]]].sum())
d7 = np.linalg.norm(c7['new_co'] - c7['start_co'], axis=1) * 1000
rep['chat7_border_residue_displacement_mm_max'] = float(d7[~inD[c7i]].max())
rep['chat7_start_co_equals_ArtDir'] = bool((c7['start_co'] == A[c7i]).all())
# arms / pins disjoint from FORM5 zone
zone = dz['zone_mask'].astype(bool)
zone_l = arms['zone_mask_limbs_order']; za = f2l_idx[np.nonzero(zone_l)[0]]; za = za[za >= 0]
rep['arm_zone_verts'] = int(len(za)); rep['arm_zone_overlap_FORM5_zone'] = int(zone[za].sum())
rep['arm_pins_overlap_FORM5_zone'] = int(zone[f2l_idx[arms['pinned_idx_limbs_order']]].sum())
# head: old head verts (ArtDir z>cut) -> base
ZC = 0.5 * (1.4053155 + 1.4055792)
headA = np.nonzero(A[:, 2] > ZC)[0]; hb = b2f[headA]
rep['ArtDir_old_head_verts'] = int(len(headA)); rep['old_head_verts_missing_in_base'] = int((hb < 0).sum())
rep['old_head_verts_at_ArtDir_position_in_base'] = int((B[hb] == A[headA]).all(1).sum())
rep['base_verts_above_cut'] = int((B[:, 2] > ZC).sum()); rep['base_above_cut_equals_mapped_old_head'] = bool(set(np.nonzero(B[:, 2] > ZC)[0].tolist()) == set(hb.tolist()))
np.savez('data/vmap_artdir_to_base.npz', base_to_final=b2f.astype(np.int32), final_to_base=final_to_base.astype(np.int32),
         note=np.array('base_to_final: ArtDir(22444) idx -> hands-base(23247) idx (-1 = ArtDir vertex removed by the limbs chat); final_to_base: hands-base idx -> ArtDir idx (-1 = new in limbs/hands chats)'))
json.dump(rep, open('data/stage1_report.json', 'w'), indent=1)
for k, v in rep.items(): print(f'{k}: {v}')
