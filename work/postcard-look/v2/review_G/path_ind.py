import bpy, sys, numpy as np, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
PRE=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER','CART_PATH')
def bvh(pred):
    V=[];F=[]
    for o in bpy.data.objects:
        if o.type!='MESH' or not pred(o.name): continue
        M=o.matrix_world; b=len(V); V+=[tuple(M@v.co) for v in o.data.vertices]
        for p in o.data.polygons:
            vs=[b+i for i in p.vertices]
            for k in range(1,len(vs)-1): F.append((vs[0],vs[k],vs[k+1]))
    return BVHTree.FromPolygons(V,F), np.array(V)
gb,_=bvh(lambda n:n.startswith(PRE))
pb,PV=bvh(lambda n:n.startswith('DRESS_PATH'))
print("path verts",len(PV),"bbox",PV.min(0),PV.max(0))
dn=Vector((0,0,-1))
def top(b,x,y):
    h=b.ray_cast(Vector((x,y,20.0)),dn)
    return None if h[0] is None else h[0].z
ex=[]
for p in PV:
    g=top(gb,p[0],p[1])
    if g is not None: ex.append(p[2]-g)
ex=np.array(ex)
print("vertex z - collider-top: n %d max %.4f m min %.4f ; share >1.2cm %.3f%% ; vertices with ex>-0.02 max %.4f"%(len(ex),ex.max(),ex.min(),100*(ex>0.0121).mean(),ex[ex>-0.02].max()))
h=0.0275
x0,y0=PV[:,0].min(),PV[:,1].min(); nx=int((PV[:,0].max()-x0)/h)+1; ny=int((PV[:,1].max()-y0)/h)+1
# coarse mask via 0.2 grid then dense only near path
Zp={};Zg={}
n=0;over=[];buried=0;cnt=0
for j in range(ny):
    y=y0+j*h
    for i in range(nx):
        x=x0+i*h
        zp=top(pb,x,y)
        if zp is None: continue
        zg=top(gb,x,y)
        if zg is None: continue
        Zp[(i,j)]=zp;Zg[(i,j)]=zg
        e=zp-zg; over.append(e)
over=np.array(over)
print("dense samples %d area %.1f m2: max(cm) %.2f  p99(cm) %.2f  >1.5cm: %d ; buried(<-0.5cm) %.1f%% ; ex>1.2cm: %d"%(len(over),len(over)*h*h,100*over.max(),100*np.percentile(over,99),(over>0.015).sum(),100*(over<-0.005).mean(),(over>0.012).sum()))
# ball test: centre positions every 4th lattice node on path; sphere r=0.055 rests at max over disc (g+chord) using the ground field sampled on-the-fly
R=0.055; r=int(R/h)
offs=[(a,b,math.sqrt(R*R-(a*h)**2-(b*h)**2)) for a in range(-r,r+1) for b in range(-r,r+1) if (a*h)**2+(b*h)**2<=R*R]
hid_c=[];hid_v=[];tested=0
keys=sorted(Zp.keys())
sel=keys[::40]
for (i,j) in sel:
    gz=[];pz=[]
    ok=True
    for a,b,ch in offs:
        x=x0+(i+a)*h; y=y0+(j+b)*h
        g=top(gb,x,y)
        if g is None: ok=False;break
        p=Zp.get((i+a,j+b))
        if p is None:
            p=top(pb,x,y)
        gz.append(g+ch); pz.append(p if p is not None else -1e9)
    if not ok: continue
    cz=max(gz)
    chs=np.array([o[2] for o in offs]); pz=np.array(pz)
    lo=cz-chs
    hid=np.clip(pz-lo,0,2*chs)
    hid_v.append(hid.sum()/(2*chs).sum())
    # centre column: hidden fraction of the diameter
    k0=[n_ for n_,o in enumerate(offs) if o[0]==0 and o[1]==0][0]
    hid_c.append(hid[k0]/(2*chs[k0]))
    tested+=1
hid_v=np.array(hid_v);hid_c=np.array(hid_c)
print("ball test positions %d: volume-ish hidden max %.1f%% p95 %.1f%% ; centre-column diameter hidden max %.1f%%"%(tested,100*hid_v.max(),100*np.percentile(hid_v,95),100*hid_c.max()))
# what about a ball that touches ONLY a lower surface next to the path (e.g. fairway step): ok.
# edge skirts: lowest path vertex vs ground
sk=ex[ex<-0.02]
print("skirt feet count %d, depth min %.3f max %.3f"%(len(sk),sk.min() if len(sk) else 0,sk.max() if len(sk) else 0))
