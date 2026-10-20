import numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
A=np.load('data/artdir_body.npz')['V']; B=np.load('data/base_body.npz')['V']
dz=np.load(f'{R}/work/female-torso-form5/export/torso_form5_delta.npz')
print('delta keys', dz.files)
for k in dz.files: print(' ', k, dz[k].shape, dz[k].dtype)
vm=np.load(f'{R}/work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz')
print('vmap keys', vm.files, [(k, vm[k].shape) for k in vm.files])
b2f=vm['base_to_final']; print('vmap len', len(b2f), 'neg count', (b2f<0).sum(), 'final max', b2f.max())
idx=dz['moved_idx']; start=dz['start_co']; new=dz['new_co']
t=b2f[idx]; print('delta verts', len(idx), 'missing in limbs order', (t<0).sum())
same=(B[t]==start).all(1)
print('base == start_co (clean) :', same.sum(), '  base != start_co (conflict by script def):', (~same).sum())
# identity check of vmap vs positions: ArtDir pos == base pos for all vmapped verts that are mapped
ok=b2f>=0
eq=(B[b2f[ok]]==A[ok]).all(1)
print('vmapped ArtDir verts:', ok.sum(), ' at identical position in base:', eq.sum(), ' moved in base vs ArtDir:', (~eq).sum())
mv=np.nonzero(ok)[0][~eq]
print('moved verts (ArtDir idx) z-range', A[mv,2].min(), A[mv,2].max())
# classify moved verts by zone
zm=dz['zone_mask'] if 'zone_mask' in dz.files else None
print('zone_mask true', zm.sum() if zm is not None else None)
# moved in base but not in delta zone
inzone=np.zeros(len(A),bool); 
if zm is not None: inzone=zm.astype(bool)
print('base-moved verts inside FORM5 zone:', inzone[mv].sum(), ' outside:', (~inzone[mv]).sum())
# conflicts: which delta verts have base != start_co
cf=idx[~same]
print('conflict delta verts: n', len(cf), ' max |base-start| mm', (np.abs(B[t[~same]]-start[~same]).max(1)*1000).max())
