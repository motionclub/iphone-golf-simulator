import bpy, sys, numpy as np, re
A,B=sys.argv[sys.argv.index("--")+1:][:2]
PRE=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER','CART_PATH')
def load(p):
    bpy.ops.wm.open_mainfile(filepath=p)
    out={}
    for o in bpy.data.objects:
        if o.type!='MESH': continue
        me=o.data; M=o.matrix_world
        V=np.array([tuple(M@v.co) for v in me.vertices],dtype=np.float64)
        F=[tuple(p.vertices) for p in me.polygons]
        N=np.array([tuple((M.to_3x3()@p.normal)) for p in me.polygons])
        out[o.name]=(V,F,N)
    return out
a=load(A); b=load(B)
gA=sorted(n for n in a if n.startswith(PRE)); gB=sorted(n for n in b if n.startswith(PRE))
print("ground objs base",gA); 
print("ground objs look",gB)
print("same set:",gA==gB)
bad=0
for n in gA:
    if n not in b: print("MISSING",n); bad+=1; continue
    Va,Fa,Na=a[n]; Vb,Fb,Nb=b[n]
    same_v = Va.shape==Vb.shape and np.array_equal(Va,Vb)
    maxd = np.abs(Va-Vb).max() if Va.shape==Vb.shape else None
    sameF = Fa==Fb
    up=[i for i,nn in enumerate(Na) if nn[2]>0.5]
    upb=[i for i,nn in enumerate(Nb) if nn[2]>0.5]
    print(f"{n:22s} verts {len(Va)}/{len(Vb)} bitexact={same_v} maxd={maxd} faces_same={sameF} up_faces {len(up)}/{len(upb)}")
    if not (same_v and sameF): bad+=1
extra=[n for n in b if n not in a]
print("new objects:",len(extra),"; with ground prefix:",[n for n in extra if n.startswith(PRE)])
print("prefixes of new:",sorted(set(re.sub(r'[_.]?\d+$','',n) for n in extra)))
print("BAD",bad)
