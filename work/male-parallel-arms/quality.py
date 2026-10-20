import numpy as np
from zonelib import *
AX=np.array([0.678,-0.178,-0.713]); C0=np.array([0.437,-0.061,1.064])
def arm_t(V,side):
    P=V.copy(); P[:,0]*=side; return (P-C0)@AX
def face_normals(V,polys):
    N=np.zeros((len(polys),3))
    for i,f in enumerate(polys):
        p=V[list(f)]; q=np.roll(p,-1,0)
        N[i]=np.array([((p[:,1]-q[:,1])*(p[:,2]+q[:,2])).sum(),((p[:,2]-q[:,2])*(p[:,0]+q[:,0])).sum(),((p[:,0]-q[:,0])*(p[:,1]+q[:,1])).sum()])
    l=np.linalg.norm(N,axis=1,keepdims=True); return N/np.maximum(l,1e-15)
def edge_faces(polys):
    ef={}
    for fi,f in enumerate(polys):
        for k in range(len(f)):
            a,b=f[k],f[(k+1)%len(f)]; ef.setdefault((min(a,b),max(a,b)),[]).append(fi)
    return ef
_cache={}
def metrics(V,T,polys,zoneR,zoneL,shell,iters=6):
    n=len(V)
    if 'E' not in _cache: _cache['E']=edges_of(polys,n); _cache['ef']=edge_faces(polys)
    E=_cache['E']; ef=_cache['ef']
    N=vnormals(V,T)
    out={}
    for nm,z,side in (('R',zoneR,+1),('L',zoneL,-1)):
        # interior = zone verts with all neighbours in zone (so Taubin sees only zone), weights 1 for them, 0 pinned boundary
        w=np.zeros(n); idx=np.nonzero(z)[0]
        inz=z.copy()
        # boundary: zone verts adjacent to non-zone
        nbz=np.zeros(n,bool)
        for a,b in E:
            if z[a]!=z[b]: nbz[a]=nbz[b]=True
        w[z&~nbz]=1.0
        P=taubin(V,E,w,iters)
        r=((P-V)*N).sum(1)
        t=arm_t(V,side)
        # exclude rows near the shoulder cut: use t>-0.22
        for rn,(a,b) in {'upper':(-0.22,-0.02),'fore':(-0.02,0.085),'wristhand':(0.085,0.5)}.items():
            m=z&(w>0)&(t>=a)&(t<b)
            out[f'{nm}_{rn}_hf_rms_mm']=float(1000*np.sqrt(np.mean(r[m]**2))) if m.sum() else None
            out[f'{nm}_{rn}_hf_p99_mm']=float(1000*np.percentile(np.abs(r[m]),99)) if m.sum() else None
    Fn=face_normals(V,polys)
    zz=zoneR|zoneL
    cnt30=cnt45=cnt60=0; mx=0; tot=0
    for (a,b),fs in ef.items():
        if len(fs)==2 and zz[a] and zz[b]:
            c=np.clip((Fn[fs[0]]*Fn[fs[1]]).sum(),-1,1); ang=np.degrees(np.arccos(c)); tot+=1
            if ang>30: cnt30+=1
            if ang>45: cnt45+=1
            if ang>60: cnt60+=1
            mx=max(mx,ang)
    out.update(edges=tot,dihedral_gt30=cnt30,dihedral_gt45=cnt45,dihedral_gt60=cnt60,dihedral_max=float(mx))
    return out
if __name__=='__main__':
    import json
    V,T,polys=load(); zR=np.load('data/zone_R.npy'); zL=np.load('data/zone_L.npy'); sh=np.load('data/shell_cur.npy')
    m=metrics(V,T,polys,zR,zL,sh); print(json.dumps(m,indent=1))
