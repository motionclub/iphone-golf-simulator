import bpy, sys, numpy as np, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import Counter
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
rng=np.random.default_rng(7)
V=[];F=[];INFO=[]
for o in bpy.data.objects:
    if o.type!='MESH' or o.name.startswith(('WATER_','LAVA','DRESS_PATH')): continue
    M=o.matrix_world; b=len(V); me=o.data
    V+=[tuple(M@v.co) for v in me.vertices]
    for p in me.polygons:
        vs=[b+i for i in p.vertices]
        mn=me.materials[p.material_index].name if p.material_index<len(me.materials) and me.materials[p.material_index] else '?'
        for k in range(1,len(vs)-1):
            F.append((vs[0],vs[k],vs[k+1])); INFO.append((o.name,mn))
bvh=BVHTree.FromPolygons(V,F)
V=np.array(V)
def front(o,d,maxd=200.0):
    cur=o
    for _ in range(12):
        h=bvh.ray_cast(cur,d,maxd)
        if h[0] is None: return None
        if h[1].dot(d)<0: return h
        cur=h[0]+d*1e-4
        maxd-=h[3]
    return None
ter=[o for o in bpy.data.objects if o.name.startswith('TERRAIN')][0]
M=ter.matrix_world; me=ter.data
PLAY=float(sys.argv[sys.argv.index("--")+2]) if len(sys.argv)>sys.argv.index("--")+2 else 6.0
# sample wall points: random points on non-top terrain faces
pts=[];nrm=[]
for p in me.polygons:
    n=M.to_3x3()@p.normal
    if n.z>0.5 or abs(n.z)>0.9: continue
    vs=[M@me.vertices[i].co for i in p.vertices]
    for _ in range(max(1,int(p.area/1.5))):
        w=rng.dirichlet(np.ones(len(vs)))
        q=sum((v*wi for v,wi in zip(vs,w)),Vector((0,0,0)))
        if 0.3<=q.z<=PLAY-0.0: pts.append(q); nrm.append(n.normalized())
print("wall sample points",len(pts))
views={'aerial':(25.0,30.0),'low':(12.0,1.7),'oblique':(40.0,15.0)}
res={k:Counter() for k in views}
bad_examples=[]
for k,(out,up) in views.items():
    for q,n in zip(pts,nrm):
        h2=Vector((n.x,n.y,0)).normalized() if (n.x or n.y) else None
        if h2 is None: continue
        cam=Vector((q.x,q.y,max(q.z+up,2.0)))+h2*out if k!='low' else Vector((q.x,q.y,q.z+up if False else 1.7))+h2*out
        d=(q-cam).normalized()
        # camera must see open air (no hit before): just cast and categorise first front hit
        h=front(cam,d)
        if h is None: res[k]['miss']+=1; continue
        nm,mn=INFO[h[2]]
        z=h[0].z
        cls=nm.rstrip('0123456789_.')
        if cls.startswith('TERRAIN'):
            vertical=abs(h[1].z)<0.7
            res[k][('TERRAIN',mn,'wall' if vertical else 'top')]+=1
            if mn=='LK_ROUGH' and vertical and z>0.3 and len(bad_examples)<8: bad_examples.append((k,tuple(round(c,2) for c in h[0]),round(z,2)))
        else:
            res[k][(cls,mn)]+=1
tot=0
for k in views:
    n=sum(res[k].values()); tot+=n
    print("--",k,n)
    for kk,v in res[k].most_common(8): print("   ",kk,v, "%.2f%%"%(100*v/n))
roughwall=sum(v for k in views for kk,v in res[k].items() if isinstance(kk,tuple) and kk[0]=='TERRAIN' and kk[1]=='LK_ROUGH' and kk[2]=='wall')
anyterrwall=sum(v for k in views for kk,v in res[k].items() if isinstance(kk,tuple) and kk[0]=='TERRAIN' and kk[2]=='wall')
print("TOTAL rays",tot,"first-hit on TERRAIN vertical LK_ROUGH:",roughwall,"%.2f%%"%(100*roughwall/tot),"; on any TERRAIN wall:",anyterrwall,"%.2f%%"%(100*anyterrwall/tot))
print("examples",bad_examples)
# z-histogram of TERRAIN wall hits is in examples; also materials of vertical terrain wall faces by z-band
Wm=Counter()
for p in me.polygons:
    n=M.to_3x3()@p.normal
    if n.z>0.5: continue
    zc=np.mean([ (M@me.vertices[i].co).z for i in p.vertices])
    mn=me.materials[p.material_index].name
    Wm[(mn,'z>=5.5' if zc>=5.5 else ('z>=5' if zc>=5 else 'z<5'))]+=p.area
print("terrain wall area by material/band",{k:round(v,1) for k,v in Wm.items()})
