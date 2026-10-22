import numpy as np, sys, time
sys.path.insert(0,'.')
import hand_build as HB, hand_topo as T, hand_sdf as H
d=np.load('baseline/mesh.npz'); co=d['co']; F=np.load('faces.npy')
side=int(sys.argv[1]) if len(sys.argv)>1 else 1
t0=time.time()
res=HB.build_hand(co,F,side)
B=res['builder']; cut=res['cut']
print('new verts',len(B.pos),'new faces',len(B.faces),'removed faces',int(cut['removed'].sum()),'freed verts',int(cut['Hmask'].sum()),'ring',len(cut['ring']))
tris=sum(1 for f in B.faces if len(f)==3)
print('tris in new faces',tris)
# unused vertices
used=set(v for f in B.faces for v in f)
unused=[i for i in range(len(B.pos)) if (B.N+i) not in used]
print('unused new verts',len(unused))
kept=F[cut['kept']]
newf,vis=T.orient_consistently(B.faces,kept)
allf=[tuple(map(int,f)) for f in kept]+newf
print('manifold check (edges,boundary,nonmanifold,bad orient):',T.check_manifold(allf))
print('unvisited new faces',sum(1 for v in vis[len(kept):] if not v))
print('time',time.time()-t0)

from collections import defaultdict
e=defaultdict(list)
nk=len(kept)
for fi,f in enumerate(allf):
    for k in range(len(f)):
        a,b=f[k],f[(k+1)%len(f)]
        e[(min(a,b),max(a,b))].append((fi,a,b))
N=B.N
def desc(v):
    return f'old{v}' if v<N else f'new{v-N}'
nm=[(k,v) for k,v in e.items() if len(v)>2]
for k,v in nm:
    print('nonmanifold edge',desc(k[0]),desc(k[1]),'faces',[(fi,'kept' if fi<nk else 'new') for fi,_,_ in v])
bad=[(k,v) for k,v in e.items() if len(v)==2 and v[0][1:]==v[1][1:]]
print('bad orient edges: count',len(bad))
for k,v in bad[:12]:
    print('  ',desc(k[0]),desc(k[1]),[(fi,'kept' if fi<nk else 'new', len(allf[fi])) for fi,_,_ in v])
