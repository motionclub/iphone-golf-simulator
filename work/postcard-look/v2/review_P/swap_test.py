import sys, os, math, collections, json
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
import postcard_props_lib as PL
hole = os.environ.get("HOLE", "10"); seed = int(os.environ.get("SEED", "1"))
bpy.ops.wm.open_mainfile(filepath=R + f"/work/postcard-look/baseline/blender/hole_{hole}.blend")
# legacy world bboxes
leg = {}
for o in PL.legacy_rocks():
    me=o.data; co=np.empty(len(me.vertices)*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
    mw=o.matrix_world
    pts=np.array([list(mw@Vector(c)) for c in co])
    leg[o.name]=(pts.min(0),pts.max(0))
nleg=len(leg)
rep=[]
out=PL.swap_legacy_rocks(None, basalt=(hole=="10"), seed=seed, report=rep)
bpy.context.view_layer.update()
# independent scale stats
bad=0; mn=9; mx=0; mr=0
rows=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(("ROCK_","CLIFF_")) : continue
    if any(c.name==PL.LIB_COLLECTION for c in o.users_collection): continue
    s=o.matrix_world.to_scale(); s=[abs(v) for v in s]
    # shear check: R^T M should be diagonal
    M=o.matrix_world.to_3x3(); 
    mn=min(mn,min(s)); mx=max(mx,max(s)); r=max(s)/min(s); mr=max(mr,r)
    if min(s)<0.5-1e-3 or max(s)>2.0+1e-3 or r>2.0+1e-3: bad+=1
    # shear: column vectors orthogonal?
    c=[M.col[i].normalized() for i in range(3)]
    dots=max(abs(c[0].dot(c[1])),abs(c[0].dot(c[2])),abs(c[1].dot(c[2])))
    rows.append((o.name,o.data.name,s,dots))
maxshear=max(r[3] for r in rows)
# verts
vmin=min(PL.welded_vertex_count(o.data) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(("ROCK_","CLIFF_")) and not any(c.name==PL.LIB_COLLECTION for c in o.users_collection))
# floating/buried: for each swapped obj, world bbox z min vs legacy z min
fl=[];bu=[]
for o in out:
    me=o.data; co=np.empty(len(me.vertices)*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
    mw=o.matrix_world; P=np.array([list(mw@Vector(c)) for c in co])
    lg=leg.get(o["lk_swap"])
    if lg is None: continue
    dz=P.min(0)[2]-lg[0][2]
    if abs(dz)>1.0 and o.name.split(".")[0] not in ():
        (fl if dz>0 else bu).append((o.name,round(dz,2)))
print(f"HOLE {hole} seed {seed}: legacy {nleg} out {len(out)} scale {mn:.3f}..{mx:.3f} maxratio {mr:.3f} violations {bad} maxshear {maxshear:.4f} vmin {vmin}")
print(" floating>1m", len(fl), fl[:5], " buried>1m", len(bu), bu[:5])
print(collections.Counter(r[1] for r in rows).most_common(30))
