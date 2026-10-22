import bpy, numpy as np
from collections import Counter
for nm in ("ROCK_SKIN_00","ROCK_SKIN_05","DRESS_CONE"):
    o=bpy.data.objects.get(nm)
    if o is None: print("no",nm); continue
    me=o.data
    print(nm, "verts",len(me.vertices),"polys",len(me.polygons),"mats",[m.name for m in me.materials],"props",list(me.keys()))
    c=Counter(len(p.vertices) for p in me.polygons); print(" sides per poly",dict(c))
    nz=np.array([p.normal.z for p in me.polygons]); print(" |nz|>0.5:", int((abs(nz)>0.5).sum()), "of", len(nz))
    uv=me.uv_layers.active; arr=np.empty(len(me.loops)*2); uv.data.foreach_get("uv",arr); arr=arr.reshape(-1,2)
    print(" uv range", arr.min(0), arr.max(0))
    # face widths
    ws=[]
    for p in me.polygons[:200]:
        vs=np.array([me.vertices[i].co for i in p.vertices])
        if abs(p.normal.z)<0.5:
            n=np.array([p.normal.x,p.normal.y,0]); n/=np.linalg.norm(n)+1e-9
            t=np.cross([0,0,1],n); s=vs@t; ws.append(s.max()-s.min())
    print(" side face widths: mean %.2f max %.2f"%(np.mean(ws),np.max(ws)))
    print(" bbox", [tuple(np.round(o.bound_box[i],1)) for i in (0,6)])
