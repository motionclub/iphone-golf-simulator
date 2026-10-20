import numpy as np, collections
L=lambda n: np.load(f'data/{n}.npz',allow_pickle=True)
FIN,F3,S3,A=L('final_body'),L('f3_body'),L('stage3_body'),L('artdir_body')
D=np.load('export/full_merge_delta.npz'); NLOW=12421
VF,V3=FIN['V'],F3['V']
nkeep=13224; keep_v=np.ones(23247,bool); keep_v[D['old_head_idx']]=False; newidx=np.cumsum(keep_v)-1
ring_final=set(newidx[D['ring_base_idx']].tolist())
def corners(d,V):
    # dict: (pos of vertex, frozenset of face vertex positions) -> (decoded normal, raw, loop idx)
    ls,lt,cv=d['loop_start'],d['loop_total'],d['corner_verts']; out={}
    cn=d['corner_normals']; raw=d['custom_normal_i16']
    for s,t in zip(ls,lt):
        vs=cv[s:s+t]; fk=frozenset(tuple(V[v]) for v in vs)
        for i in range(t): out[(tuple(V[vs[i]]),fk)]=(cn[s+i].astype(np.float64),raw[s+i],s+i,int(vs[i]))
    return out
cf=corners(FIN,VF); c3=corners(F3,V3); cs=corners(S3,S3['V']); ca=corners(A,A['V'])
ring_pos=set(tuple(VF[i]) for i in ring_final)
def deg(a,b): return float(np.degrees(np.arccos(np.clip(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
def vd(a,b): return float(np.linalg.norm(a-b))
rows=[]
for key,(n_f,r_f,l_f,v_f) in cf.items():
    if key[0] not in ring_pos: continue
    if key not in c3: rows.append(('no F3 match',)); continue
    n3,r3,_,_=c3[key]
    # stock/ArtDir for lower-face corners (old fan)
    nsta=cs.get(key)
    rows.append((l_f<56322, vd(n_f,n3), deg(n_f,n3), None if nsta is None else deg(n_f,nsta[0]), None if nsta is None else deg(n3,nsta[0]), bool((r_f==r3).all())))
rows=[r for r in rows if len(r)>1]
low=[r for r in rows if r[0]]; head=[r for r in rows if not r[0]]
print('ring corners: lower-face loops', len(low), ' head-face loops', len(head))
for nm,rr in (('LOWER faces at ring verts',low),('HEAD faces at ring verts',head)):
    d=np.array([r[2] for r in rr]); print(f'{nm}: final vs F3 decode deg: max {d.max():.3f} mean {d.mean():.3f}  >0.1deg: {(d>0.1).sum()}  raw equal to F3 raw: {sum(r[5] for r in rr)}/{len(rr)}')
    ds=[r[3] for r in rr if r[3] is not None]
    if ds: print(f'    final vs STOCK(old fan) deg max {max(ds):.2f} mean {np.mean(ds):.2f};  F3 vs STOCK deg max {max(r[4] for r in rr if r[4] is not None):.2f} mean {np.mean([r[4] for r in rr if r[4] is not None]):.2f}')
