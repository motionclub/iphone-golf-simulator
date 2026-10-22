"""export/vmaps_full_merge.npz : all index maps between ArtDir, the hands base, F3 and the FULL staged Body_F.  ./py.sh tools/make_vmaps.py"""
import numpy as np, json
D = np.load('export/full_merge_delta.npz'); vmz = np.load('data/vmap_artdir_to_base.npz'); vm = vmz['base_to_final'].astype(np.int64); f2a = vmz['final_to_base'].astype(np.int64)
F3 = np.load('data/f3_body.npz'); A = np.load('data/artdir_body.npz')
NB = 23247; old = D['old_head_idx'].astype(np.int64); keep_v = np.ones(NB, bool); keep_v[old] = False; newidx = np.cumsum(keep_v) - 1; nkeep = int(keep_v.sum())
nfinal = nkeep + len(D['head_V'])
base_to_final = np.where(keep_v, newidx, -1)
final_to_base = np.full(nfinal, -1, np.int64); final_to_base[:nkeep] = np.nonzero(keep_v)[0]
artdir_to_final = np.where(vm >= 0, base_to_final[np.maximum(vm, 0)], -1)                  # ArtDir idx -> final idx (-1: removed old head, removed SDF hand/foot verts)
final_to_artdir = np.full(nfinal, -1, np.int64); final_to_artdir[:nkeep] = f2a[final_to_base[:nkeep]]
f3_to_final = np.full(len(F3['V']), -1, np.int64)
f3_to_final[D['head_f3_idx']] = nkeep + np.arange(len(D['head_f3_idx']))                  # F3 head vertices (idx >= 12421) appended in F3 order, orphans dropped
f3_to_final[D['ring_f3_idx']] = newidx[D['ring_base_idx'].astype(np.int64)]               # the 30 collar-ring vertices = base ring vertices
np.savez_compressed('export/vmaps_full_merge.npz', artdir_to_base=vm.astype(np.int32), base_to_artdir=f2a.astype(np.int32), base_to_final=base_to_final.astype(np.int32), final_to_base=final_to_base.astype(np.int32),
                    artdir_to_final=artdir_to_final.astype(np.int32), final_to_artdir=final_to_artdir.astype(np.int32), f3_to_final=f3_to_final.astype(np.int32),
                    note=np.array('-1 = no counterpart. artdir_to_base: limbs vertex map (ArtDir 22,444 -> hands base 23,247). base_to_final: retained base verts keep their order (new = old - removed old-head verts below); the 10,023 old-head verts are -1. '
                                  'final idx >= 13,224 are F3 head verts (F3 order, 460 orphan verts dropped); the 30 collar-ring verts are base verts.'))
s = dict(artdir_verts=len(vm), artdir_mapped=int((vm >= 0).sum()), artdir_removed_by_limbs_chat=int((vm < 0).sum()), base_verts=NB, base_with_artdir_counterpart=int((f2a >= 0).sum()), base_without_artdir_counterpart=int((f2a < 0).sum()),
         base_retained_in_final=nkeep, base_old_head_removed=int((~keep_v).sum()), f3_head_verts_appended=int(len(D['head_f3_idx'])), f3_orphans_not_carried=int(len(D['orphans_dropped_f3_idx'])), final_verts=int(nfinal),
         f3_verts=len(F3['V']), f3_lower_body_verts_not_copied=12421 - 30, collar_ring_verts_shared=30)
print(json.dumps(s, indent=1)); json.dump(s, open('data/vmap_summary.json', 'w'), indent=1)
