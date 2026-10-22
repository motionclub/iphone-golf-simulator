import sys, pickle
sys.path.insert(0,'.')
import numpy as np
from collections import defaultdict
from ff_common import *
name=sys.argv[1]
V,Fb=load_base()
Vn=np.load(f'tmp/V_{name}.npy'); D=pickle.load(open(f'tmp/F_{name}.pkl','rb')); Fn=D['faces']; tags=D['tags']
kept=set(tuple(sorted(f)) for f in Fb)
new_idx=[i for i,f in enumerate(Fn) if tuple(sorted(f)) not in kept]
def loc(p):
    side=1 if Vn[p,0]>0 else -1
    return to_local(Vn[p],side,foot_frame(side))
def fnorm(p):
    p=list(p); 
    n=np.cross(Vn[p[2]]-Vn[p[0]],Vn[p[3]]-Vn[p[1]]) if len(p)==4 else np.cross(Vn[p[1]]-Vn[p[0]],Vn[p[2]]-Vn[p[0]])
    return n/max(np.linalg.norm(n),1e-18)
FN=np.array([fnorm(p) for p in Fn])
ef=defaultdict(list)
for i,p in enumerate(Fn):
    for k in range(len(p)):
        a,b=p[k],p[(k+1)%len(p)]; ef[(min(a,b),max(a,b))].append(i)
flips=[]
for i,p in enumerate(Fn):
    nb=[]
    for k in range(len(p)):
        a,b=p[k],p[(k+1)%len(p)]; nb+=[j for j in ef[(min(a,b),max(a,b))] if j!=i]
    if nb and FN[i]@FN[nb].mean(0)<0: flips.append(i)
newset=set(new_idx)
print('flipped faces total',len(flips),'in new region',sum(1 for i in flips if i in newset))
for i in flips:
    p=Fn[i]; c=np.mean([loc(v) for v in p],axis=0)*1000
    print('  face',i,'new' if i in newset else 'old','len',len(p),'centre f,l,z mm',np.round(c,1),'tags',[tags.get(v,('old',))[1][:3] if v in tags else 'old' for v in p][:4])
def angs(p):
    a=[]
    for k in range(4):
        u=Vn[p[(k-1)%4]]-Vn[p[k]]; v=Vn[p[(k+1)%4]]-Vn[p[k]]
        c=(u@v)/max(np.linalg.norm(u)*np.linalg.norm(v),1e-18); a.append(np.degrees(np.arccos(np.clip(c,-1,1))))
    return a
print('bad quads (min<12 or max>168):')
for i in new_idx:
    p=Fn[i]
    if len(p)!=4: continue
    a=angs(p)
    if min(a)<12 or max(a)>168:
        c=np.mean([loc(v) for v in p],axis=0)*1000
        print('  ',i,[round(x) for x in a],'centre',np.round(c,1),[tags.get(v,('old',))[1][:3] if v in tags else 'old' for v in p])
E=set()
for i in new_idx:
    p=Fn[i]
    for k in range(len(p)): E.add((min(p[k],p[(k+1)%len(p)]),max(p[k],p[(k+1)%len(p)])))
E=sorted(E); L=np.array([np.linalg.norm(Vn[a]-Vn[b]) for a,b in E])*1000
print('edges <1.5mm:',int((L<1.5).sum()),' shortest:',[ (round(L[j],2),tags.get(E[j][0]),tags.get(E[j][1])) for j in np.argsort(L)[:4]])
