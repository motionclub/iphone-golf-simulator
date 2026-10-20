import sys, numpy as np
sys.path.insert(0,'../male-micro1e')
import hand_sdf as H
import run
tag=sys.argv[1]; thr=float(sys.argv[2]) if len(sys.argv)>2 else 90
V=np.load(f'data/it/{tag}_cur.npy') if tag!='base' else run.V0
fo=sorted(run.folds(V,thr),reverse=True)
print(len(fo),'edges >',thr)
for ang,a,b in fo:
    side=+1 if V[a,0]>0 else -1
    if side<0: continue
    m=(V[a]+V[b])/2; l=H.to_local(m[None].astype(float),+1)[0]
    print(f'{ang:6.1f} local a\'={l[0]:+.3f} n={l[1]:+.3f} w={l[2]:+.3f} len={1000*np.linalg.norm(V[a]-V[b]):.1f}mm verts {a},{b}')
