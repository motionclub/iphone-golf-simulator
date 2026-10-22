import bpy, collections, numpy as np
YD=0.9144
c=collections.defaultdict(collections.Counter)
H={}
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith('PLANT_') and not o.name.startswith('PLANT_VINE'):
        t=o.matrix_world.translation
        if abs(t.x)<1e-6 and abs(t.y)<1e-6: continue
        d=t.y/YD
        pad='tee' if d<100 else ('mid' if d<260 else 'green')
        k=o.name.split('.')[0].replace('PLANT_','')
        c[pad][k]+=1
        H.setdefault(k,[]).append(o.dimensions.z)
for p in c: print(p,dict(c[p]))
for k,v in H.items(): print(k,'height max %.2f median %.2f'%(max(v),np.median(v)))
