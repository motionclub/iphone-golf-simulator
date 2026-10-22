import numpy as np
D=np.load('data/start_cur.npz'); co0=D['co'].astype(np.float64); lv=D['loop_v']; ls=D['loop_start']; lt=D['loop_total']
Z=np.load('data/zones_cur.npz'); arm=Z['arm']
faces=[lv[s:s+t] for s,t in zip(ls,lt)]
from collections import defaultdict
e2f=defaultdict(list)
for fi,f in enumerate(faces):
    for k in range(len(f)):
        a,b=f[k],f[(k+1)%len(f)]; e2f[(min(a,b),max(a,b))].append(fi)
pairs=[(e,f) for e,f in e2f.items() if len(f)==2 and (arm[e[0]] or arm[e[1]])]
def fn(co):
    N=[]
    for f in faces:
        p=co[f]; n=np.cross(p[2]-p[0],p[3]-p[1]) if len(f)==4 else np.cross(p[1]-p[0],p[2]-p[0])
        N.append(n/ (np.linalg.norm(n)+1e-12))
    return np.array(N)
N0=fn(co0)
def stats(co):
    N=fn(co); out=[]
    for (a,b),(f1,f2) in pairs:
        out.append(np.degrees(np.arccos(np.clip(N[f1]@N[f2],-1,1))))
    out=np.array(out)
    mid=np.array([(co[a]+co[b])/2 for (a,b),_ in pairs])
    return out,mid
d0,mid=stats(co0)
def report(co,label):
    d1,_=stats(co)
    zone=(np.abs(mid[:,0])>0.1)&(mid[:,2]>0.95)&(mid[:,2]<1.36)
    print(label,'arm all: max %.1f p99 %.1f | start max %.1f p99 %.1f || armpit-shoulder zone: max %.1f p99 %.1f (start %.1f %.1f) | worst growth %.1f'%(d1.max(),np.percentile(d1,99),d0.max(),np.percentile(d0,99),d1[zone].max(),np.percentile(d1[zone],99),d0[zone].max(),np.percentile(d0[zone],99),(d1-d0).max()))
if __name__=='__main__':
    import sys
    report(np.load(sys.argv[1]).astype(np.float64),sys.argv[1])
