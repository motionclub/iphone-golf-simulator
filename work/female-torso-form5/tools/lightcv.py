import sys; sys.path.insert(0,'tools')
from fplate import *
M=Mesh(); N=M.normals(); co=M.co
legs=(co[:,2]<0.74)&(co[:,2]>0.14)&~M.T
arms=(M.arm)&(co[:,2]>0.93)&(co[:,2]<1.30)&(np.abs(co[:,0])>0.15)&~M.T
def basis_full(N,vw,co,extra=()):
    B=[sh2c_full(N,vw)]
    z=co[:,2]; x=(co[:,0]*vw.right[0]+co[:,1]*vw.right[1])
    if 'z' in extra: B.append(np.stack([z,z*z],1))
    if 'x' in extra: B.append(np.stack([x,x*x],1))
    if 'xz' in extra: B.append(np.stack([x*z],1))
    return np.concatenate(B,1)
for name in ('front','back'):
    vw=View(name)
    I=luminance_at(vw,co,2.0)
    for extra in ((),('z',),('x',),('z','x'),('z','x','xz')):
        A=basis_full(N,vw,co,extra)
        vl=visible(vw,co,N,sel=legs); va=visible(vw,co,N,sel=arms)
        def fit(vis): 
            c,*_=np.linalg.lstsq(A[vis],I[vis],rcond=None); return c
        def r2(c,vis): p=A@c; return 1-((I[vis]-p[vis])**2).sum()/((I[vis]-I[vis].mean())**2).sum()
        cl=fit(vl); ca=fit(va); cb=fit(vl|va)
        print(f'{name} extra={extra!s:18s} fit legs R2 {r2(cl,vl):.3f}  fit arms R2 {r2(ca,va):.3f} | legs->arms {r2(cl,va):.3f}  arms->legs {r2(ca,vl):.3f} | both->both {r2(cb,vl|va):.3f}  n legs {vl.sum()} arms {va.sum()}')
