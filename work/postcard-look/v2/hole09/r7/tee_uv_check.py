import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
fw=bpy.data.objects['FAIRWAY']; tb=bpy.data.objects['TEE_BOX']
def tris(ob):
    me=ob.data; me.calc_loop_triangles()
    return me
me=tris(fw); uv=me.uv_layers[0].data
verts=[v.co.copy() for v in me.vertices]
tr=[(lt.vertices[:], lt.loops[:]) for lt in me.loop_triangles]
bvh=BVHTree.FromPolygons(verts,[t[0] for t in tr])
# tee box
me2=tb.data; uv2=me2.uv_layers[0].data
diffs=[]
for p in me2.polygons:
    for li in p.loop_indices:
        v=me2.vertices[me2.loops[li].vertex_index].co
        loc,n,idx,d=bvh.ray_cast(Vector((v.x,v.y,50)),Vector((0,0,-1)))
        if loc is None: continue
        vi,li3=tr[idx]
        a,b,c=[verts[i] for i in vi]
        # barycentric in xy
        T=np.array([[a.x-c.x,b.x-c.x],[a.y-c.y,b.y-c.y]]); r=np.array([v.x-c.x,v.y-c.y])
        l1,l2=np.linalg.solve(T,r); l3=1-l1-l2
        u_f=l1*np.array(uv[li3[0]].uv)+l2*np.array(uv[li3[1]].uv)+l3*np.array(uv[li3[2]].uv)
        u_t=np.array(uv2[li].uv)
        diffs.append((v.x,v.y,*(u_t-u_f)))
d=np.array(diffs)
print('n',len(d),'|dU| max',np.abs(d[:,2]).max(),'|dV| max',np.abs(d[:,3]).max())
print(d[np.argsort(-np.abs(d[:,2]))[:8]])
print('tee zrange', min(v.co.z for v in me2.vertices), max(v.co.z for v in me2.vertices))
print('fw z near', min(v.z for v in verts), max(v.z for v in verts))
