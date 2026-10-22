import bpy, sys, numpy as np, math
A=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=A[0])
objs=[o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith("DRESS_RUIN") or o.name.startswith("DRESS_ARCH"))]
print("objs",[o.name for o in objs])
nv=[];plan=[];nang=[];uvres=[];uvarea=[]
tot=0
for o in objs:
    me=o.data
    me.calc_loop_triangles()
    try: me.calc_normals_split()
    except Exception: pass
    uv=me.uv_layers[0].data
    co=np.array([v.co[:] for v in me.vertices])
    for p in me.polygons:
        vi=list(p.vertices)
        pts=co[vi]
        n=np.array(p.normal)
        d=np.abs((pts-pts.mean(0))@n).max()
        nv.append(len(vi)); plan.append(d)
        # loop normals
        mx=0
        for li in p.loop_indices:
            ln=np.array(me.loops[li].normal)
            mx=max(mx,math.degrees(math.acos(max(-1,min(1,ln@n)))))
        nang.append(mx)
        # UV affine residual
        u=np.array([uv[li].uv[:] for li in p.loop_indices])
        ax=np.cross(n,[0,0,1.0]) if abs(n[2])<0.9 else np.array([1.0,0,0])
        ax/=np.linalg.norm(ax); bx=np.cross(n,ax)
        X=np.c_[pts@ax,pts@bx,np.ones(len(pts))]
        sol,res,_,_=np.linalg.lstsq(X,u,rcond=None)
        r=np.abs(X@sol-u).max()
        uvres.append(r)
        tot+=1
nv=np.array(nv);plan=np.array(plan);nang=np.array(nang);uvres=np.array(uvres)
print("faces",tot,"nverts hist",np.bincount(nv))
print("planarity max dist (mm): p50 %.2f p90 %.2f p99 %.2f max %.2f"%tuple(np.percentile(plan,[50,90,99,100])*1000))
print("loop-normal vs face normal deg: p50 %.2f p90 %.2f p99 %.2f max %.2f"%tuple(np.percentile(nang,[50,90,99,100])))
print("UV affine residual: p50 %.4f p90 %.4f p99 %.4f max %.4f"%tuple(np.percentile(uvres,[50,90,99,100])))
print("faces with loop-normal dev >3deg: %d (%.1f%%)"%((nang>3).sum(),100*(nang>3).mean()))
print("faces with planarity > 5mm: %d"%((plan>0.005).sum()))
