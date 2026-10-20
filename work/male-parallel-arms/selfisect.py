"""blender -b --python selfisect.py -- <coords.npy|base> : count self-intersecting triangle pairs among arm-zone triangles (non-adjacent)"""
import bpy, sys, numpy as np
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-arms/'
D=np.load(W+'data/mesh_start.npz'); T=D['T']
V=D['V'] if a[0]=='base' else np.load(a[0])
zone=np.load(W+'data/zone.npy')
sel=zone[T].any(1)
Ts=T[sel]
tree=BVHTree.FromPolygons([tuple(map(float,v)) for v in V],[tuple(map(int,t)) for t in Ts],epsilon=0.0)
pairs=tree.overlap(tree)
bad=[]
for i,j in pairs:
    if i>=j: continue
    s=set(Ts[i])&set(Ts[j])
    if s: continue
    bad.append((i,j))
# cluster location
res=dict(n_pairs=len(bad))
if bad:
    c=np.array([V[Ts[i]].mean(0) for i,j in bad]); res['centroid_min']=c.min(0).round(3).tolist(); res['centroid_max']=c.max(0).round(3).tolist()
    # count by side/region
    res['right']=int((c[:,0]>0).sum()); res['left']=int((c[:,0]<0).sum())
print('SELFISECT',a[0],res)
