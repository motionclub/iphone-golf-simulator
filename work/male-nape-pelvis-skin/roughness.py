"""Mesh-noise audit: dihedral angles across edges (deg) inside a zone, start vs candidate. blender python3.13: roughness.py <tag...>"""
import sys; sys.path.insert(0,'.')
from common import *
E=edges()
# edge -> adjacent faces
from collections import defaultdict
ef=defaultdict(list)
for fi,f in enumerate(F):
    for k in range(len(f)):
        a,b=f[k],f[(k+1)%len(f)]; ef[(min(a,b),max(a,b))].append(fi)
pairs=[(e,fs) for e,fs in ef.items() if len(fs)==2]
def fnorm(V):
    n=np.zeros((len(F),3))
    for i,f in enumerate(F):
        P=V[list(f)]; fn=np.zeros(3)
        for k in range(1,len(f)-1): fn+=np.cross(P[k]-P[0],P[k+1]-P[0])
        n[i]=fn/max(np.linalg.norm(fn),1e-18)
    return n
def dihedral(V):
    n=fnorm(V); a=np.array([p[1][0] for p in pairs]); b=np.array([p[1][1] for p in pairs]); return np.degrees(np.arccos(np.clip((n[a]*n[b]).sum(1),-1,1)))
ev=np.array([p[0] for p in pairs]); zc=(V0[ev[:,0],2]+V0[ev[:,1],2])/2; xc=np.abs(V0[ev[:,0],0]+V0[ev[:,1],0])/2
zones={'pelvis rear+front z.735-1.06 |x|<.2':(zc>=0.735)&(zc<=1.06)&(xc<=0.2),'crotch z.735-.83 |x|<.1':(zc>=0.735)&(zc<=0.83)&(xc<=0.1),'nape z1.30-1.48 |x|<.14':(zc>=1.30)&(zc<=1.48)&(xc<=0.14)}
d0=dihedral(V0)
for t in (sys.argv[1:] if __name__=='__main__' else []):
    V=np.load(f'data/V_{t}.npy'); d1=dihedral(V)
    for nm,m in zones.items():
        print(f'{t:8s} {nm:34s} edges {int(m.sum()):5d} | start p50/p95/p99/max {np.percentile(d0[m],50):4.1f}/{np.percentile(d0[m],95):5.1f}/{np.percentile(d0[m],99):5.1f}/{d0[m].max():5.1f} | cand {np.percentile(d1[m],50):4.1f}/{np.percentile(d1[m],95):5.1f}/{np.percentile(d1[m],99):5.1f}/{d1[m].max():5.1f} | new sharp edges (>40deg & start<25): {int(((d1>40)&(d0<25)&m).sum())}')
