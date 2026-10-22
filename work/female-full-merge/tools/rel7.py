import numpy as np, collections
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
A=np.load('data/artdir_body.npz')['V']; B=np.load('data/base_body.npz')['V']
f5=np.load(f'{R}/work/female-torso-form5/export/torso_form5_delta.npz')
c7=np.load(f'{R}/work/female-parallel-torso/export/torso_delta.npz')
vm=np.load(f'{R}/work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz'); b2f=vm['base_to_final']
border=f5['border_mask'].astype(bool); zone=f5['zone_mask'].astype(bool)
idx=f5['moved_idx']; inidx=np.zeros(len(A),bool); inidx[idx]=True
c7i=c7['moved_idx']; c7new=c7['new_co']; c7map=-np.ones(len(A),int); c7map[c7i]=np.arange(len(c7i))
bi=np.nonzero(border)[0]
print('FORM5 border verts', len(bi), ' in delta:', inidx[bi].sum())
# classify border ring: floor ring z~0.62; neck (z>1.3); arm junction else
z=A[bi,2]
kind=np.where(np.abs(z-0.62)<0.01,'floor',np.where(z>1.3,'neck/shoulder','arm-junction'))
print(collections.Counter(kind))
# c7-moved border verts
mb=[i for i in bi if c7map[i]>=0]
print('chat-7-moved border verts', len(mb))
d=np.array([np.linalg.norm(c7new[c7map[i]]-A[i]) for i in mb])*1000
kk=np.array([kind[list(bi).index(i)] for i in mb])
for k in ('floor','neck/shoulder','arm-junction'):
    m=kk==k
    if m.any(): print(f'   {k:14s} n={m.sum():3d}  disp mm: max {d[m].max():.3f} mean {d[m].mean():.3f}  >1mm:{(d[m]>1).sum()}  >0.001mm:{(d[m]>0.001).sum()}')
# arm zone pins etc
arms=np.load(f'{R}/work/female-arms-form2/export/arms_delta.npz')
pins_limbs=arms['pinned_idx_limbs_order']; zone_l=arms['zone_mask_limbs_order']
f2l=vm['final_to_base']  # limbs idx -> ArtDir idx
print('arms: zone verts', zone_l.sum(), ' pinned', len(pins_limbs), ' moved', len(arms['moved_idx_limbs_order']))
armzone_art=np.zeros(len(A),bool); 
art_of_zone=f2l[np.nonzero(zone_l)[0]]; art_of_zone=art_of_zone[art_of_zone>=0]; armzone_art[art_of_zone]=True
pin_art=f2l[pins_limbs]; pin_art=pin_art[pin_art>=0]
print('arm-zone verts (ArtDir idx) overlapping FORM5 zone:', (armzone_art&zone).sum(), ' overlapping FORM5 border:', (armzone_art&border).sum(), ' pins overlapping FORM5 border:', border[pin_art].sum(), ' pins overlapping FORM5 zone:', zone[pin_art].sum())
# adjacency: pins adjacent to FORM5 border?
