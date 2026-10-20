import numpy as np, collections
A=np.load('data/artdir_body.npz'); B=np.load('data/base_body.npz'); F=np.load('data/f3_body.npz')
def faces(d):
    ls,lt,cv=d['loop_start'],d['loop_total'],d['corner_verts']
    return [tuple(cv[s:s+t]) for s,t in zip(ls,lt)]
def edges_of(fl):
    cnt=collections.Counter()
    for f in fl:
        for i in range(len(f)):
            a,b=f[i],f[(i+1)%len(f)]; cnt[(min(a,b),max(a,b))]+=1
    return cnt
VA=A['V']; VB=B['V']; VF=F['V']
# ---- ArtDir head cut
zc=0.50*(1.4053155+1.4055792)
headA=VA[:,2]>zc
fa=faces(A)
cls=np.array([0 if not any(headA[v] for v in f) else (2 if all(headA[v] for v in f) else 1) for f in fa])
print('ArtDir faces: lower',(cls==0).sum(),' crossing',(cls==1).sum(),' head',(cls==2).sum(), ' total', len(fa))
# boundary of lower faces (edges with exactly one lower face)
low=[f for f,c in zip(fa,cls) if c==0]
ec=edges_of(low); bnd=[e for e,c in ec.items() if c==1]
print('ArtDir lower-body open boundary edges:', len(bnd), ' verts', len(set(v for e in bnd for v in e)))
ringA=sorted(set(v for e in bnd for v in e))
print('  ring z range', VA[ringA,2].min(), VA[ringA,2].max())
# crossing faces count & their composition
print('  crossing faces verts per face', collections.Counter(len(f) for f,c in zip(fa,cls) if c==1))
# ---- F3 head/lower
nlowF=12421
fF=faces(F)
clsF=np.array([0 if all(v<nlowF for v in f) else (2 if all(v>=nlowF for v in f) else 1) for f in fF])
print('F3 faces: lower',(clsF==0).sum(),' crossing',(clsF==1).sum(),' head',(clsF==2).sum(), ' total', len(fF))
lowF=[f for f,c in zip(fF,clsF) if c==0]
ecF=edges_of(lowF); bndF=[e for e,c in ecF.items() if c==1]
print('F3 lower-body open boundary edges:', len(bndF), ' verts', len(set(v for e in bndF for v in e)))
ringF=sorted(set(v for e in bndF for v in e))
print('  ring z range', VF[ringF,2].min(), VF[ringF,2].max())
# match ring positions
kA={tuple(v):i for i,v in enumerate(VA)}
posA=set(tuple(VA[i]) for i in ringA); posF=set(tuple(VF[i]) for i in ringF)
print('ring position sets equal:', posA==posF, len(posA), len(posF))
# lower face sets equal (by position tuples)?
def facekey(V,f):
    # rotation/orientation-normalised key of positions
    pts=[tuple(V[v]) for v in f]; i=pts.index(min(pts)); pts=pts[i:]+pts[:i]
    r=[pts[0]]+pts[1:][::-1]
    return min(tuple(pts),tuple(r))
sA=collections.Counter(facekey(VA,f) for f,c in zip(fa,cls) if c==0)
sF=collections.Counter(facekey(VF,f) for f,c in zip(fF,clsF) if c==0)
print('lower faces: ArtDir',sum(sA.values()),' F3',sum(sF.values()),' multiset equal:', sA==sF, ' only in A', sum((sA-sF).values()), ' only in F3', sum((sF-sA).values()))
# in F3 are all crossing faces touching ring verts only?
cross=[f for f,c in zip(fF,clsF) if c==1]
print('F3 crossing faces', len(cross), ' lower verts used by crossing faces all on ring:', all(v in set(ringF) for f in cross for v in f if v<nlowF))
# ---- base: head verts via exact position match
kB=collections.defaultdict(list)
for i,v in enumerate(VB): kB[tuple(v)].append(i)
hA=np.nonzero(headA)[0]
miss=[i for i in hA if tuple(VA[i]) not in kB]
multi=[i for i in hA if len(kB.get(tuple(VA[i]),[]))>1]
print('ArtDir head verts', len(hA), ' missing in base by exact pos:', len(miss), ' multi-match:', len(multi))
# base ring: positions equal to F3 ring?
miss_r=[i for i in ringF if tuple(VF[i]) not in kB]; multi_r=[i for i in ringF if len(kB.get(tuple(VF[i]),[]))>1]
print('F3 ring verts missing in base:', len(miss_r), ' multiple matches:', len(multi_r))
# base head verts exact count above cut
print('base verts above cut z>%.5f'%zc, (VB[:,2]>zc).sum(), ' (ArtDir head verts', len(hA),')')
