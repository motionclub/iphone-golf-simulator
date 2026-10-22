import numpy as np, collections
A=np.load('data/artdir_body.npz'); B=np.load('data/base_body.npz'); F=np.load('data/f3_body.npz'); FF=np.load('data/f3_face.npz')
zc=1.40545
def faces(d):
    ls,lt,cv=d['loop_start'],d['loop_total'],d['corner_verts']
    return [tuple(cv[s:s+t]) for s,t in zip(ls,lt)]
fb=faces(B); VB=B['V']
hb=VB[:,2]>zc
fcls=np.array([2 if all(hb[v] for v in f) else (1 if any(hb[v] for v in f) else 0) for f in fb])
print('base faces: lower',(fcls==0).sum(),'cross',(fcls==1).sum(),'head',(fcls==2).sum())
mat=B['material_index']
print('base material names', list(B['material_names']))
print('base material usage lower body:', dict(collections.Counter(mat[fcls==0].tolist())), ' cross:', dict(collections.Counter(mat[fcls==1].tolist())), ' head:', dict(collections.Counter(mat[fcls==2].tolist())))
print('F3 material names', list(F['material_names']), ' usage:', dict(collections.Counter(F['material_index'].tolist())))
# tris
tb=B['loop_total']-2
print('base tris: lower',int(tb[fcls==0].sum()),' cross',int(tb[fcls==1].sum()),' head',int(tb[fcls==2].sum()), ' total', int(tb.sum()))
ff=faces(F); nlowF=12421
fclsF=np.array([0 if all(v<nlowF for v in f) else (2 if all(v>=nlowF for v in f) else 1) for f in ff]); tF=F['loop_total']-2
print('F3 tris: lower',int(tF[fclsF==0].sum()),' cross',int(tF[fclsF==1].sum()),' head',int(tF[fclsF==2].sum()),' total',int(tF.sum()))
print('F3 loop_total counts', dict(collections.Counter(F['loop_total'].tolist())), ' base', dict(collections.Counter(B['loop_total'].tolist())))
# smooth/sharp
print('smooth: base all', bool(B['use_smooth'].all()), ' F3 all', bool(F['use_smooth'].all()))
print('sharp_edge: base', int(B['sharp_edge'].sum()) if 'sharp_edge' in B.files else None, ' F3', int(F['sharp_edge'].sum()) if 'sharp_edge' in F.files else None, ' artdir', 'sharp_edge' in A.files)
# UV
for nm,d in (('base',B),('F3',F),('art',A)):
    uv=d['uv']; print(nm,'uv range', uv.min(0), uv.max(0), ' unique uv', len(np.unique(uv.round(5),axis=0)))
# F3 head loops uv
lsF=F['loop_start']; ltF=F['loop_total']
hl=np.concatenate([np.arange(s,s+t) for s,t,c in zip(lsF,ltF,fclsF) if c!=0])
print('F3 head-face loops uv unique', np.unique(F['uv'][hl].round(5),axis=0)[:5], len(np.unique(F['uv'][hl].round(5),axis=0)))
print('F3 head-face materials', dict(collections.Counter(F['material_index'][fclsF!=0].tolist())))
# custom normals raw
for nm,d in (('base',B),('F3',F),('art',A)):
    c=d['custom_normal_i16']; print(nm,'custom_normal raw: code0 zero frac', float((c[:,0]==0).mean()), ' nonzero code1', float((c[:,1]!=0).mean()), ' range', c.min(), c.max())
# vertex groups
vg=F['vg_names']; W=F['vg_weights']
print('F3 vgroups', len(vg), list(vg))
for i,n in enumerate(vg):
    m=np.nonzero(W[i]>0)[0]
    print(f'  {n:22} n={len(m):4d} idx[{m.min()},{m.max()}] on_ring_or_below={int((m<nlowF).sum())} w[{W[i][m].min():.2f},{W[i][m].max():.2f}]')
# Face_F
print('Face_F verts', len(FF['V']), 'z', FF['V'][:,2].min(), FF['V'][:,2].max(), 'materials', list(FF['material_names']))
