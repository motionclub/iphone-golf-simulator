import numpy as np, sys, bpy
sys.path.insert(0,'.')
import loops, hand_sdf as H
me=bpy.data.objects['Body_M'].data
cv=np.empty(len(me.loops),np.int64); me.loops.foreach_get('vertex_index',cv); F=cv.reshape(-1,4)
np.save('faces.npy',F)
co=np.array([v.co[:] for v in me.vertices],float)
ef,ve=loops.build(F,len(co))
L=H.to_local(co,+1)
# candidate seed edges: edges whose midpoint is near given w levels on the right arm, edge roughly perpendicular to arm axis
res=[]
seen=set()
for (a,b),fs in ef.items():
    if len(fs)!=2: continue
    if co[a,0]<0.30 or co[b,0]<0.30: continue
    wa,wb=L[a,2],L[b,2]
    if not (-0.12<wa<0.02): continue
    if abs(wa-wb)>0.006: continue                 # horizontal-ish edge
    loop,closed=loops.walk_loop(a,b,F,ef,ve)
    if closed:
        key=frozenset(loop)
        if key in seen: continue
        seen.add(key)
        w=L[loop,2]; res.append((float(w.mean()),len(loop),float(w.std())))
res.sort()
for r in res: print(f'loop w_mean={r[0]:+.4f} len={r[1]:3d} w_std={r[2]:.4f}')
