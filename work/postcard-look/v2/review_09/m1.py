import bpy, bmesh, numpy as np, collections, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get()
def welded(me):
    v=np.array([tuple(x.co) for x in me.vertices]); 
    if len(v)==0: return 0
    return len(set(map(tuple,np.round(v/1e-4).astype(int))))
# ---- rocks
rock=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('ROCK_','DRESS_'))]
print('rock/dress objs',len(rock))
meshes={}
for o in rock: meshes[o.data.name]=o.data
rows=[]
for n,me in meshes.items():
    rows.append((welded(me),len(me.polygons),n))
rows.sort()
print('min welded', rows[:6])
print('mesh count',len(rows))
small=[r for r in rows if r[0]<60]; print('meshes <60 welded', small)
# scale
bad=[];mx=0;mn=9;worst=0
for o in rock:
    m=np.array(o.matrix_world)[:3,:3]
    s=np.linalg.svd(m,compute_uv=False)
    mx=max(mx,s.max());mn=min(mn,s.min());worst=max(worst,s.max()/s.min())
    if s.min()<0.5-1e-3 or s.max()>2+1e-3 or s.max()/s.min()>2: bad.append((o.name,s.round(2).tolist()))
print('scale range',mn,mx,'worst ratio',worst,'bad',len(bad),bad[:5])
# also parent chain / scale on dims relative to mesh? check object.scale vs matrix
# face count per rock object
face=collections.Counter()
for o in rock:
    face[len(o.data.polygons)]+=1
print('max faces', max(face), sorted(face.items())[-3:])
# families
fams=collections.Counter(re_ for re_ in [o.data.name for o in rock]); print(len(fams),'mesh datablocks; most used',fams.most_common(5))
