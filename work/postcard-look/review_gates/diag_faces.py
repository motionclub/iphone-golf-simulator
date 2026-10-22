import sys, json, math, importlib.util
sys.dont_write_bytecode = True
import numpy as np, bpy, bmesh
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec=importlib.util.spec_from_file_location("plv", REPO+"/blender/scripts/postcard_look_verify.py"); V=importlib.util.module_from_spec(spec); spec.loader.exec_module(V)
h=int(sys.argv[sys.argv.index("--")+1]); tag=f"{h:02d}"
bpy.ops.wm.open_mainfile(filepath=f"{REPO}/work/postcard-look/review_gates/st/hole_{tag}_pos.blend", load_ui=False)
SIG=json.load(open(f"{REPO}/work/postcard-look/baseline_signature/hole_{tag}.json")); g=SIG["grid"]
C=V.st_ctx(h, {}); S=V.Snap("blend", C)
for ob in V.coll_objects(S):
    w=S.wld(ob); up=(w["N"][:,2]>0.5)&(w["A"]>1e-9)
    T=w["T"][up]; W=w["W"]
    # vertex share count among up tris
    cnt=np.bincount(T.ravel(), minlength=len(W))
    nogrid=0; shared=0; areas=[]
    for t in T:
        P=W[t][:, :2]; lo,hi=P.min(0),P.max(0)
        i0,i1=math.ceil((lo[0]-g["x0"])/g["step"]), math.floor((hi[0]-g["x0"])/g["step"])
        j0,j1=math.ceil((lo[1]-g["y0"])/g["step"]), math.floor((hi[1]-g["y0"])/g["step"])
        ins=False
        for i in range(i0,i1+1):
            for j in range(j0,j1+1):
                if V.pip(P,np.array([g["x0"]+i*g["step"]]),np.array([g["y0"]+j*g["step"]]))[0]: ins=True
        if not ins:
            nogrid+=1
            if (cnt[t]>=2).all(): shared+=1; areas.append(0.5*abs(np.cross(P[1]-P[0],P[2]-P[0])))
    print(f"{ob.name}: up tris {len(T)}, area {w['A'][up].sum():.0f} m2, tris with no grid point {nogrid}, of those all-verts-shared {shared}, max area {max(areas) if areas else 0:.2f} m2, polys {len(ob.data.polygons)}")
