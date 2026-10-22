import numpy as np, collections
A=np.load('data/artdir_body.npz'); B=np.load('data/base_body.npz'); F=np.load('data/f3_body.npz')
def faces(d):
    ls,lt,cv=d['loop_start'],d['loop_total'],d['corner_verts']
    return [tuple(int(x) for x in cv[s:s+t]) for s,t in zip(ls,lt)]
for nm,d in (('ArtDir',A),('base',B),('F3',F)):
    V=d['V']; fl=faces(d); m=d['material_index']
    zc=np.array([V[list(f),2].mean() for f in fl])
    sk=m==1
    print(nm,'Skin_F faces',int(sk.sum()),' zc range', zc[sk].min(), zc[sk].max())
    # histogram of Skin_F faces by z bands
    bands=[(0,0.2),(0.2,0.6),(0.6,0.9),(0.9,1.3),(1.3,1.38),(1.38,1.41),(1.41,1.5),(1.5,1.8)]
    print('   Skin_F by z band:', [(a,b,int(((zc>=a)&(zc<b)&sk).sum()), int(((zc>=a)&(zc<b)).sum())) for a,b in bands])
