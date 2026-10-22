"""R5 v2: delete / flip ONE up-facing polygon of a collision mesh that holds no signature grid point, whose vertices all stay
on other up faces, and with NO other collision surface under it (a real fall-through hole). Writes mut/hole_NN_rt_hole_*.blend/.fbx."""
import sys, json, math, os, importlib.util
sys.dont_write_bytecode = True
import numpy as np, bpy, bmesh
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
RG=REPO+"/work/postcard-look/review_gates"
spec=importlib.util.spec_from_file_location("plv", REPO+"/blender/scripts/postcard_look_verify.py"); V=importlib.util.module_from_spec(spec); spec.loader.exec_module(V)
h=int(sys.argv[sys.argv.index("--")+1]); tag=f"{h:02d}"
POS=f"{RG}/st/hole_{tag}_pos.blend"
SIG=json.load(open(f"{REPO}/work/postcard-look/baseline_signature/hole_{tag}.json")); g=SIG["grid"]
man=[]
def pick():
    bpy.ops.wm.open_mainfile(filepath=POS, load_ui=False)
    C=V.st_ctx(h, {}); S=V.Snap("blend", C)
    best=None
    for ob in V.coll_objects(S):
        me=ob.data
        mw=np.array(ob.matrix_world)
        others=[o for o in V.coll_objects(S) if o.name!=ob.name]
        R=V.Rays(S, others)
        upp=[p for p in me.polygons if (mw[:3,:3]@np.array(p.normal))[2]>0.5]
        cnt={}
        for p in upp:
            for v in p.vertices: cnt[v]=cnt.get(v,0)+1
        for p in upp:
            if any(cnt[v]<2 for v in p.vertices): continue
            W=np.array([mw[:3,:3]@np.array(me.vertices[v].co)+mw[:3,3] for v in p.vertices])
            P=W[:,:2]; lo,hi=P.min(0),P.max(0)
            ins=False
            for i in range(math.ceil((lo[0]-g["x0"])/g["step"]), math.floor((hi[0]-g["x0"])/g["step"])+1):
                for j in range(math.ceil((lo[1]-g["y0"])/g["step"]), math.floor((hi[1]-g["y0"])/g["step"])+1):
                    if V.pip(P,np.array([g["x0"]+i*g["step"]]),np.array([g["y0"]+j*g["step"]]))[0]: ins=True
            if ins: continue
            c=W.mean(0)
            if R.cast(float(c[0]),float(c[1])) is not None: continue
            a=p.area
            if best is None or a>best[2]: best=(ob.name,p.index,a,c)
    return best
b=pick()
print("PICK", b, flush=True)
if b:
    for mode in ("delete","flip"):
        bpy.ops.wm.open_mainfile(filepath=POS, load_ui=False)
        ob=bpy.data.objects[b[0]]
        bm=bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
        f=bm.faces[b[1]]
        if mode=="delete": bmesh.ops.delete(bm, geom=[f], context="FACES_ONLY")
        else: f.normal_flip()
        bm.to_mesh(ob.data); bm.free(); ob.data.update()
        nm=f"rt_collider_hole_{mode}"
        blend=f"{RG}/mut/hole_{tag}_{nm}.blend"; fbx=f"{RG}/mut/hole_{tag}_{nm}.fbx"
        bpy.ops.wm.save_as_mainfile(filepath=blend, copy=True); V.st_export(h, fbx)
        man.append(dict(name=nm, expect=["PLAY_SURFACE_TOPS","PLAY_SURFACE_GRID"], kind="redteam",
             note=f"{b[0]} polygon {b[1]} ({b[2]:.2f} m2 at {b[3][0]:.1f},{b[3][1]:.1f}; nothing collides under it) {'deleted' if mode=='delete' else 'flipped (single-sided collider)'}; vertices kept -> GroundHeight misses there", blend=blend, fbx=fbx, look=f"{RG}/st/Look"))
json.dump(man, open(f"{RG}/mut/hole_{tag}_manifest_hole.json","w"), indent=1)
