import numpy as np, collections
A=np.load('data/artdir_body.npz'); B=np.load('data/base_body.npz'); F=np.load('data/f3_body.npz'); T=np.load('data/form5_body.npz')
def faces(d):
    ls,lt,cv=d['loop_start'],d['loop_total'],d['corner_verts']
    return [tuple(int(x) for x in cv[s:s+t]) for s,t in zip(ls,lt)]
def topo(name,d):
    fl=faces(d); cnt=collections.Counter()
    for f in fl:
        for i in range(len(f)):
            a,b=f[i],f[(i+1)%len(f)]; cnt[(min(a,b),max(a,b))]+=1
    bnd=[e for e,c in cnt.items() if c==1]; nm=[e for e,c in cnt.items() if c>2]
    V=d['V']
    print(f'{name}: faces {len(fl)} edges {len(cnt)} boundary {len(bnd)} nonmanifold {len(nm)}')
    if bnd:
        bv=np.array(sorted(set(v for e in bnd for v in e)))
        print('   boundary verts', len(bv), ' z', V[bv,2].min(), V[bv,2].max(), ' |x|max', np.abs(V[bv,0]).max())
        # connected components of boundary edges
        adj=collections.defaultdict(list)
        for a,b in bnd: adj[a].append(b); adj[b].append(a)
        seen=set(); comps=[]
        for s in adj:
            if s in seen: continue
            st=[s]; seen.add(s); comp=[s]
            while st:
                u=st.pop()
                for w in adj[u]:
                    if w not in seen: seen.add(w); st.append(w); comp.append(w)
            comps.append(comp)
        print('   boundary loops:', len(comps))
        for c in sorted(comps, key=lambda c:-V[c,2].mean()):
            P=V[c]; print('     loop n=%3d  centre (%.3f %.3f %.3f)  z[%.4f,%.4f]'%(len(c),*P.mean(0),P[:,2].min(),P[:,2].max()))
    return fl
for n,d in (('ArtDir',A),('base(hands cand.)',B),('FORM5 cand.',T),('F3 Body_F',F)): topo(n,d)
# inner-mouth / eye info: F3 faces materials around boundary?
