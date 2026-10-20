import sys; sys.path.insert(0,'.')
from common import *
E = edges(); L = np.linalg.norm(V0[E[:,0]]-V0[E[:,1]],axis=1)
def zone_stats(name, m):
    em = m[E[:,0]] & m[E[:,1]]
    print(f'{name}: verts {m.sum()}  edges {em.sum()}  edge len mm: mean {L[em].mean()*1000:.2f} med {np.median(L[em])*1000:.2f} p10 {np.percentile(L[em],10)*1000:.2f} p90 {np.percentile(L[em],90)*1000:.2f}')
Z=V0[:,2]; X=V0[:,0]
zone_stats('NAPE z1.28-1.42 |x|<=.18', (Z>=1.28)&(Z<=1.42)&(np.abs(X)<=0.18))
zone_stats('PELVIS z.77-1.05 |x|<=.22', (Z>=0.77)&(Z<=1.05)&(np.abs(X)<=0.22))
print('total verts', N0, 'faces', len(F), 'quads', sum(1 for f in F if len(f)==4), 'tris', sum(1 for f in F if len(f)==3), 'ngons', sum(1 for f in F if len(f)>4))
# crotch apex: the highest z among vertices with |x|<0.05 that belong to the gap boundary -> look at verts with x in (-.03,.03), y>-.05
c = V0[(np.abs(X)<0.03)]
print('mid-column z hist (|x|<.03) .70-.90:')
zz=np.sort(c[(c[:,2]>0.70)&(c[:,2]<0.90)][:,2]); print(np.round(zz,3)[:100])
# per-z rows: rear-most y at |x|<4mm and widest |x|
print('z | rear y mid (mm) | front y mid (mm) | half width (mm)  [torso only |x|<.25]')
for z in np.arange(0.70,1.50,0.02):
    S = section_segments(V0, z)
    if len(S)==0: continue
    P = S.reshape(-1,2); P = P[np.abs(P[:,0])<0.25]
    mid = P[np.abs(P[:,0])<0.006]
    print(f'{z:.2f} | {mid[:,1].max()*1000 if len(mid) else float("nan"):7.1f} | {mid[:,1].min()*1000 if len(mid) else float("nan"):7.1f} | {np.abs(P[:,0]).max()*1000:6.1f}')
