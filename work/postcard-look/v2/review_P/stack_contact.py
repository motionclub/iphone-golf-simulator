import sys, os, math, collections
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import postcard_props_lib as PL
hole=os.environ.get("HOLE","09"); seed=int(os.environ.get("SEED","5"))
bpy.ops.wm.open_mainfile(filepath=R + f"/work/postcard-look/baseline/blender/hole_{hole}.blend")
out=PL.swap_legacy_rocks(None, basalt=(hole=="10"), seed=seed)
bpy.context.view_layer.update()
g=collections.defaultdict(list)
for o in out: g[o["lk_swap"]].append(o)
def bvh(o):
    me=o.data; me.calc_loop_triangles(); mw=o.matrix_world
    return BVHTree.FromPolygons([tuple(mw@v.co) for v in me.vertices],[tuple(lt.vertices) for lt in me.loop_triangles])
multi={k:v for k,v in g.items() if len(v)>1}
print("hole",hole,"multi-instance groups",len(multi),"of",len(g))
disc=0;total=0;worst=[]
for k,v in multi.items():
    # connectivity: each instance must overlap/touch another (distance < 0.15m) -> graph connected
    bv=[bvh(o) for o in v]
    n=len(v); adj=[[] for _ in range(n)]
    for i in range(n):
        for j in range(i+1,n):
            if bv[i].overlap(bv[j]): adj[i].append(j); adj[j].append(i); continue
            # nearest distance via sampling verts
            d=9e9
            for vv in list(v[i].data.vertices)[::3]:
                p=v[i].matrix_world@vv.co
                h=bv[j].find_nearest(p)
                if h[0] is not None: d=min(d,h[3])
            if d<0.3: adj[i].append(j); adj[j].append(i)
    seen={0}; st=[0]
    while st:
        a=st.pop()
        for b in adj[a]:
            if b not in seen: seen.add(b); st.append(b)
    total+=1
    if len(seen)<n: disc+=1; worst.append((k,[o.name for o in v]))
print("groups with a disconnected (floating) piece:",disc,"/",total,worst[:5])
for k,v in list(multi.items()):
    if not k.startswith("ROCK_STACK"): continue
    print(k)
    for o in v:
        me=o.data; pts=np.array([list(o.matrix_world@vv.co) for vv in me.vertices])
        print("   ",o.name,"loc",np.round(o.matrix_world.translation,1),"scale",np.round(o.matrix_world.to_scale(),2),"zmin %.2f zmax %.2f"%(pts[:,2].min(),pts[:,2].max()))
