import sys; sys.path.insert(0,'.')
from leglib import *
def face_normals(V):
    out=[]
    for p in F:
        a=V[p[0]];b=V[p[1]];c=V[p[2]];d=V[p[3]] if len(p)>3 else None
        n=np.cross(V[p[2]]-V[p[0]],V[p[3]]-V[p[1]]) if len(p)==4 else np.cross(b-a,c-a)
        out.append(n/max(np.linalg.norm(n),1e-15))
    return np.array(out)
def quad_min_angle(V,faces):
    mins=[]
    for p in faces:
        ang=[]
        for k in range(4):
            a=V[p[(k-1)%4]]-V[p[k]]; b=V[p[(k+1)%4]]-V[p[k]]
            ang.append(np.degrees(np.arccos(np.clip(a@b/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
        mins.append((min(ang),max(ang)))
    return np.array(mins)
def report(tag,Vs=None):
    V=np.load(f'data/V_{tag}.npy')
    n0=face_normals(V0); n1=face_normals(V)
    zf=np.array([all(ZONE[i] for i in p) or any(ZONE[i] for i in p) for p in F])
    dots=(n0*n1).sum(1)
    el=np.linalg.norm(V[Ei]-V[Ej],axis=1); ez=ZONE[Ei]&ZONE[Ej]
    q=quad_min_angle(V,[F[i] for i in np.nonzero(zf)[0]])
    q0=quad_min_angle(V0,[F[i] for i in np.nonzero(zf)[0]])
    # leg-leg clearance
    L=V[LEFT]; R=V[RIGHT]
    mind=1e9
    for a in range(0,len(L),500):
        dd=np.linalg.norm(L[a:a+500,None,:]-R[None,:,:],axis=2); mind=min(mind,dd.min())
    print(tag,': zone faces',zf.sum(),'| flipped (dot<0.2 vs start):',(dots[zf]<0.2).sum(),'min dot %.3f'%dots[zf].min(),
      '| edge mm zone mean %.2f p1 %.2f p99 %.2f max %.2f (start mean %.2f p99 %.2f max %.2f)'%(el[ez].mean()*1000,np.percentile(el[ez],1)*1000,np.percentile(el[ez],99)*1000,el[ez].max()*1000,
      np.linalg.norm(V0[Ei]-V0[Ej],axis=1)[ez].mean()*1000,np.percentile(np.linalg.norm(V0[Ei]-V0[Ej],axis=1)[ez],99)*1000,np.linalg.norm(V0[Ei]-V0[Ej],axis=1)[ez].max()*1000),
      '| quad angle min %.1f max %.1f (start %.1f %.1f) | leg-leg min vertex gap %.1f mm'%(q[:,0].min(),q[:,1].max(),q0[:,0].min(),q0[:,1].max(),mind*1000))
for t in sys.argv[1:]: report(t)
