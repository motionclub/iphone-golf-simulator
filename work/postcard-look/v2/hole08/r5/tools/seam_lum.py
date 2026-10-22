"""albedo luminance just below / just above the tee-box front edge, sampled from the Look PNG at the real UVs. usage: Blender -b --python seam_lum.py -- BLEND"""
import sys, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools"); sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
import frame_variation as FV
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
from mathutils import geometry as G
def lum_at(x,y):
    ok,loc,n,pidx,ob,_=sc.ray_cast(dg,Vector((x,y,20)),Vector((0,0,-1)),distance=80)
    if not ok or not ob.name.startswith(("TEE_BOX","FAIRWAY","GREEN","TERRAIN")): return None, None
    me=ob.data; poly=me.polygons[pidx]
    m=me.materials[poly.material_index].name.split(".")[0]
    if m not in FV.TEX: return None, m
    lp=ob.matrix_world.inverted()@loc
    uvl=me.uv_layers.active.data
    vs=[me.vertices[me.loops[li].vertex_index].co for li in range(poly.loop_start,poly.loop_start+poly.loop_total)]
    uvs=[uvl[li].uv for li in range(poly.loop_start,poly.loop_start+poly.loop_total)]
    best=None
    for k in range(1,len(vs)-1):
        w_=G.barycentric_transform(lp,vs[0],vs[k],vs[k+1],Vector((0,0,0)),Vector((1,0,0)),Vector((0,1,0)))
        l1,l2=w_.x,w_.y; l0=1-l1-l2; mn=min(l0,l1,l2)
        if best is None or mn>best[0]: best=(mn,l0,l1,l2,k)
        if mn>=-1e-6: break
    _,l0,l1,l2,k=best
    u=l0*uvs[0][0]+l1*uvs[k][0]+l2*uvs[k+1][0]; v=l0*uvs[0][1]+l1*uvs[k][1]+l2*uvs[k+1][1]
    return float(FV.sample(FV.lum_tex(m),u,v)), ob.name
# seam: tee box boundary (ellipse-ish) front y~3.8 at x=0; walk the boundary points
import bmesh
tb=bpy.data.objects["TEE_BOX"]
bm=bmesh.new(); bm.from_mesh(tb.data)
bnd=sorted({(v.co.x,v.co.y) for e in bm.edges if len(e.link_faces)==1 for v in e.verts})
res=[]
OFFS=[0.1,0.2,0.3,0.45,0.6,0.8]
for (x,y) in bnd:
    if y<1.0: continue
    d=np.array([x,y]); d/= np.linalg.norm(d)
    a=[lum_at(x-d[0]*o,y-d[1]*o)[0] for o in OFFS]; b=[lum_at(x+d[0]*(o+0.38*0),y+d[1]*o)[0] for o in OFFS]
    a=[v for v in a if v is not None]; b=[v for v in b if v is not None]
    if len(a)<4 or len(b)<4: continue
    res.append((round(x,2),round(y,2),float(np.mean(a)),float(np.mean(b))))
for r in sorted(res): print("SEAM x %.2f y %.2f  tee(0.1-0.8m avg) %.0f  fairway %.0f  step %+.0f"%(r[0],r[1],r[2],r[3],r[3]-r[2]))
a=np.array([(r[2],r[3]) for r in res])
print("SEAMSTAT low-pass mean |step| %.1f  rms %.1f  max %.1f  n %d"%(np.abs(a[:,1]-a[:,0]).mean(), np.sqrt(((a[:,1]-a[:,0])**2).mean()), np.abs(a[:,1]-a[:,0]).max(), len(a)))
