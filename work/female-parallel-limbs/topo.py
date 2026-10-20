import bpy, bmesh, numpy as np
b=bpy.data.objects['Body_F']; me=b.data
v=np.array([tuple(x.co) for x in me.vertices])
print('mats',[m.name for m in me.materials])
mi=np.array([p.material_index for p in me.polygons])
print('poly mat counts',np.bincount(mi))
# vertices touched by each material
for k,m in enumerate(me.materials):
    idx=set()
    for p in me.polygons:
        if p.material_index==k: idx.update(p.vertices)
    idx=np.array(sorted(idx),dtype=int)
    if not len(idx): continue
    print(k,m.name,len(idx),v[idx].min(0).round(3),v[idx].max(0).round(3))
# hand zone: |x|>0.255 & z<0.93 ; foot zone z<0.09
for name,mask in(('hand',(np.abs(v[:,0])>0.255)&(v[:,2]<0.93)&(v[:,2]>0.7)),('foot',v[:,2]<0.10)):
    print(name,mask.sum(),v[mask].min(0).round(3),v[mask].max(0).round(3))
# wrist/ankle ring: scan slices
for z in [0.95,0.93,0.91,0.9,0.89,0.88,0.87,0.86,0.85,0.84,0.83,0.82,0.80]:
    m=(np.abs(v[:,2]-z)<0.004)&(v[:,0]>0.25)
    print('arm z',z,m.sum(),v[m][:,0].min().round(3) if m.sum() else '',v[m][:,0].max().round(3) if m.sum() else '')
for z in [0.14,0.12,0.10,0.09,0.08,0.07,0.06,0.05,0.04,0.03,0.02,0.01,0.0]:
    m=(np.abs(v[:,2]-z)<0.004)&(v[:,0]>0)
    print('leg z',z,m.sum(), v[m].min(0).round(3), v[m].max(0).round(3))
