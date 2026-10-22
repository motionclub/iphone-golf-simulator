import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
from mathutils import geometry as G
def uv_at(x,y):
    ok,loc,n,pidx,ob,_=sc.ray_cast(dg,Vector((x,y,20)),Vector((0,0,-1)),distance=80)
    me=ob.data; poly=me.polygons[pidx]
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
    return ob.name,(l0*uvs[0][0]+l1*uvs[k][0]+l2*uvs[k+1][0], l0*uvs[0][1]+l1*uvs[k][1]+l2*uvs[k+1][1])
for (x,y) in [(0.5,3.2),(0.5,3.9),(2.0,3.0),(2.0,3.6),(-0.5,3.4),(-0.5,3.9)]:
    print("UV",x,y,uv_at(x,y))
