import sys, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
import hole08_look as K
ob=bpy.data.objects["BUNKER_01_LIP"]; me=ob.data
V=np.array([v.co[:] for v in me.vertices]); n=len(V)
nb=[set() for _ in range(n)]
for e in me.edges:
    a,b=e.vertices; nb[a].add(b); nb[b].add(a)
zmax=V[:,2].max(); crest=[i for i in range(n) if V[i,2]>zmax-0.02]; cset=set(crest)
cn={i:[j for j in nb[i] if j in cset] for i in crest}
print("crest",len(crest),"neighbours hist",sorted({len(v) for v in cn.values()}))
order=[crest[0]]; prev=None; cur=crest[0]
while True:
    nx=[j for j in cn[cur] if j!=prev]
    if not nx or nx[0]==crest[0]: break
    prev,cur=cur,nx[0]; order.append(cur)
    if len(order)>len(crest): break
print("order",len(order))
C=V[order]
seg=np.linalg.norm(np.roll(C,-1,axis=0)-C,axis=1); S=np.concatenate([[0],np.cumsum(seg)]); L=S[-1]
print("ring length",L)
cen=C[:,:2].mean(0)
def project(p):
    best=None
    for k in range(len(C)):
        a=C[k]; b=C[(k+1)%len(C)]; ab=b-a; t=np.clip(((p-a)@ab)/(ab@ab),0,1); q=a+ab*t; d=np.linalg.norm(p-q)
        if best is None or d<best[0]: best=(d,S[k]+t*seg[k],q)
    d,s,q=best
    out=np.hypot(*(p[:2]-cen))>np.hypot(*(q[:2]-cen))
    return s,(d if out else -d)
ST=np.array([project(p) for p in V])
tile=12.0; k_t=max(1,round(L/tile)); tile2=L/k_t
def stats(uvfun):
    lay=me.uv_layers.active.data; flips=0; ratios=[]
    for p in me.polygons:
        vs=[me.loops[li].vertex_index for li in range(p.loop_start,p.loop_start+p.loop_total)]
        U=uvfun(vs)
        Vv=V[vs]
        e1=Vv[1]-Vv[0]; e2=Vv[3]-Vv[0]; nr=np.cross(e1,e2); nr/=np.linalg.norm(nr); a1=e1/np.linalg.norm(e1); a2=np.cross(nr,a1)
        P2=np.array([[ (v-Vv[0])@a1,(v-Vv[0])@a2] for v in Vv])
        sol=np.linalg.lstsq(np.c_[P2,np.ones(4)],U,rcond=None)[0]; J=sol[:2].T
        sv=np.linalg.svd(J,compute_uv=False); ratios.append(sv[0]/sv[1]); flips+= np.linalg.det(J)<=0
    return flips,max(ratios),np.mean(ratios)
def wrapd(d): return d-L*np.round(d/L)
def uv_np(vs, sign=1.0):
    ref=ST[vs[0],0]
    return np.array([[ (ref+wrapd(ST[v,0]-ref))/tile2, sign*ST[v,1]/tile2] for v in vs])
print("planar", stats(lambda vs: V[vs][:,:2]/12.0))
print("nearest-point +", stats(lambda vs: uv_np(vs,1.0)))
print("nearest-point -", stats(lambda vs: uv_np(vs,-1.0)))
