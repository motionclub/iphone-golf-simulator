import sys
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
PL.ensure_library()
for k in ["ROCK_WALL_BASALT_S","ROCK_WALL_BASALT_M","ROCK_WALL_BASALT_L","ROCK_WALL_BASALT_A","ROCK_BASALT_A"]:
    me=PL.library_object(k).data
    tops=[p for p in me.polygons if p.normal.z>0.8 and len(p.vertices)>=5]
    vert=[p for p in me.polygons if abs(p.normal.z)<0.4]
    A=sum(p.area for p in me.polygons)
    zs=sorted({round(max(me.vertices[v].co.z for v in p.vertices),1) for p in tops})
    # regular hexagon? check side lengths cv
    cvs=[]
    for p in tops:
        co=np.array([me.vertices[v].co[:] for v in p.vertices]); 
        d=np.linalg.norm(co-np.roll(co,1,0),axis=1); cvs.append(d.std()/d.mean())
    print(k,"tris/faces",len(me.polygons),"hex-ish tops",len(tops),"vert faces",len(vert),"vertArea%",round(100*sum(p.area for p in vert)/A),"top levels",len(zs),"side CV median",round(float(np.median(cvs)),2), "nverts per top",sorted({len(p.vertices) for p in tops}))
