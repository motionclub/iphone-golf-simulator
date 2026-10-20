"""Build the portable merge delta (hands base -> FULL staged).  ./py.sh tools/make_full_delta.py -> export/full_merge_delta.npz
Pure numpy; inputs are dumps of the immutable start copies + the stage-1 vmap.  The replay script (export/merge_full_delta.py) consumes ONLY this file,
the hands-base blend and the F3 blend (Face_F object + its materials)."""
import numpy as np, json, collections, hashlib, subprocess
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
A = np.load('data/artdir_body.npz'); B = np.load('data/base_body.npz'); F = np.load('data/f3_body.npz')
vm = np.load('data/vmap_artdir_to_base.npz')['base_to_final'].astype(np.int64)
dz = np.load('start/torso_form5_delta.npz'); c7 = np.load('start/chat7_torso_delta.npz')
VB = B['V']; NB = len(VB)
# ---------------- step 1: retire chat 7
c7_idx = vm[c7['moved_idx']]
# ---------------- step 2: FORM5 torso delta in base order (+ the stock script's custom-normal weight vector, same lines)
idx = dz['moved_idx'].astype(np.int64); tidx = vm[idx]
wo = dz['cn_vertex_weight'].astype(np.float64)
wt = np.zeros(NB); wt[tidx] = wo[idx]                                    # apply_mask is all-True after the retire step (0 conflicts)
allw = np.nonzero(wo > 0)[0]; ta = vm[allw]; ok = ta >= 0
extra = ta[ok]; keep = wt[extra] == 0; wt[extra[keep]] = wo[allw[ok]][keep]
# ---------------- step 3: head graft
ZC = 0.5 * (1.4053155 + 1.4055792)
old_head = np.sort(vm[np.nonzero(A['V'][:, 2] > ZC)[0]])
assert (old_head >= 0).all() and set(old_head.tolist()) == set(np.nonzero(VB[:, 2] > ZC)[0].tolist())
NLOW = 12421                                                             # F3 Body_F: indices < NLOW are collar ring + everything below (== ArtDir lower body)
fls, flt, fcv = F['loop_start'], F['loop_total'], F['corner_verts']
isHeadV = np.arange(len(F['V'])) >= NLOW
used_f3 = np.zeros(len(F['V']), bool); used_f3[fcv] = True
orphans = np.nonzero(~used_f3)[0]; assert (orphans >= NLOW).all()                 # F3 Body_F carries 460 unreferenced vertices inside the two eye openings (no face/edge/group uses them)
head_ids = np.nonzero(isHeadV & used_f3)[0]
loc = -np.ones(len(F['V']), np.int64); loc[head_ids] = np.arange(len(head_ids))
face_head = np.add.reduceat(isHeadV[fcv].astype(np.int64), fls) > 0
hf = np.nonzero(face_head)[0]
ring_f3 = np.unique(np.concatenate([fcv[fls[f]:fls[f] + flt[f]] for f in hf])); ring_f3 = ring_f3[ring_f3 < NLOW]
assert len(ring_f3) == 30
# base vertex at the identical position (retained base verts only, must be unique)
keepv = np.ones(NB, bool); keepv[old_head] = False
H = collections.defaultdict(list)
for i in np.nonzero(keepv)[0]: H[tuple(VB[i])].append(int(i))
ring_base = np.array([H[tuple(F['V'][r])][0] if len(H[tuple(F['V'][r])]) == 1 else -1 for r in ring_f3])
assert (ring_base >= 0).all(), 'collar ring vertex has no unique counterpart in the base'
ring_lookup = -np.ones(len(F['V']), np.int64); ring_lookup[ring_f3] = np.arange(30)
# head loops in F3 face order
hl_start = []; hl_total = []; refs = []; uv = []; cn = []; mats = []; pos = 0
for f in hf:
    s, t = fls[f], flt[f]
    hl_start.append(pos); hl_total.append(t); pos += t
    for k in range(t):
        v = int(fcv[s + k])
        refs.append(int(loc[v]) if v >= NLOW else -(int(ring_lookup[v]) + 1))
    uv.append(F['uv'][s:s + t]); cn.append(F['custom_normal_i16'][s:s + t]); mats.append(F['material_index'][f])
head_V = F['V'][head_ids].astype(np.float32)
vgn = [str(x) for x in F['vg_names']]; W = F['vg_weights']
vg_off = [0]; vg_idx = []; vg_w = []
for g in range(len(vgn)):
    m = np.nonzero(W[g] > 0)[0]; assert (m >= NLOW).all() and used_f3[m].all()
    vg_idx.append(loc[m]); vg_w.append(W[g][m]); vg_off.append(vg_off[-1] + len(m))
out = dict(format_version=np.int32(1), base_vertex_count=np.int32(NB),
    base_sha256=np.array(sha('start/base_hands_candidate.blend')), f3_sha256=np.array(sha('start/F3_head_STAGED.blend')),
    form5_delta_sha256=np.array(sha('start/torso_form5_delta.npz')), chat7_delta_sha256=np.array(sha('start/chat7_torso_delta.npz')),
    c7_idx=c7_idx.astype(np.int32), c7_co_in_base=c7['new_co'].astype(np.float32), c7_co_original=c7['start_co'].astype(np.float32),
    t_idx=tidx.astype(np.int32), t_start=dz['start_co'].astype(np.float32), t_new=dz['new_co'].astype(np.float32), cn_weight=wt,
    cut_z=np.float64(ZC), old_head_idx=old_head.astype(np.int32), ring_base_idx=ring_base.astype(np.int32), ring_f3_idx=ring_f3.astype(np.int32), ring_pos=F['V'][ring_f3].astype(np.float32),
    head_V=head_V, head_f3_idx=head_ids.astype(np.int32), orphans_dropped_f3_idx=orphans.astype(np.int32), head_loop_start=np.array(hl_start, np.int32), head_loop_total=np.array(hl_total, np.int32), head_corner_ref=np.array(refs, np.int32),
    head_face_mat=np.array(mats, np.int8), head_uv=np.concatenate(uv).astype(np.float32), head_cn_raw=np.concatenate(cn).astype(np.int16),
    material_names=np.array(['Base_Grey_F', 'Skin_F']), vg_names=np.array(vgn), vg_offsets=np.array(vg_off, np.int32),
    vg_head_local_idx=np.concatenate(vg_idx).astype(np.int32), vg_weights=np.concatenate(vg_w).astype(np.float32))
np.savez_compressed('export/full_merge_delta.npz', **out)
print('delta written: c7', len(c7_idx), ' torso', len(tidx), ' old head verts', len(old_head), ' ring', len(ring_base), ' head verts', len(head_V), ' head faces', len(hf), ' head loops', len(refs))
print('final verts', int(keepv.sum()) + len(head_V), ' F3 orphan verts dropped:', len(orphans))
print('SHA delta', sha('export/full_merge_delta.npz'))
