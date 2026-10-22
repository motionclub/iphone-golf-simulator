import bpy, sys, numpy as np, math
sys.path.insert(0,"/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
def mat_masonry_joints(seed=1001, courses=8):
    rng_ = np.random.default_rng([seed, 1]); out=[]
    for k in range(courses):
        nb=int(rng_.integers(4,8)); w=rng_.uniform(0.6,1.4,nb); cb=np.concatenate([[0.0],np.cumsum(w)/w.sum()]); ph=float(rng_.random())
        out.append(sorted(((cb[i]-ph)%1.0) for i in range(nb)))
    return out
J=mat_masonry_joints()
cat={}
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(("DRESS_RUIN","DRESS_ARCH","DRESS_BLOCK")): continue
    me=o.data; uvl=me.uv_layers.active
    mw=np.array(o.matrix_world)[:3,:3]
    for p in me.polygons:
        if p.area<0.0002: continue
        uu=np.array([uvl.data[li].uv[0] for li in p.loop_indices]); vv=np.array([uvl.data[li].uv[1] for li in p.loop_indices])
        if uu.max()-uu.min()>0.2: continue
        vc=0.5*(vv.min()+vv.max()); jr=int(round(vc*8))%8; jf=round(vc*8)/8
        in_row= vv.min()>=jf-25/512-0.004 and vv.max()<=jf+23/512+0.004
        cross=False
        for jb in J[jr]:
            for sh in range(int(math.floor(uu.min()))-1,int(math.ceil(uu.max()))+2):
                if uu.min()-0.008<=jb+sh<=uu.max()+0.008: cross=True
        n=mw@np.array(p.normal); top=abs(n[2])>=0.75
        key=("top" if top else "side", "rowfail" if not in_row else "", "joint" if cross else "")
        c=cat.setdefault(key,[0,0.0]); c[0]+=1; c[1]+=p.area
for k,v in sorted(cat.items(), key=lambda kv:-kv[1][0]): print(k,v[0],round(v[1],2))
