import sys, json
from pathlib import Path
W=Path(__file__).resolve().parent; R=W.parents[1]
sys.path[:0]=[str(W),str(R/'male-micro1e')]
import numpy as np
import hand_build as HB0, hand_build2 as HB2, hand_sdf as H, hand_topo as T
params=json.load(open(W/'params_m1f_final.json'))
HB2.P.update(params); HB0.P.update({k:v for k,v in params.items() if k in HB0.P})
BASE=np.load(R/'male-micro1e/baseline/mesh.npz')['co'].astype(float); F0=np.load(R/'male-micro1e/faces.npy')
r=HB2.build_hand(BASE,F0,+1,-0.055)
B=r['builder']; N=len(BASE); loop=r['loop']
P=lambda v: B.pos[v-N]
print('hole loop local (a n w):')
for v in loop: print(np.round(P(v),4))
# thumb rows: find via faces (loop -> first ring)
faces=B.faces
loopset=set(loop)
first=[ [f for f in faces if loop[k] in f and f[0]==loop[k]] for k in range(10)]
fr=[f for f in faces if f[0] in loopset and f[1] in loopset]
ring0=[f[3] for f in fr]
ids=sorted(set(f[2] for f in fr)|set(f[3] for f in fr)-set(loop))
print('first thumb ring local:')
for f in fr: print(np.round(P(f[3]),4),np.round(P(f[2]),4))
