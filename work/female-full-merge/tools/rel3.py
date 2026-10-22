import numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
A=np.load('data/artdir_body.npz')['V']; B=np.load('data/base_body.npz')['V']
f5=np.load(f'{R}/work/female-torso-form5/export/torso_form5_delta.npz')
c7=np.load(f'{R}/work/female-parallel-torso/export/torso_delta.npz')
print('c7 keys', c7.files)
for k in c7.files: print('  ',k,c7[k].shape)
vm=np.load(f'{R}/work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz'); b2f=vm['base_to_final']
idx=f5['moved_idx']; t=b2f[idx]; start=f5['start_co']; new=f5['new_co']
# chat-7 moved set and position
c7i=c7['moved_idx']; c7new=c7['new_co']; c7start=c7['start_co']
print('c7 moved', len(c7i), ' c7 start==ArtDir:', (c7start==A[c7i]).all())
c7map=-np.ones(len(A),int); c7map[c7i]=np.arange(len(c7i))
cls=np.zeros(len(idx),int)  # 0 clean(base==start), 1 superseded c7 (base==c7 new), 2 other
for k,(i,ti) in enumerate(zip(idx,t)):
    p=B[ti]
    if (p==start[k]).all(): cls[k]=0
    elif c7map[i]>=0 and (p==c7new[c7map[i]]).all(): cls[k]=1
    else: cls[k]=2
print('FORM5 delta verts by base state: clean', (cls==0).sum(), ' == chat-7 new position (superseded):', (cls==1).sum(), ' OTHER (real conflict):', (cls==2).sum())
oth=np.nonzero(cls==2)[0]
if len(oth):
    print(' other: z range', start[oth,2].min(), start[oth,2].max(), 'max |base-start| mm', (np.abs(B[t[oth]]-start[oth]).max(1)*1000).max())
    # is the base position close to c7 new?
# which c7 moved verts are in FORM5 zone/not in delta?
zone=f5['zone_mask'].astype(bool); border=f5['border_mask'].astype(bool)
inidx=np.zeros(len(A),bool); inidx[idx]=True
c7_in_zone=zone[c7i]; c7_in_delta=inidx[c7i]
print('c7 moved verts:', len(c7i), ' in FORM5 zone:', c7_in_zone.sum(), ' in FORM5 delta:', c7_in_delta.sum(), ' in FORM5 border:', border[c7i].sum(), ' outside zone:', (~c7_in_zone).sum())
# c7 verts in zone but NOT in delta (stay at c7 position unless reset)
nd=c7i[c7_in_zone & ~c7_in_delta]; print('c7-moved zone verts not moved by FORM5 delta:', len(nd))
if len(nd):
    d=np.abs(c7new[c7map[nd]]-A[nd]).max(1)*1000; print('   their c7 displacement mm: max', d.max(), ' >0.001:', (d>0.001).sum(), ' on border:', border[nd].sum())
no=c7i[~c7_in_zone]; print('c7-moved verts OUTSIDE FORM5 zone:', len(no))
if len(no):
    d=np.abs(c7new[c7map[no]]-A[no]).max(1)*1000; print('   max displacement mm', d.max(), ' z range', A[no,2].min(), A[no,2].max())
# base-moved verts overall classification vs ArtDir
ok=b2f>=0
mv=np.nonzero(ok)[0][~(B[b2f[ok]]==A[ok]).all(1)]
is_c7=np.zeros(len(A),bool); is_c7[c7i]=True
print('base-moved (vs ArtDir) verts', len(mv), ' of which chat-7-torso:', is_c7[mv].sum(), ' not chat-7:', (~is_c7[mv]).sum())
rest=mv[~is_c7[mv]]
print(' non-c7 moved z range', A[rest,2].min(), A[rest,2].max())
# of those, how many inside FORM5 zone?
print(' non-c7 moved verts inside FORM5 zone:', zone[rest].sum(), '  in delta:', inidx[rest].sum())
# c7 verts: does base == c7 new for all of them (i.e. c7 not further changed by arms etc.)?
tt=b2f[c7i]; okc=tt>=0
same7=(B[tt[okc]]==c7new[okc]).all(1)
print('c7 verts mapped:', okc.sum(), ' base==c7 new:', same7.sum(), ' base differs (changed again, e.g. arms pins/zone):', (~same7).sum())
np.savez('data/prov_tmp.npz', cls=cls)
